"""OctopusBrain: Modular, biologically inspired distributed neural architecture."""

from octopus_brain.config import OctopusBrainConfig, EnvConfig
from octopus_brain.modules import PeripheralModule
from octopus_brain.central import CentralSystem
from octopus_brain.brain import OctopusBrain
from octopus_brain.losses import OctopusLoss, AdaptiveGateBudgeter
from octopus_brain.coalition import extract_coalitions_from_matrix
from octopus_brain.trainer import OctopusTrainer

from octopus_brain.connectome import CephalopodConnectome, ConnectomeNode, SynapticEdge, Neurotransmitter, NeuronCategory
from octopus_brain.biophysics import BiophysicalConnectomeSimulator
from octopus_brain.connectome_controller import ConnectomeEmbodiedController
from octopus_brain.hodgkin_huxley import CephalopodHodgkinHuxley
from octopus_brain.vertical_lobe_ltp import VerticalLobeAssociativeMemory
from octopus_brain.bend_propagation import StereotypicBendWaveController
from octopus_brain.neuromodulation import CephalopodNeuromodulation

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
