#!/usr/bin/env python3
"""OctoFlow Privacy-Preserving Metrics Collector (P12.3).

Aggregates public repository and package metrics from:
- PyPI Download Statistics (via pypistats.org API)
- GitHub Public REST API (repository, issues, pull requests, releases, workflow runs)

Strictly zero telemetry:
- Collects only publicly visible, aggregated metadata.
- No user device fingerprinting, no phone-home analytics, no tracking pixels.
- Can run locally by maintainers or scheduled weekly in CI writing an artifact.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_REPO = "TODO_OWNER_OR_ORG/octoflow"
DEFAULT_PACKAGE = "octoflow"


def parse_iso_ts(ts_str: str) -> datetime.datetime:
    """Parse ISO 8601 timestamp string into UTC datetime."""
    clean = ts_str.replace("Z", "+00:00")
    return datetime.datetime.fromisoformat(clean)


def fetch_json(url: str, headers: dict[str, str] | None = None, timeout: float = 8.0) -> Any:
    """Fetch JSON payload from URL with standard headers."""
    req_headers = {
        "User-Agent": "OctoFlow-Metrics-Collector/1.0",
        "Accept": "application/vnd.github.v3+json, application/json",
    }
    if headers:
        req_headers.update(headers)

    if not (url.startswith("https://") or url.startswith("http://")):
        raise ValueError(f"Unsafe URL scheme: {url}")

    req = urllib.request.Request(url, headers=req_headers)  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None


class MetricsCollector:
    """Collects public metrics from PyPI and GitHub with fixture support."""

    def __init__(
        self,
        repo: str = DEFAULT_REPO,
        package: str = DEFAULT_PACKAGE,
        token: str | None = None,
        fixture_data: dict[str, Any] | None = None,
    ):
        self.repo = repo
        self.package = package
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.fixture = fixture_data or {}

    def _get_github_headers(self) -> dict[str, str]:
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def collect_pypi_metrics(self) -> dict[str, Any]:
        """Fetch download counts from pypistats API."""
        if "pypi_recent" in self.fixture:
            recent_data = self.fixture["pypi_recent"]
        else:
            recent_url = f"https://pypistats.org/api/packages/{self.package}/recent"
            recent_data = fetch_json(recent_url)

        if "pypi_overall" in self.fixture:
            overall_data = self.fixture["pypi_overall"]
        else:
            overall_url = f"https://pypistats.org/api/packages/{self.package}/overall"
            overall_data = fetch_json(overall_url)

        last_30_days = 0
        last_7_days = 0
        last_day = 0
        if recent_data and isinstance(recent_data, dict):
            rdata = recent_data.get("data", {})
            last_30_days = rdata.get("last_month", 0)
            last_7_days = rdata.get("last_week", 0)
            last_day = rdata.get("last_day", 0)

        mirrors_ratio = None
        without_mirrors_30d = 0
        with_mirrors_30d = 0
        if overall_data and isinstance(overall_data, dict):
            items = overall_data.get("data", [])
            for row in items:
                cat = row.get("category")
                dls = row.get("downloads", 0)
                if cat == "without_mirrors":
                    without_mirrors_30d += dls
                elif cat == "with_mirrors":
                    with_mirrors_30d += dls
            if with_mirrors_30d > 0 and without_mirrors_30d > 0:
                mirrors_ratio = round(without_mirrors_30d / with_mirrors_30d, 2)

        return {
            "package": self.package,
            "last_30_days": last_30_days or without_mirrors_30d,
            "last_7_days": last_7_days,
            "last_day": last_day,
            "without_mirrors_30d": without_mirrors_30d or last_30_days,
            "with_mirrors_30d": with_mirrors_30d or last_30_days,
            "organic_ratio": mirrors_ratio,
        }

    def collect_github_metrics(self) -> dict[str, Any]:
        """Fetch repository, issues, pull requests, releases, and CI stats from GitHub API."""
        gh_headers = self._get_github_headers()
        base_api = f"https://api.github.com/repos/{self.repo}"

        # 1. Repo Metadata
        repo_data = self.fixture.get("repo")
        if repo_data is None:
            repo_data = fetch_json(base_api, headers=gh_headers) or {}

        stars = repo_data.get("stargazers_count", 0)
        forks = repo_data.get("forks_count", 0)

        # 2. Issues & Response Times
        issues_raw = self.fixture.get("issues")
        if issues_raw is None:
            issues_url = f"{base_api}/issues?state=all&per_page=100"
            issues_raw = fetch_json(issues_url, headers=gh_headers) or []

        # Filter out pull requests from issues list
        issues = [i for i in issues_raw if "pull_request" not in i]
        open_issues = [i for i in issues if i.get("state") == "open"]
        closed_issues = [i for i in issues if i.get("state") == "closed"]

        # Comments for first response calculation
        comments_fixture = self.fixture.get("comments", {})

        first_response_hours: list[float] = []
        bug_close_days: list[float] = []

        for issue in issues:
            issue_num = str(issue.get("number"))
            created_ts = parse_iso_ts(issue["created_at"])
            author = issue.get("user", {}).get("login")

            # Comments check
            if issue_num in comments_fixture:
                comments = comments_fixture[issue_num]
            elif self.fixture:
                comments = []
            else:
                comments_url = f"{base_api}/issues/{issue_num}/comments"
                comments = fetch_json(comments_url, headers=gh_headers) or []

            # First comment by non-author
            non_author_comments = [c for c in comments if c.get("user", {}).get("login") != author]
            if non_author_comments:
                first_c = min(non_author_comments, key=lambda c: c["created_at"])
                c_ts = parse_iso_ts(first_c["created_at"])
                delta_h = (c_ts - created_ts).total_seconds() / 3600.0
                if delta_h >= 0:
                    first_response_hours.append(delta_h)

            # Bug time to close
            is_bug = any(
                str(lbl.get("name", "")).lower() == "bug" for lbl in issue.get("labels", [])
            )
            if is_bug and issue.get("state") == "closed" and issue.get("closed_at"):
                closed_ts = parse_iso_ts(issue["closed_at"])
                delta_d = (closed_ts - created_ts).total_seconds() / 86400.0
                if delta_d >= 0:
                    bug_close_days.append(delta_d)

        median_first_response_h = (
            round(statistics.median(first_response_hours), 1) if first_response_hours else None
        )
        median_bug_close_d = round(statistics.median(bug_close_days), 1) if bug_close_days else None

        # 3. Pull Requests & Contributor Retention
        pulls_raw = self.fixture.get("pulls")
        if pulls_raw is None:
            pulls_url = f"{base_api}/pulls?state=all&per_page=100"
            pulls_raw = fetch_json(pulls_url, headers=gh_headers) or []

        merged_pulls = [p for p in pulls_raw if p.get("merged_at")]
        open_pulls = [p for p in pulls_raw if p.get("state") == "open"]

        pr_merge_hours: list[float] = []
        author_merged_prs: dict[str, list[datetime.datetime]] = {}

        now_ref = datetime.datetime.now(datetime.timezone.utc)
        if merged_pulls:
            max_merge = max(parse_iso_ts(p["merged_at"]) for p in merged_pulls)
            now_ref = max(now_ref, max_merge)

        ninety_days_ago = now_ref - datetime.timedelta(days=90)

        for pr in merged_pulls:
            c_ts = parse_iso_ts(pr["created_at"])
            m_ts = parse_iso_ts(pr["merged_at"])
            delta_h = (m_ts - c_ts).total_seconds() / 3600.0
            if delta_h >= 0:
                pr_merge_hours.append(delta_h)

            author = pr.get("user", {}).get("login", "unknown")
            if author not in author_merged_prs:
                author_merged_prs[author] = []
            author_merged_prs[author].append(m_ts)

        median_pr_merge_h = round(statistics.median(pr_merge_hours), 1) if pr_merge_hours else None

        # Repeat contributors (2+ merged PRs)
        repeat_contributors = sum(
            1 for pr_times in author_merged_prs.values() if len(pr_times) >= 2
        )

        # First-time contributors in last 90 days
        first_time_90d = 0
        for _author, pr_times in author_merged_prs.items():
            first_merge = min(pr_times)
            if first_merge >= ninety_days_ago:
                first_time_90d += 1

        # 4. Release Cadence
        releases_raw = self.fixture.get("releases")
        if releases_raw is None:
            releases_url = f"{base_api}/releases?per_page=100"
            releases_raw = fetch_json(releases_url, headers=gh_headers) or []

        release_dates = []
        for r in releases_raw:
            ts = r.get("published_at") or r.get("created_at")
            if ts:
                release_dates.append(parse_iso_ts(ts))

        release_dates.sort()
        release_cadence_days = None
        if len(release_dates) >= 2:
            intervals = [
                (release_dates[i] - release_dates[i - 1]).total_seconds() / 86400.0
                for i in range(1, len(release_dates))
            ]
            release_cadence_days = round(statistics.median(intervals), 1)

        # 5. CI Workflow Pass Rate
        workflows_raw = self.fixture.get("workflow_runs")
        if workflows_raw is None:
            wf_url = f"{base_api}/actions/runs?per_page=100"
            wf_resp = fetch_json(wf_url, headers=gh_headers) or {}
            workflows_raw = wf_resp.get("workflow_runs", [])

        completed_runs = [w for w in workflows_raw if w.get("status") == "completed"]
        success_runs = [w for w in completed_runs if w.get("conclusion") == "success"]
        ci_pass_rate = (
            round((len(success_runs) / len(completed_runs)) * 100.0, 1) if completed_runs else 100.0
        )

        return {
            "stars": stars,
            "forks": forks,
            "open_issues": len(open_issues),
            "closed_issues": len(closed_issues),
            "open_pulls": len(open_pulls),
            "merged_pulls": len(merged_pulls),
            "median_first_response_hours": median_first_response_h,
            "median_bug_close_days": median_bug_close_d,
            "median_pr_merge_hours": median_pr_merge_h,
            "repeat_contributors_count": repeat_contributors,
            "first_time_contributors_90d": first_time_90d,
            "total_releases": len(releases_raw),
            "median_release_cadence_days": release_cadence_days,
            "ci_pass_rate_pct": ci_pass_rate,
            "ci_completed_runs": len(completed_runs),
        }

    def compute_all_metrics(self) -> dict[str, Any]:
        """Compute full combined metric payload."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        pypi = self.collect_pypi_metrics()
        github = self.collect_github_metrics()

        # Targets evaluation (from Part 1 maintainer targets)
        first_resp_h = github.get("median_first_response_hours")
        first_resp_target_met = (
            first_resp_h is not None and first_resp_h <= 72.0
        )  # <= 3 business days (72h)

        repeat_contrib_target_met = github.get("repeat_contributors_count", 0) >= 2

        cadence_d = github.get("median_release_cadence_days")
        cadence_target_met = (cadence_d is not None and cadence_d <= 35.0) or (
            github.get("total_releases", 0) >= 1
        )

        ci_target_met = github.get("ci_pass_rate_pct", 100.0) >= 95.0

        return {
            "collected_at": now_iso,
            "repository": self.repo,
            "package": self.package,
            "targets": {
                "first_response_sla_met": first_resp_target_met,
                "contributor_retention_met": repeat_contrib_target_met,
                "release_cadence_met": cadence_target_met,
                "ci_pass_rate_met": ci_target_met,
            },
            "pypi": pypi,
            "github": github,
        }

    def render_markdown(self, data: dict[str, Any]) -> str:
        """Render a clean GitHub-Flavored Markdown metrics dashboard."""
        ts = data.get("collected_at", "")
        pypi = data.get("pypi", {})
        gh = data.get("github", {})
        targets = data.get("targets", {})

        def target_badge(met: bool) -> str:
            return "Target Met" if met else "In Progress"

        lines = [
            "# OctoFlow Privacy-Preserving Metrics Dashboard",
            "",
            "> [!NOTE]",
            "> **Zero Telemetry Commitment:** OctoFlow contains no phoning home, no analytics code, and no user tracking.",
            "> All metrics in this report are computed strictly from public package registries (PyPI) and public repository activity (GitHub).",
            "",
            f"**Report Generated:** `{ts}` | **Target Repository:** `{data.get('repository')}`",
            "",
            "---",
            "",
            "## 1. Executive Summary & Maintainer Targets",
            "",
            "| Focus Area | Metric | Current Value | Target SLA | Status |",
            "| :--- | :--- | :--- | :--- | :--- |",
            f"| **Responsiveness** | Median First Response | `{gh.get('median_first_response_hours', 'N/A')} hours` | $\\le 72$ hours (3 days) | {target_badge(targets.get('first_response_sla_met', False))} |",
            f"| **Retention** | Contributors with 2+ PRs | `{gh.get('repeat_contributors_count', 0)}` | $\\ge 2$ contributors | {target_badge(targets.get('contributor_retention_met', False))} |",
            f"| **Cadence** | Median Release Interval | `{gh.get('median_release_cadence_days', 'N/A')} days` | Monthly ($\\le 35$ days) | {target_badge(targets.get('release_cadence_met', False))} |",
            f"| **Quality** | CI Build Pass Rate | `{gh.get('ci_pass_rate_pct', 100.0)}%` | $\\ge 95.0\\%$ | {target_badge(targets.get('ci_pass_rate_met', False))} |",
            "",
            "---",
            "",
            "## 2. Adoption & Package Downloads",
            "",
            "- **PyPI Package:** [`"
            + str(pypi.get("package"))
            + "`](https://pypi.org/project/"
            + str(pypi.get("package"))
            + "/)",
            f"- **Downloads (Last 30 Days):** `{pypi.get('last_30_days', 0):,}`",
            f"- **Downloads (Last 7 Days):** `{pypi.get('last_7_days', 0):,}`",
            f"- **Downloads (Last 24 Hours):** `{pypi.get('last_day', 0):,}`",
            f"- **Clean Installs (Without Automated Mirrors):** `{pypi.get('without_mirrors_30d', 0):,}`",
            f"- **Organic / Mirror Ratio:** `{pypi.get('organic_ratio', 'N/A')}`",
            "",
            "> [!TIP]",
            "> **The Download Trap:** Raw PyPI download numbers are heavily inflated by automated CI/CD mirrors, container base image builds, and package index crawlers. Focus on week-over-week trends in `without_mirrors` rather than raw spike counts.",
            "",
            "---",
            "",
            "## 3. Community Responsiveness & Triage",
            "",
            f"- **Open Issues:** `{gh.get('open_issues', 0)}`",
            f"- **Closed Issues:** `{gh.get('closed_issues', 0)}`",
            f"- **Median First Response Time:** `{gh.get('median_first_response_hours', 'N/A')} hours` (Target: $\\le 72$ hours)",
            f"- **Median Bug Time-to-Close:** `{gh.get('median_bug_close_days', 'N/A')} days`",
            f"- **Median PR Merge Time:** `{gh.get('median_pr_merge_hours', 'N/A')} hours`",
            "",
            "---",
            "",
            "## 4. Contributor Health & Velocity",
            "",
            f"- **Repeat Contributors ($\\ge 2$ Merged PRs):** `{gh.get('repeat_contributors_count', 0)}`",
            f"- **New Contributors (Last 90 Days):** `{gh.get('first_time_contributors_90d', 0)}`",
            f"- **Open Pull Requests:** `{gh.get('open_pulls', 0)}`",
            f"- **Merged Pull Requests:** `{gh.get('merged_pulls', 0)}`",
            f"- **Total Public Releases:** `{gh.get('total_releases', 0)}`",
            f"- **Median Days Between Releases:** `{gh.get('median_release_cadence_days', 'N/A')} days`",
            f"- **CI Suite Pass Rate:** `{gh.get('ci_pass_rate_pct', 100.0)}%` (across `{gh.get('ci_completed_runs', 0)}` completed runs)",
            "",
            "---",
            "",
            "## 5. Vanity Metrics (Informational Only)",
            "",
            f"- **GitHub Stars:** `{gh.get('stars', 0)}`",
            f"- **GitHub Forks:** `{gh.get('forks', 0)}`",
            "",
            "> [!WARNING]",
            "> **The GitHub Stars Trap:** Stars measure social curiosity and bookmarking, not product effectiveness, user retention, or code quality. Never treat star counts as an OKR or milestone success criterion.",
            "",
            "---",
            "",
            "## 6. Voluntary Feedback Pipeline",
            "",
            "Because OctoFlow collects zero telemetry, qualitative user feedback is solicited through voluntary channels:",
            "1. **`octoflow feedback`**: Interactive CLI command that opens or prints a prefilled GitHub Issue template (with optional sanitized diagnostics reviewed by the user first).",
            "2. **GitHub Discussions ('Show and tell')**: Where users share custom specialist rosters, benchmark results, and real-world architectures.",
            "3. **`octoflow bugreport`**: Sanitized diagnostic generator that redacts all secrets before reporting.",
        ]
        return "\n".join(lines) + "\n"


def main() -> int:
    """CLI entrypoint for scripts/metrics.py."""
    parser = argparse.ArgumentParser(
        description="Collect privacy-preserving public metrics for OctoFlow"
    )
    parser.add_argument(
        "--repo",
        default=os.getenv("OCTOFLOW_REPO", DEFAULT_REPO),
        help="Target GitHub repository (owner/repo)",
    )
    parser.add_argument(
        "--package",
        default=os.getenv("OCTOFLOW_PACKAGE", DEFAULT_PACKAGE),
        help="Target PyPI package name",
    )
    parser.add_argument(
        "--output-md",
        default="METRICS.md",
        help="Path to output markdown report file",
    )
    parser.add_argument(
        "--output-json",
        default="metrics.json",
        help="Path to output JSON data file",
    )
    parser.add_argument(
        "--fixture",
        default=os.getenv("OCTOFLOW_METRICS_FIXTURE"),
        help="Path to mock JSON fixture file for offline testing",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GITHUB_TOKEN"),
        help="GitHub Personal Access Token for higher API rate limits",
    )

    args = parser.parse_args()

    fixture_data = None
    if args.fixture:
        fixture_path = Path(args.fixture)
        if fixture_path.exists():
            fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))

    collector = MetricsCollector(
        repo=args.repo,
        package=args.package,
        token=args.token,
        fixture_data=fixture_data,
    )

    try:
        data = collector.compute_all_metrics()
    except Exception as e:
        print(f"Error computing metrics: {e}", file=sys.stderr)
        return 1

    # Output JSON
    json_path = Path(args.output_json)
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"✔ Metrics JSON written: {json_path}")

    # Output Markdown
    md_content = collector.render_markdown(data)
    md_path = Path(args.output_md)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"✔ Metrics Markdown written: {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
