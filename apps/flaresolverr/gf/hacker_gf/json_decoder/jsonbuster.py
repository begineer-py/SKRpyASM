import json
import os
from typing import List, Dict, Any, Tuple, Optional


class JsonInspector:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.raw_data = {}
        self.path_map: Dict[str, Dict[str, Any]] = {}
        self.depth_map: Dict[int, List[str]] = {}
        self.max_depth = 0
        self._load_and_parse()

    def _get_key_son(self, node: Any) -> Tuple[List[str], int]:
        if isinstance(node, dict):
            keys = list(node.keys())
            return (keys, len(keys))
        elif isinstance(node, list):
            keys = [f"[{i}]" for i in range(len(node))]
            return (keys, len(node))
        return ([], 0)

    def _walk(self, node: Any, depth: int, path: str, key_name: str) -> int:
        """遍歷並回傳該節點的子樹高度 (Subtree Height)"""
        self.max_depth = max(self.max_depth, depth)

        # 獲取子節點初步資訊
        son_keys, son_count = self._get_key_son(node)

        # 預先建立 entry (subtree_height 稍後更新)
        entry = {
            "key": key_name,
            "value": node,
            "where": path,
            "key_son": [son_keys, son_count],
            "depth": depth,
            "subtree_height": 0,
        }
        self.path_map[path] = entry

        current_max_child_h = -1  # 如果沒有子節點，高度偏移是 -1 (+1 後變 0)

        if isinstance(node, dict):
            for k, v in node.items():
                child_h = self._walk(v, depth + 1, f"{path}.{k}", k)
                current_max_child_h = max(current_max_child_h, child_h)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                child_h = self._walk(item, depth + 1, f"{path}[{i}]", f"[{i}]")
                current_max_child_h = max(current_max_child_h, child_h)

        # 該節點的高度 = 子節點的最大高度 + 1
        actual_height = current_max_child_h + 1
        self.path_map[path]["subtree_height"] = actual_height

        if depth not in self.depth_map:
            self.depth_map[depth] = []
        self.depth_map[depth].append(path)

        return actual_height

    def _load_and_parse(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.raw_data = json.load(f)
        # root 的 key 名稱為 root，深度 0
        self._walk(self.raw_data, 0, "root", "root")

    def get_by_depth(
        self, depth: int, start: int = 0, end: Optional[int] = None
    ) -> Dict[str, Any]:
        target_depth = depth if depth >= 0 else (self.max_depth + 1 + depth)
        paths = self.depth_map.get(target_depth, [])
        actual_end = end if end is not None else len(paths)
        selected_paths = paths[start:actual_end]
        keys_data = [self.path_map[p] for p in selected_paths]

        return {
            "depth": target_depth,
            "total_at_layer": len(paths),
            "keys": keys_data,
        }

    def get_layer_keys_overview(self, depth: int) -> Dict[str, Any]:
        """
        【新增】只看這一層有哪些不重複的 Key 名稱
        這對於分析 Schema 超有用，不會被重複的 Array Item 淹沒
        """
        target_depth = self._resolve_depth(depth)
        paths = self.depth_map.get(target_depth, [])

        # 提取這一層所有節點的 key 名稱並去重
        unique_keys = sorted(list(set([self.path_map[p]["key"] for p in paths])))

        return {
            "depth": target_depth,
            "unique_key_count": len(unique_keys),
            "unique_keys": unique_keys,
            "sample_paths": paths[:5],  # 給幾個路徑參考
        }

    def get_by_path(self, where: str) -> Optional[Dict[str, Any]]:
        return self.path_map.get(where)


# === 測試執行 ===
if __name__ == "__main__":
    inspector = JsonInspector(os.path.join(os.path.dirname(__file__), "test.json"))

    # 1. 測試最底層 (-1)
    print("\n--- 測試最底層 (-1) ---")
    # 不傳 end 就拿該層全部資料
    last_layer = inspector.get_by_depth(
        depth=-1,
        start=0,
        end=10,
    )
    print(json.dumps(last_layer, indent=2, ensure_ascii=False))

    # # 2. 測試看某一層的所有「不重複 Key」
    # print("\n--- 測試第 2 層的 Key 概觀 ---")
    # overview = inspector.get_layer_keys_overview(depth=2)
    # print(json.dumps(overview, indent=2, ensure_ascii=False))
