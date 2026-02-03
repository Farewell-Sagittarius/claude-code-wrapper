# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Anthropic Messages API wrapper for Claude Agent SDK. OpenAI compatibility is provided externally via LiteLLM.

## Architecture

```
┌─────────────────────────┐
│   Docker (LiteLLM)      │
│   Port 8080 → external  │
│   host.docker.internal:8790
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Host (Wrapper)        │
│   Port 8790             │
│   - Anthropic API only  │
│   - /v1/messages        │
│   - /v1/sessions        │
└─────────────────────────┘
```

## Commands

```bash
# Run wrapper (host)
python -m src.main
uvicorn src.main:app --host 0.0.0.0 --port 8790 --reload

# Run LiteLLM (Docker)
docker-compose up -d

# Run all tests
pytest

# Skip integration tests
pytest -m "not integration"

# Skip MCP tests
pytest -m "not mcp"
```

## Request Flow

1. Client sends request with `Authorization: Bearer sk-{level}-*` header
2. `middleware/auth.py` verifies key and determines tool mode
3. `routes/anthropic.py` receives request
4. `adapters/anthropic_adapter.py` converts to internal format
5. `services/claude.py` builds ClaudeAgentOptions and calls SDK
6. `services/session.py` manages conversation state

## API Key Permission Levels

| Level | Prefix | Tools | MCP |
|-------|--------|-------|-----|
| light | sk-light-* | None | No |
| basic | sk-basic-* | Built-in | No |
| heavy | sk-heavy-* | All + plugins | Yes |
| custom | sk-custom-* | Per-request | Conditional |

## Model Aliases

- `claude-code-opus` → `claude-opus-4-5-20251101`
- `claude-code-sonnet` → `claude-sonnet-4-5-20250929`
- `claude-code-haiku` → `claude-haiku-4-5-20251001`

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | FastAPI app setup, routing, lifecycle |
| `src/config.py` | Settings, API keys, model mapping |
| `src/services/claude.py` | Claude SDK wrapper, tool/MCP config |
| `src/services/session.py` | Session storage with 1-hour TTL |
| `src/middleware/auth.py` | API key verification, tool mode |
| `src/adapters/anthropic_adapter.py` | Anthropic format conversion |
| `litellm-config.yaml` | LiteLLM model mapping and passthrough |
| `docker-compose.yml` | LiteLLM container configuration |

## Test Markers

- `@pytest.mark.integration` - Requires running Claude instance
- `@pytest.mark.mcp` - Requires MCP server interaction
