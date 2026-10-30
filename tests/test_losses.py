"""Unit tests for OctopusLoss and AdaptiveGateBudgeter."""

import pytest

torch = pytest.importorskip("torch")
from octopus_brain.config import OctopusBrainConfig
from octopus_brain.losses import AdaptiveGateBudgeter, OctopusLoss


def test_adaptive_gate_budgeter_init_and_properties():
    budgeter = AdaptiveGateBudgeter(target_rate=0.25, lr=0.05, init_val=0.2)
    assert budgeter.target_rate == 0.25
    assert budgeter.lr == 0.05
    assert 0.15 < budgeter.lambda_val.item() < 0.25


def test_adaptive_gate_budgeter_penalty_computation():
    budgeter = AdaptiveGateBudgeter(target_rate=0.25, lr=0.05, init_val=0.1)

    # Over target (rate = 0.50 > 0.25)
    high_probs = torch.full((4, 8), 0.50)
    primal, dual = budgeter.compute_penalty(high_probs)
    assert primal.item() > 0
    assert dual.requires_grad

    # Under target (rate = 0.10 < 0.25)
    low_probs = torch.full((4, 8), 0.10)
    primal_low, _ = budgeter.compute_penalty(low_probs)
    assert primal_low.item() < primal.item()


def test_adaptive_gate_budgeter_dual_step():
    budgeter = AdaptiveGateBudgeter(target_rate=0.25, lr=0.1, init_val=0.2)
    initial_lambda = budgeter.lambda_val.item()

    # High reporting rate should increase lambda (higher penalty)
    new_lambda = budgeter.update_dual_step(0.60)
    assert new_lambda > initial_lambda

    # Low reporting rate should decrease lambda
    lower_lambda = budgeter.update_dual_step(0.05)
    assert lower_lambda < new_lambda


def test_octopus_loss_full_forward_and_gradient_flow():
    config = OctopusBrainConfig(n_modules=4, obs_dim=8)
    loss_fn = OctopusLoss(config)

    T, B, N, obs_dim = 10, 2, 4, 8
    action_log_probs = torch.randn(T, B, N, requires_grad=True)
    action_entropies = torch.rand(T, B, N, requires_grad=True)
    values = torch.randn(T, B, N, 1, requires_grad=True)
    returns = torch.randn(T, B, N)
    report_probs = torch.sigmoid(torch.randn(T, B, N, requires_grad=True))
    pred_obs = torch.randn(T, B, N, obs_dim, requires_grad=True)
    actual_obs = torch.randn(T, B, N, obs_dim)
    consolidation_loss = torch.tensor(0.5, requires_grad=True)

    losses = loss_fn(
        action_log_probs=action_log_probs,
        action_entropies=action_entropies,
        values=values,
        returns=returns,
        report_probs=report_probs,
        pred_obs=pred_obs,
        actual_next_obs=actual_obs,
        consolidation_loss=consolidation_loss,
        is_consolidation_step=True,
    )

    assert "total_loss" in losses
    assert "policy_loss" in losses
    assert "value_loss" in losses
    assert "entropy_loss" in losses
    assert "message_penalty" in losses
    assert "forward_model_loss" in losses
    assert "consolidation_loss" in losses

    total_loss = losses["total_loss"]
    total_loss.backward()

    assert action_log_probs.grad is not None
    assert values.grad is not None
    assert pred_obs.grad is not None


def test_octopus_loss_ppo_clipped_surrogate():
    config = OctopusBrainConfig(n_modules=4, obs_dim=8)
    loss_fn = OctopusLoss(config)

    T, B, N = 8, 1, 4
    old_log_probs = torch.randn(T, B, N)
    # New log probs shifted
    new_log_probs = old_log_probs + 0.1
    new_log_probs.requires_grad = True
    entropies = torch.rand(T, B, N)
    values = torch.randn(T, B, N, 1, requires_grad=True)
    returns = torch.randn(T, B, N)
    advantages = torch.randn(T, B, N)
    report_probs = torch.sigmoid(torch.randn(T, B, N))

    losses = loss_fn(
        action_log_probs=new_log_probs,
        action_entropies=entropies,
        values=values,
        returns=returns,
        report_probs=report_probs,
        old_action_log_probs=old_log_probs,
        advantages=advantages,
        clip_eps=0.2,
        normalize_adv=True,
    )

    assert "policy_loss" in losses
    assert not torch.isnan(losses["policy_loss"])
    losses["total_loss"].backward()
    assert new_log_probs.grad is not None
