# v0.5.0 规划：MCP Server

> **版本代号**: "Connected Memory"  
> **目标**: 从单机工具进化为可集成的基础设施

---

## 核心目标

```
┌─────────────────────────────────────────────────────────────┐
│                    v0.5.0 核心目标                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🌐 成为 AI 工具生态的基础设施                                 │
│     └─ 通过 MCP 协议与 AI 工具集成                            │
│                                                              │
│  🔌 标准接口                                                  │
│     └─ 实现 MCP Server，提供标准化的记忆搜索/存储能力          │
│                                                              │
│  🧩 适配器模式                                                │
│     └─ 为不同工具提供专用适配器，降低集成成本                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Tools Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Kimi CLI   │  │ Claude Code │  │   Other AI Tools    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                    │            │
│         └────────────────┼────────────────────┘            │
│                          │                                 │
│                          ▼                                 │
│              ┌───────────────────────┐                     │
│              │    MCP Protocol       │                     │
│              │  (Model Context       │                     │
│              │   Protocol)           │                     │
│              └───────────┬───────────┘                     │
│                          │                                 │
│                          ▼                                 │
│              ┌───────────────────────┐                     │
│              │   MemNexus MCP Server │                     │
│              │   - memory_search     │                     │
│              │   - memory_store      │                     │
│              │   - session_explore   │                     │
│              └───────────┬───────────┘                     │
│                          │                                 │
│                          ▼                                 │
│              ┌───────────────────────┐                     │
│              │    MemNexus Core      │                     │
│              │  (CodeMemory, etc.)   │                     │
│              └───────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 任务分解

### Phase A: MCP Server 核心 (Week 1)

| 任务 | 说明 | 优先级 |
|------|------|--------|
| MCP 协议研究 | 研究 MCP 协议规范 | ⭐⭐⭐ |
| Server 基础架构 | `memnexus/mcp/server.py` | ⭐⭐⭐ |
| Tool 注册机制 | 动态 tool 注册 | ⭐⭐⭐ |
| STDIO/SSE 传输 | 支持两种传输模式 | ⭐⭐⭐ |

### Phase B: MCP Tools 实现 (Week 1-2)

| Tool | 功能 | 输入 | 输出 |
|------|------|------|------|
| `memory_search` | 搜索记忆 | query, limit | 记忆列表 |
| `memory_store` | 存储记忆 | content, metadata | 存储ID |
| `session_explore` | 探索会话 | query, context | 相关决策 |
| `code_find` | 查找代码 | symbol_name | 代码位置 |
| `git_blame` | Git blame | file_path, line | 提交信息 |

### Phase C: CLI 集成 (Week 2)

```bash
# 启动 MCP Server
memnexus mcp serve              # STDIO 模式（默认）
memnexus mcp serve --sse        # SSE 模式
memnexus mcp serve --port 8080  # 自定义端口

# 测试 MCP 工具
memnexus mcp test memory_search "authentication"
```

### Phase D: 适配器优化 (Week 2-3)

| 适配器 | 用途 |
|--------|------|
| `KimiCLIAdapter` | 优化 Kimi CLI 的 memory 命令 |

---

## 接口设计

### MCP Server 配置

```python
# mcp_config.json
{
  "mcpServers": {
    "memnexus": {
      "command": "memnexus",
      "args": ["mcp", "serve"],
      "env": {
        "MEMNEXUS_PROJECT": "/path/to/project"
      }
    }
  }
}
```

### Tool Schema

```python
# memory_search
{
    "name": "memory_search",
    "description": "Search project memory for relevant context",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "number", "default": 5},
            "type": {"enum": ["code", "git", "session"], "default": "code"}
        },
        "required": ["query"]
    }
}

# memory_store
{
    "name": "memory_store",
    "description": "Store important decision or context",
    "inputSchema": {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "category": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["content"]
    }
}
```

---

## 文件结构

```
src/memnexus/
├── mcp/                        # NEW
│   ├── __init__.py
│   ├── server.py              # MCP Server 核心
│   ├── tools.py               # Tool 定义和实现
│   ├── transport.py           # STDIO/SSE 传输层
│   └── adapters/              # 工具适配器
│       ├── __init__.py
│       └── kimi_cli.py        # Kimi CLI 适配器
├── cli.py                     # ADD mcp 子命令
└── ...
```

---

## 依赖项

```toml
[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0",           # MCP SDK
    "sse-starlette>=1.0.0", # SSE 传输
]
```

---

## 发布标准

```markdown
✅ v0.5.0 Ready:
- [ ] MCP Server 实现完整
- [ ] 至少 3 个 MCP Tools 可用
- [ ] CLI `memnexus mcp serve` 可用
- [ ] Kimi CLI 适配器优化
- [ ] 文档和示例完整
- [ ] 测试覆盖率 > 70%
```

---

## 风险与应对

| 风险 | 应对策略 |
|------|----------|
| MCP 协议变更 | 关注官方规范，使用版本锁定 |
| 性能问题 | 早期进行负载测试 |

---

## 参考资源

- MCP Protocol: https://modelcontextprotocol.io
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk

---

*Last updated: 2026-04-01*
