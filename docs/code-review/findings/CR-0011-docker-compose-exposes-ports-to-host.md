# CR-0011：docker-compose.yml 多服務直接暴露埠至宿主機

- Status: **Fixed - Pending Verification**
- Severity: P2
- Domain: Docker
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Review cycle: 3
- Fingerprint: docker/port-exposure/docker-compose.yml/multiple-services

## Summary

`docker/docker-compose.yml` 中多個內部服務直接將埠綁定至宿主機 `127.0.0.1`（PostgreSQL 5432、Redis 6379、Hasura 8085、NocoDB 8081、FlareSolverr 8191/8192、FlareProxyGo 8192/1337），增加攻擊面，違反最小權限原則。僅 Nginx (80) 和 Django (8000) 需對外暴露。

**Cycle 3 (Docker Rotation) 已修復關鍵風險**：
- nginx: `0.0.0.0:80` → `127.0.0.1:80` (修復關鍵風險，**配置已更新，待容器重建生效**)
- c2_kali_sandbox: `network_mode: host` → bridge network (`c2_network`), 減少 capabilities (移除 SYS_ADMIN, apparmor:unconfined)
- 新增 nginx healthcheck

**Cycle 4 發現剩餘問題**:
- flaresolverr: 仍缺少 8192 埠綁定 (原預設監聽 `0.0.0.0:8192`，嚴重風險)，需新增 `"127.0.0.1:8192:8192"`
- 內部服務 (postgres, redis, hasura, nocodb) 的 ports 映射仍存在，待後續分階段移除

**待後續處理**: 內部服務 (postgres, redis, hasura, nocodb, flaresolverr, flareproxygo) 的 ports 映射移除，改為純內部網路通訊。這會影響開發習慣，需評估影響後分階段執行。

## Evidence

- File: `docker/docker-compose.yml`
- Lines: 15, 33, 48, 73, 97, 109, 110
- Symbol: ports mapping

```yaml
postgres:
  ports:
    - "127.0.0.1:5432:5432"

redis:
  ports:
    - "127.0.0.1:6379:6379"

hasura:
  ports:
    - "127.0.0.1:8085:8080"

nocodb:
  ports:
    - "127.0.0.1:8081:8080"

flaresolverr:
  ports:
    - "127.0.0.1:8191:8191"
    - "8192/tcp"  # 無綁定 IP，預設 0.0.0.0

flareproxygo:
  ports:
    - "127.0.0.1:8192:8080"
    - "127.0.0.1:1337:1337"
```

**Cycle 3 修復內容**:
```yaml
nginx:
  ports:
    - "127.0.0.1:80:80"  # 修復: 0.0.0.0 → 127.0.0.1
  healthcheck:           # 新增: healthcheck
    test: ["CMD-SHELL", "curl -f http://localhost/ || exit 1"]

c2_kali_sandbox:
  # 修復: network_mode: host → bridge
  networks:
    - c2_network
  cap_add:               # 減少 capabilities
    - NET_RAW
    - NET_ADMIN
  security_opt:
    - seccomp:unconfined  # 僅保留 bwrap 所需
  # 移除: SYS_ADMIN, apparmor:unconfined
```

### Cycle 4 待修復 (flaresolverr 8192 埠):
```yaml
flaresolverr:
  ports:
    - "127.0.0.1:8191:8191"
    - "127.0.0.1:8192:8192"  # 新增: 明確綁定 127.0.0.1，防止 0.0.0.0 暴露
```

問題：
1. **PostgreSQL/Redis**：資料庫、快取應僅供內部服務存取，無需暴露至宿主機
2. **Hasura/NocoDB**：管理介面應透過 Nginx 反向代理存取，非直接暴露
3. **FlareSolverr 8192**：無綁定 IP，預設監聽 `0.0.0.0`，對全網開放
4. **FlareProxyGo 1337**：代理埠暴露至宿主機
5. **nginx (已修復)**：原綁定 `0.0.0.0:80`，現改為 `127.0.0.1:80`
6. **c2_kali_sandbox (已修復)**：原 `network_mode: host`，現改為 bridge network

## Trigger

審查 Docker 網路拓撲與埠暴露策略。

## Impact

1. **攻擊面擴大**：宿主機被入侵時，內部服務直接可被存取
2. **資料庫直接連線風險**：開發者可能慣性直接連 `localhost:5432` 繞過應用層權限控制
3. **管理介面暴露**：Hasura Console、NocoDB 直接可訪問，若密碼弱則極度危險
4. **FlareSolverr 8192 監聽 0.0.0.0**：嚴重安全漏洞，任何可連宿主機者可存取瀏覽器自動化 API
5. **nginx 0.0.0.0 (已修復)**：Web 伺服器對全網開放
6. **kali_sandbox host network (已修復)**：沙盒擁有完整宿主機網路存取權

## Why this matters

Docker 內部網路（`c2_network`）已提供服務間通訊。僅邊緣服務需暴露埠。CLAUDE.md 8.4 節要求檢查「是否有不必要暴露的 port」。

## Recommended change

1. **移除內部服務的 `ports` 映射**，改用 Docker 內部 DNS 通訊：
```yaml
# 移除 postgres、redis、hasura、nocodb 的 ports 區塊
# 服務間使用服務名稱：postgres:5432, redis:6379, hasura:8080, nocodb:8080
```

2. **FlareSolverr 修正 8192 埠綁定**：
```yaml
flaresolverr:
  ports:
    - "127.0.0.1:8191:8191"
    - "127.0.0.1:8192:8192"  # 明確綁定 127.0.0.1
```

3. **開發者工具存取**：提供 `make db-shell`、`make redis-cli` 等命令透過 `docker exec` 存取

4. **Hasura/NocoDB 管理介面**：透過 Nginx 反向代理 + 認證存取，或 SSH tunnel

5. **保留必要暴露**：
```yaml
nginx:
  ports:
    - "127.0.0.1:80:80"  # 僅本機存取

django:
  ports:
    - "127.0.0.1:8000:8000"  # 僅本機 API 存取
```

## Verification

1. `docker compose config` 確認無內部服務 ports 映射
2. `docker exec c2_django pg_isready -h postgres -U myuser` 確認內部連線正常
3. 宿主機 `curl localhost:5432` 確認連線被拒絕
4. 宿主機 `curl localhost:8192` 確認 FlareSolverr 8192 無回應
5. `docker compose -f docker/docker-compose.yml config --quiet` - ✅ 通過 (Cycle 3)

## Resolution criteria

僅 Nginx (127.0.0.1:80) 和 Django (127.0.0.1:8000) 暴露至宿主機，所有內部服務透過 Docker 網路通訊。

## Notes

- 此變更會影響本地開發習慣（無法直接用 pgAdmin 連 localhost:5432）
- 需更新開發文檔說明正確存取方式
- CI/CD 中需確認服務健康檢查不依賴宿主機埠
- **Cycle 3 完成**: 關鍵風險 (nginx 0.0.0.0, kali_sandbox host network) 已修復
- **後續建議**: 分階段移除內部服務 ports 映射，配合開發文檔更新