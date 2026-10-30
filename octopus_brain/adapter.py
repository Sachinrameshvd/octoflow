"""Universal Gymnasium & PettingZoo Adapter for OctopusBrain.

Enables external developers, roboticists, and researchers to plug the OctopusBrain
architecture into any standard multi-agent reinforcement learning environment or
custom physics simulator (MuJoCo, PyBullet, Isaac Gym, or real soft robotics).
"""

import os
from typing import Any

import numpy as np
import torch

from octopus_brain.brain import OctopusBrain
from octopus_brain.config import OctopusBrainConfig
from octopus_brain.lexicon import InterBrachialLexiconDecoder

ACTION_NAMES = ["STAY", "UP", "DOWN", "LEFT", "RIGHT"]


class OctopusGymAdapter:
    """High-level controller interface wrapping OctopusBrain for standard Gym/Gymnasium envs.

    Features:
    - Zero-boilerplate interface: accepts numpy observation arrays directly.
    - Automatic shape normalization: accepts (N, obs_dim), (B, N, obs_dim), or 1D (D,) arrays.
    - Dynamic arm masking: easily sever or disable specific arms on the fly for fault-tolerance tests.
    - Rich behavioral telemetry: returns chosen actions, gating flags, dynamic coalition clusters,
      forward-model surprise values, Critic V(s) estimates, and decoded biological message intents.
    - Checkpoint loading: load trained weights from .pt or state dicts.
    """

    def __init__(
        self,
        model: OctopusBrain | None = None,
        config: OctopusBrainConfig | None = None,
        checkpoint_path: str | None = None,
        device: str | torch.device | None = None,
    ):
        if device is None:
            self.device = torch.device(
                "cuda"
                if torch.cuda.is_available()
                else "mps"
                if torch.backends.mps.is_available()
                else "cpu"
            )
        elif isinstance(device, str):
            self.device = torch.device(device)
        else:
            self.device = device

        self.config = config or (model.config if model is not None else OctopusBrainConfig())
        self.model = model or OctopusBrain(self.config)
        self.model.to(self.device)

        if checkpoint_path and os.path.exists(checkpoint_path):
            self.load_checkpoint(checkpoint_path)

        self.model.eval()
        self.lexicon = InterBrachialLexiconDecoder(message_dim=self.config.message_dim)
        self._current_batch_size = 1
        self.reset(batch_size=1)

    @property
    def n_arms(self) -> int:
        return self.config.n_modules

    @property
    def obs_dim(self) -> int:
        return self.config.obs_dim

    @property
    def action_dim(self) -> int:
        return self.config.action_dim

    def reset(self, batch_size: int = 1) -> None:
        """Reset internal recurrent states and central consolidation buffers."""
        self._current_batch_size = batch_size
        self.model.reset(batch_size=batch_size, device=self.device)

    def adapt_observation(self, observation: np.ndarray | torch.Tensor | list) -> torch.Tensor:
        """Universal observation normalizer.

        Maps 1D flat observations (e.g. CartPole (4,), Pendulum (3,)) or standard multi-arm
        observations (8, 16) into standard tensor shape (B, N, obs_dim).
        """
        if isinstance(observation, list):
            obs_np = np.array(observation, dtype=np.float32)
        elif isinstance(observation, np.ndarray):
            obs_np = observation.astype(np.float32)
        else:
            obs_np = observation.detach().cpu().numpy().astype(np.float32)

        # 1D flat observation (e.g. from standard classical control / box env)
        if obs_np.ndim == 1:
            total_len = obs_np.shape[0]
            adapted = np.zeros((self.n_arms, self.obs_dim), dtype=np.float32)
            # Partition or tile features across all arms
            for i in range(self.n_arms):
                start = (i * total_len) // self.n_arms
                end = ((i + 1) * total_len) // self.n_arms
                slice_len = min(self.obs_dim, end - start)
                if slice_len > 0:
                    adapted[i, :slice_len] = obs_np[start : start + slice_len]
                else:
                    # Tile
                    adapted[i, : min(total_len, self.obs_dim)] = obs_np[
                        : min(total_len, self.obs_dim)
                    ]
            obs_t = torch.tensor(adapted, dtype=torch.float32, device=self.device).unsqueeze(0)
            return obs_t

        obs_t = torch.tensor(obs_np, dtype=torch.float32, device=self.device)
        if obs_t.dim() == 2:
            obs_t = obs_t.unsqueeze(0)  # (1, N, obs_dim)

        return obs_t

    def predict(
        self,
        observation: np.ndarray | torch.Tensor | list,
        active_mask: np.ndarray | torch.Tensor | list[int] | None = None,
        deterministic: bool = True,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Compute actions for all peripheral arms given observations.

        Args:
            observation: (N, obs_dim), (B, N, obs_dim), or 1D (D,) sensory input.
            active_mask: Optional mask or list of active arm indices (e.g. [0, 1, 2, 4, 5, 6, 7] to sever arm 3).
            deterministic: True for greedy/argmax action execution; False for stochastic exploration.

        Returns:
            actions: (N,) or (B, N) discrete actions as a numpy array.
            info: Behavioral telemetry dictionary:
                - "report_events": (N,) boolean reporting flags.
                - "report_rate": float scalar communication rate.
                - "coalition_clusters": list of arm index tuples currently collaborating.
                - "active_coalitions": list of (arm_i, arm_j, weight) attention links.
                - "surprise_values": (N,) forward-model prediction errors.
                - "action_logits": (N, action_dim) policy logits.
                - "values": (N,) Critic state-value baselines V(s).
                - "action_names": (N,) human-readable action labels.
                - "decoded_intents": list of 8 decoded biological semantic message dictionaries.
                - "severed_arms": list of amputated/inactive arm indices.
        """
        is_unbatched = False
        if isinstance(observation, np.ndarray) and observation.ndim == 2:
            is_unbatched = True
        elif isinstance(observation, (list, tuple)) and (
            len(observation) > 0 and not isinstance(observation[0], (list, tuple))
        ):
            is_unbatched = True

        obs_t = self.adapt_observation(observation)
        batch_size = obs_t.size(0)

        if self.model.hidden_states is None or self._current_batch_size != batch_size:
            self.reset(batch_size=batch_size)

        # Parse active_mask
        mask_t = None
        severed_arms = []
        if active_mask is not None:
            if isinstance(active_mask, (list, tuple)):
                mask_np = np.zeros((batch_size, self.n_arms), dtype=bool)
                for idx in active_mask:
                    if 0 <= idx < self.n_arms:
                        mask_np[:, idx] = True
                mask_t = torch.tensor(mask_np, dtype=torch.bool, device=self.device)
                severed_arms = [i for i in range(self.n_arms) if i not in active_mask]
            elif isinstance(active_mask, np.ndarray):
                mask_t = torch.tensor(active_mask, dtype=torch.bool, device=self.device)
                if mask_t.dim() == 1:
                    mask_t = mask_t.unsqueeze(0).expand(batch_size, -1)
                severed_arms = [i for i, v in enumerate(active_mask) if not v]
            elif isinstance(active_mask, torch.Tensor):
                mask_t = active_mask.to(self.device).bool()
                if mask_t.dim() == 1:
                    mask_t = mask_t.unsqueeze(0).expand(batch_size, -1)
                severed_arms = [i for i, v in enumerate(mask_t[0].cpu().numpy()) if not v]

        # Step the brain
        with torch.no_grad():
            out = self.model.step(obs_t, active_mask=mask_t, deterministic=deterministic)

        # Extract actions and metrics as standard numpy objects
        actions_np = out["actions"].detach().cpu().numpy()
        report_events_np = out["report_events"].detach().cpu().numpy().astype(bool)
        surprise_np = out["surprise_values"].detach().cpu().numpy()
        values_np = out["values"].squeeze(-1).detach().cpu().numpy()

        # Enforce physical zeroing for amputated arms (stay = 0)
        if severed_arms:
            for s_idx in severed_arms:
                actions_np[..., s_idx] = 0

        # Decode semantic message chatter
        nbr_msgs = (
            self.model.prev_neighbor_msgs[0]
            if self.model.prev_neighbor_msgs is not None
            else torch.zeros(self.n_arms, self.config.message_dim, device=self.device)
        )
        rep_flags = report_events_np[0] if report_events_np.ndim > 1 else report_events_np
        decoded_intents = self.lexicon.decode_all_arms(nbr_msgs, report_flags=rep_flags)

        if is_unbatched or obs_t.size(0) == 1:
            actions_out = actions_np[0]
            report_out = report_events_np[0]
            surprise_out = surprise_np[0]
            values_out = values_np[0]
            action_names = [
                ACTION_NAMES[a] if 0 <= a < len(ACTION_NAMES) else "STAY" for a in actions_out
            ]
        else:
            actions_out = actions_np
            report_out = report_events_np
            surprise_out = surprise_np
            values_out = values_np
            action_names = [
                [ACTION_NAMES[a] if 0 <= a < len(ACTION_NAMES) else "STAY" for a in b_act]
                for b_act in actions_out
            ]

        info = {
            "report_events": report_out,
            "report_rate": float(out["report_rate"]),
            "coalition_clusters": out.get("coalition_clusters", []),
            "active_coalitions": out.get("active_coalitions", []),
            "surprise_values": surprise_out,
            "values": values_out,
            "action_names": action_names,
            "decoded_intents": decoded_intents,
            "action_logits": out["action_logits"].detach().cpu().numpy(),
            "is_consolidation_step": bool(out.get("is_consolidation_step", False)),
            "severed_arms": severed_arms,
        }

        return actions_out, info

    def load_checkpoint(self, path: str) -> None:
        """Load trained model weights from checkpoint file."""
        try:
            ckpt = torch.load(path, map_location=self.device, weights_only=True)
        except TypeError:
            ckpt = torch.load(path, map_location=self.device)

        if "model_state_dict" in ckpt:
            self.model.load_state_dict(ckpt["model_state_dict"])
        else:
            self.model.load_state_dict(ckpt)
        self.model.eval()
