"""Whole-Brain 3D Cephalopod Atlas and Morphometric Density Field.

Defines the anatomical voxel atlas for an adult Octopus vulgaris (~500,000,000 neurons):
- Supraesophageal mass (Vertical Lobe, Superior Frontal, Subvertical, Peduncle, Buccal).
- Subesophageal mass (Anterior, Middle, Posterior Basal, Chromatophore motor centers).
- Bilateral Optic Lobes (Deep Retina, Medulla, Lobula).
- 8 Peripheral Brachial Axial Cords (Brachial Neuromeres & Sucker Ganglia).

Calibrated to histological cell counts and micro-CT volumes
(J.Z. Young 1971; Hochner 2012; Budelmann 1995; Packard 1972).
"""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class NeuropilLobeDefinition:
    """Quantitative definition of a brain lobe in the adult octopus."""

    id: str
    name: str
    parent_mass: str  # 'supraesophageal', 'subesophageal', 'optic', 'brachial_arm'
    volume_mm3: float
    neuron_count: int
    cell_density_per_mm3: float
    center_pos_mm: tuple[float, float, float]
    bounding_radius_mm: float
    primary_neurotransmitter: str
    is_plastic_associative: bool = False
    is_motor_command: bool = False


class AdultOctopusAtlas:
    """Adult Octopus vulgaris whole-brain anatomical morphometric atlas."""

    TOTAL_TARGET_NEURONS: int = 500_000_000

    def __init__(self):
        self.lobes: dict[str, NeuropilLobeDefinition] = {}
        self._build_atlas()

    def _build_atlas(self):
        # 1. SUPRAESOPHAGEAL MASS (~45,000,000 neurons, ~9% of total)
        # Vertical Lobe System (Amacrine parallel fibers for associative memory)
        self.lobes["vertical_lobe"] = NeuropilLobeDefinition(
            id="vertical_lobe",
            name="Vertical Lobe System (MSF/VL)",
            parent_mass="supraesophageal",
            volume_mm3=32.0,
            neuron_count=25_000_000,
            cell_density_per_mm3=781_250.0,
            center_pos_mm=(0.0, 3.2, 1.2),
            bounding_radius_mm=2.5,
            primary_neurotransmitter="acetylcholine",
            is_plastic_associative=True,
        )
        self.lobes["superior_frontal_lobe"] = NeuropilLobeDefinition(
            id="superior_frontal_lobe",
            name="Superior Frontal Lobe",
            parent_mass="supraesophageal",
            volume_mm3=8.0,
            neuron_count=2_500_000,
            cell_density_per_mm3=312_500.0,
            center_pos_mm=(0.0, 2.4, 0.7),
            bounding_radius_mm=1.5,
            primary_neurotransmitter="acetylcholine",
        )
        self.lobes["subvertical_lobe"] = NeuropilLobeDefinition(
            id="subvertical_lobe",
            name="Subvertical Lobe",
            parent_mass="supraesophageal",
            volume_mm3=6.5,
            neuron_count=2_000_000,
            cell_density_per_mm3=307_692.0,
            center_pos_mm=(0.0, 1.8, 0.4),
            bounding_radius_mm=1.3,
            primary_neurotransmitter="acetylcholine",
        )
        self.lobes["peduncle_lobes"] = NeuropilLobeDefinition(
            id="peduncle_lobes",
            name="Peduncle & Olfactory Lobe Complex",
            parent_mass="supraesophageal",
            volume_mm3=9.5,
            neuron_count=3_500_000,
            cell_density_per_mm3=368_421.0,
            center_pos_mm=(1.8, 2.0, 0.5),
            bounding_radius_mm=1.6,
            primary_neurotransmitter="dopamine",
        )
        self.lobes["buccal_mass_superior"] = NeuropilLobeDefinition(
            id="buccal_mass_superior",
            name="Superior Buccal Lobe",
            parent_mass="supraesophageal",
            volume_mm3=14.0,
            neuron_count=12_000_000,
            cell_density_per_mm3=857_142.0,
            center_pos_mm=(0.0, 1.2, -0.6),
            bounding_radius_mm=1.8,
            primary_neurotransmitter="glutamate",
        )

        # 2. SUBESOPHAGEAL MASS (~25,000,000 neurons, ~5% of total)
        # Motor coordination, chromatophore pattern generation, funneled jet propulsion
        self.lobes["anterior_basal_lobe"] = NeuropilLobeDefinition(
            id="anterior_basal_lobe",
            name="Anterior Basal Motor Lobe",
            parent_mass="subesophageal",
            volume_mm3=12.0,
            neuron_count=6_000_000,
            cell_density_per_mm3=500_000.0,
            center_pos_mm=(0.0, 0.5, -0.5),
            bounding_radius_mm=1.6,
            primary_neurotransmitter="acetylcholine",
            is_motor_command=True,
        )
        self.lobes["posterior_basal_lobe"] = NeuropilLobeDefinition(
            id="posterior_basal_lobe",
            name="Posterior Basal & Visceral Centers",
            parent_mass="subesophageal",
            volume_mm3=18.0,
            neuron_count=9_000_000,
            cell_density_per_mm3=500_000.0,
            center_pos_mm=(0.0, -0.6, -0.8),
            bounding_radius_mm=2.0,
            primary_neurotransmitter="acetylcholine",
            is_motor_command=True,
        )
        self.lobes["chromatophore_lobes"] = NeuropilLobeDefinition(
            id="chromatophore_lobes",
            name="Chromatophore Camouflage Motor Lobe",
            parent_mass="subesophageal",
            volume_mm3=15.0,
            neuron_count=10_000_000,
            cell_density_per_mm3=666_667.0,
            center_pos_mm=(0.0, 0.0, -1.2),
            bounding_radius_mm=1.8,
            primary_neurotransmitter="glutamate",
            is_motor_command=True,
        )

        # 3. BILATERAL OPTIC LOBES (~130,000,000 neurons, ~26% of total)
        # Massive visual processing centers: Deep retina, Medulla cortex, Lobula complex
        self.lobes["optic_lobe_left"] = NeuropilLobeDefinition(
            id="optic_lobe_left",
            name="Left Optic Lobe (Deep Retina + Medulla)",
            parent_mass="optic",
            volume_mm3=140.0,
            neuron_count=65_000_000,
            cell_density_per_mm3=464_286.0,
            center_pos_mm=(-4.5, 1.5, 0.0),
            bounding_radius_mm=4.0,
            primary_neurotransmitter="acetylcholine",
        )
        self.lobes["optic_lobe_right"] = NeuropilLobeDefinition(
            id="optic_lobe_right",
            name="Right Optic Lobe (Deep Retina + Medulla)",
            parent_mass="optic",
            volume_mm3=140.0,
            neuron_count=65_000_000,
            cell_density_per_mm3=464_286.0,
            center_pos_mm=(4.5, 1.5, 0.0),
            bounding_radius_mm=4.0,
            primary_neurotransmitter="acetylcholine",
        )

        # 4. DISTRIBUTED 8 BRACHIAL AXIAL CORDS (~300,000,000 neurons, ~60% of total)
        # Each arm contains ~37.5 million neurons partitioned into ~200-300 sucker neuromeres
        neurons_per_arm = 37_500_000
        vol_per_arm = 180.0
        for arm_idx in range(8):
            angle = (arm_idx / 8.0) * 2.0 * np.pi
            r_center = 7.0
            cx = float(r_center * np.cos(angle))
            cy = -1.0
            cz = float(r_center * np.sin(angle))

            self.lobes[f"brachial_arm_{arm_idx}"] = NeuropilLobeDefinition(
                id=f"brachial_arm_{arm_idx}",
                name=f"Arm #{arm_idx + 1} Brachial Axial Cord & Sucker Ganglia",
                parent_mass="brachial_arm",
                volume_mm3=vol_per_arm,
                neuron_count=neurons_per_arm,
                cell_density_per_mm3=float(neurons_per_arm / vol_per_arm),
                center_pos_mm=(cx, cy, cz),
                bounding_radius_mm=8.5,
                primary_neurotransmitter="acetylcholine",
                is_motor_command=True,
            )

    def get_summary(self) -> dict[str, Any]:
        """Calculates total brain metrics."""
        total_neurons = sum(l.neuron_count for l in self.lobes.values())
        total_vol = sum(l.volume_mm3 for l in self.lobes.values())

        by_mass = {}
        for l in self.lobes.values():
            by_mass[l.parent_mass] = by_mass.get(l.parent_mass, 0) + l.neuron_count

        return {
            "species": "Octopus vulgaris (Adult Cephalopod Full-Scale Blue Brain Atlas)",
            "total_neurons": total_neurons,
            "total_volume_mm3": round(total_vol, 1),
            "lobes_count": len(self.lobes),
            "neuron_distribution_by_mass": {
                "supraesophageal_mass": by_mass.get("supraesophageal", 0),
                "subesophageal_mass": by_mass.get("subesophageal", 0),
                "optic_lobes": by_mass.get("optic", 0),
                "brachial_arms_total": by_mass.get("brachial_arm", 0),
            },
            "central_to_peripheral_ratio": f"{round((by_mass.get('supraesophageal', 0) + by_mass.get('subesophageal', 0) + by_mass.get('optic', 0)) / total_neurons * 100, 1)}% Central vs {round(by_mass.get('brachial_arm', 0) / total_neurons * 100, 1)}% Peripheral",
        }
