from typing import List

from numpy import number

key_son = tuple(list[str], int)  # <所有的下一層key, len>
depth_schema_input = {
    "depth": int,
    "start": int,
    "end": int,
}
depth_schema_output = {
    "depth": int,
    "start": int,
    "end": int,
    "keys": list["key":str, "value":int, str, list, dict, "where":str, key_son],
}
key_schema_input = {
    "where": str,
}
key_schema_output = {
    "key": str,
    "value": int,
    "where": str,
    "key_son": key_son,
}
# 給入一個where看那個key的value
score = int
gemini_input = {int, key_schema_output}
gemini_output = {int, score}
