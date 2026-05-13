# targets/schemas.py

from ninja import Schema, ModelSchema
from pydantic import Field
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
    value: str = Field(..., description="種子的實際值，例如 'example.com' 或是 '192.168.1.1'")
    type: str = Field("DOMAIN", description="種子類型，可選值為: DOMAIN (預設), IP_RANGE, URL, GITHUB_REPO")
