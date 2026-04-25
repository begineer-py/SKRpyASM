# subdomain_finder/schemas.py (靈活版本)

from ninja import Schema, ModelSchema
from typing import Optional, List
from apps.core.models import SubfinderScan
from apps.core.models import Subdomain, IP
from ninja import Field


class DomainReconTriggerSchema(Schema):
    """觸發 DOMAIN 偵察鏈的請求體"""

    seed_id: int
    callback_step_id: Optional[int] = None
    # timeout: Optional[int] = 900 # 如果需要，可以保留 timeout


class SubfinderScanSchema(ModelSchema):
    seed_value: str = None
    target_name: str = None

    class Meta:
        model = SubfinderScan
        fields = [
            "id",
            "which_seed",
            "status",
            "added_count",
            "started_at",
            "completed_at",
            "created_at",
        ]

    @staticmethod
    def resolve_seed_value(obj):
        # 確保查詢時用了 select_related('which_seed')
        return obj.which_seed.value if obj.which_seed else None

    @staticmethod
    def resolve_target_name(obj):
        # 確保查詢時用了 select_related('which_seed__target')
        return (
            obj.which_seed.target.name
            if obj.which_seed and obj.which_seed.target
            else None
        )


# 1. 定義 IP 的 Schema (這是為了嵌套在子域名裡顯示)
class IPSchema(ModelSchema):
    class Meta:
        model = IP
        fields = ["id", "address", "version"]


# 2. 定義單個子域名的詳細情報 Schema
class SubdomainSchema(ModelSchema):
    # 如果 ip 為空，返回 null
    ip: Optional[IPSchema] = None

    # 映射 sources_text
    class Meta:
        model = Subdomain
        fields = [
            "id",
            "name",
            "is_active",
            "sources_text",
            "first_seen",
            "last_seen",
            "created_at",
        ]


# 3. 定義結果集包裝盒 (Wrapper)
class SubdomainResultSetSchema(Schema):
    """
    API 返回的最終格式：包含目標元數據和結果列表
    """

    target_id: int
    target_domain: str
    count: int
    ip: str
    results: List[SubdomainSchema]


class SubdomainResultSetSchemaNoIP(Schema):
    """
    API 返回的最終格式：包含目標元數據和結果列表
    """

    target_id: int
    target_domain: str
    count: int
    results: List[SubdomainSchema]


class SubBruteSchema(Schema):
    sub_id: int
