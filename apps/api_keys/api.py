from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from .models import APIKey
from .schemas import APIKeyIn, APIKeyOut, APIKeyUpdate

router = Router(tags=["API Keys"])

@router.post("/", response=APIKeyOut)
def create_api_key(request, data: APIKeyIn):
    api_key = APIKey.objects.create(**data.dict())
    return api_key

@router.get("/", response=List[APIKeyOut])
def list_api_keys(request):
    return APIKey.objects.all()

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
