"""OctopusBrain: Complete modular neural architecture integrating peripheral modules and central system."""

from typing import Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
import torch.nn.functional as F

from octopus_brain.config import OctopusBrainConfig
from octopus_brain.modules import PeripheralModule
from octopus_brain.central import CentralSystem
from octopus_brain.coalition import extract_coalitions_from_matrix


class OctopusBrain(nn.Module):
    """Octopus-inspired modular brain with distributed peripheral processing

    and sparse, asynchronous central coalition consolidation.
    """

    def __init__(self, config: Optional[OctopusBrainConfig] = None):
        super().__init__()
        self.config = config or OctopusBrainConfig()
        self.n_modules = self.config.n_modules
        self.obs_dim = self.config.obs_dim
        self.action_dim = self.config.action_dim
        self.hidden_dim = self.config.hidden_dim
        self.message_dim = self.config.message_dim

        # Peripheral arm modules
        self.modules_list = nn.ModuleList([
            PeripheralModule(module_id=i, config=self.config)
            for i in range(self.n_modules)
        ])

        # Central consolidation system
        self.central_system = CentralSystem(config=self.config)

        # Internal state tracking for episodic execution
        self.hidden_states: Optional[List[torch.Tensor]] = None
        self.central_state: Optional[torch.Tensor] = None
        self.prev_actions: Optional[torch.Tensor] = None
        self.prev_pred_obs: Optional[torch.Tensor] = None
        self.prev_neighbor_msgs: Optional[torch.Tensor] = None
        self.prev_central_feedback: Optional[torch.Tensor] = None
        self.step_count: int = 0

    def reset(self, batch_size: int = 1, device: Optional[torch.device] = None) -> None:
        """Reset internal recurrent states and buffers at episode boundaries."""
        if device is None:
            device = next(self.parameters()).device

        self.hidden_states = [
            mod.init_hidden(batch_size, device) for mod in self.modules_list
        ]
        self.central_state = self.central_system.init_central_state(batch_size, device)
        self.prev_actions = torch.zeros(batch_size, self.n_modules, self.action_dim, device=device)
        self.prev_actions[:, :, 0] = 1.0  # Default one-hot action (stay)
        self.prev_pred_obs = torch.zeros(batch_size, self.n_modules, self.obs_dim, device=device)
        self.prev_neighbor_msgs = torch.zeros(
            batch_size, self.n_modules, self.message_dim, device=device
        )
        self.prev_central_feedback = torch.zeros(
            batch_size, self.n_modules, self.message_dim, device=device
        )
        self.central_system.reset_buffer()
        self.step_count = 0

    def _get_neighbor_inputs(self, neighbor_msgs: torch.Tensor) -> torch.Tensor:
        """Extract lateral incoming neighbor messages based on topology (default: ring).

        Args:
            neighbor_msgs: (B, N, message_dim)

        Returns:
            (B, N, 2 * message_dim) concatenated [left_neighbor_msg, right_neighbor_msg]
        """
        batch_size, n_mod, msg_dim = neighbor_msgs.size()

        if self.config.neighbor_topology == "ring":
            # Left neighbor: (i - 1) % N, Right neighbor: (i + 1) % N
            left_msgs = torch.roll(neighbor_msgs, shifts=1, dims=1)
            right_msgs = torch.roll(neighbor_msgs, shifts=-1, dims=1)
            return torch.cat([left_msgs, right_msgs], dim=-1)  # (B, N, 2 * message_dim)
        elif self.config.neighbor_topology == "line":
            # Non-periodic boundary
            left_pad = torch.zeros(batch_size, 1, msg_dim, device=neighbor_msgs.device)
            right_pad = torch.zeros(batch_size, 1, msg_dim, device=neighbor_msgs.device)
            left_msgs = torch.cat([left_pad, neighbor_msgs[:, :-1, :]], dim=1)
            right_msgs = torch.cat([neighbor_msgs[:, 1:, :], right_pad], dim=1)
            return torch.cat([left_msgs, right_msgs], dim=-1)
        else:
            # Full topology: fallback to ring
            left_msgs = torch.roll(neighbor_msgs, shifts=1, dims=1)
            right_msgs = torch.roll(neighbor_msgs, shifts=-1, dims=1)
            return torch.cat([left_msgs, right_msgs], dim=-1)

    def step(
        self,
        obs: torch.Tensor,
        active_mask: Optional[torch.Tensor] = None,
        deterministic: bool = False,
        disable_central: bool = False,
        force_report_all: bool = False,
    ) -> Dict[str, Union[torch.Tensor, float, bool, List]]:
        """Perform one synchronous environment step across all distributed modules.

        Args:
            obs: (B, N, obs_dim) Sensory observations for all N modules.
            active_mask: (B, N) or (N,) Optional boolean/float mask indicating functioning modules.
            deterministic: If True, uses greedy action sampling and hard thresholding.
            disable_central: If True, completely bypasses central coalition system (Always Local baseline).
            force_report_all: If True, forces all modules to report every step (Synchronous baseline).

        Returns:
            Dictionary with actions, distributions, diagnostics (report events, surprise, coalitions).
        """
        batch_size, n_mod, obs_dim = obs.size()
        device = obs.device

        if self.hidden_states is None:
            self.reset(batch_size=batch_size, device=device)

        if active_mask is None:
            active_mask = torch.ones(batch_size, n_mod, dtype=torch.bool, device=device)
        elif active_mask.dim() == 1:
            active_mask = active_mask.unsqueeze(0).expand(batch_size, -1)

        # 1. Prepare lateral neighbor inputs from previous step's neighbor messages
        neighbor_inputs = self._get_neighbor_inputs(self.prev_neighbor_msgs)  # (B, N, 2 * msg_dim)

        # 2. Step each peripheral module
        module_outputs = []
        new_hidden_states = []

        for i in range(self.n_modules):
            mod_active = active_mask[:, i].all().item()
            out_i = self.modules_list[i](
                obs_t=obs[:, i, :],
                prev_action=self.prev_actions[:, i, :],
                neighbor_in=neighbor_inputs[:, i, :],
                central_feedback=self.prev_central_feedback[:, i, :],
                h_prev=self.hidden_states[i],
                pred_obs_prev=self.prev_pred_obs[:, i, :],
                is_active=mod_active,
                deterministic=deterministic,
            )
            module_outputs.append(out_i)
            new_hidden_states.append(out_i["h_next"])

        # 3. Collate module outputs
        actions = torch.stack([out["action"] for out in module_outputs], dim=1)  # (B, N)
        actions_onehot = torch.stack([out["action_onehot"] for out in module_outputs], dim=1)  # (B, N, action_dim)
        action_logits = torch.stack([out["action_logits"] for out in module_outputs], dim=1)  # (B, N, action_dim)
        action_log_probs = torch.stack([out["action_log_prob"] for out in module_outputs], dim=1)  # (B, N)
        action_entropies = torch.stack([out["action_entropy"] for out in module_outputs], dim=1)  # (B, N)
        values = torch.stack([out["value"] for out in module_outputs], dim=1)  # (B, N, 1)
        surprises = torch.stack([out["surprise"] for out in module_outputs], dim=1).squeeze(-1)  # (B, N)
        report_probs = torch.stack([out["report_prob"] for out in module_outputs], dim=1).squeeze(-1)  # (B, N)
        report_flags = torch.stack([out["report_flag"] for out in module_outputs], dim=1).squeeze(-1)  # (B, N)
        central_msgs = torch.stack([out["message_to_central"] for out in module_outputs], dim=1)  # (B, N, msg_dim)
        neighbor_msgs = torch.stack([out["neighbor_message"] for out in module_outputs], dim=1)  # (B, N, msg_dim)
        pred_next_obs = torch.stack([out["pred_next_obs"] for out in module_outputs], dim=1)  # (B, N, obs_dim)

        if force_report_all:
            # Baseline 2: Synchronous always-communicating architecture
            report_flags = torch.ones_like(report_flags)
            # Central messages generated unconditionally
            central_msgs = torch.stack([
                self.modules_list[i].central_msg_proj(module_outputs[i]["h_next"])
                for i in range(self.n_modules)
            ], dim=1)

        # 4. Central System Execution
        central_out = self.central_system(
            messages=central_msgs,
            report_flags=report_flags,
            central_state=self.central_state,
            step_count=self.step_count + 1,
            is_ablated=disable_central,
        )

        central_feedback = central_out["central_feedback"]  # (B, N, msg_dim)
        new_central_state = central_out["central_state"]  # (B, central_dim)
        coalition_matrix = central_out["coalition_matrix"]  # (B, N, N)
        is_consolidation = central_out["is_consolidation_step"]
        consolidation_loss = central_out["consolidation_loss"]

        # 5. Extract Discrete Coalition Graphs & Connected Components
        coalition_graph_info = {"active_coalitions": [], "isolated_modules": list(range(self.n_modules)), "edge_list": []}
        active_coalition_pairs = []
        if coalition_matrix.numel() > 0:
            mean_coalition = coalition_matrix.mean(dim=0).detach().cpu().numpy()  # (N, N)
            coalition_graph_info = extract_coalitions_from_matrix(mean_coalition, threshold=0.15)
            active_coalition_pairs = [
                (i, j, float(w)) for i, j, w in coalition_graph_info["edge_list"]
            ]

        # 6. Update step state for next timestep
        self.hidden_states = new_hidden_states
        self.central_state = new_central_state
        self.prev_actions = actions_onehot
        self.prev_pred_obs = pred_next_obs
        self.prev_neighbor_msgs = neighbor_msgs
        self.prev_central_feedback = central_feedback
        self.step_count += 1

        # Mean report rate across batch and modules
        mean_report_rate = float(report_flags.float().mean().item())

        return {
            "actions": actions,
            "action_logits": action_logits,
            "action_log_probs": action_log_probs,
            "action_entropies": action_entropies,
            "values": values,
            "report_events": report_flags,
            "report_probs": report_probs,
            "report_rate": mean_report_rate,
            "coalition_matrix": coalition_matrix,
            "active_coalitions": active_coalition_pairs,
            "coalition_clusters": coalition_graph_info["active_coalitions"],
            "coalition_graph": coalition_graph_info,
            "surprise_values": surprises,
            "is_consolidation_step": is_consolidation,
            "consolidation_loss": consolidation_loss,
            "pred_next_obs": pred_next_obs,
            "central_feedback": central_feedback,
            "step_count": self.step_count,
        }

    def forward(
        self,
        obs: torch.Tensor,
        active_mask: Optional[torch.Tensor] = None,
        deterministic: bool = False,
        disable_central: bool = False,
        force_report_all: bool = False,
    ) -> Dict[str, Union[torch.Tensor, float, bool, List]]:
        """PyTorch nn.Module forward pass alias routing to step."""
        return self.step(
            obs=obs,
            active_mask=active_mask,
            deterministic=deterministic,
            disable_central=disable_central,
            force_report_all=force_report_all,
        )
