from ninja import Router
from typing import List, Dict, Any
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from ninja.errors import HttpError
from c2_core.config.logging import log_function_call
import logging
from django.core.exceptions import ValidationError  # <--- 記得導入這個！

from .schemas import (
    PeriodicTaskSchema,
    PeriodicTaskCreateSchema,
    PeriodicTaskUpdateSchema,
    IntervalScheduleSchema,
    CrontabScheduleSchema,
)
from django.shortcuts import get_object_or_404

router = Router()
logger = logging.getLogger(__name__)


# --- 查詢所有定時任務 ---
@log_function_call()
@router.get("/tasks", response=List[PeriodicTaskSchema])
async def list_periodic_tasks(request):  # 操！異步化！
    """
    列出所有已配置的週期性任務，並手動構建字典以匹配 Schema。
    """
    tasks_queryset = PeriodicTask.objects.select_related(
        "interval", "crontab", "solar", "clocked"
    ).all()

    results = []
    # 操！異步化！
    async for task in tasks_queryset:
        task_dict = {
            "id": task.id,
            "name": task.name,
            "task": task.task,
            "enabled": task.enabled,
            "description": task.description,
            "interval": (
                {
                    "id": task.interval.id,
                    "every": task.interval.every,
                    "period": task.interval.period,
                }
                if task.interval
                else None
            ),
            "crontab": (
                {
                    "id": task.crontab.id,
                    "minute": task.crontab.minute,
                    "hour": task.crontab.hour,
                    "day_of_week": task.crontab.day_of_week,
                    "day_of_month": task.crontab.day_of_month,
                    "month_of_year": task.crontab.month_of_year,
                    "timezone": (
                        str(task.crontab.timezone)
                        if task.crontab and task.crontab.timezone
                        else None
                    ),
                }
                if task.crontab
                else None
            ),
            "total_run_count": task.total_run_count,
            "date_changed": task.date_changed,
            "last_run_at": task.last_run_at,
            "solar": None,
            "clocked": None,
            "args": task.args,
            "kwargs": task.kwargs,
            "queue": task.queue,
            "exchange": task.exchange,
            "routing_key": task.routing_key,
            "priority": task.priority,
            "expires": task.expires,
            "expire_seconds": task.expire_seconds,
            "one_off": task.one_off,
            "start_time": task.start_time,
        }
        results.append(task_dict)

    return results


# --- 創建一個新的定時任務 (智能版) ---
@log_function_call()
@router.post("/tasks", response=PeriodicTaskSchema)
async def create_periodic_task(
    request, payload: PeriodicTaskCreateSchema
):  # 操！異步化！
    """
    一步到位创建一个新的周期性任务。API 内部会自动处理 IntervalSchedule 的查找或创建。
    """
    task_data = payload.dict()
    interval_data = task_data.pop("interval")

    # 操！異步化！
    interval_schedule, created = await IntervalSchedule.objects.aget_or_create(
        every=interval_data["every"], period=interval_data["period"]
    )
    if created:
        logger.info(
            f"为新任务创建了时间计划: every {interval_data['every']} {interval_data['period']}"
        )

    # 操！異步化！
    task, created = await PeriodicTask.objects.aupdate_or_create(
        name=task_data.pop("name"),
        defaults={**task_data, "interval": interval_schedule},
    )

    if not created:
        raise HttpError(409, f"Task with name '{payload.name}' already exists.")
    return task


# --- 查詢單個定時任務 ---
@log_function_call()
@router.get("/tasks/{task_id}", response=PeriodicTaskSchema)
async def get_periodic_task(request, task_id: int):  # 操！異步化！
    try:
        # 操！異步化！
        task = await PeriodicTask.objects.select_related("interval", "crontab").aget(
            id=task_id
        )
        # 注意：單個對象返回時，Ninja 的異步處理通常沒問題，
        # 但為了絕對安全和一致性，我們也應該手動序列化。
        # 暫時保持這樣，如果 get 單個對象也報錯，再改成像 list 一樣的手動模式。
        return task
    except PeriodicTask.DoesNotExist:
        raise HttpError(404, "Periodic task not found.")


# --- 更新一個定時任務 ---
@log_function_call()
@router.put("/tasks/{task_id}", response=PeriodicTaskSchema)
def update_periodic_task(request, task_id: int, payload: PeriodicTaskUpdateSchema):
    """
    更新定時任務。修正了直接賦值 Dict 給 ForeignKey 的錯誤。
    """
    task = get_object_or_404(PeriodicTask, id=task_id)

    # exclude_unset=True 很重要，只處理前端有傳過來的欄位
    data = payload.dict(exclude_unset=True)

    # 1. 特殊處理 interval
    if "interval" in data:
        interval_data = data.pop("interval")
        if interval_data:
            schedule, _ = IntervalSchedule.objects.get_or_create(**interval_data)
            task.interval = schedule
            task.crontab = None  # 切換模式時，清空另一種排程
        else:
            task.interval = None

    # 2. 特殊處理 crontab
    if "crontab" in data:
        crontab_data = data.pop("crontab")
        if crontab_data:
            schedule, _ = CrontabSchedule.objects.get_or_create(**crontab_data)
            task.crontab = schedule
            task.interval = None  # 切換模式時，清空另一種排程
        else:
            task.crontab = None

    # 3. 處理剩餘的普通欄位 (name, args, kwargs, enabled...)
    for key, value in data.items():
        setattr(task, key, value)

    try:
        task.save()
    except ValidationError as e:
        # 如果是 name 重複，e.message_dict 會包含 {'name': ['...']}
        # 我們把它解析出來，拋出一個乾淨的 400 錯誤給前端
        error_msg = str(e)
        if hasattr(e, "message_dict"):
            if "name" in e.message_dict:
                error_msg = f"任務名稱重複: {e.message_dict['name'][0]}"
            else:
                error_msg = str(e.message_dict)
        raise HttpError(400, error_msg)
    return task


# --- 刪除一個定時任務 ---
@log_function_call()
@router.delete("/tasks/{task_id}", response={204: None})
async def delete_periodic_task(request, task_id: int):  # 操！異步化！
    try:
        # 操！異步化！
        task = await PeriodicTask.objects.aget(id=task_id)
        # 操！異步化！
        await task.adelete()
        return 204
    except PeriodicTask.DoesNotExist:
        raise HttpError(404, "Periodic task not found.")


# --- 輔助 API：查詢與創建調度計劃 ---
@log_function_call()
@router.get("/schedules/intervals", response=List[IntervalScheduleSchema])
async def list_intervals(request):  # 操！異步化！
    # .all() 是 lazy 的，Ninja 的異步模式會處理好異步迭代
    return await IntervalSchedule.objects.all()
