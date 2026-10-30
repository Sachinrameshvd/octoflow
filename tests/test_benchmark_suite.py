"""Unit tests for Benchmark Suite execution and ablation baselines."""

import os
import tempfile

import pytest

torch = pytest.importorskip("torch")
from experiments.baselines import (
    AlwaysLocalBaseline,
    DenseCentralizedBaseline,
    SynchronousFullCommBaseline,
)
from experiments.run_benchmark_suite import run_benchmark_suite
from octopus_brain.config import OctopusBrainConfig


def test_baseline_models_step():
    config = OctopusBrainConfig(n_modules=4, hidden_dim=32, message_dim=16)
    obs = torch.randn(1, 4, config.obs_dim)

    models = [
        DenseCentralizedBaseline(config),
        AlwaysLocalBaseline(config),
        SynchronousFullCommBaseline(config),
    ]

    for model in models:
        model.reset(batch_size=1)
        out = model.step(obs)
        assert "actions" in out
        assert out["actions"].shape == (1, 4)


def test_run_benchmark_suite_dry_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_benchmark_suite(num_seeds=1, episodes_per_seed=2, output_dir=tmpdir)
        json_file = os.path.join(tmpdir, "benchmark_results.json")
        plot_file = os.path.join(tmpdir, "benchmark_results.png")
        assert os.path.exists(json_file)
        assert os.path.exists(plot_file)
