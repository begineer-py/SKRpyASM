# CR-0018：安全配置缺口 (Security Hardening Gaps)

- Status: **Open**
- Severity: P2
- Domain: Cross-cutting (Security)
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Review cycle: 4
- Fingerprint: cross-cutting/security/configuration/gaps

## Summary

Django 專案缺少生產環境必要的安全配置：缺失安全標頭 (HSTS, CSP, X-Frame-Options 等)、CSRF 保護被關閉、Session/Cookie 安全屬性未設定、無速率限制、DEBUG=True 預設開啟。

## Evidence

### 1. CSRF 保護被關閉 (settings.py:79)
```python
# "django.middleware.csrf.CsrfViewMiddleware",  # 跨站請求偽造保護中間件 (開發階段關閉，便於前後端分離除錯)
```
**風險**: 所有 POST/PUT/DELETE/PATCH 請求無 CSRF 驗證，易受 CSRF 攻擊。

### 2. DEBUG = True 預設開啟 (settings.py:33)
```python
DEBUG = True
```
**風險**: 錯誤頁面洩露堆疊追蹤、環境變數、SQL 查詢等敏感資訊。

### 3. ALLOWED_HOSTS 過於寬鬆 (settings.py:35-39)
```python
ALLOWED_HOSTS = ["*"]  # 預設允許所有主機
```
**風險**: Host Header Injection 攻擊，可導致緩存投毒、密碼重設鏈接劫持。

### 4. 缺失安全標頭配置
以下設定**完全缺失**於 settings.py:
| 設定 | 建議值 | 用途 |
|------|--------|------|
| `SECURE_HSTS_SECONDS` | 31536000 (1年) | 強制 HTTPS、防降級攻擊 |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | True | 覆蓋子域名 |
| `SECURE_HSTS_PRELOAD` | True | 支援 HSTS preload list |
| `SECURE_SSL_REDIRECT` | True | 強制 HTTP → HTTPS 重導向 |
| `SECURE_CONTENT_TYPE_NOSNIFF` | True | 防 MIME-type sniffing |
| `SECURE_REFERRER_POLICY` | "strict-origin-when-cross-origin" | 控制 Referrer 資訊 |
| `SECURE_CROSS_ORIGIN_OPENER_POLICY` | "same-origin" | 隔離瀏覽器上下文 |
| `X_FRAME_OPTIONS` | "DENY" | 防點擊劫持 (已有 middleware 但未設定值) |

### 5. Session/Cookie 安全屬性未設定
| 設定 | 建議值 | 現狀 |
|------|--------|------|
| `SESSION_COOKIE_SECURE` | True | 未設定 (預設 False) |
| `SESSION_COOKIE_HTTPONLY` | True | 未設定 (預設 True) |
| `SESSION_COOKIE_SAMESITE` | "Lax" 或 "Strict" | 未設定 (預設 "Lax" Django 4.0+) |
| `CSRF_COOKIE_SECURE` | True | 未設定 |
| `CSRF_COOKIE_HTTPONLY` | True | 未設定 |
| `CSRF_COOKIE_SAMESITE` | "Lax" | 未設定 |

### 6. 無 API 速率限制
- Django Ninja / DRF 無配置 `DEFAULT_THROTTLE_CLASSES` / `DEFAULT_THROTTLE_RATES`
- 公開端點 (如 `/api/scanners/*`, `/api/flaresolverr/*`) 可被濫用發起大量掃描
- 登入/註冊端點無暴力破解防護

### 7. CORS 配置過於寬鬆 (開發環境可接受，生產需收斂)
```python
CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173", ...]
CORS_ALLOW_CREDENTIALS = True
```
生產環境應明確列出允許域名，不使用通配符。

### 8. API_KEY 加密金鑰硬編碼 (settings.py:474)
```python
API_KEY_ENCRYPTION_KEY = "Z39ixGU2CW6QcUodG8z3IYNrV_a4Vud2Uy_esQRLGfM="
```
**風險**: 金鑰洩露導致所有儲存的 API Keys 可被解密。應從環境變數讀取或使用密鑰管理服務。

### 9. 資料庫密碼預設值 (settings.py:150-157, CR-0010)
```python
"PASSWORD": os.environ.get("POSTGRES_PASSWORD") or "secret",
```
已標記為 Accepted risk，但生產部署必須覆蓋。

## Trigger

Cycle 4 (Cross-cutting Rotation) - 安全配置基線審查。

## Impact

1. **CSRF 攻擊**: 攻擊者可誘騙管理員執行狀態改變操作 (刪除目標、修改配置、觸發掃描)
2. **資訊洩露**: DEBUG 頁面洩露技術細節，協助攻擊者偵察
3. **Host Header 攻擊**: 緩存投毒、密碼重設鏈接劫持
4. **中間人攻擊**: 缺 HSTS/SSL Redirect，HTTP 流量可被攔截竄改
5. **點擊劫持**: 缺 X-Frame-Options，頁面可被 iframe 嵌入
6. **Session 劫持**: Cookie 缺 Secure/HttpOnly/SameSite，XSS 可竊取 session
7. **API 濫用**: 無速率限制，掃描端點可被濫發消耗資源
8. **金鑰洩露**: 硬編碼加密金鑰，原始碼洩露即導致所有 API Keys 外洩

## Why this matters

OWASP Top 10 / ASVS Level 1 要求上述所有防護。作為安全工具平台，自身安全配置必須達標。

## Recommended Change

### 立即修復 (開發環境也建議):

1. **啟用 CSRF** (開發環境可用 `csrf_exempt` 裝飾器針對特定 API):
```python
# 取消註解
MIDDLEWARE = [
    ...
    "django.middleware.csrf.CsrfViewMiddleware",  # 啟用
    ...
]
```

2. **環境區分配置** (建立 `settings/production.py` 繼承 `settings/base.py`):
```python
# production.py
DEBUG = False
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

# Security headers
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Secure cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# Proxy SSL header (如果在 Nginx 後)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

3. **API 速率限制** (Ninja/DRF):
```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [...],
    "DEFAULT_PERMISSION_CLASSES": [...],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "scanner": "10/minute",      # 掃描觸發端點
        "auth": "5/minute",          # 登入/註冊
        "fuzz": "20/minute",         # Fuzzing
    },
}
```
使用: `@throttle(scope="scanner")` 裝飾掃描端點。

4. **移除硬編碼加密金鑰**:
```python
API_KEY_ENCRYPTION_KEY = os.environ.get("API_KEY_ENCRYPTION_KEY")
if not API_KEY_ENCRYPTION_KEY and not DEBUG:
    raise ImproperlyConfigured("API_KEY_ENCRYPTION_KEY must be set in production")
```

5. **Content Security Policy** (可選，配合前端):
```python
# 需 django-csp 套件
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # 視前端需求調整
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "wss:", "https:")  # SSE/WebSocket
```

### 遷移策略

1. 建立 `settings/production.py` 和 `settings/development.py`
2. `DJANGO_SETTINGS_MODULE` 由環境變數控制
3. 開發環境保持寬鬆 (DEBUG=True, CSRF 關閉或針對性豁免)
4. CI/CD 部署時強制使用 production settings
5. 運行 `python manage.py check --deploy` 驗證生產配置

## Verification

1. `python manage.py check --deploy` - Django 部署檢查 (應零警告)
2. `curl -I https://domain.com` - 驗證安全標頭:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Cross-Origin-Opener-Policy: same-origin`
3. `curl -v -X POST ...` - 驗證 CSRF token 驗證
4. 速率限制測試: 連續呼叫端點超過閾值收到 429
5. Cookie 檢查: `Set-Cookie` 包含 `Secure; HttpOnly; SameSite=Lax`

## Resolution Criteria

- `python manage.py check --deploy` 零警告零錯誤
- 所有安全標頭正確回傳
- CSRF 保護啟用 (開發環境可配置豁免)
- API 速率限制生效
- 硬編碼金鑰移除，改由環境變數注入
- Session/Cookie 安全屬性正確

## Notes

- 開發環境維持便利性 (DEBUG=True, CSRF 關閉) 但需明確隔離配置檔
- Nginx 已終結 SSL，需設定 `SECURE_PROXY_SSL_HEADER`
- 參考: Django 官方文檔 "Deployment checklist", "Security middleware", OWASP ASVS