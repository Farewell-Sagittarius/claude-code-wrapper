# Anthropic Messages API 参数文档

本文档整理 Anthropic Messages API 的参数支持情况。

> OpenAI 格式兼容性通过 LiteLLM 代理提供，详见 README.md。

---

## 请求参数 (`/v1/messages`)

| 参数 | 类型 | 必填 | 描述 | 状态 |
|------|------|------|------|------|
| `model` | string | ✅ | 模型 ID | ✅ 支持，含别名映射 |
| `messages` | array | ✅ | 对话消息列表 | ✅ 支持 |
| `max_tokens` | integer | ❌ | 最大生成 tokens | ✅ 支持，默认 4096 |
| `system` | string/array | ❌ | 系统提示 | ✅ 支持 |
| `temperature` | number | ❌ | 采样温度 (0-1) | ⚠️ 接收但忽略 |
| `top_p` | number | ❌ | 核采样参数 | ⚠️ 接收但忽略 |
| `top_k` | integer | ❌ | Top-K 采样 | ⚠️ 接收但忽略 |
| `stop_sequences` | array | ❌ | 停止序列 | ❌ SDK 不支持 |
| `stream` | boolean | ❌ | 是否流式 | ✅ 支持 |
| `metadata` | object | ❌ | 请求元数据 | ⚠️ 接收但忽略 |
| `thinking` | object | ❌ | 扩展思维配置 | ✅ 支持 |
| `tools` | array | ❌ | 工具定义列表 | ⚠️ 接收但忽略 |
| `tool_choice` | object | ❌ | 工具选择策略 | ⚠️ 接收但忽略 |

---

## Wrapper 扩展参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `session_id` | string | 会话 ID，用于多轮对话上下文保持 |
| `allowed_tools` | array | 允许使用的内置工具列表 |
| `disallowed_tools` | array | 禁止使用的内置工具列表 |
| `max_turns` | integer | 最大 Agent 对话轮数 |
| `mcp_servers` | object | MCP 服务器配置 |

---

## 响应格式

| 字段 | 类型 | 状态 |
|------|------|------|
| `id` | string | ✅ 支持，格式 `msg_*` |
| `type` | string | ✅ 固定 `"message"` |
| `role` | string | ✅ 固定 `"assistant"` |
| `content` | array | ✅ 支持 |
| `model` | string | ✅ 支持 |
| `stop_reason` | string | ✅ 支持 |
| `stop_sequence` | string | ⚠️ 始终 null |
| `usage` | object | ✅ 支持 |
| `usage.input_tokens` | integer | ✅ 支持 |
| `usage.output_tokens` | integer | ✅ 支持 |

---

## 消息内容类型

| 类型 | 状态 | 说明 |
|------|------|------|
| `text` | ✅ 支持 | 文本内容 |
| `image` (base64) | ✅ 兼容 | 缓存到文件，通过 Read 工具读取 |
| `image` (url) | ✅ 兼容 | 下载并缓存 |
| `document` (text) | ✅ 兼容 | 缓存到文件 |
| `document` (base64 PDF) | ✅ 兼容 | 缓存到文件 |
| `tool_use` | ⚠️ 透传 | 传递给 Claude SDK |
| `tool_result` | ⚠️ 透传 | 传递给 Claude SDK |

---

## 扩展思维 (Extended Thinking)

```json
{
  "thinking": {
    "type": "enabled",
    "budget_tokens": 16000
  }
}
```

| type | 说明 |
|------|------|
| `enabled` | 启用扩展思维，需指定 `budget_tokens` |
| `disabled` | 禁用扩展思维 |

---

## MCP 服务器配置

```json
{
  "mcp_servers": {
    "server-name": {
      "type": "stdio",
      "command": "node",
      "args": ["server.js"]
    }
  }
}
```

### Stdio 类型

```json
{
  "type": "stdio",
  "command": "python",
  "args": ["mcp_server.py"],
  "env": {"KEY": "value"}
}
```

### SSE 类型

```json
{
  "type": "sse",
  "url": "http://localhost:3000/mcp"
}
```

### HTTP 类型

```json
{
  "type": "http",
  "url": "http://localhost:3000/mcp",
  "headers": {"Authorization": "Bearer token"}
}
```

---

## 模型别名

| 别名 | 实际模型 |
|------|----------|
| `claude-code-opus` | `claude-opus-4-5-20251101` |
| `claude-code-sonnet` | `claude-sonnet-4-5-20250929` |
| `claude-code-haiku` | `claude-haiku-4-5-20251001` |

---

## 状态图例

| 符号 | 含义 |
|------|------|
| ✅ | 完全支持 |
| ⚠️ | 接收但不生效 / 部分支持 / 透传 |
| ❌ | 不支持 |

---

## 参考链接

- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
