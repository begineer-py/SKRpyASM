# apps/targets/api.py
# 目標（Target）與種子（Seed）管理 API

import logging
from typing import List
from ninja import Router
from ninja.errors import HttpError
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from apps.core.models import Target, Seed
from .schemas import (
    TargetSchema,
    CreateTargetSchema,
    UpdateTargetSchema,
    SeedSchema,
    AddSeedSchema,
)

# 導入日誌與路由配置
logger = logging.getLogger(__name__)
router = Router(tags=["Targets & Seeds (Configuration)"])

# ==========================================
# Target Management (配置目標)
# ==========================================


@router.get("/list", response=List[TargetSchema])
async def list_targets(request):
    """列出所有目標專案"""
    return [t async for t in Target.objects.all()]


@router.post("/", response=TargetSchema)
async def create_target(request, payload: CreateTargetSchema):
    """創建一個新目標"""
    try:
        # 使用 acreate 異步創建
        target = await Target.objects.acreate(**payload.dict())
        return target
    except Exception as e:
        logger.error(f"創建目標失敗: {e}")
        raise HttpError(400, f"創建失敗，目標名稱可能重複: {e}")


@router.get("/{target_id}", response=TargetSchema)
async def get_target(request, target_id: int):
    """獲取單個目標詳情"""
    try:
        return await Target.objects.aget(id=target_id)
    except ObjectDoesNotExist:
        raise HttpError(404, "目標不存在")


@router.put("/{target_id}", response=TargetSchema)
async def update_target(request, target_id: int, payload: UpdateTargetSchema):
    """更新目標資訊"""
    try:
        target = await Target.objects.aget(id=target_id)
        for attr, value in payload.dict(exclude_unset=True).items():
            setattr(target, attr, value)
        await target.asave()
        return target
    except ObjectDoesNotExist:
        raise HttpError(404, "目標不存在")


@router.delete("/{target_id}", response={204: None})
async def delete_target(request, target_id: int):
    """刪除目標 (及其下所有種子和資產)"""
    try:
        target = await Target.objects.aget(id=target_id)
        await target.adelete()
        return 204
    except ObjectDoesNotExist:
        raise HttpError(404, "目標不存在")


# ==========================================
# Seed Management (配置種子)
# ==========================================


@router.post("/{target_id}/seeds", response=SeedSchema)
async def add_seed_to_target(request, target_id: int, payload: AddSeedSchema):
    """
    為指定目標添加掃描種子 (Domain/IP/URL)。
    """
    try:
        # 1. 確保目標存在
        target = await Target.objects.aget(id=target_id)

        # 2. 創建種子 (注意：Seed 有 unique_together 約束，需處理重複)
        seed = await Seed.objects.acreate(target=target, **payload.dict())
        return seed

    except ObjectDoesNotExist:
        raise HttpError(404, "目標 ID 不存在")
    except Exception as e:
        # 通常是捕獲 IntegrityError (重複添加)
        logger.warning(f"添加種子失敗: {e}")
        raise HttpError(400, f"添加種子失敗，可能已存在: {e}")


@router.get("/{target_id}/seeds", response=List[SeedSchema])
async def list_target_seeds(request, target_id: int):
    """
    列出指定目標下的所有種子。
    """
    # 這裡我們確認目標存在，然後撈取種子
    try:
        target = await Target.objects.aget(id=target_id)
        # Django 的 related_name="seeds" 讓我們可以用 target.seeds.all()
        # 在異步環境下，我们需要这样迭代
        seeds = [s async for s in target.seeds.all()]
        return seeds
    except ObjectDoesNotExist:
        raise HttpError(404, "目標不存在")


@router.delete("/seeds/{seed_id}", response={204: None})
async def delete_seed(request, seed_id: int):
    """刪除一個種子"""
    try:
        seed = await Seed.objects.aget(id=seed_id)
        await seed.adelete()
        return 204
    except ObjectDoesNotExist:
        raise HttpError(404, "種子不存在")
