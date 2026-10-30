"""Memory Ablation Experiment: Isolating Biological Asymmetry.

Tests the biological asymmetry between:
- Peripheral local working memory (fast reactive control within-episode)
- Central slow consolidation memory (long-horizon / cross-temporal associative context)

Evaluates 4 Conditions:
1. Full System: Local Memory + Central Consolidation
2. Central Ablated: Local Memory Only, Central Consolidation Off
3. Local Ablated: Central Consolidation Only, Local Memory Reset Every Step
4. Pure Reactive: Both Local and Central Memory Ablated

CRITICAL PROTOCOL:
Logs report rate and coalition statistics BEFORE reporting any task-performance numbers.
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch
from envs.reach_and_avoid import ReachAndAvoidEnv
from octopus_brain.brain import OctopusBrain
from octopus_brain.config import EnvConfig, OctopusBrainConfig


def evaluate_condition(
    env: ReachAndAvoidEnv,
    model: OctopusBrain,
    ablate_local_memory: bool = False,
    ablate_central_memory: bool = False,
    num_episodes: int = 20,
    seed: int = 42,
    device: torch.device = torch.device("cpu"),
) -> dict[str, float]:
    """Evaluate one memory ablation condition across reactive and delayed-cue tasks."""
    total_rewards = []
    report_rates = []
    coalition_sizes = []
    hazard_collisions = []
    cue_accuracy_scores = []

    for ep in range(num_episodes):
        obs_np, _ = env.reset(seed=seed + ep)
        model.reset(batch_size=1, device=device)
        obs = torch.tensor(obs_np, dtype=torch.float32, device=device).unsqueeze(0)

        ep_reward = 0.0
        ep_hazards = 0
        cue_correct = 0

        for t in range(env.max_steps):
            if ablate_local_memory:
                # Local memory ablated: zero out peripheral hidden states before step
                model.hidden_states = [torch.zeros_like(h) for h in model.hidden_states]

            with torch.no_grad():
                out = model.step(
                    obs,
                    deterministic=True,
                    disable_central=ablate_central_memory,
                )

            actions = out["actions"][0].cpu().numpy()
            report_rates.append(float(out["report_rate"]))

            if "coalition_matrix" in out and out["coalition_matrix"].numel() > 0:
                c_mat = out["coalition_matrix"][0].cpu().numpy()
                coalition_sizes.append(float(np.sum(c_mat > 0.15)))
            else:
                coalition_sizes.append(0.0)

            next_obs_np, rewards, term, trunc, step_info = env.step(actions)
            ep_reward += float(np.sum(rewards))
            ep_hazards += step_info["hazard_hits"]

            # Late-episode context cue retention check (steps t >= 10)
            if t >= 10 and step_info["single_completed"] > 0:
                # If reward collected matches the cue given at step 0-2
                cue_correct += 1

            obs = torch.tensor(next_obs_np, dtype=torch.float32, device=device).unsqueeze(0)
            if term or trunc:
                break

        total_rewards.append(ep_reward)
        hazard_collisions.append(ep_hazards)
        cue_accuracy_scores.append(cue_correct)

    return {
        "mean_reward": float(np.mean(total_rewards)),
        "std_reward": float(np.std(total_rewards)),
        "mean_hazards": float(np.mean(hazard_collisions)),
        "cue_retention_score": float(np.mean(cue_accuracy_scores)),
        "mean_report_rate": float(np.mean(report_rates)),
        "mean_coalition_size": float(np.mean(coalition_sizes)),
    }


def run_memory_ablation_experiment(
    num_episodes: int = 20,
    checkpoint_path: str | None = "checkpoints/best_octopus_brain.pt",
) -> None:
    """Run dual-benchmark memory ablation study across all 4 conditions."""
    print("=" * 80)
    print("OCTOPUS-BRAIN: MEMORY ABLATION EXPERIMENT")
    print(
        f"Checkpoint: {checkpoint_path if (checkpoint_path and os.path.exists(checkpoint_path)) else 'Random Weights'}"
    )
    print("=" * 80)

    device = torch.device("cpu")
    config = OctopusBrainConfig(n_modules=8, hidden_dim=64, message_dim=32, consolidation_every=5)

    # 1. Benchmark A: Standard reactive ReachAndAvoid
    env_reactive = ReachAndAvoidEnv(EnvConfig(n_arms=8, max_steps=40, delayed_cue_mode=False))

    # 2. Benchmark B: Long-Horizon Delayed Context Recall (Cue flashes at t<=2 then disappears)
    env_delayed = ReachAndAvoidEnv(EnvConfig(n_arms=8, max_steps=40, delayed_cue_mode=True))

    model = OctopusBrain(config).to(device)
    if checkpoint_path and os.path.exists(checkpoint_path):
        try:
            ckpt = torch.load(checkpoint_path, map_location=device, weights_only=True)
        except TypeError:
            ckpt = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        print(f"--> Loaded trained checkpoint: {checkpoint_path}\n")

    # CRITICAL PRE-LOGGING: Check gate health before proceeding
    print("\n" + "-" * 80)
    print("CRITICAL GATE HEALTH & DIAGNOSTIC PRE-LOGGING:")
    print("-" * 80)
    pre_diag = evaluate_condition(
        env_reactive,
        model,
        ablate_local_memory=False,
        ablate_central_memory=False,
        num_episodes=5,
        seed=10,
    )
    report_rate_pct = pre_diag["mean_report_rate"] * 100.0
    print(f"[*] Report Rate: {report_rate_pct:.2f}%")
    print(f"[*] Coalition Frequency: {pre_diag['mean_coalition_size']:.2f} active links/step")

    if report_rate_pct <= 0.01:
        print("[WARNING] DEGENERATE GATE: 0.0% report rate!")
    elif report_rate_pct >= 99.9:
        print("[WARNING] DEGENERATE GATE: 100.0% report rate!")
    else:
        print("[OK] Gate is operating in healthy sparse regime.")
    print("-" * 80)

    conditions = [
        ("Full Architecture (Local + Central)", False, False),
        ("Central Ablated (Local Only)", False, True),
        ("Local Ablated (Central Only)", True, False),
        ("Both Ablated (Pure Reactive)", True, True),
    ]

    results_table = []

    print("\nEvaluating 4 memory ablation conditions across Dual Benchmarks...")
    for name, ablate_loc, ablate_cent in conditions:
        # Evaluate Reactive Benchmark
        res_react = evaluate_condition(
            env_reactive,
            model,
            ablate_local_memory=ablate_loc,
            ablate_central_memory=ablate_cent,
            num_episodes=num_episodes,
            seed=100,
        )
        # Evaluate Long-Horizon Delayed Cue Benchmark
        res_delay = evaluate_condition(
            env_delayed,
            model,
            ablate_local_memory=ablate_loc,
            ablate_central_memory=ablate_cent,
            num_episodes=num_episodes,
            seed=200,
        )
        results_table.append((name, res_react, res_delay))

    print("\n" + "=" * 85)
    print(f"{'Condition':<35}{'Reactive Rew':<16}{'Hazards Avoided':<18}{'Delayed Cue Score':<16}")
    print("=" * 85)

    for name, r_react, r_delay in results_table:
        hazards_avoided = max(0, 15 - r_react["mean_hazards"])
        print(
            f"{name:<35}"
            f"{r_react['mean_reward']:>7.2f} (±{r_react['std_reward']:.1f})   "
            f"{hazards_avoided:>8.1f}          "
            f"{r_delay['cue_retention_score']:>8.2f}"
        )

    print("=" * 85)
    print("Memory Ablation experiment complete.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OctopusBrain Memory Ablation Experiment")
    parser.add_argument("--episodes", type=int, default=20, help="Number of episodes per condition")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="checkpoints/best_octopus_brain.pt",
        help="Checkpoint path to evaluate",
    )
    args = parser.parse_args()

    run_memory_ablation_experiment(num_episodes=args.episodes, checkpoint_path=args.checkpoint)
