"""
apps/analyze_ai/tasks/asset_configs.py

AssetAnalysisConfig 工廠配置（Factory Registry）

每種資產型別（IP / Subdomain / URL）的差異部分被集中定義在此，
讓通用的 AI 分析執行器 `_execute_ai_batch` 可以完全共用同一套流程。

==============================
使用方式：
    from apps.analyze_ai.tasks.asset_configs import ASSET_REGISTRY
    config = ASSET_REGISTRY["ip"]
    model   = config.analysis_model          # IPAIAnalysis
    ids     = config.get_ids(record_qs)      # 從 QuerySet 取得資產 ID
    data    = config.data_fetcher([1, 2, 3]) # 透過 GraphQL 取資料
    prompt  = config.prompt_loader()         # 讀取對應 Prompt 模板
==============================
"""

from dataclasses import dataclass, field
from typing import Callable, List, Type

from django.db.models import Model


@dataclass
class AssetAnalysisConfig:
    """
    定義單一資產型別的分析配置。

    Attributes:
        analysis_model:  對應的 AIAnalysis Model（如 IPAIAnalysis）
        asset_id_field:  Model 上指向資產的 FK 欄位名稱（如 "ip_id"）
        asset_fk_field:  FK 欄位的邏輯名稱，用於 analysis_map key（如 "ip"）
        data_fetcher:    接受 List[int] 並回傳 GraphQL 資產資料的函式
        prompt_loader:   無參數、回傳 prompt 字串的函式
        result_fields:   bulk_update 時需要更新的欄位名稱列表
    """

    analysis_model: Type[Model]
    asset_id_field: str
    asset_fk_field: str
    data_fetcher: Callable[[List[int]], dict]
    prompt_loader: Callable[[], str]
    result_fields: List[str] = field(default_factory=list)

    def get_asset_id(self, record) -> int:
        """從分析記錄取得對應資產的 ID（如 record.ip_id）。"""
        return getattr(record, self.asset_id_field)

    def build_analysis_map(self, records: list) -> dict:
        """建立 { asset_id -> record } 的對應字典，方便後續填值。"""
        return {self.get_asset_id(r): r for r in records}


# =============================================================================
# 延遲匯入（避免循環 import 與啟動時的 Django ORM 未就緒問題）
# =============================================================================

def _build_registry() -> dict:
    """
    在第一次使用時才建立 ASSET_REGISTRY，避免 Django AppRegistry 未就緒時報錯。
    """
    from apps.core.models import InitialAIAnalysis, IPAIAnalysis, SubdomainAIAnalysis, URLAIAnalysis
    from .common import (
        fetch_initial_data_for_batch,
        fetch_ip_data_for_batch,
        fetch_subdomain_data_for_batch,
        fetch_url_data_for_batch,
        load_initial_prompt_template,
        load_prompt_template,
        load_subdomain_prompt_template,
        load_url_prompt_template,
    )

    return {
        "initial": AssetAnalysisConfig(
            analysis_model=InitialAIAnalysis,
            asset_id_field="id",  # InitialAIAnalysis itself doesn't have an asset_id_field in the same way, need to be careful
            asset_fk_field="initial", 
            data_fetcher=fetch_initial_data_for_batch,
            prompt_loader=load_initial_prompt_template,
            result_fields=[
                "summary",
                "inferred_purpose",
                "worth_deep_analysis",
                "raw_response",
                "status",
                "completed_at",
            ],
        ),
        "ip": AssetAnalysisConfig(
            analysis_model=IPAIAnalysis,
            asset_id_field="ip_id",
            asset_fk_field="ip",
            data_fetcher=fetch_ip_data_for_batch,
            prompt_loader=load_prompt_template,
            result_fields=[
                "summary",
                "inferred_purpose",
                "port_analysis_summary",
                "potential_vulnerabilities",
                "recommended_actions",
                "command_actions",
                "raw_response",
                "status",
                "completed_at",
            ],
        ),
        "subdomain": AssetAnalysisConfig(
            analysis_model=SubdomainAIAnalysis,
            asset_id_field="subdomain_id",
            asset_fk_field="subdomain",
            data_fetcher=fetch_subdomain_data_for_batch,
            prompt_loader=load_subdomain_prompt_template,
            result_fields=[
                "summary",
                "inferred_purpose",
                "business_impact",
                "tech_stack_summary",
                "potential_vulnerabilities",
                "recommended_actions",
                "command_actions",
                "raw_response",
                "status",
                "completed_at",
            ],
        ),
        "url": AssetAnalysisConfig(
            analysis_model=URLAIAnalysis,
            asset_id_field="url_result_id",
            asset_fk_field="url_result",
            data_fetcher=fetch_url_data_for_batch,
            prompt_loader=load_url_prompt_template,
            result_fields=[
                "summary",
                "inferred_purpose",
                "potential_vulnerabilities",
                "recommended_actions",
                "command_actions",
                "extracted_entities",
                "raw_response",
                "status",
                "completed_at",
            ],
        ),
    }


# 使用 __getattr__ 的懶加載 proxy：模組首次被 import 時並不執行 _build_registry，
# 只有當程式碼存取 ASSET_REGISTRY 時才觸發建立，確保 Django ORM 已就緒。
_registry_cache: dict | None = None


def get_asset_registry() -> dict:
    """
    取得全域 ASSET_REGISTRY。
    - 第一次呼叫：建立並快取
    - 後續呼叫：直接回傳快取
    """
    global _registry_cache
    if _registry_cache is None:
        _registry_cache = _build_registry()
    return _registry_cache


# 提供直接匯入的別名，讓呼叫者可以用 `from ... import ASSET_REGISTRY`
# 但實際上是一個函式，可確保延遲初始化。
# 若需要靜態存取，請呼叫 get_asset_registry()。
ASSET_REGISTRY = get_asset_registry
