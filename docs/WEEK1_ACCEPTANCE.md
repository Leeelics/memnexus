# Week 1 验收标准

> **目标**: 代码清理与架构简化，为 Code Memory 新定位做准备

---

## 总体目标

完成从"复杂多 Agent 编排系统"到"精简代码记忆基础设施"的转变，确保：
1. 代码库精简，核心功能清晰
2. 一键初始化流程可用
3. 为 Week 2 的 Git 集成打下基础

---

## Day 1-2: 代码清理与分支创建

### 任务清单

- [ ] 创建并切换到 `feature/code-memory` 分支
- [ ] 标记 experimental 功能（不删除，只标记）
- [ ] 简化 `src/memnexus/__init__.py` 导出
- [ ] 简化 `src/memnexus/memory/__init__.py` 导出
- [ ] 更新主 `README.md`，移除复杂功能宣传

### 验收标准

#### ✅ 标准 1: 分支创建
```bash
# 验证命令
git branch | grep code-memory
# 预期输出: * feature/code-memory
```

#### ✅ 标准 2: Experimental 标记
```python
# 在以下文件顶部添加标记:

# src/memnexus/memory/advanced_rag.py
"""
.. warning::
    Experimental feature. Not actively maintained in v1.0.
    Use RAGPipeline for stable functionality.
"""

# src/memnexus/memory/layers/__init__.py
"""
.. warning::
    Experimental hierarchical memory system. 
    Frozen in v1.0. Will be revisited in future versions.
"""

# src/memnexus/memory/retrieval/adaptive.py
"""
.. warning::
    Experimental adaptive retrieval. Frozen in v1.0.
"""

# src/memnexus/memory/rmt/ 整个目录
# 添加 README.md: "Experimental - Frozen in v1.0"
```

#### ✅ 标准 3: 简化导出
```python
# src/memnexus/__init__.py 应该只导出核心功能:
__all__ = [
    "__version__",
    "settings",
    "Session",
    "SessionManager",
    "MemoryStore",      # 核心：记忆存储
    "MemoryEntry",
]

# src/memnexus/memory/__init__.py 应该只导出:
__all__ = [
    # Core memory (stable)
    "MemoryStore",
    "MemoryEntry", 
    "ContextManager",
    "RAGPipeline",
    "Document",
    "DocumentChunker",
    # Note: Advanced features marked as experimental
]
```

#### ✅ 标准 4: README 更新
- [ ] 移除"分层记忆 v2.0"、"自适应检索"等复杂功能的宣传
- [ ] 添加新的定位说明（参考 VISION.md）
- [ ] 简化快速开始指南

---

## Day 3-4: 核心 API 简化

### 任务清单

- [ ] 简化 `MemoryStore` 类，只保留核心方法
- [ ] 创建 `src/memnexus/code_memory/` 目录结构
- [ ] 定义 `CodeMemoryStore` 接口
- [ ] 确保基础测试通过

### 验收标准

#### ✅ 标准 5: MemoryStore 简化
```python
# src/memnexus/memory/store.py
# 只保留以下公共方法:

class MemoryStore:
    async def initialize(self) -> None
    async def add(self, entry: MemoryEntry) -> str
    async def search(self, query: str, limit: int = 5) -> List[MemoryEntry]
    async def get_by_id(self, id: str) -> Optional[MemoryEntry]
    async def delete(self, id: str) -> bool
    
    # 新增：获取统计信息
    async def stats(self) -> Dict[str, Any]
```

#### ✅ 标准 6: Code Memory 目录创建
```
src/memnexus/code_memory/
├── __init__.py
├── git_extractor.py      # Git 历史提取（Week 2 实现）
├── code_parser.py        # 代码解析（Week 3 实现）
├── dependency_graph.py   # 依赖图（Week 3 实现）
└── code_memory.py        # 代码记忆主类
```

#### ✅ 标准 7: CodeMemory 接口定义
```python
# src/memnexus/code_memory/__init__.py

class CodeMemory:
    """Code-aware memory system for AI programming tools."""
    
    async def initialize(self) -> None
    
    # Git-related (Week 2)
    async def index_git_history(self, repo_path: str) -> None
    async def query_git_history(self, query: str) -> List[GitMemory]
    
    # Code-related (Week 3)
    async def index_code(self, code_path: str) -> None
    async def search_code(self, query: str) -> List[CodeMemory]
    async def find_references(self, symbol: str) -> List[CodeReference]
    
    # General
    async def search(self, query: str) -> List[MemoryEntry]
```

#### ✅ 标准 8: 测试通过
```bash
# 运行测试
uv run pytest tests/test_session.py -v

# 预期结果: 所有测试通过
```

---

## Day 5-7: 项目初始化流程

### 任务清单

- [ ] 实现 `memnexus init` 命令
- [ ] 实现 `memnexus status` 命令
- [ ] 实现配置验证
- [ ] 测试初始化流程

### 验收标准

#### ✅ 标准 9: `memnexus init` 命令
```bash
# 在空目录运行
mkdir test-project && cd test-project
memnexus init

# 预期输出:
# ✓ Detected Git repository
# ✓ Created .memnexus/ directory
# ✓ Initialized LanceDB at .memnexus/memory.lance
# ✓ Configuration saved to .memnexus/config.yaml
# 
# Next steps:
#   1. Run `memnexus index` to index your codebase
#   2. Run `memnexus server` to start the API server
```

#### ✅ 标准 10: 初始化后的目录结构
```
test-project/
├── .memnexus/                 # 创建的目录
│   ├── config.yaml           # 配置文件
│   ├── memory.lance/         # LanceDB 数据
│   └── logs/                 # 日志目录
├── .git/                     # 已存在的 Git 目录
└── ...                       # 项目文件
```

#### ✅ 标准 11: `memnexus status` 命令
```bash
memnexus status

# 预期输出:
# MemNexus Status
# ===============
# Project: test-project
# Git repo: Yes (main branch, 42 commits)
# Memory DB: Initialized (0 entries)
# Last indexed: Never
# 
# Commands:
#   memnexus index    - Index your codebase
#   memnexus server   - Start API server
```

#### ✅ 标准 12: 配置验证
```python
# .memnexus/config.yaml 应该包含:
version: "1.0"
project:
  name: "test-project"
  root: "/path/to/test-project"
  
memory:
  backend: "lancedb"
  path: ".memnexus/memory.lance"
  
git:
  enabled: true
  max_history: 1000
  
code:
  languages: ["python", "javascript", "typescript", "rust"]
  exclude_patterns: ["*.pyc", "node_modules/", ".git/"]
```

---

## Week 1 整体验收清单

### 功能验收

```markdown
- [ ] 1. 分支创建: `feature/code-memory` 分支存在且当前在该分支
- [ ] 2. Experimental 标记: 所有复杂功能已标记为 experimental
- [ ] 3. 简化导出: `__init__.py` 只导出核心功能
- [ ] 4. README 更新: 文档反映新的定位和简化功能
- [ ] 5. MemoryStore 简化: 只保留核心 5 个方法
- [ ] 6. Code Memory 目录: 目录结构创建完成
- [ ] 7. 接口定义: CodeMemory 类接口定义完成
- [ ] 8. 测试通过: `pytest tests/test_session.py` 通过
- [ ] 9. init 命令: `memnexus init` 能成功初始化项目
- [ ] 10. status 命令: `memnexus status` 显示正确信息
- [ ] 11. 配置验证: 生成的配置文件格式正确
```

### 代码质量验收

```markdown
- [ ] 12. 无循环导入: `python -c "import memnexus"` 成功
- [ ] 13. 类型检查: `uv run mypy src/memnexus --ignore-missing-imports` 无错误
- [ ] 14. 代码格式: `uv run ruff format --check .` 通过
- [ ] 15. 代码检查: `uv run ruff check .` 无严重错误
```

### 演示验收

```markdown
- [ ] 16. 能演示完整的初始化流程
- [ ] 17. 能展示简化后的代码结构
- [ ] 18. 能解释哪些功能被标记为 experimental
```

---

## 快速验证脚本

创建一个验证脚本，一键检查 Week 1 完成度：

```bash
#!/bin/bash
# scripts/verify-week1.sh

echo "=== Week 1 Verification ==="
echo ""

# 1. 分支检查
echo "1. Checking branch..."
git branch | grep "* feature/code-memory" && echo "   ✓ On feature/code-memory" || echo "   ✗ Not on feature/code-memory"

# 2. 导入检查
echo ""
echo "2. Checking imports..."
uv run python -c "import memnexus; print('   ✓ Import successful')" 2>/dev/null || echo "   ✗ Import failed"

# 3. 测试检查
echo ""
echo "3. Running tests..."
uv run pytest tests/test_session.py -q 2>/dev/null && echo "   ✓ Tests pass" || echo "   ✗ Tests failed"

# 4. 命令检查
echo ""
echo "4. Checking CLI commands..."
memnexus --help > /dev/null 2>&1 && echo "   ✓ CLI available" || echo "   ✗ CLI not available"

# 5. 目录结构检查
echo ""
echo "5. Checking directory structure..."
[ -d "src/memnexus/code_memory" ] && echo "   ✓ code_memory directory exists" || echo "   ✗ code_memory directory missing"

echo ""
echo "=== Verification Complete ==="
```

---

## 常见问题

### Q: 为什么不删除 experimental 功能，而是标记？
**A**: 保留代码但标记为 experimental，方便未来需要时恢复，也保留历史记录。

### Q: 简化后会不会功能太少？
**A**: Week 1 的目标是精简，Week 2-3 会添加 Git 和代码感知功能，功能会丰富起来。

### Q: 测试失败了怎么办？
**A**: 优先修复核心测试（test_session.py），其他测试可以暂时跳过或标记为 xfail。

---

## 下一步

Week 1 完成后，进入 Week 2: Git 集成 MVP

