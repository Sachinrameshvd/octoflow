"""Unit tests for OctopusBrain architecture shapes, gradient flow, and gating dynamics."""

import pytest
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from octopus_brain.config import OctopusBrainConfig, EnvConfig
from octopus_brain.modules import PeripheralModule
from octopus_brain.central import CentralSystem
from octopus_brain.brain import OctopusBrain
from octopus_brain.losses import OctopusLoss
from experiments.baselines import (
    DenseCentralizedBaseline,
    SynchronousFullCommBaseline,
    AlwaysLocalBaseline,
)


def test_peripheral_module_shapes():
    """Verify PeripheralModule forward pass tensor shapes."""
    config = OctopusBrainConfig(obs_dim=16, action_dim=5, hidden_dim=64, message_dim=32)
    module = PeripheralModule(module_id=0, config=config)

    batch_size = 4
    obs = torch.randn(batch_size, config.obs_dim)
    prev_act = torch.zeros(batch_size, config.action_dim)
    prev_act[:, 0] = 1.0
    neighbor_in = torch.randn(batch_size, 2 * config.message_dim)
    central_feedback = torch.randn(batch_size, config.message_dim)
    h_prev = module.init_hidden(batch_size, obs.device)
    pred_obs_prev = torch.randn(batch_size, config.obs_dim)

    out = module(
        obs_t=obs,
        prev_action=prev_act,
        neighbor_in=neighbor_in,
        central_feedback=central_feedback,
        h_prev=h_prev,
        pred_obs_prev=pred_obs_prev,
    )

    assert out["action"].shape == (batch_size,)
    assert out["action_onehot"].shape == (batch_size, config.action_dim)
    assert out["action_logits"].shape == (batch_size, config.action_dim)
    assert out["action_log_prob"].shape == (batch_size,)
    assert out["action_entropy"].shape == (batch_size,)
    assert out["value"].shape == (batch_size, 1)
    assert out["h_next"].shape == (batch_size, config.hidden_dim)
    assert out["surprise"].shape == (batch_size, 1)
    assert out["report_prob"].shape == (batch_size, 1)
    assert out["report_flag"].shape == (batch_size, 1)
    assert out["message_to_central"].shape == (batch_size, config.message_dim)
    assert out["neighbor_message"].shape == (batch_size, config.message_dim)
    assert out["pred_next_obs"].shape == (batch_size, config.obs_dim)


def test_central_system_shapes_and_consolidation():
    """Verify CentralSystem coalition attention and sparse consolidation."""
    config = OctopusBrainConfig(n_modules=8, message_dim=32, central_dim=64, consolidation_every=5)
    central = CentralSystem(config)

    batch_size = 2
    messages = torch.randn(batch_size, config.n_modules, config.message_dim)
    report_flags = torch.zeros(batch_size, config.n_modules, 1)
    # Modules 1 and 3 report
    report_flags[:, 1, 0] = 1.0
    report_flags[:, 3, 0] = 1.0

    state = central.init_central_state(batch_size, messages.device)

    # Step 1: non-consolidation step
    out_step1 = central(messages, report_flags, state, step_count=1)
    assert out_step1["central_feedback"].shape == (batch_size, config.n_modules, config.message_dim)
    assert out_step1["coalition_matrix"].shape == (batch_size, config.n_modules, config.n_modules)
    assert out_step1["is_consolidation_step"] is False
    assert out_step1["consolidation_loss"].item() == 0.0

    # Non-reporting modules should receive 0 feedback
    assert torch.all(out_step1["central_feedback"][:, 0, :] == 0.0)
    assert torch.all(out_step1["central_feedback"][:, 2, :] == 0.0)

    # Step 5: consolidation step
    for s in range(2, 6):
        out_cons = central(messages, report_flags, state, step_count=s)
    assert out_cons["is_consolidation_step"] is True
    assert out_cons["consolidation_loss"] >= 0.0


def test_octopus_brain_full_step_and_diagnostics():
    """Verify OctopusBrain complete step execution, neighbor passing, and diagnostics."""
    config = OctopusBrainConfig(n_modules=6, obs_dim=16, action_dim=5)
    brain = OctopusBrain(config)

    batch_size = 3
    obs = torch.randn(batch_size, config.n_modules, config.obs_dim)

    brain.reset(batch_size=batch_size)
    out = brain.step(obs)

    assert out["actions"].shape == (batch_size, config.n_modules)
    assert out["action_logits"].shape == (batch_size, config.n_modules, config.action_dim)
    assert out["report_events"].shape == (batch_size, config.n_modules)
    assert out["surprise_values"].shape == (batch_size, config.n_modules)
    assert out["coalition_matrix"].shape == (batch_size, config.n_modules, config.n_modules)
    assert isinstance(out["report_rate"], float)
    assert isinstance(out["active_coalitions"], list)


def test_end_to_end_gradient_flow():
    """Verify gradients flow end-to-end to all module parameters, gate nets, and thresholds."""
    config = OctopusBrainConfig(
        n_modules=4,
        obs_dim=16,
        action_dim=5,
        hidden_dim=32,
        message_dim=16,
        central_dim=32,
        consolidation_every=2,
    )
    brain = OctopusBrain(config)
    loss_fn = OctopusLoss(config)

    batch_size = 2
    obs = torch.randn(batch_size, config.n_modules, config.obs_dim)
    brain.reset(batch_size=batch_size)

    # Step 1
    out1 = brain.step(obs)
    next_obs = torch.randn(batch_size, config.n_modules, config.obs_dim)

    # Step 2 (triggers consolidation)
    out2 = brain.step(next_obs)

    returns = torch.ones(batch_size, config.n_modules)

    loss_dict = loss_fn(
        action_log_probs=out2["action_log_probs"],
        action_entropies=out2["action_entropies"],
        values=out2["values"],
        returns=returns,
        report_probs=out2["report_probs"],
        pred_obs=out2["pred_next_obs"],
        actual_next_obs=obs,
        consolidation_loss=out2["consolidation_loss"],
        is_consolidation_step=out2["is_consolidation_step"],
    )

    total_loss = loss_dict["total_loss"]
    total_loss.backward()

    # Verify gradients exist and are non-zero for critical parameters
    for i, mod in enumerate(brain.modules_list):
        # GRU weights
        assert mod.gru_cell.weight_hh.grad is not None, f"Module {i} GRU grad is None"
        assert torch.norm(mod.gru_cell.weight_hh.grad) > 0.0

        # Actor head
        assert mod.actor[0].weight.grad is not None, f"Module {i} actor grad is None"

        # Forward model (predictive surprise)
        assert mod.forward_model[0].weight.grad is not None, f"Module {i} fwd model grad is None"

        # Gate net and learnable threshold
        assert mod.gate_net[0].weight.grad is not None, f"Module {i} gate grad is None"
        assert mod.report_threshold.grad is not None, f"Module {i} threshold grad is None"

    # Central system
    assert brain.central_system.q_proj.weight.grad is not None, "Central Q proj grad is None"
    assert brain.central_system.feedback_proj[0].weight.grad is not None, "Central feedback grad is None"


def test_gating_report_rate_not_stuck():
    """Verify that reporting gate is not stuck at 0% or 100% under initial config and responds to threshold."""
    config = OctopusBrainConfig(
        n_modules=6,
        report_threshold_init=0.0,  # Balanced initial threshold
        tau=1.0,
    )
    brain = OctopusBrain(config)

    batch_size = 20
    obs = torch.randn(batch_size, config.n_modules, config.obs_dim)
    brain.reset(batch_size=batch_size)

    out = brain.step(obs, deterministic=False)
    report_rate = out["report_rate"]

    # Initial report rate should be in healthy range (strictly > 0% and < 100%)
    assert 0.0 < report_rate < 1.0, f"Report rate {report_rate*100:.1f}% is stuck at degenerate extreme!"

    # Test responsiveness: setting high threshold should reduce report rate
    with torch.no_grad():
        for mod in brain.modules_list:
            mod.report_threshold.data.fill_(10.0)

    brain.reset(batch_size=batch_size)
    out_high = brain.step(obs, deterministic=True)
    assert out_high["report_rate"] <= report_rate, "Raising threshold should reduce report rate"


def test_baseline_architectures_run():
    """Verify all 3 baseline ablations execute cleanly with identical input shapes."""
    config = OctopusBrainConfig(n_modules=4, obs_dim=16, action_dim=5)
    obs = torch.randn(2, config.n_modules, config.obs_dim)

    # 1. Dense Centralized Baseline
    dense = DenseCentralizedBaseline(config)
    dense.reset(batch_size=2)
    out_dense = dense.step(obs)
    assert out_dense["actions"].shape == (2, config.n_modules)
    assert out_dense["report_rate"] == 1.0

    # 2. Synchronous Full Comm Baseline
    sync = SynchronousFullCommBaseline(config)
    sync.reset(batch_size=2)
    out_sync = sync.step(obs)
    assert out_sync["actions"].shape == (2, config.n_modules)
    assert out_sync["report_rate"] == 1.0

    # 3. Always Local Baseline
    local = AlwaysLocalBaseline(config)
    local.reset(batch_size=2)
    out_local = local.step(obs)
    assert out_local["actions"].shape == (2, config.n_modules)


def test_coalition_graph_extraction():
    """Verify connected component coalition clustering from attention matrices."""
    from octopus_brain.coalition import extract_coalitions_from_matrix

    # Adjacency with 2 distinct coalitions: {0, 1} and {4, 5, 6}
    adj_matrix = np.zeros((8, 8), dtype=np.float32)
    adj_matrix[0, 1] = adj_matrix[1, 0] = 0.45
    adj_matrix[4, 5] = adj_matrix[5, 4] = 0.30
    adj_matrix[5, 6] = adj_matrix[6, 5] = 0.25

    res = extract_coalitions_from_matrix(adj_matrix, threshold=0.20)
    assert res["num_active_coalitions"] == 2
    assert {0, 1} in res["active_coalitions"]
    assert {4, 5, 6} in res["active_coalitions"]
    assert set(res["isolated_modules"]) == {2, 3, 7}


def test_adaptive_gate_budgeter():
    """Verify Lagrangian dual multiplier updates and budget penalty."""
    from octopus_brain.losses import AdaptiveGateBudgeter

    budgeter = AdaptiveGateBudgeter(target_rate=0.25, lr=0.1, init_val=0.1)
    init_lambda = float(budgeter.lambda_val.item())

    # High report rate (0.80 > 0.25) -> lambda should increase
    new_lambda = budgeter.update_dual_step(0.80)
    assert new_lambda > init_lambda, "Dual multiplier should increase when rate > target"

    # Low report rate (0.05 < 0.25) -> lambda should decrease
    decreased_lambda = budgeter.update_dual_step(0.05)
    assert decreased_lambda < new_lambda, "Dual multiplier should decrease when rate < target"
