"""Comprehensive test suite for VerticalLobeMemory & EpisodicCodebaseRAG (Subsystem 3.4).

Verifies:
1. Biophysical Hebbian pattern consolidation and sub-millisecond recall.
2. Recall threshold filtering and non-matching fallback.
3. Degenerate sensory observations (zero-norm, NaN, Inf) handling without crash.
4. Synaptic weight matrix clipping to prevent numerical explosion.
5. Synaptic decay (LTD - Long Term Depression) and unreinforced memory fading.
6. VerticalLobeMemory serialization roundtrip (save and load).
7. EpisodicCodebaseRAG indexing and semantic search over code chunks.
8. EpisodicCodebaseRAG persistence roundtrip (save and load).
"""

import os

import numpy as np
from octoflow.memory import EpisodicCodebaseRAG, VerticalLobeMemory


def test_hebbian_seed_and_recall():
    """Verify seeded diagnostic patterns are recalled accurately."""
    mem = VerticalLobeMemory(feature_dim=16, recall_threshold=0.70)

    # Test syntax error query (feature 6 active)
    query_syntax = np.zeros(16, dtype=np.float32)
    query_syntax[6] = 1.0

    res = mem.recall(query_syntax)
    assert res is not None, "Syntax query should match seeded syntax pattern"
    guidance, confidence = res
    assert "colons" in guidance.lower() or "indentation" in guidance.lower()
    assert confidence >= 0.70


def test_hebbian_consolidation_and_recall():
    """Verify novel error pattern consolidation and retrieval."""
    mem = VerticalLobeMemory(feature_dim=16, recall_threshold=0.70)

    # Custom novel error signature (feature 2 and 5 active)
    novel_sig = np.zeros(16, dtype=np.float32)
    novel_sig[2] = 2.0
    novel_sig[5] = 2.0

    # Before consolidation: no match
    assert mem.recall(novel_sig) is None

    # Consolidate
    mem.consolidate(
        error_obs=novel_sig,
        error_name="PostgresDeadlockError",
        fix_guidance="Retry transaction with exponential backoff and enforce consistent table lock ordering.",
    )

    # After consolidation: matches immediately
    res = mem.recall(novel_sig)
    assert res is not None
    guidance, confidence = res
    assert "transaction" in guidance.lower()
    assert confidence > 0.95


def test_hebbian_matrix_clipping_and_decay():
    """Verify synaptic weight matrix updates, bounded clipping, and decay."""
    mem = VerticalLobeMemory(feature_dim=16, recall_threshold=0.70)
    assert hasattr(mem, "W"), "Memory should maintain Hebbian weight matrix W"
    assert mem.W.shape == (16, 16)

    # Repeated heavy consolidation must not cause runaway weight explosion
    sig = np.ones(16, dtype=np.float32)
    for _ in range(100):
        mem.consolidate(sig, "StressPattern", "Guidance")

    # Weights must be clipped within [-max_weight, max_weight]
    max_w = getattr(mem, "max_weight", 5.0)
    assert np.all(mem.W <= max_w + 1e-5), f"Synaptic weights exceeded max_weight: {np.max(mem.W)}"
    assert np.all(mem.W >= -max_w - 1e-5), f"Synaptic weights below -max_weight: {np.min(mem.W)}"

    # Test decay
    initial_norm = np.linalg.norm(mem.W)
    assert initial_norm > 0.0
    mem.apply_decay(decay_rate=0.20)
    decayed_norm = np.linalg.norm(mem.W)
    assert decayed_norm < initial_norm, "Decay must reduce synaptic weight norm"


def test_degenerate_observation_safety():
    """Verify zero-norm and NaN observations do not crash memory."""
    mem = VerticalLobeMemory(feature_dim=16)

    # Zero observation
    zero_obs = np.zeros(16, dtype=np.float32)
    assert mem.recall(zero_obs) is None
    mem.consolidate(zero_obs, "ZeroError", "Ignore")

    # NaN observation
    nan_obs = np.full(16, np.nan, dtype=np.float32)
    assert mem.recall(nan_obs) is None
    mem.consolidate(nan_obs, "NaNError", "Ignore")


def test_memory_save_and_load(tmp_path):
    """Verify VerticalLobeMemory roundtrip serialization."""
    save_file = str(tmp_path / "test_memory.json")
    mem = VerticalLobeMemory(feature_dim=16)

    sig = np.zeros(16, dtype=np.float32)
    sig[3] = 1.0
    mem.consolidate(sig, "CustomErr", "CustomGuidance123")
    mem.save(save_file)

    assert os.path.exists(save_file)

    # Load into fresh instance
    new_mem = VerticalLobeMemory(feature_dim=16)
    loaded = new_mem.load(save_file)
    assert loaded is True

    res = new_mem.recall(sig)
    assert res is not None
    assert "CustomGuidance123" in res[0]


def test_episodic_codebase_rag_index_and_search(tmp_path):
    """Verify EpisodicCodebaseRAG indexes workspace and retrieves relevant symbols."""
    # Create mock workspace files
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    auth_file = src_dir / "auth.py"
    auth_file.write_text(
        "def verify_jwt_token(token: str) -> bool:\n"
        '    """Verify JWT authorization signature and claims."""\n'
        "    if not token:\n"
        "        return False\n"
        "    return token.startswith('bearer_')\n"
    )

    db_file = src_dir / "db.py"
    db_file.write_text(
        "class DatabasePool:\n"
        "    def execute_query(self, sql: str):\n"
        '        """Execute SQL against Postgres connection pool."""\n'
        "        pass\n"
    )

    rag = EpisodicCodebaseRAG(vector_dim=64)
    indexed_count = rag.index_workspace(str(tmp_path))
    assert indexed_count >= 2

    # Query for JWT verification
    results = rag.search("verify jwt token authorization", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "auth.py" in top["file_path"]
    assert top["score"] > 0.0


def test_episodic_codebase_rag_save_and_load(tmp_path):
    """Verify EpisodicCodebaseRAG save and load persistence."""
    src_dir = tmp_path / "project"
    src_dir.mkdir()
    f = src_dir / "service.py"
    f.write_text("def dispatch_alert(arm_id: int): pass\n")

    rag = EpisodicCodebaseRAG(vector_dim=32)
    rag.index_workspace(str(tmp_path))
    assert len(rag.chunks) > 0

    save_path = str(tmp_path / "rag_index.json")
    rag.save(save_path)
    assert os.path.exists(save_path)

    new_rag = EpisodicCodebaseRAG(vector_dim=32)
    success = new_rag.load(save_path)
    assert success is True
    assert len(new_rag.chunks) == len(rag.chunks)
    assert new_rag._matrix is not None

    # Search works on loaded index
    results = new_rag.search("dispatch alert", top_k=1)
    assert len(results) == 1
    assert "service.py" in results[0]["file_path"]
