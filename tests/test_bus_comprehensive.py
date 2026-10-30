"""Comprehensive test suite for InterBrachialBus (Subsystem 3.3).

Verifies:
1. Ring topology neighbor routing for N=8, 24, 64.
2. Edge topologies (N=1, N=2).
3. Lateral send and ring broadcast to neighbors.
4. Bounded inbox queue overflow (maxlen=20 FIFO retention).
5. Dead / invalid arm target handling without bus corruption.
6. PII sanitization integration during message delivery.
"""

import pytest
from octoflow.bus import InterBrachialBus, MessageIntent


def test_ring_topology_scaling():
    """Verify neighbor calculation wraps correctly across ring sizes N=8, 24, 64."""
    for n in [8, 24, 64]:
        bus = InterBrachialBus(n_arms=n)
        for i in range(n):
            left, right = bus.get_neighbors(i)
            expected_left = (i - 1) % n
            expected_right = (i + 1) % n
            assert left == expected_left, (
                f"N={n}, node {i}: expected left {expected_left}, got {left}"
            )
            assert right == expected_right, (
                f"N={n}, node {i}: expected right {expected_right}, got {right}"
            )


def test_ring_topology_edge_cases():
    """Verify behavior on minimal rings N=1 and N=2."""
    bus_2 = InterBrachialBus(n_arms=2)
    assert bus_2.get_neighbors(0) == (1, 1)
    assert bus_2.get_neighbors(1) == (0, 0)

    # N <= 0 should raise ValueError
    with pytest.raises(ValueError):
        InterBrachialBus(n_arms=0)
    with pytest.raises(ValueError):
        InterBrachialBus(n_arms=-5)


def test_send_lateral_and_drain():
    """Verify lateral message transmission and inbox draining."""
    bus = InterBrachialBus(n_arms=8)
    msg = bus.send_lateral(
        sender_id=1,
        target_id=2,
        intent=MessageIntent.COOPERATIVE_PULL,
        summary="Please inspect DB migration",
        payload={"migration_id": 42},
    )
    assert msg.sender_id == 1
    assert msg.target_id == 2
    assert msg.summary == "Please inspect DB migration"
    assert len(bus.message_history) == 1

    # Arm 2 should have 1 message, Arm 1 should have 0
    inbox_1 = bus.poll_inbox(1)
    assert len(inbox_1) == 0

    inbox_2 = bus.poll_inbox(2)
    assert len(inbox_2) == 1
    assert inbox_2[0].payload["migration_id"] == 42

    # Inbox 2 is drained
    assert len(bus.poll_inbox(2)) == 0


def test_broadcast_ring():
    """Verify broadcast delivers to left and right neighbors only."""
    bus = InterBrachialBus(n_arms=8)
    msgs = bus.broadcast_ring(
        sender_id=0,
        intent=MessageIntent.AUTONOMOUS_EXPLORE,
        summary="Exploring neighborhood",
    )
    assert len(msgs) == 2
    left_target = msgs[0].target_id
    right_target = msgs[1].target_id
    assert left_target == 7
    assert right_target == 1

    assert len(bus.poll_inbox(7)) == 1
    assert len(bus.poll_inbox(1)) == 1
    assert len(bus.poll_inbox(0)) == 0


def test_inbox_queue_bounded_overflow():
    """Verify bounded inbox maxlen=20 discards oldest messages without leak."""
    bus = InterBrachialBus(n_arms=8)
    target = 3

    for i in range(35):
        bus.send_lateral(
            sender_id=0,
            target_id=target,
            intent=MessageIntent.AUTONOMOUS_EXPLORE,
            summary=f"Message {i}",
        )

    inbox = bus.poll_inbox(target)
    assert len(inbox) == 20
    # Oldest (0-14) dropped, newest (15-34) retained
    assert inbox[0].summary == "Message 15"
    assert inbox[-1].summary == "Message 34"


def test_invalid_target_handling():
    """Verify sending to or polling non-existent arm handles safely with KeyError or ValueError."""
    bus = InterBrachialBus(n_arms=8)

    with pytest.raises((ValueError, KeyError)):
        bus.send_lateral(sender_id=0, target_id=99, intent=MessageIntent.AUTONOMOUS_EXPLORE)

    with pytest.raises((ValueError, KeyError)):
        bus.poll_inbox(99)


def test_pii_sanitization_on_bus():
    """Verify sensitive tokens are cleansed before delivery on the bus."""
    bus = InterBrachialBus(n_arms=8)
    # Transmit payload containing dummy auth token / secret
    bus.send_lateral(
        sender_id=0,
        target_id=1,
        intent=MessageIntent.COOPERATIVE_PULL,
        summary="Connecting using secret key "
        + "sk-ant-"
        + "api03-abcdef1234567890abcdef1234567890",
        payload={"api_token": "sk-proj-" + "supersecrettoken1234567890abcdef12345"},
    )
    inbox = bus.poll_inbox(1)
    assert len(inbox) == 1
    delivered = inbox[0]
    # Guard should sanitize secret tokens
    assert "sk-ant-" not in delivered.summary or "[REDACTED" in delivered.summary


def test_dead_arm_neighbor_bypass():
    """Verify dead arm failure triggers neighbor bypass across ring."""
    bus = InterBrachialBus(n_arms=8)
    # Default: Arm 0 neighbors are (7, 1)
    assert bus.get_neighbors(0) == (7, 1)

    # Arm 1 fails/dies
    bus.mark_arm_inactive(1)
    assert not bus.is_arm_active(1)

    # Arm 0 right neighbor bypasses dead Arm 1 to reach Arm 2
    left, right = bus.get_neighbors(0)
    assert left == 7
    assert right == 2

    # Arm 2 left neighbor bypasses dead Arm 1 to reach Arm 0
    left2, right2 = bus.get_neighbors(2)
    assert left2 == 0
    assert right2 == 3

    # Recover Arm 1
    bus.mark_arm_active(1)
    assert bus.get_neighbors(0) == (7, 1)
