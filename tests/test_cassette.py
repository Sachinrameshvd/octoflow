"""Unit tests for CassetteRecorder and ReplayProvider."""

import tempfile
import pytest
from pathlib import Path

from octoflow.cassette import (
    CassetteRecorder,
    ReplayProvider,
    normalize_cassette_text,
    compute_request_hash,
)
from octoflow.provider import MockLLMProvider


def test_normalize_cassette_text_strips_paths_and_secrets(tmp_path):
    fake_key = "Bearer " + "ghp_" + "1234567890abcdefghijklmnopqrstuvwxyz"
    raw = f"Working in {tmp_path}/workspace with /Users/sachinrk/secret and TOKEN={fake_key}"
    normalized = normalize_cassette_text(raw, workspace_root=tmp_path)
    assert str(tmp_path) not in normalized
    assert "<WORKSPACE>" in normalized
    assert "/Users/sachinrk" not in normalized
    assert "<HOME>" in normalized
    assert "1234567890abcdef" not in normalized


def test_cassette_record_and_replay_cycle(tmp_path):
    cassette_dir = tmp_path / "cassettes"
    mock_provider = MockLLMProvider()

    # 1. Record
    recorder = CassetteRecorder(
        provider=mock_provider,
        cassette_dir=cassette_dir,
        workspace_root=tmp_path,
    )
    prompt = "Current Arm Objective: Write rate limiter in limiter.py\nStep: 1 of max 5"
    sys_prompt = "You are Backend Developer in the OctoFlow swarm."

    resp1 = recorder.generate(prompt=prompt, system_prompt=sys_prompt)
    assert resp1.content
    assert (cassette_dir / "cassette.json").exists()

    # 2. Replay offline
    replay = ReplayProvider(
        cassette_dir=cassette_dir,
        workspace_root=tmp_path,
    )
    resp2 = replay.generate(prompt=prompt, system_prompt=sys_prompt)
    assert resp2.content == resp1.content
    assert resp2.tokens_prompt == resp1.tokens_prompt
    assert resp2.tokens_completion == resp1.tokens_completion


def test_cassette_record_and_replay_async(tmp_path):
    import asyncio

    async def _run():
        cassette_dir = tmp_path / "cassettes_async"
        mock_provider = MockLLMProvider()

        recorder = CassetteRecorder(
            provider=mock_provider,
            cassette_dir=cassette_dir,
            workspace_root=tmp_path,
        )
        prompt = "Async arm prompt"
        sys_prompt = "Async system prompt"

        resp1 = await recorder.agenerate(prompt=prompt, system_prompt=sys_prompt)
        assert resp1.content

        replay = ReplayProvider(
            cassette_dir=cassette_dir,
            workspace_root=tmp_path,
        )
        resp2 = await replay.agenerate(prompt=prompt, system_prompt=sys_prompt)
        assert resp2.content == resp1.content

    asyncio.run(_run())
