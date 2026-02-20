# MemNexus 架构设计

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Web Frontend (React)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  任务看板    │  │  Agent 状态  │  │  共享记忆    │  │  人工干预面板    │ │
│  │  (Kanban)   │  │  (Monitor)  │  │  (Memory)   │  │  (Control)     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket / HTTP
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API Gateway (FastAPI)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  REST API   │  │  WebSocket  │  │   Auth      │  │    Rate Limit   │ │
│  │  Router     │  │  Handler    │  │  Middleware │  │    Middleware   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Core Services                                    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Orchestrator Engine                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │   Session   │  │    Task     │  │  Dependency │              │   │
│  │  │   Manager   │  │  Scheduler  │  │   Resolver  │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Agent Manager                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │   Agent     │  │    ACP      │  │    MCP      │              │   │
│  │  │   Pool      │  │   Adapter   │  │   Adapter   │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Memory Engine                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │   Memory    │  │  LlamaIndex │  │   Vector    │              │   │
│  │  │   Store     │  │   Pipeline  │  │   Search    │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │  Agent-1  │   │  Agent-2  │   │  Agent-N  │
            │ Claude    │   │   Kimi    │   │   Codex   │
            │ Process   │   │  Process  │   │  Process  │
            └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
                  │               │               │
                  └───────────────┼───────────────┘
                                  ▼
                        ┌───────────────────┐
                        │   Shared Memory   │
                        │   (~/.memnexus/)  │
                        └───────────────────┘
```

### 1.2 数据流

#### 场景：Agent 执行并共享结果

```
1. 用户创建会话
   UI → POST /api/v1/sessions → SessionManager.create()
   
2. 启动 Agent
   Orchestrator → AgentManager.spawn("claude")
   → subprocess.Popen(["claude", "--dangerously-skip-permissions"])
   
3. Agent 输出捕获
   Claude Process stdout → ACPAdapter.parse()
   → MemoryEngine.save(type="code", content=...)
   → WebSocket.broadcast({type: "agent_output", ...})
   
4. 其他 Agent 读取
   Kimi Process → ACPAdapter.request_context()
   → MemoryEngine.query(tags=["code", "backend"])
   → 返回相关记忆
```

## 2. 核心组件

### 2.1 Orchestrator Engine

```python
class Orchestrator:
    """中央编排器 - 协调所有组件"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.agent_manager = AgentManager()
        self.task_scheduler = TaskScheduler()
        self.memory_engine = MemoryEngine()
        
    async def create_session(self, config: SessionConfig) -> Session:
        """创建新会话"""
        # 1. 创建会话记录
        session = await self.session_manager.create(config)
        
        # 2. 初始化 Agents
        for agent_config in config.agents:
            agent = await self.agent_manager.spawn(agent_config)
            session.agents.append(agent)
            
        # 3. 创建任务图
        tasks = self.task_scheduler.build_dependency_graph(config.tasks)
        session.tasks = tasks
        
        return session
        
    async def execute_session(self, session_id: str):
        """执行会话"""
        session = await self.session_manager.get(session_id)
        
        # 根据策略执行
        if session.strategy == Strategy.SEQUENTIAL:
            await self._execute_sequential(session)
        elif session.strategy == Strategy.PARALLEL:
            await self._execute_parallel(session)
            
    async def _execute_sequential(self, session: Session):
        """顺序执行"""
        for task in session.tasks:
            # 等待依赖完成
            await self._wait_for_dependencies(task)
            
            # 分配 Agent
            agent = self.agent_manager.assign(task)
            
            # 构建上下文
            context = await self._build_context(agent, task)
            
            # 执行
            result = await agent.execute(task, context)
            
            # 保存结果
            await self.memory_engine.save_task_result(task, result)
            
            # 检查是否需要干预
            if result.requires_intervention:
                await self._pause_for_intervention(session, task, result)
```

### 2.2 Agent Manager

```python
class AgentManager:
    """Agent 生命周期管理"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.adapters: Dict[str, ProtocolAdapter] = {
            "acp": ACPAdapter(),
            "mcp": MCPAdapter(),
        }
        
    async def spawn(self, config: AgentConfig) -> Agent:
        """启动 Agent 进程"""
        # 选择适配器
        adapter = self.adapters[config.protocol]
        
        # 启动进程
        process = await adapter.spawn(
            cli=config.cli,
            working_dir=config.working_dir,
            env=config.env,
        )
        
        # 创建 Agent 对象
        agent = Agent(
            id=generate_id(),
            config=config,
            process=process,
            adapter=adapter,
        )
        
        # 启动输出监听
        asyncio.create_task(self._monitor_output(agent))
        
        self.agents[agent.id] = agent
        return agent
        
    async def _monitor_output(self, agent: Agent):
        """监控 Agent 输出"""
        async for line in agent.process.stdout:
            output = line.decode().strip()
            
            # 解析输出
            event = agent.adapter.parse_output(output)
            
            # 更新 Agent 状态
            agent.update_state(event)
            
            # 广播给 Web UI
            await websocket_manager.broadcast({
                "type": "agent_event",
                "agent_id": agent.id,
                "event": event.dict(),
            })
            
            # 存储到记忆
            await memory_engine.save(event.to_memory())
```

### 2.3 Memory Engine

```python
class MemoryEngine:
    """共享记忆系统"""
    
    def __init__(self):
        self.vector_store = LanceDBStore()
        self.metadata_store = PostgresStore()
        self.index = LlamaIndexPipeline()
        
    async def save(self, memory: Memory) -> str:
        """保存记忆"""
        # 1. 生成 embedding
        embedding = await self.index.embed(memory.content)
        memory.embedding = embedding
        
        # 2. 存入向量数据库
        await self.vector_store.insert(memory)
        
        # 3. 存入元数据数据库
        await self.metadata_store.insert(memory)
        
        # 4. 通知订阅者
        await self._notify_subscribers(memory)
        
        return memory.id
        
    async def query(self, query: MemoryQuery) -> List[Memory]:
        """查询记忆"""
        memories = []
        
        # 1. 语义搜索
        if query.semantic_search:
            embedding = await self.index.embed(query.semantic_search)
            semantic_results = await self.vector_store.search(
                embedding=embedding,
                top_k=query.top_k,
                filter=query.to_filter(),
            )
            memories.extend(semantic_results)
            
        # 2. 关键词搜索
        if query.keywords:
            keyword_results = await self.metadata_store.search(
                keywords=query.keywords,
                filter=query.to_filter(),
            )
            memories.extend(keyword_results)
            
        # 3. 去重和排序
        return self._deduplicate_and_rank(memories, query)
        
    async def subscribe(
        self,
        session_id: str,
        callback: Callable[[Memory], None]
    ):
        """订阅记忆更新"""
        await redis.subscribe(f"memory:{session_id}", callback)
```

### 2.4 Protocol Adapters

#### ACP Adapter

```python
class ACPAdapter:
    """Agent Client Protocol 适配器"""
    
    PROTOCOL_VERSION = "2025-01-01"
    
    async def spawn(self, cli: str, working_dir: str, env: dict) -> Process:
        """启动 ACP 进程"""
        cmd = [cli, "--dangerously-skip-permissions"]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            env={**os.environ, **env},
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # 发送 initialize 请求
        await self._send_initialize(process)
        
        return process
        
    async def _send_initialize(self, process: Process):
        """发送 ACP initialize 请求"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": self.PROTOCOL_VERSION,
                "capabilities": {
                    "tools": True,
                    "resources": True,
                },
            },
        }
        
        process.stdin.write(json.dumps(request).encode() + b"\n")
        await process.stdin.drain()
        
    def parse_output(self, line: str) -> AgentEvent:
        """解析 ACP 输出"""
        try:
            data = json.loads(line)
            
            if "method" in data:
                # 这是请求（如 tool call）
                return self._parse_request(data)
            elif "result" in data or "error" in data:
                # 这是响应
                return self._parse_response(data)
            else:
                # 这是通知（如 log）
                return self._parse_notification(data)
        except json.JSONDecodeError:
            # 非 JSON 输出（如普通日志）
            return AgentEvent(type="log", content=line)
```

## 3. 数据模型

### 3.1 核心实体

```python
# Session 会话
class Session(BaseModel):
    id: str
    name: str
    description: str
    status: SessionStatus
    strategy: ExecutionStrategy
    working_dir: str
    agents: List[Agent]
    tasks: List[Task]
    created_at: datetime
    updated_at: datetime

# Agent 智能体
class Agent(BaseModel):
    id: str
    session_id: str
    role: AgentRole
    status: AgentStatus
    cli: str  # claude, kimi, codex
    protocol: ProtocolType  # acp, mcp
    working_dir: str
    current_task: Optional[str]
    process: Optional[Process]
    
# Task 任务
class Task(BaseModel):
    id: str
    session_id: str
    name: str
    description: str
    status: TaskStatus
    agent_id: Optional[str]
    dependencies: List[str]  # task IDs
    prompt: str
    result: Optional[TaskResult]
    created_at: datetime
    completed_at: Optional[datetime]

# Memory 记忆
class Memory(BaseModel):
    id: str
    session_id: str
    type: MemoryType
    content: dict
    embedding: Optional[List[float]]
    created_by: str  # agent_id
    tags: List[str]
    created_at: datetime
```

### 3.2 数据库 Schema

```sql
-- 会话表
CREATE TABLE sessions (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL,
    strategy VARCHAR(32) NOT NULL,
    working_dir VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent 表
CREATE TABLE agents (
    id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) REFERENCES sessions(id),
    role VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    cli VARCHAR(64) NOT NULL,
    protocol VARCHAR(16) NOT NULL,
    working_dir VARCHAR(512) NOT NULL,
    current_task_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 任务表
CREATE TABLE tasks (
    id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) REFERENCES sessions(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL,
    agent_id VARCHAR(64) REFERENCES agents(id),
    dependencies JSONB DEFAULT '[]',
    prompt TEXT NOT NULL,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 记忆元数据表
CREATE TABLE memories (
    id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) REFERENCES sessions(id),
    type VARCHAR(32) NOT NULL,
    content JSONB NOT NULL,
    created_by VARCHAR(64) REFERENCES agents(id),
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. 部署架构

### 4.1 本地开发

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  memnexus:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - .:/app
      - ~/.memnexus:/data
    environment:
      - MEMNEXUS_ENV=development
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/memnexus
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: memnexus
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7
    volumes:
      - redis_data:/data
      
volumes:
  postgres_data:
  redis_data:
```

### 4.2 生产部署

```
┌─────────────────────────────────────────┐
│              Load Balancer               │
│              (Nginx/Traefik)             │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌───────┐   ┌───────┐   ┌───────┐
│Web-1  │   │Web-2  │   │Web-N  │   MemNexus API
│       │   │       │   │       │   (FastAPI + WebSocket)
└───┬───┘   └───┬───┘   └───┬───┘
    │           │           │
    └───────────┼───────────┘
                ▼
        ┌───────────────┐
        │    Redis      │   缓存 + 消息队列
        │   Cluster     │
        └───────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
┌───────────────┐ ┌───────────────┐
│  PostgreSQL   │ │   LanceDB     │
│    Primary    │ │   (Shared)    │
└───────────────┘ └───────────────┘
```

## 5. 关键技术决策

### 5.1 为什么选择 LanceDB？

| 特性 | LanceDB | Chroma | Pinecone |
|-----|---------|--------|----------|
| 部署方式 | 嵌入式/无服务 | 嵌入式/服务 | 托管服务 |
| 依赖 | 零依赖 | 零依赖 | 网络依赖 |
| 性能 | Arrow 列式存储 | 中等 | 高 |
| 混合搜索 | 原生支持 | 需配置 | 需配置 |
| 适合场景 | 本地 CLI 工具 | 小型应用 | 企业级 |

**决策**: MemNexus 是本地开发工具，LanceDB 的零配置、嵌入式特性完美契合。

### 5.2 为什么选择 ACP 优先？

| 协议 | 支持情况 | 生态成熟度 |
|-----|---------|-----------|
| ACP | Claude Code ✅, Kimi CLI ✅ | 半官方，但工具支持好 |
| MCP | Claude Desktop ✅, 其他 ❓ | 开放标准，发展中 |

**决策**: 当前主要 CLI 工具（Claude、Kimi）原生支持 ACP，先实现 ACP，MCP 作为扩展。

### 5.3 为什么用 LlamaIndex？

- **Chunking**: 自动代码/文本分块
- **RAG Pipeline**: 检索增强生成
- **多模态**: 支持代码、文本、图像
- **可扩展**: 自定义索引策略

---

## 6. 扩展点

### 6.1 添加新的 CLI Agent

```python
# src/memnexus/agents/custom.py

class CustomAgent(BaseAgent):
    """自定义 Agent 示例"""
    
    name = "custom"
    protocol = ProtocolType.ACP
    
    async def spawn(self, config: AgentConfig) -> Process:
        return await asyncio.create_subprocess_exec(
            "my-custom-cli",
            "--work-dir", config.working_dir,
            stdin=PIPE,
            stdout=PIPE,
        )
        
    def parse_output(self, line: str) -> AgentEvent:
        # 自定义解析逻辑
        pass

# 注册
agent_registry.register(CustomAgent)
```

### 6.2 自定义编排策略

```python
# src/memnexus/orchestrator/strategies.py

class RoundRobinStrategy(BaseStrategy):
    """轮询策略 - 轮流分配任务给 Agents"""
    
    def __init__(self):
        self.current_index = 0
        
    async def assign_task(
        self,
        task: Task,
        agents: List[Agent]
    ) -> Agent:
        agent = agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(agents)
        return agent
```

---

## 7. 监控与调试

### 7.1 日志结构

```json
{
  "timestamp": "2026-02-20T10:30:00Z",
  "level": "INFO",
  "component": "orchestrator",
  "session_id": "sess_abc123",
  "agent_id": "ag_claude_001",
  "task_id": "task_design_001",
  "event": "task_completed",
  "duration_ms": 45000,
  "context": {
    "input_tokens": 1024,
    "output_tokens": 2048,
    "tools_called": ["read_file", "edit_file"]
  }
}
```

### 7.2 关键指标

| 指标 | 类型 | 说明 |
|-----|------|------|
| agent_execution_duration | Histogram | Agent 执行耗时 |
| memory_query_latency | Histogram | 记忆查询延迟 |
| websocket_connections | Gauge | 当前 WebSocket 连接数 |
| task_completion_rate | Counter | 任务完成率 |
| agent_error_rate | Counter | Agent 错误率 |

---

**文档版本**: 1.0  
**最后更新**: 2026-02-20
