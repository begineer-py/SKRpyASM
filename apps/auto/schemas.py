from ninja import Schema
from typing import Optional, List

class AutoConvertSchema(Schema):
    analysis_id: int

class AutoConvertResponseSchema(Schema):
    success: bool
    detail: str
    steps_created: int
