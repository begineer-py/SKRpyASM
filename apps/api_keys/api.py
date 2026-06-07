from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from django.http import FileResponse
import logging
import os
from apps.core.models.api_key import APIKey
from .models import AgentLLMConfig
from .schemas import (
    APIKeyIn,
    APIKeyOut,
    APIKeyBriefOut,
    APIKeyUpdate,
    AgentLLMConfigIn,
    AgentLLMConfigOut,
    AgentLLMConfigUpdate,
    AgentEffectiveConfigOut,
    TestLLMIn,
    TestLLMOut,
)
from .utils import (
    get_active_api_keys,
    generate_subfinder_config,
    generate_amass_config,
    generate_gau_config,
    generate_nuclei_secrets,
)

SUPPORTED_SERVICES = [
    # --- 安全掃描服務 ---
    "shodan",
    "securitytrails",
    "censys",
    "chaos",
    "dnsdb",
    "virustotal",
    "binaryedge",
    "zoomeye",
    "fofa",
    "github",
    "hunter",
    "urlscan",
    "alienvault",
    "threatcrowd",
    "passivetotal",
    "riskiq",
    "intelx",
    "fullhunt",
    "quake",
    "netlas",
    "publicwww",
    "nvd",
    # --- AI 提供商密鑰 ---
    "openai",
    "anthropic",
    "mistral",
    "gemini",
    "deepseek",
    "ollama",
    "langchain",
    "vulncheck",
]

router = Router(tags=["API Keys"])
logger = logging.getLogger(__name__)


# ── APIKey CRUD ────────────────────────────────────────────────────────────────

@router.get("/supported-services", response=List[str])
def list_supported_services(request):
    """回傳支援的服務名稱列表 (供前端下拉選單使用)。"""
    return SUPPORTED_SERVICES

@router.post("/", response=APIKeyOut)
def create_api_key(request, data: APIKeyIn):
    api_key = APIKey.objects.create(**data.model_dump())
    return api_key

@router.get("/", response=List[APIKeyOut])
def list_api_keys(request):
    return APIKey.objects.all()

@router.post("/bulk", response=List[APIKeyOut])
def bulk_create_api_keys(request, data_list: List[APIKeyIn]):
    """批量匯入多個 API 金鑰 (支援同 service 多個 key)。"""
    created = []
    for data in data_list:
        api_key = APIKey.objects.create(**data.model_dump())
        created.append(api_key)
    return created


@router.get("/download")
def download_config(request, tool: str):
    """
    下載指定工具的配置檔案。
    tool: subfinder | amass | gau | nuclei
    """
    keys = get_active_api_keys()
    if tool == "subfinder":
        path = generate_subfinder_config(keys)
        filename = "subfinder-provider-config.yaml"
    elif tool == "amass":
        path = generate_amass_config(keys)
        filename = "amass-config.ini"
    elif tool == "gau":
        path = generate_gau_config(keys)
        filename = "gau-config.toml"
    elif tool == "nuclei":
        path = generate_nuclei_secrets(keys)
        filename = "nuclei-secrets.yaml"
    else:
        return {"error": "Unsupported tool. Use: subfinder, amass, gau, nuclei"}

    try:
        response = FileResponse(open(path, "rb"), as_attachment=True, filename=filename)
        return response
    finally:
        if os.path.exists(path):
            os.remove(path)


# ── AgentLLMConfig CRUD ────────────────────────────────────────────────────────

def _build_effective_config(agent_id: str, db_cfg) -> AgentEffectiveConfigOut:
    """合并視圖：DB（最高）> 全域默認。"""
    from apps.auto.settings import AutoAppConfig

    effective = AutoAppConfig.get_agent_config(agent_id)

    db_out = None
    if db_cfg is not None:
        # 顯式構造，避免 Pydantic v2 廢棄的 from_orm 造成 model_dump 錯誤
        key_ref = None
        if db_cfg.api_key_ref_id is not None:
            try:
                kr = db_cfg.api_key_ref
                key_ref = APIKeyBriefOut(
                    id=kr.id,
                    service_name=kr.service_name,
                    description=kr.description,
                )
            except Exception as e:
                logger.warning(
                    "_build_effective_config: api_key_ref_id=%s 解析失敗 agent='%s': %s",
                    db_cfg.api_key_ref_id, agent_id, e,
                )
        db_out = AgentLLMConfigOut(
            id=db_cfg.id,
            agent_id=db_cfg.agent_id,
            provider=db_cfg.provider,
            model_name=db_cfg.model_name,
            temperature=db_cfg.temperature,
            api_base_url=db_cfg.api_base_url,
            api_key_ref=key_ref,
            is_active=db_cfg.is_active,
            description=db_cfg.description,
            created_at=db_cfg.created_at,
            updated_at=db_cfg.updated_at,
        )

    return AgentEffectiveConfigOut(
        agent_id=agent_id,
        effective_provider=effective["provider"],
        effective_model=effective["model"],
        effective_temperature=effective["temperature"],
        effective_api_base_url=effective.get("api_base_url"),
        has_db_config=db_cfg is not None,
        has_env_override=False,   # env var per-agent 已移除，狀態只有 DB / DEFAULT
        db_config=db_out,
    )


@router.get("/agent-configs/", response=List[AgentEffectiveConfigOut])
def list_agent_effective_configs(request):
    """
    回傳所有已知 Agent 的有效配置（DB + env var + 全域默認合并視圖）。
    agent 清單由 agent_registry.discover_agent_ids() 自動發現：
    新增含有 assistant_id 的 AIAssistant 子類後自動出現，無需手動維護清單。
    """
    from apps.auto.agent_registry import discover_agent_ids

    known_ids = discover_agent_ids()
    db_map = {
        cfg.agent_id: cfg
        for cfg in AgentLLMConfig.objects.filter(
            agent_id__in=known_ids
        ).select_related("api_key_ref")
    }

    return [
        _build_effective_config(agent_id, db_map.get(agent_id))
        for agent_id in known_ids
    ]


@router.get("/agent-configs/db/", response=List[AgentLLMConfigOut])
def list_agent_db_configs(request):
    """回傳僅在 DB 中有記錄的 Agent 配置（原始 DB 值，不合并默認值）。"""
    return AgentLLMConfig.objects.all().select_related("api_key_ref")


@router.post("/agent-configs/", response=AgentLLMConfigOut)
def create_agent_config(request, data: AgentLLMConfigIn):
    """為指定 Agent 新建 LLM 配置。若已存在請改用 PUT。"""
    api_key_ref = None
    if data.api_key_id is not None:
        api_key_ref = get_object_or_404(APIKey, id=data.api_key_id)

    cfg = AgentLLMConfig.objects.create(
        agent_id=data.agent_id,
        provider=data.provider,
        model_name=data.model_name,
        temperature=data.temperature,
        api_base_url=data.api_base_url,
        api_key_ref=api_key_ref,
        is_active=data.is_active,
        description=data.description,
    )
    return cfg


@router.get("/agent-configs/{agent_id}", response=AgentEffectiveConfigOut)
def get_agent_effective_config(request, agent_id: str):
    """取得指定 Agent 的有效配置（合并視圖）。"""
    db_cfg = (
        AgentLLMConfig.objects
        .filter(agent_id=agent_id)
        .select_related("api_key_ref")
        .first()
    )
    return _build_effective_config(agent_id, db_cfg)


@router.put("/agent-configs/{agent_id}", response=AgentLLMConfigOut)
def upsert_agent_config(request, agent_id: str, data: AgentLLMConfigUpdate):
    """
    Upsert：若 DB 已有此 agent_id 的記錄則更新，否則新建。
    僅更新請求中明確傳入的欄位（非 None 才覆蓋）。
    """
    cfg, _ = AgentLLMConfig.objects.get_or_create(agent_id=agent_id)

    update_data = data.model_dump(exclude_unset=True)  # Pydantic v2 compatible

    if "api_key_id" in update_data:
        key_id = update_data.pop("api_key_id")
        cfg.api_key_ref = get_object_or_404(APIKey, id=key_id) if key_id is not None else None

    for attr, value in update_data.items():
        setattr(cfg, attr, value)

    cfg.save()
    # select_related 確保 api_key_ref 已載入，避免序列化時觸發額外查詢
    cfg = AgentLLMConfig.objects.select_related("api_key_ref").get(id=cfg.id)
    return cfg


@router.delete("/agent-configs/{agent_id}")
def delete_agent_config(request, agent_id: str):
    """刪除 DB 中的 Agent 配置記錄，使其回退到 env var 或全域默認值。"""
    cfg = get_object_or_404(AgentLLMConfig, agent_id=agent_id)
    cfg.delete()
    return {"success": True, "message": f"Agent '{agent_id}' config deleted; reverted to env/default."}


# ── LLM 連線測試端點 ──────────────────────────────────────────────────────────

@router.post("/test-llm", response=TestLLMOut)
def test_llm_connection(request, data: TestLLMIn):
    """
    測試任意 LLM 配置的連線（不需已存 DB 記錄）。
    用於 Edit Modal 儲存前先驗證配置是否有效。
    """
    import time
    from apps.core.llms import get_llm_instance
    from langchain_core.messages import HumanMessage

    api_key_val = None
    if data.api_key_id is not None:
        key_obj = get_object_or_404(APIKey, id=data.api_key_id)
        api_key_val = key_obj.key_value
    else:
        try:
            from apps.api_keys.utils import get_ai_provider_key
            api_key_val = get_ai_provider_key(data.provider)
        except Exception:
            pass

    try:
        llm = get_llm_instance(
            model_name=data.model_name or None,
            temperature=data.temperature,
            provider=data.provider,
            _override_api_key=api_key_val,
            _override_api_base=data.api_base_url or None,
        )
        start = time.monotonic()
        response = llm.invoke([HumanMessage(content="Reply with exactly one word: OK")])
        latency = int((time.monotonic() - start) * 1000)
        return TestLLMOut(
            success=True,
            message=str(response.content)[:200],
            latency_ms=latency,
            model_used=data.model_name,
            provider_used=data.provider,
        )
    except Exception as e:
        return TestLLMOut(
            success=False,
            message=str(e)[:500],
            latency_ms=None,
            model_used=data.model_name,
            provider_used=data.provider,
        )


@router.post("/agent-configs/{agent_id}/test", response=TestLLMOut)
def test_agent_config(request, agent_id: str):
    """
    使用 Agent 的當前有效配置（DB > env > 默認）進行連線測試。
    用於 Agent 卡片上的快速測試。
    """
    import time
    from apps.auto.settings import AutoAppConfig
    from apps.core.llms import get_llm_instance
    from langchain_core.messages import HumanMessage

    cfg = AutoAppConfig.get_agent_config(agent_id)
    try:
        llm = get_llm_instance(
            model_name=cfg["model"],
            temperature=cfg["temperature"],
            provider=cfg["provider"],
            _override_api_key=cfg.get("api_key"),
            _override_api_base=cfg.get("api_base_url"),
        )
        start = time.monotonic()
        response = llm.invoke([HumanMessage(content="Reply with exactly one word: OK")])
        latency = int((time.monotonic() - start) * 1000)
        return TestLLMOut(
            success=True,
            message=str(response.content)[:200],
            latency_ms=latency,
            model_used=cfg["model"],
            provider_used=cfg["provider"],
        )
    except Exception as e:
        return TestLLMOut(
            success=False,
            message=str(e)[:500],
            latency_ms=None,
            model_used=cfg.get("model"),
            provider_used=cfg["provider"],
        )


# ── APIKey 單筆 CRUD（必須放在所有具名路由之後，避免 /{id} 攔截其他路徑）────────
@router.get("/{api_key_id}", response=APIKeyOut)
def get_api_key(request, api_key_id: int):
    return get_object_or_404(APIKey, id=api_key_id)

@router.patch("/{api_key_id}", response=APIKeyOut)
def update_api_key(request, api_key_id: int, data: APIKeyUpdate):
    api_key = get_object_or_404(APIKey, id=api_key_id)
    for attr, value in data.model_dump(exclude_unset=True).items():
        setattr(api_key, attr, value)
    api_key.save()
    return api_key

@router.delete("/{api_key_id}")
def delete_api_key(request, api_key_id: int):
    api_key = get_object_or_404(APIKey, id=api_key_id)
    api_key.delete()
    return {"success": True}
