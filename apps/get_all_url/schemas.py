from ninja import Schema


class ScanAllUrlSchema(Schema):
    # 雖然 URL 有 target_id，但如果你的前端習慣在 body 帶 id，這裡保留沒問題
    # 但邏輯上我們會優先使用 URL path 中的 target_identifier 來確保權限隔離
    name: str


class SuccessScanAllUrlSchema(Schema):
    name: str
    if_run: bool
