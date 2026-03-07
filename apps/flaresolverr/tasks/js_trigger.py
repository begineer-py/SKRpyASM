# --- 全局變數，用來存放模型 ---

from transformers import AutoModelForSequenceClassification, AutoTokenizer
from c2_core.config.utils import sanitize_for_db
from c2_core.config.config import Config
from apps.flaresolverr.security_parser import SecurityAnalyzer
import torch
import chompjs
import logging
import sys
from celery.signals import worker_process_init
from celery import shared_task
from django.db import transaction
from apps.core.models import ExtractedJS, JavaScriptFile, JSONObject, Form, URLResult
from c2_core.config.logging import log_function_call
from apps.flaresolverr.utils import (
    downloader,
    get_score_batch,
    save_params_to_db,
    get_target_from_js_file,
    sync_previous_results,
    walk,
)
import json
from apps.flaresolverr.json_object.js_json_extractor import JSJsonExtractor

logger = logging.getLogger(__name__)

# Model imports
MODEL_PATH = Config.MODEL_PATH
AI_TOKENIZER = None
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
AI_MODEL = None


# --- 核心：進程啟動時加載模型 ---
@worker_process_init.connect
def init_ai_model(**kwargs):
    cmd_args = " ".join(sys.argv)
    if "ai_queue" not in cmd_args:
        logger.info("[!] 跳過 AI 模型加載 (非 AI Worker)")
        return

    logger.info(f"[*] Celery Worker 啟動，正在將 AI 模型加載至 {DEVICE}...")
    global AI_MODEL
    global AI_TOKENIZER
    AI_TOKENIZER = AutoTokenizer.from_pretrained(MODEL_PATH)
    AI_MODEL = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(DEVICE)
    AI_MODEL.eval()

    logger.info("[✓] AI 模型已長駐顯存，準備開搞.")


# tasks.py
@shared_task(name="tasks.perform_js_scan")
@log_function_call()
def perform_js_scan(object_id, source_type):
    try:
        target_obj = None
        if source_type == "external":
            download_external_js(object_id)  # 這裡會填入 content 並產生 hash
            target_obj = JavaScriptFile.objects.get(id=object_id)
            fk_kwargs = {"which_javascript_file_id": object_id}

        else:
            target_obj = ExtractedJS.objects.get(id=object_id)
            fk_kwargs = {"which_extracted_js_id": object_id}

        # 2. 內容空檢查
        if not target_obj.content:
            target_obj.is_analyzed = True
            target_obj.save(update_fields=["is_analyzed"])
            return "Empty content."
        target = None
        if source_type == "external":
            target = get_target_from_js_file(target_obj)
        else:
            # 使用 select_related 減少查詢，並獲取 URL 物件
            target_obj = ExtractedJS.objects.select_related("which_url").get(
                id=object_id
            )

            url_record = target_obj.which_url
            if not url_record:
                logger.error(
                    f"錯誤：ExtractedJS ID:{object_id} 根本沒有關聯的 URLResult (which_url_id 是空的)"
                )
                target = None
            else:
                # 關鍵點：檢查資料庫層面的原始 ID，不要透過 ORM 自動抓物件
                raw_target_id = url_record.target_id  # 直接讀取資料庫欄位
                target = url_record.target

                logger.info(
                    f"DEBUG: URL_ID={url_record.id}, Raw_Target_ID_in_DB={raw_target_id}, ORM_Target={target}"
                )

        if not target:
            # 這裡現在能精確知道是哪個環節斷了
            logger.warning(f"JS 溯源失敗 (ID: {object_id})。")
        # 如果真的找不到 Target (孤兒 JS)
        if not target:
            logger.warning(
                f"JS 溯源失敗 (ID: {object_id})。標記為已分析以避免重複掃描。"
            )
            target_obj.is_analyzed = True
            if hasattr(target_obj, "status"):
                target_obj.status = "SKIPPED"  # 標記為跳過
            target_obj.save()
            return "Target not found."
        # --- 核心去重邏輯 ---
        # 檢查資料庫中是否已有相同的內容被分析過了
        content_hash = target_obj.content_hash
        already_done = None

        # 優先找已經分析過的同類或異類物件
        already_done = (
            JavaScriptFile.objects.filter(
                content_hash=content_hash, is_analyzed=True
            ).first()
            or ExtractedJS.objects.filter(
                content_hash=content_hash, is_analyzed=True
            ).first()
        )

        if already_done:
            logger.info(
                f"發現重複內容 (Hash: {content_hash})，直接複製結果並標記完成。"
            )

            # 1. 如果有 Target，將之前的分析結果(Endpoint)關聯到目前的 Target
            # 這裡調用一個專門處理「複製關聯」的函式
            sync_previous_results(target_obj, already_done)

            # 2. 標記目前物件為已分析，避免進入 AI 隊列
            target_obj.is_analyzed = True
            if hasattr(target_obj, "status"):
                target_obj.status = "SKIPPED"
            target_obj.save()
            return f"Skipped due to duplicate content: {content_hash}"

        # --- 執行掃描 (順序很重要) ---

        # Step 1: 參數掃描 (Param Scan)
        # 先跑這個，因為它需要讀取 raw content。
        # 如果先跑 AI Scan，External JS 的 content 可能會被清空。
        logger.info(f"啟動 Param Scan -> {object_id}")
        param_scan(target_obj.content, source_type, object_id, fk_kwargs)

        # Step 2: AI 結構掃描 (AI Scan)
        logger.info(f"啟動 AI Scan -> {object_id}")
        ai_scan(object_id, source_type, target_obj.content, fk_kwargs)

        return f"JS Analysis Completed for {source_type} ID {object_id}"

    except Exception as e:
        logger.error(f"perform_js_scan 流程失敗: {e}", exc_info=True)


# --- 3. 子任務：下載 ---


@shared_task(name="tasks.download_external_js", queue="default")
def download_external_js(js_file_id):
    """
    負責下載外部 JS，支援 Requests 和 FlareSolverr
    """
    try:
        js_obj = JavaScriptFile.objects.get(id=js_file_id)
        if js_obj.status == "ANALYZED":
            return f"Skipped {js_obj.src} (Already Analyzed)"
        if not js_obj.src:
            logger.info(f"Skipped {js_obj.src} (No URL)")
            return f"Skipped {js_obj.src} (No URL)"
        js_url = js_obj.src
        content = downloader(js_url)

        if content:
            js_obj.content = content
            js_obj.status = "DOWNLOADED"
            js_obj.save()
            # 注意：這裡不再自動觸發 ai_scan，改由 perform_js_scan 統一調度
            return f"Downloaded: {js_url}"
        else:
            raise Exception("All download methods failed")

    except Exception as e:
        # 下載失敗標記為已分析(避免卡死循環)，但內容是空的
        JavaScriptFile.objects.filter(id=js_file_id).update(is_analyzed=True)
        return f"Final Failure: {e}"


# --- 4. 子任務：AI 結構掃描 ---


@log_function_call()
@shared_task(name="tasks.ai_scan", queue="ai_queue")
def ai_scan(object_id, source_type, data, fk_kwargs):
    """
    使用 ChompJS 解析 AST，並用 AI 模型對變數/函數命名進行評分
    """
    try:
        # 1. 解析 JS 物件 (chompjs)
        JsonExtractor = JSJsonExtractor()
        parsed_data = JsonExtractor.execute(js_code=data)
        logger.info(f"Parsed Data: {json.dumps(parsed_data, indent=2)}")
        nodes_to_scan = []

        # 注意：chompjs 回傳的是一個 list (多個物件)，所以要對每個物件執行 walk
        if isinstance(parsed_data, list):
            for idx, item in enumerate(parsed_data):
                # 傳入 4 個參數：物件, 路徑, 初始深度, 存放清單
                walk(item, f"root[{idx}]", 0, nodes_to_scan)
        else:
            walk(parsed_data, "root", 0, nodes_to_scan)

        if not nodes_to_scan:
            return {"status": "skipped", "reason": "No JSON objects found"}
        # 2. AI 批量打分
        results = []
        batch_size = 50

        # 檢查模型是否加載
        global AI_MODEL, AI_TOKENIZER, DEVICE
        if AI_MODEL is None:
            # Fallback: 如果這是在同步模式或非 AI Worker 上跑，嘗試臨時加載
            logger.warning("AI Model not loaded globally, loading temporarily...")
            AI_TOKENIZER = AutoTokenizer.from_pretrained(MODEL_PATH)
            AI_MODEL = AutoModelForSequenceClassification.from_pretrained(
                MODEL_PATH
            ).to(DEVICE)
            AI_MODEL.eval()

        for i in range(0, len(nodes_to_scan), batch_size):
            batch = nodes_to_scan[i : i + batch_size]
            scores = get_score_batch(batch, AI_MODEL, AI_TOKENIZER, DEVICE)
            for j, node in enumerate(batch):
                node["score"] = float(scores[j])
                results.append(node)

        # 3. 過濾並儲存 (只存高分特徵)
        logger.info(f"AI 批量打分結果: {results}")
        results = [r for r in results if r["score"] > 0.6]

        allowed_fields = {f.name for f in JSONObject._meta.get_fields()}
        to_create = [
            JSONObject(
                **{k: v for k, v in res.items() if k in allowed_fields}, **fk_kwargs
            )
            for res in results
        ]

        with transaction.atomic():
            JSONObject.objects.bulk_create(to_create)

            # 4. 更新狀態與清理
            if source_type == "inline":
                obj = ExtractedJS.objects.get(id=object_id)
                obj.is_analyzed = True
                obj.save()
            else:
                obj = JavaScriptFile.objects.get(id=object_id)
                obj.is_analyzed = True
                obj.content = ""  # 外部 JS 存完特徵後清空內容以節省空間
                obj.save()

        return {"status": "success", "found_nodes": len(to_create)}

    except Exception as e:
        logger.error(f"JS AI 掃描失敗 (ID: {object_id}, Type: {source_type}): {e}")
        return {"error": str(e)}


# --- 5. 子任務：參數掃描 ---


@log_function_call()
@shared_task(name="tasks.param_scan", queue="default")
def param_scan(js_content, source_type, object_id, fk_kwargs):
    """
    接收 JS 內容，透過 SecurityAnalyzer 分析 Endpoint 與參數，並入庫。
    """
    try:
        base_url = ""
        forms_data = []
        source_obj = None  # 發現來源物件 (URLResult 或 JavaScriptFile)
        target = None  # 歸屬專案

        # 1. 搞定上下文 (Context) 並提取 Target
        if source_type == "external":
            source_obj = JavaScriptFile.objects.get(id=object_id)
            # base_url = source_obj.src
            first_page = source_obj.related_pages.first()
            base_url = first_page.url
            # 使用強大的溯源函式
            target = get_target_from_js_file(source_obj)
            # 如果 JSFile 沒存 target，嘗試從它關聯的頁面拿
            if not target:
                first_page = source_obj.related_pages.first()
                if first_page:
                    target = first_page.target

        elif source_type == "inline":
            ext_js = ExtractedJS.objects.get(id=object_id)
            source_obj = ext_js.which_url  # 這是一個 URLResult 物件
            base_url = source_obj.url
            target = source_obj.target

            # 撈出同頁面的 Forms 增加準確度
            related_forms = Form.objects.filter(which_url=source_obj)
            for f in related_forms:
                forms_data.append(
                    {
                        "action": f.action,
                        "method": f.method,
                        "parameters": f.parameters,
                    }
                )

        if not js_content or not target:
            logger.warning(f"跳過掃描：找不到 Target 歸屬或內容為空 (ID: {object_id})")
            return
        # logger.debug(base_url)
        # logger.debug(forms_data)
        # logger.debug(js_content)
        # 2. 開工：分析 JS
        analyzer = SecurityAnalyzer()
        analysis_result = analyzer.analyze(
            base_url=base_url, js_code=js_content, forms_data=forms_data
        )

        if not analysis_result:
            return "No results found."

        # 提取 endpoints list
        endpoints_list = []
        if isinstance(analysis_result, dict) and "endpoints" in analysis_result:
            endpoints_list = analysis_result["endpoints"]
        elif isinstance(analysis_result, list):
            endpoints_list = analysis_result

        # 3. 入庫：傳入分析結果、Target 以及 來源物件
        saved_count = save_params_to_db(endpoints_list, target, source_obj)

        return f"Param Scan Done. Target: {target.name}, Saved: {saved_count}"

    except Exception as e:
        logger.error(f"Param Scan 炸裂 (ID: {object_id}): {e}", exc_info=True)
        return f"Error: {e}"
