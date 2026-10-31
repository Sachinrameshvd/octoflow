#!/usr/bin/env python3
"""OctoFlow Performance Baseline & Regression Measurement Script.

Measures:
1. CLI Help Startup Time (median of runs)
2. Module Import Times (`import octoflow`, `import octoflow.cli`)
3. Cockpit Idle CPU % and RSS Memory (sampled over PTY)
4. Frame Render Time (p50 and p95 over multiple frames)
5. WebGL Visualizer Distribution Size (raw and gzipped)
6. Environment & Package Installation Size

Outputs results to benchmarks/perf/baseline.json.
Supports --quick for fast smoke testing and CI execution.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import platform
import pty
import select
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psutil


def get_machine_info() -> dict[str, Any]:
    """Gather hardware and environment metadata for reproducible benchmarks."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def measure_help_startup(python_bin: str, runs: int = 10) -> dict[str, Any]:
    """Measure wall-clock execution time of `octoflow.cli --help`."""
    durations: list[float] = []
    for _ in range(runs):
        t0 = time.perf_counter()
        res = subprocess.run(
            [python_bin, "-m", "octoflow.cli", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        t1 = time.perf_counter()
        if res.returncode != 0:
            raise RuntimeError(f"CLI help failed with code {res.returncode}: {res.stderr}")
        durations.append(t1 - t0)

    return {
        "runs_count": runs,
        "median_seconds": round(statistics.median(durations), 4),
        "mean_seconds": round(statistics.mean(durations), 4),
        "min_seconds": round(min(durations), 4),
        "max_seconds": round(max(durations), 4),
        "stdev_seconds": round(statistics.stdev(durations), 4) if len(durations) > 1 else 0.0,
        "raw_samples": [round(d, 4) for d in durations],
    }


def measure_import_time(python_bin: str, module_name: str, runs: int = 5) -> dict[str, Any]:
    """Measure isolated process import time for a specific module."""
    durations: list[float] = []
    for _ in range(runs):
        code = f"import {module_name}"
        t0 = time.perf_counter()
        res = subprocess.run(
            [python_bin, "-c", code],
            capture_output=True,
            text=True,
            check=False,
        )
        t1 = time.perf_counter()
        if res.returncode != 0:
            raise RuntimeError(f"Import {module_name} failed: {res.stderr}")
        durations.append(t1 - t0)

    return {
        "module": module_name,
        "runs_count": runs,
        "median_seconds": round(statistics.median(durations), 4),
        "mean_seconds": round(statistics.mean(durations), 4),
        "min_seconds": round(min(durations), 4),
        "max_seconds": round(max(durations), 4),
    }


def measure_cockpit_idle(python_bin: str, duration_sec: float = 60.0) -> dict[str, Any]:
    """Spawn the interactive cockpit inside a PTY and sample idle CPU and RSS memory."""
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        [python_bin, "-m", "octoflow.cli"],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    process = psutil.Process(proc.pid)

    # Allow cockpit to complete initialization and render initial frame
    time.sleep(1.0)

    cpu_samples: list[float] = []
    rss_samples: list[float] = []
    sample_interval = 0.5
    end_time = time.time() + duration_sec

    try:
        # Drain stdout in non-blocking fashion so PTY buffer does not block
        while time.time() < end_time:
            if proc.poll() is not None:
                break
            r, _, _ = select.select([master], [], [], 0.05)
            if r:
                try:
                    os.read(master, 16384)
                except OSError:
                    pass

            try:
                cpu = process.cpu_percent(interval=sample_interval)
                mem = process.memory_info().rss / (1024 * 1024)
                cpu_samples.append(cpu)
                rss_samples.append(mem)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        os.close(master)
        os.close(slave)

    if not cpu_samples:
        cpu_samples = [0.0]
    if not rss_samples:
        rss_samples = [0.0]

    return {
        "sampling_duration_seconds": duration_sec,
        "samples_count": len(cpu_samples),
        "cpu_percent_median": round(statistics.median(cpu_samples), 2),
        "cpu_percent_p95": round(sorted(cpu_samples)[int(len(cpu_samples) * 0.95)], 2),
        "cpu_percent_max": round(max(cpu_samples), 2),
        "rss_mb_median": round(statistics.median(rss_samples), 2),
        "rss_mb_max": round(max(rss_samples), 2),
    }


def measure_frame_render_time(repo_root: Path, frame_count: int = 600) -> dict[str, Any]:
    """Measure the time taken to compose interactive cockpit frames."""
    from octoflow.cockpit.render import build_cockpit_grid
    from octoflow.cockpit.session import CockpitSession

    session = CockpitSession(workspace=repo_root)
    durations_ms: list[float] = []

    # Warmup
    for w in range(5):
        build_cockpit_grid(session, buffer="", cursor_pos=0, tick=w, octo_x=float(w), octo_y=0)

    for i in range(frame_count):
        t0 = time.perf_counter()
        build_cockpit_grid(
            session,
            buffer=f"goal step {i % 10}",
            cursor_pos=min(i % 10, 5),
            tick=i,
            octo_x=float(i % 50),
            octo_y=1 if (i % 6) < 3 else 0,
            pasted_line_count=1,
        )
        t1 = time.perf_counter()
        durations_ms.append((t1 - t0) * 1000.0)

    sorted_ms = sorted(durations_ms)
    p50 = statistics.median(durations_ms)
    p95 = sorted_ms[int(len(sorted_ms) * 0.95)]

    return {
        "frames_measured": frame_count,
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "mean_ms": round(statistics.mean(durations_ms), 3),
        "min_ms": round(min(durations_ms), 3),
        "max_ms": round(max(durations_ms), 3),
    }


def measure_visualizer_dist(dist_dir: Path) -> dict[str, Any]:
    """Calculate raw and gzipped sizes of visualizer distribution artifacts."""
    if not dist_dir.exists():
        return {"error": f"Dist directory not found at {dist_dir}"}

    total_raw = 0
    total_gzip = 0
    chunks: list[dict[str, Any]] = []

    for file_path in sorted(dist_dir.rglob("*")):
        if file_path.is_file():
            data = file_path.read_bytes()
            raw_len = len(data)
            gz_len = len(gzip.compress(data))
            total_raw += raw_len
            total_gzip += gz_len
            rel_name = str(file_path.relative_to(dist_dir))
            chunks.append(
                {
                    "file": rel_name,
                    "raw_bytes": raw_len,
                    "raw_kb": round(raw_len / 1024, 2),
                    "gzip_bytes": gz_len,
                    "gzip_kb": round(gz_len / 1024, 2),
                }
            )

    chunks.sort(key=lambda x: x["raw_bytes"], reverse=True)

    return {
        "dist_path": str(dist_dir),
        "total_raw_bytes": total_raw,
        "total_raw_mb": round(total_raw / (1024 * 1024), 2),
        "total_gzip_bytes": total_gzip,
        "total_gzip_mb": round(total_gzip / (1024 * 1024), 2),
        "top_chunks": chunks[:10],
    }


def measure_install_size(repo_root: Path) -> dict[str, Any]:
    """Measure virtual environment and repository package size on disk."""
    venv_dir = repo_root / ".venv"
    venv_bytes = 0
    if venv_dir.exists():
        for f in venv_dir.rglob("*"):
            if f.is_file() and not f.is_symlink():
                try:
                    venv_bytes += f.stat().st_size
                except OSError:
                    pass

    octoflow_dir = repo_root / "octoflow"
    octo_bytes = 0
    if octoflow_dir.exists():
        for f in octoflow_dir.rglob("*"):
            if f.is_file():
                try:
                    octo_bytes += f.stat().st_size
                except OSError:
                    pass

    return {
        "venv_size_mb": round(venv_bytes / (1024 * 1024), 2),
        "octoflow_package_size_mb": round(octo_bytes / (1024 * 1024), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect OctoFlow Performance Baseline")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run lightweight smoke baseline (3 help runs, 5s idle, 30 frames)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks/perf/baseline.json"),
        help="Path to write baseline.json output",
    )
    parser.add_argument(
        "--check-thresholds",
        type=Path,
        default=None,
        help="Optional path to thresholds JSON to check against",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    python_bin = sys.executable

    print("================================================================")
    print("◈ OctoFlow Performance Baseline Suite (P4.3)")
    print(f"◈ Mode: {'QUICK (Smoke / CI)' if args.quick else 'FULL (Comprehensive)'}")
    print(f"◈ Python: {python_bin}")
    print("================================================================\n")

    help_runs = 3 if args.quick else 10
    idle_duration = 5.0 if args.quick else 60.0
    frame_count = 30 if args.quick else 600

    print("1/6 Collecting machine specifications...")
    machine_info = get_machine_info()

    print(f"2/6 Measuring CLI --help startup ({help_runs} runs)...")
    help_startup = measure_help_startup(python_bin, runs=help_runs)
    print(f"    ✔ Median Help Startup: {help_startup['median_seconds']}s")

    print("3/6 Measuring module import times...")
    import_octoflow = measure_import_time(python_bin, "octoflow", runs=3 if args.quick else 5)
    import_cli = measure_import_time(python_bin, "octoflow.cli", runs=3 if args.quick else 5)
    print(f"    ✔ Import 'octoflow': {import_octoflow['median_seconds']}s")
    print(f"    ✔ Import 'octoflow.cli': {import_cli['median_seconds']}s")

    print(f"4/6 Measuring cockpit idle CPU & RSS ({idle_duration}s)...")
    cockpit_idle = measure_cockpit_idle(python_bin, duration_sec=idle_duration)
    print(
        f"    ✔ Idle CPU: {cockpit_idle['cpu_percent_median']}% (p95: {cockpit_idle['cpu_percent_p95']}%)"
    )
    print(f"    ✔ Idle RSS: {cockpit_idle['rss_mb_median']} MB")

    print(f"5/6 Measuring cockpit frame render time ({frame_count} frames)...")
    frame_render = measure_frame_render_time(repo_root, frame_count=frame_count)
    print(f"    ✔ Render p50: {frame_render['p50_ms']}ms | p95: {frame_render['p95_ms']}ms")

    print("6/6 Measuring visualizer distribution & install sizes...")
    visualizer_dir = repo_root / "visualizer" / "dist"
    if not visualizer_dir.exists():
        visualizer_dir = repo_root / "octoflow" / "dist"
    vis_dist = measure_visualizer_dist(visualizer_dir)
    install_size = measure_install_size(repo_root)
    print(
        f"    ✔ Visualizer Dist: {vis_dist.get('total_raw_mb', 0.0)} MB (gzip: {vis_dist.get('total_gzip_mb', 0.0)} MB)"
    )
    print(f"    ✔ Venv Size: {install_size['venv_size_mb']} MB")

    baseline_data = {
        "version": "1.0",
        "phase": "P4.3",
        "mode": "quick" if args.quick else "full",
        "machine": machine_info,
        "metrics": {
            "help_startup": help_startup,
            "import_times": {
                "octoflow": import_octoflow,
                "octoflow_cli": import_cli,
            },
            "cockpit_idle": cockpit_idle,
            "frame_render": frame_render,
            "visualizer_dist": vis_dist,
            "install_size": install_size,
        },
    }

    # Write output JSON
    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(baseline_data, f, indent=2)

    print(f"\n✔ Baseline recorded successfully to: {output_path}")

    # Check soft thresholds if requested
    if args.check_thresholds and args.check_thresholds.exists():
        thresholds = json.loads(args.check_thresholds.read_text(encoding="utf-8"))
        print("\nChecking against soft performance thresholds:")
        failed = False
        max_help = thresholds.get("max_help_startup_seconds", 1.0)
        max_p95_render = thresholds.get("max_frame_render_p95_ms", 25.0)
        max_idle_cpu = thresholds.get("max_cockpit_idle_cpu_percent", 15.0)

        if help_startup["median_seconds"] > max_help:
            print(f"  ✖ Help startup {help_startup['median_seconds']}s > threshold {max_help}s")
            failed = True
        else:
            print(f"  ✔ Help startup {help_startup['median_seconds']}s <= threshold {max_help}s")

        if frame_render["p95_ms"] > max_p95_render:
            print(f"  ✖ Frame render p95 {frame_render['p95_ms']}ms > threshold {max_p95_render}ms")
            failed = True
        else:
            print(
                f"  ✔ Frame render p95 {frame_render['p95_ms']}ms <= threshold {max_p95_render}ms"
            )

        if cockpit_idle["cpu_percent_median"] > max_idle_cpu:
            print(f"  ✖ Idle CPU {cockpit_idle['cpu_percent_median']}% > threshold {max_idle_cpu}%")
            failed = True
        else:
            print(
                f"  ✔ Idle CPU {cockpit_idle['cpu_percent_median']}% <= threshold {max_idle_cpu}%"
            )

        if failed:
            print("\n⚠ Soft threshold check encountered warnings.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
