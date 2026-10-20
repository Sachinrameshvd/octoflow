"""Characterization tests for the extracted cockpit router.

Verifies that the extraction of classify_input into octoflow/router.py preserves
existing routing semantics before hardening in P1.3.
"""

import pytest
from octoflow.router import classify_input, classify_input_legacy, RouteKind


def test_characterization_empty_and_whitespace():
    assert classify_input("").kind == RouteKind.EMPTY
    assert classify_input("   \t\n  ").kind == RouteKind.EMPTY


def test_characterization_prompt_prefixes():
    route = classify_input("octos ❯ ls -la")
    assert route.kind == RouteKind.SHELL_SIMPLE
    assert route.command == "ls -la"

    route_dollar = classify_input("$ ls -la")
    assert route_dollar.kind == RouteKind.SHELL_SIMPLE
    assert route_dollar.command == "ls -la"


def test_characterization_explicit_shell_prefixes():
    r1 = classify_input("!echo hello")
    assert r1.kind == RouteKind.SHELL_EXPLICIT
    assert r1.command == "echo hello"

    r2 = classify_input("/sh pytest tests/ -q")
    assert r2.kind == RouteKind.SHELL_EXPLICIT
    assert r2.command == "pytest tests/ -q"


def test_characterization_legacy_passthrough_commands():
    cmds = ["mkdir foo", "ls -l", "pwd", "touch test.txt", "cd ..", "cat README.md"]
    for c in cmds:
        route = classify_input(c)
        assert route.kind == RouteKind.SHELL_SIMPLE
        assert route.command == c


def test_characterization_slash_commands():
    r1 = classify_input("/help")
    assert r1.kind == RouteKind.SLASH_COMMAND

    # Slashless normalization
    r2 = classify_input("manual 3")
    assert r2.kind == RouteKind.SLASH_COMMAND
    assert r2.command.startswith("/manual")


def test_characterization_swarm_goal():
    route = classify_input("build a distributed key-value store in python")
    assert route.kind == RouteKind.SWARM_GOAL
    assert "build" in route.command
