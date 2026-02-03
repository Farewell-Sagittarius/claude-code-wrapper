# Anthropic-Only 重构 + LiteLLM 集成

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 wrapper 简化为只支持 Anthropic API，使用 LiteLLM 作为统一入口提供 OpenAI 兼容性。

**Architecture:** LiteLLM (Docker) 作为前端代理，wrapper (宿主机) 只实现 Anthropic Messages API。

**Tech Stack:** Python 3.10+, FastAPI, LiteLLM, Docker

---

## 架构图

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
│   - 访问文件系统         │
└─────────────────────────┘
```

### 请求流程

| 客户端格式 | LiteLLM 处理 | Wrapper 接收 |
|-----------|-------------|-------------|
| OpenAI `/v1/chat/completions` | 转换为 Anthropic 格式 | `/v1/messages` |
| Anthropic `/anthropic/v1/messages` | 透传 | `/v1/messages` |

---

## 阶段 1：清理 OpenAI 代码

### Task 1.1: 删除 OpenAI 模型

**删除文件:**
- `src/models/openai/__init__.py`
- `src/models/openai/content.py`
- `src/models/openai/request.py`
- `src/models/openai/response.py`

**删除目录:**
```bash
rm -rf src/models/openai/
```

### Task 1.2: 删除 OpenAI 适配器

**删除文件:**
```bash
rm src/adapters/openai_adapter.py
```

### Task 1.3: 删除 OpenAI 路由

**删除文件:**
```bash
rm src/routes/chat.py
rm src/routes/models.py
```

### Task 1.4: 更新 main.py

**修改:** `src/main.py`

移除以下 router 注册:
```python
# 删除这些行
from .routes.chat import router as chat_router
from .routes.models import router as models_router
app.include_router(chat_router)
app.include_router(models_router)
```

### Task 1.5: 更新 routes/__init__.py

**修改:** `src/routes/__init__.py`

```python
"""API routes for Claude Code Wrapper."""

from .anthropic import router as anthropic_router
from .sessions import router as sessions_router

__all__ = ["anthropic_router", "sessions_router"]
```

### Task 1.6: 更新 models/__init__.py

**修改:** `src/models/__init__.py`

移除 openai 模块导出，只保留:
```python
"""Data models for Anthropic API."""

from . import anthropic
from .common import (
    McpHttpServerConfig,
    McpServerConfig,
    McpSSEServerConfig,
    McpStdioServerConfig,
    TokenUsage,
)

__all__ = [
    "anthropic",
    "McpHttpServerConfig",
    "McpServerConfig",
    "McpSSEServerConfig",
    "McpStdioServerConfig",
    "TokenUsage",
]
```

### Task 1.7: 更新 adapters/__init__.py

**修改:** `src/adapters/__init__.py`

```python
"""Adapters for format conversion."""

from .anthropic_adapter import AnthropicAdapter
from .base import FileCache, estimate_tokens, fetch_url, guess_mime_type, parse_data_url

__all__ = [
    "AnthropicAdapter",
    "FileCache",
    "estimate_tokens",
    "fetch_url",
    "guess_mime_type",
    "parse_data_url",
]
```

### Task 1.8: 验证代码清理

```bash
python -c "from src.main import app; print('OK')"
```

### Task 1.9: Commit 阶段 1

```bash
git add -A
git commit -m "refactor: remove OpenAI API support, keep Anthropic only"
```

---

## 阶段 2：清理测试

### Task 2.1: 删除 OpenAI 测试文件

```bash
rm tests/test_chat_completions.py
rm tests/test_openai_spec.py
```

### Task 2.2: 更新 conftest.py

**修改:** `tests/conftest.py`

移除 OpenAI 相关 fixtures:
- `simple_chat_request`
- `streaming_chat_request`

保留 Anthropic 相关 fixtures:
- `simple_anthropic_request`
- `anthropic_headers`
- API key fixtures
- Client fixtures

### Task 2.3: 更新 test_multimodal.py

**修改:** `tests/test_multimodal.py`

移除所有 OpenAI 格式的测试用例，只保留 Anthropic 格式测试。

### Task 2.4: 运行测试验证

```bash
pytest -v
```

### Task 2.5: Commit 阶段 2

```bash
git add -A
git commit -m "test: remove OpenAI tests, keep Anthropic only"
```

---

## 阶段 3：配置 LiteLLM

### Task 3.1: 创建 litellm-config.yaml

**创建:** `litellm-config.yaml`

```yaml
model_list:
  - model_name: claude-code-opus
    litellm_params:
      model: anthropic/claude-code-opus
      api_base: http://host.docker.internal:8790/v1

  - model_name: claude-code-sonnet
    litellm_params:
      model: anthropic/claude-code-sonnet
      api_base: http://host.docker.internal:8790/v1

  - model_name: claude-code-haiku
    litellm_params:
      model: anthropic/claude-code-haiku
      api_base: http://host.docker.internal:8790/v1

litellm_settings:
  drop_params: false
  allowed_openai_params:
    - session_id
    - mcp_servers
    - allowed_tools
    - disallowed_tools
    - max_turns

general_settings:
  pass_through_endpoints:
    - path: "/anthropic/v1/messages"
      target: "http://host.docker.internal:8790/v1/messages"
      headers:
        - "authorization"
        - "anthropic-version"
```

### Task 3.2: 创建 docker-compose.yml

**创建:** `docker-compose.yml`

```yaml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "8080:4000"
    volumes:
      - ./litellm-config.yaml:/app/config.yaml
    command: ["--config", "/app/config.yaml"]
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
```

### Task 3.3: 测试 LiteLLM 集成

1. 启动 wrapper: `python -m src.main`
2. 启动 LiteLLM: `docker-compose up -d`
3. 测试 OpenAI 格式:
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-basic-dev" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-code-opus", "messages": [{"role": "user", "content": "Hello"}]}'
```
4. 测试 Anthropic 透传:
```bash
curl http://localhost:8080/anthropic/v1/messages \
  -H "Authorization: Bearer sk-basic-dev" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model": "claude-code-opus", "max_tokens": 100, "messages": [{"role": "user", "content": "Hello"}]}'
```

### Task 3.4: Commit 阶段 3

```bash
git add -A
git commit -m "feat: add LiteLLM configuration for OpenAI compatibility"
```

---

## 阶段 4：更新文档

### Task 4.1: 更新 CLAUDE.md

更新架构说明，反映新的 LiteLLM + Anthropic-only 架构。

### Task 4.2: 更新 README.md

更新部署说明和使用方式:
- 移除 OpenAI 端点说明
- 添加 LiteLLM 部署说明
- 更新客户端使用示例

### Task 4.3: 删除过时计划文档

```bash
rm docs/plans/2026-02-03-separate-openai-anthropic-models.md
```

### Task 4.4: Commit 阶段 4

```bash
git add -A
git commit -m "docs: update documentation for Anthropic-only architecture"
```

---

## 完成检查清单

- [ ] 删除 `src/models/openai/`
- [ ] 删除 `src/adapters/openai_adapter.py`
- [ ] 删除 `src/routes/chat.py`
- [ ] 删除 `src/routes/models.py`
- [ ] 更新 `src/main.py`
- [ ] 更新 `src/routes/__init__.py`
- [ ] 更新 `src/models/__init__.py`
- [ ] 更新 `src/adapters/__init__.py`
- [ ] 删除 `tests/test_chat_completions.py`
- [ ] 删除 `tests/test_openai_spec.py`
- [ ] 更新 `tests/conftest.py`
- [ ] 更新 `tests/test_multimodal.py`
- [ ] 创建 `litellm-config.yaml`
- [ ] 创建 `docker-compose.yml`
- [ ] 测试 LiteLLM 集成
- [ ] 更新 `CLAUDE.md`
- [ ] 更新 `README.md`
- [ ] 删除过时计划文档
- [ ] 所有测试通过
