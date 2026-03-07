import json
import logging
from typing import Union
from django.utils import timezone
from apps.core.models import Subdomain, TechStack, URLResult

logger = logging.getLogger(__name__)


def process_nuclei_tech_line(line_str: str, target_obj: Union[Subdomain, URLResult]):
    """
    通用解析函數：處理 Nuclei JSON 輸出並關聯至 Subdomain 或 URLResult
    """
    try:
        data = json.loads(line_str)

        # 1. 提取技術名稱 (matcher-name)
        tech_name = data.get("matcher-name")
        if not tech_name:
            return

        # 2. 提取元數據 (Tags & Version)
        info = data.get("info", {})
        tags = info.get("tags", [])
        metadata = info.get("metadata", {})
        version = metadata.get("version", None)

        # 3. 判斷傳入對象類型並準備過濾條件
        lookup_params = {
            "name": tech_name,
            "version": version,
        }

        if isinstance(target_obj, Subdomain):
            lookup_params["subdomain"] = target_obj
            target_identifier = target_obj.name
            target_obj.is_tech_analyzed = True
            target_obj.save()
        elif isinstance(target_obj, URLResult):
            # 根據模型定義，欄位名為 which_url_result
            lookup_params["which_url_result"] = target_obj
            target_identifier = target_obj.url

            target_obj.is_tech_analyzed = True
            target_obj.save()
        # 4. 執行 update_or_create
        tech_obj, created = TechStack.objects.update_or_create(
            **lookup_params,
            defaults={"categories": tags, "last_seen": timezone.now()},
        )

        log_level = logging.INFO if created else logging.DEBUG
        action_str = "偵測到新技術" if created else "更新技術資訊"
        logger.log(log_level, f"{action_str}: {target_identifier} -> {tech_name}")

    except json.JSONDecodeError:
        logger.error(f"無法解析的 JSON 行: {line_str[:100]}...")
    except Exception as e:
        logger.error(f"儲存技術堆疊時發生錯誤: {str(e)}", exc_info=True)
