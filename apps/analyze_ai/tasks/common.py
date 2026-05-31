import json
import logging
from typing import List, Dict, Any

from django.conf import settings
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from c2_core.config.config import Config
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)

HASURA_GRAPHQL_URL = f"{Config.HASURA_URL}/v1/graphql" if Config.HASURA_URL else None
HASURA_ADMIN_SECRET = Config.HASURA_ADMIN_SECRET

INITIAL_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "initial_prompts.txt"
)


@log_function_call()
def get_graphql_client() -> Client:
    headers = (
        {"x-hasura-admin-secret": HASURA_ADMIN_SECRET} if HASURA_ADMIN_SECRET else {}
    )
    transport = RequestsHTTPTransport(
        url=HASURA_GRAPHQL_URL, headers=headers, use_json=True
    )
    return Client(transport=transport, fetch_schema_from_transport=False)


@log_function_call()
def load_initial_prompt_template() -> str:
    try:
        with open(INITIAL_PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"找不到 Initial Prompt 模板文件: {INITIAL_PROMPT_TEMPLATE_PATH}")
        raise


def fetch_initial_data_for_batch(analysis_ids: List[int]) -> Dict[str, Any]:
    from apps.core.models import InitialAIAnalysis, IP, Subdomain
    from apps.core.models.url_assets import URLResult

    records = InitialAIAnalysis.objects.filter(id__in=analysis_ids).select_related('ip', 'subdomain', 'url_result')

    ip_ids = [r.ip_id for r in records if r.ip_id]
    sub_ids = [r.subdomain_id for r in records if r.subdomain_id]
    url_ids = [r.url_result_id for r in records if r.url_result_id]

    all_assets = []
    record_map = {}
    for r in records:
        if r.ip_id: record_map[('ip', r.ip_id)] = r.id
        if r.subdomain_id: record_map[('subdomain', r.subdomain_id)] = r.id
        if r.url_result_id: record_map[('url', r.url_result_id)] = r.id

    if ip_ids:
        ips = IP.objects.filter(id__in=ip_ids).prefetch_related('ports').values(
            "id", "address", "version"
        )
        ports_qs = dict(IP.objects.filter(id__in=ip_ids).prefetch_related('ports'))
        for ip in ips:
            ip_obj = ports_qs.get(ip['id'])
            ports = list(ip_obj.ports.filter(state="open").values("port_number", "protocol", "service_name", "service_version")) if ip_obj else []
            all_assets.append({
                "correlation_id": record_map.get(('ip', ip['id'])),
                "asset_data": {
                    "ip_address": ip['address'],
                    "ip_version": ip['version'],
                    "ports": ports,
                },
            })

    if sub_ids:
        subs = Subdomain.objects.filter(id__in=sub_ids).values(
            "id", "name", "is_resolvable", "cdn_name", "waf_name"
        )
        for s in subs:
            all_assets.append({
                "correlation_id": record_map.get(('subdomain', s['id'])),
                "asset_data": {
                    "name": s['name'],
                    "is_resolvable": s['is_resolvable'],
                },
            })

    if url_ids:
        urls = URLResult.objects.filter(id__in=url_ids).values(
            "id", "url", "status_code", "title"
        )
        for u in urls:
            all_assets.append({
                "correlation_id": record_map.get(('url', u['id'])),
                "asset_data": {
                    "url": u['url'],
                    "status_code": u['status_code'],
                    "title": u['title'],
                },
            })

    return {"list_of_assets": [a for a in all_assets if a['correlation_id']]}


def _build_strategic_context(record) -> Dict[str, Any]:
    if not hasattr(record, 'overview') or not record.overview:
        return {}

    context = {
        "overview_summary": record.overview.summary,
        "overview_knowledge": record.overview.knowledge,
        "overview_techs": record.overview.techs,
        "overview_plan": record.overview.plan,
        "recent_steps_execution": []
    }

    from apps.core.models import Step
    recent_steps = Step.objects.filter(overview=record.overview, status__in=["COMPLETED", "FAILED"]).order_by('-id')[:3]

    for st in reversed(list(recent_steps)):
        step_data = {
            "step_id": st.id,
            "command_template": st.command_template,
            "note": st.note,
        }
        verifications = []
        for v in st.verifications.all():
            out = v.execution_output or ""
            verifications.append({
                "verdict": v.verdict,
                "strategy": v.observation_prompt,
                "output_preview": out[:1000]
            })
        step_data["verifications"] = verifications
        context["recent_steps_execution"].append(step_data)

    if record.triggered_by_step:
        context["triggered_by_step_id"] = record.triggered_by_step.id

    return context


def _execute_ai_batch(asset_type: str, asset_ids: List[int], task_self) -> None:
    from django.utils import timezone
    from django.db import transaction
    from .asset_configs import get_asset_registry

    registry = get_asset_registry()
    if asset_type not in registry:
        raise KeyError(
            f"未知的資產型別 '{asset_type}'，"
            f"可用型別: {list(registry.keys())}"
        )

    config = registry[asset_type]
    Model = config.analysis_model

    logger.info(
        f"Task {task_self.request.id}: 開始處理 [{asset_type}] 批次，"
        f"數量: {len(asset_ids)}。"
    )

    with transaction.atomic():
        analysis_qs = Model.objects.filter(
            **{f"{config.asset_id_field}__in": asset_ids}, status="PENDING"
        )
        analysis_ids = list(analysis_qs.values_list("id", flat=True))

        if not analysis_ids:
            logger.warning(f"[{asset_type}] 沒有找到 PENDING 分析記錄，任務結束。")
            return

        analysis_qs.update(status="RUNNING")
        analysis_records = list(Model.objects.filter(id__in=analysis_ids))

    analysis_ids = [r.id for r in analysis_records]

    try:
        data_payload = config.data_fetcher(asset_ids)
        if not data_payload.get("list_of_assets"):
            logger.warning(f"[{asset_type}] 未能提取到任何情報，任務終止。")
            Model.objects.filter(id__in=analysis_ids).update(
                status="FAILED", error_message="Failed to fetch asset data."
            )
            return

        for asset in data_payload["list_of_assets"]:
            correlation_id = asset["correlation_id"]
            record = next((r for r in analysis_records if config.get_asset_id(r) == correlation_id), None)
            if record:
                asset["strategic_context"] = _build_strategic_context(record)

        from django.contrib.auth import get_user_model
        from apps.ai_assistant.helpers.use_cases import create_thread
        from apps.analyze_ai.assistants import InitialAnalyzerAgent

        User = get_user_model()
        system_user = User.objects.first()
        if not system_user:
            system_user = User.objects.create(username="system_auto_ai")

        assistant = InitialAnalyzerAgent()
        input_message = json.dumps(data_payload, indent=2)

        thread = create_thread(
            name=f"{asset_type.upper()} Analysis Batch - {len(asset_ids)} assets",
            user=system_user,
            assistant_id=assistant.id
        )

        logger.info(f"[{asset_type}] 已建立 Thread #{thread.id}，呼叫 Agent: {assistant.name}")
        output = assistant.run(input_message, thread_id=thread.id)

        try:
            if isinstance(output, dict):
                ai_response = output
            else:
                ai_response = json.loads(output)
        except json.JSONDecodeError as e:
            logger.error(f"[{asset_type}] Agent 返回非預期的 JSON 解析錯誤: {e}. Output was:\n{output}")
            ai_response = None
            last_exception = e

        if not ai_response:
            error_msg = f"[{asset_type}] Agent 執行異常或返回空數據。"
            logger.error(error_msg)
            Model.objects.filter(id__in=analysis_ids).update(
                status="FAILED", error_message=error_msg
            )
            if hasattr(locals(), 'last_exception') and last_exception:
                task_self.retry(exc=last_exception)
            return

        analysis_results = ai_response.get("analysis_results", [])
        logger.info(f"[{asset_type}] 收到 {len(analysis_results)} 條 AI 分析結果。")

        if not analysis_results:
            logger.warning(f"[{asset_type}] 未收到任何 AI 分析結果，任務終止。")
            Model.objects.filter(id__in=analysis_ids).update(
                status="FAILED", error_message="No AI analysis results received."
            )
            logger.warning(f"原始 AI 回應: {ai_response}")
            return

        analysis_map = config.build_analysis_map(analysis_records)
        records_to_update = []

        for result in analysis_results:
            correlation_id = result.get("correlation_id")
            record = analysis_map.get(correlation_id)
            if not record:
                logger.warning(
                    f"[{asset_type}] AI 返回未知 correlation_id: "
                    f"{correlation_id}，已忽略。"
                )
                continue

            for result_field in config.result_fields:
                if result_field == "status":
                    record.status = "COMPLETED"
                elif result_field == "completed_at":
                    record.completed_at = timezone.now()
                else:
                    setattr(record, result_field, result.get(result_field))

            record.raw_response = result
            records_to_update.append(record)

        if records_to_update:
            Model.objects.bulk_update(records_to_update, config.result_fields)
            logger.info(
                f"[{asset_type}] 成功更新 {len(records_to_update)} 條分析記錄。"
            )

        for record in records_to_update:
            if record.overview:
                knowledge = record.overview.knowledge or {}
                entry_key = f"{asset_type}_{record.id}"
                knowledge[entry_key] = {
                    "summary": getattr(record, "summary", ""),
                    "inferred_purpose": getattr(record, "inferred_purpose", ""),
                    "timestamp": timezone.now().isoformat()
                }
                record.overview.knowledge = knowledge
                record.overview.save(update_fields=["knowledge", "updated_at"])

    except Exception as e:
        error_msg = f"[{asset_type}] 批次處理發生未知錯誤: {e}"
        logger.exception(error_msg)
        analysis_qs.update(status="FAILED", error_message=str(e))
        task_self.retry(exc=e)
