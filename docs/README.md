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

- **[../CLAUDE.md](../CLAUDE.md)** - Claude Code 项目配置

### 构建与部署

- **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - 详细的构建与部署指南
  - 环境配置
  - 依赖安装
  - 服务启动
  - 生产环境部署

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
│   ├── BUILD_GUIDE.md               # 构建指南
│   ├── CVE_API_GUIDE.md             # CVE API 指南
│   ├── CVE_IMPLEMENTATION_SUMMARY.md # CVE 实现总结
│   ├── DELIVERY_CHECKLIST.md        # 交付检查清单
│   ├── technical_details.md         # 技术细节
│   ├── file_references.md           # 文件引用
│   ├── message_loading_analysis.md  # 消息加载分析
│   ├── MESSAGE_LOADING_INDEX.md     # 消息加载索引
│   └── README_DOCUMENTATION.md      # README 文档
├── test_cve_api.sh                  # CVE API 测试脚本
└── test_cve_intelligence.py         # CVE Intelligence 测试脚本
```

## 📖 阅读顺序建议

### 新用户

1. **[../README.md](../README.md)** - 了解项目概况
2. **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - 快速启动系统
3. **[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md)** - 深入理解架构

### 开发者

1. **[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md)** - 完整技术架构
2. **[technical_details.md](technical_details.md)** - 技术实现细节
3. **[CVE_IMPLEMENTATION_SUMMARY.md](CVE_IMPLEMENTATION_SUMMARY.md)** - CVE 系统实现

### API 使用者

1. **[CVE_API_GUIDE.md](CVE_API_GUIDE.md)** - CVE API 完整指南
2. **[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md)** - 第十二章：完整 API 路由映射

## 🔍 快速查找

### 查找 API 端点
- 完整 API 映射：[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md) 第十二章
- CVE API：[CVE_API_GUIDE.md](CVE_API_GUIDE.md)

### 查找架构设计
- 三层 AI Agent：[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md) 第二章
- CVE Intelligence：[../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md) 第十三章

### 查找部署指南
- 快速启动：[BUILD_GUIDE.md](BUILD_GUIDE.md)
- 环境配置：[BUILD_GUIDE.md](BUILD_GUIDE.md) + [../SKRpyASM_技術白皮書.md](../SKRpyASM_技術白皮書.md) 第十四章

## 📝 文档维护

- 主文档：`SKRpyASM_技術白皮書.md` 是最权威和最完整的文档
- 专题文档：`docs/` 目录下的文档提供特定主题的详细说明
- 更新频率：随系统功能更新而更新

---

_最后更新：2026-05-19_
