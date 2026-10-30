"""Baseline ablations for OctopusBrain research benchmarking.

Three required ablations to isolate causal factors:
1. DenseCentralizedBaseline:
   - Centralized dense policy observing all arms simultaneously
   - Parameter-matched to OctopusBrain
2. SynchronousFullCommBaseline:
   - Synchronous always-communicating version of OctopusBrain (r_i == 1 at all times)
3. AlwaysLocalBaseline:
   - Modular peripheral modules with ring neighbor passing, but central coalition system disabled (r_i == 0)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from octopus_brain.brain import OctopusBrain
from octopus_brain.config import OctopusBrainConfig
from torch.distributions import Categorical


class DenseCentralizedBaseline(nn.Module):
    """Ablation 1: Dense centralized policy with matched parameter budget.

    Takes concatenated observations from all arms and outputs joint actions.
    """

    def __init__(self, config: OctopusBrainConfig | None = None):
        super().__init__()
        self.config = config or OctopusBrainConfig()
        self.n_modules = self.config.n_modules
        self.obs_dim = self.config.obs_dim
        self.action_dim = self.config.action_dim

        total_obs_dim = self.n_modules * self.obs_dim
        total_act_dim = self.n_modules * self.action_dim

        # Compute parameter target from OctopusBrain to match capacity
        ref_brain = OctopusBrain(self.config)
        target_params = sum(p.numel() for p in ref_brain.parameters())

        # Size hidden dimension to match target_params closely
        # Encoder + GRU + Actor-Critic + Value heads
        hidden_dim = int(np_hidden := max(128, int((target_params / 4) ** 0.5)))
        self.hidden_dim = hidden_dim

        self.encoder = nn.Sequential(
            nn.Linear(total_obs_dim + total_act_dim, self.hidden_dim),
            nn.LayerNorm(self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.ReLU(),
        )

        self.gru = nn.GRUCell(self.hidden_dim, self.hidden_dim)

        self.actor_heads = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Linear(self.hidden_dim, self.hidden_dim // 2),
                    nn.ReLU(),
                    nn.Linear(self.hidden_dim // 2, self.action_dim),
                )
                for _ in range(self.n_modules)
            ]
        )

        self.critic = nn.Sequential(
            nn.Linear(self.hidden_dim, self.hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(self.hidden_dim // 2, 1),
        )

        self.hidden_state: torch.Tensor | None = None
        self.prev_actions: torch.Tensor | None = None
        self.step_count: int = 0

    def reset(self, batch_size: int = 1, device: torch.device | None = None) -> None:
        """Reset internal recurrent state."""
        if device is None:
            device = next(self.parameters()).device
        self.hidden_state = torch.zeros(batch_size, self.hidden_dim, device=device)
        self.prev_actions = torch.zeros(batch_size, self.n_modules * self.action_dim, device=device)
        self.step_count = 0

    def step(
        self,
        obs: torch.Tensor,
        active_mask: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> dict[str, torch.Tensor | float | bool | list]:
        """Execute one centralized step.

        Args:
            obs: (B, N, obs_dim)
            active_mask: (B, N)
            deterministic: bool
        """
        batch_size, n_mod, obs_dim = obs.size()
        device = obs.device

        if self.hidden_state is None:
            self.reset(batch_size, device)

        # Zero out observations for inactive / killed modules
        if active_mask is not None:
            if active_mask.dim() == 1:
                active_mask = active_mask.unsqueeze(0).expand(batch_size, -1)
            obs = obs * active_mask.unsqueeze(-1).float()

        flat_obs = obs.view(batch_size, -1)  # (B, N * obs_dim)
        combined_in = torch.cat([flat_obs, self.prev_actions], dim=-1)

        encoded = self.encoder(combined_in)
        self.hidden_state = self.gru(encoded, self.hidden_state)

        action_list = []
        logits_list = []
        log_prob_list = []
        entropy_list = []
        action_onehots = []

        for i in range(self.n_modules):
            logits = self.actor_heads[i](self.hidden_state)
            dist = Categorical(logits=logits)
            if deterministic:
                act = torch.argmax(logits, dim=-1)
            else:
                act = dist.sample()

            if active_mask is not None and not active_mask[:, i].all().item():
                # Inactive module forced to 0
                act = torch.zeros_like(act)

            action_list.append(act)
            logits_list.append(logits)
            log_prob_list.append(dist.log_prob(act))
            entropy_list.append(dist.entropy())
            action_onehots.append(F.one_hot(act, num_classes=self.action_dim).float())

        actions = torch.stack(action_list, dim=1)  # (B, N)
        action_logits = torch.stack(logits_list, dim=1)
        action_log_probs = torch.stack(log_prob_list, dim=1)
        action_entropies = torch.stack(entropy_list, dim=1)
        values = self.critic(self.hidden_state).unsqueeze(1).expand(-1, self.n_modules, -1)

        self.prev_actions = torch.cat(action_onehots, dim=-1).detach()
        self.step_count += 1

        # Central baseline has no internal modular coalitions / gating
        dummy_coalition = torch.zeros(batch_size, self.n_modules, self.n_modules, device=device)
        dummy_reports = torch.ones(batch_size, self.n_modules, device=device)  # 100% centralized

        return {
            "actions": actions,
            "action_logits": action_logits,
            "action_log_probs": action_log_probs,
            "action_entropies": action_entropies,
            "values": values,
            "report_events": dummy_reports,
            "report_probs": dummy_reports,
            "report_rate": 1.0,  # Always central
            "coalition_matrix": dummy_coalition,
            "active_coalitions": [],
            "surprise_values": torch.zeros(batch_size, self.n_modules, device=device),
            "is_consolidation_step": False,
            "consolidation_loss": torch.tensor(0.0, device=device),
            "pred_next_obs": torch.zeros_like(obs),
            "step_count": self.step_count,
        }


class SynchronousFullCommBaseline(OctopusBrain):
    """Ablation 2: Synchronous always-communicating version of OctopusBrain.

    All modules report every single timestep (r_i == 1), with central attention active continuously.
    """

    def step(
        self,
        obs: torch.Tensor,
        active_mask: torch.Tensor | None = None,
        deterministic: bool = False,
        disable_central: bool = False,
        force_report_all: bool = True,
    ) -> dict[str, torch.Tensor | float | bool | list]:
        return super().step(
            obs=obs,
            active_mask=active_mask,
            deterministic=deterministic,
            disable_central=False,
            force_report_all=True,  # 100% communication rate forced
        )


class AlwaysLocalBaseline(OctopusBrain):
    """Ablation 3: Never coalesce, always local version of OctopusBrain.

    Modules communicate laterally with ring neighbors, but central coalition attention
    and central consolidation are permanently disabled (r_i == 0).
    """

    def step(
        self,
        obs: torch.Tensor,
        active_mask: torch.Tensor | None = None,
        deterministic: bool = False,
        disable_central: bool = True,
        force_report_all: bool = False,
    ) -> dict[str, torch.Tensor | float | bool | list]:
        return super().step(
            obs=obs,
            active_mask=active_mask,
            deterministic=deterministic,
            disable_central=True,  # Central system ablated
            force_report_all=False,
        )
