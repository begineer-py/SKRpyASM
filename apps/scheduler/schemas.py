from ninja import Schema
from typing import Optional, Any, Union, List, Dict
from datetime import datetime
from pydantic import field_validator, model_validator
import json  # 操！这次绝不能漏！


# ... (Output Schemas 保持不变) ...
class IntervalScheduleSchema(Schema):
    id: int
    every: int
    period: str


class CrontabScheduleSchema(Schema):
    id: int
    minute: str
    hour: str
    day_of_week: str
    day_of_month: str
    month_of_year: str
    timezone: Optional[str] = None


class PeriodicTaskSchema(Schema):
    id: int
    name: str
    task: str
    enabled: bool
    description: str
    interval: Optional[IntervalScheduleSchema] = None
    crontab: Optional[CrontabScheduleSchema] = None
    solar: Optional[Any] = None
    clocked: Optional[Any] = None
    args: str
    kwargs: str
    queue: Optional[str] = None
    exchange: Optional[str] = None
    routing_key: Optional[str] = None
    priority: Optional[int] = None
    expires: Optional[datetime] = None
    expire_seconds: Optional[int] = None
    one_off: bool
    start_time: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    total_run_count: int
    date_changed: datetime


# ... (Input Helper Schemas 保持不变) ...
class IntervalDataSchema(Schema):
    every: int
    period: str


class CrontabDataSchema(Schema):
    minute: str = "*"
    hour: str = "*"
    day_of_week: str = "*"
    day_of_month: str = "*"
    month_of_year: str = "*"
    timezone: Optional[str] = None


# ... (Update Schema) ...
class PeriodicTaskUpdateSchema(Schema):
    name: Optional[str] = None
    task: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    interval: Optional[IntervalDataSchema] = None
    crontab: Optional[CrontabDataSchema] = None

    # 操！把类型定义得极其宽泛，先骗过 Pydantic 的类型检查
    args: Optional[Union[str, List[Any]]] = None
    kwargs: Optional[Union[str, Dict[str, Any]]] = None

    # 然后用 field_validator 在 mode='before' 时进行清洗
    @field_validator("args", mode="before")
    @classmethod
    def parse_args(cls, v):
        if isinstance(v, list):
            return json.dumps(v)
        return v

    @field_validator("kwargs", mode="before")
    @classmethod
    def parse_kwargs(cls, v):
        if isinstance(v, dict):
            return json.dumps(v)
        return v


# ... (Create Schema) ...
class PeriodicTaskCreateSchema(Schema):
    name: str
    task: str
    interval: Optional[IntervalDataSchema] = None
    crontab: Optional[CrontabDataSchema] = None
    enabled: bool = True
    description: Optional[str] = ""

    # 同样的宽泛类型
    args: Union[str, List[Any]] = "[]"
    kwargs: Union[str, Dict[str, Any]] = "{}"

    # 同样的验证器
    @field_validator("args", mode="before")
    @classmethod
    def parse_args(cls, v):
        if isinstance(v, list):
            return json.dumps(v)
        return v

    @field_validator("kwargs", mode="before")
    @classmethod
    def parse_kwargs(cls, v):
        if isinstance(v, dict):
            return json.dumps(v)
        return v

    # 加上之前漏掉的 check_schedule_provided
    @model_validator(mode="before")
    @classmethod
    def check_schedule_provided(cls, data):
        if isinstance(data, dict):
            if not data.get("interval") and not data.get("crontab"):
                raise ValueError("Either interval or crontab must be provided.")
            if data.get("interval") and data.get("crontab"):
                raise ValueError("Only one of interval or crontab should be provided.")
        return data

    # 同时也加上 interval 和 crontab 的创建用 Schema，以免 api.py 报错


class IntervalScheduleCreateSchema(Schema):
    every: int
    period: str


class CrontabScheduleCreateSchema(Schema):
    minute: str = "*"
    hour: str = "*"
    day_of_week: str = "*"
    day_of_month: str = "*"
    month_of_year: str = "*"
    timezone: Optional[str] = None
