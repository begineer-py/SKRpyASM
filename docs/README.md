# SKRpyASM 文档目录

本目录包含 SKRpyASM 项目的详细技术文档。

## 📚 文档索引

### 核心文档

- **[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md)** - 完整的技术白皮书（主文档）
  - 系统概述与架构
  - 三层 AI Agent 架构
  - 核心技术特点
  - CVE Intelligence 情报系统
  - 完整 API 路由映射

- **[../README.md](../README.md)** - 项目简介与快速开始

- **[../CLAUDE.md](../CLAUDE.md)** - Claude Code 项目配置（包含完整的开发与部署指令，是部署命令的权威来源）

### CVE Intelligence 系统

- **[CVE_API_GUIDE.md](CVE_API_GUIDE.md)** - CVE Intelligence REST API 使用指南
  - 7 个 API 端点详细说明
  - Tags 搜索功能
  - 使用场景示例
  - API Key 管理

- **[CVE_IMPLEMENTATION_SUMMARY.md](CVE_IMPLEMENTATION_SUMMARY.md)** - CVE Intelligence 实现总结
  - 架构设计
  - 三层缓存策略
  - 自动豐富化流程
  - 性能优化

### 开发文档

- **[APP_DOC_AUDIT.md](APP_DOC_AUDIT.md)** - 各 app 实作与文档差异稽核
  - 实际职责
  - 公开 API 范围
  - 文档误差与缺口
  - 后续补写建议

- **[auto.md](auto.md)** - `apps/auto` 内部自动化框架说明

- **[core.md](core.md)** - `apps/core` 模型层与公开 API 说明

- **[analyze_ai.md](analyze_ai.md)** - `apps/analyze_ai` 初步分析与规划流程说明

- **[http_sender.md](http_sender.md)** - `apps/http_sender` fuzzing 入口说明

- **[api_keys.md](api_keys.md)** - `apps/api_keys` API key 与 Agent LLM config 说明

- **[ai_assistant.md](ai_assistant.md)** - `apps/ai_assistant` REST/SSE 接口说明

- **[scheduler.md](scheduler.md)** - `apps/scheduler` 调度 API 与后台任务说明

- **[flaresolverr.md](flaresolverr.md)** - `apps/flaresolverr` crawler/request 流程说明

- **[targets.md](targets.md)** - `apps/targets` target/seed 与资产联动说明

- **[nmap_scanner.md](nmap_scanner.md)** - Nmap 扫描派发说明

- **[subfinder.md](subfinder.md)** - Subfinder / Amass recon chain 说明

- **[nuclei_scanner.md](nuclei_scanner.md)** - Nuclei 漏洞扫描与技术辨识说明

- **[get_all_url.md](get_all_url.md)** - GAU URL 收集说明

- **[technical_details.md](technical_details.md)** - 技术细节文档

- **[file_references.md](file_references.md)** - 文件引用索引

- **[message_loading_analysis.md](message_loading_analysis.md)** - 消息加载分析

- **[MESSAGE_LOADING_INDEX.md](MESSAGE_LOADING_INDEX.md)** - 消息加载索引

- **[README_DOCUMENTATION.md](README_DOCUMENTATION.md)** - README 文档说明

### 项目管理

- **[DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md)** - 交付检查清单

## 🗂️ 文档结构

```
C2_Django_AI_git/
├── SKRpyASM_技術白皮書.md          # 主技术白皮书（完整版）
├── README.md                        # 项目简介
├── CLAUDE.md                        # Claude Code 配置
├── docs/                            # 详细文档目录
│   ├── README.md                    # 本文件
│   ├── APP_DOC_AUDIT.md             # app 文档稽核
│   ├── auto.md                      # auto app 说明
│   ├── core.md                      # core app 说明
│   ├── analyze_ai.md                # analyze_ai app 说明
│   ├── http_sender.md               # http_sender app 说明
│   ├── api_keys.md                  # api_keys app 说明
│   ├── ai_assistant.md              # ai_assistant app 说明
│   ├── scheduler.md                 # scheduler app 说明
│   ├── flaresolverr.md              # flaresolverr app 说明
│   ├── targets.md                   # targets app 说明
│   ├── nmap_scanner.md              # nmap_scanner 说明
│   ├── subfinder.md                 # subfinder 说明
│   ├── nuclei_scanner.md            # nuclei_scanner 说明
│   ├── get_all_url.md               # get_all_url 说明
│   ├── CVE_API_GUIDE.md             # CVE API 指南
│   ├── CVE_IMPLEMENTATION_SUMMARY.md # CVE 实现总结
│   ├── DELIVERY_CHECKLIST.md        # 交付检查清单
│   ├── technical_details.md         # 技术细节
│   ├── file_references.md           # 文件引用
│   ├── message_loading_analysis.md  # 消息加载分析
│   ├── MESSAGE_LOADING_INDEX.md     # 消息加载索引
│   └── README_DOCUMENTATION.md      # README 文档
```

> 部署與開發指令已收斂至根目錄 [`../CLAUDE.md`](../CLAUDE.md) 的 **Development Commands** 章節。

## 📖 阅读顺序建议

### 新用户

1. **[../README.md](../README.md)** - 了解项目概况
2. **[../CLAUDE.md](../CLAUDE.md)** - 开发与部署指令（Quick Start + Development Commands）
3. **[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md)** - 深入理解架构

### 开发者

1. **[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md)** - 完整技术架构
2. **[APP_DOC_AUDIT.md](APP_DOC_AUDIT.md)** - 先看 app 与文档的落差
3. **[auto.md](auto.md)**、**[core.md](core.md)**、**[analyze_ai.md](analyze_ai.md)** - 核心 app 专页
4. **[http_sender.md](http_sender.md)**、**[api_keys.md](api_keys.md)**、**[ai_assistant.md](ai_assistant.md)**、**[scheduler.md](scheduler.md)**、**[flaresolverr.md](flaresolverr.md)** - 其余关键 app 专页
5. **[targets.md](targets.md)**、**[nmap_scanner.md](nmap_scanner.md)**、**[subfinder.md](subfinder.md)**、**[nuclei_scanner.md](nuclei_scanner.md)**、**[get_all_url.md](get_all_url.md)** - 公开入口与 scanner 子模块专页
6. **[technical_details.md](technical_details.md)** - 技术实现细节
7. **[CVE_IMPLEMENTATION_SUMMARY.md](CVE_IMPLEMENTATION_SUMMARY.md)** - CVE 系统实现

### API 使用者

1. **[CVE_API_GUIDE.md](CVE_API_GUIDE.md)** - CVE API 完整指南
2. **[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md)** - 白皮书附录中的完整 API 路由映射

## 🔍 快速查找

### 查找 API 端点
- 完整 API 映射：[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md) 第十二章
- CVE API：[CVE_API_GUIDE.md](CVE_API_GUIDE.md)

### 查找架构设计
- 三层 AI Agent：[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md) 第二章
- App 现况与文档落差：[APP_DOC_AUDIT.md](APP_DOC_AUDIT.md)
- CVE Intelligence：优先参考 [CVE_API_GUIDE.md](CVE_API_GUIDE.md) 与 [CVE_IMPLEMENTATION_SUMMARY.md](CVE_IMPLEMENTATION_SUMMARY.md)

### 查找部署指南
- Quick Start：[../README.md](../README.md) 的 Quick Start 段落
- 完整开发与部署指令：[../CLAUDE.md](../CLAUDE.md) 的 Development Commands 章節（Migrations / Tests / Celery / CI）

## 📝 文档维护

- 主文档：`SKRpyASM_技術白皮書.md` 是最权威和最完整的文档
- 专题文档：`docs/` 目录下的文档提供特定主题的详细说明
- 更新频率：随系统功能更新而更新

---

_最后更新：2026-06-06_
