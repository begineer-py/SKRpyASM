# CR-0010：docker-compose.yml 含硬編碼預設密碼

- Status: Accepted risk
- Severity: P1
- Domain: Docker
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: docker/hardcoded-secrets/docker-compose.yml/postgres-hasura-nocodb

## Summary

`docker/docker-compose.yml` 中多個服務使用硬編碼的預設密碼（`myuser`/`secret`/`mydb`），且 Hasura 管理員密鑰、NocoDB 資料庫密碼直接寫在 compose 檔案中，違反安全最佳實踐，若此檔案被提交到版控或部署到生產環境將造成嚴重安全風險。

## Evidence

- File: `docker/docker-compose.yml`
- Lines: 10-13, 55, 61, 79-84
- Symbol: environment variables

```yaml
postgres:
  environment:
    POSTGRES_USER: myuser
    POSTGRES_PASSWORD: secret
    POSTGRES_DB: mydb

hasura:
  environment:
    HASURA_GRAPHQL_DATABASE_URL: postgres://myuser:secret@postgres:5432/mydb
    HASURA_GRAPHQL_ADMIN_SECRET: "YourSuperStrongAdminSecretHere"  # <-- 務必修改
    HASURA_GRAPHQL_ENABLE_CONSOLE: "true"
    HASURA_GRAPHQL_DEV_MODE: "true"

nocodb:
  environment:
    NC_PG_USER: myuser
    NC_PG_PASSWORD: secret
    NC_PG_DATABASE: mydb
```

註解 `# <-- 務必修改` 表明作者知曉風險，但未強制透過環境變數注入。

## Trigger

審查 Docker 基礎設施配置時發現。

## Impact

1. **生產環境密碼洩漏**：若直接部署此 compose 檔，資料庫、Hasura、NocoDB 皆使用弱密碼
2. **版控洩漏風險**：檔案已在 git 中，密碼已洩漏至版本歷史
3. **供應鏈攻擊面**：公開倉庫可被掃描到預設憑證
4. **合規違規**：違反密碼管理最佳實踐（OWASP、SOC2 等）

## Why this matters

SKRpyASM 是攻擊面管理平台，自身基礎設施若有硬編碼密碼，嚴重損害專案可信度。Docker Compose 應僅作為模板，所有密鑰必須透過 `.env` 檔案或秘密管理系統注入。

## Recommended change

1. **移除所有硬編碼密碼**，改為 `${VARIABLE:-default}` 語法：
```yaml
postgres:
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-myuser}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_DB: ${POSTGRES_DB:-mydb}
```

2. **Hasura Admin Secret 必須強制從環境變數讀取**，無預設值：
```yaml
HASURA_GRAPHQL_ADMIN_SECRET: ${HASURA_GRAPHQL_ADMIN_SECRET}
```

3. **建立 `.env.example` 範本**（已存在）並確保 `.env` 在 `.gitignore` 中（已確認）

4. **生產環境使用 Docker Secrets 或外部秘密管理**（HashiCorp Vault、AWS Secrets Manager 等）

5. **CI/CD 流程中驗證**：啟動前檢查必要環境變數已設定

**決議：Accepted risk** - 用戶認為預設值對首次使用者的快速體驗很重要（out-of-the-box 可用），風險由部署者自行評估。生產部署時仍建議覆蓋所有預設值。

## Verification

1. 檢查 `docker compose config` 輸出無硬編碼密碼
2. 嘗試不設定 `.env` 啟動，確認因缺少必要變數而失敗
3. 使用 `git log -p -- docker/docker-compose.yml` 確認歷史無敏感資訊（已洩漏需輪換）

## Resolution criteria

已確認風險並接受：預設值保留以支援首次使用者快速體驗。生產部署文檔需明確警告必須覆蓋所有預設密碼。

## Notes

- `.env.example` 已存在且包含對應變數，但 compose 未完全使用
- `POSTGRES_PASSWORD` 等在 `.env.example` 中有預設值，生產必須覆蓋
- Hasura Admin Secret 在 `.env.example` 中為 `YourSuperStrongAdminSecretHere`，極度危險
- **決議**：Accepted risk - 保留預設值支援開發者快速上手，生產部署需自行覆蓋
- 建議在 README/部署文檔中添加明確警告