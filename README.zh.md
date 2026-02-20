# MemNexus - 多智能体协作系统

<p align="center">
  <a href="README.md">English</a> | <b>简体中文</b>
</p>

> **多智能体协作编排系统** - 打破 AI 编程工具的记忆孤岛

<p align="center">
  <a href="#-project-overview"><img src="https://img.shields.io/badge/Phase-3%20Complete-blue?style=for-the-badge" alt="Phase 3 Complete"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.12+-green?style=for-the-badge&logo=python" alt="Python 3.12+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Leeelics/MemNexus/releases"><img src="https://img.shields.io/github/v/release/Leeelics/MemNexus?style=for-the-badge" alt="Release"></a>
</p>

<p align="center">
  <a href="#-quick-start">快速开始</a> •
  <a href="#-documentation">文档</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-license">License</a>
</p>

## 🎯 项目简介

MemNexus 是一个本地 AI OS-level 记忆守护进程，旨在连接 Claude Code、Kimi CLI、Codex 等 AI 编程工具，实现：

- **上下文共享** - 多 Agent 共享记忆，互相可见输出和代码更改
- **任务编排** - Architect → Backend → Frontend → Testing 自动化流程
- **实时监控** - Web Dashboard 实时查看任务状态
- **人工干预** - 关键节点暂停、调整、重新分配任务

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      MemNexus Core                          │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Session    │    Agent     │    Task      │    Memory      │
│  (工作空间)   │  (AI助手实例) │   (任务单元)  │   (记忆存储)    │
└──────────────┴──────────────┴──────────────┴────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌──────────┐
   │  ACP    │          │  RAG    │          │  React   │
   │ Protocol│          │ Pipeline│          │ Frontend │
   └─────────┘          └─────────┘          └──────────┘
```

## 🚀 快速开始

### 安装

MemNexus 使用 [uv](https://github.com/astral-sh/uv) 进行快速、可靠的 Python 包管理。

```bash
# 克隆仓库
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus

# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖（推荐）
uv sync

# 激活虚拟环境
source .venv/bin/activate

# 或者使用 pip
pip install -e ".[dev]"
```

### 启动服务

```bash
# 启动后端服务
memnexus server

# 启动前端 (新终端)
cd frontend
npm install
npm run dev
```

### 创建第一个会话

```bash
# 创建会话
memnexus session-create "My Project" --agents claude,kimi

# 包装 CLI 工具
memnexus wrapper sess_abc123 claude --name claude-backend

# 或者使用 ACP 协议
memnexus acp-connect sess_abc123 --cli claude
```

## 📖 使用指南

### Phase 1: 基础功能

```bash
# CLI Wrapper 模式
memnexus wrapper <session_id> <cli> [--name <name>]
memnexus agent-launch <session_id> <cli>

# 内存操作
memnexus memory-search <session_id> "query"
memnexus memory-stats
```

### Phase 2: 协议与 RAG

```bash
# ACP 协议连接
memnexus acp-connect <session_id> --cli claude
memnexus acp-connect <session_id> -c kimi -n kimi-agent

# RAG 文档处理
memnexus rag-ingest <session_id> <file_path>
memnexus rag-query <session_id> "query" -k 10

# 实时同步监控
memnexus sync-watch <session_id>
```

### Phase 3: 编排与干预

```bash
# 多 Agent 编排
memnexus orchestrate <session_id> --strategy parallel
memnexus plan-show <session_id>

# 人工干预
memnexus intervention-list <session_id>
memnexus intervention-resolve <id> -a approve
```

## 🛠️ 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Web Framework | FastAPI + Uvicorn | 异步 Web 服务和 API |
| CLI Framework | Typer + Rich | 交互式命令行界面 |
| Vector Database | LanceDB | 嵌入式向量 + 全文搜索 |
| RAG Pipeline | LlamaIndex | 文档分块和检索 |
| Frontend | React + TypeScript + Tailwind | 现代化 Web 界面 |
| State Management | Zustand | 前端状态管理 |
| Protocol | ACP (JSON-RPC) | Agent 通信协议 |

## 📁 项目结构

```
MemNexus/
├── src/memnexus/
│   ├── agents/          # Agent 实现
│   ├── core/            # 核心模块 (Config, Session)
│   ├── memory/          # 内存系统 (Store, RAG, Sync)
│   ├── orchestrator/    # 编排系统 (Engine, Scheduler, Intervention)
│   ├── protocols/       # 协议实现 (ACP)
│   ├── cli.py           # CLI 入口
│   └── server.py        # FastAPI 服务
├── frontend/            # React 前端
│   └── src/
│       ├── components/  # 通用组件
│       ├── pages/       # 页面组件
│       ├── services/    # API 服务
│       └── store/       # 状态管理
├── docs/                # 设计文档
└── pyproject.toml       # 项目配置
```

## 🔌 API 端点

### Sessions
- `GET /api/v1/sessions` - 列出所有会话
- `POST /api/v1/sessions` - 创建会话
- `GET /api/v1/sessions/{id}` - 获取会话详情

### Agents
- `POST /api/v1/sessions/{id}/agents/connect` - ACP 连接
- `POST /api/v1/sessions/{id}/agents/launch` - 启动 Agent

### Memory & RAG
- `GET /api/v1/sessions/{id}/memory` - 查询内存
- `POST /api/v1/sessions/{id}/rag/query` - RAG 查询

### Orchestration
- `POST /api/v1/sessions/{id}/plan` - 创建执行计划
- `POST /api/v1/sessions/{id}/execute` - 执行计划
- `GET /api/v1/sessions/{id}/interventions` - 获取干预列表

### WebSocket
- `WS /ws` - 实时更新
- `WS /ws/sync/{session_id}` - 内存同步

## 📊 开发阶段

- ✅ **Phase 1** - 快速原型 (CLI Wrapper + Shared Memory)
- ✅ **Phase 2** - 协议实现 (ACP + RAG + Real-time Sync)
- ✅ **Phase 3** - 完整产品 (Orchestrator + Intervention + React Frontend)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📝 License

MemNexus is licensed under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2026 Leeelics

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

### Why MIT License?

We chose the MIT License because it:
- ✅ Allows free use for personal and commercial projects
- ✅ Permits modification and distribution
- ✅ Provides liability protection
- ✅ Is simple and widely understood

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - System design and architecture
- [Getting Started](docs/GETTING_STARTED.md) - Step-by-step setup guide
- [API Reference](docs/API.md) - Complete API documentation
- [CLI Guide](docs/CLI.md) - Command-line interface reference
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and development
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [ACP Protocol](docs/PROTOCOL_ACP.md) - ACP protocol specification
- [MCP Protocol](docs/PROTOCOL_MCP.md) - MCP protocol specification

## 👤 Author

**Leeelics** - [GitHub](https://github.com/Leeelics)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [LlamaIndex](https://www.llamaindex.ai/) - RAG framework
- [LanceDB](https://lancedb.github.io/lancedb/) - Vector database
- [React](https://react.dev/) - Frontend framework

---

<p align="center">
  <b>MemNexus</b> - 让多个 AI 助手协同工作，打破记忆孤岛
</p>

<p align="center">
  <a href="https://github.com/Leeelics/MemNexus">⭐ Star us on GitHub</a>
</p>
