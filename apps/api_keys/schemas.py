from ninja import Schema
from typing import Optional
from datetime import datetime

class APIKeyOut(Schema):
    id: int
    service_name: str
    key_value: str
    is_active: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class APIKeyIn(Schema):
    service_name: str
    key_value: str
    is_active: bool = True
    description: Optional[str] = None

class APIKeyUpdate(Schema):
    service_name: Optional[str] = None
    key_value: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
