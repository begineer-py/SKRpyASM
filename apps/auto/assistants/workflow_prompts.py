"""VulnClaw workflow routing table — 精簡路由信號，注入 agent system prompt。

設計理念：
- Prompt 只放 routing table（~200 tokens），指引 agent 去哪裡找 workflow
- 完整 workflow 內容透過 import_skills 匯入 DB（父 SKILL.md + references）
- Agent 透過 search_skills / load_skill 按需載入

父 SKILL.md 全部匯入 DB，對應的 search_skills 關鍵字：
- web-pentest              → search_skills("web pentest")
- web-security-advanced    → search_skills("web security advanced")
- ctf-web                  → search_skills("ctf web")
- waf-bypass               → search_skills("waf bypass")
- rapid-checklist          → search_skills("rapid checklist")
- recon-playbook           → search_skills("recon playbook") (ReconAgent 自動載入)
"""

WORKFLOW_ROUTING_TABLE = """<workflow_routing>
## VulnClaw 技能路由表

完整攻擊方法論與 payload 透過技能系統按需載入。啟動時依目標類型載入對應 playbook：

### PostExploitAgent 適用
| 目標特徵 | 載入指令 | 內容涵蓋 |
|----------|---------|---------|
| 通用 Web 應用 | `search_skills("web pentest")` | 技術棧識別/目錄枚舉/認證/輸入驗證/邏輯漏洞 |
| 進階 Web 攻擊面 | `search_skills("web security advanced")` | 注入族/協議安全/認證邏輯/檔案基礎設施/部署安全 + CTF 路由 |
| CTF 場景 | `search_skills("ctf web")` | PHP 偽協議/弱比較/雙寫繞過/RCE 長度繞過/flag 位置速查 |
| 遇到 WAF/過濾 | `search_skills("waf bypass")` | WAF 繞過技巧庫 |

### ReportingAgent 適用
| 報告需求 | 載入指令 | 內容涵蓋 |
|----------|---------|---------|
| 快速 checklist + payload 族譜 | `search_skills("rapid checklist")` | 測試方法論/payload 分類/OWASP 對齊 |

### 使用方式
1. 判斷目標類型 → `load_skill("<skill_name>")` 載入對應 playbook
2. `follow_skill_guidance("<skill_name>")` 正式遵循指引
3. 需要特定 payload 時用 `search_skills("<關鍵字>")` 精確查詢 references
   - 例：`search_skills("sql injection")` / `search_skills("ssrf")` / `search_skills("ssti")`
</workflow_routing>"""
