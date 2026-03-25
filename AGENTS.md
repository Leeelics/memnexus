# MemNexus - AI Agent 开发指南

> **目标读者**: AI 编程助手（如 Claude Code、Kimi CLI 等）
>
> **项目状态**: v0.2.0 - Code Memory for AI Programming Tools

---

## 项目概述

MemNexus 是一个**代码记忆基础设施**（Code Memory Infrastructure），为 AI 编程工具提供持久的项目记忆能力。

### 核心定位

**不是**：多 Agent 协作编排系统、通用记忆层、项目管理工具

**而是**：专为 AI 编程场景设计的代码记忆基础设施

- **Code-Aware**: 理解代码结构（AST），不只是文本
- **Git-Native**: 与 Git 历史深度集成
- **Tool-Agnostic**: 服务所有 AI 编程工具

### 核心功能

1. **Git 历史索引** - 索引 commit 历史，支持语义搜索
2. **代码解析** - 解析 Python 代码结构（函数、类、方法）
3. **向量记忆** - LanceDB 存储，支持语义检索
4. **Kimi CLI 插件** - 原生集成 Kimi CLI 1.25.0+

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 存储 | LanceDB | 向量数据库 |
| Embedding | sentence-transformers | 文本向量化 |
| 代码解析 | Python AST | Python 代码分析 |
| Git 操作 | GitPython | Git 历史提取 |
| Web | FastAPI | HTTP API |
| CLI | Typer + Rich | 命令行界面 |

---

## 项目结构

```
MemNexus/
├── src/memnexus/              # Python 源代码
│   ├── __init__.py            # 导出 CodeMemory, SearchResult
│   ├── code_memory.py         # 核心 CodeMemory 类
│   ├── cli.py                 # CLI 入口
│   ├── server.py              # FastAPI 服务器
│   └── memory/                # 记忆系统
│       ├── store.py           # LanceDB 向量存储
│       ├── git.py             # Git 集成
│       └── code.py            # 代码解析
├── docs/                      # 文档
│   ├── VISION.md              # 产品定位
│   ├── ROADMAP.md             # 路线图
│   ├── API.md                 # API 文档
│   └── CLI.md                 # CLI 文档
├── tests/                     # 测试
├── README.md                  # 项目说明
├── INSTALL.md                 # 安装指南
└── CHANGELOG.md               # 更新日志
```

---

## 快速开始

### 安装

```bash
pip install memnexus
```

### 使用

```python
import asyncio
from memnexus import CodeMemory

async def main():
    # 初始化
    memory = await CodeMemory.init("./my-project")
    
    # 索引
    await memory.index_git_history()
    await memory.index_codebase()
    
    # 搜索
    results = await memory.search("authentication")
    for r in results:
        print(f"{r.source}: {r.content[:100]}")

asyncio.run(main())
```

### CLI

```bash
memnexus init              # 初始化项目
memnexus index --git       # 索引 Git 历史
memnexus index --code      # 索引代码
memnexus search "query"    # 搜索记忆
memnexus server            # 启动 API 服务
```

---

## 核心 API

### CodeMemory

```python
class CodeMemory:
    # 初始化
    @classmethod
    async def init(cls, project_path: str) -> "CodeMemory"
    
    # Git 相关
    async def index_git_history(self, limit: int = 1000) -> Dict
    async def query_git_history(self, query: str, limit: int = 5) -> List[GitSearchResult]
    async def get_file_history(self, file_path: str, limit: int = 20) -> List[GitSearchResult]
    
    # 代码相关
    async def index_codebase(self, languages: List[str] = None) -> Dict
    async def search_code(self, query: str, symbol_type: str = None) -> List[SearchResult]
    async def find_symbol(self, name: str) -> Optional[SearchResult]
    
    # 通用
    async def add(self, content: str, source: str, metadata: dict = None) -> str
    async def search(self, query: str, limit: int = 5) -> List[SearchResult]
```

---

## HTTP API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/stats` | 项目统计 |
| GET | `/api/v1/search` | 搜索记忆 |
| POST | `/api/v1/memory` | 添加记忆 |
| POST | `/api/v1/git/index` | 索引 Git |
| GET | `/api/v1/git/search` | 搜索 Git |
| POST | `/api/v1/code/index` | 索引代码 |
| GET | `/api/v1/code/search` | 搜索代码 |
| GET | `/api/v1/code/symbol/{name}` | 查找符号 |

---

## 开发指南

### 构建

```bash
# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff format .
ruff check . --fix
mypy src/memnexus
```

### 发布

```bash
# 构建
python -m build

# 检查
twine check dist/*

# 上传
twine upload dist/*
```

---

## 冻结功能（Experimental）

以下功能已标记为 experimental，当前版本不维护但保留代码：

- `advanced_rag.py` - 复杂 RAG 系统
- `layers/` - 分层记忆架构
- `retrieval/adaptive.py` - 自适应检索
- `rmt/` - 循环记忆传递
- `knowledge_graph/` - 知识图谱

这些功能在 `memory/` 目录中带有 README 说明。

---

## 参考文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 愿景 | `docs/VISION.md` | 产品定位 |
| 路线图 | `docs/ROADMAP.md` | 开发计划 |
| API | `docs/API.md` | API 参考 |
| CLI | `docs/CLI.md` | CLI 参考 |
| 安装 | `INSTALL.md` | 安装指南 |
| 贡献 | `CONTRIBUTING.md` | 贡献指南 |

---

**版本**: 0.2.0  
**最后更新**: 2026-03-25
