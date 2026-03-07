# subdomain_finder/schemas.py (靈活版本)

from ninja import Schema, ModelSchema
from typing import Optional, List
from apps.core.models import SubfinderScan
from apps.core.models import Subdomain, IP
from ninja import Field


class DomainReconTriggerSchema(Schema):
    """觸發 DOMAIN 偵察鏈的請求體"""

    seed_id: int
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
        fields = ["id", "ipv4", "ipv6"]


# 2. 定義單個子域名的詳細情報 Schema
class SubdomainSchema(ModelSchema):
    # 如果 ip 為空，返回 null
    ip: Optional[IPSchema] = None

    # 映射 sources_text
    sources: str = Field(..., alias="sources_text")

    # 映射 cname (雖然名字一樣，但顯式聲明更清晰)
    # 如果 cname 為空字符串，這裡會原樣返回
    cname: Optional[str] = None

    class Meta:
        model = Subdomain
        fields = [
            "id",
            "name",
            "is_active",
            "sources_text",
            "cname",  # <-- 確保這裡有加
            "dns_records",
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
