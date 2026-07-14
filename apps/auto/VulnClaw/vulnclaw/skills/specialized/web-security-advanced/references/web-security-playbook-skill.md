---
name: web-security-playbook
description: Authorized web security reference for selecting attack categories, payload families, bypass notes, workflow summaries, and mitigations across web, API, JWT, cloud, AI, framework, and WebSocket testing. Use for pentest planning, report drafting, or converting the extracted wiki into narrower web-focused skills.
tags: ['web', 'security']
---

# Web Security Playbook

Use this skill for authorized security testing, defense validation, training, or documentation work.

## When To Use

- The user needs a category-level web testing playbook rather than a single exploit recipe.
- The task involves choosing among multiple web attack families, payload styles, or bypass approaches.
- The user wants to turn the extracted wiki into narrower skills, checklists, notes, or reports.

## When Not To Use

- A narrower existing skill already covers the request better.
- The task is primarily internal network, AD, Windows, Exchange, or SharePoint work.
- The user only needs a tool cheat sheet rather than attack-family guidance.

## Workflow

1. Start with `search_skills("web playbook index")`, then narrow to 1-3 relevant category files.
2. If the request still spans multiple attack families, keep the answer grouped by category instead of by individual payload.
3. If a specific payload entry is needed, query the relevant `search_skills("...")` entries; any extracted source path still shown in entries should be treated as provenance only.
4. Return only the payload families, variants, prerequisites, bypass notes, OPSEC notes, and mitigations that match the authorized scope.
5. When writing a new skill, checklist, or report, rewrite the selected material into the target format instead of copying whole reference files.

## Category Map

- 点击劫持 | `search_skills("clickjacking")` |
- 供应链攻击 | `search_skills("supply chain")` |
- 缓存与CDN安全 | `search_skills("cache cdn")` |
- 开放重定向 | `search_skills("open redirect")` |
- 框架漏洞 | `search_skills("framework vulnerability")` |
- 请求走私 | `search_skills("request smuggling")` |
- 认证漏洞 | `search_skills("authentication")` |
- 文件漏洞 | `search_skills("file vulnerability")` |
- 业务逻辑漏洞 | `search_skills("business logic")` |
- 原型链污染 | `search_skills("prototype pollution")` |
- 云安全漏洞 | `search_skills("cloud security")` |
- AI安全 | `search_skills("ai security")` |
- API安全 | `search_skills("api security")` |
- CSRF跨站请求伪造 | `search_skills("csrf")` |
- JWT安全 | `search_skills("jwt")` |
- LFI/RFI文件包含 | `search_skills("lfi rfi")` |
- RCE远程代码执行 | `search_skills("rce")` |
- SQL/NoSQL注入 | `search_skills("sql injection")` |
- SSRF服务端请求伪造 | `search_skills("ssrf")` |
- SSTI模板注入 | `search_skills("ssti")` |
- WebSocket安全 | `search_skills("websocket")` |
- XSS跨站脚本 | `search_skills("xss")` |
- XXE实体注入 | `search_skills("xxe")` |

## Notes

- Prefer 1-3 categories per request, not the whole corpus.
- Use `search_skills("web playbook index")` as the first stop for category selection.
- Use source markdown files for detailed commands and tutorial text.
- Keep outputs scoped to the user's target stack and authorization.

