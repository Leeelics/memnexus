# OpenViking 测试与 Benchmark 体系深度分析

> 分析时间：2026-04-01  
> 项目路径：`/home/lee/kit/OpenViking`

---

## 1. 项目概述

**OpenViking** 是一个 Agent-native 上下文数据库，采用多语言架构：
- **Python**：核心业务逻辑、客户端/服务端 API
- **C++**：底层向量索引引擎（`tests/engine/`）
- **Rust**：CLI 工具（`crates/ov_cli`）
- **Go**：AGFS 文件系统相关组件

其质量保障体系呈现**金字塔型分层结构**：单元测试 → 集成测试 → API E2E 测试 → RAG Benchmark 效果评估。

---

## 2. 测试体系结构

测试代码集中存放在 `tests/` 目录下，按功能域垂直拆分：

```
tests/
├── client/           # 客户端 API 测试
├── server/           # HTTP Server API & SDK 测试
├── session/          # Session 生命周期与消息管理测试
├── vectordb/         # 向量数据库层测试
├── storage/          # 存储层语义处理与集合测试
├── eval/             # RAGAS 算法评估测试
├── integration/      # 端到端工作流测试
├── engine/           # C++ 索引引擎测试（GoogleTest）
├── api_test/         # 独立 API 集成测试套件（CI 专用）
└── cli/              # CLI 工具测试
```

### 2.1 各模块测试重点

| 目录 | 测试对象 | 典型测试场景 |
|------|---------|-------------|
| `client/` | `AsyncOpenViking` / `SyncOpenViking` | 初始化/关闭、资源增删改查、语义搜索、文件系统操作 |
| `server/` | FastAPI HTTP 服务 | `/health`、鉴权、资源 API、文件系统端点、Session 管理、错误处理 |
| `session/` | `Session` 类 | 创建与加载、消息追加、ToolPart 状态流转、Commit 与归档 |
| `vectordb/` | `VikingVectorIndex` | 二进制行存储、Filter 操作、大规模集合、崩溃恢复（WAL 回放） |
| `storage/` | 语义处理器、VectorDB 适配器 | Embedding 转换、多语言处理、集合 Schema、Stale Lock |
| `integration/` | 完整工作流 | 资源→向量化→搜索、会话→Commit→记忆提取、导出→删除→导入闭环 |
| `engine/` | C++ 索引引擎 | 向量索引、相似度搜索、并发访问、持久化 |

---

## 3. 测试框架与工具

### 3.1 Python 测试栈

```toml
# pyproject.toml 节选
[project.optional-dependencies]
test = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "ragas>=0.1.0",
    "datasets>=2.0.0",
    "pandas>=2.0.0",
    ...
]
```

- **pytest**：核心测试运行器
- **pytest-asyncio**：支持大量异步 API 的测试
- **pytest-cov**：覆盖率收集，默认开启
- **ragas / datasets / pandas**：RAG 效果评估与数据处理

pytest 配置：

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
asyncio_mode = "auto"
addopts = "-v --cov=openviking --cov-report=term-missing"
```

### 3.2 C++ 测试栈

- **GoogleTest**：断言与测试组织
- **CMake**：构建系统（`tests/engine/CMakeLists.txt`）

测试文件：
- `tests/engine/test_common.cpp` — 内存管理、字符串操作、错误处理
- `tests/engine/test_index_engine.cpp` — 向量索引与搜索核心

### 3.3 Rust 测试栈

- `crates/ov_cli` 使用标准 `cargo test` / `cargo build` 流程
- CI 中对 Linux x86_64/ARM64、macOS x86_64/ARM64、Windows x86_64 进行交叉编译验证

---

## 4. 测试运行方式

### 4.1 Python 测试

```bash
# 运行全部 Python 测试
pytest tests/client tests/server tests/session tests/vectordb tests/misc tests/integration -v

# 带 HTML 覆盖率报告
pytest tests/ --cov=openviking --cov-report=html

# 运行特定模块
pytest tests/server/test_auth.py -v

# 关键词过滤
pytest tests/ -k "lifecycle" -v
```

### 4.2 C++ 引擎测试

```bash
cd tests/engine
mkdir build && cd build
cmake ..
make
./test_index_engine
```

### 4.3 Rust CLI 测试

```bash
cargo test -p ov_cli
cargo build --release -p ov_cli
```

---

## 5. CI/CD 自动化体系

CI 配置位于 `.github/workflows/`，采用**分层触发策略**：

### 5.1 工作流矩阵

| 工作流文件 | 触发条件 | 职责 |
|-----------|---------|------|
| `ci.yml` → `_test_full.yml` | `push` 到 `main` | **全矩阵兼容性测试**：OS × Python 版本 |
| `api_test.yml` | `push` 到 `main` / `api_test`、PR 到 `main` | **真实服务 API 集成测试** |
| `pr.yml` | 任意 PR | 快速反馈：lint + 轻量测试 |
| `rust-cli.yml` | `push` 到 `main`、PR 修改 `crates/**` | Rust CLI 跨平台编译与发布 |
| `_lint.yml` | 被调用 | ruff + mypy 代码检查 |
| `_codeql.yml` | 被调用 | CodeQL 安全扫描 |

### 5.2 `_test_full.yml` 详解

- **矩阵**：`ubuntu-24.04` / `macos-14` / `windows-latest` × `Python 3.10/3.11/3.12/3.13`
- **构建**：安装 Go、CMake、Rust、uv → `uv sync --frozen --extra test` → `python setup.py build_ext --inplace`
- **当前执行**：由于单元测试尚在修复中，**目前只运行 `tests/integration/test_quick_start_lite.py`**
- **计划恢复**：待单元测试稳定后切换为 `pytest tests/ -v --cov=openviking --cov-report=term`

### 5.3 `api_test.yml` 详解

这是**最真实的 E2E 测试**：

1. **启动 OpenViking Server**：动态寻找可用端口，后台启动 `python -m openviking.server.bootstrap`
2. **配置注入**：根据环境变量是否存在 `VLM_API_KEY` / `EMBEDDING_API_KEY`，生成完整或最小化的 `ov.conf`
3. **测试分层**：
   - **有密钥**：运行完整 API 测试套件（除 Windows 跳过 filesystem 测试）
   - **无密钥**：跳过 retrieval、admin、skills、observer 等需要模型能力的测试，只跑基础功能
4. **平台覆盖**：`ubuntu-24.04`、`ubuntu-24.04-arm`、`macos-14`、`macos-15-intel`、`windows-latest`
5. **产物收集**：上传 `api-test-report.html` 和 server log 作为 artifact

---

## 6. Benchmark 评估体系

项目内建独立的 **RAG Benchmark 框架**，路径：`benchmark/RAG/`。

### 6.1 项目结构

```
benchmark/RAG/
├── src/
│   ├── pipeline.py              # 评估核心流水线
│   ├── adapters/                # 数据集适配器（Locomo / SyllabusQA / Qasper / FinanceBench）
│   └── core/                    # VectorStore、LLMClient、Metrics、JudgeUtil
├── config/                      # YAML 配置文件
├── scripts/
│   ├── download_dataset.py      # 下载原始数据
│   ├── sample_dataset.py        # 数据采样
│   └── prepare_dataset.py       # 一键准备
├── run.py                       # 评估主入口
└── README.md / README_zh.md
```

### 6.2 支持的数据集

| 数据集 | 文档数 | QA 数 | 领域特点 |
|--------|--------|-------|---------|
| **Locomo** | 10 | 1540 | 多轮长对话，含事实/时间/推理/理解四类问题 |
| **SyllabusQA** | 39 | 5078 | 教育领域大纲，6 种问题类型 |
| **Qasper** | 1585 | 5049 | 学术论文，抽取式/自由式/是否答案 |
| **FinanceBench** | 84 | 150 | 金融领域，开源子集 |

### 6.3 评估流程（5 阶段）

```
┌─────────────────┐
│ 1. Data Prep    │  下载 → 采样 → 格式转换（Adapter）
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Ingestion    │  文档向量化，写入 OpenViking Vector Store
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. Generation   │  对每个问题：检索 top-k 上下文 → LLM 生成答案
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. Evaluation   │  LLM-as-Judge 对比 gold answer 打分
└────────┬────────┘
         ▼
┌─────────────────┐
│ 5. Cleanup      │  删除向量库与中间文档
└─────────────────┘
```

### 6.4 核心评估指标

| 指标 | 含义 | 取值范围 |
|------|------|---------|
| **Recall** | 检索召回率（检索到的相关文档比例） | 0 ~ 1 |
| **F1 Score** | 生成答案与标准答案的 F1 匹配度 | 0 ~ 1 |
| **Accuracy** | LLM-as-Judge 评分 | 0 ~ 4（可归一化到 0~1） |
| **Latency** | 单次检索平均耗时 | 秒 |
| **Token Usage** | 输入/输出/Embedding Token 消耗 | 整数 |

### 6.5 运行方式

```bash
# 1. 安装 benchmark 依赖
uv pip install -e ".[benchmark]"

# 2. 进入目录并准备数据
cd benchmark/RAG
python scripts/prepare_dataset.py --dataset Locomo --num-docs 5

# 3. 配置 LLM 和 OpenViking
#    编辑 config/locomo_config.yaml，设置 llm.api_key 和 dataset_path

# 4. 运行完整评估
python run.py --config config/locomo_config.yaml

# 5. 分阶段运行（可选）
python run.py --config config/locomo_config.yaml --step gen   # 只生成答案
python run.py --config config/locomo_config.yaml --step eval  # 只评估
python run.py --config config/locomo_config.yaml --step del   # 只清理
```

### 6.6 输出产物

评估结果保存在 `Output/{dataset_name}/experiment_{name}/`：

```
Output/
└── Locomo/
    └── experiment_test_top_5/
        ├── generated_answers.json          # 每个问题的检索结果与生成答案
        ├── qa_eval_detailed_results.json   # LLM Judge 详细评分与 reasoning
        ├── benchmark_metrics_report.json   # 聚合指标报告
        ├── docs/                           # 处理后的文档（若未 skip ingestion）
        └── benchmark.log                   # 运行日志
```

---

## 7. 参考基准结果

项目 README 中公布了使用 `doubao-seed-2-0-pro-260215`（temperature=0, top-k=5）的参考结果：

| Dataset | Queries Evaluated | Avg Recall | Avg F1 | Avg Accuracy (0-4) | Normalized Accuracy |
|---------|-------------------|------------|--------|-------------------|---------------------|
| **FinanceBench** | 12 | 0.694 | 0.224 | 2.50 | 0.625 |
| **Locomo** | 80 | 0.592 | 0.254 | 2.40 | 0.600 |
| **Qasper** | 60 | 0.614 | 0.293 | 2.12 | 0.529 |
| **SyllabusQA** | 90 | 0.675 | 0.344 | 2.54 | 0.636 |

这些结果可作为后续优化迭代的 baseline。

---

## 8. 当前状态与 Gap 分析

### 8.1 已具备的能力

- ✅ 完整的测试目录分层（client / server / session / vectordb / integration）
- ✅ 多语言测试覆盖（Python + C++ + Rust）
- ✅ 自动化 CI 矩阵测试（跨 OS × 跨 Python 版本）
- ✅ 真实服务 E2E 测试（`api_test.yml` 启动 live server）
- ✅ 独立 RAG Benchmark 框架，含 4 个标准数据集
- ✅ 代码风格检查（ruff + mypy）与安全扫描（CodeQL）

### 8.2 当前 Gap

- ⚠️ **全量 pytest 套件未在 CI 中运行**：`_test_full.yml` 目前仅执行 `test_quick_start_lite.py`，完整单元测试/集成测试的修复和回归仍在进行中。
- ⚠️ **API Test 对密钥的强依赖**：没有 VLM/Embedding 密钥时，大量测试被跳过，覆盖率下降。
- ⚠️ **Benchmark 未纳入 CI**：RAG benchmark 依赖外部数据集和 LLM API，目前似乎是**离线手动运行**的，未在自动化流水线中体现。

---

## 9. 总结

OpenViking 的测试与 benchmark 体系设计得比较完善：

1. **测试层面**：从 C++ 引擎到 Python 服务端、客户端、向量库、Session 管理，形成了纵向全链路覆盖。
2. **CI 层面**：PR 快速反馈 + Main 分支全矩阵兼容 + API 真实服务 E2E，三层防护网。
3. **效果评估层面**：通过 `benchmark/RAG` 提供标准化的检索与生成效果度量，支撑算法迭代。

下一步值得关注的方向：
- 推动 `_test_full.yml` 恢复运行完整 pytest 套件；
- 探索将 benchmark 关键路径纳入 nightly CI 或 release gate；
- 为 API Test 引入本地 mock LLM/Embedding 服务，降低对外部密钥的依赖。

---

*文档生成时间：2026-04-01*
