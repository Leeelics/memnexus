---
name: memnexus
description: MemNexus Code Memory - Persistent memory for AI coding sessions
triggers:
  - "/memory"
  - "/recall"
  - "/remember"
---

# MemNexus Code Memory

**MemNexus** 为 Kimi CLI 提供持久的项目记忆能力。它让 AI 助手能够记住之前的会话内容、代码变更历史、设计决策等。

## 快速开始

```bash
# 1. 初始化项目（在项目根目录）
memnexus init

# 2. 索引项目
memnexus index --git --code

# 3. 开始使用 Kimi CLI，MemNexus 会自动提供记忆
```

## 可用命令

### `/memory search <query>`

搜索项目记忆。

**示例：**
```
/memory search "auth module implementation"
/memory search "recent database changes" --source git
/memory search "login function" --source code
```

**选项：**
- `--source git` - 只搜索 Git 历史
- `--source code` - 只搜索代码符号
- `--limit 10` - 返回最多 10 条结果

### `/memory store <content>`

存储重要信息到记忆。

**示例：**
```
/memory store "使用 Redis 缓存用户会话，TTL 设置为 1 小时" --category decision
/memory store "发现 bug：并发登录时会出现 race condition" --category finding --tags auth bug
```

**选项：**
- `--category decision` - 设计决策
- `--category finding` - 重要发现
- `--category pattern` - 代码模式
- `--category workaround` - 临时解决方案
- `--tags tag1 tag2` - 添加标签

### `/memory status`

查看 MemNexus 状态。

**示例：**
```
/memory status
```

**输出：**
- 项目是否已初始化
- 已索引的 Git commit 数量
- 已索引的代码符号数量
- 总记忆条目数

### `/memory index`

索引项目到记忆。

**示例：**
```
/memory index              # 索引 Git 和代码
/memory index --git        # 只索引 Git
/memory index --code       # 只索引代码
```

### `/memory find <symbol>`

查找特定代码符号。

**示例：**
```
/memory find authenticate_user
/memory find AuthController
/memory find AuthController.login
```

### `/memory history <file>`

查看文件的 Git 历史。

**示例：**
```
/memory history src/auth.py
/memory history src/auth.py --limit 5
```

## 使用场景

### 场景 1：继续之前的工作

**你：** 继续优化登录功能

**Kimi（通过 MemNexus）：**
> 根据记忆，登录功能在 `auth/login.py`：
> - 上次修改：2 天前 (commit: a1b2c3)
> - 当前实现使用 JWT + Redis
> - 已知问题：并发登录有 race condition
> 
> 建议优化方向：添加分布式锁

### 场景 2：理解代码变更

**你：** 这个函数为什么这么写？

**Kimi（通过 MemNexus）：**
> 根据 Git 历史，`authenticate_user` 函数在 3 周前的 PR #42 中修改：
> - 原实现：直接查询数据库
> - 修改原因：添加缓存层提高性能
> - 相关讨论："考虑到并发，我们需要..."

### 场景 3：记录重要决策

**你：** `/memory store "决定使用 PostgreSQL 而不是 MySQL，因为需要 JSONB 支持" --category decision --tags database architecture`

**之后：**

**你：** 我们为什么选 PostgreSQL？

**Kimi：**
> 根据之前的记录："决定使用 PostgreSQL 而不是 MySQL，因为需要 JSONB 支持"

## 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                    MemNexus 架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Kimi CLI Session                                            │
│       ↓                                                      │
│  MemNexus Plugin (/memory commands)                          │
│       ↓                                                      │
│  CodeMemory (Git + Code)                                     │
│       ↓                                                      │
│  LanceDB (向量存储)                                           │
│                                                              │
│  存储内容：                                                   │
│  - Git commit 历史 (message, diff, author)                   │
│  - 代码符号 (函数、类、方法、签名、文档)                        │
│  - 用户记录 (设计决策、重要发现)                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 最佳实践

### 1. 定期索引

在以下情况后运行 `/memory index`：
- 完成一个重要功能
- 提交了多个 commit
- 发现长时间没有索引

### 2. 记录关键决策

当做出重要设计决策时：
```
/memory store "决定使用 CQRS 模式分离读写" --category decision
```

### 3. 标记 Bug 和解决方案

```
/memory store "Bug: 内存泄漏原因是未关闭连接池。解决方案：使用上下文管理器" --category finding --tags bug memory
```

### 4. 使用标签

为记忆添加标签便于后续搜索：
```
/memory store "API 速率限制：100 req/min" --category pattern --tags api rate-limiting
```

## 故障排除

### "Project not initialized"

在项目根目录运行：
```bash
memnexus init
memnexus index --git --code
```

### "No results found"

1. 检查项目是否已索引：`/memory status`
2. 如果未索引，运行：`/memory index`
3. 尝试不同的搜索词

### 搜索结果不准确

尝试更具体的查询：
- ❌ "login"
- ✅ "authenticate_user function implementation"

## 与直接使用 MemNexus CLI 的区别

| 方式 | 适用场景 |
|------|----------|
| **Kimi Plugin** (`/memory`) | 在 Kimi 会话中快速查询，结果自动融入对话 |
| **MemNexus CLI** (`memnexus`) | 批量操作、脚本集成、查看详细统计 |

两者共享同一个记忆数据库，可以混合使用。

## 隐私说明

- 所有数据存储在本地 `.memnexus/` 目录
- 不会上传到任何服务器
- 可以安全地添加 `.memnexus/` 到 `.gitignore`
