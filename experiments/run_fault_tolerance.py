"""Fault Tolerance Experiment: Module Knockout Degradation Analysis.

Evaluates how graceful degradation is when random peripheral arm modules
are severed / killed mid-episode, comparing OctopusBrain against DenseCentralizedBaseline.

CRITICAL PROTOCOL:
Logs report rate and coalition statistics BEFORE reporting any task-performance numbers.
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Dict, List, Tuple, Optional
import numpy as np
import torch
import torch.optim as optim

from octopus_brain.config import OctopusBrainConfig, EnvConfig
from octopus_brain.brain import OctopusBrain
from octopus_brain.losses import OctopusLoss
from envs.reach_and_avoid import ReachAndAvoidEnv
from experiments.baselines import DenseCentralizedBaseline, AlwaysLocalBaseline


def run_episode(
    env: ReachAndAvoidEnv,
    model: torch.nn.Module,
    num_killed: int = 0,
    kill_step: int = 15,
    seed: int = 42,
    device: torch.device = torch.device("cpu"),
) -> Dict[str, float]:
    """Execute one rollout with random module knockout mid-episode."""
    obs_np, info = env.reset(seed=seed)
    n_modules = env.n_arms
    model.reset(batch_size=1, device=device)

    # Choose random modules to kill
    rng = np.random.RandomState(seed)
    killed_indices = rng.choice(n_modules, size=num_killed, replace=False) if num_killed > 0 else []

    active_mask = torch.ones(n_modules, dtype=torch.bool, device=device)
    episode_reward = 0.0
    report_rates = []
    coalition_sizes = []
    single_success = 0
    joint_success = 0
    hazard_hits = 0

    obs = torch.tensor(obs_np, dtype=torch.float32, device=device).unsqueeze(0)  # (1, N, obs_dim)

    for t in range(env.max_steps):
        # Kill modules at kill_step
        if t >= kill_step and num_killed > 0:
            for idx in killed_indices:
                active_mask[idx] = False

        with torch.no_grad():
            if isinstance(model, DenseCentralizedBaseline):
                out = model.step(obs, active_mask=active_mask, deterministic=True)
            else:
                out = model.step(obs, active_mask=active_mask, deterministic=True)

        actions = out["actions"][0].cpu().numpy()
        report_rate = out["report_rate"]
        report_rates.append(report_rate)

        # Active coalition count
        if "coalition_matrix" in out and out["coalition_matrix"].numel() > 0:
            c_mat = out["coalition_matrix"][0].cpu().numpy()
            n_active_coalitions = np.sum(c_mat > 0.15)
            coalition_sizes.append(float(n_active_coalitions))
        else:
            coalition_sizes.append(0.0)

        next_obs_np, rewards, terminated, truncated, step_info = env.step(actions)
        # Inactive modules do not collect reward
        for idx in killed_indices:
            if t >= kill_step:
                rewards[idx] = 0.0

        episode_reward += float(np.sum(rewards))
        single_success += step_info["single_completed"]
        joint_success += step_info["joint_completed"]
        hazard_hits += step_info["hazard_hits"]

        obs = torch.tensor(next_obs_np, dtype=torch.float32, device=device).unsqueeze(0)
        if terminated or truncated:
            break

    return {
        "reward": episode_reward,
        "single_success": single_success,
        "joint_success": joint_success,
        "hazard_hits": hazard_hits,
        "mean_report_rate": float(np.mean(report_rates)),
        "mean_coalition_size": float(np.mean(coalition_sizes)),
    }


def train_quick_policy(
    model: torch.nn.Module,
    env: ReachAndAvoidEnv,
    num_episodes: int = 60,
    lr: float = 0.003,
    device: torch.device = torch.device("cpu"),
) -> None:
    """Lightweight CPU training loop for demonstration and calibration."""
    model.train()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    loss_fn = OctopusLoss()

    for ep in range(num_episodes):
        obs_np, _ = env.reset(seed=ep)
        model.reset(batch_size=1, device=device)
        obs = torch.tensor(obs_np, dtype=torch.float32, device=device).unsqueeze(0)

        log_probs_list = []
        entropies_list = []
        values_list = []
        rewards_list = []
        report_probs_list = []
        pred_obs_list = []
        actual_obs_list = []

        for t in range(env.max_steps):
            out = model.step(obs, deterministic=False)
            actions = out["actions"][0].detach().cpu().numpy()

            next_obs_np, rewards, term, trunc, _ = env.step(actions)
            next_obs = torch.tensor(next_obs_np, dtype=torch.float32, device=device).unsqueeze(0)

            log_probs_list.append(out["action_log_probs"])
            entropies_list.append(out["action_entropies"])
            values_list.append(out["values"])
            rewards_list.append(torch.tensor(rewards, dtype=torch.float32, device=device).unsqueeze(0))
            report_probs_list.append(out["report_probs"])
            pred_obs_list.append(out["pred_next_obs"])
            actual_obs_list.append(next_obs)

            obs = next_obs
            if term or trunc:
                break

        # Compute discounted returns
        T = len(rewards_list)
        returns = []
        R = torch.zeros(1, env.n_arms, device=device)
        gamma = 0.95
        for t in reversed(range(T)):
            R = rewards_list[t] + gamma * R
            returns.insert(0, R)

        returns_t = torch.stack(returns, dim=0)  # (T, 1, N)
        log_probs_t = torch.stack(log_probs_list, dim=0)  # (T, 1, N)
        entropies_t = torch.stack(entropies_list, dim=0)
        values_t = torch.stack(values_list, dim=0)
        report_probs_t = torch.stack(report_probs_list, dim=0)
        pred_obs_t = torch.stack(pred_obs_list, dim=0)
        actual_obs_t = torch.stack(actual_obs_list, dim=0)

        losses = loss_fn(
            action_log_probs=log_probs_t,
            action_entropies=entropies_t,
            values=values_t,
            returns=returns_t,
            report_probs=report_probs_t,
            pred_obs=pred_obs_t,
            actual_next_obs=actual_obs_t,
        )

        optimizer.zero_grad()
        losses["total_loss"].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()


def run_fault_tolerance_experiment(
    num_trials: int = 15,
    train_steps: int = 40,
    checkpoint_path: Optional[str] = "checkpoints/best_octopus_brain.pt",
) -> None:
    """Run fault tolerance evaluation across different module knockout counts."""
    print("=" * 80)
    print("OCTOPUS-BRAIN: FAULT TOLERANCE & MODULE KNOCKOUT EXPERIMENT")
    print(f"Checkpoint: {checkpoint_path if (checkpoint_path and os.path.exists(checkpoint_path)) else 'Quick Calibration'}")
    print("=" * 80)

    device = torch.device("cpu")
    config = OctopusBrainConfig(n_modules=8, hidden_dim=64, message_dim=32)
    env_config = EnvConfig(n_arms=8, max_steps=40)
    env = ReachAndAvoidEnv(env_config)

    print(f"Instantiating OctopusBrain (N={config.n_modules}) and DenseCentralizedBaseline...")
    octopus_model = OctopusBrain(config).to(device)
    dense_model = DenseCentralizedBaseline(config).to(device)

    # Load checkpoint if provided
    has_checkpoint = False
    if checkpoint_path and os.path.exists(checkpoint_path):
        try:
            ckpt = torch.load(checkpoint_path, map_location=device, weights_only=True)
        except TypeError:
            ckpt = torch.load(checkpoint_path, map_location=device)
        octopus_model.load_state_dict(ckpt["model_state_dict"])
        print(f"--> Loaded trained OctopusBrain checkpoint: {checkpoint_path}")
        has_checkpoint = True

    print(f"OctopusBrain parameters:        {sum(p.numel() for p in octopus_model.parameters()):,}")
    print(f"DenseCentralized parameters:    {sum(p.numel() for p in dense_model.parameters()):,}")

    if train_steps > 0:
        if not has_checkpoint:
            print(f"\nCalibrating OctopusBrain ({train_steps} training episodes on CPU)...")
            train_quick_policy(octopus_model, env, num_episodes=train_steps, device=device)
        print(f"Calibrating DenseCentralized baseline ({train_steps} training episodes on CPU)...")
        train_quick_policy(dense_model, env, num_episodes=train_steps, device=device)

    octopus_model.eval()
    dense_model.eval()

    knockout_counts = [0, 1, 2, 3, 4]
    results_octopus = {k: [] for k in knockout_counts}
    results_dense = {k: [] for k in knockout_counts}

    # 1. DIAGNOSTIC PRE-LOGGING: Check gating health FIRST!
    print("\n" + "-" * 80)
    print("CRITICAL GATE HEALTH DIAGNOSTICS (BEFORE TASK PERFORMANCE):")
    print("-" * 80)

    pre_diag = run_episode(env, octopus_model, num_killed=0, seed=100, device=device)
    report_rate_pct = pre_diag["mean_report_rate"] * 100.0
    print(f"[*] OctopusBrain Initial Report Rate: {report_rate_pct:.2f}%")
    print(f"[*] OctopusBrain Mean Coalition Size: {pre_diag['mean_coalition_size']:.2f} active bindings/step")

    if report_rate_pct <= 0.01:
        print("[WARNING] DEGENERATE GATE DETECTED: Report rate is 0.0% (Never triggering)!")
    elif report_rate_pct >= 99.9:
        print("[WARNING] DEGENERATE GATE DETECTED: Report rate is 100.0% (Always reporting)!")
    else:
        print("[OK] Gate is operating in healthy sparse regime (0% < Rate < 100%).")
    print("-" * 80)

    # 2. Run Knockout Degradation Curves
    print("\nRunning module knockout trials across degradation conditions...")
    for k in knockout_counts:
        for seed in range(num_trials):
            res_oct = run_episode(env, octopus_model, num_killed=k, seed=1000 + seed, device=device)
            res_dns = run_episode(env, dense_model, num_killed=k, seed=1000 + seed, device=device)
            results_octopus[k].append(res_oct)
            results_dense[k].append(res_dns)

    # 3. Print Results Table
    print("\n" + "=" * 80)
    print(f"{'Modules Killed':<15}{'OctopusBrain Reward':<22}{'Dense Central Reward':<22}{'Octopus Retained %':<20}")
    print("=" * 80)

    base_oct_rew = np.mean([r["reward"] for r in results_octopus[0]])
    base_dns_rew = np.mean([r["reward"] for r in results_dense[0]])

    for k in knockout_counts:
        oct_rews = [r["reward"] for r in results_octopus[k]]
        dns_rews = [r["reward"] for r in results_dense[k]]
        oct_mean = float(np.mean(oct_rews))
        dns_mean = float(np.mean(dns_rews))
        oct_retention = (oct_mean / max(base_oct_rew, 1e-4)) * 100.0 if base_oct_rew > 0 else 100.0
        dns_retention = (dns_mean / max(base_dns_rew, 1e-4)) * 100.0 if base_dns_rew > 0 else 100.0

        print(f"{k:<15}{oct_mean:>8.2f} (std {np.std(oct_rews):.2f})    {dns_mean:>8.2f} (std {np.std(dns_rews):.2f})    {oct_retention:>6.1f}% vs {dns_retention:>5.1f}%")

    print("=" * 80)
    print("Fault Tolerance summary complete.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OctopusBrain Fault Tolerance Experiment")
    parser.add_argument("--trials", type=int, default=15, help="Number of trials per knockout condition")
    parser.add_argument("--train-steps", type=int, default=30, help="Number of baseline calibration training episodes")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/best_octopus_brain.pt", help="Path to trained OctopusBrain checkpoint")
    args = parser.parse_args()

    run_fault_tolerance_experiment(
        num_trials=args.trials,
        train_steps=args.train_steps,
        checkpoint_path=args.checkpoint,
    )
