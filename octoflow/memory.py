"""Vertical Lobe Hebbian Associative Memory for Instant Bug/Fix Pattern Recall.

Inspired by the cephalopod Vertical Lobe presynaptic Long-Term Potentiation (LTP)
circuit. Associates sensory error signatures with verified resolution policies,
enabling sub-millisecond retrieval without expensive vector database RAG lookups.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


class FixPattern:
    """A cached resolution pattern learned via Vertical Lobe LTP."""

    def __init__(self, signature_vector: np.ndarray, error_name: str, fix_guidance: str):
        self.signature = signature_vector / (np.linalg.norm(signature_vector) + 1e-8)
        self.error_name = error_name
        self.fix_guidance = fix_guidance
        self.reinforcement_count = 1


class VerticalLobeMemory:
    """Associative presynaptic memory using Hebbian-style pattern consolidation."""

    def __init__(
        self,
        feature_dim: int = 16,
        recall_threshold: float = 0.75,
        db_path: str = ":memory:",
    ):
        self.feature_dim = feature_dim
        self.recall_threshold = recall_threshold
        self.max_weight: float = 5.0
        self.decay_rate: float = 0.05
        self.W = np.zeros((feature_dim, feature_dim), dtype=np.float32)
        self.patterns: list[FixPattern] = []
        self._seed_common_patterns()
        self.rag = EpisodicCodebaseRAG(db_path=db_path)

    def _seed_common_patterns(self) -> None:
        """Seed biophysical memory with common software/ML debugging heuristics."""
        # Pattern 1: Syntax / Indentation Error
        v1 = np.zeros(self.feature_dim, dtype=np.float32)
        v1[6] = 1.0  # Syntax error flag
        self.patterns.append(
            FixPattern(
                v1,
                "SyntaxError / ParseError",
                "Check for missing colons, mismatched brackets, or Python indentation inconsistencies.",
            )
        )

        # Pattern 2: CUDA / Memory OOM
        v2 = np.zeros(self.feature_dim, dtype=np.float32)
        v2[7] = 1.0  # OOM flag
        self.patterns.append(
            FixPattern(
                v2,
                "CUDA OutOfMemory",
                "Reduce batch size by 50%, enable torch.amp.autocast, or call torch.cuda.empty_cache().",
            )
        )

        # Pattern 3: Missing Module / File
        v3 = np.zeros(self.feature_dim, dtype=np.float32)
        v3[9] = 1.0  # Missing file flag
        self.patterns.append(
            FixPattern(
                v3,
                "ModuleNotFoundError / FileNotFoundError",
                "Verify import paths, check working directory structure, or add package to requirements.",
            )
        )

        # Pattern 4: Type / Schema Validation Error
        v4 = np.zeros(self.feature_dim, dtype=np.float32)
        v4[10] = 1.0  # Type error flag
        self.patterns.append(
            FixPattern(
                v4,
                "TypeError / SchemaValidationError",
                "Check Pydantic field types, ensure JSON response matches expected schema, or add cast.",
            )
        )

    def recall(self, sensory_obs: np.ndarray) -> tuple[str, float] | None:
        """Query memory with current error signature. Returns (guidance, confidence) if matched."""
        if np.isnan(sensory_obs).any() or np.isinf(sensory_obs).any():
            return None
        norm = np.linalg.norm(sensory_obs)
        if norm < 1e-8:
            return None
        query = sensory_obs / norm

        best_score = -1.0
        best_pattern: FixPattern | None = None

        for p in self.patterns:
            similarity = float(np.dot(query, p.signature))
            if similarity > best_score:
                best_score = similarity
                best_pattern = p

        if best_pattern is not None and best_score >= self.recall_threshold:
            return best_pattern.fix_guidance, best_score

        return None

    def consolidate(self, error_obs: np.ndarray, error_name: str, fix_guidance: str) -> None:
        """Apply Hebbian LTP consolidation to associate the error signature with the fix."""
        if np.isnan(error_obs).any() or np.isinf(error_obs).any():
            return
        norm = np.linalg.norm(error_obs)
        if norm < 1e-8:
            return
        signature = error_obs / norm

        # Update and clip Hebbian weight matrix (dW = eta * outer(signature, signature))
        dW = np.outer(signature, signature).astype(np.float32)
        self.W = np.clip(self.W + 0.1 * dW, -self.max_weight, self.max_weight)

        # Check if similar pattern exists to reinforce
        for p in self.patterns:
            if float(np.dot(signature, p.signature)) > 0.85:
                p.reinforcement_count += 1
                p.fix_guidance = fix_guidance
                return

        # Create new associative pattern
        self.patterns.append(FixPattern(signature, error_name, fix_guidance))

    def apply_decay(self, decay_rate: float | None = None) -> None:
        """Apply biological synaptic decay (LTD) to prevent runaway potentiation."""
        rate = float(decay_rate if decay_rate is not None else self.decay_rate)
        rate = max(0.0, min(1.0, rate))
        self.W = np.clip(self.W * (1.0 - rate), -self.max_weight, self.max_weight)
        for p in self.patterns:
            p.reinforcement_count = max(1, int(p.reinforcement_count * (1.0 - rate)))

    def save(self, filepath: str) -> None:
        """Persist learned Hebbian patterns and synaptic weights to disk."""
        import json
        from pathlib import Path

        p = Path(filepath).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "feature_dim": self.feature_dim,
            "recall_threshold": self.recall_threshold,
            "max_weight": self.max_weight,
            "decay_rate": self.decay_rate,
            "W": self.W.tolist(),
            "patterns": [
                {
                    "signature": pat.signature.tolist(),
                    "error_name": pat.error_name,
                    "fix_guidance": pat.fix_guidance,
                    "reinforcement_count": pat.reinforcement_count,
                }
                for pat in self.patterns
            ],
        }
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, filepath: str) -> bool:
        """Load persisted Hebbian patterns from disk."""
        import json
        from pathlib import Path

        p = Path(filepath).expanduser().resolve()
        if not p.exists():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            self.feature_dim = data.get("feature_dim", self.feature_dim)
            self.recall_threshold = data.get("recall_threshold", self.recall_threshold)
            self.max_weight = data.get("max_weight", 5.0)
            self.decay_rate = data.get("decay_rate", 0.05)
            if "W" in data:
                self.W = np.array(data["W"], dtype=np.float32)
            else:
                self.W = np.zeros((self.feature_dim, self.feature_dim), dtype=np.float32)

            self.patterns = []
            for item in data.get("patterns", []):
                pat = FixPattern(
                    signature_vector=np.array(item["signature"], dtype=np.float32),
                    error_name=item["error_name"],
                    fix_guidance=item["fix_guidance"],
                )
                pat.reinforcement_count = item.get("reinforcement_count", 1)
                self.patterns.append(pat)
            return True
        except Exception:
            return False

    def index_codebase(self, workspace_dir: str, db_path: str | Path | None = None) -> int:
        """Index the workspace codebase into episodic semantic vector memory."""
        if not hasattr(self, "rag") or self.rag is None:
            self.rag = EpisodicCodebaseRAG(db_path=db_path)
        return self.rag.index_workspace(workspace_dir)

    def index_workspace(self, workspace_dir: str, incremental: bool = True) -> int:
        """Scan and index all workspace source files into SQLite-backed semantic chunks."""
        if not hasattr(self, "rag") or self.rag is None:
            self.rag = EpisodicCodebaseRAG()
        return self.rag.index_workspace(workspace_dir, incremental=incremental)

    def search_codebase(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        """Search the codebase for semantically relevant symbols, functions, or snippets."""
        if not hasattr(self, "rag") or self.rag is None:
            self.rag = EpisodicCodebaseRAG()
        return self.rag.search(query, top_k=top_k)

    def search_symbols(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Search indexed codebase for exact or partial symbol names (classes, functions)."""
        if not hasattr(self, "rag") or self.rag is None:
            self.rag = EpisodicCodebaseRAG()
        return self.rag.search_symbols(query, top_k=top_k)

    def find_callers(self, symbol_name: str) -> list[dict[str, Any]]:
        """Find functions or methods that invoke the specified symbol."""
        if not hasattr(self, "rag") or self.rag is None:
            self.rag = EpisodicCodebaseRAG()
        return self.rag.find_callers(symbol_name)

    def find_callees(self, symbol_name: str) -> list[dict[str, Any]]:
        """Find functions or methods invoked by the specified symbol."""
        if not hasattr(self, "rag") or self.rag is None:
            self.rag = EpisodicCodebaseRAG()
        return self.rag.find_callees(symbol_name)


class CodeChunk:
    """A semantic code chunk stored in the episodic codebase connectome."""

    def __init__(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        content: str,
        symbol: str = "",
        vector: np.ndarray | None = None,
        symbol_type: str = "",
        docstring: str = "",
    ):
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.symbol = symbol
        self.vector = vector
        self.symbol_type = symbol_type
        self.docstring = docstring


class EpisodicCodebaseRAG:
    """Persistent SQLite-backed semantic vector RAG & AST connectome over the codebase.

    Provides:
    - AST-aware symbol chunking (Python classes, functions, async functions, docstrings).
    - Lightweight subword character n-gram dense embeddings (zero heavy external dependencies).
    - Persistent SQLite database (~/.octoflow/memory/<repo_hash>.db or :memory:) for instant cross-session recall.
    - Bidirectional call graph analysis (who calls whom, which symbols invoke which dependencies).
    - Incremental indexing skipping unchanged files based on filesystem mtime.
    """

    SUPPORTED_EXTS = {
        ".py",
        ".ts",
        ".js",
        ".tsx",
        ".jsx",
        ".rs",
        ".go",
        ".json",
        ".html",
        ".css",
        ".md",
        ".toml",
        ".yaml",
        ".yml",
        ".sql",
        ".sh",
    }

    IGNORE_DIRS = {
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
        "dist",
        "build",
        ".pytest_cache",
        ".next",
        "target",
        "vendor",
    }

    def __init__(
        self,
        vector_dim: int = 128,
        db_path: str | Path | None = None,
    ):
        self.vector_dim = vector_dim
        self.db_path = str(db_path) if db_path is not None else ":memory:"
        self.chunks: list[CodeChunk] = []
        self._matrix: np.ndarray | None = None
        self._conn: Any | None = None
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize SQLite tables for persistent semantic code indexing and call graphs."""
        import sqlite3

        if self.db_path != ":memory:":
            p = Path(self.db_path).expanduser().resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(p), check_same_thread=False)
        else:
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)

        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS files_meta (
                    file_path TEXT PRIMARY KEY,
                    mtime REAL NOT NULL,
                    chunk_count INTEGER NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    symbol TEXT,
                    symbol_type TEXT,
                    content TEXT NOT NULL,
                    docstring TEXT,
                    vector BLOB
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    symbol_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    docstring TEXT
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS call_graph (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caller TEXT NOT NULL,
                    callee TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(file_path)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_call_caller ON call_graph(caller)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_call_callee ON call_graph(callee)"
            )

    def _compute_vector(self, text: str) -> np.ndarray:
        """Compute a normalized subword character n-gram hash vector."""
        import re

        vec = np.zeros(self.vector_dim, dtype=np.float32)
        tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        for tok in tokens:
            idx = abs(hash(tok)) % self.vector_dim
            vec[idx] += 1.0
            if len(tok) >= 3:
                for i in range(len(tok) - 2):
                    ng = tok[i : i + 3]
                    vec[abs(hash(ng)) % self.vector_dim] += 0.5
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec /= norm
        return vec

    def _extract_python_ast(
        self, content: str, rel_path: str, lines: list[str]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Parse Python source into AST chunks, symbol definitions, and caller edges."""
        import ast

        chunks: list[dict[str, Any]] = []
        symbols: list[dict[str, Any]] = []
        calls: list[dict[str, Any]] = []

        try:
            tree = ast.parse(content)
        except Exception:
            # Fall back to line windows if file has syntax errors
            return self._extract_generic_chunks(rel_path, lines)

        class Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.current_scope = ""

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                start_l = node.lineno
                end_l = getattr(node, "end_lineno", node.lineno + len(node.body))
                chunk_text = "\n".join(lines[start_l - 1 : end_l])
                doc = ast.get_docstring(node) or ""
                symbols.append(
                    {
                        "name": node.name,
                        "symbol_type": "class",
                        "file_path": rel_path,
                        "start_line": start_l,
                        "end_line": end_l,
                        "docstring": doc,
                    }
                )
                chunks.append(
                    {
                        "file_path": rel_path,
                        "start_line": start_l,
                        "end_line": end_l,
                        "symbol": node.name,
                        "symbol_type": "class",
                        "content": chunk_text,
                        "docstring": doc,
                    }
                )
                old_scope = self.current_scope
                self.current_scope = node.name
                self.generic_visit(node)
                self.current_scope = old_scope

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._record_func(node, "function")

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._record_func(node, "async_function")

            def _record_func(
                self, node: ast.FunctionDef | ast.AsyncFunctionDef, ftype: str
            ) -> None:
                start_l = node.lineno
                end_l = getattr(node, "end_lineno", node.lineno + len(node.body))
                chunk_text = "\n".join(lines[start_l - 1 : end_l])
                doc = ast.get_docstring(node) or ""
                scoped_name = (
                    f"{self.current_scope}.{node.name}"
                    if self.current_scope
                    else node.name
                )
                stype = "method" if self.current_scope else ftype
                symbols.append(
                    {
                        "name": scoped_name,
                        "symbol_type": stype,
                        "file_path": rel_path,
                        "start_line": start_l,
                        "end_line": end_l,
                        "docstring": doc,
                    }
                )
                chunks.append(
                    {
                        "file_path": rel_path,
                        "start_line": start_l,
                        "end_line": end_l,
                        "symbol": scoped_name,
                        "symbol_type": stype,
                        "content": chunk_text,
                        "docstring": doc,
                    }
                )
                old_scope = self.current_scope
                self.current_scope = scoped_name
                self.generic_visit(node)
                self.current_scope = old_scope

            def visit_Call(self, node: ast.Call) -> None:
                callee = ""
                if isinstance(node.func, ast.Name):
                    callee = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    callee = node.func.attr
                if callee and self.current_scope:
                    calls.append(
                        {
                            "caller": self.current_scope,
                            "callee": callee,
                            "file_path": rel_path,
                            "line_number": getattr(node, "lineno", 0),
                        }
                    )
                self.generic_visit(node)

        visitor = Visitor()
        visitor.visit(tree)

        # If no AST symbols found (e.g. flat script), fall back to sliding windows
        if not chunks:
            return self._extract_generic_chunks(rel_path, lines)

        return chunks, symbols, calls

    def _extract_generic_chunks(
        self, rel_path: str, lines: list[str]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Generic sliding window chunker with regex symbol boundary detection."""
        chunks: list[dict[str, Any]] = []
        symbols: list[dict[str, Any]] = []
        calls: list[dict[str, Any]] = []

        chunk_size = 35
        step = 25
        for i in range(0, len(lines), step):
            chunk_lines = lines[i : i + chunk_size]
            chunk_text = "\n".join(chunk_lines)
            if not chunk_text.strip():
                continue

            symbol = ""
            symbol_type = "snippet"
            for line in chunk_lines:
                clean_l = line.strip()
                if (
                    clean_l.startswith("def ")
                    or clean_l.startswith("class ")
                    or clean_l.startswith("function ")
                    or clean_l.startswith("export ")
                    or clean_l.startswith("fn ")
                    or clean_l.startswith("func ")
                ):
                    raw_name = (
                        clean_l.split("(")[0]
                        .replace("def ", "")
                        .replace("class ", "")
                        .replace("function ", "")
                        .replace("export ", "")
                        .replace("fn ", "")
                        .replace("func ", "")
                        .strip()
                    )
                    symbol = raw_name
                    symbol_type = "symbol"
                    break

            chunks.append(
                {
                    "file_path": rel_path,
                    "start_line": i + 1,
                    "end_line": min(len(lines), i + chunk_size),
                    "symbol": symbol,
                    "symbol_type": symbol_type,
                    "content": chunk_text,
                    "docstring": "",
                }
            )
            if symbol:
                symbols.append(
                    {
                        "name": symbol,
                        "symbol_type": symbol_type,
                        "file_path": rel_path,
                        "start_line": i + 1,
                        "end_line": min(len(lines), i + chunk_size),
                        "docstring": "",
                    }
                )

        return chunks, symbols, calls

    def index_workspace(self, workspace_dir: str, incremental: bool = True) -> int:
        """Scan and index all workspace source files into SQLite-backed semantic chunks."""
        ws = Path(workspace_dir).resolve()
        if not ws.exists():
            return 0

        self.chunks = []
        cur = self._conn.cursor()

        # Load indexed file mtime cache if incremental
        existing_mtimes: dict[str, float] = {}
        if incremental:
            for row in cur.execute("SELECT file_path, mtime FROM files_meta"):
                existing_mtimes[row[0]] = float(row[1])

        files_to_index: list[tuple[Path, str, float]] = []
        for file_path in ws.rglob("*"):
            if file_path.is_dir():
                continue
            if any(
                part.startswith(".")
                or "venv" in part.lower()
                or part in self.IGNORE_DIRS
                for part in file_path.parts[:-1]
            ):
                continue
            if file_path.suffix.lower() not in self.SUPPORTED_EXTS:
                continue

            try:
                mtime = file_path.stat().st_mtime
                rel_path = str(file_path.relative_to(ws))
                if incremental and rel_path in existing_mtimes and existing_mtimes[rel_path] >= mtime:
                    continue  # Unchanged file, skip re-indexing
                files_to_index.append((file_path, rel_path, mtime))
            except Exception:
                continue

        # Process changed/new files
        for fpath, rel_p, mtime in files_to_index:
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                if not lines:
                    continue

                if fpath.suffix.lower() == ".py":
                    c_list, s_list, call_list = self._extract_python_ast(content, rel_p, lines)
                else:
                    c_list, s_list, call_list = self._extract_generic_chunks(rel_p, lines)

                # Remove previous entries for this file
                cur.execute("DELETE FROM chunks WHERE file_path = ?", (rel_p,))
                cur.execute("DELETE FROM symbols WHERE file_path = ?", (rel_p,))
                cur.execute("DELETE FROM call_graph WHERE file_path = ?", (rel_p,))

                # Insert chunks
                for item in c_list:
                    vec = self._compute_vector(f"{rel_p} {item['symbol']}\n{item['content']}")
                    cur.execute(
                        """
                        INSERT INTO chunks (file_path, start_line, end_line, symbol, symbol_type, content, docstring, vector)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rel_p,
                            item["start_line"],
                            item["end_line"],
                            item["symbol"],
                            item["symbol_type"],
                            item["content"],
                            item["docstring"],
                            vec.astype(np.float32).tobytes(),
                        ),
                    )

                # Insert symbols
                for sym in s_list:
                    cur.execute(
                        """
                        INSERT INTO symbols (name, symbol_type, file_path, start_line, end_line, docstring)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sym["name"],
                            sym["symbol_type"],
                            rel_p,
                            sym["start_line"],
                            sym["end_line"],
                            sym["docstring"],
                        ),
                    )

                # Insert call graph edges
                for cl in call_list:
                    cur.execute(
                        """
                        INSERT INTO call_graph (caller, callee, file_path, line_number)
                        VALUES (?, ?, ?, ?)
                        """,
                        (cl["caller"], cl["callee"], rel_p, cl["line_number"]),
                    )

                # Update files_meta
                cur.execute(
                    """
                    INSERT INTO files_meta (file_path, mtime, chunk_count)
                    VALUES (?, ?, ?)
                    ON CONFLICT(file_path) DO UPDATE SET mtime = excluded.mtime, chunk_count = excluded.chunk_count
                    """,
                    (rel_p, mtime, len(c_list)),
                )

            except Exception:
                continue

        self._conn.commit()

        # Reconstruct in-memory active matrix from SQLite
        self._sync_in_memory_chunks()
        return len(self.chunks)

    def _sync_in_memory_chunks(self) -> None:
        """Synchronize in-memory CodeChunk list and NumPy matrix from SQLite database."""
        cur = self._conn.cursor()
        self.chunks = []
        vecs: list[np.ndarray] = []

        for row in cur.execute(
            "SELECT file_path, start_line, end_line, content, symbol, symbol_type, docstring, vector FROM chunks"
        ):
            blob = row[7]
            vec = (
                np.frombuffer(blob, dtype=np.float32).copy()
                if blob is not None
                else None
            )
            chunk = CodeChunk(
                file_path=row[0],
                start_line=row[1],
                end_line=row[2],
                content=row[3],
                symbol=row[4] or "",
                vector=vec,
                symbol_type=row[5] or "",
                docstring=row[6] or "",
            )
            self.chunks.append(chunk)
            if vec is not None and len(vec) == self.vector_dim:
                vecs.append(vec)

        if vecs:
            self._matrix = np.vstack(vecs)
        else:
            self._matrix = None

    def search(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        """Search code chunks matching query with cosine similarity."""
        if not self.chunks or self._matrix is None:
            return []

        query_vec = self._compute_vector(query)
        scores = np.dot(self._matrix, query_vec)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: list[dict[str, Any]] = []
        for idx in top_indices:
            score = float(scores[idx])
            chunk = self.chunks[idx]
            results.append(
                {
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "symbol": chunk.symbol,
                    "symbol_name": chunk.symbol,
                    "symbol_type": getattr(chunk, "symbol_type", ""),
                    "score": round(score, 4),
                    "similarity": round(score, 4),
                    "snippet": chunk.content[:400],
                    "content": chunk.content,
                }
            )
        return results

    def search_symbols(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Search symbol index by name matching substring query."""
        cur = self._conn.cursor()
        results: list[dict[str, Any]] = []
        clean_q = f"%{query.strip()}%"
        for row in cur.execute(
            """
            SELECT name, symbol_type, file_path, start_line, end_line, docstring
            FROM symbols
            WHERE name LIKE ?
            LIMIT ?
            """,
            (clean_q, top_k),
        ):
            results.append(
                {
                    "name": row[0],
                    "symbol_type": row[1],
                    "file_path": row[2],
                    "start_line": row[3],
                    "end_line": row[4],
                    "docstring": row[5] or "",
                }
            )
        return results

    def find_callers(self, symbol_name: str) -> list[dict[str, Any]]:
        """Find functions or methods that call the specified symbol."""
        cur = self._conn.cursor()
        results: list[dict[str, Any]] = []
        target = symbol_name.strip()
        for row in cur.execute(
            """
            SELECT caller, callee, file_path, line_number
            FROM call_graph
            WHERE callee = ? OR callee LIKE ?
            """,
            (target, f"%.{target}"),
        ):
            results.append(
                {
                    "caller": row[0],
                    "callee": row[1],
                    "file_path": row[2],
                    "line_number": row[3],
                }
            )
        return results

    def find_callees(self, symbol_name: str) -> list[dict[str, Any]]:
        """Find functions or methods called by the specified symbol."""
        cur = self._conn.cursor()
        results: list[dict[str, Any]] = []
        target = symbol_name.strip()
        for row in cur.execute(
            """
            SELECT caller, callee, file_path, line_number
            FROM call_graph
            WHERE caller = ? OR caller LIKE ?
            """,
            (target, f"%.{target}"),
        ):
            results.append(
                {
                    "caller": row[0],
                    "callee": row[1],
                    "file_path": row[2],
                    "line_number": row[3],
                }
            )
        return results

    def get_stats(self) -> dict[str, Any]:
        """Return counts of indexed files, chunks, symbols, and call graph edges."""
        cur = self._conn.cursor()
        f_count = cur.execute("SELECT COUNT(*) FROM files_meta").fetchone()[0]
        c_count = cur.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        s_count = cur.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        call_count = cur.execute("SELECT COUNT(*) FROM call_graph").fetchone()[0]
        return {
            "files_indexed": int(f_count),
            "chunks_stored": int(c_count),
            "symbols_indexed": int(s_count),
            "call_graph_edges": int(call_count),
            "vector_dimension": self.vector_dim,
            "database_path": self.db_path,
        }

    def save(self, filepath: str) -> None:
        """Persist semantic code chunks and embeddings to disk (JSON format)."""
        import json

        p = Path(filepath).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "vector_dim": self.vector_dim,
            "chunks": [
                {
                    "file_path": c.file_path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "content": c.content,
                    "symbol": c.symbol,
                    "symbol_type": getattr(c, "symbol_type", ""),
                    "docstring": getattr(c, "docstring", ""),
                    "vector": c.vector.tolist() if c.vector is not None else None,
                }
                for c in self.chunks
            ],
        }
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, filepath: str) -> bool:
        """Load persisted semantic code chunks and reconstruct vector matrix."""
        import json

        p = Path(filepath).expanduser().resolve()
        if not p.exists():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            self.vector_dim = data.get("vector_dim", self.vector_dim)
            self.chunks = []
            cur = self._conn.cursor()
            cur.execute("DELETE FROM chunks")

            for item in data.get("chunks", []):
                vec = (
                    np.array(item["vector"], dtype=np.float32)
                    if item.get("vector") is not None
                    else None
                )
                chunk = CodeChunk(
                    file_path=item["file_path"],
                    start_line=item["start_line"],
                    end_line=item["end_line"],
                    content=item["content"],
                    symbol=item.get("symbol", ""),
                    vector=vec,
                    symbol_type=item.get("symbol_type", ""),
                    docstring=item.get("docstring", ""),
                )
                self.chunks.append(chunk)
                cur.execute(
                    """
                    INSERT INTO chunks (file_path, start_line, end_line, symbol, symbol_type, content, docstring, vector)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.file_path,
                        chunk.start_line,
                        chunk.end_line,
                        chunk.symbol,
                        chunk.symbol_type,
                        chunk.content,
                        chunk.docstring,
                        vec.astype(np.float32).tobytes() if vec is not None else None,
                    ),
                )

            self._conn.commit()

            if self.chunks and any(c.vector is not None for c in self.chunks):
                self._matrix = np.vstack([c.vector for c in self.chunks if c.vector is not None])
            else:
                self._matrix = None
            return True
        except Exception:
            return False
