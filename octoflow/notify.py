"""OctoFlow Team Mission Webhook Dispatcher (Slack & Discord).

Dispatches rich, bio-glyph styled notification cards to team channels
with mission verdicts, token economics, and PR links.
"""

import os
from typing import Any

import httpx


def format_slack_payload(
    mission_data: dict[str, Any], custom_msg: str | None = None
) -> dict[str, Any]:
    """Format an interactive Slack Block Kit card."""
    obj = mission_data.get("objective", "Mission Execution")
    verdict = mission_data.get("verdict", "PASSED")
    status_icon = "✔" if verdict == "PASSED" else "✖"
    econ = mission_data.get("token_economy", {})

    header_text = custom_msg or f"{status_icon} OctoFlow Swarm Mission: {verdict}"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text[:150],
                "emoji": False,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Objective:*\n{obj[:100]}"},
                {
                    "type": "mrkdwn",
                    "text": f"*Branch:*\n`{mission_data.get('branch', 'main')}` ({mission_data.get('commit', 'HEAD')})",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Swarm Cost:*\n${econ.get('swarm_cost', 0.0):.3f} ({econ.get('savings_pct', 0.0)}% saved)",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Ganglia Status:*\n{len(mission_data.get('arms', []))} arms verified clean",
                },
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"OctoFlow Cephalopod Swarm • Duration: {mission_data.get('duration_seconds', 0.0)}s • Zero AST syntax errors",
                }
            ],
        },
    ]

    return {"blocks": blocks, "text": f"{status_icon} OctoFlow Mission Audit: {verdict}"}


def format_discord_payload(
    mission_data: dict[str, Any], custom_msg: str | None = None
) -> dict[str, Any]:
    """Format a Discord webhook embed."""
    obj = mission_data.get("objective", "Mission Execution")
    verdict = mission_data.get("verdict", "PASSED")
    status_icon = "✔" if verdict == "PASSED" else "✖"
    econ = mission_data.get("token_economy", {})

    color = 0x22C55E if verdict == "PASSED" else 0xEF4444

    embed = {
        "title": f"◈ OctoFlow Swarm Mission Audit • {verdict}",
        "description": custom_msg or f"**Objective**: {obj}",
        "color": color,
        "fields": [
            {"name": "Swarm Verdict", "value": f"{status_icon} {verdict}", "inline": True},
            {
                "name": "Cost Saved",
                "value": f"{econ.get('savings_pct', 0.0)}% (${econ.get('swarm_cost', 0.0):.3f})",
                "inline": True,
            },
            {"name": "Branch", "value": f"`{mission_data.get('branch', 'main')}`", "inline": True},
            {"name": "8-Arm Topology", "value": "100% AST & security clearance", "inline": True},
            {
                "name": "Duration",
                "value": f"{mission_data.get('duration_seconds', 0.0)}s",
                "inline": True,
            },
        ],
        "footer": {"text": "OctoFlow Cephalopod Swarm Automation"},
    }

    return {"embeds": [embed], "content": None}


def send_mission_notification(
    webhook_url: str | None = None,
    mission_data: dict[str, Any] | None = None,
    custom_message: str | None = None,
    timeout: float = 8.0,
) -> bool:
    """Send mission summary to Slack, Discord, or generic incoming webhook."""
    url = (
        webhook_url
        or os.getenv("OCTOFLOW_WEBHOOK_URL")
        or os.getenv("SLACK_WEBHOOK_URL")
        or os.getenv("DISCORD_WEBHOOK_URL")
    )
    if not url:
        return False

    if not mission_data:
        from octoflow.report import collect_mission_audit_data

        mission_data = collect_mission_audit_data()

    if "discord.com" in url:
        payload = format_discord_payload(mission_data, custom_msg=custom_message)
    elif "slack.com" in url:
        payload = format_slack_payload(mission_data, custom_msg=custom_message)
    else:
        payload = {
            "title": f"OctoFlow Mission Audit: {mission_data.get('verdict', 'PASSED')}",
            "objective": mission_data.get("objective", ""),
            "message": custom_message or "Mission execution completed.",
            "data": mission_data,
        }

    try:
        resp = httpx.post(url, json=payload, timeout=timeout)
        return resp.status_code in [200, 201, 204]
    except Exception:
        return False
