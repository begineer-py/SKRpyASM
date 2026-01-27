from django.views.generic import detail
from ninja import Schema
from typing import Optional, Any, Union, List, Dict
from datetime import datetime
from pydantic import field_validator, model_validator
import json  # 操！这次绝不能漏！

from pydantic import Field
