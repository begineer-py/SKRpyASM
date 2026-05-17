from dataclasses import dataclass, field
from typing import Callable, List, Type

from django.db.models import Model


@dataclass
class AssetAnalysisConfig:
    analysis_model: Type[Model]
    asset_id_field: str
    asset_fk_field: str
    data_fetcher: Callable[[List[int]], dict]
    prompt_loader: Callable[[], str]
    result_fields: List[str] = field(default_factory=list)

    def get_asset_id(self, record) -> int:
        return getattr(record, self.asset_id_field)

    def build_analysis_map(self, records: list) -> dict:
        return {self.get_asset_id(r): r for r in records}


def _build_registry() -> dict:
    from apps.core.models import InitialAIAnalysis
    from .common import (
        fetch_initial_data_for_batch,
        load_initial_prompt_template,
    )

    return {
        "initial": AssetAnalysisConfig(
            analysis_model=InitialAIAnalysis,
            asset_id_field="id",
            asset_fk_field="initial",
            data_fetcher=fetch_initial_data_for_batch,
            prompt_loader=load_initial_prompt_template,
            result_fields=[
                "summary",
                "inferred_purpose",
                "worth_deep_analysis",
                "risk_score",
                "raw_response",
                "status",
                "completed_at",
            ],
        ),
    }


_registry_cache: dict | None = None


def get_asset_registry() -> dict:
    global _registry_cache
    if _registry_cache is None:
        _registry_cache = _build_registry()
    return _registry_cache


ASSET_REGISTRY = get_asset_registry
