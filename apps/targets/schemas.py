# targets/schemas.py

from ninja import Schema, ModelSchema
from datetime import datetime
from typing import List, Optional
from apps.core.models import Target, Seed

# =======================
# Target Schemas
# =======================


class TargetSchema(ModelSchema):
    class Meta:
        model = Target
        fields = ["id", "name", "description", "created_at"]


class CreateTargetSchema(Schema):
    name: str
    description: Optional[str] = None


class UpdateTargetSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None


# =======================
# Seed Schemas
# =======================


class SeedSchema(ModelSchema):
    class Meta:
        model = Seed
        fields = ["id", "value", "type", "is_active", "created_at"]


class AddSeedSchema(Schema):
    value: str
    type: str = "DOMAIN"  # 默認為 DOMAIN，對應 models.py 的 choices
