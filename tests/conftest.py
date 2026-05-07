import os
import sys

import pytest

# Ensure chatbi-application is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import impl  # noqa: F401 — triggers all @register_* decorators
from db_mcp_server.schema_rag import FIELD_DESCRIPTIONS, TABLE_DESCRIPTIONS
from config import settings


@pytest.fixture(scope="session")
def field_descriptions():
    return FIELD_DESCRIPTIONS


@pytest.fixture(scope="session")
def table_descriptions():
    return TABLE_DESCRIPTIONS


@pytest.fixture(scope="session")
def retriever_cfg():
    return settings.retriever


@pytest.fixture(scope="session")
def reranker_cfg():
    return settings.reranker


@pytest.fixture(scope="session")
def sample_queries():
    return [
        "show me last month sales for Samsung phones",
        "top 5 brands by revenue",
        "which city has the most customers",
        "average order value by shipping province",
        "count cancelled orders in Q1 2025",
    ]
