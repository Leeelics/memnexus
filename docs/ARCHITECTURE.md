# MemNexus 架构设计

> **版本**: 0.2.0  
> **定位**: Code Memory for AI Programming Tools

---

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI Programming Tools                              │
│         (Claude Code, Kimi CLI, Codex, Cursor, etc.)                     │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌─────────────────┐
│  Kimi Plugin │   │   HTTP API   │   │  Python Library │
│  (/memory)   │   │  (REST/WS)   │   │  (CodeMemory)   │
└──────┬───────┘   └──────┬───────┘   └────────┬────────┘
       │                  │                    │
       └──────────────────┼────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MemNexus Core                                    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    CodeMemory                                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │    Git      │  │    Code     │  │   General   │              │   │
│  │  │  Extractor  │  │   Parser    │  │   Memory    │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Memory Store (LanceDB)                        │   │
│  │  - Vector storage with semantic search                           │   │
│  │  - Git commits, code symbols, user memories                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流

#### 场景：索引项目并搜索

```
1. 初始化项目
   User → memnexus init → Create .memnexus/ directory
                              ↓
                        Create config.yaml
                        Initialize LanceDB

2. 索引 Git 历史
   User → memnexus index --git
                              ↓
                        GitMemoryExtractor.extract_recent()
                              ↓
                        Parse commits (hash, message, author, diff)
                              ↓
                        MemoryStore.add() → LanceDB

3. 索引代码
   User → memnexus index --code
                              ↓
                        CodeParser.parse_file()
                              ↓
                        Extract symbols (functions, classes, methods)
                              ↓
                        CodeChunker.chunk_file()
                              ↓
                        MemoryStore.add() → LanceDB

4. 搜索记忆
   User → memnexus search "authentication"
                              ↓
                        MemoryStore.search() (vector similarity)
                              ↓
                        Return ranked results
```

---

## 2. 核心组件

### 2.1 CodeMemory

主入口类，提供统一接口。

```python
class CodeMemory:
    # 三层能力
    - Git: index_git_history(), query_git_history()
    - Code: index_codebase(), search_code()
    - General: add(), search()
```

### 2.2 GitMemoryExtractor

提取 Git 历史信息。

```python
class GitMemoryExtractor:
    - extract_recent(limit=100) → List[GitCommit]
    - extract_file_history(file_path) → List[GitCommit]
    - extract_by_pattern(pattern) → List[GitCommit]
    - extract_by_author(author) → List[GitCommit]
```

### 2.3 CodeParser

解析代码结构（当前支持 Python）。

```python
class CodeParser:
    - parse_file(file_path) → List[CodeSymbol]
    - extract_imports(file_path) → List[ImportInfo]
    - extract_function_calls(content) → List[str]
```

### 2.4 MemoryStore

向量存储，使用 LanceDB。

```python
class MemoryStore:
    - add(entry: MemoryEntry) → str (id)
    - search(query, limit=5) → List[MemoryEntry]
    - initialize() → None
```

---

## 3. 数据模型

### 3.1 GitCommit

```python
@dataclass
class GitCommit:
    hash: str              # Short hash (8 chars)
    message: str           # Commit message
    author: str            # Author name <email>
    timestamp: datetime
    files_changed: List[str]
    diff_summary: str      # Summary of changes
    stats: dict            # {files_changed, insertions, deletions}
```

### 3.2 CodeSymbol

```python
@dataclass
class CodeSymbol:
    name: str              # Function/class/method name
    symbol_type: str       # "function", "class", "method"
    content: str           # Full source code
    signature: str         # Function signature with types
    docstring: Optional[str]
    file_path: str
    start_line: int
    end_line: int
    metadata: dict         # decorators, parameters, etc.
```

### 3.3 MemoryEntry

```python
@dataclass
class MemoryEntry:
    content: str           # Text content for embedding
    source: str            # Source identifier
    memory_type: str       # "git_commit", "code_symbol", "generic"
    metadata: dict
    embedding: Optional[List[float]]
```

---

## 4. 接口层

### 4.1 CLI

```bash
memnexus init [path]       # Initialize project
memnexus status            # Show project status
memnexus index [--git] [--code]  # Index project
memnexus search <query>    # Search memory
memnexus server            # Start HTTP server
```

### 4.2 HTTP API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | Health check |
| `/stats` | GET | Project statistics |
| `/api/v1/search` | GET | Search all memories |
| `/api/v1/memory` | POST | Add memory |
| `/api/v1/git/index` | POST | Index Git history |
| `/api/v1/git/search` | GET | Search Git history |
| `/api/v1/code/index` | POST | Index codebase |
| `/api/v1/code/search` | GET | Search code symbols |
| `/api/v1/code/symbol/{name}` | GET | Find specific symbol |

### 4.3 Kimi CLI Plugin

```
/memory search <query>     # Search project memory
/memory store <content>    # Store important info
/memory status             # Check status
/memory index              # Index project
/memory find <symbol>      # Find code symbol
/memory history <file>     # Get file history
```

---

## 5. 存储结构

```
.memnexus/
├── config.yaml              # Project configuration
├── memory.lance/            # LanceDB vector database
│   ├── commits/             # Git commit embeddings
│   ├── code/                # Code symbol embeddings
│   └── generic/             # User memory embeddings
└── user_memories/           # User-stored memories (JSON)
    └── *.json
```

---

## 6. 技术选型理由

| 技术 | 选择理由 |
|------|----------|
| **LanceDB** | 嵌入式向量数据库，无需服务器，支持全文搜索 |
| **sentence-transformers** | 本地 embedding，无需 API key |
| **Python AST** | 标准库，无需额外依赖，足够解析 Python |
| **GitPython** | 成熟的 Git 操作库 |
| **FastAPI** | 现代、快速、易用的 Web 框架 |
| **Typer** | 基于 Click，类型友好的 CLI 框架 |

---

## 7. 未来扩展

### 7.1 计划中的功能

- **多语言支持**: TypeScript, JavaScript, Rust, Go
- **VSCode 扩展**: 编辑器内记忆提示
- **Claude Code 集成**: 原生插件支持
- **团队共享**: 多用户记忆空间

### 7.2 Experimental 功能

以下功能已冻结，代码保留但不维护：

- `advanced_rag.py` - 复杂 RAG 系统
- `layers/` - 分层记忆架构
- `knowledge_graph/` - 知识图谱
- `rmt/` - 循环记忆传递

---

**最后更新**: 2026-03-25
