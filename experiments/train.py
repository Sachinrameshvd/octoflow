"""CLI Training Script for OctopusBrain Architecture with GAE & Adaptive Lagrangian Gating.

Usage:
    python experiments/train.py --episodes 150 --eval-every 25 --checkpoint checkpoints/best_model.pt
"""

import sys
import os
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import torch

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from octopus_brain.config import OctopusBrainConfig, EnvConfig
from octopus_brain.brain import OctopusBrain
from octopus_brain.trainer import OctopusTrainer
from envs.reach_and_avoid import ReachAndAvoidEnv
from envs.hunting_env import CooperativeHuntingEnv
from envs.curriculum import CurriculumEnv, CurriculumScheduler


def main():
    parser = argparse.ArgumentParser(description="Train OctopusBrain with GAE and Lagrangian Gating")
    parser.add_argument("--episodes", type=int, default=150, help="Total training episodes")
    parser.add_argument("--eval-every", type=int, default=25, help="Evaluation interval")
    parser.add_argument("--lr", type=float, default=0.002, help="Learning rate")
    parser.add_argument("--gamma", type=float, default=0.96, help="Discount factor gamma")
    parser.add_argument("--gae-lambda", type=float, default=0.92, help="GAE lambda parameter")
    parser.add_argument("--target-rate", type=float, default=0.25, help="Target communication rate (e.g. 0.25 for 25 percent)")
    parser.add_argument("--env-type", type=str, default="reach_and_avoid", choices=["reach_and_avoid", "hunting", "curriculum"], help="Environment type")
    parser.add_argument("--algorithm", type=str, default="ppo", choices=["ppo", "a2c"], help="Optimization algorithm (ppo or a2c)")
    parser.add_argument("--ppo-epochs", type=int, default=3, help="PPO epochs per rollout trajectory")
    parser.add_argument("--clip-eps", type=float, default=0.2, help="PPO clipping epsilon")
    parser.add_argument("--no-normalize-adv", action="store_true", help="Disable GAE advantage normalization")
    parser.add_argument("--no-lr-schedule", action="store_true", help="Disable CosineAnnealing learning rate schedule")
    parser.add_argument("--no-entropy-anneal", action="store_true", help="Disable exploration entropy decay")
    parser.add_argument("--curiosity-coef", type=float, default=0.02, help="Intrinsic surprise exploration reward coefficient")
    parser.add_argument("--batch-episodes", type=int, default=1, help="Number of rollout episodes to batch/aggregate per update")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume training from")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/best_octopus_brain.pt", help="Checkpoint output path")
    parser.add_argument("--plot-path", type=str, default="experiments/training_curves.png", help="Training curves plot path")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using compute device: {device}")

    # Initialize Configs
    config = OctopusBrainConfig(
        n_modules=8,
        obs_dim=16,
        action_dim=5,
        hidden_dim=64,
        message_dim=32,
        central_dim=64,
        consolidation_every=5,
        target_report_rate=args.target_rate,
        adaptive_budgeting=True,
    )
    env_config = EnvConfig(n_arms=8, max_steps=40)

    # Initialize requested environment
    if args.env_type == "curriculum":
        print("--> Initializing Multi-Stage Curriculum Environment...")
        env = CurriculumEnv(base_config=env_config)
    elif args.env_type == "hunting":
        print("--> Initializing Dynamic Cooperative Hunting Environment...")
        env = CooperativeHuntingEnv(config=env_config)
    else:
        print("--> Initializing Standard ReachAndAvoid Environment...")
        env = ReachAndAvoidEnv(env_config)

    model = OctopusBrain(config).to(device)

    # Optionally resume weights
    if args.resume and os.path.exists(args.resume):
        try:
            ckpt = torch.load(args.resume, map_location=device, weights_only=True)
        except TypeError:
            ckpt = torch.load(args.resume, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        print(f"--> Resumed model weights from: {args.resume}")

    trainer = OctopusTrainer(
        model=model,
        env=env,
        config=config,
        lr=args.lr,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
        algorithm=args.algorithm,
        ppo_epochs=args.ppo_epochs,
        clip_eps=args.clip_eps,
        normalize_advantages=not args.no_normalize_adv,
        lr_schedule=not args.no_lr_schedule,
        entropy_anneal=not args.no_entropy_anneal,
        curiosity_coef=args.curiosity_coef,
        batch_episodes=args.batch_episodes,
        device=device,
    )

    results = trainer.train(
        num_episodes=args.episodes,
        eval_every=args.eval_every,
        checkpoint_path=args.checkpoint,
        verbose=True,
    )

    # Plot Training Convergence Curves
    history = results["history"]
    if len(history["episode_rewards"]) > 0:
        os.makedirs(os.path.dirname(os.path.abspath(args.plot_path)), exist_ok=True)
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("OctopusBrain: Training Convergence & Loss Telemetry", fontsize=13, fontweight="bold")

        # 1. Rewards
        ax1 = axes[0, 0]
        window = min(10, len(history["episode_rewards"]))
        smoothed = np.convolve(history["episode_rewards"], np.ones(window)/window, mode='valid')
        ax1.plot(history["episode_rewards"], alpha=0.3, color="#0284c7", label="Raw Episode Reward")
        ax1.plot(range(window - 1, len(history["episode_rewards"])), smoothed, color="#0284c7", linewidth=2, label="Moving Average")
        ax1.set_title("Episode Reward Convergence", fontweight="bold")
        ax1.set_xlabel("Episode")
        ax1.set_ylabel("Reward")
        ax1.legend(loc="lower right")

        # 2. Communication Rate & Dual Lambda
        ax2 = axes[0, 1]
        ax2.plot(np.array(history["mean_report_rates"]) * 100.0, color="#10b981", label="Report Rate (%)")
        ax2.axhline(args.target_rate * 100.0, color="#ef4444", linestyle="--", label=f"Target ({args.target_rate*100:.0f}%)")
        ax2.set_title("Adaptive Lagrangian Gate Communication (%)", fontweight="bold")
        ax2.set_xlabel("Episode")
        ax2.set_ylabel("Reporting Rate %")
        ax2.legend(loc="upper right")

        # 3. Policy & Value Loss
        ax3 = axes[1, 0]
        ax3.plot(history["policy_losses"], label="Policy Loss", color="#8b5cf6")
        ax3.plot(history["value_losses"], label="Value Loss", color="#f59e0b")
        ax3.set_title("Actor-Critic Loss Curves", fontweight="bold")
        ax3.set_xlabel("Episode")
        ax3.set_ylabel("Loss")
        ax3.legend(loc="upper right")

        # 4. Target Hits & Hazard Avoidance
        ax4 = axes[1, 1]
        ax4.plot(history["single_hits"], label="Single Target Hits", color="#3b82f6", alpha=0.7)
        ax4.plot(history["joint_hits"], label="Joint Cooperative Hits", color="#10b981", linewidth=1.5)
        ax4.plot(history["hazard_hits"], label="Hazard Collisions", color="#ef4444", alpha=0.7)
        ax4.set_title("Behavioral Performance Metrics", fontweight="bold")
        ax4.set_xlabel("Episode")
        ax4.set_ylabel("Count / Episode")
        ax4.legend(loc="upper left")

        plt.tight_layout()
        plt.savefig(args.plot_path, dpi=300)
        plt.close(fig)
        print(f"\nSaved training convergence plot to: {args.plot_path}")

    final_eval = results["final_eval"]
    print("\n" + "=" * 80)
    print("FINAL EVALUATION METRICS:")
    print(f"  Mean Reward:          {final_eval['mean_reward']:+.2f} ± {final_eval['std_reward']:.2f}")
    print(f"  Mean Report Rate:     {final_eval['mean_report_rate']*100:.1f}%")
    print(f"  Mean Coalition Size:  {final_eval['mean_coalition_size']:.2f} arms / step")
    print(f"  Single Target Hits:   {final_eval['mean_single_hits']:.2f} / episode")
    print(f"  Joint Target Hits:    {final_eval['mean_joint_hits']:.2f} / episode")
    print(f"  Hazard Hits:          {final_eval['mean_hazard_hits']:.2f} / episode")
    print("=" * 80)


if __name__ == "__main__":
    main()
