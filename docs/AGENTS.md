# docs/ - Documentation Guide

> **Language**: 中文（与项目保持一致）
> **Purpose**: MemNexus 技术文档、协议规范与架构设计

---

## Overview

This directory contains comprehensive technical documentation for MemNexus, covering architecture, protocols, APIs, and development guides.

## Documentation Structure

| File | Purpose | Audience |
|------|---------|----------|
| `ARCHITECTURE.md` | 系统架构设计、组件关系、数据流 | 开发者、架构师 |
| `PROTOCOL_ACP.md` | ACP (Agent Client Protocol) 规范 | Agent 开发者 |
| `PROTOCOL_MCP.md` | MCP (Model Context Protocol) 规范 | Tool 开发者 |
| `API.md` | REST API & WebSocket 参考 | 前端/集成开发者 |
| `CLI.md` | 命令行工具完整参考 | 用户、运维 |
| `DEVELOPMENT.md` | 开发环境搭建与贡献指南 | 贡献者 |
| `DEPLOYMENT.md` | 生产环境部署指南 | 运维工程师 |
| `GETTING_STARTED.md` | 快速入门教程 | 新用户 |
| `PRD.md` | 产品需求文档 | 产品、设计 |

## Documentation Conventions

### Language
- **Primary**: 中文（简体）- 与代码注释（英文）区分
- **Code examples**: 英文（与代码库一致）
- **API docs**: 双语（中文说明 + 英文 endpoint）

### Format
- Architecture docs: ASCII diagrams + PlantUML
- Protocol specs: JSON-RPC examples
- API docs: OpenAPI-style endpoint tables
- Tutorials: Step-by-step with code blocks

### File Naming
```
ARCHITECTURE.md      # 系统架构（大写，无空格）
PROTOCOL_ACP.md      # 协议规范（大写前缀）
API.md               # 接口文档
CLI.md               # CLI 文档
development.md       # 开发指南（小写，可接受）
```

## Where to Look

| Task | File | Notes |
|------|------|-------|
| 理解系统架构 | `ARCHITECTURE.md` | 从架构图开始 |
| 集成 ACP 协议 | `PROTOCOL_ACP.md` | JSON-RPC over stdio |
| 开发新 Agent | `PROTOCOL_ACP.md` + `API.md` | 协议 + 接口 |
| 部署到生产 | `DEPLOYMENT.md` | 安全、性能、运维 |
| 贡献代码 | `DEVELOPMENT.md` | 开发环境、PR 流程 |

## Cross-References

- Architecture diagrams reference `../src/memnexus/` modules
- Protocol specs reference `../src/memnexus/protocols/`
- API docs auto-generated from `../src/memnexus/server.py`

## Commands

```bash
# View docs
cat docs/ARCHITECTURE.md

# Search across docs
grep -r "WebSocket" docs/

# Check for stale references
grep -r "TODO\|FIXME\|XXX" docs/
```

---

**Keep docs in sync with code changes.** Update relevant doc when modifying:
- API endpoints (`server.py` → `API.md`)
- Protocol behavior (`protocols/` → `PROTOCOL_*.md`)
- Architecture changes (module renames → `ARCHITECTURE.md`)
