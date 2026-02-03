# Claude Code Wrapper

OpenAI 兼容的 API 包装器，用于将 Claude Agent SDK 暴露为标准 API 端点。支持 OpenAI Chat Completions API 和 Anthropic Messages API 格式。

## 功能特性

- **OpenAI 兼容端点** - `/v1/chat/completions`，可直接使用 OpenAI SDK
- **Anthropic 兼容端点** - `/v1/messages`，支持原生 Anthropic 格式
- **多密钥认证** - 4 种工具权限级别（light/basic/heavy/custom）
- **会话管理** - 支持对话上下文保持
- **文件处理** - 支持 OpenAI 标准的 inline 文件格式
- **扩展思考** - 通过 `reasoning_effort` 参数控制思考深度
- **MCP 服务器** - 支持配置外部 MCP 服务器
- **流式响应** - 支持 SSE 流式输出

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd claude-code-wrapper

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 配置

复制环境变量示例文件：

```bash
cp .env.example .env
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PORT` | 服务端口 | `8790` |
| `HOST` | 监听地址 | `0.0.0.0` |
| `DEBUG_MODE` | 调试模式 | `false` |
| `CLAUDE_CWD` | Claude 工作目录 | `/home/user` |
| `API_KEY_LIGHT` | 轻量级 API 密钥（无工具） | `sk-light-dev` |
| `API_KEY_BASIC` | 基础 API 密钥（内置工具） | `sk-basic-dev` |
| `API_KEY_HEAVY` | 重度 API 密钥（全部工具） | `sk-heavy-dev` |
| `API_KEY_CUSTOM` | 自定义 API 密钥 | `sk-custom-dev` |

## 启动服务

```bash
# 直接运行
python -m src.main

# 或使用 uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8790 --reload
```

## API 端点

### OpenAI 格式 - Chat Completions

```
POST /v1/chat/completions
```

使用 OpenAI SDK：

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8790/v1",
    api_key="sk-basic-dev"
)

response = client.chat.completions.create(
    model="claude-code-opus",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Anthropic 格式 - Messages

```
POST /v1/messages
```

使用 Anthropic SDK：

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:8790/v1",
    api_key="sk-basic-dev"
)

response = client.messages.create(
    model="claude-code-opus",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.content[0].text)
```

### 其他端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/models` | GET | 获取可用模型列表 |
| `/v1/sessions` | GET | 获取所有活跃会话 |
| `/v1/sessions/{id}` | GET | 获取特定会话详情 |
| `/v1/sessions/{id}` | DELETE | 删除会话 |
| `/v1/sessions/stats` | GET | 获取会话统计信息 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | Swagger API 文档 |

## 模型别名

| 别名 | 实际模型 |
|------|----------|
| `claude-code-opus` | `claude-opus-4-5-20251101` |
| `claude-code-sonnet` | `claude-sonnet-4-5-20250929` |
| `claude-code-haiku` | `claude-haiku-4-5-20251001` |

## 工具权限级别

通过不同的 API 密钥控制 Claude 可使用的工具：

| 级别 | 密钥前缀 | 可用工具 |
|------|----------|----------|
| `light` | `sk-light-*` | 无工具（纯对话） |
| `basic` | `sk-basic-*` | 所有内置工具（Task, Bash, Read, Edit, Write 等） |
| `heavy` | `sk-heavy-*` | 内置工具 + 插件 + MCP 服务器 |
| `custom` | `sk-custom-*` | 根据请求参数自定义 |

## 高级功能

### 会话保持

通过 `session_id` 参数保持对话上下文：

```python
response = client.chat.completions.create(
    model="claude-code-opus",
    messages=[{"role": "user", "content": "记住这个数字：42"}],
    extra_body={"session_id": "my-session-123"}
)

# 后续请求使用相同的 session_id
response = client.chat.completions.create(
    model="claude-code-opus",
    messages=[{"role": "user", "content": "刚才的数字是多少？"}],
    extra_body={"session_id": "my-session-123"}
)
```

### 扩展思考

使用 `reasoning_effort` 参数控制思考深度（兼容 OpenAI o1/o3）：

```python
response = client.chat.completions.create(
    model="claude-code-opus",
    messages=[{"role": "user", "content": "复杂的数学问题..."}],
    extra_body={"reasoning_effort": "high"}  # none/low/medium/high
)
```

| 级别 | 最大思考 tokens |
|------|-----------------|
| `none` | 禁用扩展思考 |
| `low` | 8,000 |
| `medium` | 16,000 |
| `high` | 31,999 |

### 文件输入

支持 OpenAI 标准的 inline 文件格式：

```python
import base64

with open("document.pdf", "rb") as f:
    file_data = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="claude-code-opus",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "分析这个文档"},
            {
                "type": "file",
                "file": {
                    "filename": "document.pdf",
                    "file_data": f"data:application/pdf;base64,{file_data}"
                }
            }
        ]
    }]
)
```

### MCP 服务器配置

在请求中配置 MCP 服务器：

```python
response = client.chat.completions.create(
    model="claude-code-opus",
    messages=[{"role": "user", "content": "使用 MCP 工具..."}],
    extra_body={
        "mcp_servers": {
            "my-server": {
                "type": "stdio",
                "command": "node",
                "args": ["server.js"]
            }
        }
    }
)
```

## Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .

EXPOSE 8790
CMD ["python", "-m", "src.main"]
```

## 项目结构

```
claude-code-wrapper/
├── src/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── models/              # 数据模型
│   │   ├── common.py        # 共享类型
│   │   ├── openai/          # OpenAI API 模型
│   │   └── anthropic/       # Anthropic API 模型
│   ├── routes/              # API 路由
│   │   ├── chat.py          # /v1/chat/completions
│   │   ├── anthropic.py     # /v1/messages
│   │   ├── models.py        # /v1/models
│   │   └── sessions.py      # /v1/sessions
│   ├── services/            # 业务逻辑
│   │   ├── claude.py        # Claude Agent SDK 封装
│   │   └── session.py       # 会话管理
│   └── adapters/            # 格式转换适配器
│       ├── base.py          # 基础工具
│       ├── openai_adapter.py
│       └── anthropic_adapter.py
├── requirements.txt
├── .env.example
└── README.md
```

## 依赖

- Python 3.10+
- FastAPI
- Uvicorn
- Claude Agent SDK
- Pydantic v2
- HTTPX

## License

MIT
