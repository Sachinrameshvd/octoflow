"""Publication-Ready Multi-Seed Benchmarking & Plotting Suite for OctopusBrain.

Runs multi-seed evaluations across all models and baseline ablations,
logs structured results to JSON, and generates publication-grade figures:
1. Pareto Frontier Curve: Task Reward vs. Communication Bandwidth
2. Fault Tolerance Degradation Curves (Mean ± Shaded Standard Error)
3. Coalition Attention Alignment Heatmap
4. Memory Asymmetry Dual-Benchmark Comparison
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np
import torch
from envs.reach_and_avoid import ReachAndAvoidEnv
from octopus_brain.brain import OctopusBrain
from octopus_brain.config import EnvConfig, OctopusBrainConfig

from experiments.baselines import (
    AlwaysLocalBaseline,
    DenseCentralizedBaseline,
    SynchronousFullCommBaseline,
)
from experiments.run_coalition_analysis import evaluate_coalition_correlation
from experiments.run_fault_tolerance import run_episode as run_knockout_ep
from experiments.run_memory_ablation import evaluate_condition as run_memory_ep


def run_benchmark_suite(
    num_seeds: int = 3,
    episodes_per_seed: int = 10,
    output_dir: str = "experiments",
    checkpoint_path: str | None = "checkpoints/best_octopus_brain.pt",
) -> None:
    """Run comprehensive multi-seed benchmark and produce publication figures."""
    print("=" * 80)
    print("OCTOPUS-BRAIN: PUBLICATION-GRADE MULTI-SEED BENCHMARK SUITE")
    print(f"Seeds: {num_seeds} | Evaluation Episodes/Seed: {episodes_per_seed}")
    print(
        f"Checkpoint: {checkpoint_path if (checkpoint_path and os.path.exists(checkpoint_path)) else 'Random Initialization'}"
    )
    print("=" * 80)

    device = torch.device("cpu")
    config = OctopusBrainConfig(n_modules=8, hidden_dim=64, message_dim=32, consolidation_every=5)
    env_config = EnvConfig(n_arms=8, max_steps=40)
    env = ReachAndAvoidEnv(env_config)

    # 1. Models to evaluate
    oct_model = OctopusBrain(config).to(device)
    if checkpoint_path and os.path.exists(checkpoint_path):
        try:
            ckpt = torch.load(checkpoint_path, map_location=device, weights_only=True)
        except TypeError:
            ckpt = torch.load(checkpoint_path, map_location=device)
        oct_model.load_state_dict(ckpt["model_state_dict"])
        print(f"--> Loaded trained checkpoint: {checkpoint_path}\n")

    models = {
        "OctopusBrain (Async/Adaptive)": oct_model,
        "Synchronous (Full Comm)": SynchronousFullCommBaseline(config).to(device),
        "Always Local (No Central)": AlwaysLocalBaseline(config).to(device),
        "Dense Centralized": DenseCentralizedBaseline(config).to(device),
    }

    # 2. Pareto Evaluation (Reward vs Communication Rate)
    print("\n[1/4] Evaluating Pareto Frontier (Task Reward vs. Communication Bandwidth)...")
    pareto_results: dict[str, dict[str, list[float]]] = {
        name: {"rewards": [], "comm_rates": []} for name in models
    }

    for name, model in models.items():
        for seed in range(num_seeds):
            for ep in range(episodes_per_seed):
                res = run_knockout_ep(
                    env, model, num_killed=0, seed=1000 * seed + ep, device=device
                )
                pareto_results[name]["rewards"].append(res["reward"])
                pareto_results[name]["comm_rates"].append(res["mean_report_rate"])

    # 3. Fault Tolerance Degradation Curves
    print("\n[2/4] Evaluating Fault Tolerance under Knockouts (k = 0..4 modules severed)...")
    knockout_counts = [0, 1, 2, 3, 4]
    fault_results: dict[str, dict[int, list[float]]] = {
        "OctopusBrain": {k: [] for k in knockout_counts},
        "Dense Centralized": {k: [] for k in knockout_counts},
        "Always Local": {k: [] for k in knockout_counts},
    }

    for k in knockout_counts:
        for seed in range(num_seeds):
            for ep in range(episodes_per_seed):
                r_oct = run_knockout_ep(
                    env,
                    models["OctopusBrain (Async/Adaptive)"],
                    num_killed=k,
                    seed=2000 * seed + ep,
                    device=device,
                )
                r_dns = run_knockout_ep(
                    env,
                    models["Dense Centralized"],
                    num_killed=k,
                    seed=2000 * seed + ep,
                    device=device,
                )
                r_loc = run_knockout_ep(
                    env,
                    models["Always Local (No Central)"],
                    num_killed=k,
                    seed=2000 * seed + ep,
                    device=device,
                )
                fault_results["OctopusBrain"][k].append(r_oct["reward"])
                fault_results["Dense Centralized"][k].append(r_dns["reward"])
                fault_results["Always Local"][k].append(r_loc["reward"])

    # 4. Coalition Alignment & Attention Matrix Extraction
    print("\n[3/4] Evaluating Coalition Attention Alignment...")
    coalition_eval = evaluate_coalition_correlation(
        env, models["OctopusBrain (Async/Adaptive)"], num_episodes=20, seed=42, device=device
    )

    # Extract sample coalition attention matrix
    obs_np, _ = env.reset(seed=99)
    models["OctopusBrain (Async/Adaptive)"].reset(batch_size=1, device=device)
    sample_out = models["OctopusBrain (Async/Adaptive)"].step(
        torch.tensor(obs_np, dtype=torch.float32, device=device).unsqueeze(0),
        force_report_all=True,
    )
    sample_c_mat = sample_out["coalition_matrix"][0].detach().cpu().numpy()

    # 5. Memory Asymmetry Dual Benchmark
    print("\n[4/4] Evaluating Memory Asymmetry Dual-Benchmark...")
    env_reactive = ReachAndAvoidEnv(EnvConfig(n_arms=8, max_steps=40, delayed_cue_mode=False))
    env_delayed = ReachAndAvoidEnv(EnvConfig(n_arms=8, max_steps=40, delayed_cue_mode=True))

    memory_conditions = [
        ("Full Architecture", False, False),
        ("Central Ablated", False, True),
        ("Local Ablated", True, False),
        ("Both Ablated", True, True),
    ]
    memory_results = []
    for cond_name, ablate_loc, ablate_cent in memory_conditions:
        r_react = run_memory_ep(
            env_reactive,
            models["OctopusBrain (Async/Adaptive)"],
            ablate_loc,
            ablate_cent,
            num_episodes=15,
            seed=500,
        )
        r_delay = run_memory_ep(
            env_delayed,
            models["OctopusBrain (Async/Adaptive)"],
            ablate_loc,
            ablate_cent,
            num_episodes=15,
            seed=600,
        )
        memory_results.append((cond_name, r_react["mean_reward"], r_delay["cue_retention_score"]))

    # Save JSON Log
    json_path = os.path.join(output_dir, "benchmark_results.json")
    summary_data = {
        "pareto": {
            m: {
                "mean_reward": float(np.mean(pareto_results[m]["rewards"])),
                "std_reward": float(np.std(pareto_results[m]["rewards"])),
                "mean_comm_rate": float(np.mean(pareto_results[m]["comm_rates"])),
            }
            for m in pareto_results
        },
        "fault_tolerance": {
            m: {k: float(np.mean(fault_results[m][k])) for k in knockout_counts}
            for m in fault_results
        },
        "coalition_analysis": coalition_eval,
        "memory_ablation": memory_results,
    }
    with open(json_path, "w") as f:
        json.dump(summary_data, f, indent=2)
    print(f"\nSaved structured metrics log to: {json_path}")

    # Generate Publication Figure
    plot_path = os.path.join(output_dir, "benchmark_results.png")
    print(f"Generating 4-panel publication figure: {plot_path}...")

    plt.style.use(
        "seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default"
    )
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle(
        "octopus-brain: Empirical Benchmark & Ablation Study",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    # Subplot 1: Pareto Frontier (Reward vs Comm Rate)
    ax1 = axes[0, 0]
    colors = {
        "OctopusBrain (Async/Adaptive)": "#0284c7",
        "Synchronous (Full Comm)": "#10b981",
        "Always Local (No Central)": "#f59e0b",
        "Dense Centralized": "#6b7280",
    }
    for name in pareto_results:
        x = np.mean(pareto_results[name]["comm_rates"]) * 100.0
        y = np.mean(pareto_results[name]["rewards"])
        y_err = np.std(pareto_results[name]["rewards"]) / np.sqrt(
            len(pareto_results[name]["rewards"])
        )
        ax1.errorbar(
            x,
            y,
            yerr=y_err,
            fmt="o",
            color=colors[name],
            label=name,
            markersize=8,
            capsize=4,
            elinewidth=1.5,
        )

    ax1.set_xlabel("Communication Bandwidth (% Reporting)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Task Reward", fontsize=10, fontweight="bold")
    ax1.set_title("A. Pareto Trade-off (Reward vs. Bandwidth)", fontsize=11, fontweight="bold")
    ax1.legend(loc="lower right", fontsize=8)

    # Subplot 2: Fault Tolerance Degradation Curves
    ax2 = axes[0, 1]
    ft_colors = {
        "OctopusBrain": "#0284c7",
        "Dense Centralized": "#ef4444",
        "Always Local": "#f59e0b",
    }
    for name in fault_results:
        means = [np.mean(fault_results[name][k]) for k in knockout_counts]
        stds = [
            np.std(fault_results[name][k]) / np.sqrt(len(fault_results[name][k]))
            for k in knockout_counts
        ]
        ax2.plot(knockout_counts, means, marker="o", color=ft_colors[name], label=name, linewidth=2)
        ax2.fill_between(
            knockout_counts,
            np.array(means) - np.array(stds),
            np.array(means) + np.array(stds),
            color=ft_colors[name],
            alpha=0.15,
        )

    ax2.set_xlabel("Number of Modules Knocked Out (Severed)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Task Reward", fontsize=10, fontweight="bold")
    ax2.set_title("B. Fault Tolerance Degradation Curves", fontsize=11, fontweight="bold")
    ax2.set_xticks(knockout_counts)
    ax2.legend(loc="lower left", fontsize=8)

    # Subplot 3: Coalition Attention Heatmap
    ax3 = axes[1, 0]
    im = ax3.imshow(sample_c_mat, cmap="viridis", interpolation="nearest")
    fig.colorbar(im, ax=ax3, fraction=0.046, pad=0.04)
    ax3.set_title(
        f"C. Coalition Attention Matrix A (Phi Corr: {coalition_eval['phi_correlation']:+.2f})",
        fontsize=11,
        fontweight="bold",
    )
    ax3.set_xlabel("Key Module ID", fontsize=10, fontweight="bold")
    ax3.set_ylabel("Query Module ID", fontsize=10, fontweight="bold")
    ax3.set_xticks(range(config.n_modules))
    ax3.set_yticks(range(config.n_modules))

    # Subplot 4: Memory Asymmetry Breakdown
    ax4 = axes[1, 1]
    cond_labels = [c[0] for c in memory_results]
    react_scores = [c[1] for c in memory_results]
    delay_scores = [c[2] * 10.0 for c in memory_results]  # Scaled for visual comparison

    x_indices = np.arange(len(cond_labels))
    width = 0.35

    ax4.bar(
        x_indices - width / 2, react_scores, width, label="Reactive Performance", color="#3b82f6"
    )
    ax4.bar(
        x_indices + width / 2,
        delay_scores,
        width,
        label="Delayed Context Retention (x10)",
        color="#8b5cf6",
    )
    ax4.set_xticks(x_indices)
    ax4.set_xticklabels(cond_labels, rotation=15, ha="right", fontsize=8)
    ax4.set_ylabel("Performance Score", fontsize=10, fontweight="bold")
    ax4.set_title(
        "D. Biological Memory Asymmetry (Local vs Central)", fontsize=11, fontweight="bold"
    )
    ax4.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close(fig)
    print(f"Publication-grade benchmark figure generated at: {plot_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OctopusBrain Benchmark Suite")
    parser.add_argument("--seeds", type=int, default=3, help="Number of seeds")
    parser.add_argument("--episodes", type=int, default=10, help="Episodes per seed")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="checkpoints/best_octopus_brain.pt",
        help="Checkpoint path to evaluate",
    )
    parser.add_argument(
        "--outdir", type=str, default="experiments", help="Output directory for plots and json"
    )
    args = parser.parse_args()

    run_benchmark_suite(
        num_seeds=args.seeds,
        episodes_per_seed=args.episodes,
        output_dir=args.outdir,
        checkpoint_path=args.checkpoint,
    )
