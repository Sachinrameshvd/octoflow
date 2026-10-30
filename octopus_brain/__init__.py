"""OctopusBrain: Modular, biologically inspired distributed neural architecture."""

from octopus_brain.config import EnvConfig, OctopusBrainConfig

try:
    from octopus_brain.brain import OctopusBrain
    from octopus_brain.central import CentralSystem
    from octopus_brain.losses import AdaptiveGateBudgeter, OctopusLoss
    from octopus_brain.modules import PeripheralModule
    from octopus_brain.trainer import OctopusTrainer
except ImportError:
    PeripheralModule = None
    CentralSystem = None
    OctopusBrain = None
    OctopusLoss = None
    AdaptiveGateBudgeter = None
    OctopusTrainer = None

from octopus_brain.bend_propagation import StereotypicBendWaveController
from octopus_brain.biophysics import BiophysicalConnectomeSimulator
from octopus_brain.connectome import (
    CephalopodConnectome,
    ConnectomeNode,
    NeuronCategory,
    Neurotransmitter,
    SynapticEdge,
)
from octopus_brain.connectome_controller import ConnectomeEmbodiedController
from octopus_brain.hodgkin_huxley import CephalopodHodgkinHuxley
from octopus_brain.neuromodulation import CephalopodNeuromodulation
from octopus_brain.vertical_lobe_ltp import VerticalLobeAssociativeMemory

__all__ = [
    "OctopusBrainConfig",
    "EnvConfig",
    "PeripheralModule",
    "CentralSystem",
    "OctopusBrain",
    "OctopusLoss",
    "AdaptiveGateBudgeter",
    "extract_coalitions_from_matrix",
    "OctopusTrainer",
    "CephalopodConnectome",
    "ConnectomeNode",
    "SynapticEdge",
    "Neurotransmitter",
    "NeuronCategory",
    "BiophysicalConnectomeSimulator",
    "ConnectomeEmbodiedController",
    "CephalopodHodgkinHuxley",
    "VerticalLobeAssociativeMemory",
    "StereotypicBendWaveController",
    "CephalopodNeuromodulation",
]
