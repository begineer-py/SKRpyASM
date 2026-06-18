"""VulnClaw 父技能 workflow 常數 — 從 SKILL.md 提煉，注入 agent system prompt。

來源映射（提煉日期 2026-06）：
- WEB_PENTEST_WORKFLOW      ← specialized/web-pentest/SKILL.md
- WEB_SECURITY_ADVANCED_WF  ← specialized/web-security-advanced/SKILL.md
- CTF_WEB_WORKFLOW          ← specialized/ctf-web/SKILL.md (含 4 段內嵌速查表)
- WAF_BYPASS_SIGNAL         ← core/waf-bypass.md (精簡 routing 信號)
- RAPID_CHECKLIST_WORKFLOW  ← specialized/rapid-checklist/SKILL.md

轉換規則：
- references/foo.md 檔案參考 → search_skills("keyword") 路由提示
- ctf-web 保留 4 段內嵌速查表（PHP 偽協議 / flag 位置 / RCE 長度繞過 / 雙寫繞過）
- 其餘剝離詳細 payload（由 references/ 透過 DB 搜尋提供）
- 保留原始語言（簡體中文）
"""

WEB_PENTEST_WORKFLOW = '''<workflow_web_pentest>
# Web 应用渗透测试流程

针对 Web 应用的专项渗透测试流程，覆盖从信息收集到漏洞验证的完整链路。
更深入的 Web 安全知识 → `search_skills("web security advanced")` 或 `search_skills("injection")`。

## 1. 技术栈识别
- 使用 fetch 工具获取 HTTP 响应头
- 使用 chrome-devtools 工具分析前端技术
- 识别后端框架和 CMS

## 2. 目录枚举
- 常见目录：/admin, /api, /upload, /config, /backup
- 敏感文件：robots.txt, sitemap.xml, .env, .git/HEAD
- API 文档：/swagger, /docs, /api-docs

## 3. 认证测试
- 默认凭据测试
- 暴力破解检测
- 会话管理缺陷
- JWT 安全测试

## 4. 输入验证测试
- SQL 注入 → `search_skills("sql injection")`
- XSS（反射/存储/DOM）→ `search_skills("xss")`
- SSRF
- LFI/RFI → `search_skills("file inclusion")`
- 命令注入 → `search_skills("command injection")`
- 文件上传

## 5. 逻辑漏洞测试
- 越权访问（水平/垂直）
- 业务逻辑绕过
- 竞态条件
- 支付逻辑漏洞

## 6. 输出
- Web 渗透报告
- PoC 脚本
</workflow_web_pentest>'''


WEB_SECURITY_ADVANCED_WF = '''<workflow_web_security_advanced>
# Web 高级安全测试流程

当目标是 Web 应用、API、网关或浏览器面向服务，且需要系统性的漏洞测试时使用。

## CTF 场景路由

> 当目标为 CTF 题目（已知有 flag，需要绕过特定过滤）时，优先使用 ctf-web 速查（见 CTF_WEB_WORKFLOW）：

| CTF 场景 | 路由关键词 |
|---------|-----------|
| PHP 弱比较/类型绕过 | `search_skills("php bypass")` |
| 命令注入空格绕过 | `search_skills("command injection bypass")` |
| eval 回显/无回显 | `search_skills("eval rce")` |
| PHP 代码审计 | `search_skills("php code audit")` |
| SSTI 注入链 | `search_skills("ssti injection")` |
| 反序列化利用链 | `search_skills("deserialization")` |
| 文件上传 → RCE | `search_skills("file upload rce")` |

本流程侧重渗透测试方法论；CTF 实战绕过值和 payload 模板请参考 ctf-web 速查。

## 场景路由

| 攻击面类型 | 路由关键词 |
|-----------|-----------|
| 参数注入（SQLi/XSS/命令执行/SSTI/XXE） | `search_skills("sql injection")` 或 `search_skills("ssti")` |
| 协议安全（CORS/GraphQL/WebSocket/OAuth/请求走私） | `search_skills("web protocol security")` |
| 认证与逻辑（IDOR/越权/支付/密码重置/鉴权绕过） | `search_skills("auth logic vuln")` |
| 文件与基础设施（上传/遍历/包含/部署/缓存/CDN/云） | `search_skills("file infrastructure")` |
| 部署安全 | `search_skills("deployment security")` |

## 测试流程

### 1. 输入验证测试
- SQL 注入：布尔/时间/报错/Union/堆叠
- XSS：反射/存储/DOM/CSP 绕过
- 命令注入：分隔符绕过、编码绕过
- SSTI：模板引擎识别 + RCE 链
- XXE：实体注入、OOB 数据外带
- 反序列化：Java/PHP/Python 链

### 2. 认证与会话测试
- 默认凭据、暴力破解
- 会话管理缺陷（固定/劫持/不安全 Cookie）
- JWT 安全（算法篡改/密钥爆破/none算法）
- OAuth/OIDC 配置缺陷
- MFA 绕过

### 3. 逻辑漏洞测试
- 越权访问（水平/垂直）
- 业务逻辑绕过（支付/优惠券/投票）
- 竞态条件
- IDOR（不安全直接对象引用）

### 4. 协议安全测试
- CORS 配置错误
- GraphQL 内省/注入
- WebSocket 认证与注入
- HTTP 请求走私
- SSRF（内网探测/云元数据）

### 5. 文件与部署安全
- 文件上传绕过
- 路径穿越
- LFI/RFI
- CDN/缓存投毒
- 供应链攻击
- 云安全配置
</workflow_web_security_advanced>'''


CTF_WEB_WORKFLOW = '''<workflow_ctf_web>
# CTF Web 攻击知识库

针对 CTF Web 题目的实战知识库，提供**具体绕过值、payload 模板、代码审计 checklist**。

**与 web-security-advanced 的区别**：
- web-security-advanced → 渗透测试方法论（怎么系统性测试一个 Web 应用）
- ctf-web → CTF 实战知识库（PHP 弱比较用什么值、空格怎么绕过、eval 输出怎么回显）

## 核心原则

1. **精确值优于方法论** — 提供可直接使用的绕过值和 payload，而非"可以尝试"的建议
2. **工具验证** — 所有 payload 必须用 `fetch` 或 `python_execute` 工具实际发送验证，不猜测结果
3. **路径选择** — 多条利用路径时，优先选过滤最少、最简单的
4. **失败记录** — 某个 payload 失败后立即记录，不重复尝试

## First-Pass 工作流（CTF Web 题标准流程）

1. 访问目标 URL，查看页面源码、HTTP 头、Cookie
2. **如源码含 `highlight_file` → 用 python_execute + strip_tags 提取纯源码**（fetch 输出可能误读）
3. 检查 robots.txt、.git/、.svn/、备份文件（index.php.bak、www.zip 等）
4. 目录扫描（常见：/flag、/admin、/login、/upload、/api）
5. 如有源码 → 进入代码审计模式（`search_skills("php code audit")`）
6. 如无源码 → 主动探测注入点、上传点、文件包含

## 场景路由

| 场景 | 路由关键词 |
|------|-----------|
| 源码提取 | `search_skills("source code extraction")` |
| PHP 弱比较/类型绕过 | `search_skills("php bypass")` |
| ⭐ MD5 弱比较碰撞（`md5(a)==md5(b)` 弱比较） | `search_skills("md5 weak compare")` — ⚠️ 0e 后必须纯数字！直接用 `QNKCDZO`+`240610708` 等已验证值 |
| 命令注入空格绕过 | `search_skills("command injection bypass")` |
| eval/RCE 技巧 | `search_skills("eval rce")` |
| SSTI 注入链 | `search_skills("ssti injection")` |
| 反序列化利用链 | `search_skills("deserialization")` |
| 文件上传 → RCE | `search_skills("file upload rce")` |
| PHP 代码审计 | `search_skills("php code audit")` |

## ⭐ PHP 伪协议速查（文件包含/参数传文件名时优先尝试）

**触发条件**：当题目出现以下任一特征时，**先试 php://filter 再想其他方法**：

| 触发特征 | 示例 |
|---------|------|
| 参数接受文件名/路径 | `?file=xxx` / `?page=xxx` / `?num=xxx` / `?path=xxx` |
| `include` / `require` / `include_once` | 源码中有这些函数 |
| 页面展示源码 | `highlight_file()` / `show_source()` |
| 题目要求"读文件"或"找 flag" | 明确要读取服务器文件 |

### 伪协议 Payload 速查

```
# 1. 读 PHP 源码（base64 编码，避免 PHP 执行）
?file=php://filter/read=convert.base64-encode/resource=flag.php
?file=php://filter/read=convert.base64-encode/resource=index.php

# 2. 读 PHP 源码（rot13 编码）
?file=php://filter/read=string.rot13/resource=flag.php

# 3. 直接读文件（如 .txt/.log 等非 PHP 文件）
?file=php://filter/resource=/etc/passwd

# 4. 代码执行
?file=php://input  (POST body 中放 PHP 代码)
?file=data://text/plain;base64,PD9waHAgc3lzdGVtKCdjYXQgL2ZsYWcnKTs/Pg==
```

### ⚠️ 关键提醒

1. **不要只想着"绕过"，先想能不能"直接读"** — 很多题目的参数接受文件名，可以直接用伪协议读 flag.php，根本不需要绕过任何过滤
2. **`convert.base64-encode` 是万能读取器** — PHP 文件被 include 会执行，但 base64 编码后不会执行，可以拿到源码
3. **参数名不一定叫 `file`** — 可能是 `page`、`num`、`path`、`template` 等，只要参数值被当作文件路径/名处理就可能有效
4. **拿到 base64 后用 `crypto_decode` 工具解码** — 不要自己脑补解码结果

## 常见 flag 位置速查

**⚠️ RCE 得手后，必须按以下优先级测试 flag 位置，不要停留在当前目录的 flag.php：**

```
优先级 1（最常见）: cat /flag
优先级 2:           cat /flag.txt
优先级 3:           ls /  → 找到根目录的 flag 文件名
优先级 4:           cat /var/www/html/flag.php
优先级 5:           cat /home/ctf/flag
优先级 6:           cat /root/flag
其他位置:           /environment, /proc/self/environ, env 命令
```

**注意**：`ls` 默认列当前目录（`/var/www/html/`），根目录的 `/flag` 需要 `ls /` 才能看到。

## 常见 CTF Web 题型速判

| 题目特征 | 可能考点 | 推荐路由 |
|---------|---------|---------|
| 参数接受文件名/路径 | ⭐ **先试 php://filter 读 flag** | 见上方「PHP 伪协议速查」 |
| 页面只有登录框 | SQL 注入 / 弱口令 / 条件竞争 | `search_skills("php bypass")` |
| 页面有代码展示 | 代码审计 | `search_skills("php code audit")` |
| eval/system 字样 | RCE + 空格/关键字绕过 | `search_skills("eval rce")` + `search_skills("command injection bypass")` |
| eval + 长度限制 | RCE + `$_GET` 链式传参绕长度 | 见下方「RCE + 长度限制绕过」 |
| 文件上传功能 | 后缀绕过 / MIME 绕过 | `search_skills("file upload rce")` |
| 页面模板渲染 | SSTI | `search_skills("ssti injection")` |
| 序列化/反序列化 | PHP/Java 反序列化 | `search_skills("deserialization")` |
| 有 WAF/过滤提示 | 正则绕过 / 编码绕过 | `search_skills("php bypass")` + `search_skills("command injection bypass")` |

## RCE + 长度限制绕过（首推策略）

当 `eval()` 有 `strlen()` 长度限制时（如 ≤ 18 字符），**首推 `$_GET` 链式传参**：

### 标准解法

```
?get=eval($_GET['A']);&A=system('cat /flag');
```

**原理**：
- `eval($_GET['A'])` = 16 字符，通过长度限制
- 真正的命令在第二个 GET 参数 `A` 中，没有长度限制
- PHP 会先执行 `eval()`，将 `$_GET['A']` 的值作为 PHP 代码执行

### 变体

| 长度限制 | payload | 字符数 |
|---------|---------|--------|
| ≤ 18 | `eval($_GET['A']);` | 16 |
| ≤ 18 | `eval($_GET[0]);` | 14 |
| ≤ 16 | `eval($_GET[A]);` | 13（无引号，PHP 自动转字符串） |
| ≤ 12 | `$_GET[0]();` | 10（A 参数传函数名如 `system`，另一个参数传命令） |

### 注意事项
- 不要花时间在缩短 payload 上（如用 `?>` 退出 PHP 模式、用反引号等），**链式传参是通用解法**
- 双 GET 参数 URL 格式：`?get=eval($_GET['A']);&A=system('cat /flag');`
- 用 `python_execute` 工具构造请求，而非 fetch 工具（fetch 可能不支持多参数）

## ⭐ preg_replace / str_replace 双写绕过速查

**触发条件**：源码含 `preg_replace('/X/', '', $str)` 或 `str_replace('X', '', $str)`，且替换后需 `$str === "X"`

### 核心原理
在关键词中间嵌入完整关键词，替换删除内层后，外层拼合出原词。

### 通用构造公式
```
输入 = 关键词前半 + 关键词 + 关键词后半
```

### 常见过滤词速查表

| 过滤关键词 | 双写输入 | 替换过程 | 结果 |
|-----------|---------|---------|------|
| NSSCTF | `NSSNSSCTFCTF` | 删中间NSSCTF → NSS+CTF | `NSSCTF` ✅ |
| flag | `flflagag` | 删中间flag → fl+ag | `flag` ✅ |
| cat | `cacatt` | 删中间cat → ca+t | `cat` ✅ |
| system | `syssystemtem` | 删中间system → sys+tem | `system` ✅ |
| hack | `hahackck` | 删中间hack → ha+ck | `hack` ✅ |
| cmd | `cmcmdd` | 删中间cmd → cm+d | `cmd` ✅ |
| exec | `exexecec` | 删中间exec → ex+ec | `exec` ✅ |

### ⚠️ 关键注意事项
1. **大小写绕过不适用** — 替换后返回 `NssCTF`，不等于 `"NSSCTF"`，严格比较失败
2. **识别信号** — 看到 `preg_replace('/X/', '', $str)` + `$str === "X"` → 立即双写
3. **str_replace 同理** — `str_replace` 也是一次替换，双写同样有效
4. **多次替换** — 如果代码多次调用 `preg_replace`，可能需要三写/四写，但 CTF 中通常只需双写
</workflow_ctf_web>'''


WAF_BYPASS_SIGNAL = '''<workflow_waf_bypass_signal>
# WAF 绕过 routing 信号（详细 payload 见 references/ 速查）

## 识别信号 → 路由

| 源码/响应信号 | 绕过方向 | 路由关键词 |
|--------------|---------|-----------|
| `preg_replace('/X/', '', $str)` + `$str === "X"` | **双写绕过**（核心） | `search_skills("waf bypass")` → 双写速查表 |
| 函数名被过滤（system/exec/passthru） | 函数名混淆（base64/拼接/可变函数） | `search_skills("function name obfuscation")` |
| 关键字被过滤（SELECT/cat/flag） | 关键字拆分 / 注释绕过 / 反转字符串 | `search_skills("keyword bypass")` |
| SQL 关键字过滤 | 大小写混合 / 内联注释 / 双重编码 | `search_skills("sql injection bypass")` |
| 命令分隔符过滤 | 换行符 / 管道符 / 逻辑运算 / 子 shell | `search_skills("command injection bypass")` |
| 命令本身被过滤（cat/id） | 变量拼接 / 通配符 / 空变量 / 转义混淆 | `search_skills("command obfuscation")` |
| XSS 标签过滤 | img/svg/body/input 事件处理器变体 | `search_skills("xss bypass")` |

## 核心判断

- **preg_replace 双写是 PHP WAF 最常见陷阱** — 大小写绕过不适用（替换后不等于原词）
- **优先级**：直接读 > 双写 > 编码 > 混淆 — 能不绕过就不绕过
- **payload 详细值**（${IFS}/$IFS$9 等分隔符、Base64 编码模板、注释符变体等）→ 通过 `search_skills("waf bypass")` 查询 references
</workflow_waf_bypass_signal>'''


RAPID_CHECKLIST_WORKFLOW = '''<workflow_rapid_checklist>
# 渗透速查与 Payload 路由

**仅在路由已明确后使用**。本流程用于快速查找，不替代方法论或工作流选择。

## 使用场景

- 快速回忆某类漏洞或阻塞点应该先看什么
- 快速筛选 Payload 家族、绕过方向和验证顺序
- 快速确认 AI、MCP、容器、WebSocket、JWT、文件、认证、SSRF 等常见测试卡片
- 从"我知道要测什么"进入"我先从哪一类验证开始"

## CTF 专项速查

> CTF 题目优先用 ctf-web 速查（见 CTF_WEB_WORKFLOW），以下为快速卡片：

| 场景 | 快速定位 |
|------|---------|
| PHP 弱比较 → 0e 开头 MD5 值 | `search_skills("php bypass")` |
| 命令注入空格绕过 → ${IFS}/$IFS$9/< | `search_skills("command injection bypass")` |
| eval 无回显 → 写文件/DNS 外带 | `search_skills("eval rce")` |

## 快速路由卡片

### Web 注入 / 输出执行
- SQLi → `'`, `"`, `)`, 布尔差异, 时间差异, 报错差异 — `search_skills("sql injection")`
- XSS → `<script>`, `<img onerror>`, `javascript:`, DOM sink — `search_skills("xss")`
- 命令注入 → `;id`, `|id`, 子 shell — `search_skills("command injection")`
- SSTI → `{{7*7}}`, `${7*7}`, 模板引擎指纹 — `search_skills("ssti injection")`
- XXE → `<!ENTITY>`, 参数实体, OOB 外带 — `search_skills("xxe")`

### 认证 / 逻辑 / Token
- JWT → none算法, 算法篡改, 密钥爆破, jku/x5u 注入 — `search_skills("jwt attack")`
- CSRF → 缺少 Token, Token 可预测, Referer 校验缺陷 — `search_skills("csrf")`
- IDOR → 修改 ID 参数, 批量遍历 — `search_skills("idor")`
- 支付逻辑 → 金额篡改, 负数, 竞态 — `search_skills("payment logic")`

### AI / MCP
- Prompt 注入 → 直接/间接/CoT 干扰 — `search_skills("prompt injection")`
- 工具滥用 → MCP 投毒/指令覆盖 — `search_skills("mcp abuse")`
- 身份逃逸 → 角色越界/权限漂移 — `search_skills("identity escape")`

## 详细参考
- 速查与 Payload 整合参考 → `search_skills("rapid checklist payloads")`
- Payload 详细集合 → `search_skills("payload collection")`
- 测试方法论 → `search_skills("testing methodology")`
</workflow_rapid_checklist>'''
