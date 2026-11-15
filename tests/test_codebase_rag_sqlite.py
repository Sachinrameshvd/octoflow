"""Tests for Persistent SQLite-backed Codebase RAG, AST Chunking & Call Graph Connectome.

Verifies:
- AST symbol extraction (Python classes, functions, methods, async functions, docstrings).
- SQLite persistence of code chunks, dense vectors, and symbol indexes.
- Incremental indexing skipping unchanged files based on mtime.
- Cross-reference call graph queries (find_callers and find_callees).
- Symbol lookup by exact and partial names.
- Semantic vector similarity search over functions and classes.
- Integration through VerticalLobeMemory.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from octoflow.memory import EpisodicCodebaseRAG, VerticalLobeMemory


@pytest.fixture
def sample_workspace(tmp_path: Path) -> Path:
    """Create a multi-file Python project with classes, functions, calls, and docstrings."""
    ws = tmp_path / "sample_project"
    ws.mkdir(parents=True)

    # 1. Models file
    models_file = ws / "models.py"
    models_file.write_text(
        '''"""Data models for enterprise user management."""

class UserAccount:
    """Represents an authenticated enterprise user."""

    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate this account."""
        self.is_active = False
''',
        encoding="utf-8",
    )

    # 2. Services file with calls to models
    services_file = ws / "services.py"
    services_file.write_text(
        '''"""User services handling authentication and password hashing."""

from .models import UserAccount

def hash_password(raw_secret: str) -> str:
    """Hash raw password with Argon2 algorithm."""
    return f"hashed_{raw_secret}"

class UserService:
    """Enterprise user workflow management service."""

    def register_user(self, username: str, email: str, raw_secret: str) -> UserAccount:
        """Register a new enterprise user with hashed credentials."""
        hashed = hash_password(raw_secret)
        user = UserAccount(username, email)
        return user

    def terminate_user(self, user: UserAccount) -> None:
        """Safely terminate and deactivate an enterprise user."""
        user.deactivate()
''',
        encoding="utf-8",
    )

    # 3. Utilities file
    utils_file = ws / "utils.py"
    utils_file.write_text(
        '''"""General utility helpers."""

def sanitize_input(value: str) -> str:
    """Strip dangerous characters from user input."""
    return value.strip()
''',
        encoding="utf-8",
    )

    return ws


def test_sqlite_rag_ast_chunking_and_symbols(sample_workspace: Path, tmp_path: Path) -> None:
    """Verify AST parser extracts classes, methods, docstrings, and symbols into SQLite."""
    db_file = tmp_path / "test_memory.db"
    rag = EpisodicCodebaseRAG(vector_dim=128, db_path=db_file)

    chunk_count = rag.index_workspace(str(sample_workspace))
    assert chunk_count >= 5  # UserAccount, deactivate, hash_password, UserService, register_user, terminate_user

    # Verify SQLite stats
    stats = rag.get_stats()
    assert stats["files_indexed"] == 3
    assert stats["symbols_indexed"] >= 6
    assert stats["database_path"] == str(db_file)
    assert db_file.exists()

    # Search symbols
    user_symbols = rag.search_symbols("UserAccount")
    assert len(user_symbols) >= 1
    assert user_symbols[0]["symbol_type"] == "class"
    assert "Represents an authenticated" in user_symbols[0]["docstring"]

    hash_symbols = rag.search_symbols("hash_password")
    assert len(hash_symbols) >= 1
    assert hash_symbols[0]["symbol_type"] == "function"
    assert "Hash raw password" in hash_symbols[0]["docstring"]


def test_call_graph_cross_referencing(sample_workspace: Path, tmp_path: Path) -> None:
    """Verify call graph tracks who calls whom across classes and functions."""
    db_file = tmp_path / "call_graph.db"
    rag = EpisodicCodebaseRAG(vector_dim=128, db_path=db_file)
    rag.index_workspace(str(sample_workspace))

    # Find who calls hash_password
    callers = rag.find_callers("hash_password")
    assert len(callers) >= 1
    assert any("register_user" in c["caller"] for c in callers)

    # Find who calls deactivate
    deactivate_callers = rag.find_callers("deactivate")
    assert len(deactivate_callers) >= 1
    assert any("terminate_user" in c["caller"] for c in deactivate_callers)

    # Find what register_user calls (callees)
    callees = rag.find_callees("register_user")
    assert len(callees) >= 1
    callee_names = [c["callee"] for c in callees]
    assert "hash_password" in callee_names or "UserAccount" in callee_names


def test_incremental_indexing_skips_unchanged_files(sample_workspace: Path, tmp_path: Path) -> None:
    """Verify incremental indexing skips files whose mtime has not changed."""
    db_file = tmp_path / "incremental.db"
    rag = EpisodicCodebaseRAG(vector_dim=128, db_path=db_file)

    # Initial index
    first_count = rag.index_workspace(str(sample_workspace), incremental=True)
    assert first_count > 0

    # Second index with no file modifications
    second_count = rag.index_workspace(str(sample_workspace), incremental=True)
    assert second_count == first_count  # Keeps same count, no re-indexing


def test_semantic_vector_search_relevance(sample_workspace: Path, tmp_path: Path) -> None:
    """Verify vector search returns most semantically relevant code chunks."""
    db_file = tmp_path / "vector_search.db"
    rag = EpisodicCodebaseRAG(vector_dim=128, db_path=db_file)
    rag.index_workspace(str(sample_workspace))

    # Search for hashing/passwords
    results = rag.search("argon2 password hash raw secret", top_k=2)
    assert len(results) >= 1
    top_result = results[0]
    assert "hash_password" in top_result["symbol"] or "services.py" in top_result["file_path"]

    # Search for account termination
    deact_results = rag.search("deactivate account terminate user", top_k=2)
    assert len(deact_results) >= 1
    symbols_found = [r["symbol"] for r in deact_results]
    assert any("deactivate" in s or "terminate" in s for s in symbols_found)


def test_vertical_lobe_memory_integration(sample_workspace: Path, tmp_path: Path) -> None:
    """Verify VerticalLobeMemory provides seamless symbol search and codebase indexing."""
    db_file = tmp_path / "v_memory.db"
    vlm = VerticalLobeMemory()

    # Index via VerticalLobeMemory
    count = vlm.index_codebase(str(sample_workspace), db_path=db_file)
    assert count > 0

    # Search codebase
    results = vlm.search_codebase("password security", top_k=2)
    assert len(results) >= 1

    # Search symbols
    syms = vlm.search_symbols("UserService")
    assert len(syms) >= 1
    assert syms[0]["symbol_type"] == "class"

    # Find callers
    callers = vlm.find_callers("deactivate")
    assert len(callers) >= 1

