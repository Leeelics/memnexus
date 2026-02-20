# ACP (Agent Client Protocol) 协议规范

## 概述

ACP 是 Anthropic 设计的协议，用于 IDE/编辑器与 Claude Code 等 Agent 之间的通信。

## 协议特点

- **传输方式**: JSON-RPC over stdio
- **连接模式**: 长连接，双向通信
- **核心能力**: 工具调用、资源访问、状态保持

## 通信流程

### 1. 初始化

```json
// Client -> Agent (initialize)
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-01-01",
    "capabilities": {
      "tools": true,
      "resources": true,
      "prompts": false
    },
    "clientInfo": {
      "name": "MemNexus",
      "version": "0.1.0"
    }
  }
}

// Agent -> Client (initialize response)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-01-01",
    "capabilities": {
      "tools": {
        "listChanged": true
      },
      "resources": {
        "subscribe": true,
        "listChanged": true
      }
    },
    "serverInfo": {
      "name": "claude-code",
      "version": "2.1.34"
    }
  }
}
```

### 2. 发送提示

```json
// Client -> Agent (prompt/request)
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "prompts/request",
  "params": {
    "name": "default",
    "arguments": {
      "prompt": "设计用户认证系统的数据库 schema",
      "sessionId": "sess_abc123"
    }
  }
}
```

### 3. 流式响应

```json
// Agent -> Client (streaming response)
{
  "jsonrpc": "2.0",
  "method": "notifications/message",
  "params": {
    "level": "info",
    "message": "我将为您设计数据库 schema..."
  }
}

// 工具调用
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "Read",
    "arguments": {
      "file_path": "README.md"
    }
  }
}

// Client -> Agent (tool result)
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": "# Project README...",
    "mimeType": "text/markdown"
  }
}
```

## 工具类型

### 标准工具

| 工具名 | 说明 | 参数 |
|-------|------|------|
| Read | 读取文件 | file_path, offset, limit |
| Edit | 编辑文件 | file_path, old_string, new_string |
| Create | 创建文件 | file_path, content |
| Execute | 执行命令 | command, cwd, timeout |
| LS | 列出目录 | path |
| Grep | 搜索文件 | pattern, path |
| Glob | 文件匹配 | pattern |

### 消息类型

```json
// 普通消息
{
  "type": "message",
  "role": "assistant",
  "content": "我将开始设计..."
}

// 工具调用
{
  "type": "tool_call",
  "toolName": "Read",
  "parameters": {...}
}

// 工具结果
{
  "type": "tool_result",
  "toolCallId": "call_123",
  "content": "..."
}

// 系统消息
{
  "type": "system",
  "subtype": "init",
  "cwd": "/workspace",
  "sessionId": "sess_abc123"
}
```

## MemNexus 实现

```python
class ACPAdapter:
    """ACP 协议适配器"""
    
    PROTOCOL_VERSION = "2025-01-01"
    
    async def connect(self, process: Process) -> ACPConnection:
        """建立 ACP 连接"""
        conn = ACPConnection(process)
        
        # 发送 initialize
        response = await conn.send_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": self.PROTOCOL_VERSION,
                "capabilities": {
                    "tools": True,
                    "resources": True,
                }
            }
        })
        
        return conn
        
    async def send_prompt(
        self,
        conn: ACPConnection,
        prompt: str,
        context: dict = None
    ) -> AsyncIterator[ACPEvent]:
        """发送提示并流式接收响应"""
        
        # 发送提示
        await conn.send({
            "jsonrpc": "2.0",
            "id": generate_id(),
            "method": "prompts/request",
            "params": {
                "name": "default",
                "arguments": {
                    "prompt": prompt,
                    "context": context
                }
            }
        })
        
        # 流式接收
        async for message in conn.receive_stream():
            event = self._parse_message(message)
            yield event
            
            # 处理工具调用
            if event.type == "tool_call":
                result = await self._handle_tool_call(event)
                await conn.send({
                    "jsonrpc": "2.0",
                    "id": event.id,
                    "result": result
                })
```

## 参考

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [ACP Protocol Draft](https://github.com/anthropics/claude-code/blob/main/PROTOCOL.md)
