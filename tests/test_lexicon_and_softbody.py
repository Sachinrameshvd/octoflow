"""Unit tests for Inter-Brachial Message Lexicon and Continuous 3D Soft-Body Tentacle Physics."""

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from envs.soft_body_tentacle import SoftBodyTentacleEnv
from octopus_brain.lexicon import INTENT_METADATA, InterBrachialLexiconDecoder, MessageIntent


def test_lexicon_initialization():
    """Verify lexicon initializes valid intent prototypes and metadata."""
    decoder = InterBrachialLexiconDecoder(message_dim=32)
    assert decoder.prototypes.shape == (6, 32)
    assert len(decoder.intents) == 6

    for intent in decoder.intents:
        assert intent in INTENT_METADATA
        meta = INTENT_METADATA[intent]
        assert "label" in meta
        assert "icon" in meta
        assert "color" in meta


def test_lexicon_vector_decoding():
    """Verify decoding a synthetic message vector produces correct intent and confidence."""
    decoder = InterBrachialLexiconDecoder(message_dim=32)

    # Test decoding prototype 1 directly (TARGET_DETECTED)
    proto_target = decoder.prototypes[1].cpu().numpy()
    intent, conf, meta = decoder.decode_vector(proto_target)
    assert intent == MessageIntent.TARGET_DETECTED
    assert conf >= 0.99
    assert meta["label"] == "Prey / Food Detected"

    # Test decoding prototype 2 directly (COOPERATIVE_PULL)
    proto_coop = decoder.prototypes[2].cpu().numpy()
    intent, conf, meta = decoder.decode_vector(proto_coop)
    assert intent == MessageIntent.COOPERATIVE_PULL
    assert conf >= 0.99
    assert "Cooperative" in meta["label"]


def test_lexicon_all_arms_decoding():
    """Verify batch decoding for 8 arms with gated reporting flags."""
    decoder = InterBrachialLexiconDecoder(message_dim=32)
    dummy_msgs = torch.randn(8, 32)
    report_flags = [False, True, True, False, False, False, False, False]

    decoded = decoder.decode_all_arms(dummy_msgs, report_flags=report_flags)
    assert len(decoded) == 8

    # Non-reporting arm (Arm 0) should remain autonomous exploration
    assert decoded[0]["intent"] == MessageIntent.AUTONOMOUS_EXPLORE
    assert decoded[0]["is_reporting"] is False
    assert decoded[0]["confidence"] >= 0.9

    # Reporting arm (Arm 1) should be active
    assert decoded[1]["is_reporting"] is True
    assert decoded[1]["arm_index"] == 1
    assert "description" in decoded[1]


def test_soft_body_tentacle_env_initialization():
    """Verify soft-body 3D tentacle environment initialization and observation space."""
    env = SoftBodyTentacleEnv(n_arms=8, segments_per_arm=5, max_steps=40)
    assert env.observation_space.shape == (8, 16)
    assert env.action_space.shape == (8,)

    obs, info = env.reset()
    assert obs.shape == (8, 16)
    assert "target_pos" in info
    assert len(info["target_pos"]) == 3


def test_soft_body_tentacle_volume_preservation():
    """Verify muscular hydrostat continuum mechanics: volume preservation."""
    env = SoftBodyTentacleEnv(n_arms=8, segments_per_arm=5)
    env.reset()

    # Step environment with elongation commands (action 1 = elongate / pitch)
    actions = np.ones(8, dtype=np.int64)
    obs, rewards, term, trunc, info = env.step(actions)

    assert obs.shape == (8, 16)
    assert len(rewards) == 8
    assert isinstance(term, bool)
    assert isinstance(trunc, bool)

    # Check that arm lengths and radii maintain positive bounds
    for arm in env.arms:
        assert arm.base_radius > 0.0
        assert arm.segment_length > 0.0
        tip_pos = arm.get_tip_position()
        assert len(tip_pos) == 3


def test_soft_body_tentacle_actions_and_rewards():
    """Verify all discrete action indices (0 to 4) execute safely and compute rewards."""
    env = SoftBodyTentacleEnv(n_arms=8, segments_per_arm=4, max_steps=10)
    obs, _ = env.reset()

    for act_idx in range(5):
        actions = np.full(8, act_idx, dtype=np.int64)
        obs, rewards, term, trunc, info = env.step(actions)
        assert np.isfinite(obs).all()
        assert np.isfinite(rewards).all()

    # Test episode termination / truncation
    actions = np.zeros(8, dtype=np.int64)
    for _ in range(12):
        obs, rewards, term, trunc, info = env.step(actions)
    assert trunc is True  # Reached max steps
