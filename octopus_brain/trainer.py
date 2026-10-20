"""Production-Grade Actor-Critic Trainer with GAE & Adaptive Lagrangian Gating for OctopusBrain."""

from typing import Dict, List, Optional, Tuple, Any
import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR

from octopus_brain.config import OctopusBrainConfig, EnvConfig
from octopus_brain.brain import OctopusBrain
from octopus_brain.losses import OctopusLoss
from envs.reach_and_avoid import ReachAndAvoidEnv


class OctopusTrainer:
    """End-to-end multi-agent reinforcement learning trainer for OctopusBrain architectures."""

    def __init__(
        self,
        model: OctopusBrain,
        env: ReachAndAvoidEnv,
        config: Optional[OctopusBrainConfig] = None,
        lr: float = 0.002,
        gamma: float = 0.96,
        gae_lambda: float = 0.92,
        max_grad_norm: float = 1.0,
        device: Optional[torch.device] = None,
        algorithm: str = "ppo",
        ppo_epochs: int = 3,
        clip_eps: float = 0.2,
        normalize_advantages: bool = True,
        lr_schedule: bool = True,
        entropy_anneal: bool = True,
        entropy_init: float = 0.04,
        entropy_final: float = 0.005,
        curiosity_coef: float = 0.02,
        batch_episodes: int = 1,
    ):
        self.config = config or model.config
        self.model = model
        self.env = env
        self.lr = lr
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.max_grad_norm = max_grad_norm
        self.device = device or torch.device("cpu")
        self.algorithm = algorithm.lower()
        self.ppo_epochs = max(1, ppo_epochs)
        self.clip_eps = clip_eps
        self.normalize_advantages = normalize_advantages
        self.lr_schedule = lr_schedule
        self.entropy_anneal = entropy_anneal
        self.entropy_init = entropy_init
        self.entropy_final = entropy_final
        self.curiosity_coef = curiosity_coef
        self.batch_episodes = max(1, batch_episodes)

        self.model.to(self.device)
        self.optimizer = optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=1e-4)
        self.scheduler: Optional[CosineAnnealingLR] = None
        self.loss_fn = OctopusLoss(self.config)
        self.history: Dict[str, List[float]] = {
            "episode_rewards": [],
            "mean_report_rates": [],
            "total_losses": [],
            "policy_losses": [],
            "value_losses": [],
            "entropy_losses": [],
            "forward_losses": [],
            "dual_lambdas": [],
            "single_hits": [],
            "joint_hits": [],
            "hazard_hits": [],
        }

    def collect_episode(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Run a single rollout episode and package trajectory tensors for learning."""
        self.model.train()
        obs_np, _ = self.env.reset(seed=seed)
        self.model.reset(batch_size=1, device=self.device)
        obs = torch.tensor(obs_np, dtype=torch.float32, device=self.device).unsqueeze(0)

        obs_list = []
        actions_list = []
        log_probs_list = []
        entropies_list = []
        values_list = []
        rewards_list = []
        report_probs_list = []
        pred_obs_list = []
        actual_obs_list = []
        dones_list = []

        single_target_hits = 0
        joint_target_hits = 0
        hazard_collisions = 0
        total_reward = 0.0

        for t in range(self.env.max_steps):
            obs_list.append(obs.detach().clone())
            out = self.model.step(obs, deterministic=False)
            actions = out["actions"][0].detach().cpu().numpy()
            actions_list.append(out["actions"].detach().clone())

            next_obs_np, env_rewards, term, trunc, info = self.env.step(actions)
            next_obs = torch.tensor(next_obs_np, dtype=torch.float32, device=self.device).unsqueeze(0)

            # Intrinsic curiosity reward from forward-model surprise
            step_rewards = env_rewards.copy()
            if self.curiosity_coef > 0:
                surprises = out.get("surprise_values", torch.zeros_like(out["actions"].float()))[0].detach().cpu().numpy()
                intrinsic_reward = self.curiosity_coef * np.clip(surprises, 0.0, 1.0)
                step_rewards = step_rewards + intrinsic_reward

            # Metrics
            total_reward += float(np.sum(env_rewards))
            single_target_hits += info.get("single_target_hits", info.get("single_completed", 0))
            joint_target_hits += info.get("joint_target_hits", info.get("joint_completed", 0))
            hazard_collisions += info.get("hazard_collisions", info.get("hazard_hits", 0))

            log_probs_list.append(out["action_log_probs"])  # (1, N)
            entropies_list.append(out["action_entropies"])
            values_list.append(out["values"])              # (1, N, 1)
            rewards_list.append(torch.tensor(step_rewards, dtype=torch.float32, device=self.device).unsqueeze(0))
            report_probs_list.append(out["report_probs"])
            pred_obs_list.append(out["pred_next_obs"])
            actual_obs_list.append(next_obs)
            dones_list.append(term or trunc)

            obs = next_obs
            if term or trunc:
                break

        T = len(rewards_list)
        values = torch.stack(values_list, dim=0).squeeze(-1)  # (T, 1, N)
        rewards_t = torch.stack(rewards_list, dim=0)          # (T, 1, N)

        # 1. Generalized Advantage Estimation (GAE)
        advantages = torch.zeros_like(rewards_t)
        last_gae = torch.zeros(1, self.env.n_arms, device=self.device)

        for t in reversed(range(T)):
            if t == T - 1:
                next_val = torch.zeros(1, self.env.n_arms, device=self.device)
            else:
                next_val = values[t + 1]

            delta = rewards_t[t] + self.gamma * next_val - values[t]
            last_gae = delta + self.gamma * self.gae_lambda * last_gae
            advantages[t] = last_gae

        returns = advantages + values

        return {
            "log_probs": torch.stack(log_probs_list, dim=0),      # (T, 1, N)
            "entropies": torch.stack(entropies_list, dim=0),      # (T, 1, N)
            "values": torch.stack(values_list, dim=0),            # (T, 1, N, 1)
            "returns": returns,                                   # (T, 1, N)
            "advantages": advantages,                             # (T, 1, N)
            "obs_list": obs_list,                                 # List of T tensors (1, N, obs_dim)
            "actions_list": actions_list,                         # List of T tensors (1, N)
            "report_probs": torch.stack(report_probs_list, dim=0),# (T, 1, N)
            "pred_obs": torch.stack(pred_obs_list, dim=0),        # (T, 1, N, obs_dim)
            "actual_obs": torch.stack(actual_obs_list, dim=0),    # (T, 1, N, obs_dim)
            "total_reward": total_reward,
            "mean_report_rate": float(torch.stack(report_probs_list).mean().item()),
            "single_hits": single_target_hits,
            "joint_hits": joint_target_hits,
            "hazard_hits": hazard_collisions,
        }

    def train_step(self, trajectory: Dict[str, Any]) -> Dict[str, float]:
        """Perform policy gradient / PPO & Lagrangian dual optimization step."""
        if self.algorithm == "ppo" and "obs_list" in trajectory and "actions_list" in trajectory:
            return self._train_step_ppo(trajectory)
        else:
            return self._train_step_a2c(trajectory)

    def _train_step_a2c(self, trajectory: Dict[str, Any]) -> Dict[str, float]:
        """Single-step Actor-Critic update with normalized GAE advantage."""
        self.model.train()
        self.optimizer.zero_grad()

        losses = self.loss_fn(
            action_log_probs=trajectory["log_probs"],
            action_entropies=trajectory["entropies"],
            values=trajectory["values"],
            returns=trajectory["returns"],
            report_probs=trajectory["report_probs"],
            pred_obs=trajectory["pred_obs"],
            actual_next_obs=trajectory["actual_obs"],
            advantages=trajectory.get("advantages"),
            normalize_adv=self.normalize_advantages,
        )

        losses["total_loss"].backward()
        if self.max_grad_norm > 0:
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
        self.optimizer.step()

        # Update Lagrangian dual multiplier
        if self.loss_fn.adaptive_budgeting and self.loss_fn.gate_budgeter is not None:
            self.loss_fn.gate_budgeter.update_dual_step(trajectory["mean_report_rate"])

        return {
            "total_loss": float(losses["total_loss"].item()),
            "policy_loss": float(losses["policy_loss"].item()),
            "value_loss": float(losses["value_loss"].item()),
            "entropy_loss": float(losses["entropy_loss"].item()),
            "forward_loss": float(losses["forward_model_loss"].item()),
            "dual_lambda": float(losses["dual_lambda"]),
        }

    def _train_step_ppo(self, trajectory: Dict[str, Any]) -> Dict[str, float]:
        """Multi-epoch PPO clipped surrogate optimization over the trajectory."""
        old_log_probs = trajectory["log_probs"].detach()
        returns = trajectory["returns"].detach()
        advantages = trajectory.get("advantages", trajectory["returns"] - trajectory["values"].squeeze(-1)).detach()
        actual_obs = trajectory["actual_obs"].detach()
        obs_seq = trajectory["obs_list"]
        actions_seq = trajectory["actions_list"]
        T = len(obs_seq)

        tot_loss, pol_loss, val_loss, ent_loss, fwd_loss, dual_lam = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        for _ in range(self.ppo_epochs):
            self.model.train()
            self.model.reset(batch_size=1, device=self.device)
            self.optimizer.zero_grad()

            new_log_probs_list = []
            new_entropies_list = []
            new_values_list = []
            new_report_probs_list = []
            new_pred_obs_list = []

            for t in range(T):
                out = self.model.step(obs_seq[t], deterministic=False)
                logits = out["action_logits"]  # (1, N, action_dim)
                dist = torch.distributions.Categorical(logits=logits)
                act = actions_seq[t]          # (1, N)
                new_log_probs_list.append(dist.log_prob(act))
                new_entropies_list.append(dist.entropy())
                new_values_list.append(out["values"])
                new_report_probs_list.append(out["report_probs"])
                new_pred_obs_list.append(out["pred_next_obs"])

            new_log_probs = torch.stack(new_log_probs_list, dim=0)
            new_entropies = torch.stack(new_entropies_list, dim=0)
            new_values = torch.stack(new_values_list, dim=0)
            new_report_probs = torch.stack(new_report_probs_list, dim=0)
            new_pred_obs = torch.stack(new_pred_obs_list, dim=0)

            losses = self.loss_fn(
                action_log_probs=new_log_probs,
                action_entropies=new_entropies,
                values=new_values,
                returns=returns,
                report_probs=new_report_probs,
                pred_obs=new_pred_obs,
                actual_next_obs=actual_obs,
                old_action_log_probs=old_log_probs,
                clip_eps=self.clip_eps,
                advantages=advantages,
                normalize_adv=self.normalize_advantages,
            )

            losses["total_loss"].backward()
            if self.max_grad_norm > 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
            self.optimizer.step()

            tot_loss += float(losses["total_loss"].item())
            pol_loss += float(losses["policy_loss"].item())
            val_loss += float(losses["value_loss"].item())
            ent_loss += float(losses["entropy_loss"].item())
            fwd_loss += float(losses["forward_model_loss"].item())
            dual_lam = float(losses["dual_lambda"])

        # Update Lagrangian dual multiplier step
        if self.loss_fn.adaptive_budgeting and self.loss_fn.gate_budgeter is not None:
            self.loss_fn.gate_budgeter.update_dual_step(trajectory["mean_report_rate"])

        n_epochs = max(1, self.ppo_epochs)
        return {
            "total_loss": tot_loss / n_epochs,
            "policy_loss": pol_loss / n_epochs,
            "value_loss": val_loss / n_epochs,
            "entropy_loss": ent_loss / n_epochs,
            "forward_loss": fwd_loss / n_epochs,
            "dual_lambda": dual_lam,
        }

    def evaluate(self, n_episodes: int = 10, seed: int = 42) -> Dict[str, float]:
        """Run deterministic evaluation and compute aggregate metrics."""
        self.model.eval()
        rewards = []
        report_rates = []
        single_hits = []
        joint_hits = []
        hazard_hits = []
        coalition_sizes = []

        for ep in range(n_episodes):
            obs_np, _ = self.env.reset(seed=seed + ep)
            self.model.reset(batch_size=1, device=self.device)
            obs = torch.tensor(obs_np, dtype=torch.float32, device=self.device).unsqueeze(0)

            ep_rew = 0.0
            ep_reports = []
            ep_single = 0
            ep_joint = 0
            ep_hazards = 0
            ep_coalitions = []

            for _ in range(self.env.max_steps):
                with torch.no_grad():
                    out = self.model.step(obs, deterministic=True)
                actions = out["actions"][0].detach().cpu().numpy()
                next_obs_np, r, term, trunc, info = self.env.step(actions)

                ep_rew += float(np.sum(r))
                ep_reports.append(float(out["report_probs"].mean().item()))
                ep_coalitions.append(float(len(out.get("active_coalitions", []))))
                ep_single += info.get("single_target_hits", info.get("single_completed", 0))
                ep_joint += info.get("joint_target_hits", info.get("joint_completed", 0))
                ep_hazards += info.get("hazard_collisions", info.get("hazard_hits", 0))

                obs = torch.tensor(next_obs_np, dtype=torch.float32, device=self.device).unsqueeze(0)
                if term or trunc:
                    break

            rewards.append(ep_rew)
            report_rates.append(np.mean(ep_reports))
            coalition_sizes.append(np.mean(ep_coalitions))
            single_hits.append(ep_single)
            joint_hits.append(ep_joint)
            hazard_hits.append(ep_hazards)

        return {
            "mean_reward": float(np.mean(rewards)),
            "std_reward": float(np.std(rewards)),
            "mean_report_rate": float(np.mean(report_rates)),
            "mean_coalition_size": float(np.mean(coalition_sizes)),
            "mean_single_hits": float(np.mean(single_hits)),
            "mean_joint_hits": float(np.mean(joint_hits)),
            "mean_hazard_hits": float(np.mean(hazard_hits)),
        }

    def train_batch(self, trajectories: List[Dict[str, Any]]) -> Dict[str, float]:
        """Multi-trajectory batched gradient update."""
        loss_dicts = []
        for traj in trajectories:
            ld = self.train_step(traj)
            loss_dicts.append(ld)
        keys = loss_dicts[0].keys()
        return {k: float(np.mean([d[k] for d in loss_dicts])) for k in keys}

    def train(
        self,
        num_episodes: int = 120,
        eval_every: int = 20,
        checkpoint_path: Optional[str] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """Complete training loop with periodic evaluations and best model checkpointing."""
        if verbose:
            print("=" * 80)
            print(f"STARTING OCTOPUSBRAIN TRAINING ({num_episodes} Episodes)")
            print(f"Architecture: {self.config.n_modules} Arms | Hidden: {self.config.hidden_dim} | Device: {self.device}")
            print(f"Algorithm: {self.algorithm.upper()} (epochs={self.ppo_epochs}, clip={self.clip_eps}) | Batch Rollouts: {self.batch_episodes}")
            print(f"Curiosity Bonus Coef: {self.curiosity_coef}")
            print("=" * 80)

        best_eval_reward = -float("inf")
        start_time = time.time()

        if self.lr_schedule and self.scheduler is None:
            self.scheduler = CosineAnnealingLR(self.optimizer, T_max=num_episodes, eta_min=1e-5)

        for ep in range(1, num_episodes + 1):
            # Entropy Annealing: High exploration initially, fine-tuned deterministic precision late
            if self.entropy_anneal:
                progress = min(1.0, float(ep) / max(1, num_episodes))
                self.loss_fn.entropy_coef = self.entropy_init + progress * (self.entropy_final - self.entropy_init)

            # Collect episode trajectory (or multiple parallel rollouts)
            if self.batch_episodes <= 1:
                trajectory = self.collect_episode(seed=100 + ep)
                loss_dict = self.train_step(trajectory)
                trajectories = [trajectory]
            else:
                trajectories = [
                    self.collect_episode(seed=100 + (ep - 1) * self.batch_episodes + b)
                    for b in range(self.batch_episodes)
                ]
                loss_dict = self.train_batch(trajectories)
                trajectory = trajectories[0]

            if self.scheduler is not None:
                self.scheduler.step()

            # Record metrics (averaged across batch rollouts)
            mean_ep_rew = float(np.mean([t["total_reward"] for t in trajectories]))
            mean_ep_rep = float(np.mean([t["mean_report_rate"] for t in trajectories]))
            mean_single = float(np.mean([t["single_hits"] for t in trajectories]))
            mean_joint = float(np.mean([t["joint_hits"] for t in trajectories]))
            mean_haz = float(np.mean([t["hazard_hits"] for t in trajectories]))

            self.history["episode_rewards"].append(mean_ep_rew)
            self.history["mean_report_rates"].append(mean_ep_rep)
            self.history["total_losses"].append(loss_dict["total_loss"])
            self.history["policy_losses"].append(loss_dict["policy_loss"])
            self.history["value_losses"].append(loss_dict["value_loss"])
            self.history["entropy_losses"].append(loss_dict["entropy_loss"])
            self.history["forward_losses"].append(loss_dict["forward_loss"])
            self.history["dual_lambdas"].append(loss_dict["dual_lambda"])
            self.history["single_hits"].append(mean_single)
            self.history["joint_hits"].append(mean_joint)
            self.history["hazard_hits"].append(mean_haz)

            # Curriculum Stage Progression Check
            if hasattr(self.env, "scheduler") and self.env.scheduler is not None:
                graduated = self.env.scheduler.record_episode(
                    mean_ep_rew, mean_haz, ep
                )
                if graduated and verbose:
                    print(
                        f"\n{'*'*70}\n"
                        f"🎓 [CURRICULUM ADVANCEMENT] Graduated to: {self.env.scheduler.current_stage_name}!\n"
                        f"{'*'*70}\n"
                    )

            # Periodic Evaluation & Logging
            if ep % eval_every == 0 or ep == num_episodes:
                eval_metrics = self.evaluate(n_episodes=8, seed=9000 + ep)
                elapsed = time.time() - start_time

                if verbose:
                    print(
                        f"[Ep {ep:03d}/{num_episodes}] "
                        f"Train Rew: {np.mean(self.history['episode_rewards'][-eval_every:]):+6.2f} | "
                        f"Eval Rew: {eval_metrics['mean_reward']:+6.2f} | "
                        f"Comm Rate: {eval_metrics['mean_report_rate']*100:4.1f}% | "
                        f"Dual λ: {loss_dict['dual_lambda']:4.2f} | "
                        f"Joint Hits: {eval_metrics['mean_joint_hits']:3.1f} | "
                        f"Hazards: {eval_metrics['mean_hazard_hits']:3.1f} | "
                        f"Time: {elapsed:4.1f}s"
                    )

                if checkpoint_path and eval_metrics["mean_reward"] > best_eval_reward:
                    best_eval_reward = eval_metrics["mean_reward"]
                    self.save_checkpoint(checkpoint_path)
                    if verbose:
                        print(f"  --> Saved new best checkpoint to {checkpoint_path} (Eval Rew: {best_eval_reward:+.2f})")

        return {
            "best_eval_reward": best_eval_reward,
            "final_eval": self.evaluate(n_episodes=15, seed=9999),
            "history": self.history,
        }

    def save_checkpoint(self, path: str) -> None:
        """Save model weights, optimizer state, and training history."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "config": self.config,
                "history": self.history,
            },
            path,
        )

    def load_checkpoint(self, path: str) -> None:
        """Load model weights and config from checkpoint."""
        try:
            checkpoint = torch.load(path, map_location=self.device, weights_only=True)
        except TypeError:
            checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        if "optimizer_state_dict" in checkpoint:
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        if "history" in checkpoint:
            self.history = checkpoint["history"]
