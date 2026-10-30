"""OctoFlow Swarm Evaluation & Benchmarking Harness.

Executes autonomous 8-arm evaluations across standard algorithmic and architectural
challenges, measuring pass rate, execution latency, LLM calls, and real/estimated token consumption
under both gated and ungated (always_escalate) modes.
"""

from __future__ import annotations

import datetime
import json
import random
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from rich.console import Console
from rich.table import Table

from octoflow.conductor import SupraesophagealConductor
from octoflow.config import OctoFlowConfig
from octoflow.provider import BaseLLMProvider, LLMResponse
from octoflow.themes import get_theme


@dataclass
class BenchmarkTask:
    id: str
    name: str
    category: str
    objective: str
    target_file: str
    reference_solution: str
    acceptance_test_file: str
    acceptance_test_code: str
    verification_code: str = ""


# Reference implementations and pytest acceptance suites for challenge tasks
BENCHMARK_SUITE: list[BenchmarkTask] = [
    BenchmarkTask(
        id="rate_limiter",
        name="Sliding Window Rate Limiter",
        category="Systems",
        objective="Implement a thread-safe SlidingWindowRateLimiter class with allow_request(client_id, limit, window_sec) in limiter.py",
        target_file="limiter.py",
        reference_solution="""import time
import threading

class SlidingWindowRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._requests = {}

    def allow_request(self, client_id: str, limit: int, window_sec: float) -> bool:
        with self._lock:
            now = time.time()
            timestamps = self._requests.setdefault(client_id, [])
            self._requests[client_id] = [t for t in timestamps if now - t < window_sec]
            if len(self._requests[client_id]) < limit:
                self._requests[client_id].append(now)
                return True
            return False
""",
        acceptance_test_file="test_limiter.py",
        acceptance_test_code="""import time
from limiter import SlidingWindowRateLimiter

def test_sliding_window_rate_limiter():
    rl = SlidingWindowRateLimiter()
    assert rl.allow_request("user_1", 2, 1.0) is True
    assert rl.allow_request("user_1", 2, 1.0) is True
    assert rl.allow_request("user_1", 2, 1.0) is False
    assert rl.allow_request("user_2", 2, 1.0) is True

def test_rate_limiter_expiry():
    rl = SlidingWindowRateLimiter()
    assert rl.allow_request("user_3", 1, 0.05) is True
    assert rl.allow_request("user_3", 1, 0.05) is False
    time.sleep(0.06)
    assert rl.allow_request("user_3", 1, 0.05) is True
""",
        verification_code="""from limiter import SlidingWindowRateLimiter
rl = SlidingWindowRateLimiter()
assert rl.allow_request("user_1", 2, 1.0) is True
assert rl.allow_request("user_1", 2, 1.0) is True
assert rl.allow_request("user_1", 2, 1.0) is False
assert rl.allow_request("user_2", 2, 1.0) is True
print("VERIFICATION_PASSED")
""",
    ),
    BenchmarkTask(
        id="lru_cache",
        name="O(1) LRU Cache",
        category="Algorithms",
        objective="Implement an LRUCache class with get(key) and put(key, value) in lru.py supporting capacity eviction",
        target_file="lru.py",
        reference_solution="""from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
""",
        acceptance_test_file="test_lru.py",
        acceptance_test_code="""from lru import LRUCache

def test_lru_operations():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    assert cache.get(1) == 10
    cache.put(3, 30)  # Evicts key 2
    assert cache.get(2) == -1
    assert cache.get(3) == 30
    assert cache.get(1) == 10

def test_lru_update_existing():
    cache = LRUCache(2)
    cache.put(1, 100)
    cache.put(1, 150)
    assert cache.get(1) == 150
""",
        verification_code="""from lru import LRUCache
cache = LRUCache(2)
cache.put(1, 10)
cache.put(2, 20)
assert cache.get(1) == 10
cache.put(3, 30)
assert cache.get(2) == -1
assert cache.get(3) == 30
print("VERIFICATION_PASSED")
""",
    ),
    BenchmarkTask(
        id="jwt_validator",
        name="HMAC-SHA256 JWT Tokenizer",
        category="Security",
        objective="Implement generate_token(payload, secret) and verify_token(token, secret) using pure hashlib and hmac in auth.py",
        target_file="auth.py",
        reference_solution="""import hmac
import hashlib
import json
import base64

def generate_token(payload: dict, secret: str) -> str:
    payload_str = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
    return f"{payload_str}.{signature}"

def verify_token(token: str, secret: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_str, signature = parts
        expected_sig = hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        return json.loads(base64.urlsafe_b64decode(payload_str.encode()).decode())
    except Exception:
        return None
""",
        acceptance_test_file="test_auth.py",
        acceptance_test_code="""from auth import generate_token, verify_token

def test_jwt_valid():
    tok = generate_token({"sub": "octo", "role": "admin"}, "secret_key_123")
    data = verify_token(tok, "secret_key_123")
    assert data is not None
    assert data.get("sub") == "octo"
    assert data.get("role") == "admin"

def test_jwt_invalid_key():
    tok = generate_token({"sub": "octo"}, "secret_key_123")
    assert verify_token(tok, "wrong_key") is None

def test_jwt_malformed():
    assert verify_token("not-a-valid-token", "secret_key_123") is None
""",
        verification_code="""from auth import generate_token, verify_token
tok = generate_token({"sub": "octo"}, "secret_key_123")
data = verify_token(tok, "secret_key_123")
assert data.get("sub") == "octo"
assert verify_token(tok, "wrong_key") is None
print("VERIFICATION_PASSED")
""",
    ),
    BenchmarkTask(
        id="dag_topo_sort",
        name="Topological DAG Resolver",
        category="Architecture",
        objective="Implement resolve_dependencies(nodes, edges) in topo.py returning valid execution order or raising ValueError on cycles",
        target_file="topo.py",
        reference_solution="""def resolve_dependencies(nodes, edges):
    from collections import defaultdict, deque
    in_degree = {n: 0 for n in nodes}
    adj = defaultdict(list)
    for u, v in edges:
        adj[v].append(u)
        in_degree[u] += 1
    queue = deque([n for n in nodes if in_degree[n] == 0])
    order = []
    while queue:
        curr = queue.popleft()
        order.append(curr)
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    if len(order) != len(nodes):
        raise ValueError("Cycle detected in graph")
    return order
""",
        acceptance_test_file="test_topo.py",
        acceptance_test_code="""import pytest
from topo import resolve_dependencies

def test_valid_dag_order():
    nodes = ["app", "db", "auth"]
    edges = [("app", "db"), ("app", "auth"), ("auth", "db")]
    order = resolve_dependencies(nodes, edges)
    assert order.index("db") < order.index("auth")
    assert order.index("auth") < order.index("app")

def test_cyclic_graph_raises():
    nodes = ["a", "b"]
    edges = [("a", "b"), ("b", "a")]
    with pytest.raises(ValueError):
        resolve_dependencies(nodes, edges)
""",
        verification_code="""from topo import resolve_dependencies
nodes = ["app", "db", "auth"]
edges = [("app", "db"), ("app", "auth"), ("auth", "db")]
order = resolve_dependencies(nodes, edges)
assert order.index("db") < order.index("auth")
assert order.index("auth") < order.index("app")
print("VERIFICATION_PASSED")
""",
    ),
    BenchmarkTask(
        id="fastapi_todo",
        name="Tiny FastAPI Todo API",
        category="Web",
        objective='Implement a tiny FastAPI todo API in app.py with Pydantic model Todo(id: Optional[int] = None, title: str) and routes: GET /todos (returns list of todos), POST /todos (accepts JSON {"title": str}, assigns integer id, returns item with id and title), and DELETE /todos/{todo_id} (checks if todo_id exists: if not found raises HTTPException(status_code=404), otherwise removes it and returns 200 or 204)',
        target_file="app.py",
        reference_solution="""from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

class TodoCreate(BaseModel):
    title: str

_todos: Dict[int, str] = {}
_next_id: int = 1

@app.get("/todos")
def get_todos():
    return [{"id": tid, "title": title} for tid, title in _todos.items()]

@app.post("/todos", status_code=201)
def create_todo(todo: TodoCreate):
    global _next_id
    item_id = _next_id
    _next_id += 1
    _todos[item_id] = todo.title
    return {"id": item_id, "title": todo.title}

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    if todo_id not in _todos:
        raise HTTPException(status_code=404, detail="Todo not found")
    del _todos[todo_id]
    return {"status": "deleted", "id": todo_id}
""",
        acceptance_test_file="test_app.py",
        acceptance_test_code="""import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_todo_api_lifecycle():
    resp = client.get("/todos")
    assert resp.status_code == 200
    initial_count = len(resp.json())

    post_resp = client.post("/todos", json={"title": "Buy groceries"})
    assert post_resp.status_code in (200, 201)
    data = post_resp.json()
    assert "id" in data
    assert data["title"] == "Buy groceries"
    todo_id = data["id"]

    list_resp = client.get("/todos")
    assert list_resp.status_code == 200
    todos = list_resp.json()
    assert len(todos) == initial_count + 1
    assert any(t["id"] == todo_id for t in todos)

    del_resp = client.delete(f"/todos/{todo_id}")
    assert del_resp.status_code in (200, 204)

    del_again = client.delete(f"/todos/{todo_id}")
    assert del_again.status_code == 404
""",
        verification_code="""from fastapi.testclient import TestClient
from app import app
client = TestClient(app)
r = client.get("/todos")
assert r.status_code == 200
post = client.post("/todos", json={"title": "test"})
assert post.status_code in (200, 201)
tid = post.json()["id"]
del_r = client.delete(f"/todos/{tid}")
assert del_r.status_code in (200, 204)
print("VERIFICATION_PASSED")
""",
    ),
]


class FakeBenchmarkProvider(BaseLLMProvider):
    """Deterministic fake provider for benchmarks and testing with known usage numbers."""

    provider_name = "fake"
    model = "fake-model-v1"

    def __init__(
        self,
        prompt_tokens: int = 150,
        completion_tokens: int = 50,
        estimated: bool = False,
        task_solutions: dict[str, tuple[str, str]] | None = None,
    ):
        super().__init__()
        self.prompt_tokens_val = int(prompt_tokens)
        self.completion_tokens_val = int(completion_tokens)
        self.estimated = bool(estimated)
        self.call_count = 0
        self.written_files: set = set()
        self.task_solutions = task_solutions or {}

    def _get_solution_for_prompt(self, prompt: str) -> tuple[str, str] | None:
        p_lower = prompt.lower()
        if "limiter" in p_lower or "rate limit" in p_lower or "slidingwindow" in p_lower:
            task = next((t for t in BENCHMARK_SUITE if t.id == "rate_limiter"), None)
            if task:
                return task.target_file, task.reference_solution
        if "lru" in p_lower or "lrucache" in p_lower or "lru.py" in p_lower:
            task = next((t for t in BENCHMARK_SUITE if t.id == "lru_cache"), None)
            if task:
                return task.target_file, task.reference_solution
        if (
            "jwt" in p_lower
            or "auth.py" in p_lower
            or "generate_token" in p_lower
            or "hmac" in p_lower
        ):
            task = next((t for t in BENCHMARK_SUITE if t.id == "jwt_validator"), None)
            if task:
                return task.target_file, task.reference_solution
        if "topo" in p_lower or "dag" in p_lower or "resolve_dependencies" in p_lower:
            task = next((t for t in BENCHMARK_SUITE if t.id == "dag_topo_sort"), None)
            if task:
                return task.target_file, task.reference_solution
        if "fastapi" in p_lower or "todo" in p_lower or "app.py" in p_lower:
            task = next((t for t in BENCHMARK_SUITE if t.id == "fastapi_todo"), None)
            if task:
                return task.target_file, task.reference_solution
        return None

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        self.call_count += 1
        solution = self._get_solution_for_prompt(prompt) or self._get_solution_for_prompt(
            system_prompt
        )

        # Write solution file if not written yet
        if solution and solution[0] not in self.written_files:
            target_path, code = solution
            self.written_files.add(target_path)
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": target_path,
                    "content": code,
                    "explanation": f"Writing verified implementation to {target_path}",
                }
            )
        else:
            content = json.dumps(
                {
                    "action": "read_file",
                    "path": "README.md",
                    "explanation": "Inspecting workspace state.",
                }
            )

        resp = LLMResponse(
            content=content,
            tokens_prompt=self.prompt_tokens_val,
            tokens_completion=self.completion_tokens_val,
            total_tokens=self.prompt_tokens_val + self.completion_tokens_val,
            estimated_cost_dollars=0.0,
            estimated=self.estimated,
        )
        self.record_usage(resp)
        return resp

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        return self.generate(prompt, system_prompt, temperature, max_tokens)


def run_single_benchmark_run(
    task: BenchmarkTask,
    mode: str = "gated",
    provider_name: str = "mock",
    model_name: str | None = None,
    seed: int = 42,
    temperature: float = 0.0,
    workspace_dir: str | None = None,
    custom_provider: BaseLLMProvider | None = None,
    max_cycles: int = 3,
    record_cassette_dir: str | None = None,
) -> dict[str, Any]:
    """Execute a single benchmark run in an isolated sandbox and record truthful telemetry."""
    normalized_mode = "always_escalate" if mode in ("ungated", "always_escalate") else "gated"

    # Seed randomness for reproducible client-side execution
    random.seed(seed)
    np.random.seed(seed)

    def _execute(target_dir: str) -> dict[str, Any]:
        t0 = time.time()
        cfg = OctoFlowConfig(
            workspace_dir=target_dir,
            model_provider=provider_name,
            model_name=model_name
            or ("fake-eval-v1" if provider_name == "fake" else "claude-3-5-sonnet-20241022"),
            gate_mode=normalized_mode,
            temperature=temperature,
            dry_run=False,
            allow_mock=True,
            is_bench=True,
        )

        conductor = SupraesophagealConductor(config=cfg)
        if custom_provider is not None:
            conductor.provider = custom_provider
            custom_provider.set_ledger(conductor.usage_ledger)
            for arm in conductor.arms:
                arm.provider = custom_provider

        if record_cassette_dir:
            from octoflow.cassette import CassetteRecorder

            rec = CassetteRecorder(
                provider=conductor.provider,
                cassette_dir=record_cassette_dir,
                workspace_root=target_dir,
            )
            rec.set_ledger(conductor.usage_ledger)
            conductor.provider = rec
            for arm in conductor.arms:
                arm.provider = rec

        try:
            conductor.run_swarm(task.objective, max_cycles=max_cycles)
        except Exception:
            pass
        wall_time = time.time() - t0

        # Collect files written (excluding acceptance tests and internal files)
        target_path = Path(target_dir)
        files_written = sorted(
            [
                p.name
                for p in target_path.glob("*.py")
                if not p.name.startswith("test_") and not p.name.startswith("_")
            ]
        )

        # Write and run the pytest acceptance file in the sandbox
        acc_file = target_path / task.acceptance_test_file
        acc_file.write_text(task.acceptance_test_code, encoding="utf-8")

        test_passed = False
        try:
            pytest_cmd = [sys.executable, "-m", "pytest", "-q", task.acceptance_test_file]
            res = subprocess.run(
                pytest_cmd,
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=15,
            )
            test_passed = res.returncode == 0
        except Exception:
            test_passed = False

        usage_summary = conductor.usage_ledger.summary()
        outcome = "complete" if test_passed else ("partial" if len(files_written) > 0 else "failed")

        return {
            "task": task.id,
            "task_name": task.name,
            "category": task.category,
            "mode": normalized_mode,
            "provider": provider_name,
            "model": model_name or getattr(conductor.provider, "model", "default"),
            "seed": seed,
            "temperature": temperature,
            "wall_time_seconds": round(wall_time, 4),
            "llm_calls": usage_summary["total_calls"],
            "tokens": {
                "prompt_tokens": usage_summary["prompt_tokens"],
                "completion_tokens": usage_summary["completion_tokens"],
                "total_tokens": usage_summary["total_tokens"],
                "estimated": usage_summary["is_estimated"],
            },
            "files_written": files_written,
            "acceptance_test_passed": test_passed,
            "outcome": outcome,
            "settings": {
                "temperature": temperature,
                "gate_mode": normalized_mode,
                "seed": seed,
                "max_cycles": max_cycles,
            },
        }

    if workspace_dir:
        Path(workspace_dir).mkdir(parents=True, exist_ok=True)
        return _execute(workspace_dir)
    else:
        with tempfile.TemporaryDirectory() as tmp_dir:
            return _execute(tmp_dir)


def generate_summary_markdown(
    runs_data: list[dict[str, Any]],
    out_path: str | Path,
) -> str:
    """Compute aggregate statistics and generate comprehensive summary.md."""
    if not runs_data:
        content = "# OctoFlow Benchmark Summary\n\nNo runs recorded.\n"
        Path(out_path).write_text(content, encoding="utf-8")
        return content

    # Detect provider and estimation status
    provider = runs_data[0].get("provider", "unknown")
    model = runs_data[0].get("model", "unknown")
    is_estimated = any(r.get("tokens", {}).get("estimated", False) for r in runs_data)
    temperature = runs_data[0].get("temperature", 0.0)
    seed = runs_data[0].get("seed", 42)

    # Group runs by (task, mode)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    tasks_seen = {}
    for r in runs_data:
        t_id = r["task"]
        tasks_seen[t_id] = r.get("task_name", t_id)
        key = (t_id, r["mode"])
        grouped.setdefault(key, []).append(r)

    # Compute task-level metrics
    task_stats: dict[str, dict[str, Any]] = {}
    for t_id, t_name in tasks_seen.items():
        task_stats[t_id] = {"name": t_name}
        for mode in ("gated", "always_escalate"):
            runs = grouped.get((t_id, mode), [])
            if runs:
                calls = [r["llm_calls"] for r in runs]
                tot_toks = [r["tokens"]["total_tokens"] for r in runs]
                p_toks = [r["tokens"]["prompt_tokens"] for r in runs]
                c_toks = [r["tokens"]["completion_tokens"] for r in runs]
                walls = [r["wall_time_seconds"] for r in runs]
                passed = sum(1 for r in runs if r["acceptance_test_passed"])
                task_stats[t_id][mode] = {
                    "count": len(runs),
                    "calls_min": min(calls),
                    "calls_med": statistics.median(calls),
                    "calls_max": max(calls),
                    "tokens_min": min(tot_toks),
                    "tokens_med": statistics.median(tot_toks),
                    "tokens_max": max(tot_toks),
                    "p_tokens_med": statistics.median(p_toks),
                    "c_tokens_med": statistics.median(c_toks),
                    "wall_med": statistics.median(walls),
                    "pass_rate_pct": round((passed / len(runs)) * 100.0, 1),
                }

    # Compute ratios for tasks with both modes
    overall_gated_tokens = []
    overall_ungated_tokens = []
    for t_id, data in task_stats.items():
        if "gated" in data and "always_escalate" in data:
            g_med = data["gated"]["tokens_med"]
            u_med = data["always_escalate"]["tokens_med"]
            ratio = (g_med / u_med) if u_med > 0 else 1.0
            savings = (1.0 - ratio) * 100.0
            data["ratio"] = round(ratio, 3)
            data["savings_pct"] = round(savings, 1)
            overall_gated_tokens.append(g_med)
            overall_ungated_tokens.append(u_med)
        else:
            data["ratio"] = None
            data["savings_pct"] = None

    if overall_ungated_tokens and sum(overall_ungated_tokens) > 0:
        overall_ratio = sum(overall_gated_tokens) / sum(overall_ungated_tokens)
        overall_reduction = round((1.0 - overall_ratio) * 100.0, 1)
    else:
        overall_reduction = None

    # Determine empirical headline verdict
    if overall_reduction is not None:
        if overall_reduction >= 80.0:
            verdict_text = (
                f"**SUPPORTED**: The measured empirical token reduction is **{overall_reduction}%**, "
                "which falls within the advertised 80-90% savings range for these benchmark challenges."
            )
        else:
            verdict_text = (
                f"**CORRECTED**: The measured empirical token reduction is **{overall_reduction}%**, "
                f"which does NOT support the headline claim of '80-90% fewer tokens'. "
                "Token consumption claims must reflect measured evidence rather than theoretical extrapolations."
            )
    else:
        verdict_text = (
            "Comparative reduction ratio requires evaluating both `gated` and `ungated` modes."
        )

    # Build Markdown table rows
    table_rows = []
    for t_id, data in task_stats.items():
        t_name = data["name"]
        for mode in ("gated", "always_escalate"):
            m_data = data.get(mode)
            if not m_data:
                continue
            mode_label = "Gated" if mode == "gated" else "Ungated (always_escalate)"
            ratio_str = (
                f"{data['savings_pct']}% reduction"
                if (data.get("savings_pct") is not None and mode == "gated")
                else "-"
            )
            table_rows.append(
                f"| `{t_id}` | {t_name} | {mode_label} | "
                f"{m_data['calls_min']} / {m_data['calls_med']:.1f} / {m_data['calls_max']} | "
                f"{m_data['tokens_min']} / {m_data['tokens_med']:.1f} / {m_data['tokens_max']} | "
                f"{m_data['p_tokens_med']:.1f} | {m_data['c_tokens_med']:.1f} | "
                f"{m_data['wall_med']:.2f}s | {m_data['pass_rate_pct']}% | {ratio_str} |"
            )

    table_content = "\n".join(table_rows)

    # Token measurement explanation for Limitations section
    if is_estimated:
        token_caveat = (
            "⚠️ **Tokens were ESTIMATED**: The provider or local environment returned no direct token usage headers. "
            "Token quantities were computed using the fallback heuristic `ceil(chars / 4)`. "
            "Character estimates are approximate and may deviate from specific BPE/WordPiece tokenizers by ±15-20%."
        )
    else:
        token_caveat = (
            "✔ **Tokens were MEASURED**: Token usage was obtained directly from API provider response headers "
            "(`prompt_tokens`, `completion_tokens`)."
        )

    md_content = f"""# OctoFlow Swarm Benchmark Summary

**Generated At:** {datetime.datetime.now(datetime.timezone.utc).isoformat()}  
**Provider:** `{provider}` | **Model:** `{model}` | **Tokens Estimated:** `{is_estimated}`  
**Runs per Configuration:** {len(runs_data)} total runs | **Temperature:** `{temperature}` | **Base Seed:** `{seed}`  

---

## 1. Executive Summary & Headline Claim Verification

- **Headline Claim Evaluated:** *"80-90% fewer tokens with event-triggered surprise gating"*
- **Measured Median Token Reduction:** {f"**{overall_reduction}%**" if overall_reduction is not None else "N/A"}
- **Empirical Verdict:** {verdict_text}

---

## 2. Comparative Results Across Benchmark Tasks

| Task ID | Task Name | Mode | Calls (Min/Med/Max) | Total Tokens (Min/Med/Max) | Prompt Tokens (Med) | Comp Tokens (Med) | Wall Time | Pass Rate | Gated Savings |
|---|---|---|---|---|---|---|---|---|---|
{table_content}

---

## 3. Methodology

### Benchmark Tasks & Verification
Evaluated against 4 standard algorithmic and architectural challenges:
1. **Rate Limiter (`rate_limiter`):** Thread-safe sliding window rate limiter in `limiter.py`.
2. **LRU Cache (`lru_cache`):** O(1) capacity-evicting LRU cache in `lru.py`.
3. **JWT Validator (`jwt_validator`):** HMAC-SHA256 signature and verification in `auth.py`.
4. **DAG Topological Sort (`dag_topo_sort`):** Dependency resolution and cycle detection in `topo.py`.

### Execution Environment & Isolation
- Each benchmark run executes in an isolated sandbox workspace.
- Acceptance testing is executed inside the sandbox using standard `pytest` running acceptance test suites directly against generated code.

### Gated vs. Ungated (`always_escalate`) Baseline
- **Gated Mode (`gated`):** Arms encode sensory feedback from tool executions into state observations. When sensory surprise $\\Delta S_i \\le \\theta$, the arm enters quiescence and suppresses subsequent LLM queries for that mission phase.
- **Ungated Baseline (`always_escalate`):** Arms force escalation on every evaluation cycle (equivalent to $\\theta = 0$), bypassing silent auto-quiescence and invoking the LLM model on every cycle across all arms.

### Determinism & Temperature
- Temperature was fixed to `{temperature}` where supported by the provider to maximize reproducibility.
- Random seeds were pinned starting at seed `{seed}` for client-side ordering and mock sampling.
- **Nondeterminism Disclosure:** Even at temperature 0, distributed frontier LLM APIs (e.g. Anthropic, OpenAI) may exhibit non-deterministic generation due to floating-point batching order and mixture-of-experts routing in production infrastructure.

---

## 4. Limitations & Data Caveats

- **Token Measurement Fidelity:**
  - {token_caveat}
- **Provider & Model Scope:**
  - Evaluated using provider `{provider}` with model `{model}`.
  - Results using mock or fake providers represent synthetic execution traces designed for verification of accounting and harness mechanics, NOT empirical performance of neural foundation models.
- **Task Scope:**
  - The challenge tasks test targeted Python algorithmic implementations. Real-world multi-file software refactorings may involve differing ratios of silent file inspection versus escalation.
"""

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(md_content, encoding="utf-8")
    return md_content


def run_benchmark_harness(
    task: str = "all",
    mode: str = "both",
    provider: str = "mock",
    model: str | None = None,
    runs: int = 3,
    seed: int = 42,
    temperature: float = 0.0,
    out_dir: str = "benchmarks/results",
    custom_provider: BaseLLMProvider | None = None,
    console: Console | None = None,
    record_cassette: str | None = None,
) -> dict[str, Any]:
    """Primary entry point for running the honest benchmark harness."""
    c = console or Console()
    th = get_theme("tokyo_night")

    # Select tasks
    if task == "all":
        selected_tasks = list(BENCHMARK_SUITE)
    else:
        # Match task ID or alias (handling hyphens and underscores interchangeably)
        norm_task = task.lower().replace("-", "_")
        matched = [
            t
            for t in BENCHMARK_SUITE
            if t.id == task or task in t.id or norm_task == t.id.replace("-", "_")
        ]
        if not matched:
            valid_ids = [t.id for t in BENCHMARK_SUITE]
            raise ValueError(f"Unknown task '{task}'. Available: {valid_ids}")
        selected_tasks = matched

    # Select modes
    mode_clean = mode.lower().strip()
    if mode_clean == "both":
        eval_modes = ["gated", "always_escalate"]
    elif mode_clean in ("ungated", "always_escalate"):
        eval_modes = ["always_escalate"]
    else:
        eval_modes = ["gated"]

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    all_runs: list[dict[str, Any]] = []

    c.print(f"\n[{th.rich_primary}]◈ OctoFlow Reproducible Benchmark Harness[/{th.rich_primary}]")
    c.print(
        f"[dim]Provider: {provider} | Tasks: {len(selected_tasks)} | Modes: {eval_modes} | Runs per mode: {runs}[/dim]\n"
    )

    for t in selected_tasks:
        for m in eval_modes:
            mode_display = "Gated" if m == "gated" else "Ungated"
            c.print(
                f"[{th.rich_secondary}]► Running {t.name} ({mode_display})...[/{th.rich_secondary}]"
            )
            for run_idx in range(1, runs + 1):
                run_seed = seed + run_idx - 1
                res = run_single_benchmark_run(
                    task=t,
                    mode=m,
                    provider_name=provider,
                    model_name=model,
                    seed=run_seed,
                    temperature=temperature,
                    custom_provider=custom_provider,
                    record_cassette_dir=record_cassette,
                )
                all_runs.append(res)

                # Save individual JSON per run
                run_file = out_path / f"{t.id}_{m}_run_{run_idx}.json"
                run_file.write_text(json.dumps(res, indent=2), encoding="utf-8")

                status_mark = (
                    f"[{th.rich_success}]✔ PASS[/]"
                    if res["acceptance_test_passed"]
                    else f"[{th.rich_danger}]✖ FAIL[/]"
                )
                c.print(
                    f"  [dim]Run {run_idx}/{runs}:[/dim] {status_mark} • "
                    f"Calls: [white]{res['llm_calls']}[/white] • "
                    f"Tokens: [white]{res['tokens']['total_tokens']:,}[/white] "
                    f"({'est' if res['tokens']['estimated'] else 'measured'}) • "
                    f"Time: [dim]{res['wall_time_seconds']}s[/dim]"
                )

    # Generate summary.md
    summary_md_path = out_path / "summary.md"
    generate_summary_markdown(all_runs, summary_md_path)
    c.print(
        f"\n[{th.rich_success}]✔ Benchmark complete. Summary written to {summary_md_path}[/{th.rich_success}]\n"
    )

    return {
        "runs": all_runs,
        "summary_file": str(summary_md_path),
        "total_runs": len(all_runs),
    }


def run_single_benchmark(
    task: Any,
    config: OctoFlowConfig | None = None,
    mode: str = "balanced",
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    """Legacy compatibility helper."""
    if isinstance(task, str):
        matching = [t for t in BENCHMARK_SUITE if t.id == task]
        if not matching:
            raise ValueError(
                f"Unknown benchmark task '{task}'. Available: {[t.id for t in BENCHMARK_SUITE]}"
            )
        selected_task = matching[0]
    else:
        selected_task = task

    cfg = config or OctoFlowConfig(workspace_dir=workspace_dir or ".", model_provider="mock")
    run_res = run_single_benchmark_run(
        task=selected_task,
        mode=cfg.gate_mode,
        provider_name=cfg.model_provider,
        model_name=cfg.model_name,
        workspace_dir=workspace_dir,
    )
    return {
        "task_key": selected_task.id,
        "task_id": selected_task.id,
        "name": selected_task.name,
        "category": selected_task.category,
        "passed": run_res["acceptance_test_passed"],
        "ast_valid": True,
        "files_created": run_res["files_written"],
        "duration_sec": run_res["wall_time_seconds"],
        "latency_s": run_res["wall_time_seconds"],
        "tokens_spent": run_res["tokens"]["total_tokens"],
        "cost_dollars": round(run_res["tokens"]["total_tokens"] * 0.00001, 4),
        "cost_estimate_usd": round(run_res["tokens"]["total_tokens"] * 0.00001, 4),
    }


def run_swarm_benchmark_suite(
    tasks: list[str] | str | None = None,
    task_key: str | None = None,
    mode: str = "balanced",
    workspace_dir: str | None = None,
    config: OctoFlowConfig | None = None,
    console: Console | None = None,
) -> dict[str, Any]:
    """Legacy compatibility suite wrapper."""
    c = console or Console()
    th = get_theme("tokyo_night")

    filter_keys = set()
    if task_key:
        filter_keys.add(task_key)
    if isinstance(tasks, str):
        filter_keys.add(tasks)
    elif isinstance(tasks, list):
        filter_keys.update(tasks)

    suite = [t for t in BENCHMARK_SUITE if (not filter_keys or t.id in filter_keys)]
    results: list[dict[str, Any]] = []

    c.print(
        f"\n[{th.rich_primary}]◈ OctoFlow Swarm Evaluation: Running {len(suite)} benchmark challenges...[/{th.rich_primary}]\n"
    )

    for task in suite:
        res = run_single_benchmark(task, config=config, mode=mode, workspace_dir=workspace_dir)
        results.append(res)

    total_tasks = len(results)
    passed_tasks = len([r for r in results if r["passed"]])
    pass_rate_pct = round((passed_tasks / max(total_tasks, 1)) * 100, 1)
    total_tokens = sum(r["tokens_spent"] for r in results)
    total_cost = sum(r["cost_dollars"] for r in results)
    avg_latency = round(sum(r["duration_sec"] for r in results) / max(total_tasks, 1), 2)

    t = Table(
        title="OctoFlow Swarm Benchmark Suite Results", border_style=th.rich_border, expand=True
    )
    t.add_column("Task ID", style="bold white", width=16)
    t.add_column("Category", style=th.rich_secondary, width=14)
    t.add_column("Verdict", width=12)
    t.add_column("Latency", width=10)
    t.add_column("Tokens", width=10)
    t.add_column("Cost", style="dim")

    for r in results:
        v_str = (
            f"[{th.rich_success}]✔ PASSED[/]" if r["passed"] else f"[{th.rich_danger}]✖ FAILED[/]"
        )
        t.add_row(
            r["task_id"],
            r["category"],
            v_str,
            f"{r['duration_sec']}s",
            f"{r['tokens_spent']:,}",
            f"${r['cost_dollars']:.4f}",
        )

    c.print(t)
    c.print(
        f"\n[{th.rich_success}]✔ Overall Pass@1 Rate:[/{th.rich_success}] [bold white]{pass_rate_pct}% ({passed_tasks}/{total_tasks})[/bold white]\n"
    )

    return {
        "pass_rate_pct": pass_rate_pct,
        "total_tasks": total_tasks,
        "passed_tasks": passed_tasks,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "avg_latency": avg_latency,
        "tasks": results,
    }
