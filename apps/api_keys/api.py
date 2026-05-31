from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from django.http import FileResponse
import os
from apps.core.models.api_key import APIKey
from .schemas import APIKeyIn, APIKeyOut, APIKeyUpdate
from .utils import (
    get_active_api_keys,
    generate_subfinder_config,
    generate_amass_config,
    generate_gau_config,
    generate_nuclei_secrets,
)

SUPPORTED_SERVICES = [
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
]

router = Router(tags=["API Keys"])


@router.get("/supported-services", response=List[str])
def list_supported_services(request):
    """回傳支援的服務名稱列表 (供前端下拉選單使用)。"""
    return SUPPORTED_SERVICES

@router.post("/", response=APIKeyOut)
def create_api_key(request, data: APIKeyIn):
    api_key = APIKey.objects.create(**data.dict())
    return api_key

@router.get("/", response=List[APIKeyOut])
def list_api_keys(request):
    return APIKey.objects.all()

@router.post("/bulk", response=List[APIKeyOut])
def bulk_create_api_keys(request, data_list: List[APIKeyIn]):
    """批量匯入多個 API 金鑰 (支援同 service 多個 key)。"""
    created = []
    for data in data_list:
        api_key = APIKey.objects.create(**data.dict())
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


@router.get("/{api_key_id}", response=APIKeyOut)
def get_api_key(request, api_key_id: int):
    return get_object_or_404(APIKey, id=api_key_id)

@router.patch("/{api_key_id}", response=APIKeyOut)
def update_api_key(request, api_key_id: int, data: APIKeyUpdate):
    api_key = get_object_or_404(APIKey, id=api_key_id)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(api_key, attr, value)
    api_key.save()
    return api_key

@router.delete("/{api_key_id}")
def delete_api_key(request, api_key_id: int):
    api_key = get_object_or_404(APIKey, id=api_key_id)
    api_key.delete()
    return {"success": True}
