"""Pytest configuration and fixtures for wrapper tests."""

import asyncio
import os
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app


# API Keys for different tool modes
API_KEYS = {
    "light": "sk-light-dev",
    "basic": "sk-basic-dev",
    "heavy": "sk-heavy-dev",
    "custom": "sk-custom-dev",
}


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Create synchronous test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def light_headers() -> dict:
    """Headers with light mode API key (no tools)."""
    return {
        "Authorization": f"Bearer {API_KEYS['light']}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }


@pytest.fixture
def basic_headers() -> dict:
    """Headers with basic mode API key (built-in tools)."""
    return {
        "Authorization": f"Bearer {API_KEYS['basic']}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }


@pytest.fixture
def heavy_headers() -> dict:
    """Headers with heavy mode API key (all tools + MCP)."""
    return {
        "Authorization": f"Bearer {API_KEYS['heavy']}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }


@pytest.fixture
def custom_headers() -> dict:
    """Headers with custom mode API key."""
    return {
        "Authorization": f"Bearer {API_KEYS['custom']}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }


@pytest.fixture
def anthropic_headers() -> dict:
    """Headers for Anthropic API format (alias for basic_headers)."""
    return {
        "Authorization": f"Bearer {API_KEYS['basic']}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
