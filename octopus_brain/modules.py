"""PeripheralModule: Distributed arm controller for OctopusBrain.

Each module corresponds to one peripheral sub-system (e.g. octopus arm-tip) with:
- A local recurrent state (GRU cell)
- A local actor-critic policy head
- A local forward-model predictive coding network computing sensory surprise
- A learnable event-trigger threshold deciding when to signal the central system
- Lateral neighbor communication projections
"""

from typing import Dict, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

from octopus_brain.config import OctopusBrainConfig


class PeripheralModule(nn.Module):
    """Autonomous peripheral module representing an octopus arm controller."""

    def __init__(self, module_id: int, config: OctopusBrainConfig):
        super().__init__()
        self.module_id = module_id
        self.config = config
        self.obs_dim = config.obs_dim
        self.action_dim = config.action_dim
        self.hidden_dim = config.hidden_dim
        self.message_dim = config.message_dim

        # Input dimension: observation + previous action one-hot + 2 neighbor messages + central feedback
        # 2 neighbor messages (left, right) -> 2 * message_dim
        # central feedback -> message_dim
        in_dim = self.obs_dim + self.action_dim + (2 * self.message_dim) + self.message_dim

        # Sensory & message preprocessor
        self.input_encoder = nn.Sequential(
            nn.Linear(in_dim, self.hidden_dim),
            nn.LayerNorm(self.hidden_dim),
            nn.Tanh(),
        )

        # Local recurrent working memory
        self.gru_cell = nn.GRUCell(self.hidden_dim, self.hidden_dim)

        # Local policy (Actor) and Value baseline (Critic)
        self.actor = nn.Sequential(
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.action_dim),
        )
        self.critic = nn.Sequential(
            nn.Linear(self.hidden_dim, self.hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(self.hidden_dim // 2, 1),
        )

        # Local forward predictive model: predicts next sensory observation from (h_t, action)
        self.forward_model = nn.Sequential(
            nn.Linear(self.hidden_dim + self.action_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.obs_dim),
        )

        # Learnable event-trigger threshold and gating head
        # Gate takes hidden state + surprise scalar -> logit
        self.gate_net = nn.Sequential(
            nn.Linear(self.hidden_dim + 1, self.hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(self.hidden_dim // 2, 1),
        )
        # Learnable threshold theta, initialized from config
        self.report_threshold = nn.Parameter(
            torch.tensor([float(config.report_threshold_init)], dtype=torch.float32)
        )

        # Lateral neighbor message projection
        self.neighbor_proj = nn.Sequential(
            nn.Linear(self.hidden_dim, self.message_dim),
            nn.Tanh(),
        )

        # Vertical central message projection
        self.central_msg_proj = nn.Sequential(
            nn.Linear(self.hidden_dim, self.message_dim),
            nn.Tanh(),
        )

    def init_hidden(self, batch_size: int, device: torch.device) -> torch.Tensor:
        """Initialize zero hidden state."""
        return torch.zeros(batch_size, self.hidden_dim, device=device)

    def forward(
        self,
        obs_t: torch.Tensor,
        prev_action: torch.Tensor,
        neighbor_in: torch.Tensor,
        central_feedback: torch.Tensor,
        h_prev: torch.Tensor,
        pred_obs_prev: Optional[torch.Tensor] = None,
        is_active: bool = True,
        deterministic: bool = False,
    ) -> Dict[str, torch.Tensor]:
        """Execute one forward step of the peripheral module.

        Args:
            obs_t: (B, obs_dim) Current sensory observation patch.
            prev_action: (B, action_dim) One-hot vector of previous action taken.
            neighbor_in: (B, 2 * message_dim) Lateral messages from ring neighbors.
            central_feedback: (B, message_dim) Top-down context from central system.
            h_prev: (B, hidden_dim) Previous recurrent hidden state.
            pred_obs_prev: (B, obs_dim) Forward model prediction from step t-1 for surprise.
            is_active: Whether this arm module is functional (for fault tolerance tests).
            deterministic: If True, greedy action selection and hard gating threshold.

        Returns:
            Dictionary containing actions, distributions, messages, surprise, gating, and predictions.
        """
        batch_size = obs_t.size(0)
        device = obs_t.device

        if not is_active:
            # Module has been severed / knocked out (fault tolerance testing)
            zeros_msg = torch.zeros(batch_size, self.message_dim, device=device)
            zeros_act = torch.zeros(batch_size, dtype=torch.long, device=device)
            zeros_onehot = torch.zeros(batch_size, self.action_dim, device=device)
            zeros_onehot[:, 0] = 1.0  # Default NOOP / stay
            return {
                "action": zeros_act,
                "action_onehot": zeros_onehot,
                "action_logits": torch.zeros(batch_size, self.action_dim, device=device),
                "action_log_prob": torch.zeros(batch_size, device=device),
                "action_entropy": torch.zeros(batch_size, device=device),
                "value": torch.zeros(batch_size, 1, device=device),
                "h_next": torch.zeros(batch_size, self.hidden_dim, device=device),
                "surprise": torch.zeros(batch_size, 1, device=device),
                "report_prob": torch.zeros(batch_size, 1, device=device),
                "report_flag": torch.zeros(batch_size, 1, device=device),
                "message_to_central": zeros_msg,
                "neighbor_message": zeros_msg,
                "pred_next_obs": torch.zeros(batch_size, self.obs_dim, device=device),
            }

        # 1. Compute Surprise Signal: difference between actual sensory input and prior prediction
        if pred_obs_prev is not None:
            # Normalized mean-squared prediction error
            diff = obs_t - pred_obs_prev
            surprise = torch.mean(diff ** 2, dim=-1, keepdim=True)  # (B, 1)
        else:
            surprise = torch.zeros(batch_size, 1, device=device)

        # 2. Encode sensory + message inputs
        combined_in = torch.cat([obs_t, prev_action, neighbor_in, central_feedback], dim=-1)
        encoded_in = self.input_encoder(combined_in)

        # 3. Update local recurrent state
        h_next = self.gru_cell(encoded_in, h_prev)

        # 4. Action selection via Actor-Critic
        logits = self.actor(h_next)
        value = self.critic(h_next)
        dist = Categorical(logits=logits)

        if deterministic:
            action = torch.argmax(logits, dim=-1)
        else:
            action = dist.sample()

        action_log_prob = dist.log_prob(action)
        action_entropy = dist.entropy()
        action_onehot = F.one_hot(action, num_classes=self.action_dim).float()

        # 5. Local forward model: predict observation for step t+1 from (h_next, action)
        fwd_in = torch.cat([h_next, action_onehot], dim=-1)
        pred_next_obs = self.forward_model(fwd_in)

        # 6. Event Trigger: calculate reporting probability and gating
        # Gate combines recurrent state representation and prediction surprise
        gate_input = torch.cat([h_next, surprise], dim=-1)
        gate_raw = self.gate_net(gate_input)  # (B, 1)
        gate_logit = (gate_raw - self.report_threshold) / max(self.config.tau, 1e-4)
        report_prob = torch.sigmoid(gate_logit)

        if deterministic:
            report_flag = (report_prob >= 0.5).float()
        else:
            # Straight-Through Gumbel / Sigmoid estimator for end-to-end differentiability
            hard_flag = (report_prob >= 0.5).float()
            # STE: In forward pass it acts as hard 0/1 gate; in backward pass gradients flow through report_prob
            report_flag = (hard_flag - report_prob).detach() + report_prob

        # 7. Generate outgoing messages
        neighbor_msg = self.neighbor_proj(h_next)
        raw_central_msg = self.central_msg_proj(h_next)
        # Message to central system is modulated by the event trigger gate
        message_to_central = raw_central_msg * report_flag

        return {
            "action": action,
            "action_onehot": action_onehot,
            "action_logits": logits,
            "action_log_prob": action_log_prob,
            "action_entropy": action_entropy,
            "value": value,
            "h_next": h_next,
            "surprise": surprise,
            "report_prob": report_prob,
            "report_flag": report_flag,
            "message_to_central": message_to_central,
            "neighbor_message": neighbor_msg,
            "pred_next_obs": pred_next_obs,
        }
