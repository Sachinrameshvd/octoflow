"""CentralSystem: Non-controlling central memory and coalition attention system.

Features:
- Dynamic Coalition Attention computed strictly over reporting modules
- Pairwise binding matrix generation (for tracking temporary coalitions)
- Slow, sparse consolidation update (triggered periodically every K steps, not every timestep)
- Top-down contextual feedback broadcast only to active reporting modules
"""

from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

from octopus_brain.config import OctopusBrainConfig


class CentralSystem(nn.Module):
    """Central consolidation and coalition binding module."""

    def __init__(self, config: OctopusBrainConfig):
        super().__init__()
        self.config = config
        self.n_modules = config.n_modules
        self.message_dim = config.message_dim
        self.central_dim = config.central_dim
        self.num_heads = config.num_heads
        self.consolidation_every = config.consolidation_every

        # Projection for keys, queries, values in coalition attention
        self.q_proj = nn.Linear(self.message_dim, self.message_dim)
        self.k_proj = nn.Linear(self.message_dim, self.message_dim)
        self.v_proj = nn.Linear(self.message_dim, self.message_dim)
        self.out_proj = nn.Linear(self.message_dim, self.message_dim)

        # Contextual feedback projection (back to peripheral modules)
        self.feedback_proj = nn.Sequential(
            nn.Linear(self.message_dim + self.central_dim, self.message_dim),
            nn.LayerNorm(self.message_dim),
            nn.Tanh(),
        )

        # Slow central consolidation recurrent unit
        self.slow_gru = nn.GRUCell(self.message_dim, self.central_dim)

        # Long-horizon predictive / associative consolidation decoder
        self.consolidation_decoder = nn.Sequential(
            nn.Linear(self.central_dim, self.message_dim),
            nn.ReLU(),
            nn.Linear(self.message_dim, self.message_dim),
        )

        # Trajectory buffer to hold step-level summaries between consolidation intervals
        self.buffer: List[torch.Tensor] = []

    def init_central_state(self, batch_size: int, device: torch.device) -> torch.Tensor:
        """Initialize slow central memory state."""
        return torch.zeros(batch_size, self.central_dim, device=device)

    def reset_buffer(self) -> None:
        """Clear consolidation trajectory buffer."""
        self.buffer = []

    def forward(
        self,
        messages: torch.Tensor,
        report_flags: torch.Tensor,
        central_state: torch.Tensor,
        step_count: int,
        is_ablated: bool = False,
    ) -> Dict[str, torch.Tensor]:
        """Compute coalition attention and sparse consolidation.

        Args:
            messages: (B, N, message_dim) Messages from all peripheral modules.
            report_flags: (B, N, 1) or (B, N) Binary/soft gating indicator of reporting modules.
            central_state: (B, central_dim) Current slow central memory state.
            step_count: Current timestep within episode.
            is_ablated: If True, completely disable central system (Always Local baseline).

        Returns:
            Dictionary containing:
                - central_feedback: (B, N, message_dim) Feedback vectors to peripheral modules.
                - central_state: (B, central_dim) Updated slow central state.
                - coalition_matrix: (B, N, N) Pairwise attention binding weights.
                - is_consolidation_step: bool.
                - consolidation_loss: scalar tensor (0.0 on non-consolidation steps).
                - active_module_count: (B, 1) count of reporting modules.
        """
        batch_size, n_mod, msg_dim = messages.size()
        device = messages.device

        if report_flags.dim() == 2:
            report_flags = report_flags.unsqueeze(-1)  # (B, N, 1)

        if is_ablated:
            # Central ablation (Always Local mode)
            zeros_feedback = torch.zeros(batch_size, n_mod, msg_dim, device=device)
            zeros_coalition = torch.zeros(batch_size, n_mod, n_mod, device=device)
            return {
                "central_feedback": zeros_feedback,
                "central_state": central_state,
                "coalition_matrix": zeros_coalition,
                "is_consolidation_step": False,
                "consolidation_loss": torch.tensor(0.0, device=device),
                "active_module_count": torch.zeros(batch_size, 1, device=device),
            }

        # 1. Coalition Attention over Reporting Modules
        # Mask out non-reporting modules so attention is computed ONLY over reporting modules
        # report_mask: (B, N) -> True where module reports (report_flags > 0.1)
        reporting_mask = (report_flags.squeeze(-1) > 0.1)  # (B, N) bool
        active_counts = reporting_mask.float().sum(dim=-1, keepdim=True)  # (B, 1)

        # Multi-head coalition attention
        # Q, K, V: (B, N, message_dim)
        Q = self.q_proj(messages)
        K = self.k_proj(messages)
        V = self.v_proj(messages)

        # Reshape for multi-head: (B, H, N, D_head)
        H = self.num_heads
        d_k = msg_dim // H

        Q_h = Q.view(batch_size, n_mod, H, d_k).transpose(1, 2)  # (B, H, N, d_k)
        K_h = K.view(batch_size, n_mod, H, d_k).transpose(1, 2)  # (B, H, N, d_k)
        V_h = V.view(batch_size, n_mod, H, d_k).transpose(1, 2)  # (B, H, N, d_k)

        # Raw attention scores: (B, H, N, N)
        scores = torch.matmul(Q_h, K_h.transpose(-2, -1)) / (d_k ** 0.5)

        # Create key mask: where key module is NOT reporting, score = -1e9
        # reporting_mask: (B, N) -> expand to (B, 1, 1, N)
        key_mask = (~reporting_mask).unsqueeze(1).unsqueeze(2)  # (B, 1, 1, N)
        scores = scores.masked_fill(key_mask, -1e9)

        # Softmax over key dimension
        attn_weights = F.softmax(scores, dim=-1)  # (B, H, N, N)

        # Zero out attention rows for queries that are NOT reporting
        query_mask = reporting_mask.unsqueeze(1).unsqueeze(-1)  # (B, 1, N, 1)
        attn_weights = attn_weights * query_mask.float()

        # Weighted values
        attended = torch.matmul(attn_weights, V_h)  # (B, H, N, d_k)
        attended = attended.transpose(1, 2).contiguous().view(batch_size, n_mod, msg_dim)
        attended = self.out_proj(attended)  # (B, N, message_dim)

        # Mean coalition matrix across attention heads for diagnostics: (B, N, N)
        coalition_matrix = attn_weights.mean(dim=1)  # (B, N, N)

        # 2. Central Feedback Generation
        # Combine attended coalition context with slow central state broadcast
        central_broadcast = central_state.unsqueeze(1).expand(-1, n_mod, -1)  # (B, N, central_dim)
        feedback_in = torch.cat([attended, central_broadcast], dim=-1)
        raw_feedback = self.feedback_proj(feedback_in)  # (B, N, message_dim)

        # Top-down feedback is routed ONLY to reporting modules
        central_feedback = raw_feedback * report_flags  # (B, N, message_dim)

        # 3. Buffer Step Summary for Slow Consolidation
        # Summarize current reporting events across active modules: (B, message_dim)
        # Safe mean over active reporting modules
        safe_divisor = torch.clamp(active_counts, min=1.0)
        step_summary = (attended * report_flags).sum(dim=1) / safe_divisor  # (B, message_dim)
        self.buffer.append(step_summary)

        # 4. Sparse Slow Consolidation Update
        is_consolidation = (step_count > 0) and (step_count % self.consolidation_every == 0)
        consolidation_loss = torch.tensor(0.0, device=device)

        if is_consolidation and len(self.buffer) > 0:
            # Pool trajectory buffer over the last K steps
            stacked_buffer = torch.stack(self.buffer, dim=1)  # (B, K, message_dim)
            pooled_summary = torch.mean(stacked_buffer, dim=1)  # (B, message_dim)

            # Update slow central recurrent memory
            new_central_state = self.slow_gru(pooled_summary, central_state)

            # Consolidation associative reconstruction / predictive loss:
            # Slow memory decodes the pooled experience summary
            reconstructed = self.consolidation_decoder(new_central_state)
            consolidation_loss = F.mse_loss(reconstructed, pooled_summary)

            central_state = new_central_state
            self.reset_buffer()

        return {
            "central_feedback": central_feedback,
            "central_state": central_state,
            "coalition_matrix": coalition_matrix,
            "is_consolidation_step": is_consolidation,
            "consolidation_loss": consolidation_loss,
            "active_module_count": active_counts,
        }
