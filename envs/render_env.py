"""Visual Trajectory Animator for ReachAndAvoid environment and OctopusBrain.

Features:
- Real-time ASCII terminal animation
- Matplotlib 2D high-resolution renderer
- Dynamic coalition binding visualization (drawing colored coordination arcs between arms)
- Export to animated GIF or video
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.animation import FuncAnimation, PillowWriter
from octopus_brain.brain import OctopusBrain
from octopus_brain.config import EnvConfig, OctopusBrainConfig

from envs.reach_and_avoid import ReachAndAvoidEnv


class EnvironmentVisualizer:
    """Renderer and animator for ReachAndAvoid environment and OctopusBrain."""

    def __init__(self, env: ReachAndAvoidEnv):
        self.env = env
        self.grid_size = env.grid_size
        self.n_arms = env.n_arms

    def render_ascii(
        self,
        step: int,
        reward: float,
        report_rate: float,
        coalition_clusters: list[Any],
        clear_screen: bool = True,
    ) -> str:
        """Render ASCII representation of the grid arena and arm states."""
        grid = [["." for _ in range(self.grid_size)] for _ in range(self.grid_size)]

        # 1. Place Arm Bases
        for _i, (bx, by) in enumerate(self.env.arm_bases):
            ix, iy = (
                int(np.clip(round(bx), 0, self.grid_size - 1)),
                int(np.clip(round(by), 0, self.grid_size - 1)),
            )
            grid[iy][ix] = "b"

        # 2. Place Hazards
        for h in self.env.hazards:
            ix, iy = (
                int(np.clip(round(h[0]), 0, self.grid_size - 1)),
                int(np.clip(round(h[1]), 0, self.grid_size - 1)),
            )
            grid[iy][ix] = "X"

        # 3. Place Single Targets
        for st in self.env.single_targets:
            ix, iy = (
                int(np.clip(round(st[0]), 0, self.grid_size - 1)),
                int(np.clip(round(st[1]), 0, self.grid_size - 1)),
            )
            grid[iy][ix] = "*"

        # 4. Place Joint Targets
        for jt in self.env.joint_targets:
            if jt["active"]:
                ix, iy = (
                    int(np.clip(round(jt["pos"][0]), 0, self.grid_size - 1)),
                    int(np.clip(round(jt["pos"][1]), 0, self.grid_size - 1)),
                )
                grid[iy][ix] = "J"

        # 5. Place Arm Tips
        for i, tip in enumerate(self.env.arm_tips):
            ix, iy = (
                int(np.clip(round(tip[0]), 0, self.grid_size - 1)),
                int(np.clip(round(tip[1]), 0, self.grid_size - 1)),
            )
            grid[iy][ix] = str(i)

        # Build output string
        lines = []
        if clear_screen:
            lines.append("\033[H\033[J")  # ANSI clear screen

        lines.append(
            f"=== ReachAndAvoid Arena | Step: {step:02d} | Reward: {reward:+6.2f} | Report Rate: {report_rate * 100:4.1f}% ==="
        )
        lines.append("+" + "---" * self.grid_size + "+")
        for row in reversed(grid):
            lines.append("|" + "".join(f" {cell} " for cell in row) + "|")
        lines.append("+" + "---" * self.grid_size + "+")

        # Coalition details
        coalition_str = (
            ", ".join(f"C{k}: {sorted(list(c))}" for k, c in enumerate(coalition_clusters))
            or "None (Independent)"
        )
        lines.append(f"Active Ephemeral Coalitions: {coalition_str}")
        lines.append(
            "Legend: [0-7] Arm Tips | [b] Arm Bases | [*] Food | [J] Joint Target | [X] Hazard\n"
        )

        rendered = "\n".join(lines)
        return rendered

    def create_matplotlib_frame(
        self,
        ax: plt.Axes,
        step: int,
        reward: float,
        report_rate: float,
        coalition_matrix: np.ndarray,
        active_edges: list[tuple[int, int, float]],
    ) -> None:
        """Render a single high-fidelity 2D frame on a matplotlib axis."""
        ax.clear()
        ax.set_xlim(-1, self.grid_size + 1)
        ax.set_ylim(-1, self.grid_size + 1)
        ax.set_aspect("equal")
        ax.set_facecolor("#0f172a")  # Dark slate background

        # Arena boundary
        rect = patches.Rectangle(
            (0, 0),
            self.grid_size,
            self.grid_size,
            linewidth=2,
            edgecolor="#334155",
            facecolor="#1e293b",
        )
        ax.add_patch(rect)

        # 1. Draw Hazards
        for h in self.env.hazards:
            circle = patches.Circle((h[0], h[1]), 1.0, color="#ef4444", alpha=0.6, label="Hazard")
            ax.add_patch(circle)
            ax.text(
                h[0],
                h[1],
                "X",
                color="white",
                ha="center",
                va="center",
                fontweight="bold",
                fontsize=9,
            )

        # 2. Draw Single Targets
        for st in self.env.single_targets:
            ax.plot(st[0], st[1], marker="*", markersize=14, color="#eab308", label="Food Target")

        # 3. Draw Joint Targets
        for jt in self.env.joint_targets:
            if jt["active"]:
                pos = jt["pos"]
                circle = patches.Circle(
                    pos, 1.2, edgecolor="#06b6d4", facecolor="#0891b2", alpha=0.5, linewidth=2
                )
                ax.add_patch(circle)
                ax.text(
                    pos[0],
                    pos[1],
                    "JOINT",
                    color="white",
                    ha="center",
                    va="center",
                    fontsize=7,
                    fontweight="bold",
                )

        # 4. Draw Active Coalition Binding Arcs between cooperating arms
        for i, j, weight in active_edges:
            tip_i = self.env.arm_tips[i]
            tip_j = self.env.arm_tips[j]
            ax.plot(
                [tip_i[0], tip_j[0]],
                [tip_i[1], tip_j[1]],
                color="#ec4899",
                linestyle="--",
                linewidth=max(1.5, weight * 4.0),
                alpha=0.85,
                zorder=4,
                label="Coalition Link",
            )

        # 5. Draw Arms (Base -> Tentacle -> Tip)
        palette = [
            "#38bdf8",
            "#818cf8",
            "#a78bfa",
            "#f472b6",
            "#fb7185",
            "#34d399",
            "#4ade80",
            "#fbbf24",
        ]
        for i in range(self.n_arms):
            base = self.env.arm_bases[i]
            tip = self.env.arm_tips[i]
            color = palette[i % len(palette)]

            # Base anchor
            ax.plot(base[0], base[1], marker="s", markersize=8, color="#64748b", zorder=3)

            # Arm reach boundary circle
            reach_circle = patches.Circle(
                base, self.env.arm_reach, color="#475569", fill=False, linestyle=":", alpha=0.3
            )
            ax.add_patch(reach_circle)

            # Arm body tentacle
            ax.plot(
                [base[0], tip[0]],
                [base[1], tip[1]],
                color=color,
                linewidth=3.5,
                alpha=0.8,
                zorder=3,
            )

            # Arm tip
            ax.plot(
                tip[0],
                tip[1],
                marker="o",
                markersize=10,
                color=color,
                markeredgecolor="white",
                markeredgewidth=1.5,
                zorder=5,
            )
            ax.text(
                tip[0],
                tip[1],
                str(i),
                color="black",
                ha="center",
                va="center",
                fontsize=7,
                fontweight="bold",
                zorder=6,
            )

        # Title & HUD
        ax.set_title(
            f"octopus-brain | Step: {step:02d} | Cumulative Reward: {reward:+.2f} | Report Rate: {report_rate * 100:.1f}%\n"
            f"Active Coalitions: {len(active_edges)} bindings active",
            color="white",
            fontsize=10,
            pad=10,
        )
        ax.grid(True, linestyle="--", alpha=0.15, color="white")
        ax.tick_params(colors="gray")


def run_visual_rollout(
    mode: str = "ascii",
    steps: int = 30,
    save_path: str | None = None,
    fps: int = 4,
) -> None:
    """Execute a simulated rollout with full visual animation."""
    config = OctopusBrainConfig(n_modules=8, hidden_dim=64, message_dim=32)
    env_config = EnvConfig(n_arms=8, max_steps=steps)
    env = ReachAndAvoidEnv(env_config)
    brain = OctopusBrain(config)
    brain.eval()

    visualizer = EnvironmentVisualizer(env)
    obs_np, _ = env.reset(seed=42)
    brain.reset(batch_size=1)
    obs = torch.tensor(obs_np, dtype=torch.float32).unsqueeze(0)

    cumulative_reward = 0.0

    if mode == "ascii":
        print("Starting ASCII Visualizer Rollout...")
        time.sleep(1)
        for t in range(steps):
            with torch.no_grad():
                out = brain.step(obs, deterministic=False)

            actions = out["actions"][0].cpu().numpy()
            report_rate = out["report_rate"]
            coalition_clusters = out.get("coalition_clusters", [])

            rendered = visualizer.render_ascii(
                step=t,
                reward=cumulative_reward,
                report_rate=report_rate,
                coalition_clusters=coalition_clusters,
                clear_screen=True,
            )
            print(rendered)
            time.sleep(1.0 / max(fps, 1))

            next_obs_np, rewards, term, trunc, _ = env.step(actions)
            cumulative_reward += float(np.sum(rewards))
            obs = torch.tensor(next_obs_np, dtype=torch.float32).unsqueeze(0)

            if term or trunc:
                break
        print(f"\nRollout finished. Final Reward: {cumulative_reward:.2f}")

    elif mode == "gif":
        if save_path is None:
            save_path = "octopus_brain_trajectory.gif"

        print(f"Generating Matplotlib Animation (saving to {save_path})...")
        fig, ax = plt.subplots(figsize=(7, 7), facecolor="#0f172a")

        frames_data = []
        for t in range(steps):
            with torch.no_grad():
                out = brain.step(obs, deterministic=False)

            actions = out["actions"][0].cpu().numpy()
            report_rate = out["report_rate"]
            c_mat = (
                out["coalition_matrix"][0].cpu().numpy()
                if out["coalition_matrix"].numel() > 0
                else np.zeros((8, 8))
            )
            edges = out.get("active_coalitions", [])

            # Store snapshot
            snapshot = {
                "step": t,
                "reward": cumulative_reward,
                "report_rate": report_rate,
                "c_mat": c_mat,
                "edges": edges,
                "arm_tips": env.arm_tips.copy(),
                "single_targets": [st.copy() for st in env.single_targets],
                "joint_targets": [
                    {"pos": jt["pos"].copy(), "active": jt["active"]} for jt in env.joint_targets
                ],
                "hazards": [h.copy() for h in env.hazards],
            }
            frames_data.append(snapshot)

            next_obs_np, rewards, term, trunc, _ = env.step(actions)
            cumulative_reward += float(np.sum(rewards))
            obs = torch.tensor(next_obs_np, dtype=torch.float32).unsqueeze(0)
            if term or trunc:
                break

        def update(frame_idx):
            data = frames_data[frame_idx]
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

        anim = FuncAnimation(fig, update, frames=len(frames_data), interval=1000 // fps)
        writer = PillowWriter(fps=fps)
        anim.save(save_path, writer=writer)
        plt.close(fig)
        print(f"Successfully saved animation to: {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OctopusBrain Visual Trajectory Animator")
    parser.add_argument(
        "--mode",
        type=str,
        default="ascii",
        choices=["ascii", "gif"],
        help="Rendering mode: ascii or gif",
    )
    parser.add_argument("--steps", type=int, default=25, help="Number of simulation steps")
    parser.add_argument("--fps", type=int, default=4, help="Frames per second")
    parser.add_argument(
        "--save", type=str, default="octopus_trajectory.gif", help="Path to save GIF animation"
    )
    args = parser.parse_args()

    run_visual_rollout(mode=args.mode, steps=args.steps, save_path=args.save, fps=args.fps)
