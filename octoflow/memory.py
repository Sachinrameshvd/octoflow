"""Vertical Lobe Hebbian Associative Memory for Instant Bug/Fix Pattern Recall.

Inspired by the cephalopod Vertical Lobe presynaptic Long-Term Potentiation (LTP)
circuit. Associates sensory error signatures with verified resolution policies,
enabling sub-millisecond retrieval without expensive vector database RAG lookups.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch


class FixPattern:
    """A cached resolution pattern learned via Vertical Lobe LTP."""
    def __init__(self, signature_vector: np.ndarray, error_name: str, fix_guidance: str):
        self.signature = signature_vector / (np.linalg.norm(signature_vector) + 1e-8)
        self.error_name = error_name
        self.fix_guidance = fix_guidance
        self.reinforcement_count = 1


class VerticalLobeMemory:
    """Associative presynaptic memory using Hebbian-style pattern consolidation."""

    def __init__(self, feature_dim: int = 16, recall_threshold: float = 0.75):
        self.feature_dim = feature_dim
        self.recall_threshold = recall_threshold
        self.max_weight: float = 5.0
        self.decay_rate: float = 0.05
        self.W = np.zeros((feature_dim, feature_dim), dtype=np.float32)
        self.patterns: List[FixPattern] = []
        self._seed_common_patterns()

    def _seed_common_patterns(self) -> None:
        """Seed biophysical memory with common software/ML debugging heuristics."""
        # Pattern 1: Syntax / Indentation Error
        v1 = np.zeros(self.feature_dim, dtype=np.float32)
        v1[6] = 1.0  # Syntax error flag
        self.patterns.append(FixPattern(
            v1,
            "SyntaxError / ParseError",
            "Check for missing colons, mismatched brackets, or Python indentation inconsistencies."
        ))

        # Pattern 2: CUDA / Memory OOM
        v2 = np.zeros(self.feature_dim, dtype=np.float32)
        v2[7] = 1.0  # OOM flag
        self.patterns.append(FixPattern(
            v2,
            "CUDA OutOfMemory",
            "Reduce batch size by 50%, enable torch.amp.autocast, or call torch.cuda.empty_cache()."
        ))

        # Pattern 3: Missing Module / File
        v3 = np.zeros(self.feature_dim, dtype=np.float32)
        v3[9] = 1.0  # Missing file flag
        self.patterns.append(FixPattern(
            v3,
            "ModuleNotFoundError / FileNotFoundError",
            "Verify import paths, check working directory structure, or add package to requirements."
        ))

        # Pattern 4: Type / Schema Validation Error
        v4 = np.zeros(self.feature_dim, dtype=np.float32)
        v4[10] = 1.0  # Type error flag
        self.patterns.append(FixPattern(
            v4,
            "TypeError / SchemaValidationError",
            "Check Pydantic field types, ensure JSON response matches expected schema, or add cast."
        ))

    def recall(self, sensory_obs: np.ndarray) -> Optional[Tuple[str, float]]:
        """Query memory with current error signature. Returns (guidance, confidence) if matched."""
        if np.isnan(sensory_obs).any() or np.isinf(sensory_obs).any():
            return None
        norm = np.linalg.norm(sensory_obs)
        if norm < 1e-8:
            return None
        query = sensory_obs / norm

        best_score = -1.0
        best_pattern: Optional[FixPattern] = None

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

    def apply_decay(self, decay_rate: Optional[float] = None) -> None:
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

    def index_codebase(self, workspace_dir: str) -> int:
        """Index the workspace codebase into episodic semantic vector memory."""
        if not hasattr(self, "rag") or self.rag is None:
            self.rag = EpisodicCodebaseRAG()
        return self.rag.index_workspace(workspace_dir)

    def search_codebase(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Search the codebase for semantically relevant symbols, functions, or snippets."""
        if not hasattr(self, "rag") or self.rag is None:
            self.rag = EpisodicCodebaseRAG()
        return self.rag.search(query, top_k=top_k)


class CodeChunk:
    """A semantic code chunk stored in the episodic codebase connectome."""
    def __init__(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        content: str,
        symbol: str = "",
        vector: Optional[np.ndarray] = None,
    ):
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.symbol = symbol
        self.vector = vector


class EpisodicCodebaseRAG:
    """Semantic vector RAG over the codebase workspace using subword character hashing.

    Matches RuVector / AgentDB functionality with zero heavy external dependencies.
    """

    SUPPORTED_EXTS = {
        ".py", ".ts", ".js", ".tsx", ".jsx", ".rs", ".go", ".json",
        ".html", ".css", ".md", ".toml", ".yaml", ".yml", ".sql", ".sh"
    }

    IGNORE_DIRS = {
        ".git", "node_modules", "venv", ".venv", "__pycache__", "dist",
        "build", ".pytest_cache", ".next", "target", "vendor"
    }

    def __init__(self, vector_dim: int = 128):
        self.vector_dim = vector_dim
        self.chunks: List[CodeChunk] = []
        self._matrix: Optional[np.ndarray] = None

    def _compute_vector(self, text: str) -> np.ndarray:
        """Compute a normalized subword character n-gram hash vector."""
        import re
        vec = np.zeros(self.vector_dim, dtype=np.float32)
        tokens = re.findall(r'[a-zA-Z0-9_]+', text.lower())
        for tok in tokens:
            idx = abs(hash(tok)) % self.vector_dim
            vec[idx] += 1.0
            if len(tok) >= 3:
                for i in range(len(tok) - 2):
                    ng = tok[i:i+3]
                    vec[abs(hash(ng)) % self.vector_dim] += 0.5
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec /= norm
        return vec

    def index_workspace(self, workspace_dir: str) -> int:
        """Scan and index all workspace source files into semantic chunks."""
        from pathlib import Path
        ws = Path(workspace_dir).resolve()
        if not ws.exists():
            return 0

        self.chunks = []
        for file_path in ws.rglob("*"):
            if file_path.is_dir():
                continue
            if any(part.startswith(".") or "venv" in part.lower() or part in self.IGNORE_DIRS for part in file_path.parts[:-1]):
                continue
            if file_path.suffix.lower() not in self.SUPPORTED_EXTS:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                if not lines:
                    continue

                rel_path = str(file_path.relative_to(ws))

                # Chunking: windows of 35 lines with 10 line overlap
                chunk_size = 35
                step = 25
                for i in range(0, len(lines), step):
                    chunk_lines = lines[i:i + chunk_size]
                    chunk_text = "\n".join(chunk_lines)
                    if not chunk_text.strip():
                        continue

                    # Extract primary symbol if python
                    symbol = ""
                    for line in chunk_lines:
                        clean_l = line.strip()
                        if clean_l.startswith("def ") or clean_l.startswith("class ") or clean_l.startswith("function ") or clean_l.startswith("export "):
                            symbol = clean_l.split("(")[0].replace("def ", "").replace("class ", "").replace("function ", "").replace("export ", "").strip()
                            break

                    vec = self._compute_vector(f"{rel_path} {symbol}\n{chunk_text}")
                    self.chunks.append(CodeChunk(
                        file_path=rel_path,
                        start_line=i + 1,
                        end_line=min(len(lines), i + chunk_size),
                        content=chunk_text,
                        symbol=symbol,
                        vector=vec,
                    ))
            except Exception:
                continue

        if self.chunks:
            self._matrix = np.vstack([c.vector for c in self.chunks])
        else:
            self._matrix = None

        return len(self.chunks)

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Search code chunks matching query with cosine similarity."""
        if not self.chunks or self._matrix is None:
            return []

        query_vec = self._compute_vector(query)
        scores = np.dot(self._matrix, query_vec)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            chunk = self.chunks[idx]
            results.append({
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "symbol": chunk.symbol,
                "score": round(score, 4),
                "snippet": chunk.content[:400],
            })
        return results

    def save(self, filepath: str) -> None:
        """Persist semantic code chunks and embeddings to disk."""
        import json
        from pathlib import Path
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
                    "vector": c.vector.tolist() if c.vector is not None else None,
                }
                for c in self.chunks
            ],
        }
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, filepath: str) -> bool:
        """Load persisted semantic code chunks and reconstruct vector matrix."""
        import json
        from pathlib import Path
        p = Path(filepath).expanduser().resolve()
        if not p.exists():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            self.vector_dim = data.get("vector_dim", self.vector_dim)
            self.chunks = []
            for item in data.get("chunks", []):
                vec = np.array(item["vector"], dtype=np.float32) if item.get("vector") is not None else None
                chunk = CodeChunk(
                    file_path=item["file_path"],
                    start_line=item["start_line"],
                    end_line=item["end_line"],
                    content=item["content"],
                    symbol=item.get("symbol", ""),
                    vector=vec,
                )
                self.chunks.append(chunk)
            if self.chunks and any(c.vector is not None for c in self.chunks):
                self._matrix = np.vstack([c.vector for c in self.chunks if c.vector is not None])
            else:
                self._matrix = None
            return True
        except Exception:
            return False

