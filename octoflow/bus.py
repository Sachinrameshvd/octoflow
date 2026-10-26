"""Inter-Brachial Ring Bus for Lateral Peer-to-Peer Communication.

Enables adjacent arm neighbors on the 8-ganglia cephalopod nerve ring to communicate
directly via compact biological semantic message tokens without routing through the
central conductor, preventing orchestrator context window saturation.
"""

import time
from collections import deque
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

class MessageIntent:
    """Enumeration of semantic arm communication intents."""
    AUTONOMOUS_EXPLORE = "AUTONOMOUS_EXPLORE"
    TARGET_DETECTED = "TARGET_DETECTED"
    COOPERATIVE_PULL = "COOPERATIVE_PULL"
    HAZARD_WARNING = "HAZARD_WARNING"
    REACH_ELONGATION = "REACH_ELONGATION"
    ANCHOR_STABILITY = "ANCHOR_STABILITY"


INTENT_METADATA = {
    MessageIntent.AUTONOMOUS_EXPLORE: {
        "label": "Autonomous Forage",
        "icon": "🟢",
        "description": "Routine local sensory sampling; no central assistance required.",
        "color": "#a6e3a1",
    },
    MessageIntent.TARGET_DETECTED: {
        "label": "Prey / Food Detected",
        "icon": "🦐",
        "description": "Chemical cues confirm food item in reach radius.",
        "color": "#89b4fa",
    },
    MessageIntent.COOPERATIVE_PULL: {
        "label": "Cooperative Grip Request",
        "icon": "🤝",
        "description": "Joint target requires dual-arm bilateral synchronization.",
        "color": "#cba6f7",
    },
    MessageIntent.HAZARD_WARNING: {
        "label": "Predator / Hazard Alert",
        "icon": "⚠️",
        "description": "High prediction surprise; rapid detour or repulsion triggered.",
        "color": "#f38ba8",
    },
    MessageIntent.REACH_ELONGATION: {
        "label": "Hydrostat Elongation",
        "icon": "↔️",
        "description": "Arm fully extended outward exploring perimeter.",
        "color": "#f9e2af",
    },
    MessageIntent.ANCHOR_STABILITY: {
        "label": "Substrate Anchor",
        "icon": "⚓️",
        "description": "Suckers locked to ground providing leverage for other arms.",
        "color": "#94e2d5",
    },
}


class BrachialMessage(BaseModel):
    """Compact lateral message exchanged across the inter-brachial ring."""
    sender_id: int
    target_id: int
    intent: str = MessageIntent.AUTONOMOUS_EXPLORE
    payload: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    timestamp: float = Field(default_factory=time.time)


from octoflow.federation import GLOBAL_FEDERATION_GUARD, FederationGuard


class InterBrachialBus:
    """Ring-topology message bus connecting arm ganglia with zero-trust PII sanitization and dead-arm fault tolerance."""

    def __init__(self, n_arms: int = 8, guard: Optional[FederationGuard] = None):
        if n_arms <= 0:
            raise ValueError(f"n_arms must be positive integer >= 1, got {n_arms}")
        self.n_arms = n_arms
        self.guard = guard or GLOBAL_FEDERATION_GUARD
        # Inboxes for each arm: arm_id -> deque of incoming BrachialMessages
        self._inboxes: Dict[int, deque] = {i: deque(maxlen=20) for i in range(n_arms)}
        self._active_arms: set[int] = set(range(n_arms))
        self.message_history: List[BrachialMessage] = []

    def mark_arm_inactive(self, arm_id: int) -> None:
        """Mark an arm as dead/offline so lateral routing bypasses it."""
        self._active_arms.discard(arm_id)

    def mark_arm_active(self, arm_id: int) -> None:
        """Mark an arm as active/online."""
        if 0 <= arm_id < self.n_arms:
            self._active_arms.add(arm_id)

    def is_arm_active(self, arm_id: int) -> bool:
        """Return True if arm is active."""
        return arm_id in self._active_arms

    def get_neighbors(self, arm_id: int) -> Tuple[int, int]:
        """Return (left_neighbor_id, right_neighbor_id) on the ring, bypassing dead arms."""
        if self.n_arms == 1:
            return 0, 0

        # Traverse backward to find first active left neighbor
        left = (arm_id - 1) % self.n_arms
        for step in range(1, self.n_arms):
            cand = (arm_id - step) % self.n_arms
            if cand in self._active_arms and cand != arm_id:
                left = cand
                break

        # Traverse forward to find first active right neighbor
        right = (arm_id + 1) % self.n_arms
        for step in range(1, self.n_arms):
            cand = (arm_id + step) % self.n_arms
            if cand in self._active_arms and cand != arm_id:
                right = cand
                break

        return left, right

    def send_lateral(
        self,
        sender_id: int,
        target_id: int,
        intent: str,
        summary: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> BrachialMessage:
        """Transmit a message laterally along the ring bus with PII sanitization."""
        if target_id not in self._inboxes:
            raise ValueError(f"Target arm {target_id} not connected to bus (valid: 0..{self.n_arms - 1})")
        if sender_id not in self._inboxes:
            raise ValueError(f"Sender arm {sender_id} not connected to bus (valid: 0..{self.n_arms - 1})")

        # Cleanse summary and payload of sensitive credentials/PII
        clean_summary, _ = self.guard.scan_and_sanitize(summary) if self.guard else (summary, [])
        clean_payload, _ = self.guard.sanitize_payload(payload or {}) if self.guard else (payload or {}, [])

        msg = BrachialMessage(
            sender_id=sender_id,
            target_id=target_id,
            intent=intent,
            summary=clean_summary,
            payload=clean_payload,
        )
        self._inboxes[target_id].append(msg)
        self.message_history.append(msg)
        return msg

    def broadcast_ring(
        self,
        sender_id: int,
        intent: str,
        summary: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> List[BrachialMessage]:
        """Broadcast a message to immediate ring neighbors (left and right), bypassing dead arms."""
        left, right = self.get_neighbors(sender_id)
        msg_l = self.send_lateral(sender_id, left, intent, summary, payload)
        msg_r = self.send_lateral(sender_id, right, intent, summary, payload)
        return [msg_l, msg_r]

    def poll_inbox(self, arm_id: int) -> List[BrachialMessage]:
        """Drain and return all pending messages for an arm."""
        if arm_id not in self._inboxes:
            raise ValueError(f"Arm {arm_id} not connected to bus (valid: 0..{self.n_arms - 1})")
        inbox = self._inboxes[arm_id]
        messages = list(inbox)
        inbox.clear()
        return messages

    def clear(self) -> None:
        """Reset all inboxes, active states, and history."""
        for inbox in self._inboxes.values():
            inbox.clear()
        self._active_arms = set(range(self.n_arms))
        self.message_history.clear()
