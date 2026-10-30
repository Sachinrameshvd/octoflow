"""Unit tests for Arm Knockout Fault Tolerance and Graceful Degradation."""

import numpy as np
import pytest

torch = pytest.importorskip("torch")
from envs.reach_and_avoid import ReachAndAvoidEnv
from experiments.run_fault_tolerance import run_episode
from octopus_brain.brain import OctopusBrain
from octopus_brain.config import EnvConfig, OctopusBrainConfig


def test_amputation_resilience():
    config = OctopusBrainConfig(n_modules=8, hidden_dim=32, message_dim=16)
    env_config = EnvConfig(n_arms=8, max_steps=15)
    env = ReachAndAvoidEnv(env_config)
    model = OctopusBrain(config)

    # Test under various knockout counts: 0, 1, 3, 5, 7 killed arms
    for k in [0, 1, 3, 5, 7]:
        res = run_episode(env, model, num_killed=k, seed=100 + k, device=torch.device("cpu"))
        assert "reward" in res
        assert "mean_report_rate" in res
        assert not np.isnan(res["reward"])
        assert 0.0 <= res["mean_report_rate"] <= 1.0


def test_model_masking_during_step():
    config = OctopusBrainConfig(n_modules=4, hidden_dim=32, message_dim=16)
    model = OctopusBrain(config)
    model.reset(batch_size=1)

    obs = torch.randn(1, 4, config.obs_dim)
    # Mask out module 0 and 2
    active_mask = torch.tensor([[0.0, 1.0, 0.0, 1.0]])

    out = model.step(obs, active_mask=active_mask)
    assert out["actions"].shape == (1, 4)
    # Check that outputs are valid without NaN
    assert not torch.isnan(out["action_logits"]).any()
