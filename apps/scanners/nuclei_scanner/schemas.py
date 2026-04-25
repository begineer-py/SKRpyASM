from ninja import Schema
from typing import List


class NucleiPayload(Schema):
    rate_limit: int = 150
