# Claude Code Wrapper

Anthropic Messages API 包装器，用于将 Claude Agent SDK 暴露为标准 API 端点。通过 LiteLLM 提供 OpenAI 格式兼容。

## 架构

```
┌─────────────────────────┐
│   Docker (LiteLLM)      │
│   Port 8080 → 外部      │
│   连接 host.docker.internal:8790
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   宿主机 (Wrapper)       │
│   Port 8790             │
│   - Anthropic API only  │
│   - /v1/messages        │
│   - /v1/sessions        │
└─────────────────────────┘
```

## 功能特性

- **Anthropic Messages API** - `/v1/messages` 原生支持
- **OpenAI 兼容** - 通过 LiteLLM 提供 `/v1/chat/completions`
- **多密钥认证** - 4 种工具权限级别（light/basic/heavy/custom）
- **会话管理** - 支持对话上下文保持
- **扩展思考** - 通过 `thinking` 参数控制思考深度
- **MCP 服务器** - 支持配置外部 MCP 服务器
- **流式响应** - 支持 SSE 流式输出

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd claude-code-wrapper

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

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
# 1. 启动 Wrapper (宿主机)
python -m src.main

# 2. 启动 LiteLLM (Docker)
docker-compose up -d
```

## API 使用

### 通过 LiteLLM (推荐)

OpenAI SDK（通过 LiteLLM 转换）：

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-basic-dev"
)

response = client.chat.completions.create(
    model="claude-code-opus",
    messages=[{"role": "user", "content": "Hello!"}],
    extra_body={"session_id": "my-session"}
)

print(response.choices[0].message.content)
```

Anthropic SDK（通过 LiteLLM 透传）：

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:8080/anthropic",
    api_key="sk-basic-dev"
)

response = client.messages.create(
    model="claude-code-opus",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
    extra_body={"session_id": "my-session"}
)

print(response.content[0].text)
```

### 直连 Wrapper

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:8790/v1",
    api_key="sk-basic-dev"
)

response = client.messages.create(
    model="claude-code-opus",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/messages` | POST | Anthropic Messages API |
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

| 级别 | 密钥前缀 | 可用工具 |
|------|----------|----------|
| `light` | `sk-light-*` | 无工具（纯对话） |
| `basic` | `sk-basic-*` | 所有内置工具 |
| `heavy` | `sk-heavy-*` | 内置工具 + 插件 + MCP |
| `custom` | `sk-custom-*` | 根据请求参数自定义 |

## 高级功能

### 会话保持

```python
response = client.messages.create(
    model="claude-code-opus",
    max_tokens=1024,
    messages=[{"role": "user", "content": "记住这个数字：42"}],
    extra_body={"session_id": "my-session-123"}
)
```

### 扩展思考

```python
response = client.messages.create(
    model="claude-code-opus",
    max_tokens=1024,
    messages=[{"role": "user", "content": "复杂问题..."}],
    thinking={"type": "enabled", "budget_tokens": 16000}
)
```

### MCP 服务器

```python
response = client.messages.create(
    model="claude-code-opus",
    max_tokens=1024,
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

## 项目结构

```
claude-code-wrapper/
├── src/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── models/              # 数据模型
│   │   ├── common.py        # 共享类型
│   │   └── anthropic/       # Anthropic API 模型
│   ├── routes/              # API 路由
│   │   ├── anthropic.py     # /v1/messages
│   │   └── sessions.py      # /v1/sessions
│   ├── services/            # 业务逻辑
│   │   ├── claude.py        # Claude Agent SDK 封装
│   │   └── session.py       # 会话管理
│   └── adapters/            # 格式转换适配器
│       ├── base.py          # 基础工具
│       └── anthropic_adapter.py
├── litellm-config.yaml      # LiteLLM 配置
├── docker-compose.yml       # LiteLLM 容器配置
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
- LiteLLM (Docker)

## License

MIT
