"""Configuration dataclasses for OctopusBrain architecture and experiments."""

from dataclasses import dataclass


@dataclass
class OctopusBrainConfig:
    """Configuration for OctopusBrain neural architecture.

    Parameters:
        n_modules: Number of peripheral arm modules (e.g. 4 to 8).
        obs_dim: Dimension of local sensory observation patch for each module.
        action_dim: Dimension of discrete action space per module (e.g. 5: Up, Down, Left, Right, Stay/Act).
        hidden_dim: Hidden dimension of peripheral module local GRU and embeddings.
        message_dim: Dimension of messages exchanged laterally between neighbors and vertically to central system.
        central_dim: Dimension of central memory and consolidation state.
        num_heads: Number of attention heads in central coalition attention.
        consolidation_every: Time horizon interval K for slow central consolidation updates (sparse clock).
        report_threshold_init: Initial value for learnable event-trigger threshold theta.
        tau: Temperature parameter for gating sigmoid / Gumbel relaxation.
        neighbor_topology: Graph topology for lateral message passing ('ring', 'line', 'full').
        message_penalty_coef: Loss coefficient penalizing high reporting frequency to prevent gate collapse.
        target_report_rate: Optional target report rate set-point (e.g. 0.25).
        consolidation_loss_coef: Weight for slow central consolidation loss.
        forward_model_loss_coef: Weight for local forward-model prediction (surprise) loss.
        entropy_coef: Entropy bonus weight for policy exploration.
        value_loss_coef: Weight for actor-critic value baseline loss.
        learning_rate: Base optimizer learning rate.
    """

    n_modules: int = 8
    obs_dim: int = 16
    action_dim: int = 5
    hidden_dim: int = 64
    message_dim: int = 32
    central_dim: int = 64
    num_heads: int = 4
    consolidation_every: int = 5
    report_threshold_init: float = -0.2
    tau: float = 1.0
    neighbor_topology: str = "ring"
    message_penalty_coef: float = 0.05
    target_report_rate: float = 0.25
    consolidation_loss_coef: float = 0.1
    forward_model_loss_coef: float = 0.2
    entropy_coef: float = 0.01
    value_loss_coef: float = 0.5
    learning_rate: float = 0.001
    adaptive_budgeting: bool = True
    lagrange_lr: float = 0.05
    lagrange_init: float = 0.1


@dataclass
class EnvConfig:
    """Configuration for ReachAndAvoid multi-arm gridworld."""

    grid_size: int = 14
    n_arms: int = 8
    arm_reach: int = 4
    n_single_targets: int = 4
    n_joint_targets: int = 2
    n_hazards: int = 3
    max_steps: int = 50
    patch_radius: int = 2
    joint_require_simultaneous: bool = True
    cooperation_reward: float = 5.0
    single_reward: float = 1.5
    hazard_penalty: float = -2.0
    step_penalty: float = -0.02
    delayed_cue_mode: bool = False


# Allow safe unpickling of configuration classes under PyTorch >=2.6 weights_only=True
try:
    import torch

    if hasattr(torch.serialization, "add_safe_globals"):
        torch.serialization.add_safe_globals([OctopusBrainConfig, EnvConfig])
except Exception:
    pass
