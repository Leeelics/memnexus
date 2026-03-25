# MemNexus 产品路线图

> **版本**: 1.0  
> **日期**: 2026-03-25  
> **状态**: 重生规划 - 基于新定位的执行路线图

---

## 路线图概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MemNexus 三阶段路线图                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: 做减法 (2-3 周)          Phase 2: 找场景 (3-4 周)                    │
│  ┌─────────────────────┐          ┌─────────────────────┐                    │
│  │ • 精简核心功能       │          │ • Vibe Kanban 集成   │                    │
│  │ • Git 集成          │    →     │ • 用户验证           │                    │
│  │ • 代码感知 RAG      │          │ • 快速迭代           │                    │
│  └─────────────────────┘          └─────────────────────┘                    │
│           │                                  │                               │
│           └──────────────────────────────────┘                               │
│                          │                                                   │
│                          ▼                                                   │
│               Phase 3: 建生态 (持续)                                          │
│               ┌─────────────────────┐                                        │
│               │ • 多工具支持         │                                        │
│               │ • 平台化             │                                        │
│               │ • 商业化探索         │                                        │
│               └─────────────────────┘                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 做减法（第 1-3 周）

**目标**: 精简到核心功能，快速可用，验证价值假设

### Week 1: 代码清理与架构简化

#### Day 1-2: 代码清理
- [ ] 创建 `feature/code-memory` 分支
- [ ] **冻结（不删除）复杂功能**:
  - [ ] 标记 `advanced_rag.py` 为 experimental
  - [ ] 标记 `layers/` 目录为 experimental
  - [ ] 标记 `rmt/` 目录为 experimental
- [ ] 简化主入口，确保 `memnexus server` 一键启动
- [ ] 更新 `README.md`，移除复杂功能的宣传

#### Day 3-4: 核心 API 简化
- [ ] 简化 `MemoryStore` API:
  ```python
  # 只保留核心方法
  store.add(content, source, metadata)
  store.search(query, limit)
  store.get_history(file_path)  # 新增：获取文件历史
  ```
- [ ] 简化 `RAGPipeline`，移除 LlamaIndex 依赖（可选）
- [ ] 确保基础测试通过

#### Day 5-7: 项目初始化流程
- [ ] 实现 `memnexus init` 命令
  - 检测当前目录是否为 Git 仓库
  - 创建 `.memnexus/` 配置目录
  - 初始化 LanceDB
- [ ] 实现 `memnexus index` 命令
  - 索引当前项目代码
  - 显示进度和统计

**Week 1 交付物**:
- [ ] 精简后的代码库
- [ ] 一键初始化流程
- [ ] 更新的文档

---

### Week 2: Git 集成 MVP

#### 目标
实现 Git 历史提取和索引，让 MemNexus 能回答"这个文件/函数最近改了什么"。

#### 任务清单

- [ ] **Day 1-2: Git 历史提取器**
  ```python
  # src/memnexus/code_memory/git_extractor.py
  class GitHistoryExtractor:
      def extract_commits(self, file_path=None, limit=100) -> List[Commit]
      def extract_file_history(self, file_path) -> FileHistory
      def extract_code_evolution(self, function_name) -> List[CodeVersion]
  ```
  - [ ] 使用 `gitpython` 库读取历史
  - [ ] 提取 commit message + diff
  - [ ] 关联代码变更与提交信息

- [ ] **Day 3-4: Git 记忆存储**
  ```python
  # 扩展 MemoryEntry
  class MemoryEntry:
      content: str
      source: str  # "git:commit:a1b2c3"
      memory_type: str  # "git_commit", "code_change", "pr_discussion"
      metadata: {
          "commit_hash": "a1b2c3",
          "author": "developer@example.com",
          "timestamp": "2026-03-01T10:00:00",
          "files_changed": ["auth/login.py"],
          "related_commits": ["d4e5f6"]
      }
  ```
  - [ ] 设计 Git 相关记忆的 schema
  - [ ] 实现 Git 记忆索引流程

- [ ] **Day 5-7: Git 查询 API**
  ```python
  # API 端点
  GET /api/v1/git/history?file=auth/login.py
  GET /api/v1/git/blame?function=authenticate_user
  GET /api/v1/git/evolution?module=auth
  ```
  - [ ] 实现文件历史查询
  - [ ] 实现函数演变查询
  - [ ] 添加 CLI 命令 `memnexus git log --smart`

**Week 2 交付物**:
- [ ] Git 历史提取和索引功能
- [ ] 能回答"这个文件最近改了什么"
- [ ] 文档和示例

---

### Week 3: 代码感知 RAG MVP

#### 目标
实现 AST-based 代码分块，让 MemNexus 理解代码结构。

#### 任务清单

- [ ] **Day 1-2: 代码解析器**
  ```python
  # src/memnexus/code_memory/code_parser.py
  class CodeParser:
      def parse_file(self, file_path) -> ParsedFile
      def extract_functions(self, content, language) -> List[Function]
      def extract_classes(self, content, language) -> List[Class]
      def extract_imports(self, content, language) -> List[Import]
  ```
  - [ ] 集成 `tree-sitter-python`
  - [ ] 集成 `tree-sitter-javascript`
  - [ ] 集成 `tree-sitter-rust`（可选）

- [ ] **Day 3-4: 代码分块策略**
  ```python
  # 函数级别的智能分块
  class CodeChunker:
      def chunk_by_function(self, file_path) -> List[CodeChunk]
      def chunk_by_class(self, file_path) -> List[CodeChunk]
      def get_chunk_context(self, chunk) -> str  # 包含依赖信息
  
  # CodeChunk 结构
  class CodeChunk:
      content: str  # 函数/类代码
      docstring: str  # 文档字符串
      signature: str  # 函数签名
      language: str  # python/javascript/rust
      file_path: str
      start_line: int
      end_line: int
      dependencies: List[str]  # 调用的其他函数
      callers: List[str]  # 调用此函数的函数
  ```

- [ ] **Day 5-6: 代码记忆索引**
  - [ ] 将代码块存入向量存储
  - [ ] 存储代码元数据（语言、文件、行号）
  - [ ] 存储代码关系（调用图）

- [ ] **Day 7: 代码查询 API**
  ```python
  # API 端点
  GET /api/v1/code/search?query="用户认证"&language=python
  GET /api/v1/code/definition?function=authenticate_user
  GET /api/v1/code/references?function=authenticate_user
  GET /api/v1/code/callgraph?entry=main
  ```

**Week 3 交付物**:
- [ ] 代码解析和分块功能
- [ ] 能回答"这个函数在哪里被调用"
- [ ] 能回答"用户认证相关的代码在哪里"

---

### Phase 1 完成标准

```markdown
✅ Phase 1 完成检查清单:

功能验证:
- [ ] 运行 `memnexus init` 成功初始化项目
- [ ] 运行 `memnexus index` 成功索引代码和 Git 历史
- [ ] 查询 "auth 模块最近改了什么" 返回相关 commit
- [ ] 查询 "login 函数在哪里被调用" 返回调用链

代码质量:
- [ ] 核心功能测试覆盖 > 60%
- [ ] 文档更新完成
- [ ] 代码审查通过

演示准备:
- [ ] 准备 3 分钟的演示视频
- [ ] 准备示例项目展示
```

---

## Phase 2: 找场景（第 4-7 周）

**目标**: 找到第一个真正使用 MemNexus 的场景，验证产品价值

### Week 4-5: Vibe Kanban 集成 POC

#### 目标
开发 Vibe Kanban 插件，让 VK 用户能在 Session 之间共享记忆。

#### 技术方案

由于 VK 可能没有官方插件机制，考虑以下集成方式：

**方案 A: MCP Server（推荐）**
```python
# MemNexus 作为 MCP Server
# VK 通过 MCP 协议调用记忆功能

class MemNexusMCPServer:
    @tool
    def memory_recall(self, query: str, context: dict) -> str:
        """在 MemNexus 中搜索相关记忆"""
        
    @tool
    def memory_store(self, content: str, metadata: dict) -> str:
        """存储当前 Session 的关键决策"""
```

**方案 B: 浏览器扩展**
- 开发 Chrome/Firefox 扩展
- 在 VK Web UI 中注入"相关记忆"面板

#### 任务清单

- [ ] **Day 1-3: 研究 VK 集成点**
  - [ ] 研究 VK 是否支持 MCP
  - [ ] 研究 VK 的 API（如果有）
  - [ ] 确定集成方案

- [ ] **Day 4-7: MCP Server 实现**
  - [ ] 实现 `memnexus mcp` 子命令
  - [ ] 暴露记忆搜索工具
  - [ ] 暴露记忆存储工具
  - [ ] 测试与 VK 的连接

- [ ] **Day 8-10: VK 场景实现**
  - [ ] Session 结束时自动存储关键决策
  - [ ] 新 Session 开始时自动召回相关记忆
  - [ ] 在 VK UI 中显示记忆面板（如果可能）

---

### Week 6: 用户验证

#### 目标
找到 3-5 个 VK 用户试用，收集反馈。

#### 任务清单

- [ ] **寻找用户**
  - [ ] 在 Vibe Kanban GitHub Discussions 发帖
  - [ ] 在相关 Discord 社区宣传
  - [ ] 找身边的开发者朋友试用

- [ ] **收集反馈**
  - [ ] 准备反馈问卷
  - [ ] 进行 1-1 用户访谈
  - [ ] 记录使用日志和痛点

- [ ] **迭代优化**
  - [ ] 根据反馈调整功能优先级
  - [ ] 修复关键问题
  - [ ] 优化用户体验

---

### Week 7: 决策点

#### 关键决策

基于用户反馈，决定下一步方向：

```
如果 VK 集成反馈好:
  → 继续深化 VK 集成，成为 VK 生态的一部分
  
如果 VK 集成反馈一般，但代码记忆功能受认可:
  → 转向独立产品，支持更多工具
  
如果整体反馈一般:
  → 重新评估产品定位，考虑 pivot
```

---

### Phase 2 完成标准

```markdown
✅ Phase 2 完成检查清单:

用户验证:
- [ ] 3+ 个用户实际试用
- [ ] 收集到具体的使用反馈
- [ ] 至少有 1 个用户表示"有用"

产品决策:
- [ ] 明确下一步方向
- [ ] 更新产品路线图
```

---

## Phase 3: 建生态（第 8 周起，持续）

**目标**: 从插件成长为基础设施，建立生态

### Stage 1: 多工具支持（2-3 个月）

#### 3.1 Kimi CLI 插件
- [ ] 开发 Kimi CLI 的记忆插件
- [ ] 通过 MCP 或 Shell 包装器集成
- [ ] 中文优化

#### 3.2 VSCode 扩展
- [ ] 开发 VSCode 扩展
- [ ] 在编辑器中显示相关记忆
- [ ] 支持代码补全时的记忆提示

#### 3.3 Claude Code 集成
- [ ] 开发 Claude Code 插件（类似 OpenViking 的做法）
- [ ] 支持 Session 记忆同步

---

### Stage 2: 平台化（3-6 个月）

#### 2.1 开放 API
- [ ] 设计稳定的 REST API
- [ ] API 文档和 SDK
- [ ] API 密钥管理

#### 2.2 第三方集成
- [ ] 邀请开发者集成 MemNexus
- [ ] 建立集成示例库
- [ ] 社区贡献指南

#### 2.3 云服务（可选）
- [ ] 云托管版本
- [ ] 团队共享记忆
- [ ] 付费计划

---

### Stage 3: 商业化探索（6-12 个月）

#### 3.1 团队版
- [ ] 团队共享记忆空间
- [ ] 权限管理
- [ ] 审计日志

#### 3.2 企业版
- [ ] 私有部署
- [ ] SSO 集成
- [ ] SLA 支持

---

## 关键里程碑

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         关键里程碑时间表                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Month 1 (Week 1-4)                                                          │
│  ├── Week 2: 代码清理完成，核心功能可用                                       │
│  ├── Week 3: Git 集成 MVP 完成                                               │
│  └── Week 4: 代码感知 RAG MVP 完成                                           │
│      🎯 Milestone 1: 第一个可用版本                                           │
│                                                                              │
│  Month 2 (Week 5-8)                                                          │
│  ├── Week 5-6: Vibe Kanban 集成 POC                                          │
│  ├── Week 7: 用户验证                                                        │
│  └── Week 8: 产品决策                                                        │
│      🎯 Milestone 2: 验证产品价值                                             │
│                                                                              │
│  Month 3-4                                                                   │
│  ├── Kimi CLI 插件                                                           │
│  └── VSCode 扩展                                                             │
│      🎯 Milestone 3: 多工具支持                                               │
│                                                                              │
│  Month 6                                                                     │
│  ├── 100+ 活跃用户                                                           │
│  └── 开源社区贡献者 5+                                                       │
│      🎯 Milestone 4: 产品市场契合 (PMF)                                       │
│                                                                              │
│  Month 12                                                                    │
│  ├── 1000+ 活跃用户                                                          │
│  ├── 商业化探索                                                              │
│  └── 成为代码记忆层的标准                                                     │
│      🎯 Milestone 5: 可持续产品                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 成功指标

### 3 个月目标

| 指标 | 目标 | 说明 |
|------|------|------|
| 活跃用户 | 50+ | 实际使用，不只是 star |
| GitHub Stars | 200+ | 自然增长 |
| 集成数量 | 2 | VK + 至少一个其他工具 |
| 用户反馈 | 5+ 正面 | "帮我省了时间" |

### 6 个月目标

| 指标 | 目标 | 说明 |
|------|------|------|
| 活跃用户 | 200+ | 持续增长 |
| 社区贡献者 | 5+ | 外部 PR |
| 知名推荐 | 1+ | 被知名开发者/团队推荐 |
| 商业化探索 | 开始 | 团队版或云版本 |

### 12 个月目标

| 指标 | 目标 | 说明 |
|------|------|------|
| 活跃用户 | 1000+ | 稳定增长 |
| 收入 | $1K+/月 | 可持续 |
| 生态集成 | 10+ | 第三方集成 |
| 团队规模 | 2-3 人 | 全职或兼职 |

---

## 风险与应对

| 风险 | 可能性 | 影响 | 应对策略 |
|------|--------|------|----------|
| Vibe Kanban 官方推出记忆功能 | 中 | 高 | 保持工具无关性，快速支持其他平台 |
| Mem0/Supermemory 推出代码专用版本 | 低 | 高 | 深耕 Git 集成，建立差异化 |
| 用户不买账，找不到 PMF | 中 | 高 | 3 个月无 traction 则 pivot |
| 技术实现比预期复杂 | 高 | 中 | 先 MVP，再迭代 |
| 时间/精力不足 | 高 | 中 | 设定明确的里程碑，及时止损 |

---

## 资源需求

### 开发资源

- **全职**: 1 人（你）
- **兼职**: 可选（社区贡献者）
- **时间投入**: 每周 20-30 小时

### 基础设施

- **开发**: 本地即可
- **测试**: GitHub Actions（已有）
- **文档**: GitHub Pages 或 Vercel
- **云服务**（未来）: 按需

### 资金需求

- **Phase 1-2**: 几乎为零（开源开发）
- **Phase 3**: 云服务成本（$50-100/月）

---

## 立即行动

### 本周任务（今天开始）

```markdown
Day 1 (今天):
- [ ] 阅读并理解 VISION.md 和 ROADMAP.md
- [ ] 创建 `feature/code-memory` 分支
- [ ] 列出需要冻结/移除的功能

Day 2-3:
- [ ] 开始代码清理
- [ ] 简化 `MemoryStore` API

Day 4-5:
- [ ] 实现 `memnexus init` 命令
- [ ] 测试初始化流程

Day 6-7:
- [ ] 开始 Git 集成
- [ ] 实现 `GitHistoryExtractor`
```

---

## 附录

### A. 技术债务清理清单

需要冻结/简化的功能：

```python
# 标记为 experimental，不导出到公共 API
src/memnexus/memory/
├── advanced_rag.py          # 冻结 - 太复杂
├── layers/                  # 冻结 - 分层记忆 v2
│   ├── manager.py
│   └── ...
├── rmt/                     # 冻结 - 循环记忆
│   └── ...
├── knowledge_graph/         # 冻结 - 知识图谱
│   └── ...
├── retrieval/               # 简化 - 只保留基础检索
│   ├── adaptive.py          # 冻结
│   └── hybrid.py            # 简化
└── compression/             # 冻结
    └── ...

# 保留并强化的功能
src/memnexus/memory/
├── store.py                 # 简化，保留核心
├── rag.py                   # 简化，保留核心
└── context.py               # 保留

# 新增的核心模块
src/memnexus/code_memory/    # 新增
├── __init__.py
├── git_extractor.py
├── code_parser.py
├── dependency_graph.py
└── code_rag.py
```

### B. 参考资源

- [Vibe Kanban GitHub](https://github.com/BloopAI/vibe-kanban)
- [OpenViking 文档](https://openviking.ai/docs)
- [Mem0 文档](https://docs.mem0.ai)
- [Tree-sitter 文档](https://tree-sitter.github.io/tree-sitter/)

---

*文档版本历史*:
- v1.0 (2026-03-25): 初始版本，基于新定位的务实路线图

---

**下一步**: 阅读 `VISION.md`，然后开始 Week 1 的任务。
