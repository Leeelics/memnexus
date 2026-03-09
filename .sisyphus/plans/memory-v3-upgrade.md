# MemNexus 全面升级开发计划

> **版本**: v3.0 - Memory Evolution  
> **目标**: 基于前沿研究论文和开源项目，实现记忆系统的重大架构升级  
> **时间预估**: 8-12 周  

---

## 执行摘要

基于对 **12+ 篇前沿论文**（HippoRAG、MELODI、SEAKR、RMT、HEMA 等）和 **10+ 开源项目**（mem0、MemGPT、GraphRAG 等）的深入研究，本计划提出 MemNexus 的 Memory v3.0 升级路径。

### 核心升级目标

1. **知识图谱增强记忆** - 引入 HippoRAG 图检索能力
2. **自适应智能检索** - 实现 SEAKR 不确定性驱动的检索决策
3. **分层压缩记忆** - 构建 MELODI 三层记忆架构
4. **海马体双记忆** - 实现 HEMA 紧凑型+向量记忆系统
5. **长期记忆扩展** - 支持 RMT 200万 token 级长上下文

### 技术差距分析

| 模块 | 当前状态 | 目标状态 | 差距等级 |
|------|---------|---------|---------|
| `memory/store.py` | LanceDB 向量存储 | 分层记忆 + 知识图谱 | 🔴 大 |
| `memory/rag.py` | 基础向量检索 | 自适应 + 图检索 + 混合 | 🔴 大 |
| `memory/context.py` | 单层上下文 | 海马体双记忆架构 | 🔴 大 |
| `memory/layers/` | 基础框架已实现 | 完整 MELODI 实现 | 🟡 中 |
| `memory/retrieval/` | SEAKR 框架已启动 | 完整自适应系统 | 🟡 中 |
| `orchestrator/` | 任务编排 | 智能调度 + 协作 | 🟡 中 |

---

## Phase 1: 知识图谱增强 (Week 1-3)

### 目标
实现 HippoRAG 论文中的知识图谱检索能力，支持多跳推理。

### 技术参考
- **论文**: HippoRAG (NeurIPS 2024)
- **开源**: GraphRAG (Microsoft), LightRAG
- **核心创新**: LLM 提取三元组 + 个性化 PageRank 图搜索

### 实施任务

#### 1.1 知识图谱构建模块
```python
# 新建: src/memnexus/memory/knowledge_graph/builder.py
class KnowledgeGraphBuilder:
    """使用 LLM 提取知识图谱三元组。"""
    
    async def extract_triples(self, text: str) -> List[Triple]:
        """从文本提取 (subject, relation, object) 三元组。"""
        # 使用 LLM 进行开放信息抽取
        
    async def build_graph(self, documents: List[Document]) -> Graph:
        """构建无模式知识图谱。"""
```

**验收标准**:
- [ ] 从代码/文档中准确提取实体关系
- [ ] 支持开放域（无预定义 schema）
- [ ] 处理速度: >1000 tokens/秒

#### 1.2 图存储集成
```python
# 新建: src/memnexus/memory/knowledge_graph/store.py
class GraphStore:
    """知识图谱存储后端。"""
    
    # 可选: Neo4j (生产) / NetworkX (开发) / 自研
    async def add_triples(self, triples: List[Triple])
    async def get_neighbors(self, entity: str, depth: int = 1)
    async def personalized_pagerank(self, seed_nodes: List[str])
```

**技术选型决策**:
- **轻量级**: NetworkX + 内存存储（开发/测试）
- **生产级**: Neo4j / Amazon Neptune（云部署）
- **嵌入式**: 考虑使用 LanceDB 的图扩展

#### 1.3 HippoRAG 检索器
```python
# 新建: src/memnexus/memory/knowledge_graph/hippo_rag.py
class HippoRAG:
    """海马体启发的长期记忆检索。"""
    
    async def retrieve(self, query: str, top_k: int = 5):
        # 1. 实体识别
        entities = await self._extract_entities(query)
        
        # 2. PageRank 图搜索
        relevant = await self._page_rank_search(entities)
        
        # 3. 获取相关文本
        return await self._get_context(relevant)
```

**性能指标**:
- 多跳问答准确率提升 >20%
- 检索延迟 < 100ms（单跳）
- 支持 3+ 跳推理

### Phase 1 依赖关系
```
1.1 三元组提取
    ↓
1.2 图存储实现
    ↓
1.3 HippoRAG 集成
    ↓
API 端点更新
```

---

## Phase 2: 自适应检索系统 (Week 2-4)

### 目标
完成 SEAKR 论文的自适应检索实现，实现"不确定性驱动检索"。

### 技术参考
- **论文**: SEAKR - Self-aware Knowledge Retrieval (2024)
- **核心创新**: 基于 LLM 内部状态的不确定性估计

### 实施任务

#### 2.1 不确定性估计模块
```python
# 扩展: src/memnexus/memory/retrieval/adaptive.py
class UncertaintyEstimator:
    """估计 LLM 对回答的不确定性。"""
    
    def estimate_from_logits(self, logits: Tensor) -> float:
        """从输出分布计算熵值。"""
        
    def estimate_from_hidden_states(self, hidden: Tensor) -> float:
        """从隐藏层状态估计置信度。"""
        
    async def estimate_semantic_uncertainty(
        self, 
        query: str, 
        llm_response: str
    ) -> UncertaintyScore:
        """基于多次采样的语义一致性。"""
```

**方法对比**:
| 方法 | 精度 | 开销 | 适用场景 |
|------|------|------|---------|
| 熵值法 | 中 | 低 | 实时决策 |
| 隐藏层 | 高 | 中 | 需要模型访问 |
| 语义一致性 | 最高 | 高 | 复杂查询 |

#### 2.2 智能检索决策
```python
class AdaptiveRetriever:
    """决定是否检索 + 如何检索。"""
    
    async def should_retrieve(
        self, 
        query: str,
        context: Context,
        uncertainty_threshold: float = 0.6
    ) -> RetrievalDecision:
        """
        决策逻辑:
        1. IF uncertainty < threshold: 跳过检索
        2. IF query is factual: 启用知识图谱
        3. IF query needs context: 启用向量检索
        4. IF complex reasoning: 启用混合检索
        """
        
    async def rerank_by_uncertainty(
        self,
        query: str,
        candidates: List[Document]
    ) -> List[Document]:
        """按不确定性降低程度重排序。"""
```

#### 2.3 检索策略路由
```python
class RetrievalRouter:
    """根据查询类型路由到不同检索器。"""
    
    ROUTES = {
        'factual': 'knowledge_graph',      # HippoRAG
        'procedural': 'vector',            # 标准 RAG
        'code': 'hybrid',                   # 混合检索
        'conversational': 'hierarchical',   # 分层记忆
    }
    
    async def route(self, query: str) -> str:
        """基于查询分类选择检索策略。"""
```

### Phase 2 性能指标
- 减少 40-60% 的不必要检索
- 检索准确率提升 15%
- 端到端延迟降低 30%

---

## Phase 3: 分层记忆架构完善 (Week 3-5)

### 目标
完成 MELODI 论文的分层压缩记忆系统。

### 技术参考
- **论文**: MELODI - Memory Compression for Long Contexts (2024)
- **核心创新**: 工作/短期/长期三层 + 三明治压缩结构

### 当前状态评估
```
已存在: memory/layers/base.py - 基础框架
已存在: memory/layers/manager.py - 管理器
缺失: 完整的压缩算法、层间流动机制
```

### 实施任务

#### 3.1 记忆压缩算法
```python
# 扩展: memory/layers/compressors/
class MELODICompressor(Compressor):
    """MELODI 分层压缩实现。"""
    
    async def compress_short_term(
        self, 
        memories: List[MemoryEntry]
    ) -> MemoryEntry:
        """
        短期压缩: 多层循环压缩上下文窗口
        保留近期对话的压缩表示
        """
        
    async def compress_long_term(
        self,
        compressed_memories: List[MemoryEntry]
    ) -> MemoryEntry:
        """
        长期压缩: 在中间层进行进一步压缩
        聚合跨窗口的关键信息
        """
```

#### 3.2 层间流动机制
```python
class HierarchicalMemoryManager:
    """三层记忆管理器。"""
    
    # 工作记忆 (Working Memory)
    # - 高保真、有限容量 (10-20 items)
    # - 当前任务焦点
    
    # 短期记忆 (Short-term Memory)
    # - 循环压缩 (50-100 items)
    # - 会话内有效
    
    # 长期记忆 (Long-term Memory)
    # - 高度压缩摘要
    # - 跨会话持久化
    
    async def promote(
        self, 
        memory: MemoryEntry,
        from_layer: MemoryLayer,
        to_layer: MemoryLayer
    ):
        """记忆在层间流动。"""
        
    async def query_all_layers(
        self,
        query: str
    ) -> LayeredRetrievalResult:
        """跨层检索，合并结果。"""
```

#### 3.3 记忆生命周期管理
```python
class MemoryLifecycle:
    """管理记忆从创建到遗忘的全生命周期。"""
    
    async def decay(self, layer: MemoryLayer):
        """
        记忆衰减:
        - 工作记忆: 任务完成后清空
        - 短期记忆: 会话结束后压缩到长期
        - 长期记忆: 按重要性排序，容量满时遗忘
        """
        
    async def consolidate(self):
        """
        记忆巩固 (睡眠时):
        - 短期 → 长期转移
        - 相似记忆合并
        - 提取抽象知识
        """
```

### Phase 3 性能目标
- 内存占用减少 8x（对比单层存储）
- 支持 300+ 轮对话
- 长上下文困惑度降低 20%

---

## Phase 4: 海马体双记忆架构 (Week 5-7)

### 目标
实现 HEMA 论文的双记忆系统，支持超长对话。

### 技术参考
- **论文**: HEMA - Hippocampus-Inspired Extended Memory (2025)
- **核心创新**: 紧凑型记忆（摘要）+ 向量记忆（情节）

### 实施任务

#### 4.1 紧凑型记忆
```python
# 新建: memory/hema/compact_memory.py
class CompactMemory:
    """
    持续更新的单句摘要。
    保留全局叙述，保持连贯性。
    """
    
    async def update(self, new_content: str):
        """
        增量更新摘要:
        - 提取关键事实
        - 合并到现有摘要
        - 保持 3.5K tokens 以内
        """
        
    def get_summary(self) -> str:
        """获取当前全局摘要。"""
```

#### 4.2 向量情节记忆
```python
class EpisodicMemory:
    """
    分块嵌入的情节存储。
    支持基于相似度的检索。
    """
    
    async def store_episode(self, content: str, metadata: dict):
        """存储情节片段。"""
        
    async def retrieve_relevant(
        self, 
        query: str,
        top_k: int = 5
    ) -> List[Episode]:
        """基于余弦相似度检索。"""
```

#### 4.3 双记忆整合
```python
class HEMAMemorySystem:
    """HEMA 双记忆架构实现。"""
    
    def __init__(self):
        self.compact = CompactMemory()
        self.episodic = EpisodicMemory()
        
    async def get_context(self, query: str) -> Context:
        """
        整合双记忆:
        1. 总是包含紧凑型记忆（全局上下文）
        2. 检索相关的向量情节
        3. 合并构建最终上下文
        """
        compact_summary = self.compact.get_summary()
        relevant_episodes = await self.episodic.retrieve_relevant(query)
        
        return self._merge_context(compact_summary, relevant_episodes)
```

### Phase 4 性能目标
- 支持 300+ 轮对话
- 事实回忆准确率: 41% → 87%
- 连贯性评分: 2.7 → 4.3

---

## Phase 5: 长期记忆扩展 (Week 6-8)

### 目标
实现 RMT 论文的循环记忆机制，支持 200万 token 级长上下文。

### 技术参考
- **论文**: RMT - Recurrent Memory Transformer (AAAI 2024)
- **开源**: RMT GitHub 实现
- **核心创新**: 记忆 token 在段间传递，线性复杂度

### 实施任务

#### 5.1 序列分段处理器
```python
# 新建: memory/rmt/segment_processor.py
class SegmentProcessor:
    """处理长序列的分段。"""
    
    def segment_sequence(
        self,
        tokens: List[int],
        segment_size: int = 2048
    ) -> List[List[int]]:
        """将长序列切分为有重叠的段。"""
        
    async def process_with_memory(
        self,
        segments: List[List[int]],
        memory_tokens: List[int]
    ) -> Tuple[List[int], List[int]]:
        """
        处理一段，返回输出 + 更新后的记忆。
        记忆 token 在段间传递。
        """
```

#### 5.2 循环记忆管理
```python
class RecurrentMemoryManager:
    """管理跨段的记忆传递。"""
    
    async def forward(
        self,
        segment: Segment,
        previous_memory: MemoryState
    ) -> Tuple[Output, MemoryState]:
        """
        前向传播:
        - 将上一段记忆注入当前段
        - 处理当前段
        - 提取更新后的记忆
        """
        
    async def process_long_sequence(
        self,
        full_sequence: str,
        max_tokens: int = 2_000_000
    ) -> AsyncIterator[Output]:
        """
        流式处理超长序列。
        适用于: 代码库分析、长文档处理
        """
```

#### 5.3 课程学习训练
```python
class CurriculumLearning:
    """段级课程学习。"""
    
    async def train_with_curriculum(
        self,
        model,
        sequences: List[str]
    ):
        """
        从短序列开始，逐步增加长度。
        使模型适应超长上下文。
        """
```

### Phase 5 性能目标
- 支持 200万 token 处理
- FLOPs 减少 29-295 倍
- 保持线性复杂度 O(n)

---

## Phase 6: TurboRAG 性能优化 (Week 7-9)

### 目标
实现 TurboRAG 论文的 KV 缓存预计算，加速推理。

### 技术参考
- **论文**: TurboRAG - KV Cache Precomputation (OpenReview 2024)
- **核心创新**: 预计算文档 KV 缓存，减少 TTFT 9.4x

### 实施任务

#### 6.1 KV 缓存预计算
```python
# 新建: memory/turbo_rag/kv_cache.py
class KVCacheManager:
    """管理文档的 KV 缓存。"""
    
    async def precompute_cache(self, document: Document):
        """
        离线索引阶段:
        - 编码文档
        - 计算并存储 KV 缓存
        """
        
    async def retrieve_kv_cache(
        self,
        query: str
    ) -> List[KVCache]:
        """
        在线检索阶段:
        - 检索相关文档的 KV 缓存
        - 直接加载，无需重新计算
        """
```

#### 6.2 独立注意力实现
```python
class IndependentAttention:
    """
    TurboRAG 独立注意力模式。
    文档独立编码，避免交叉注意力。
    """
    
    def forward(
        self,
        query_tokens: Tensor,
        doc_kv_caches: List[KVCache]
    ):
        """
        独立注意力 + 位置重排序。
        """
```

### Phase 6 性能目标
- TTFT 减少 9.4 倍
- 推理延迟降低 85%
- 吞吐量提升 5x

---

## Phase 7: 系统集成与 API (Week 8-10)

### 目标
整合所有新组件，提供统一的 API。

### 实施任务

#### 7.1 统一 RAG 接口
```python
# 重构: memory/rag_v3.py
class MemNexusRAG:
    """
    MemNexus v3.0 统一 RAG 接口。
    
    整合:
    - HippoRAG (知识图谱)
    - SEAKR (自适应检索)
    - MELODI (分层记忆)
    - HEMA (双记忆)
    - RMT (长上下文)
    - TurboRAG (性能优化)
    """
    
    async def query(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.AUTO,
        max_tokens: int = 4000
    ) -> RAGResult:
        """
        智能查询:
        1. 自适应决策是否检索
        2. 路由到最佳检索策略
        3. 跨层检索记忆
        4. 智能上下文构建
        """
```

#### 7.2 REST API 更新
```python
# server.py 新增端点

@router.post("/rag-v3/query")
async def rag_v3_query(
    request: RAGQueryRequest
) -> RAGQueryResponse:
    """新 RAG 系统查询接口。"""
    
@router.post("/rag-v3/index-document")
async def index_document_with_kg(
    document: DocumentUpload
):
    """支持知识图谱的文档索引。"""
    
@router.get("/memory/layers/stats")
async def get_memory_layer_stats():
    """获取分层记忆统计。"""
```

#### 7.3 配置系统升级
```yaml
# config.yaml 新增配置
memory:
  version: "3.0"
  
  # 分层记忆
  hierarchical:
    working_capacity: 20
    short_term_capacity: 100
    long_term_capacity: 1000
    
  # 知识图谱
  knowledge_graph:
    enabled: true
    backend: "neo4j"  # neo4j / networkx
    
  # 自适应检索
  adaptive:
    enabled: true
    uncertainty_threshold: 0.6
    
  # RMT
  rmt:
    enabled: true
    segment_size: 2048
    max_tokens: 2_000_000
```

---

## Phase 8: 测试与优化 (Week 10-12)

### 目标
全面测试、性能优化、文档更新。

### 测试矩阵

| 测试类型 | 覆盖率目标 | 关键场景 |
|---------|-----------|---------|
| 单元测试 | 80% | 各模块独立测试 |
| 集成测试 | 关键路径 | RAG 端到端流程 |
| 性能测试 | 基准对比 | 延迟、吞吐量、内存 |
| 准确率测试 | 问答数据集 | 多跳推理、长上下文 |

### 基准测试
```python
# 新建: benchmarks/rag_benchmark.py

class RAGBenchmark:
    """RAG 系统基准测试。"""
    
    async def benchmark_hipporag(self):
        """测试多跳问答性能。"""
        
    async def benchmark_melodi(self):
        """测试分层记忆压缩率。"""
        
    async def benchmark_seakr(self):
        """测试自适应检索效率。"""
        
    async def benchmark_end_to_end(self):
        """端到端性能测试。"""
```

---

## 依赖关系图

```
Phase 1: 知识图谱
    │
    ▼
Phase 2: 自适应检索 ◄────── 依赖 Phase 1
    │
    ▼
Phase 3: 分层记忆 ◄──────── 可并行 Phase 2
    │
    ▼
Phase 4: HEMA ◄──────────── 依赖 Phase 3
    │
    ▼
Phase 5: RMT ◄───────────── 可并行 Phase 4
    │
    ▼
Phase 6: TurboRAG ◄──────── 可并行 Phase 5
    │
    ▼
Phase 7: 系统集成 ◄──────── 依赖所有 Phase
    │
    ▼
Phase 8: 测试优化 ◄──────── 依赖 Phase 7
```

---

## 技术栈决策

### 知识图谱存储
| 方案 | 优点 | 缺点 | 推荐场景 |
|------|------|------|---------|
| NetworkX | 简单、无依赖 | 内存限制 | 开发/测试 |
| Neo4j | 生产级、性能高 | 部署复杂 | 生产环境 |
| LanceDB 扩展 | 统一存储 | 开发中 | 未来考虑 |

**决策**: 支持 NetworkX（开发）+ Neo4j（生产）双后端

### LLM 集成
| 方案 | 成本 | 质量 | 延迟 |
|------|------|------|------|
| OpenAI API | $$$ | 最高 | 中 |
| Local LLM | $ | 中 | 低 |
| Hybrid | $$ | 可调 | 可调 |

**决策**: 支持 OpenAI + Local LLM 混合模式

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 知识图谱构建质量差 | 中 | 高 | 多轮 LLM 验证 + 人工审核 |
| 自适应检索误触发 | 中 | 中 | 可调阈值 + A/B 测试 |
| 内存占用超标 | 低 | 高 | 压缩算法调优 + LRU 缓存 |
| API 兼容性破坏 | 低 | 高 | v2 适配器 + 渐进迁移 |

---

## 成功指标

### 技术指标
- [ ] 多跳问答准确率: +20%
- [ ] 检索延迟: -50%
- [ ] 内存占用: -80% (分层压缩)
- [ ] 支持上下文长度: 200万 tokens

### 用户体验指标
- [ ] Agent 响应更连贯
- [ ] 长对话不丢失上下文
- [ ] 复杂推理更准确

---

## 文档与交付

### 需要更新的文档
1. `docs/ARCHITECTURE.md` - 架构图更新
2. `docs/API.md` - 新 API 文档
3. `research/notes/memory-v3-design.md` - 详细设计文档
4. `CHANGELOG.md` - 版本变更日志

### 交付物清单
- [ ] 完整代码实现
- [ ] 单元测试套件
- [ ] 基准测试报告
- [ ] 迁移指南 (v2 → v3)
- [ ] API 文档

---

## 附录: 论文索引

| 论文 | 年份 | 核心贡献 | 实现模块 |
|------|------|---------|---------|
| HippoRAG | NeurIPS 2024 | 知识图谱 + PageRank | Phase 1 |
| SEAKR | 2024 | 自适应检索 | Phase 2 |
| MELODI | 2024 | 分层压缩记忆 | Phase 3 |
| HEMA | 2025 | 双记忆架构 | Phase 4 |
| RMT | AAAI 2024 | 循环记忆 | Phase 5 |
| TurboRAG | OpenReview 2024 | KV缓存预计算 | Phase 6 |

---

*计划编制: 2026-03-03*  
*最后更新: 2026-03-03*  
*版本: v1.0*
