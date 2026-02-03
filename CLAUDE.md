# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenAI-compatible API wrapper that exposes Claude Agent SDK as standard API endpoints. Supports both OpenAI Chat Completions API (`/v1/chat/completions`) and Anthropic Messages API (`/v1/messages`) formats.

## Commands

```bash
# Run server
python -m src.main
uvicorn src.main:app --host 0.0.0.0 --port 8790 --reload

# Run all tests
pytest

# Run single test file
pytest tests/test_health.py

# Run single test function
pytest tests/test_health.py::test_health_endpoint

# Skip integration tests (require running Claude)
pytest -m "not integration"

# Skip MCP tests
pytest -m "not mcp"

# With coverage
pytest --cov=src --cov-report=html
```

## Architecture

### Request Flow

1. Client sends request with `Authorization: Bearer sk-{level}-*` header
2. `middleware/auth.py` verifies key and determines tool mode (light/basic/heavy/custom)
3. Route handler (`routes/chat.py` or `routes/anthropic.py`) receives request
4. Adapter (`adapters/openai_adapter.py` or `adapters/anthropic_adapter.py`) converts to internal format
5. `services/claude.py` builds ClaudeAgentOptions and calls SDK
6. `services/session.py` manages conversation state for multi-turn support
7. Response converted back to appropriate API format

### API Key Permission Levels

| Level | Prefix | Tools | MCP |
|-------|--------|-------|-----|
| light | sk-light-* | None | No |
| basic | sk-basic-* | Built-in | No |
| heavy | sk-heavy-* | All + plugins | Yes |
| custom | sk-custom-* | Per-request | Conditional |

### Multimodal Handling

Claude Agent SDK doesn't natively support images/documents. This wrapper:
1. Caches files to `.claude_media_cache` directory
2. Includes file path reference in prompt: `[Image file: /path/to/file.png]`
3. Claude Code reads files using built-in Read tool

### Model Aliases

- `claude-code-opus` → `claude-opus-4-5-20251101`
- `claude-code-sonnet` → `claude-sonnet-4-5-20250929`
- `claude-code-haiku` → `claude-haiku-4-5-20251001`

### Extended Thinking (reasoning_effort → max_thinking_tokens)

- `none` → disabled
- `low` → 8,000
- `medium` → 16,000
- `high` → 31,999

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | FastAPI app setup, routing, lifecycle |
| `src/config.py` | Settings, API keys, model mapping |
| `src/services/claude.py` | Claude SDK wrapper, tool/MCP config |
| `src/services/session.py` | Session storage with 1-hour TTL |
| `src/middleware/auth.py` | API key verification, tool mode |
| `src/adapters/base.py` | File caching, URL fetching, token estimation |

## SDK Limitations

- `temperature`, `top_p`, `max_tokens`: Accepted but not applied
- `stop`/`stop_sequences`: Not supported
- Native tool calling format: Not supported (uses SDK's internal tools)
- JSON/structured output mode: Not supported

## Test Markers

- `@pytest.mark.integration` - Requires running Claude instance
- `@pytest.mark.mcp` - Requires MCP server interaction
