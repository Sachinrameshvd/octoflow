"""Loss functions for OctopusBrain training and regularization.

Components:
- Task Loss (Actor-Critic / Policy Gradient + Value MSE)
- Message Rate Penalty Loss (Prevents gating collapse to always-report or never-report)
- Forward Model Prediction Loss (Surprise calibration)
- Slow Central Consolidation Loss (Applied only at consolidation events)
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from octopus_brain.config import OctopusBrainConfig


class AdaptiveGateBudgeter(nn.Module):
    """Lagrangian dual optimizer for exact communication budget enforcement."""

    def __init__(self, target_rate: float = 0.25, lr: float = 0.05, init_val: float = 0.1):
        super().__init__()
        self.target_rate = float(target_rate)
        self.lr = float(lr)
        # Learnable log dual multiplier log(lambda)
        self.log_lambda = nn.Parameter(
            torch.tensor(float(np.log(max(init_val, 1e-4))), dtype=torch.float32)
        )

    @property
    def lambda_val(self) -> torch.Tensor:
        """Current clamped dual multiplier lambda = exp(log_lambda)."""
        return torch.exp(torch.clamp(self.log_lambda, -6.0, 6.0))

    def compute_penalty(self, report_probs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Compute Lagrangian penalty loss and dual loss.

        Args:
            report_probs: (B, N) or (T, B, N) Reporting probabilities.

        Returns:
            (primal_penalty, dual_loss)
        """
        mean_rate = report_probs.mean()
        diff = mean_rate - self.target_rate
        # Primal penalty term for the policy
        primal_penalty = self.lambda_val.detach() * diff + (diff**2)
        # Dual loss for updating lambda (gradient ascent on multiplier)
        dual_loss = -self.log_lambda * diff.detach()
        return primal_penalty, dual_loss

    def update_dual_step(self, mean_report_rate: float) -> float:
        """Manual update step for dual multiplier: log_lambda += lr * (rate - target)."""
        with torch.no_grad():
            diff = float(mean_report_rate) - self.target_rate
            self.log_lambda.add_(self.lr * diff)
            self.log_lambda.clamp_(-6.0, 6.0)
        return float(self.lambda_val.item())


class OctopusLoss(nn.Module):
    """Unified loss criterion for OctopusBrain training with optional adaptive budgeting."""

    def __init__(self, config: OctopusBrainConfig | None = None):
        super().__init__()
        self.config = config or OctopusBrainConfig()
        self.message_penalty_coef = self.config.message_penalty_coef
        self.target_report_rate = self.config.target_report_rate
        self.consolidation_loss_coef = self.config.consolidation_loss_coef
        self.forward_model_loss_coef = self.config.forward_model_loss_coef
        self.entropy_coef = self.config.entropy_coef
        self.value_loss_coef = self.config.value_loss_coef

        # Adaptive Lagrangian Gate Budgeter
        self.adaptive_budgeting = self.config.adaptive_budgeting
        if self.adaptive_budgeting:
            self.gate_budgeter = AdaptiveGateBudgeter(
                target_rate=self.config.target_report_rate,
                lr=self.config.lagrange_lr,
                init_val=self.config.lagrange_init,
            )
        else:
            self.gate_budgeter = None

    def compute_policy_loss(
        self,
        action_log_probs: torch.Tensor,
        action_entropies: torch.Tensor,
        values: torch.Tensor,
        returns: torch.Tensor,
        old_action_log_probs: torch.Tensor | None = None,
        clip_eps: float = 0.2,
        advantages: torch.Tensor | None = None,
        normalize_adv: bool = True,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Compute Actor-Critic policy gradient / PPO clipped loss, value, and entropy losses.

        Args:
            action_log_probs: (B, N) or (T, B, N)
            action_entropies: (B, N) or (T, B, N)
            values: (B, N, 1) or (T, B, N, 1)
            returns: (B, N) or (T, B, N) Target returns / discounted rewards.
            old_action_log_probs: Optional log probs from rollout for PPO clipping.
            clip_eps: PPO clipping epsilon (default: 0.2).
            advantages: Optional precomputed GAE advantages.
            normalize_adv: Whether to normalize advantages to mean 0, std 1.

        Returns:
            (policy_loss, value_loss, entropy_loss)
        """
        # Advantage estimation
        val = values.squeeze(-1)  # (B, N) or (T, B, N)
        if advantages is None:
            adv = (returns - val).detach()
        else:
            adv = advantages.detach()

        if normalize_adv and adv.numel() > 1:
            adv_std = adv.std()
            if adv_std > 1e-6:
                adv = (adv - adv.mean()) / (adv_std + 1e-8)

        if old_action_log_probs is not None:
            # PPO Clipped Surrogate Objective
            ratio = torch.exp(action_log_probs - old_action_log_probs.detach())
            surr1 = ratio * adv
            surr2 = torch.clamp(ratio, 1.0 - clip_eps, 1.0 + clip_eps) * adv
            policy_loss = -torch.min(surr1, surr2).mean()
        else:
            # Standard policy gradient loss
            policy_loss = -(action_log_probs * adv).mean()

        # Value baseline loss
        value_loss = F.mse_loss(val, returns)

        # Entropy regularizer (bonus for higher entropy -> negative loss)
        entropy_loss = -action_entropies.mean()

        return policy_loss, value_loss, entropy_loss

    def compute_message_penalty(
        self, report_probs: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Compute message-rate penalty loss using Lagrangian dual optimization."""
        if self.adaptive_budgeting and self.gate_budgeter is not None:
            return self.gate_budgeter.compute_penalty(report_probs)
        else:
            mean_rate = report_probs.mean()
            target_penalty = (mean_rate - self.target_report_rate) ** 2
            return target_penalty, torch.tensor(0.0, device=report_probs.device)

    def compute_forward_model_loss(
        self,
        pred_obs: torch.Tensor,
        actual_obs: torch.Tensor,
        active_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute forward-model observation prediction MSE loss.

        Args:
            pred_obs: (B, N, obs_dim) Next observation prediction.
            actual_obs: (B, N, obs_dim) Actual next observation.
            active_mask: (B, N) Optional mask for functional modules.

        Returns:
            Scalar MSE loss.
        """
        diff_sq = (pred_obs - actual_obs) ** 2
        if active_mask is not None:
            mask = active_mask.unsqueeze(-1).float()
            diff_sq = diff_sq * mask
            return diff_sq.sum() / torch.clamp(mask.sum() * pred_obs.size(-1), min=1.0)
        return diff_sq.mean()

    def forward(
        self,
        action_log_probs: torch.Tensor,
        action_entropies: torch.Tensor,
        values: torch.Tensor,
        returns: torch.Tensor,
        report_probs: torch.Tensor,
        pred_obs: torch.Tensor | None = None,
        actual_next_obs: torch.Tensor | None = None,
        consolidation_loss: torch.Tensor | None = None,
        is_consolidation_step: bool = False,
        old_action_log_probs: torch.Tensor | None = None,
        clip_eps: float = 0.2,
        advantages: torch.Tensor | None = None,
        normalize_adv: bool = True,
    ) -> dict[str, torch.Tensor]:
        """Compute total weighted training loss and breakdown metrics."""
        # 1. Task / RL losses
        policy_loss, value_loss, entropy_loss = self.compute_policy_loss(
            action_log_probs=action_log_probs,
            action_entropies=action_entropies,
            values=values,
            returns=returns,
            old_action_log_probs=old_action_log_probs,
            clip_eps=clip_eps,
            advantages=advantages,
            normalize_adv=normalize_adv,
        )

        # 2. Communication penalty loss (Lagrangian dual)
        message_penalty, dual_loss = self.compute_message_penalty(report_probs)

        # 3. Forward model surprise loss
        if pred_obs is not None and actual_next_obs is not None:
            fwd_loss = self.compute_forward_model_loss(pred_obs, actual_next_obs)
        else:
            fwd_loss = torch.tensor(0.0, device=action_log_probs.device)

        # 4. Sparse consolidation loss
        if is_consolidation_step and consolidation_loss is not None:
            cons_loss = consolidation_loss
        else:
            cons_loss = torch.tensor(0.0, device=action_log_probs.device)

        # 5. Aggregate total loss (primal loss)
        total_loss = (
            policy_loss
            + self.value_loss_coef * value_loss
            + self.entropy_coef * entropy_loss
            + self.message_penalty_coef * message_penalty
            + self.forward_model_loss_coef * fwd_loss
            + self.consolidation_loss_coef * cons_loss
            + dual_loss
        )

        current_lambda = (
            float(self.gate_budgeter.lambda_val.item()) if (self.gate_budgeter is not None) else 1.0
        )

        return {
            "total_loss": total_loss,
            "policy_loss": policy_loss,
            "value_loss": value_loss,
            "entropy_loss": entropy_loss,
            "message_penalty": message_penalty,
            "dual_loss": dual_loss,
            "dual_lambda": current_lambda,
            "forward_model_loss": fwd_loss,
            "consolidation_loss": cons_loss,
            "report_rate": report_probs.mean().detach(),
        }
