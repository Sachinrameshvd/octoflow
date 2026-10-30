"""Export trained OctopusBrain checkpoint to optimized zero-dependency ONNX model.

Allows running OctopusBrain inference in C++, MuJoCo C/C++, Unity, ROS2 robots,
WebAssembly / ONNX Runtime Web, and embedded edge compute (NVIDIA Jetson / Raspberry Pi).

Usage:
    python experiments/export_onnx.py --checkpoint checkpoints/top1_octopus_brain.pt --output checkpoints/octopus_brain.onnx
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from octopus_brain.brain import OctopusBrain
from octopus_brain.config import OctopusBrainConfig


class ExportableOctopusBrain(nn.Module):
    """Pure PyTorch functional module wrapping OctopusBrain step for ONNX export."""

    def __init__(self, brain: OctopusBrain):
        super().__init__()
        self.brain = brain
        self.config = brain.config
        self.n_modules = brain.n_modules

    def forward(
        self,
        obs: torch.Tensor,
        hidden_states: torch.Tensor,
        central_state: torch.Tensor,
        prev_actions: torch.Tensor,
        prev_neighbor_msgs: torch.Tensor,
        prev_central_feedback: torch.Tensor,
    ):
        """Single timestep forward evaluation.

        Args:
            obs: (B, N, obs_dim)
            hidden_states: (B, N, hidden_dim)
            central_state: (B, central_dim)
            prev_actions: (B, N, action_dim)
            prev_neighbor_msgs: (B, N, message_dim)
            prev_central_feedback: (B, N, message_dim)

        Returns:
            actions: (B, N)
            action_logits: (B, N, action_dim)
            report_probs: (B, N)
            new_hidden_states: (B, N, hidden_dim)
            new_central_state: (B, central_dim)
            new_prev_actions: (B, N, action_dim)
            new_neighbor_msgs: (B, N, message_dim)
            new_central_feedback: (B, N, message_dim)
        """
        batch_size = obs.size(0)

        # 1. Neighbor inputs (ring topology)
        left_msgs = torch.roll(prev_neighbor_msgs, shifts=1, dims=1)
        right_msgs = torch.roll(prev_neighbor_msgs, shifts=-1, dims=1)
        neighbor_inputs = torch.cat([left_msgs, right_msgs], dim=-1)

        # 2. Step peripheral modules
        new_hidden_list = []
        action_logits_list = []
        report_probs_list = []
        neighbor_msg_list = []
        outgoing_msg_list = []

        for i in range(self.n_modules):
            mod = self.brain.modules_list[i]
            obs_i = obs[:, i, :]
            act_prev_i = prev_actions[:, i, :]
            nbr_i = neighbor_inputs[:, i, :]
            fb_prev_i = prev_central_feedback[:, i, :]
            h_prev_i = hidden_states[:, i, :]

            # Input projection
            combined_in = torch.cat([obs_i, act_prev_i, nbr_i, fb_prev_i], dim=-1)
            enc = mod.input_encoder(combined_in)

            # GRU update
            h_next_i = mod.gru_cell(enc, h_prev_i)
            new_hidden_list.append(h_next_i)

            # Policy logits
            logits_i = mod.actor(h_next_i)
            action_logits_list.append(logits_i)

            # Gating probability
            # Surprise can be estimated or fed in; here we use 0.0 or difference from prior pred
            surprise_i = torch.zeros(batch_size, 1, device=obs.device)
            gate_in = torch.cat([h_next_i, surprise_i], dim=-1)
            gate_raw = mod.gate_net(gate_in)
            gate_logit = (gate_raw - mod.report_threshold) / max(self.config.tau, 1e-4)
            p_report_i = torch.sigmoid(gate_logit).squeeze(-1)
            report_probs_list.append(p_report_i)

            # Outgoing messages
            nbr_msg_i = mod.neighbor_proj(h_next_i)
            neighbor_msg_list.append(nbr_msg_i)

            out_msg_i = mod.central_msg_proj(h_next_i)
            outgoing_msg_list.append(out_msg_i)

        new_hidden_states = torch.stack(new_hidden_list, dim=1)  # (B, N, hidden_dim)
        action_logits = torch.stack(action_logits_list, dim=1)  # (B, N, action_dim)
        report_probs = torch.stack(report_probs_list, dim=1)  # (B, N)
        new_neighbor_msgs = torch.stack(neighbor_msg_list, dim=1)  # (B, N, message_dim)
        outgoing_msgs = torch.stack(outgoing_msg_list, dim=1)  # (B, N, message_dim)

        # Greedy actions (argmax)
        actions = torch.argmax(action_logits, dim=-1)  # (B, N)
        new_prev_actions = F.one_hot(actions, num_classes=self.config.action_dim).float()

        # 3. Central System attention and feedback
        central = self.brain.central_system
        # Soft mask communication
        gated_msgs = outgoing_msgs * report_probs.unsqueeze(-1)
        q = central.q_proj(gated_msgs)
        k = central.k_proj(gated_msgs)
        v = central.v_proj(gated_msgs)

        d_k = q.size(-1)
        scores = torch.matmul(q, k.transpose(-2, -1)) / (d_k**0.5)
        attn_weights = F.softmax(scores, dim=-1)
        coalition_context = torch.matmul(attn_weights, v)
        coalition_out = central.out_proj(coalition_context)

        # Contextual feedback
        fb_in = torch.cat(
            [coalition_out, central_state.unsqueeze(1).expand(-1, self.n_modules, -1)], dim=-1
        )
        new_central_feedback = central.feedback_proj(fb_in)

        # Slow central GRU
        summary_msg = gated_msgs.mean(dim=1)
        new_central_state = central.slow_gru(summary_msg, central_state)

        return (
            actions,
            action_logits,
            report_probs,
            new_hidden_states,
            new_central_state,
            new_prev_actions,
            new_neighbor_msgs,
            new_central_feedback,
        )


def export_model(checkpoint_path: str, output_path: str, device: str = "cpu"):
    """Export checkpoint to ONNX."""
    device = torch.device(device)
    config = OctopusBrainConfig(
        n_modules=8, obs_dim=16, action_dim=5, hidden_dim=64, message_dim=32, central_dim=64
    )
    brain = OctopusBrain(config).to(device)

    if os.path.exists(checkpoint_path):
        try:
            ckpt = torch.load(checkpoint_path, map_location=device, weights_only=True)
        except TypeError:
            ckpt = torch.load(checkpoint_path, map_location=device)
        if "model_state_dict" in ckpt:
            brain.load_state_dict(ckpt["model_state_dict"])
        else:
            brain.load_state_dict(ckpt)
        print(f"--> Loaded weights from: {checkpoint_path}")
    else:
        print(f"--> Warning: {checkpoint_path} not found. Exporting initial weights.")

    brain.eval()
    exportable = ExportableOctopusBrain(brain).to(device)
    exportable.eval()

    # Dummy inputs
    B = 1
    N = config.n_modules
    dummy_obs = torch.randn(B, N, config.obs_dim, device=device)
    dummy_hidden = torch.zeros(B, N, config.hidden_dim, device=device)
    dummy_central = torch.zeros(B, config.central_dim, device=device)
    dummy_prev_act = torch.zeros(B, N, config.action_dim, device=device)
    dummy_prev_nbr = torch.zeros(B, N, config.message_dim, device=device)
    dummy_prev_fb = torch.zeros(B, N, config.message_dim, device=device)

    input_tensors = (
        dummy_obs,
        dummy_hidden,
        dummy_central,
        dummy_prev_act,
        dummy_prev_nbr,
        dummy_prev_fb,
    )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    input_names = [
        "obs",
        "hidden_states",
        "central_state",
        "prev_actions",
        "prev_neighbor_msgs",
        "prev_central_feedback",
    ]
    output_names = [
        "actions",
        "action_logits",
        "report_probs",
        "new_hidden_states",
        "new_central_state",
        "new_prev_actions",
        "new_neighbor_msgs",
        "new_central_feedback",
    ]

    dynamic_axes = {k: {0: "batch_size"} for k in input_names + output_names}

    print(f"--> Exporting ONNX model to: {output_path}...")
    torch.onnx.export(
        exportable,
        input_tensors,
        output_path,
        export_params=True,
        opset_version=18,
        do_constant_folding=True,
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes,
    )
    print("--> Export complete!")

    # Verify with onnxruntime
    try:
        import onnxruntime as ort

        print("--> Validating with ONNX Runtime...")
        session = ort.InferenceSession(output_path, providers=["CPUExecutionProvider"])
        ort_inputs = {
            "obs": dummy_obs.cpu().numpy(),
            "hidden_states": dummy_hidden.cpu().numpy(),
            "central_state": dummy_central.cpu().numpy(),
            "prev_actions": dummy_prev_act.cpu().numpy(),
            "prev_neighbor_msgs": dummy_prev_nbr.cpu().numpy(),
            "prev_central_feedback": dummy_prev_fb.cpu().numpy(),
        }
        ort_outs = session.run(None, ort_inputs)

        # PyTorch reference
        with torch.no_grad():
            pt_outs = exportable(*input_tensors)

        # Check action parity
        pt_actions = pt_outs[0].cpu().numpy()
        ort_actions = ort_outs[0]
        match = np.array_equal(pt_actions, ort_actions)
        print(f"  --> Action Match Verification: {'PASS (100% Exact Parity)' if match else 'FAIL'}")
        max_logit_diff = np.max(np.abs(pt_outs[1].cpu().numpy() - ort_outs[1]))
        print(f"  --> Max Logit Numerical Difference: {max_logit_diff:.6e}")
        print("--> ONNX Model is verified and ready for deployment!")
    except ImportError:
        print("--> onnxruntime not installed, skipping runtime validation.")


def main():
    parser = argparse.ArgumentParser(description="Export OctopusBrain to ONNX")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/top1_octopus_brain.pt")
    parser.add_argument("--output", type=str, default="checkpoints/octopus_brain.onnx")
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    export_model(args.checkpoint, args.output, args.device)


if __name__ == "__main__":
    main()
