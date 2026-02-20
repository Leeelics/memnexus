# MemNexus 开发指南

## 开发环境搭建

### 1. 克隆仓库

```bash
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus
```

### 2. 安装依赖

使用 `uv`（推荐）：

```bash
# 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv sync

# 安装开发依赖
uv sync --extra dev
```

或使用 `pip`：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. 启动服务

```bash
# 启动 API 服务器
memnexus server

# 或开发模式（热重载）
memnexus server --reload

# 启动 Web Dashboard
memnexus web
```

### 4. 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_session.py -v

# 带覆盖率
uv run pytest --cov=memnexus --cov-report=html
```

### 5. 代码检查

```bash
# 格式化
uv run ruff format .

# 检查
uv run ruff check .

# 类型检查
uv run mypy src/memnexus
```

## 项目结构

```
memnexus/
├── src/memnexus/           # 核心代码
│   ├── core/               # 核心逻辑
│   │   ├── config.py       # 配置管理
│   │   ├── session.py      # 会话管理
│   │   └── orchestrator.py # 编排器
│   ├── agents/             # Agent 适配器
│   │   ├── base.py         # 基类
│   │   ├── claude.py       # Claude Code
│   │   ├── kimi.py         # Kimi CLI
│   │   └── registry.py     # 注册表
│   ├── protocols/          # 协议实现
│   │   ├── acp.py          # ACP 协议
│   │   └── mcp.py          # MCP 协议
│   ├── memory/             # 记忆系统
│   │   ├── store.py        # LanceDB 存储
│   │   ├── indexer.py      # LlamaIndex
│   │   └── models.py       # 数据模型
│   ├── web/                # Web 界面
│   │   ├── api.py          # API 路由
│   │   └── dashboard.py    # Streamlit
│   ├── server.py           # FastAPI 入口
│   └── cli.py              # CLI 入口
├── tests/                  # 测试
├── docs/                   # 文档
├── frontend/               # React 前端（未来）
└── scripts/                # 脚本
```

## 开发工作流

### 添加新的 Agent 支持

1. 在 `src/memnexus/agents/` 创建新文件
2. 继承 `BaseAgent` 类
3. 实现必需的方法
4. 在 `registry.py` 注册

示例：

```python
# src/memnexus/agents/custom.py

from memnexus.agents.base import BaseAgent, AgentConfig

class CustomAgent(BaseAgent):
    """自定义 Agent."""
    
    name = "custom"
    protocol = "acp"
    
    async def spawn(self, config: AgentConfig):
        """启动进程."""
        pass
    
    def parse_output(self, line: str):
        """解析输出."""
        pass

# src/memnexus/agents/registry.py
from memnexus.agents.custom import CustomAgent

AGENT_REGISTRY = {
    "claude": ClaudeAgent,
    "kimi": KimiAgent,
    "custom": CustomAgent,  # 添加这里
}
```

### 添加新的编排策略

```python
# src/memnexus/core/strategies.py

from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """编排策略基类."""
    
    @abstractmethod
    async def schedule(self, tasks, agents) -> List[TaskAssignment]:
        """调度任务."""
        pass

class RoundRobinStrategy(BaseStrategy):
    """轮询策略."""
    
    async def schedule(self, tasks, agents):
        assignments = []
        for i, task in enumerate(tasks):
            agent = agents[i % len(agents)]
            assignments.append(TaskAssignment(task, agent))
        return assignments
```

## 调试技巧

### 1. 查看日志

```bash
# 实时查看日志
tail -f ~/.memnexus/logs/memnexus.log

# 或使用 rich 格式
memnexus logs --follow
```

### 2. 调试 Agent 输出

```python
# 在代码中添加断点
import ipdb; ipdb.set_trace()

# 或使用 debug 日志
import structlog
logger = structlog.get_logger()
logger.debug("agent_output", line=line, parsed=event)
```

### 3. WebSocket 调试

```bash
# 使用 wscat 测试 WebSocket
npx wscat -c ws://localhost:8080/ws

# 发送消息
> {"type": "subscribe", "session_id": "test"}
```

## 发布流程

1. 更新版本号
   ```bash
   # pyproject.toml
   version = "0.2.0"
   ```

2. 更新 CHANGELOG.md

3. 创建 Git Tag
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. 构建发布
   ```bash
   uv build
   ```

5. 发布到 PyPI
   ```bash
   uv publish
   ```

## 常见问题

### Q: 如何重置数据？

```bash
rm -rf ~/.memnexus
# 或
memnexus reset --hard
```

### Q: 如何连接远程数据库？

```bash
export MEMNEXUS_DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"
memnexus server
```

### Q: 如何添加自定义 CLI Agent？

参考上面"添加新的 Agent 支持"部分。

## 贡献指南

1. Fork 仓库
2. 创建分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -am 'Add xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

## 参考资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [LanceDB 文档](https://lancedb.github.io/lancedb/)
- [LlamaIndex 文档](https://docs.llamaindex.ai/)
