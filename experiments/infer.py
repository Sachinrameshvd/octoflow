"""Standalone CLI Inference and Evaluation Script for OctopusBrain.

Runs inference using a trained checkpoint (or zero-shot initialized architecture)
and provides detailed per-step neuro-behavioral diagnostics, ASCII arena rendering,
and optional GIF generation.

Usage:
    # Run interactive terminal inference
    python experiments/infer.py --episodes 2 --render terminal

    # Run inference with checkpoint and save GIF
    python experiments/infer.py --checkpoint checkpoints/best_octopus_brain.pt --episodes 1 --render gif --gif-output experiments/inference_demo.gif
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import torch

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from octopus_brain.config import OctopusBrainConfig, EnvConfig
from octopus_brain.brain import OctopusBrain
from envs.reach_and_avoid import ReachAndAvoidEnv
from envs.render_env import EnvironmentVisualizer


def run_inference(
    checkpoint_path: Optional[str] = "checkpoints/best_octopus_brain.pt",
    episodes: int = 2,
    render_mode: str = "terminal",
    gif_output: Optional[str] = None,
    num_knockouts: int = 0,
    deterministic: bool = True,
    seed: int = 42,
    device_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute model inference and diagnostic telemetry."""
    if device_name:
        device = torch.device(device_name)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")

    print("=" * 80)
    print("OCTOPUSBRAIN INFERENCE ENGINE")
    print(f"Device: {device} | Checkpoint: {checkpoint_path or 'Fresh Initialization'}")
    print(f"Episodes: {episodes} | Mode: {render_mode.upper()} | Knockouts: {num_knockouts}")
    print("=" * 80)

    # Initialize environment and configuration
    config = OctopusBrainConfig(n_modules=8, hidden_dim=64, message_dim=32, central_dim=64)
    env_config = EnvConfig(n_arms=8, max_steps=40)
    env = ReachAndAvoidEnv(env_config)

    model = OctopusBrain(config).to(device)

    # Load checkpoint if available
    if checkpoint_path and os.path.exists(checkpoint_path):
        try:
            ckpt = torch.load(checkpoint_path, map_location=device, weights_only=True)
        except TypeError:
            ckpt = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        print(f"--> Successfully loaded trained model checkpoint from: {checkpoint_path}\n")
    else:
        print("--> Note: No checkpoint found or specified. Running with initial model weights.\n")

    model.eval()

    total_rewards = []
    total_single_hits = 0
    total_joint_hits = 0
    total_hazard_hits = 0
    all_report_rates = []
    all_coalitions = []

    # Setup arm knockout mask if requested
    active_mask = None
    if num_knockouts > 0:
        mask_np = np.ones((1, config.n_modules), dtype=np.float32)
        killed_indices = list(range(min(num_knockouts, config.n_modules - 1)))
        mask_np[0, killed_indices] = 0.0
        active_mask = torch.tensor(mask_np, device=device)
        print(f"[!] Arm Knockout Active: Severed arms = {killed_indices}\n")

    action_names = ["STAY", "UP", "DOWN", "LEFT", "RIGHT"]

    visualizer = EnvironmentVisualizer(env)

    for ep in range(1, episodes + 1):
        obs_np, _ = env.reset(seed=seed + ep * 100)
        model.reset(batch_size=1, device=device)
        obs = torch.tensor(obs_np, dtype=torch.float32, device=device).unsqueeze(0)

        ep_reward = 0.0
        ep_reports = []
        frames_for_gif = []

        print(f"--- EPISODE {ep}/{episodes} START ---")

        for t in range(env.max_steps):
            with torch.no_grad():
                out = model.step(obs, active_mask=active_mask, deterministic=deterministic)

            actions = out["actions"][0].detach().cpu().numpy()
            report_events = out["report_events"][0].detach().cpu().numpy().astype(bool)
            surprises = out["surprise_values"][0].detach().cpu().numpy()
            active_clusters = out.get("coalition_clusters", [])

            next_obs_np, rewards, term, trunc, info = env.step(actions)
            step_reward = float(np.sum(rewards))
            ep_reward += step_reward

            ep_reports.append(float(np.mean(report_events)))
            if len(active_clusters) > 0:
                all_coalitions.append(active_clusters)

            total_single_hits += info.get("single_completed", 0)
            total_joint_hits += info.get("joint_completed", 0)
            total_hazard_hits += info.get("hazard_hits", 0)

            # Terminal output
            if render_mode == "terminal":
                if t % 5 == 0 or t == env.max_steps - 1 or info.get("joint_completed", 0) > 0:
                    report_str = "".join(["●" if r else "○" for r in report_events])
                    cluster_str = ", ".join([f"({','.join(map(str, c))})" for c in active_clusters]) or "None"
                    print(
                        f"  [Step {t:02d}] "
                        f"Rew: {step_reward:+5.2f} | "
                        f"Reports [{report_str}] ({np.mean(report_events)*100:3.0f}%) | "
                        f"Max Surprise: {np.max(surprises):.2f} | "
                        f"Coalitions: {cluster_str}"
                    )
            elif render_mode == "ascii":
                print(visualizer.render_ascii(step=t, reward=ep_reward, report_rate=float(np.mean(report_events)), coalition_clusters=active_clusters, clear_screen=False))

            if render_mode == "gif":
                c_mat = out["coalition_matrix"][0].detach().cpu().numpy() if out["coalition_matrix"].numel() > 0 else np.zeros((8, 8))
                snapshot = {
                    "step": t,
                    "reward": ep_reward,
                    "report_rate": float(np.mean(report_events)),
                    "c_mat": c_mat,
                    "edges": out.get("active_coalitions", []),
                    "arm_tips": env.arm_tips.copy(),
                    "single_targets": [st.copy() for st in env.single_targets],
                    "joint_targets": [{"pos": jt["pos"].copy(), "active": jt["active"]} for jt in env.joint_targets],
                    "hazards": [h.copy() for h in env.hazards],
                }
                frames_for_gif.append(snapshot)

            obs = torch.tensor(next_obs_np, dtype=torch.float32, device=device).unsqueeze(0)
            if term or trunc:
                break

        total_rewards.append(ep_reward)
        all_report_rates.append(np.mean(ep_reports))
        print(f"--- EPISODE {ep} END: Total Reward = {ep_reward:+.2f}, Mean Comm Rate = {np.mean(ep_reports)*100:.1f}%\n")

        # Save GIF if requested
        if render_mode == "gif" and gif_output and len(frames_for_gif) > 0:
            import matplotlib.pyplot as plt
            from matplotlib.animation import FuncAnimation, PillowWriter
            os.makedirs(os.path.dirname(os.path.abspath(gif_output)), exist_ok=True)
            fig, ax = plt.subplots(figsize=(7, 7), facecolor="#0f172a")

            def update(frame_idx):
                data = frames_for_gif[frame_idx]
                env.arm_tips = data["arm_tips"]
                env.single_targets = data["single_targets"]
                env.joint_targets = data["joint_targets"]
                env.hazards = data["hazards"]
                visualizer.create_matplotlib_frame(
                    ax=ax,
                    step=data["step"],
                    reward=data["reward"],
                    report_rate=data["report_rate"],
                    coalition_matrix=data["c_mat"],
                    active_edges=data["edges"],
                )

            anim = FuncAnimation(fig, update, frames=len(frames_for_gif), interval=250)
            writer = PillowWriter(fps=4)
            anim.save(gif_output, writer=writer)
            plt.close(fig)
            print(f"--> Saved inference animation to: {gif_output}")

    summary = {
        "mean_reward": float(np.mean(total_rewards)),
        "std_reward": float(np.std(total_rewards)),
        "mean_report_rate": float(np.mean(all_report_rates)),
        "total_single_hits": total_single_hits,
        "total_joint_hits": total_joint_hits,
        "total_hazard_hits": total_hazard_hits,
    }

    print("=" * 80)
    print("INFERENCE SUMMARY:")
    print(f"  Mean Reward:          {summary['mean_reward']:+.2f} ± {summary['std_reward']:.2f}")
    print(f"  Mean Comm Rate:       {summary['mean_report_rate']*100:.1f}%")
    print(f"  Single Target Hits:   {summary['total_single_hits']}")
    print(f"  Joint Target Hits:    {summary['total_joint_hits']}")
    print(f"  Hazard Collisions:    {summary['total_hazard_hits']}")
    print("=" * 80)

    return summary


def main():
    parser = argparse.ArgumentParser(description="OctopusBrain Inference CLI")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/best_octopus_brain.pt", help="Path to model checkpoint")
    parser.add_argument("--episodes", type=int, default=2, help="Number of inference episodes")
    parser.add_argument("--render", type=str, default="terminal", choices=["terminal", "ascii", "gif", "quiet"], help="Rendering mode")
    parser.add_argument("--gif-output", type=str, default="experiments/inference_demo.gif", help="GIF output path")
    parser.add_argument("--knockout", type=int, default=0, help="Number of arms to sever/knockout (0..7)")
    parser.add_argument("--stochastic", action="store_true", help="Sample actions stochastically instead of greedy")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--device", type=str, default=None, help="Compute device (cpu, mps, cuda)")
    args = parser.parse_args()

    run_inference(
        checkpoint_path=args.checkpoint,
        episodes=args.episodes,
        render_mode=args.render,
        gif_output=args.gif_output,
        num_knockouts=args.knockout,
        deterministic=not args.stochastic,
        seed=args.seed,
        device_name=args.device,
    )


if __name__ == "__main__":
    main()
