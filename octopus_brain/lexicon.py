"""Inter-Brachial Message Lexicon & Semantic Decoder for OctopusBrain.

Decodes 32-dimensional continuous latent messages exchanged laterally along the
interbrachial ring and vertically to the central brain into human-interpretable
semantic communication intents.

Biological Analogy:
Cephalopods communicate state through localized chromatophore waves and neuromuscular
posturing. This module clusters the high-dimensional latent messaging space into
semantic prototypes:
- TARGET_DETECTED: Sucker chemical/tactile sensors detected high-value prey.
- COOPERATIVE_PULL: Heavy joint target requires simultaneous multi-arm synchronization.
- HAZARD_WARNING: Moving predator or toxic coral approaching sector.
- REACH_ELONGATION: Muscular hydrostat extension towards sensory boundary.
- ANCHOR_STABILITY: High normal contact force holding body against substrate.
- AUTONOMOUS_EXPLORATION: Routine local sensory sampling without urgent distress.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from octopus_brain.config import OctopusBrainConfig


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


class InterBrachialLexiconDecoder(nn.Module):
    """Vector-quantized semantic decoder mapping 32D latent vectors to semantic intents."""

    def __init__(self, message_dim: int = 32):
        super().__init__()
        self.message_dim = message_dim
        self.intents = [
            MessageIntent.AUTONOMOUS_EXPLORE,
            MessageIntent.TARGET_DETECTED,
            MessageIntent.COOPERATIVE_PULL,
            MessageIntent.HAZARD_WARNING,
            MessageIntent.REACH_ELONGATION,
            MessageIntent.ANCHOR_STABILITY,
        ]
        self.num_intents = len(self.intents)

        # Prototype vectors in latent space
        rng = np.random.RandomState(42)
        prototypes = rng.randn(self.num_intents, message_dim).astype(np.float32)
        # Normalize prototypes to unit sphere
        prototypes = prototypes / np.linalg.norm(prototypes, axis=-1, keepdims=True)
        self.register_buffer("prototypes", torch.tensor(prototypes))

    def decode_vector(self, msg_tensor: torch.Tensor) -> Tuple[str, float, Dict[str, Any]]:
        """Decode a single (message_dim,) message vector into semantic intent.

        Args:
            msg_tensor: (message_dim,) tensor or numpy array.

        Returns:
            intent_name: e.g. 'COOPERATIVE_PULL'
            confidence: cosine similarity confidence [0.0, 1.0]
            metadata: dictionary with label, icon, color
        """
        if isinstance(msg_tensor, np.ndarray):
            msg = torch.tensor(msg_tensor, dtype=torch.float32, device=self.prototypes.device)
        else:
            msg = msg_tensor.to(self.prototypes.device).float()

        if msg.dim() == 1:
            msg = msg.unsqueeze(0)

        norm_msg = F.normalize(msg, p=2, dim=-1)
        norm_proto = F.normalize(self.prototypes, p=2, dim=-1)

        sims = torch.matmul(norm_msg, norm_proto.T)[0]  # (num_intents,)
        best_idx = int(torch.argmax(sims).item())
        confidence = float(torch.clamp((sims[best_idx] + 1.0) / 2.0, 0.0, 1.0).item())

        intent = self.intents[best_idx]
        meta = INTENT_METADATA[intent]
        return intent, confidence, meta

    def decode_all_arms(
        self,
        messages: Union[np.ndarray, torch.Tensor],
        report_flags: Optional[Union[np.ndarray, torch.Tensor, List[bool]]] = None,
    ) -> List[Dict[str, Any]]:
        """Decode all N arm messages simultaneously.

        Args:
            messages: (N, message_dim) array or tensor.
            report_flags: Optional (N,) boolean array indicating active reporting.

        Returns:
            List of 8 decoded intent dictionaries.
        """
        if isinstance(messages, torch.Tensor):
            msgs_np = messages.detach().cpu().numpy()
        else:
            msgs_np = messages

        n_arms = msgs_np.shape[0]
        results = []

        for i in range(n_arms):
            is_reporting = bool(report_flags[i]) if report_flags is not None else True
            intent, conf, meta = self.decode_vector(msgs_np[i])

            if not is_reporting:
                # If arm didn't gate a message, it remains autonomous
                intent = MessageIntent.AUTONOMOUS_EXPLORE
                meta = INTENT_METADATA[intent]
                conf = 0.95

            results.append({
                "arm_index": i,
                "intent": intent,
                "label": meta["label"],
                "icon": meta["icon"],
                "color": meta["color"],
                "description": meta["description"],
                "confidence": conf,
                "is_reporting": is_reporting,
            })

        return results
