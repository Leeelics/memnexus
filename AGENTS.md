# MemNexus - AI Agent 开发指南

> **目标读者**: AI 编程助手（如 Claude Code、Kimi CLI、Codex 等）
>
> **语言**: 中文（与项目文档保持一致）

---

## 项目概述

MemNexus 是一个**多智能体协作编排系统**（Multi-Agent Collaboration Orchestration System），旨在连接不同的 AI 编程工具（Claude Code、Kimi CLI、Codex 等），打破它们之间的记忆孤岛，实现上下文共享和任务协同。

### 核心功能

- **上下文共享** - 多个 AI Agent 共享记忆，互相可见输出和代码更改
- **任务编排** - Architect → Backend → Frontend → Testing 自动化工作流
- **实时监控** - Web Dashboard 实时查看任务状态
- **人工干预** - 关键节点暂停、调整、重新分配任务

---

## 技术栈

### 后端（Python）

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web 框架 | FastAPI + Uvicorn | >=0.115 | 异步 Web 服务和 API |
| CLI 框架 | Typer + Rich | >=0.15 | 交互式命令行界面 |
| 向量数据库 | LanceDB | >=0.18 | 嵌入式向量 + 全文搜索 |
| RAG 管道 | LlamaIndex | >=0.12 | 文档分块和检索 |
| 数据验证 | Pydantic | >=2.10 | 数据模型和配置 |
| 数据库 | SQLAlchemy + asyncpg | >=2.0 | ORM 和数据库访问 |
| 缓存 | Redis | >=5.2 | 缓存和消息队列 |

### 前端

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | React | ^18.2 | UI 框架 |
| 语言 | TypeScript | ^5.3 | 类型安全 |
| 构建 | Vite | ^5.0 | 构建工具 |
| 样式 | Tailwind CSS | ^3.3 | CSS 框架 |
| 路由 | react-router-dom | ^6.20 | 客户端路由 |
| 状态 | Zustand | ^4.4 | 状态管理 |

---

## 项目结构

```
MemNexus/
├── src/memnexus/              # Python 后端源代码
│   ├── __init__.py            # 包入口，导出核心类
│   ├── cli.py                 # CLI 入口点（Typer）
│   ├── server.py              # FastAPI 服务器
│   ├── core/                  # 核心模块
│   │   ├── config.py          # 配置管理（Pydantic Settings）
│   │   └── session.py         # 会话管理器
│   ├── agents/                # Agent 实现
│   │   ├── base.py            # BaseAgent 抽象基类
│   │   └── wrapper.py         # CLI Wrapper 实现
│   ├── memory/                # 记忆系统
│   │   ├── store.py           # LanceDB 向量存储
│   │   ├── context.py         # 上下文管理器
│   │   ├── rag.py             # RAG 管道
│   │   └── sync.py            # 内存同步
│   ├── protocols/             # 协议实现
│   │   └── acp.py             # ACP 协议（JSON-RPC over stdio）
│   └── orchestrator/          # 编排系统
│       ├── engine.py          # 编排引擎
│       ├── scheduler.py       # 任务调度器
│       └── intervention.py    # 人工干预系统
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── App.tsx            # 应用根组件
│   │   ├── components/        # 可复用组件
│   │   ├── pages/             # 页面组件
│   │   ├── services/          # API 服务
│   │   └── store/             # Zustand 状态管理
│   └── package.json           # 前端依赖
├── tests/                     # 测试目录
│   └── test_session.py        # 会话管理测试
├── docs/                      # 文档目录
│   ├── ARCHITECTURE.md        # 架构设计文档（中文）
│   ├── DEVELOPMENT.md         # 开发指南
│   ├── API.md                 # API 文档
│   ├── CLI.md                 # CLI 文档
│   └── PROTOCOL_ACP.md        # ACP 协议规范
├── pyproject.toml             # Python 项目配置
├── uv.lock                    # uv 锁定文件
└── README.md / README.zh.md   # 项目说明（双语）
```

---

## 构建和运行

### 前置要求

- Python 3.12+
- Node.js 18+（前端开发）
- [uv](https://github.com/astral-sh/uv) 包管理器（推荐）

### 安装依赖

```bash
# 使用 uv（推荐）
uv sync
source .venv/bin/activate

# 或使用 pip
pip install -e ".[dev]"
```

### 启动服务

```bash
# 启动后端 API 服务器
memnexus server

# 开发模式（热重载）
memnexus server --reload

# 启动前端（新终端）
cd frontend
npm install
npm run dev
```

### 前端代理配置

前端 Vite 配置已设置代理，开发时前端（端口 3000）会自动代理到后端（端口 8080）：

```typescript
// frontend/vite.config.ts
server: {
  port: 3000,
  proxy: {
    '/api': { target: 'http://localhost:8080' },
    '/ws': { target: 'ws://localhost:8080', ws: true },
  },
}
```

---

## 测试命令

### Python 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_session.py -v

# 带覆盖率报告
uv run pytest --cov=memnexus --cov-report=html

# 排除慢测试
uv run pytest -m "not slow"
```

### 代码检查

```bash
# 格式化代码
uv run ruff format .

# 检查代码
uv run ruff check . --fix

# 类型检查
uv run mypy src/memnexus
```

### 前端测试

```bash
cd frontend
npm run lint
npm run build
```

---

## 代码风格指南

### Python 规范

- **行长度**: 100 字符
- **引号**: 双引号（ `"` ）
- **缩进**: 4 个空格
- **类型注解**: 强制使用，启用 mypy 严格模式
- **文档字符串**: 所有公共类和方法必须有 docstring

```python
# 示例代码风格
class SessionManager:
    """Manager for sessions with memory integration.
    
    Attributes:
        _sessions: 内存中的会话字典
        _context_managers: 上下文管理器缓存
    """
    
    async def create(
        self,
        name: str,
        description: str = "",
        strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL,
    ) -> Session:
        """Create a new session.
        
        Args:
            name: Session name
            description: Optional description
            strategy: Execution strategy
            
        Returns:
            Created session instance
        """
        ...
```

### TypeScript/React 规范

- 严格 TypeScript 模式
- 函数组件使用箭头函数
- 使用路径别名 `@/*` 导入

---

## 配置说明

配置通过环境变量或 `.env` 文件管理：

```bash
# 核心配置
MEMNEXUS_DEBUG=false              # 调试模式
MEMNEXUS_ENV=development          # 环境
MEMNEXUS_DATA_DIR=~/.memnexus     # 数据目录
MEMNEXUS_HOST=127.0.0.1           # 服务绑定地址
MEMNEXUS_PORT=8080                # 服务端口

# 数据库
MEMNEXUS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/memnexus
MEMNEXUS_REDIS_URL=redis://localhost:6379/0
MEMNEXUS_LANCEDB_URI=~/.memnexus/memory.lance

# 安全
MEMNEXUS_SECRET_KEY=change-me-in-production
```

---

## 核心 API 端点

### 会话管理

```
GET    /api/v1/sessions              # 列出所有会话
POST   /api/v1/sessions              # 创建会话
GET    /api/v1/sessions/{id}         # 获取会话详情
POST   /api/v1/sessions/{id}/start   # 启动会话
POST   /api/v1/sessions/{id}/pause   # 暂停会话
DELETE /api/v1/sessions/{id}         # 删除会话
```

### Agent 管理

```
GET    /api/v1/sessions/{id}/agents           # 列出会话中的 Agents
POST   /api/v1/sessions/{id}/agents           # 添加 Agent
POST   /api/v1/sessions/{id}/agents/launch    # 启动 CLI Wrapper 模式
POST   /api/v1/sessions/{id}/agents/connect   # ACP 协议连接
```

### 记忆系统

```
GET    /api/v1/sessions/{id}/memory           # 查询会话记忆
POST   /api/v1/sessions/{id}/memory           # 添加记忆
GET    /api/v1/memory/stats                   # 记忆统计
```

### RAG 管道

```
POST   /api/v1/sessions/{id}/rag/ingest       # 导入文档
POST   /api/v1/sessions/{id}/rag/query        # RAG 查询
```

### WebSocket

```
WS     /ws                         # 通用实时更新
WS     /ws/sync/{session_id}       # 会话记忆同步
```

---

## CLI 命令参考

```bash
# 会话管理
memnexus session-list                      # 列出会话
memnexus session-create "My Project"       # 创建会话
memnexus session-start <session_id>        # 启动会话
memnexus session-stop <session_id>         # 停止会话

# Agent 操作
memnexus agent-list                        # 列出 Agents
memnexus agent-launch <session_id> <cli>   # 启动 CLI Wrapper
memnexus wrapper <session_id> <cli>        # 包装模式运行

# ACP 协议
memnexus acp-connect <session_id> --cli <cli>  # ACP 连接

# 记忆操作
memnexus memory-search <session_id> <query>    # 搜索记忆
memnexus memory-stats                          # 记忆统计

# RAG
memnexus rag-ingest <session_id> <file>        # 导入文件
memnexus rag-query <session_id> <query>        # RAG 查询

# 实时同步
memnexus sync-watch <session_id>               # 监视记忆变化

# 编排
memnexus orchestrate <session_id> --strategy <strategy>
memnexus plan-show <session_id>
memnexus intervention-list <session_id>
memnexus intervention-resolve <id> -a <action>
```

---

## 安全注意事项

### 当前限制

- 无内置身份验证（计划中）
- CORS 默认允许所有来源（生产环境需配置）
- 无速率限制（建议添加反向代理）

### 生产环境建议

1. **修改默认密钥**
   ```bash
   export MEMNEXUS_SECRET_KEY="your-random-secret-key"
   ```

2. **限制 CORS 来源**
   ```python
   # src/memnexus/server.py
   allow_origins=["https://your-domain.com"]
   ```

3. **使用 HTTPS**
   - 配置 SSL/TLS 证书
   - 使用反向代理（Nginx/Traefik）

4. **最小权限运行**
   - 使用专用用户账户
   - 限制文件系统访问
   - 使用容器安全特性

---

## 开发工作流

### 添加新 Agent 支持

1. 在 `src/memnexus/agents/` 创建新文件
2. 继承 `BaseAgent` 类
3. 实现必需的方法
4. 在 `__init__.py` 中导出

```python
# src/memnexus/agents/custom.py
from memnexus.agents.base import BaseAgent, AgentConfig

class CustomAgent(BaseAgent):
    """自定义 Agent."""
    name = "custom"
    
    async def spawn(self, config: AgentConfig) -> Process:
        """启动进程."""
        pass
```

### 提交规范

使用 Conventional Commits 格式：

```
feat: 添加新的编排策略
fix: 修复内存同步问题
docs: 更新 API 文档
refactor: 简化任务调度器
test: 添加干预系统测试
chore: 更新依赖
```

---

## 文档参考

| 文档 | 路径 | 说明 |
|------|------|------|
| 架构设计 | `docs/ARCHITECTURE.md` | 系统架构和技术决策 |
| 开发指南 | `docs/DEVELOPMENT.md` | 详细开发指南 |
| API 文档 | `docs/API.md` | 完整 API 参考 |
| CLI 文档 | `docs/CLI.md` | 命令行工具参考 |
| ACP 协议 | `docs/PROTOCOL_ACP.md` | ACP 协议规范 |
| MCP 协议 | `docs/PROTOCOL_MCP.md` | MCP 协议规范 |
| 部署指南 | `docs/DEPLOYMENT.md` | 生产环境部署 |
| 快速开始 | `docs/GETTING_STARTED.md` | 详细安装配置 |

---

## 研究资料 (research/)

本地研究资料库，存放相关论文、开源项目参考和技术笔记。**此目录内容不会被 Git 追踪**。

### 资料索引

| 资料类型 | 路径 | 说明 |
|---------|------|------|
| **研究索引** | `research/README.md` | 研究资料总索引和分类 |
| **技术报告** | `research/papers/` | AI Memory 技术报告等 |
| **开源项目** | `research/projects/` | 参考项目索引和克隆脚本 |
| **RAG技术** | `research/notes/rag-techniques.md` | RAG 技术深度分析 |
| **记忆架构** | `research/notes/memory-architectures.md` | 记忆架构对比分析 |
| **MCP协议** | `research/notes/mcp-protocol.md` | MCP 协议研究 |

### 快速开始

```bash
# 查看研究索引
cat research/README.md

# 克隆所有参考项目
cd research/projects
bash clone-all.sh

# 查看技术笔记
ls research/notes/
```

---

## 故障排除

### 常见问题

1. **重置数据**
   ```bash
   rm -rf ~/.memnexus
   # 或
   memnexus reset --hard
   ```

2. **连接远程数据库**
   ```bash
   export MEMNEXUS_DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"
   memnexus server
   ```

3. **WebSocket 调试**
   ```bash
   npx wscat -c ws://localhost:8080/ws
   > {"type": "subscribe", "session_id": "test"}
   ```

---

## 发布流程

1. 更新 `pyproject.toml` 中的版本号
2. 更新 `CHANGELOG.md`
3. 创建 Git Tag: `git tag v0.x.x`
4. 推送 Tag: `git push origin v0.x.x`
5. 构建: `uv build`
6. 发布: `uv publish`

---

## 系统改造记录 (Memory v2.0)

> 2026-02-28: 基于 AI Memory 前沿技术研究的重大架构升级

### 改造概述

参考 HippoRAG、MELODI、SEAKR 等前沿论文，对记忆系统进行系统性升级。

### 新增组件

| 模块 | 位置 | 功能 | 参考论文 |
|-----|------|------|---------|
| **自适应检索** | `memory/retrieval/adaptive.py` | 不确定性驱动的智能检索 | SEAKR |
| **分层记忆** | `memory/layers/` | 工作/短期/长期三层架构 | MELODI |
| **高级RAG** | `memory/advanced_rag.py` | 集成新特性的RAG系统 | - |
| **核心类型** | `memory/core/types.py` | 统一的类型定义 | - |

### 架构对比

```
改造前 (v1.0):
  Query → Vector Search → LanceDB → Results

改造后 (v2.0):
  Query → Uncertainty Check → [High] → Hierarchical Memory → Hybrid Search
                  ↓ [Low]
            Skip Retrieval
```

### 使用方式

```python
# 新的高级RAG系统
from memnexus.memory import AdvancedRAG, RAGConfig, RetrievalStrategy

# 配置自适应检索
config = RAGConfig(
    strategy=RetrievalStrategy.ADAPTIVE,
    adaptive_threshold=0.6,
)

# 创建RAG实例
rag = AdvancedRAG(
    session_id="my_session",
    config=config,
)
await rag.initialize()

# 添加文档 (自动分层存储)
await rag.add_document("User wants to build a REST API...")

# 查询 (自动决策是否检索)
result = await rag.query("What design patterns should I use?")
print(result.context)
```

### 向后兼容

旧接口仍可用，通过 `RAGPipelineAdapter` 适配器实现渐进迁移：

```python
from memnexus.memory import RAGPipelineAdapter

# 旧代码无需修改即可运行
pipeline = RAGPipelineAdapter(session_id="test")
```

### 详细文档

- [REFACTORING_PLAN.md](./REFACTORING_PLAN.md) - 完整改造规划
- `research/notes/memory-architectures.md` - 记忆架构对比
- `research/notes/rag-techniques.md` - RAG技术分析

---

**文档版本**: 0.2.0  
**最后更新**: 2026-02-28
