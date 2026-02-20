# MemNexus - 多智能体协作系统

<p align="center">
  <a href="README.md">English</a> | <b>简体中文</b>
</p>

> **多智能体协作编排系统** - 打破 AI 编程工具的记忆孤岛

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.12+-green?style=for-the-badge&logo=python" alt="Python 3.12+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Leeelics/MemNexus/releases"><img src="https://img.shields.io/github/v/release/Leeelics/MemNexus?style=for-the-badge" alt="Release"></a>
</p>

<p align="center">
  <a href="#-quick-start">快速开始</a> •
  <a href="#-features">功能特性</a> •
  <a href="#-documentation">文档</a> •
  <a href="#-api-reference">API</a>
</p>

## 🎯 项目简介

MemNexus 是一个本地 AI 记忆守护进程，旨在连接 Claude Code、Kimi CLI、Codex 等 AI 编程工具，实现：

- **上下文共享** - 多 Agent 共享记忆，互相可见输出和代码更改
- **任务编排** - Architect → Backend → Frontend → Testing 自动化流程
- **实时监控** - Web Dashboard 实时查看任务状态
- **人工干预** - 关键节点暂停、调整、重新分配任务

## 🚀 快速开始

### 安装

MemNexus 使用 [uv](https://github.com/astral-sh/uv) 进行快速、可靠的 Python 包管理。

```bash
# 克隆仓库
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus

# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync
source .venv/bin/activate
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
memnexus session-create "My Project"

# 通过 ACP 协议连接 Claude
memnexus acp-connect <session_id> --cli claude --name claude-backend

# 或包装现有的 CLI 工具
memnexus wrapper <session_id> kimi --name kimi-frontend
```

## ✨ 功能特性

### 🤖 多智能体连接

在共享会话中连接多个 AI 助手协同工作：

```bash
# ACP 协议原生连接（推荐）
memnexus acp-connect <session_id> --cli claude
memnexus acp-connect <session_id> --cli kimi -n kimi-agent

# CLI 包装模式（适用于任何 CLI 工具）
memnexus wrapper <session_id> <cli> --name <agent-name>
```

### 🧠 共享记忆系统

基于 LanceDB 的向量共享记忆：

```bash
# 搜索会话记忆
memnexus memory-search <session_id> "API endpoints"

# 查看记忆统计
memnexus memory-stats
```

### 📚 RAG 文档处理

基于 LlamaIndex 的高级文档处理：

```bash
# 导入文档到会话
memnexus rag-ingest <session_id> README.md
memnexus rag-ingest <session_id> src/

# 带上下文查询
memnexus rag-query <session_id> "架构是什么样的？" -k 5
```

### 🎼 多智能体编排

带任务依赖的多智能体协调：

```bash
# 创建执行计划
memnexus orchestrate <session_id> --strategy parallel

# 查看执行计划
memnexus plan-show <session_id>
```

支持策略：
- `sequential` - 顺序执行，一次一个 Agent
- `parallel` - 并行执行，多 Agent 同时工作
- `pipeline` - 流水线执行
- `adaptive` - 自适应，AI 自动决定最优策略

### 👤 人工干预

在关键节点请求人工审批：

```bash
# 列出待处理的干预
memnexus intervention-list <session_id>

# 解决干预
memnexus intervention-resolve <id> -a approve
memnexus intervention-resolve <id> -a reject -m "需要修改"
```

### 📡 实时同步

实时监控记忆变化：

```bash
memnexus sync-watch <session_id>
```

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
├── src/memnexus/          # Python 后端
│   ├── agents/            # Agent 实现
│   ├── core/              # 核心模块
│   ├── memory/            # 内存系统
│   ├── orchestrator/      # 编排系统
│   ├── protocols/         # 协议实现
│   ├── cli.py             # CLI 入口
│   └── server.py          # FastAPI 服务
├── frontend/              # React 前端
│   └── src/
│       ├── components/    # 通用组件
│       ├── pages/         # 页面组件
│       ├── services/      # API 服务
│       └── store/         # 状态管理
├── docs/                  # 设计文档
└── pyproject.toml         # 项目配置
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

## 📖 文档

- [快速开始](docs/GETTING_STARTED.md) - 详细安装配置指南
- [架构概览](docs/ARCHITECTURE.md) - 系统设计与架构
- [API 文档](docs/API.md) - 完整 API 文档
- [CLI 指南](docs/CLI.md) - 命令行工具参考
- [开发指南](docs/DEVELOPMENT.md) - 贡献与开发
- [部署指南](docs/DEPLOYMENT.md) - 生产环境部署
- [ACP 协议](docs/PROTOCOL_ACP.md) - ACP 协议规范
- [MCP 协议](docs/PROTOCOL_MCP.md) - MCP 协议规范

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📝 License

MemNexus 基于 [MIT License](LICENSE) 开源。

```
MIT License

Copyright (c) 2026 Leeelics

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
```

## 👤 作者

**Leeelics** - [GitHub](https://github.com/Leeelics)

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [LlamaIndex](https://www.llamaindex.ai/) - RAG 框架
- [LanceDB](https://lancedb.github.io/lancedb/) - 向量数据库
- [React](https://react.dev/) - 前端框架
- [Astral](https://astral.sh/) - uv 包管理器

---

<p align="center">
  <b>MemNexus</b> - 让多个 AI 助手协同工作，打破记忆孤岛
</p>

<p align="center">
  <a href="https://github.com/Leeelics/MemNexus">⭐ GitHub 上给我们 Star</a>
</p>
