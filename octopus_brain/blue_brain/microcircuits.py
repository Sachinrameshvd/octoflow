"""Canonical Cephalopod Microcircuit Templates & Peter's Rule Synaptic Kernels.

Defines the repeating canonical microcircuits tiled across the adult octopus brain:
1. Vertical Lobe Associative Column:
   - SFL afferent -> Amacrine interneurons -> Large efferent neurons.
   - Dense feedforward cholinergic excitation + lateral GABAergic inhibition.
2. Brachial Sucker-Reflex Neuromere:
   - Chemotactile sensillae + mechanoreceptive proprioceptors -> Local interneuron
   - -> Longitudinal/Transverse axial motoneurons.
3. Optic Medulla Column:
   - Retinula afferent -> Transmedullary interneuron -> Tangential efferents.

Applies Peter's Rule: Structural proximity kernel P(d) = P_0 * exp(-d / lambda)
governing synaptic formation between overlapping axonal and dendritic arbors.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class MicrocircuitTemplate:
    """Canonical microcircuit template definition."""

    id: str
    lobe_id: str
    canonical_neuron_count: int
    cell_types: list[str]
    cell_type_proportions: dict[str, float]
    mean_synapses_per_cell: int
    receptive_field_radius_um: float
    decay_length_lambda_um: float
    base_connection_prob_p0: float


class CephalopodMicrocircuitLibrary:
    """Library of biological microcircuit templates for algorithmic connectomics."""

    def __init__(self):
        self.templates: dict[str, MicrocircuitTemplate] = {}
        self._build_templates()

    def _build_templates(self):
        # 1. Vertical Lobe Associative Microcircuit
        self.templates["vertical_lobe"] = MicrocircuitTemplate(
            id="vl_associative_column",
            lobe_id="vertical_lobe",
            canonical_neuron_count=1000,
            cell_types=["amacrine_fiber", "large_efferent", "gaba_interneuron"],
            cell_type_proportions={
                "amacrine_fiber": 0.94,
                "large_efferent": 0.04,
                "gaba_interneuron": 0.02,
            },
            mean_synapses_per_cell=180,
            receptive_field_radius_um=150.0,
            decay_length_lambda_um=65.0,
            base_connection_prob_p0=0.28,
        )

        # 2. Brachial Sucker Neuromere
        self.templates["brachial_neuromere"] = MicrocircuitTemplate(
            id="brachial_sucker_unit",
            lobe_id="brachial_arm",
            canonical_neuron_count=2500,
            cell_types=[
                "chemo_sensilla",
                "mechano_proprioceptor",
                "axial_motoneuron",
                "ganglionic_interneuron",
            ],
            cell_type_proportions={
                "chemo_sensilla": 0.50,
                "mechano_proprioceptor": 0.25,
                "axial_motoneuron": 0.15,
                "ganglionic_interneuron": 0.10,
            },
            mean_synapses_per_cell=95,
            receptive_field_radius_um=220.0,
            decay_length_lambda_um=80.0,
            base_connection_prob_p0=0.22,
        )

        # 3. Optic Medulla Column
        self.templates["optic_medulla"] = MicrocircuitTemplate(
            id="optic_medulla_column",
            lobe_id="optic",
            canonical_neuron_count=1500,
            cell_types=["retinula_afferent", "transmedullary_cell", "tangential_efferent"],
            cell_type_proportions={
                "retinula_afferent": 0.40,
                "transmedullary_cell": 0.50,
                "tangential_efferent": 0.10,
            },
            mean_synapses_per_cell=140,
            receptive_field_radius_um=180.0,
            decay_length_lambda_um=70.0,
            base_connection_prob_p0=0.25,
        )

    def calculate_connection_probability(self, template_id: str, distance_um: float) -> float:
        """Applies Peter's Rule: P(d) = P_0 * exp(-d / lambda)."""
        tmpl = self.templates.get(template_id)
        if tmpl is None:
            tmpl = self.templates["vertical_lobe"]

        if distance_um > tmpl.receptive_field_radius_um * 2.0:
            return 0.0

        p = tmpl.base_connection_prob_p0 * np.exp(
            -distance_um / max(1.0, tmpl.decay_length_lambda_um)
        )
        return float(np.clip(p, 0.0, 1.0))
