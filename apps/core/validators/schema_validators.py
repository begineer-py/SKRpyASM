"""
JSON Schema 驗證工具庫

用於驗證 SkillTemplate 的輸入/輸出是否符合定義的 JSON Schema。
支持 JSON Schema Draft 7 的子集。
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class SchemaValidationError(Exception):
    """Schema 驗證失敗"""
    pass


class TypeValidator:
    """
    JSON Schema 輕量級驗證器
    
    支持以下類型檢查：
    - string, integer, number, boolean, array, object, null
    - pattern (正則表達式)
    - minLength, maxLength
    - minimum, maximum
    - required (物件的必需欄位)
    - enum (列舉值)
    """
    
    SUPPORTED_TYPES = {"string", "integer", "number", "boolean", "array", "object", "null"}
    
    @staticmethod
    def validate(data: Any, schema: Dict) -> Tuple[bool, Optional[str]]:
        """
        驗證數據是否符合 schema
        
        Args:
            data: 要驗證的數據
            schema: JSON Schema 物件
        
        Returns:
            (is_valid: bool, error_message: Optional[str])
            如果驗證通過，返回 (True, None)
            如果驗證失敗，返回 (False, "錯誤訊息")
        """
        try:
            TypeValidator._validate_recursive(data, schema, "$root")
            return True, None
        except SchemaValidationError as e:
            return False, str(e)
    
    @staticmethod
    def _validate_recursive(data: Any, schema: Dict, path: str = "$") -> None:
        """
        遞歸驗證數據
        
        Args:
            data: 數據
            schema: Schema
            path: 當前路徑（用於錯誤訊息）
        """
        if not schema:
            return
        
        # 獲取預期類型
        expected_type = schema.get("type")
        
        # 類型檢查
        if expected_type:
            actual_type = TypeValidator._get_actual_type(data)
            if actual_type != expected_type:
                raise SchemaValidationError(
                    f"{path}: 期望類型 '{expected_type}'，但得到 '{actual_type}'"
                )
        
        # 字符串驗證
        if expected_type == "string":
            if not isinstance(data, str):
                raise SchemaValidationError(f"{path}: 期望字符串類型")
            
            # minLength / maxLength
            min_len = schema.get("minLength")
            max_len = schema.get("maxLength")
            if min_len is not None and len(data) < min_len:
                raise SchemaValidationError(
                    f"{path}: 字符串長度 {len(data)} 小於最小值 {min_len}"
                )
            if max_len is not None and len(data) > max_len:
                raise SchemaValidationError(
                    f"{path}: 字符串長度 {len(data)} 大於最大值 {max_len}"
                )
            
            # pattern (正則表達式)
            pattern = schema.get("pattern")
            if pattern:
                try:
                    if not re.match(pattern, data):
                        raise SchemaValidationError(
                            f"{path}: 字符串 '{data}' 不符合模式 '{pattern}'"
                        )
                except re.error as e:
                    raise SchemaValidationError(f"{path}: 無效的正則表達式 '{pattern}': {str(e)}")
            
            # enum
            enum_values = schema.get("enum")
            if enum_values and data not in enum_values:
                raise SchemaValidationError(
                    f"{path}: 值 '{data}' 不在允許的列表 {enum_values} 中"
                )
        
        # 數字驗證
        elif expected_type in ("integer", "number"):
            if expected_type == "integer" and not isinstance(data, int):
                raise SchemaValidationError(f"{path}: 期望整數類型")
            if expected_type == "number" and not isinstance(data, (int, float)):
                raise SchemaValidationError(f"{path}: 期望數字類型")
            
            # minimum / maximum
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")
            if minimum is not None and data < minimum:
                raise SchemaValidationError(
                    f"{path}: 數值 {data} 小於最小值 {minimum}"
                )
            if maximum is not None and data > maximum:
                raise SchemaValidationError(
                    f"{path}: 數值 {data} 大於最大值 {maximum}"
                )
            
            # enum
            enum_values = schema.get("enum")
            if enum_values and data not in enum_values:
                raise SchemaValidationError(
                    f"{path}: 值 {data} 不在允許的列表 {enum_values} 中"
                )
        
        # 布爾驗證
        elif expected_type == "boolean":
            if not isinstance(data, bool):
                raise SchemaValidationError(f"{path}: 期望布爾類型")
        
        # 陣列驗證
        elif expected_type == "array":
            if not isinstance(data, list):
                raise SchemaValidationError(f"{path}: 期望陣列類型")
            
            # items schema
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(data):
                    TypeValidator._validate_recursive(item, items_schema, f"{path}[{i}]")
            
            # minItems / maxItems
            min_items = schema.get("minItems")
            max_items = schema.get("maxItems")
            if min_items is not None and len(data) < min_items:
                raise SchemaValidationError(
                    f"{path}: 陣列長度 {len(data)} 小於最小值 {min_items}"
                )
            if max_items is not None and len(data) > max_items:
                raise SchemaValidationError(
                    f"{path}: 陣列長度 {len(data)} 大於最大值 {max_items}"
                )
        
        # 物件驗證
        elif expected_type == "object":
            if not isinstance(data, dict):
                raise SchemaValidationError(f"{path}: 期望物件類型")
            
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            # 檢查必需欄位
            for field in required:
                if field not in data:
                    raise SchemaValidationError(
                        f"{path}: 缺少必需欄位 '{field}'"
                    )
            
            # 驗證各欄位
            for field, field_schema in properties.items():
                if field in data:
                    TypeValidator._validate_recursive(
                        data[field], field_schema, f"{path}.{field}"
                    )
        
        # null 類型
        elif expected_type == "null":
            if data is not None:
                raise SchemaValidationError(f"{path}: 期望 null，但得到 {type(data).__name__}")
    
    @staticmethod
    def _get_actual_type(data: Any) -> str:
        """
        獲取 Python 對象的 JSON 類型
        """
        if data is None:
            return "null"
        elif isinstance(data, bool):  # 必須在 int 之前，因為 bool 是 int 的子類
            return "boolean"
        elif isinstance(data, int):
            return "integer"
        elif isinstance(data, float):
            return "number"
        elif isinstance(data, str):
            return "string"
        elif isinstance(data, list):
            return "array"
        elif isinstance(data, dict):
            return "object"
        else:
            return type(data).__name__


class InputValidator:
    """
    輸入參數驗證器
    
    檢查傳給腳本的輸入參數是否符合 input_schema
    """
    
    @staticmethod
    def validate(input_data: Dict[str, Any], input_schema: Optional[Dict]) -> Tuple[bool, Optional[str]]:
        """
        驗證輸入參數
        
        Args:
            input_data: 輸入參數字典
            input_schema: 預期的 JSON Schema
        
        Returns:
            (is_valid, error_message)
        """
        if not input_schema:
            return True, None
        
        return TypeValidator.validate(input_data, input_schema)


class OutputValidator:
    """
    輸出驗證器
    
    檢查腳本輸出是否符合 output_schema
    支持從文本中解析 JSON
    """
    
    @staticmethod
    def validate(output: str, output_schema: Optional[Dict]) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        驗證輸出
        
        Args:
            output: 腳本的原始輸出（文本）
            output_schema: 預期的 JSON Schema
        
        Returns:
            (is_valid, error_message, parsed_json)
            - is_valid: 是否驗證通過
            - error_message: 錯誤訊息
            - parsed_json: 解析的 JSON 物件（如果輸出是 JSON）
        """
        if not output_schema:
            return True, None, None
        
        # 嘗試從輸出中解析 JSON
        json_obj = OutputValidator._extract_json(output)
        if json_obj is None:
            return False, "輸出不是有效的 JSON，無法驗證", None
        
        # 驗證 JSON 是否符合 schema
        is_valid, error_msg = TypeValidator.validate(json_obj, output_schema)
        if not is_valid:
            return False, error_msg, json_obj
        
        return True, None, json_obj
    
    @staticmethod
    def _extract_json(output: str) -> Optional[Dict]:
        """
        從文本中提取 JSON 物件
        
        策略：
        1. 嘗試整行解析
        2. 尋找 JSON 物件的邊界（从 { 開始到最後的 }）
        3. 尋找 JSON 陣列的邊界（从 [ 開始到最後的 ]）
        """
        if not output or not isinstance(output, str):
            return None
        
        # 策略 1：整行解析
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass
        
        # 策略 2：尋找 JSON 物件
        brace_start = output.find("{")
        if brace_start != -1:
            brace_end = output.rfind("}")
            if brace_end > brace_start:
                try:
                    return json.loads(output[brace_start:brace_end+1])
                except json.JSONDecodeError:
                    pass
        
        # 策略 3：尋找 JSON 陣列
        bracket_start = output.find("[")
        if bracket_start != -1:
            bracket_end = output.rfind("]")
            if bracket_end > bracket_start:
                try:
                    return json.loads(output[bracket_start:bracket_end+1])
                except json.JSONDecodeError:
                    pass
        
        return None


class SchemaBuilder:
    """
    幫助 AI 快速構建 JSON Schema
    
    提供便利方法，讓 AI 能在 instructions 中指定參數類型
    """
    
    @staticmethod
    def string(min_length: Optional[int] = None, max_length: Optional[int] = None, 
               pattern: Optional[str] = None, enum: Optional[List[str]] = None) -> Dict:
        """構建字符串 schema"""
        schema = {"type": "string"}
        if min_length is not None:
            schema["minLength"] = min_length
        if max_length is not None:
            schema["maxLength"] = max_length
        if pattern is not None:
            schema["pattern"] = pattern
        if enum is not None:
            schema["enum"] = enum
        return schema
    
    @staticmethod
    def integer(minimum: Optional[int] = None, maximum: Optional[int] = None,
                enum: Optional[List[int]] = None) -> Dict:
        """構建整數 schema"""
        schema = {"type": "integer"}
        if minimum is not None:
            schema["minimum"] = minimum
        if maximum is not None:
            schema["maximum"] = maximum
        if enum is not None:
            schema["enum"] = enum
        return schema
    
    @staticmethod
    def number(minimum: Optional[float] = None, maximum: Optional[float] = None) -> Dict:
        """構建數字 schema"""
        schema = {"type": "number"}
        if minimum is not None:
            schema["minimum"] = minimum
        if maximum is not None:
            schema["maximum"] = maximum
        return schema
    
    @staticmethod
    def boolean() -> Dict:
        """構建布爾 schema"""
        return {"type": "boolean"}
    
    @staticmethod
    def array(items_schema: Optional[Dict] = None, min_items: Optional[int] = None,
              max_items: Optional[int] = None) -> Dict:
        """構建陣列 schema"""
        schema = {"type": "array"}
        if items_schema is not None:
            schema["items"] = items_schema
        if min_items is not None:
            schema["minItems"] = min_items
        if max_items is not None:
            schema["maxItems"] = max_items
        return schema
    
    @staticmethod
    def object(properties: Dict[str, Dict], required: Optional[List[str]] = None) -> Dict:
        """構建物件 schema"""
        schema = {"type": "object", "properties": properties}
        if required is not None:
            schema["required"] = required
        return schema


# 常用 schema 範例
COMMON_SCHEMAS = {
    "url_input": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "pattern": r"^https?://.*"}
        },
        "required": ["url"]
    },
    "success_output": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "string"},
            "error": {"type": "string"}
        },
        "required": ["success"]
    },
    "csrf_token_output": {
        "type": "object",
        "properties": {
            "csrf_token": {"type": "string"},
            "session_cookie": {"type": "string"}
        },
        "required": ["csrf_token"]
    }
}
