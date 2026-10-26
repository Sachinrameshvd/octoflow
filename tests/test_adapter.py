"""Unit tests for OctopusGymAdapter and ONNX export pipeline."""

import os
import pytest
import numpy as np

torch = pytest.importorskip("torch")

from octopus_brain.config import OctopusBrainConfig
from octopus_brain.brain import OctopusBrain
from octopus_brain.adapter import OctopusGymAdapter


def test_adapter_initialization_and_properties():
    """Verify adapter creation, config propagation, and dimension properties."""
    config = OctopusBrainConfig(n_modules=8, obs_dim=16, action_dim=5)
    adapter = OctopusGymAdapter(config=config, device="cpu")

    assert adapter.n_arms == 8
    assert adapter.obs_dim == 16
    assert adapter.action_dim == 5


def test_adapter_predict_unbatched():
    """Verify unbatched sensory input processing and telemetry outputs."""
    adapter = OctopusGymAdapter(device="cpu")
    obs = np.random.randn(8, 16).astype(np.float32)

    actions, info = adapter.predict(obs, deterministic=True)

    assert isinstance(actions, np.ndarray)
    assert actions.shape == (8,)
    assert "report_events" in info
    assert info["report_events"].shape == (8,)
    assert "report_rate" in info
    assert 0.0 <= info["report_rate"] <= 1.0
    assert "coalition_clusters" in info
    assert "surprise_values" in info
    assert info["surprise_values"].shape == (8,)


def test_adapter_predict_batched():
    """Verify batched multi-environment step execution."""
    adapter = OctopusGymAdapter(device="cpu")
    B = 4
    obs_batch = np.random.randn(B, 8, 16).astype(np.float32)

    actions, info = adapter.predict(obs_batch, deterministic=False)

    assert isinstance(actions, np.ndarray)
    assert actions.shape == (B, 8)
    assert info["report_events"].shape == (B, 8)


def test_adapter_dynamic_amputation_mask():
    """Verify dynamic arm knockout / amputation masking support."""
    adapter = OctopusGymAdapter(device="cpu")
    obs = np.random.randn(8, 16).astype(np.float32)

    # Arm 2 and Arm 6 severed
    active_indices = [0, 1, 3, 4, 5, 7]
    actions, info = adapter.predict(obs, active_mask=active_indices, deterministic=True)

    assert actions.shape == (8,)
    # Severed arms should default to 0 (Stay)
    assert actions[2] == 0
    assert actions[6] == 0


def test_adapter_checkpoint_loading():
    """Verify loading trained weights into adapter."""
    ckpt_path = "checkpoints/top1_octopus_brain.pt"
    if os.path.exists(ckpt_path):
        adapter = OctopusGymAdapter(checkpoint_path=ckpt_path, device="cpu")
        obs = np.zeros((8, 16), dtype=np.float32)
        actions, info = adapter.predict(obs)
        assert actions.shape == (8,)


def test_onnx_model_inference():
    """Verify onnxruntime loads and executes the exported ONNX model."""
    onnx_path = "checkpoints/octopus_brain.onnx"
    if os.path.exists(onnx_path):
        import onnxruntime as ort

        session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        B, N = 1, 8
        dummy_inputs = {
            "obs": np.zeros((B, N, 16), dtype=np.float32),
            "hidden_states": np.zeros((B, N, 64), dtype=np.float32),
            "central_state": np.zeros((B, 64), dtype=np.float32),
            "prev_actions": np.zeros((B, N, 5), dtype=np.float32),
            "prev_neighbor_msgs": np.zeros((B, N, 32), dtype=np.float32),
            "prev_central_feedback": np.zeros((B, N, 32), dtype=np.float32),
        }
        outputs = session.run(None, dummy_inputs)
        actions = outputs[0]
        assert actions.shape == (B, N)
