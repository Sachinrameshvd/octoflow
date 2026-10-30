"""Cephalopod Micro-Connectome Architecture and Biological Adjacency Matrix Builder.

Implements the connectome pipeline inspired by Google Connectomics and FlyWire:
- Biologically classified neuron types (Sensory afferents, Amacrine interneurons,
  Relay interneurons, Motor command descending neurons, Axial motoneurons).
- Explicit 3D spatial coordinate allocation across recognized cephalopod brain lobes
  (Vertical Lobe System, Subvertical, Superior Frontal, Subesophageal, Interbrachial Ring,
   and 8 Brachial Axial Cords).
- Adheres strictly to Dale's Principle: each neuron maintains a single neurotransmitter identity
  (Acetylcholine: excitatory (+), GABA / Glutamate: inhibitory (-), Dopamine / Octopamine: modulatory).
- Produces a sparse, directed, weighted synaptic adjacency matrix W_ij.
- Direct JSON export compatible with WebGL visualizers, Graph Neural Networks, and
  biophysical Spiking Neural Network (SNN) simulation engines.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


class Neurotransmitter(str, Enum):
    ACETYLCHOLINE = "acetylcholine"  # Primary invertebrate excitatory transmitter
    GABA = "gaba"  # Primary central inhibitory transmitter
    GLUTAMATE = "glutamate"  # Invertebrate neuromuscular & peripheral inhibitor
    DOPAMINE = "dopamine"  # Neuromodulatory / reinforcement transmitter
    OCTOPAMINE = "octopamine"  # Neuromodulatory / invertebrate arousal transmitter


class NeuronCategory(str, Enum):
    SENSORY_CHEMO = "sensory_chemotactile"
    SENSORY_MECHANO = "sensory_mechanoreceptor"
    SENSORY_OPTIC = "sensory_optic_retinula"
    INTER_AMACRINE = "interneuron_amacrine"
    INTER_RELAY = "interneuron_relay"
    INTER_RING = "interneuron_brachial_ring"
    MOTOR_DESCENDING = "motor_subesophageal_command"
    MOTOR_BRACHIAL = "motor_brachial_axial"


@dataclass
class ConnectomeNode:
    """A biologically identified neuron in the cephalopod connectome."""

    id: int
    label: str
    region: str
    arm_index: int  # -1 for central brain, 0..7 for arms
    segment_index: int  # -1 for central, 0..N for arm segments
    category: NeuronCategory
    neurotransmitter: Neurotransmitter
    sign: float  # +1.0 for excitatory, -1.0 for inhibitory, 0.0 for pure modulatory
    position: tuple[float, float, float]
    base_firing_threshold_mv: float = -50.0
    resting_potential_mv: float = -70.0
    membrane_capacitance_uf: float = 1.0


@dataclass
class SynapticEdge:
    """A directed synaptic contact between two identified neurons."""

    source_id: int
    target_id: int
    synapse_count: int  # Biological contact count (1 to 20+)
    conductance_ns: float  # Conductance in nano-Siemens
    sign: float  # Inherited from presynaptic neuron's Dale sign (+1 or -1)
    synapse_type: str = "chemical"  # "chemical" or "gap_junction"
    conduction_delay_ms: float = 1.0


class CephalopodConnectome:
    """Complete cephalopod connectome graph with microcircuits and biological Dale polarity."""

    def __init__(self, scale_factor: float = 1.0, seed: int = 42):
        self.scale_factor = scale_factor
        self.rng = np.random.RandomState(seed)
        self.nodes: list[ConnectomeNode] = []
        self.edges: list[SynapticEdge] = []
        self.node_by_id: dict[int, ConnectomeNode] = {}
        self.edges_by_source: dict[int, list[SynapticEdge]] = {}
        self.edges_by_target: dict[int, list[SynapticEdge]] = {}
        self.region_node_ids: dict[str, list[int]] = {}

        self._build_connectome()

    def _add_node(
        self,
        label: str,
        region: str,
        arm_index: int,
        segment_index: int,
        category: NeuronCategory,
        transmitter: Neurotransmitter,
        pos: tuple[float, float, float],
    ) -> int:
        node_id = len(self.nodes)
        sign = (
            1.0
            if transmitter == Neurotransmitter.ACETYLCHOLINE
            else (
                -1.0 if transmitter in (Neurotransmitter.GABA, Neurotransmitter.GLUTAMATE) else 0.5
            )
        )
        node = ConnectomeNode(
            id=node_id,
            label=label,
            region=region,
            arm_index=arm_index,
            segment_index=segment_index,
            category=category,
            neurotransmitter=transmitter,
            sign=sign,
            position=pos,
        )
        self.nodes.append(node)
        self.node_by_id[node_id] = node
        self.edges_by_source[node_id] = []
        self.edges_by_target[node_id] = []
        self.region_node_ids.setdefault(region, []).append(node_id)
        return node_id

    def _add_edge(
        self,
        source_id: int,
        target_id: int,
        synapse_count: int = 1,
        base_conductance_ns: float = 2.5,
    ):
        if source_id == target_id:
            return  # No autapses in baseline connectome
        src_node = self.node_by_id[source_id]
        edge = SynapticEdge(
            source_id=source_id,
            target_id=target_id,
            synapse_count=synapse_count,
            conductance_ns=base_conductance_ns * synapse_count,
            sign=src_node.sign,
            synapse_type="chemical",
            conduction_delay_ms=float(self.rng.uniform(0.5, 2.5)),
        )
        self.edges.append(edge)
        self.edges_by_source[source_id].append(edge)
        self.edges_by_target[target_id].append(edge)

    def _build_connectome(self):
        """Build the cephalopod micro-connectome adhering to published neuroanatomy."""
        # 1. Vertical Lobe (VL) System: Associative Learning & Long-Term Memory
        # Modeled after J.Z. Young (1971) & B. Hochner (2012):
        # Superior frontal afferents -> Amacrine interneurons (massive parallel fiber matrix)
        # -> Large efferent neurons -> Subvertical feedback.
        sfl_ids = []
        for i in range(int(12 * self.scale_factor)):
            x = float(self.rng.normal(0.0, 0.4))
            y = float(self.rng.normal(2.5, 0.3))
            z = float(self.rng.normal(0.8, 0.3))
            nid = self._add_node(
                label=f"SFL_Afferent_{i}",
                region="superior_frontal_lobe",
                arm_index=-1,
                segment_index=-1,
                category=NeuronCategory.INTER_RELAY,
                transmitter=Neurotransmitter.ACETYLCHOLINE,
                pos=(x, y, z),
            )
            sfl_ids.append(nid)

        vl_amacrine_ids = []
        for i in range(int(36 * self.scale_factor)):
            x = float(self.rng.normal(0.0, 0.6))
            y = float(self.rng.normal(3.2, 0.4))
            z = float(self.rng.normal(1.2, 0.4))
            # Amacrine cells are densely cholinergic or GABAergic (feedforward inhibition)
            transmitter = Neurotransmitter.ACETYLCHOLINE if i % 4 != 0 else Neurotransmitter.GABA
            nid = self._add_node(
                label=f"VL_Amacrine_{i}",
                region="vertical_lobe",
                arm_index=-1,
                segment_index=-1,
                category=NeuronCategory.INTER_AMACRINE,
                transmitter=transmitter,
                pos=(x, y, z),
            )
            vl_amacrine_ids.append(nid)

        vl_efferent_ids = []
        for i in range(int(8 * self.scale_factor)):
            x = float(self.rng.normal(0.0, 0.5))
            y = float(self.rng.normal(2.0, 0.3))
            z = float(self.rng.normal(0.5, 0.3))
            nid = self._add_node(
                label=f"VL_LargeEfferent_{i}",
                region="subvertical_lobe",
                arm_index=-1,
                segment_index=-1,
                category=NeuronCategory.INTER_RELAY,
                transmitter=Neurotransmitter.ACETYLCHOLINE,
                pos=(x, y, z),
            )
            vl_efferent_ids.append(nid)

        # Wire Vertical Lobe Matrix:
        # SFL -> Amacrine (divergent connectivity)
        for s_id in sfl_ids:
            targets = self.rng.choice(
                vl_amacrine_ids, size=min(8, len(vl_amacrine_ids)), replace=False
            )
            for t_id in targets:
                self._add_edge(s_id, int(t_id), synapse_count=int(self.rng.randint(2, 6)))

        # Amacrine -> Efferent (convergent connectivity)
        for a_id in vl_amacrine_ids:
            targets = self.rng.choice(
                vl_efferent_ids, size=min(3, len(vl_efferent_ids)), replace=False
            )
            for t_id in targets:
                self._add_edge(a_id, int(t_id), synapse_count=int(self.rng.randint(1, 5)))

        # 2. Subesophageal Motor Centers (Descending Motor Commands)
        subesoph_ids = []
        for i in range(int(16 * self.scale_factor)):
            x = float(self.rng.normal(0.0, 0.5))
            y = float(self.rng.normal(0.5, 0.4))
            z = float(self.rng.normal(-0.5, 0.4))
            transmitter = Neurotransmitter.ACETYLCHOLINE if i % 3 != 0 else Neurotransmitter.GABA
            nid = self._add_node(
                label=f"Subesoph_MotorCmd_{i}",
                region="subesophageal_mass",
                arm_index=-1,
                segment_index=-1,
                category=NeuronCategory.MOTOR_DESCENDING,
                transmitter=transmitter,
                pos=(x, y, z),
            )
            subesoph_ids.append(nid)

        # VL Efferents -> Subesophageal motor centers
        for eff_id in vl_efferent_ids:
            targets = self.rng.choice(subesoph_ids, size=min(4, len(subesoph_ids)), replace=False)
            for t_id in targets:
                self._add_edge(eff_id, int(t_id), synapse_count=int(self.rng.randint(3, 8)))

        # 3. Interbrachial Nerve Ring (Circular coordination tract across all 8 arms)
        ring_ids = []
        for arm_idx in range(8):
            angle = (arm_idx / 8.0) * 2.0 * np.pi
            rx = float(2.0 * np.cos(angle))
            ry = float(0.0 + self.rng.normal(0.0, 0.1))
            rz = float(2.0 * np.sin(angle))
            nid = self._add_node(
                label=f"Interbrachial_Ring_Arm_{arm_idx}",
                region="interbrachial_nerve_ring",
                arm_index=arm_idx,
                segment_index=-1,
                category=NeuronCategory.INTER_RING,
                transmitter=Neurotransmitter.ACETYLCHOLINE,
                pos=(rx, ry, rz),
            )
            ring_ids.append(nid)

        # Wire ring in bidirectional circular topology
        for idx in range(8):
            curr = ring_ids[idx]
            left = ring_ids[(idx - 1) % 8]
            right = ring_ids[(idx + 1) % 8]
            self._add_edge(curr, left, synapse_count=4)
            self._add_edge(curr, right, synapse_count=4)

        # 4. Distributed 8 Brachial Axial Cords & Sucker Ganglia
        self.arm_sensory_ids: dict[int, list[int]] = {i: [] for i in range(8)}
        self.arm_motor_ids: dict[int, list[int]] = {i: [] for i in range(8)}

        n_segments = 4
        for arm_idx in range(8):
            angle = (arm_idx / 8.0) * 2.0 * np.pi
            ring_node_id = ring_ids[arm_idx]

            prev_axial_motor = None
            for seg in range(n_segments):
                dist = 2.5 + seg * 1.5
                ax_x = float(dist * np.cos(angle))
                ax_y = float(-0.4 * seg + self.rng.normal(0.0, 0.1))
                ax_z = float(dist * np.sin(angle))

                # Chemotactile sucker sensory receptor
                sensory_chemo = self._add_node(
                    label=f"Arm_{arm_idx}_Seg_{seg}_ChemoSens",
                    region=f"brachial_arm_{arm_idx}",
                    arm_index=arm_idx,
                    segment_index=seg,
                    category=NeuronCategory.SENSORY_CHEMO,
                    transmitter=Neurotransmitter.ACETYLCHOLINE,
                    pos=(ax_x + 0.2, ax_y - 0.2, ax_z + 0.2),
                )
                self.arm_sensory_ids[arm_idx].append(sensory_chemo)

                # Mechanoreceptor (proprioceptive muscle stretch)
                sensory_mech = self._add_node(
                    label=f"Arm_{arm_idx}_Seg_{seg}_MechanoSens",
                    region=f"brachial_arm_{arm_idx}",
                    arm_index=arm_idx,
                    segment_index=seg,
                    category=NeuronCategory.SENSORY_MECHANO,
                    transmitter=Neurotransmitter.ACETYLCHOLINE,
                    pos=(ax_x - 0.2, ax_y, ax_z - 0.2),
                )
                self.arm_sensory_ids[arm_idx].append(sensory_mech)

                # Local brachial interneuron (ganglionic reflex coordinator)
                inter_gang = self._add_node(
                    label=f"Arm_{arm_idx}_Seg_{seg}_Interganglion",
                    region=f"brachial_arm_{arm_idx}",
                    arm_index=arm_idx,
                    segment_index=seg,
                    category=NeuronCategory.INTER_RELAY,
                    transmitter=Neurotransmitter.GABA
                    if seg % 2 == 1
                    else Neurotransmitter.ACETYLCHOLINE,
                    pos=(ax_x, ax_y + 0.1, ax_z),
                )

                # Brachial axial motoneuron (actuates longitudinal & transverse hydrostats)
                motor_axial = self._add_node(
                    label=f"Arm_{arm_idx}_Seg_{seg}_AxialMotor",
                    region=f"brachial_arm_{arm_idx}",
                    arm_index=arm_idx,
                    segment_index=seg,
                    category=NeuronCategory.MOTOR_BRACHIAL,
                    transmitter=Neurotransmitter.ACETYLCHOLINE,
                    pos=(ax_x, ax_y - 0.1, ax_z),
                )
                self.arm_motor_ids[arm_idx].append(motor_axial)

                # Local reflex loop: Sensory -> Interganglion -> Motoneuron
                self._add_edge(sensory_chemo, inter_gang, synapse_count=3)
                self._add_edge(sensory_mech, inter_gang, synapse_count=3)
                self._add_edge(inter_gang, motor_axial, synapse_count=4)
                self._add_edge(sensory_mech, motor_axial, synapse_count=2)  # Monosynaptic reflex

                # Connect along the longitudinal axial cord
                if prev_axial_motor is not None:
                    self._add_edge(prev_axial_motor, motor_axial, synapse_count=3)
                    self._add_edge(motor_axial, prev_axial_motor, synapse_count=2)
                prev_axial_motor = motor_axial

                # Base segment connects to interbrachial nerve ring
                if seg == 0:
                    self._add_edge(motor_axial, ring_node_id, synapse_count=3)
                    self._add_edge(ring_node_id, motor_axial, synapse_count=3)

                # Connect sensory ascending pathways to Central Brain (SFL & Subesophageal)
                if seg < 2:
                    target_sfl = int(self.rng.choice(sfl_ids))
                    self._add_edge(sensory_chemo, target_sfl, synapse_count=2)

            # Subesophageal motor command descending tracts -> Arm axial motoneurons
            for sub_id in subesoph_ids[:4]:
                target_motor = self.arm_motor_ids[arm_idx][0]  # Base motoneuron
                self._add_edge(sub_id, target_motor, synapse_count=4)

    def get_adjacency_matrix(self) -> np.ndarray:
        """Returns the signed, weighted NxN synaptic connectivity matrix W_ij.

        Row i is the target neuron, Column j is the source neuron.
        W_ij = sign(j) * conductance_ns * synapse_count
        """
        n = len(self.nodes)
        w = np.zeros((n, n), dtype=np.float32)
        for edge in self.edges:
            w[edge.target_id, edge.source_id] += edge.sign * edge.conductance_ns
        return w

    def get_summary(self) -> dict[str, Any]:
        """Returns statistics of the connectome."""
        n_nodes = len(self.nodes)
        n_edges = len(self.edges)
        transmitters = {}
        for node in self.nodes:
            t = node.neurotransmitter.value
            transmitters[t] = transmitters.get(t, 0) + 1

        categories = {}
        for node in self.nodes:
            c = node.category.value
            categories[c] = categories.get(c, 0) + 1

        return {
            "total_neurons": n_nodes,
            "total_synaptic_edges": n_edges,
            "mean_synapses_per_neuron": round(n_edges / max(1, n_nodes), 2),
            "neurotransmitter_counts": transmitters,
            "neuron_category_counts": categories,
            "regions": list(self.region_node_ids.keys()),
        }

    def export_json(self, filepath: str) -> None:
        """Serializes the connectome graph to JSON for 3D visualizers and analysis."""
        data = {
            "metadata": {
                "species": "Octopus vulgaris (Computational Micro-Connectome)",
                "framework": "Google Connectomics / FlyWire Inspired Pipeline",
                "summary": self.get_summary(),
            },
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "region": node.region,
                    "arm_index": node.arm_index,
                    "segment_index": node.segment_index,
                    "category": node.category.value,
                    "neurotransmitter": node.neurotransmitter.value,
                    "sign": node.sign,
                    "position": list(node.position),
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "synapse_count": edge.synapse_count,
                    "conductance_ns": edge.conductance_ns,
                    "sign": edge.sign,
                    "type": edge.synapse_type,
                    "delay_ms": edge.conduction_delay_ms,
                }
                for edge in self.edges
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
