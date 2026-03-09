# MemNexus 系统改造规划

> 基于 AI Memory 前沿技术研究的系统性架构升级

## 改造目标

将 MemNexus 从基础的向量存储 + 简单 RAG 架构，升级为具备以下能力的智能记忆系统：

1. **自适应检索** (SEAKR) - 智能判断是否需要外部检索
2. **分层记忆架构** (MELODI) - 短期/长期记忆分层存储与压缩
3. **知识图谱增强** (HippoRAG) - 支持多跳推理的神经符号混合检索
4. **循环记忆** (RMT) - 支持超长上下文的记忆传递机制
5. **智能遗忘** (SynapticRAG) - 基于时间和重要性的记忆管理

---

## 架构对比

### 当前架构

```
User Query → Vector Search → LanceDB → Results → LLM
                    ↑
            Static Embedding
```

**问题**:
- 所有查询都走完整检索流程
- 记忆单层存储，无压缩
- 纯向量相似度，无推理能力
- 记忆只增不减

### 目标架构

```
User Query → Uncertainty Check → [High] → Knowledge Graph → Multi-hop Reasoning
                    ↓ [Low]
            Vector Search + BM25
                    ↓
            Reranking (Cross-encoder)
                    ↓
            Working Memory ←→ Short-term Memory ←→ Long-term Memory
                    ↓
            Compression/Consolidation
```

---

## 改造阶段

### Phase 1: RAG 增强 (Week 1-2)

**目标**: 实现自适应检索和混合检索

| 组件 | 当前 | 改造后 | 参考论文 |
|-----|------|-------|---------|
| 检索决策 | 总是检索 | 不确定性估计 + 动态决策 | SEAKR |
| 检索方式 | 纯向量 | 向量 + BM25 混合 | Modern RAG |
| 结果排序 | 相似度排序 | Cross-encoder 重排序 | RAG best practices |
| 查询处理 | 原样查询 | 查询重写/扩展 | HyDE |

**关键文件**:
- `memory/rag.py` → `memory/advanced_rag.py`
- 新增 `memory/retrieval/` 目录

---

### Phase 2: 分层记忆架构 (Week 3-4)

**目标**: 实现 MELODI 风格的分层压缩记忆

```
┌─────────────────────────────────────┐
│        Working Memory               │
│   - 当前对话上下文 (8K tokens)      │
│   - 全精度保留                      │
├─────────────────────────────────────┤
│        Short-term Memory            │
│   - 近期会话历史 (压缩至 2K)        │
│   - 循环聚合                        │
├─────────────────────────────────────┤
│        Long-term Memory             │
│   - 历史会话摘要                    │
│   - 向量存储                        │
│   - 自动遗忘                        │
└─────────────────────────────────────┘
```

**关键文件**:
- 重构 `memory/store.py`
- 新增 `memory/layers.py`
- 新增 `memory/compression.py`

---

### Phase 3: 知识图谱集成 (Week 5-6)

**目标**: 实现 HippoRAG 的神经符号混合检索

**组件**:
1. **图谱构建器**: 使用 LLM 从文本提取三元组
2. **图存储**: NetworkX (本地) / Neo4j (生产)
3. **图检索**: Personalized PageRank
4. **混合融合**: 向量结果 + 图结果融合

**关键文件**:
- 新增 `memory/knowledge_graph.py`
- 新增 `memory/graph_rag.py`

---

### Phase 4: 智能记忆管理 (Week 7-8)

**目标**: 实现遗忘机制和记忆优化

**功能**:
- 重要性评分 (基于访问频率、时效性)
- 自动摘要合并
- 记忆去重
- 时间衰减

---

## 详细改造计划

### 1. 新增目录结构

```
src/memnexus/
├── memory/
│   ├── __init__.py
│   ├── core/                    # 新增: 核心抽象
│   │   ├── __init__.py
│   │   ├── base.py             # 记忆基类
│   │   ├── interfaces.py       # 接口定义
│   │   └── types.py            # 类型定义
│   ├── layers/                  # 新增: 分层记忆
│   │   ├── __init__.py
│   │   ├── working_memory.py   # 工作记忆
│   │   ├── short_term.py       # 短期记忆
│   │   ├── long_term.py        # 长期记忆
│   │   └── manager.py          # 层间协调
│   ├── retrieval/               # 新增: 检索系统
│   │   ├── __init__.py
│   │   ├── adaptive.py         # 自适应检索 (SEAKR)
│   │   ├── hybrid.py           # 混合检索
│   │   ├── reranker.py         # 重排序
│   │   └── query_rewriter.py   # 查询重写
│   ├── knowledge_graph/         # 新增: 知识图谱
│   │   ├── __init__.py
│   │   ├── extractor.py        # 三元组提取
│   │   ├── store.py            # 图存储
│   │   ├── retrieval.py        # 图检索
│   │   └── rag.py              # 图RAG
│   ├── compression/             # 新增: 压缩
│   │   ├── __init__.py
│   │   ├── summarizer.py       # 摘要生成
│   │   ├── merger.py           # 记忆合并
│   │   └── selector.py         # 重要内容选择
│   ├── legacy/                  # 保留: 旧实现
│   │   ├── store.py            # 原store.py
│   │   ├── rag.py              # 原rag.py
│   │   └── context.py          # 原context.py
│   └── utils/
│       └── embeddings.py
└── ...
```

---

## 关键实现细节

### 1. 自适应检索 (Adaptive Retrieval)

```python
class AdaptiveRetriever:
    """
    SEAKR 风格自适应检索
    基于模型不确定性决定是否检索
    """
    
    async def should_retrieve(self, query: str, context: Context) -> bool:
        # 方法1: 基于历史准确率
        if self.has_history(query):
            return self.get_historical_accuracy(query) < 0.7
        
        # 方法2: 基于查询复杂度
        complexity = self.estimate_complexity(query)
        return complexity > 0.5
    
    async def retrieve(self, query: str) -> List[Memory]:
        if not await self.should_retrieve(query):
            return []
        
        # 执行混合检索
        return await self.hybrid_retriever.retrieve(query)
```

### 2. 分层记忆协调器

```python
class HierarchicalMemoryManager:
    """
    MELODI 风格分层记忆管理
    """
    
    def __init__(self):
        self.working = WorkingMemoryLayer(capacity=8000)
        self.short_term = ShortTermLayer(capacity=2000, compressor=LLMCompressor())
        self.long_term = LongTermLayer(store=VectorStore())
    
    async def add(self, content: str):
        # 添加到工作记忆
        await self.working.add(content)
        
        # 溢出时压缩到短期记忆
        if self.working.is_full():
            batch = self.working.flush()
            compressed = await self.short_term.compress(batch)
            await self.short_term.add(compressed)
        
        # 短期记忆溢出时压缩到长期记忆
        if self.short_term.is_full():
            old_memories = self.short_term.get_oldest(0.3)  # 最旧的30%
            summary = await self.long_term.summarize(old_memories)
            await self.long_term.store(summary)
```

### 3. 知识图谱 RAG

```python
class KnowledgeGraphRAG:
    """
    HippoRAG 风格知识图谱增强检索
    """
    
    async def retrieve(self, query: str) -> RetrievalResult:
        # 1. 提取查询实体
        entities = await self.extract_entities(query)
        
        # 2. 图遍历 (Personalized PageRank)
        graph_results = await self.graph_search(entities)
        
        # 3. 向量检索
        vector_results = await self.vector_search(query)
        
        # 4. 融合排序
        return self.fuse_results(graph_results, vector_results)
```

---

## 向后兼容性

### 迁移策略

1. **保留旧实现**: 将当前 `store.py`, `rag.py`, `context.py` 移动到 `memory/legacy/`
2. **适配器模式**: 新系统提供旧接口的适配器
3. **渐进迁移**: 允许配置切换新旧实现

### 配置示例

```python
# config.py
MEMORY_BACKEND = "hierarchical"  # "legacy" | "hierarchical" | "simple"
RAG_MODE = "adaptive"            # "simple" | "adaptive" | "graph"
```

---

## 性能目标

| 指标 | 当前 | 目标 | 提升 |
|-----|------|------|------|
| 检索延迟 | 200ms | 50ms | 4x |
| 记忆准确率 | 60% | 85% | 1.4x |
| 长上下文支持 | 4K | 100K+ | 25x |
| 存储效率 | 1x | 0.2x | 5x (节省) |

---

## 实施检查清单

### Phase 1: RAG 增强
- [ ] 实现 AdaptiveRetriever 类
- [ ] 实现 HybridRetriever (向量 + BM25)
- [ ] 实现 CrossEncoderReranker
- [ ] 集成到现有 RAGPipeline
- [ ] 单元测试

### Phase 2: 分层记忆
- [ ] 设计 MemoryLayer 抽象
- [ ] 实现 WorkingMemoryLayer
- [ ] 实现 ShortTermLayer (含压缩)
- [ ] 实现 LongTermLayer
- [ ] 实现层间协调器
- [ ] 集成到 SessionManager

### Phase 3: 知识图谱
- [ ] 选择图存储 (NetworkX/Neo4j)
- [ ] 实现 TripleExtractor
- [ ] 实现 GraphRetriever
- [ ] 实现融合排序
- [ ] 可选：图可视化

### Phase 4: 记忆管理
- [ ] 实现重要性评分
- [ ] 实现记忆合并
- [ ] 实现自动遗忘
- [ ] 添加配置面板

---

**开始实施 →**
