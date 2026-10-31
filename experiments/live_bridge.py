"""Live Cognitive Telemetry Bridge Server for OctopusBrain.

Runs a zero-dependency HTTP/REST server on port 8765 providing real-time cognitive
telemetry from the trained OctopusBrain to the 3D Web Visualizer.

Endpoints:
    GET  /status   - Returns server health, active device, and loaded checkpoint.
    GET  /step     - Executes one real cognitive cycle and returns full 5-stage telemetry.
    POST /reset    - Resets environment and brain recurrent memory.
    POST /scenario - Switches problem scenario ('standard', 'hunting', 'amputation').

Usage:
    python experiments/live_bridge.py --port 8765 --checkpoint checkpoints/top1_octopus_brain.pt
"""

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

import httpx
import numpy as np
import torch

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from envs.hunting_env import CooperativeHuntingEnv
from envs.reach_and_avoid import ReachAndAvoidEnv
from envs.soft_body_tentacle import SoftBodyTentacleEnv
from octopus_brain.biophysics import BiophysicalConnectomeSimulator
from octopus_brain.brain import OctopusBrain
from octopus_brain.config import EnvConfig, OctopusBrainConfig
from octopus_brain.connectome import CephalopodConnectome
from octopus_brain.lexicon import InterBrachialLexiconDecoder


class CognitiveBridgeSession:
    """Manages live environment and model state for real-time visualization."""

    def __init__(
        self, checkpoint_path: str = "checkpoints/top1_octopus_brain.pt", device_name: str = "cpu"
    ):
        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )
        print(f"--> Cognitive Bridge using compute device: {self.device}")

        self.config = OctopusBrainConfig(
            n_modules=8, obs_dim=16, action_dim=5, hidden_dim=64, message_dim=32, central_dim=64
        )
        self.model = OctopusBrain(self.config).to(self.device)
        self.lexicon = InterBrachialLexiconDecoder(message_dim=32).to(self.device)

        self.checkpoint_path = checkpoint_path
        if os.path.exists(checkpoint_path):
            try:
                ckpt = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
            except TypeError:
                ckpt = torch.load(checkpoint_path, map_location=self.device)
            if "model_state_dict" in ckpt:
                self.model.load_state_dict(ckpt["model_state_dict"])
            else:
                self.model.load_state_dict(ckpt)
            print(f"--> Loaded trained weights from: {checkpoint_path}")
        else:
            print(f"--> Warning: Checkpoint {checkpoint_path} not found. Running initial weights.")

        self.model.eval()

        self.scenario_name = "standard"
        self.amputated_arms = []
        self.current_step = 0
        self.cumulative_reward = 0.0

        self.env = ReachAndAvoidEnv(EnvConfig(n_arms=8, max_steps=40))
        self.connectome = CephalopodConnectome(scale_factor=1.0)
        self.biophysics_sim = BiophysicalConnectomeSimulator(self.connectome, dt_ms=0.5)
        self.reset()

    def reset(self):
        """Reset environment and model state."""
        self.current_step = 0
        self.cumulative_reward = 0.0
        obs_np, _ = self.env.reset(seed=int(np.random.randint(1, 10000)))
        self.current_obs = obs_np
        self.model.reset(batch_size=1, device=self.device)
        self.biophysics_sim.reset(randomize_v=False)
        return self.current_obs

    def set_scenario(self, name: str):
        """Switch problem scenario."""
        self.scenario_name = name.lower()
        if self.scenario_name == "hunting":
            self.env = CooperativeHuntingEnv(EnvConfig(n_arms=8, max_steps=40))
            self.amputated_arms = []
        elif self.scenario_name == "amputation":
            self.env = ReachAndAvoidEnv(EnvConfig(n_arms=8, max_steps=40))
            self.amputated_arms = [3]  # Arm 3 severed
        elif self.scenario_name in ("soft_body_3d", "continuum_3d"):
            self.env = SoftBodyTentacleEnv(EnvConfig(n_arms=8, max_steps=40))
            self.amputated_arms = []
        else:
            self.env = ReachAndAvoidEnv(EnvConfig(n_arms=8, max_steps=40))
            self.amputated_arms = []
        return self.reset()

    def step(self):
        """Execute one cognitive cycle and return full 5-stage telemetric breakdown."""
        obs_t = torch.tensor(self.current_obs, dtype=torch.float32, device=self.device).unsqueeze(0)

        # Build active mask
        active_mask = torch.ones(1, 8, dtype=torch.bool, device=self.device)
        for arm_idx in self.amputated_arms:
            active_mask[0, arm_idx] = False

        with torch.no_grad():
            out = self.model.step(obs_t, active_mask=active_mask, deterministic=True)

        actions_np = out["actions"][0].detach().cpu().numpy()
        report_flags = out["report_events"][0].detach().cpu().numpy().astype(bool)
        report_probs = out["report_probs"][0].detach().cpu().numpy()
        surprises = out["surprise_values"][0].detach().cpu().numpy()
        logits = out["action_logits"][0].detach().cpu().numpy()
        values = out["values"][0].detach().cpu().numpy().squeeze(-1)

        c_mat = (
            out["coalition_matrix"][0].detach().cpu().numpy()
            if out["coalition_matrix"].numel() > 0
            else np.zeros((8, 8))
        )
        coalitions = out.get("coalition_clusters", [])

        # Decode semantic communication chatter using Inter-Brachial Lexicon
        nbr_msgs = (
            self.model.prev_neighbor_msgs[0]
            if self.model.prev_neighbor_msgs is not None
            else torch.zeros(8, 32, device=self.device)
        )
        decoded_intents = self.lexicon.decode_all_arms(nbr_msgs, report_flags=report_flags)

        # Step environment
        next_obs, rewards, term, trunc, info = self.env.step(actions_np)
        step_reward = float(np.sum(rewards))
        self.cumulative_reward += step_reward
        self.current_step += 1

        is_done = term or trunc
        self.current_obs = next_obs

        # Package 5-stage cognitive telemetry packet
        telemetry = {
            "step": self.current_step,
            "max_steps": self.env.max_steps,
            "scenario": self.scenario_name,
            "step_reward": step_reward,
            "cumulative_reward": self.cumulative_reward,
            "is_done": is_done,
            # Stage 1: Sensory Perception
            "observations": self.current_obs.tolist(),
            # Stage 2: Local Surprise & Prediction
            "surprise_values": surprises.tolist(),
            # Stage 3: Event-Triggered Gating
            "report_flags": report_flags.tolist(),
            "report_probs": report_probs.tolist(),
            "report_rate": float(np.mean(report_flags)),
            # Stage 4: Central Coalitions & Attention
            "coalition_clusters": [[int(x) for x in c] for c in coalitions],
            "attention_matrix": c_mat.tolist(),
            "is_consolidation_step": bool(out.get("is_consolidation_step", False)),
            "decoded_intents": decoded_intents,
            "action_logits": logits.tolist(),
            "actions": [int(a) for a in actions_np],
            "values": values.tolist(),
            "amputated_arms": self.amputated_arms,
            "single_completed": info.get("single_completed", 0),
            "joint_completed": info.get("joint_completed", 0),
            "hazard_hits": info.get("hazard_hits", 0),
            # Biophysical Connectome Telemetry (Google/FlyWire Pipeline)
            "biophysical_rates_hz": self._step_biophysics(),
            "total_action_potentials": len(self.biophysics_sim.spike_history),
        }

        if is_done:
            self.reset()

        return telemetry

    def _step_biophysics(self) -> dict:
        """Advance biophysical Leaky Integrate-and-Fire connectome with current cues."""
        i_ext = np.zeros(len(self.connectome.nodes), dtype=np.float32)
        for arm_idx in range(8):
            obs_arm = self.current_obs[arm_idx]
            chemo_cue = float(np.linalg.norm(obs_arm[0:4]))
            for nid in self.connectome.arm_sensory_ids.get(arm_idx, [])[:2]:
                i_ext[nid] = chemo_cue * 20.0
        for _ in range(10):
            self.biophysics_sim.step(i_ext)
        return self.biophysics_sim.get_population_firing_rates(time_window_ms=25.0)


# Global session instance
SESSION: CognitiveBridgeSession | None = None


class CognitiveBridgeHandler(BaseHTTPRequestHandler):
    """CORS-enabled HTTP Request Handler for real-time visualizer streaming."""

    def _set_cors_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/status":
            self._set_cors_headers(200)
            status_data = {
                "status": "online",
                "device": str(SESSION.device),
                "checkpoint": SESSION.checkpoint_path,
                "scenario": SESSION.scenario_name,
                "n_arms": 8,
                "step": SESSION.current_step,
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
        elif parsed.path == "/step":
            telemetry = SESSION.step()
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(telemetry).encode("utf-8"))
        elif parsed.path == "/reset":
            SESSION.reset()
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"status": "reset_ok"}).encode("utf-8"))
        elif parsed.path == "/connectome":
            self._set_cors_headers(200)
            summary = SESSION.connectome.get_summary()
            self.wfile.write(json.dumps(summary).encode("utf-8"))
        elif parsed.path == "/llm/pool":
            self._set_cors_headers(200)
            from octoflow.config import load_secure_config

            cfg_file = Path.home() / ".octoflow" / "config.json"
            entries = []
            if cfg_file.exists():
                data = load_secure_config(cfg_file)
                entries = data.get("llm_pool", [])
            # Mask API keys for security in UI responses
            safe_entries = []
            for item in entries:
                copy_item = dict(item)
                raw_k = copy_item.get("api_key") or ""
                if raw_k and len(raw_k) > 6:
                    copy_item["masked_key"] = raw_k[:3] + "..." + raw_k[-4:]
                elif raw_k:
                    copy_item["masked_key"] = "***"
                else:
                    copy_item["masked_key"] = "(none / local)"
                # do not expose full key
                copy_item["has_key"] = bool(raw_k)
                copy_item.pop("api_key", None)
                safe_entries.append(copy_item)
            self.wfile.write(json.dumps({"pool": safe_entries}).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            body = json.loads(post_body)
        except Exception:
            body = {}

        if parsed.path == "/reset":
            SESSION.reset()
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"status": "reset_ok"}).encode("utf-8"))
        elif parsed.path == "/scenario":
            scenario = body.get("scenario", "standard")
            SESSION.set_scenario(scenario)
            self._set_cors_headers(200)
            self.wfile.write(
                json.dumps({"status": "scenario_set", "scenario": scenario}).encode("utf-8")
            )
        elif parsed.path == "/llm/pool":
            from octoflow.config import load_secure_config

            cfg_dir = Path.home() / ".octoflow"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            cfg_file = cfg_dir / "config.json"
            cfg_data = load_secure_config(cfg_file) if cfg_file.exists() else {}

            current_pool = cfg_data.get("llm_pool", [])
            action = body.get("action", "add")

            if action == "add":
                new_entry = body.get("entry", {})
                if new_entry.get("id"):
                    # Check if already exists, update or append
                    updated = False
                    for idx, ex in enumerate(current_pool):
                        if ex.get("id") == new_entry["id"]:
                            current_pool[idx] = new_entry
                            updated = True
                            break
                    if not updated:
                        current_pool.append(new_entry)

            elif action == "remove":
                target_id = body.get("id")
                current_pool = [e for e in current_pool if e.get("id") != target_id]

            elif action == "set_priority":
                order_ids = body.get("order", [])
                reordered = []
                for p_idx, t_id in enumerate(order_ids):
                    for e in current_pool:
                        if e.get("id") == t_id:
                            e["priority"] = p_idx + 1
                            reordered.append(e)
                current_pool = reordered

            elif action == "save_all":
                current_pool = body.get("entries", [])

            cfg_data["llm_pool"] = current_pool
            cfg_file.write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")

            self._set_cors_headers(200)
            self.wfile.write(
                json.dumps({"status": "ok", "pool_size": len(current_pool)}).encode("utf-8")
            )

        elif parsed.path == "/llm/test":
            provider = body.get("provider", "gemini")
            api_key = body.get("api_key", "")
            base_url = body.get("base_url", "")
            model = body.get("model", "")

            # Lightweight health check
            try:
                import time

                t0 = time.time()
                # Test connectivity
                if provider in ["ollama", "custom", "vllm"] and base_url:
                    resp = httpx.get(f"{base_url.rstrip('/')}/models", timeout=3.0)
                    ok = resp.status_code in [200, 401, 403]
                else:
                    ok = bool(api_key or provider == "ollama")
                latency_ms = int((time.time() - t0) * 1000)
                self._set_cors_headers(200)
                self.wfile.write(json.dumps({"ok": ok, "latency_ms": latency_ms}).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(200)
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Quiet logger to avoid terminal spam during 60FPS polling
        return


def run_bridge(port: int = 8765, checkpoint: str = "checkpoints/top1_octopus_brain.pt"):
    global SESSION
    SESSION = CognitiveBridgeSession(checkpoint_path=checkpoint)
    server_address = ("127.0.0.1", port)
    HTTPServer.allow_reuse_address = True
    httpd = HTTPServer(server_address, CognitiveBridgeHandler)
    print("=" * 80)
    print(f"OCTOPUSBRAIN LIVE COGNITIVE TELEMETRY BRIDGE ACTIVE on http://127.0.0.1:{port}")
    print(f"Endpoints: http://127.0.0.1:{port}/step  |  http://127.0.0.1:{port}/status")
    print("=" * 80)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n--> Shutting down bridge.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Cognitive Telemetry Bridge")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--checkpoint", type=str, default="checkpoints/top1_octopus_brain.pt")
    args = parser.parse_args()
    run_bridge(port=args.port, checkpoint=args.checkpoint)
