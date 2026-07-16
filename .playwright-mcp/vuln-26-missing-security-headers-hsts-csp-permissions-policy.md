# 漏洞報告：Missing Security Headers (HSTS, CSP, Permissions-Policy)

---

## 基本資訊

| 項目 | 內容 |
|---|---|
| **漏洞 ID** | #26 |
| **嚴重程度** | 中危 (Medium) |
| **驗證狀態** | 驗證中 |
| **發現位置** | `https://vuln-f9wi.onrender.com/` |
| **偵測工具** | automation-agent |
| **模板 ID** | `missing-security-headers-(hsts,-csp,-permissions-policy)` |
| **CVE 豐富化** | 待豐富化 |
| **首次發現** | 2026/07/04 下午01:56 |
| **最後發現** | 2026/07/04 下午01:56 |
| **最後更新** | 2026/07/04 下午01:56 |

## 漏洞描述

The application is missing several critical security headers:

**Missing Headers:**
1. **Strict-Transport-Security (HSTS)** - Not set. Without HSTS, users are vulnerable to SSL stripping attacks and downgrade attacks.
2. **Content-Security-Policy (CSP)** - Not set. Without CSP, the application is fully vulnerable to XSS attacks (both reflected and stored). Any injected JavaScript can execute without restriction.
3. **Permissions-Policy** - Not set. Browser features (camera, microphone, geolocation) are not restricted.

**Present Headers (for reference):**
- X-Content-Type-Options: nosniff ✓
- X-Frame-Options: DENY ✓
- Referrer-Policy: same-origin ✓

The absence of CSP is particularly concerning given that the application uses Pico CSS from CDN and has multiple user-input fields that could be exploited for XSS.

## 原始請求 (Request)

```http
GET / HTTP/2
Host: vuln-f9wi.onrender.com
```

## 原始回應 (Response)

```http
HTTP/2 200
server: cloudflare
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: same-origin
(Strict-Transport-Security: MISSING)
(Content-Security-Policy: MISSING)
(Permissions-Policy: MISSING)
```
