# API Keys 管理系統

`api_keys` 應用程式用於集中管理外部服務（如 OpenAI, Hunter.io, Github 等）的認證資訊。

## 功能概觀

- **集中儲存**: 統一管理所有工具所需的 API Key。
- **動態更新**: 透過 API 即時更新金鑰，無需重啟服務。
- **狀態管理**: 支援快速啟用或停用特定服務。

## 模型 (Model)

### `APIKey`
- `service_name`: 服務名稱 (例如: 'OPENAI', 'HUNTER')，需唯一。
- `key_value`: API 金鑰的實際值。
- `is_active`: 是否啟用此金鑰。
- `description`: 服務描述或備註。

## API 接口

所有接口位於 `/api/api_keys/`。

### 1. 建立 API Key
- **路徑**: `POST /`
- **Payload**:
    ```json
    {
      "service_name": "string",
      "key_value": "string",
      "is_active": true,
      "description": "string"
    }
    ```
- **回應**: 建立成功的 `APIKey` 物件。

### 2. 列出所有 API Key
- **路徑**: `GET /`
- **回應**: `List[APIKey]`

### 3. 取得單一 API Key
- **路徑**: `GET /{api_key_id}`
- **回應**: `APIKey` 物件。

### 4. 更新 API Key
- **路徑**: `PATCH /{api_key_id}`
- **Payload**: `APIKeyUpdate` (欄位皆為選填)
- **回應**: 更新後的 `APIKey` 物件。

### 5. 刪除 API Key
- **路徑**: `DELETE /{api_key_id}`
- **回應**: `{"success": true}`
