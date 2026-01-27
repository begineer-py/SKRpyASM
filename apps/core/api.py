import ninja
from ninja import Router
from ninja.errors import HttpError
from typing import List, Optional
from datetime import datetime
import requests
import os
from django.core.exceptions import ObjectDoesNotExist
from c2_core.config.logging import log_function_call
import logging

router = Router()  # 創建一個 Ninja Router 實例
logger = logging.getLogger(__name__)  # 獲取當前模塊的日誌記錄器
