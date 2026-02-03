# 外部 Tool 支持设计

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 支持 Anthropic 原生 `tools` 参数，实现外部工具调用，同时保留内置工具能力。

**核心原则：** 客户端使用标准 Anthropic API 格式，无感知差异。

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│  请求: messages + tools                                          │
├─────────────────────────────────────────────────────────────────┤
│  1. 解析 messages，计算对话历史 hash                              │
│  2. 查找 session：hash → session_id                              │
│     - 找到 → 恢复 session，提取新消息                            │
│     - 未找到 → 创建新 session                                    │
├─────────────────────────────────────────────────────────────────┤
│  3. 处理 tools 参数                                              │
│     - 分类：内置工具 vs 外部工具                                  │
│     - 外部工具 → 动态创建 SDK MCP Server                         │
├─────────────────────────────────────────────────────────────────┤
│  4. 执行对话                                                     │
│     - 内置工具 → SDK 自动执行                                    │
│     - 外部工具 → can_use_tool 拦截，中断返回                     │
├─────────────────────────────────────────────────────────────────┤
│  5. 返回响应                                                     │
│     - 存储 hash → session_id 映射                                │
│     - stop_reason: end_turn / tool_use                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心机制

### 1. Session 识别（Hash 方案）

**原理：** 通过对话历史的 hash 值识别 session，无需客户端传递 session_id。

```python
def compute_session_hash(messages: List[dict]) -> Optional[str]:
    """计算对话历史 hash，用于识别 session。"""
    # 提取到最后一条 assistant 消息为止的历史
    history = []
    for msg in messages:
        history.append({"role": msg["role"], "content": msg["content"]})
        if msg["role"] == "assistant":
            last_history = history.copy()

    if not last_history:
        return None

    return hashlib.sha256(
        json.dumps(last_history, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:20]
```

**流程：**
```
响应时：存储 hash(对话历史) → session_id
请求时：计算 hash(到最后 assistant) → 查找 session_id
```

### 2. 新消息提取

```python
def extract_new_messages(messages: List[dict]) -> Tuple[Optional[str], List[dict]]:
    """提取新消息，返回 (session_id, new_messages)。"""
    # 找最后一条 assistant 消息的索引
    last_assistant_idx = None
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == "assistant":
            last_assistant_idx = i
            break

    # 无 assistant = 全新对话
    if last_assistant_idx is None:
        return None, messages

    # 计算 hash 查找 session
    session_hash = compute_session_hash(messages[:last_assistant_idx + 1])
    session_id = hash_to_session.get(session_hash)

    # assistant 之后的是新消息
    new_messages = messages[last_assistant_idx + 1:]

    return session_id, new_messages
```

### 3. 工具分类

```python
# 内置工具列表（Claude Agent SDK 提供）
INTERNAL_TOOLS = {
    "Read", "Write", "Edit", "MultiEdit",
    "Bash", "Glob", "Grep",
    "LS", "WebFetch", "WebSearch",
    "TodoRead", "TodoWrite",
    "Task", "Jupyter",
}

def classify_tools(tools: List[dict]) -> Tuple[List[str], List[dict]]:
    """分类工具为内置和外部。"""
    internal = []
    external = []

    for tool in tools:
        name = tool["name"]
        if name in INTERNAL_TOOLS:
            internal.append(name)
        else:
            external.append(tool)

    return internal, external
```

### 4. 外部工具处理

**动态创建 SDK MCP Server：**

```python
from claude_agent_sdk import create_sdk_mcp_server, tool, SdkMcpTool

class ExternalToolInterrupt(Exception):
    """外部工具调用中断，需返回客户端执行。"""
    def __init__(self, tool_use_id: str, name: str, input: dict):
        self.tool_use_id = tool_use_id
        self.name = name
        self.input = input

def create_external_tools_server(tools: List[dict]) -> McpSdkServerConfig:
    """为外部工具创建 SDK MCP Server。"""
    sdk_tools = []

    for tool_def in tools:
        name = tool_def["name"]
        description = tool_def.get("description", "")
        input_schema = tool_def.get("input_schema", {"type": "object", "properties": {}})

        # 创建 handler（实际不执行，只标记需要外部处理）
        async def handler(args, tool_name=name):
            # 这个 handler 不应该被调用
            # 我们通过 can_use_tool 拦截
            raise ExternalToolInterrupt(
                tool_use_id="pending",
                name=tool_name,
                input=args
            )

        sdk_tools.append(SdkMcpTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        ))

    return create_sdk_mcp_server("external_tools", tools=sdk_tools)
```

**can_use_tool 拦截：**

```python
# 存储待处理的 tool_use 信息
pending_tool_uses: Dict[str, List[ToolUseInfo]] = {}  # session_id → tool_uses

async def can_use_tool_callback(
    tool_name: str,
    tool_input: dict,
    context: ToolPermissionContext
) -> PermissionResult:
    """拦截工具调用，区分内置和外部。"""
    if tool_name in INTERNAL_TOOLS:
        return PermissionResultAllow()

    # 外部工具：拒绝并中断
    return PermissionResultDeny(
        message="External tool - returning to client",
        interrupt=True
    )
```

### 5. tool_result 处理

当客户端发送包含 tool_result 的请求：

```python
def handle_tool_result(messages: List[dict], session_id: str):
    """处理 tool_result，注入到 session 继续对话。"""
    # 提取 tool_result
    new_messages = extract_new_messages(messages)[1]

    for msg in new_messages:
        if msg["role"] == "user" and isinstance(msg["content"], list):
            for block in msg["content"]:
                if block.get("type") == "tool_result":
                    tool_use_id = block["tool_use_id"]
                    content = block.get("content", "")
                    is_error = block.get("is_error", False)

                    # 注入到 SDK session
                    # 使用 UserMessage 的 tool_use_result 字段
                    ...
```

---

## 数据结构

### SessionManager 扩展

```python
@dataclass
class Session:
    id: str
    created_at: datetime
    last_active: datetime
    messages: List[dict]
    # 新增
    pending_tool_uses: List[ToolUseInfo] = field(default_factory=list)

class SessionManager:
    sessions: Dict[str, Session]
    hash_to_session: Dict[str, str]  # 新增：content_hash → session_id

    def store_hash_mapping(self, messages: List[dict], session_id: str):
        """存储 hash → session 映射。"""
        hash_value = compute_session_hash(messages)
        if hash_value:
            self.hash_to_session[hash_value] = session_id

    def find_session_by_hash(self, messages: List[dict]) -> Optional[str]:
        """通过消息 hash 查找 session。"""
        hash_value = compute_session_hash(messages)
        if hash_value:
            return self.hash_to_session.get(hash_value)
        return None
```

### ToolUseInfo

```python
@dataclass
class ToolUseInfo:
    id: str           # "toolu_01abc..."
    name: str         # "get_weather"
    input: dict       # {"city": "Paris"}
```

---

## API 响应格式

### 正常结束

```json
{
  "id": "msg_xxx",
  "type": "message",
  "role": "assistant",
  "content": [{"type": "text", "text": "..."}],
  "model": "claude-code-opus",
  "stop_reason": "end_turn",
  "usage": {"input_tokens": 100, "output_tokens": 50}
}
```

### 需要工具调用

```json
{
  "id": "msg_xxx",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01abc",
      "name": "get_weather",
      "input": {"city": "Paris"}
    }
  ],
  "model": "claude-code-opus",
  "stop_reason": "tool_use",
  "usage": {"input_tokens": 100, "output_tokens": 30}
}
```

---

## 实现阶段

### 阶段 1：Session Hash 识别

1. 实现 `compute_session_hash()` 函数
2. 扩展 `SessionManager` 添加 `hash_to_session` 映射
3. 在响应时存储 hash 映射
4. 在请求时通过 hash 查找 session
5. 实现 `extract_new_messages()` 提取新消息
6. 测试多轮对话的 session 恢复

### 阶段 2：外部工具基础支持

1. 定义 `INTERNAL_TOOLS` 列表
2. 实现 `classify_tools()` 分类函数
3. 支持 `tools` 参数解析
4. 实现 `create_external_tools_server()` 动态创建 MCP
5. 测试工具分类逻辑

### 阶段 3：工具调用拦截

1. 实现 `can_use_tool_callback()` 拦截外部工具
2. 捕获 `ToolUseBlock` 信息
3. 返回 `stop_reason: "tool_use"` 响应
4. 测试外部工具调用中断

### 阶段 4：tool_result 处理

1. 检测 messages 中的 tool_result
2. 通过 hash 恢复 session
3. 注入 tool_result 到 SDK
4. 继续对话并返回结果
5. 端到端测试完整流程

### 阶段 5：测试与文档

1. 单元测试各组件
2. 集成测试完整流程
3. 更新 API 文档
4. 更新 README

---

## 兼容性

| 特性 | 标准 Anthropic API | 本 Wrapper |
|------|-------------------|------------|
| messages 格式 | ✅ | ✅ 完全兼容 |
| tools 参数 | ✅ | ✅ 支持 |
| tool_choice | ✅ | ⚠️ 后续支持 |
| stop_reason: tool_use | ✅ | ✅ 支持 |
| tool_result 处理 | ✅ | ✅ 透明恢复 |
| 内置工具 | ❌ | ✅ 额外能力 |

**客户端完全无感知** - 使用标准 Anthropic SDK 即可。

---

## 注意事项

1. **Hash 映射 TTL** - 与 session TTL 同步，避免内存泄漏
2. **并发安全** - hash_to_session 需要线程安全
3. **错误处理** - tool 执行失败时的优雅降级
4. **流式响应** - tool_use 在流式中的处理
