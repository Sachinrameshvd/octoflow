"""Unit tests for Coalition Attention and Graph Clustering Algorithms."""

import pytest
import numpy as np
from octoflow.coalition import extract_coalitions_from_matrix


def test_extract_coalitions_from_matrix():
    # 4-node matrix with two clear clusters: (0, 1) and (2, 3)
    c_matrix = np.array([
        [0.0, 0.6, 0.0, 0.0],
        [0.6, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.7],
        [0.0, 0.0, 0.7, 0.0],
    ])

    graph_info = extract_coalitions_from_matrix(c_matrix, threshold=0.3)
    clusters = graph_info["active_coalitions"]
    edge_list = graph_info["edge_list"]
    isolated = graph_info["isolated_modules"]

    assert len(clusters) == 2
    assert {0, 1} in [set(c) for c in clusters]
    assert {2, 3} in [set(c) for c in clusters]
    assert len(isolated) == 0
    assert len(edge_list) == 2


def test_central_system_forward_and_coalition_matrix():
    torch = pytest.importorskip("torch")
    from octopus_brain.central import CentralSystem
    from octopus_brain.config import OctopusBrainConfig

    config = OctopusBrainConfig(n_modules=8, message_dim=32, central_dim=32, num_heads=4)
    central = CentralSystem(config)

    B, N, dim = 2, 8, 32
    messages = torch.randn(B, N, dim)
    report_flags = torch.ones(B, N, 1)
    central_state = central.init_central_state(batch_size=B, device=torch.device("cpu"))

    out = central(messages, report_flags, central_state, step_count=1)
    assert "central_feedback" in out
    assert "central_state" in out
    assert "coalition_matrix" in out
    assert "is_consolidation_step" in out
    assert "consolidation_loss" in out

    c_mat = out["coalition_matrix"]
    assert c_mat.shape == (B, N, N)
    assert (c_mat >= 0.0).all()
