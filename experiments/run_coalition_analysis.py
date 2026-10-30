"""Coalition Analysis Experiment: Validating Temporary Coalition Binding.

Hypothesis under test:
Does dynamic coalition formation correlate with actual joint-subtask moments
significantly more than chance, and does it provide the necessary coordination
missing in the 'Always Local' baseline?

CRITICAL PROTOCOL:
Logs report rate and coalition statistics BEFORE reporting any task-performance numbers.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch
from envs.reach_and_avoid import ReachAndAvoidEnv
from octopus_brain.brain import OctopusBrain
from octopus_brain.config import EnvConfig, OctopusBrainConfig

from experiments.baselines import AlwaysLocalBaseline


def evaluate_coalition_correlation(
    env: ReachAndAvoidEnv,
    model: torch.nn.Module,
    num_episodes: int = 25,
    threshold: float = 0.15,
    seed: int = 42,
    device: torch.device = torch.device("cpu"),
) -> dict[str, float]:
    """Evaluate alignment between physical joint-task requirements and neural coalition attention."""
    y_true_all: list[int] = []
    y_pred_all: list[int] = []
    y_scores_all: list[float] = []
    report_rates: list[float] = []
    coalition_counts: list[float] = []
    total_joint_completed = 0
    total_single_completed = 0

    n_modules = env.n_arms

    for ep in range(num_episodes):
        obs_np, _ = env.reset(seed=seed + ep)
        model.reset(batch_size=1, device=device)
        obs = torch.tensor(obs_np, dtype=torch.float32, device=device).unsqueeze(0)

        for t in range(env.max_steps):
            with torch.no_grad():
                out = model.step(obs, deterministic=True)

            actions = out["actions"][0].cpu().numpy()
            report_rate = float(out["report_rate"])
            report_rates.append(report_rate)

            # Extract pairwise coalition matrix A: (N, N)
            c_mat = out["coalition_matrix"][0].cpu().numpy()
            coalition_counts.append(float(np.sum(c_mat > threshold)))

            # Check ground truth for all adjacent pairs (i, (i+1)%N)
            next_obs_np, rewards, term, trunc, step_info = env.step(actions)
            ground_truth_pairs = step_info["joint_ground_truth"]  # List of bools for each (i, i+1)

            for i in range(n_modules):
                j = (i + 1) % n_modules
                gt_label = 1 if ground_truth_pairs[i] else 0
                pred_score = float(max(c_mat[i, j], c_mat[j, i]))
                pred_label = 1 if pred_score >= threshold else 0

                y_true_all.append(gt_label)
                y_pred_all.append(pred_label)
                y_scores_all.append(pred_score)

            total_joint_completed += step_info["joint_completed"]
            total_single_completed += step_info["single_completed"]
            obs = torch.tensor(next_obs_np, dtype=torch.float32, device=device).unsqueeze(0)

            if term or trunc:
                break

    y_true = np.array(y_true_all)
    y_pred = np.array(y_pred_all)

    # Compute contingency table
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-6)

    # Phi coefficient (Matthews correlation coefficient)
    denom = np.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    phi_corr = ((tp * tn) - (fp * fn)) / max(denom, 1e-8)

    # Shuffled null-distribution chance correlation
    shuffled_pred = np.random.permutation(y_pred)
    tp_shuf = np.sum((y_true == 1) & (shuffled_pred == 1))
    fp_shuf = np.sum((y_true == 0) & (shuffled_pred == 1))
    fn_shuf = np.sum((y_true == 1) & (shuffled_pred == 0))
    tn_shuf = np.sum((y_true == 0) & (shuffled_pred == 0))
    denom_shuf = np.sqrt(
        float((tp_shuf + fp_shuf) * (tp_shuf + fn_shuf) * (tn_shuf + fp_shuf) * (tn_shuf + fn_shuf))
    )
    phi_chance = ((tp_shuf * tn_shuf) - (fp_shuf * fn_shuf)) / max(denom_shuf, 1e-8)

    return {
        "mean_report_rate": float(np.mean(report_rates)),
        "mean_coalition_freq": float(np.mean(coalition_counts)),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "phi_correlation": phi_corr,
        "phi_chance": phi_chance,
        "joint_completed": total_joint_completed,
        "single_completed": total_single_completed,
    }


def run_coalition_analysis_experiment(
    num_episodes: int = 25,
) -> None:
    """Run coalition alignment analysis against chance and AlwaysLocal baseline."""
    print("=" * 80)
    print("OCTOPUS-BRAIN: COALITION FORMATION ALIGNMENT EXPERIMENT")
    print("=" * 80)

    device = torch.device("cpu")
    config = OctopusBrainConfig(n_modules=8, hidden_dim=64, message_dim=32)
    env_config = EnvConfig(n_arms=8, max_steps=40)
    env = ReachAndAvoidEnv(env_config)

    print("Instantiating OctopusBrain and AlwaysLocalBaseline (Ablation 3)...")
    octopus_model = OctopusBrain(config).to(device)
    local_model = AlwaysLocalBaseline(config).to(device)

    # 1. CRITICAL PRE-LOGGING: Verify gate health before analyzing performance
    print("\n" + "-" * 80)
    print("CRITICAL GATE HEALTH & COALITION PRE-LOGGING:")
    print("-" * 80)

    eval_oct = evaluate_coalition_correlation(
        env, octopus_model, num_episodes=num_episodes, seed=42, device=device
    )
    report_rate_pct = eval_oct["mean_report_rate"] * 100.0
    print(f"[*] OctopusBrain Mean Report Rate:   {report_rate_pct:.2f}%")
    print(
        f"[*] OctopusBrain Mean Active Coalitions: {eval_oct['mean_coalition_freq']:.2f} per step"
    )

    if report_rate_pct <= 0.01:
        print("[WARNING] DEGENERATE GATE: Report rate is 0%!")
    elif report_rate_pct >= 99.9:
        print("[WARNING] DEGENERATE GATE: Report rate is 100%!")
    else:
        print("[OK] Gate is non-degenerate and sparsely triggered.")
    print("-" * 80)

    # 2. Evaluate Baseline 3 (AlwaysLocal)
    print("\nEvaluating AlwaysLocalBaseline (No Coalition Mechanism)...")
    eval_local = evaluate_coalition_correlation(
        env, local_model, num_episodes=num_episodes, seed=42, device=device
    )

    # 3. Print Detailed Comparison
    print("\n" + "=" * 80)
    print("COALITION DETECTION & TASK ALIGNMENT METRICS")
    print("=" * 80)
    print(
        f"{'Metric':<30}{'OctopusBrain':<20}{'Chance (Shuffled)':<20}{'Always Local (Ablation 3)':<20}"
    )
    print("-" * 80)
    print(f"{'Report Rate':<30}{eval_oct['mean_report_rate'] * 100:>6.1f}%{'N/A':>20}{'0.0%':>20}")
    print(
        f"{'Precision':<30}{eval_oct['precision']:>6.3f}{'N/A':>20}{eval_local['precision']:>6.3f}"
    )
    print(f"{'Recall':<30}{eval_oct['recall']:>6.3f}{'N/A':>20}{eval_local['recall']:>6.3f}")
    print(f"{'F1 Score':<30}{eval_oct['f1']:>6.3f}{'N/A':>20}{eval_local['f1']:>6.3f}")
    print(
        f"{'Phi Correlation (r_phi)':<30}{eval_oct['phi_correlation']:>+6.3f}{eval_oct['phi_chance']:>+15.3f}{eval_local['phi_correlation']:>+15.3f}"
    )
    print(
        f"{'Joint Tasks Completed':<30}{eval_oct['joint_completed']:>6d}{'N/A':>20}{eval_local['joint_completed']:>6d}"
    )
    print(
        f"{'Single Tasks Completed':<30}{eval_oct['single_completed']:>6d}{'N/A':>20}{eval_local['single_completed']:>6d}"
    )
    print("=" * 80)

    if eval_oct["phi_correlation"] > eval_oct["phi_chance"] + 0.05:
        print(
            "[CONCLUSION] Hypothesis supported: Coalition formation correlates with joint subtasks above chance."
        )
    else:
        print("[CONCLUSION] Neutral / early result: Gating policy requires additional task tuning.")
    print("Coalition analysis experiment complete.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OctopusBrain Coalition Analysis Experiment")
    parser.add_argument("--episodes", type=int, default=25, help="Number of evaluation episodes")
    args = parser.parse_args()

    run_coalition_analysis_experiment(num_episodes=args.episodes)
