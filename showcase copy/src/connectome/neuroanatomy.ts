/** Neuroanatomy database for Octopus Nervous System 3D Connectome Visualizer. */

export interface BrainRegionInfo {
  id: string;
  name: string;
  systematicName: string;
  category: 'central_supra' | 'central_sub' | 'optic' | 'arm_axial' | 'sucker' | 'intramuscular' | 'commissure';
  categoryLabel: string;
  neuronCountEstimate: string;
  percentageOfNervousSystem: string;
  dataClassification: 'known' | 'inferred' | 'approximation';
  classificationLabel: string;
  disclaimer: string;
  biologicalRole: string;
  inputs: string[];
  outputs: string[];
  connectedRegions: string[];
  keyNeurotransmitters: string[];
  scientificReferences: string[];
  colorHex: string;
}

export const NEUROANATOMY_REGIONS: Record<string, BrainRegionInfo> = {
  // --- SUPRAESOPHAGEAL MASS ---
  vertical_lobe: {
    id: 'vertical_lobe',
    name: 'Vertical Lobe System (MSF/VL)',
    systematicName: 'Lobus verticalis massae supraoesophageae',
    category: 'central_supra',
    categoryLabel: 'Supraesophageal Brain (Associative / Learning)',
    neuronCountEstimate: '~25,000,000 neurons (highest central density)',
    percentageOfNervousSystem: '~5.0% of total nervous system (~50% of central brain)',
    dataClassification: 'known',
    classificationLabel: 'Known Biological Data (Histologically Characterized)',
    disclaimer: 'Gross morphology & synaptic layer organization are well-established (Young 1971; Hochner 2012). Micro-axonal branching visualized as computational approximation.',
    biologicalRole: 'Long-term memory acquisition, visual learning, and tactile-visual associative recall. Features an analog to vertebrate hippocampus/cerebellum with long-term potentiation (LTP) capability.',
    inputs: ['Superior Frontal Lobe', 'Subvertical Lobe', 'Optic Lobes via tractus opticus'],
    outputs: ['Subvertical Lobe', 'Lateral Basal Lobe', 'Subesophageal Motor Centers'],
    connectedRegions: ['superior_frontal_lobe', 'subvertical_lobe', 'optic_lobes'],
    keyNeurotransmitters: ['Glutamate', 'Acetylcholine', 'Octopamine', 'Dopamine'],
    scientificReferences: [
      'Young, J.Z. (1971) The Anatomy of the Nervous System of Octopus vulgaris.',
      'Hochner, B. (2012) An Embodied View of Octopus Neurobiology. Current Biology.',
      'Shomrat, T. et al. (2008) Long-term potentiation in the octopus vertical lobe. J. Neurophysiol.'
    ],
    colorHex: '#c084fc' // Fluorescent Neon Violet (FlyWire style)
  },

  superior_frontal_lobe: {
    id: 'superior_frontal_lobe',
    name: 'Superior Frontal Lobe',
    systematicName: 'Lobus frontalis superior',
    category: 'central_supra',
    categoryLabel: 'Supraesophageal Brain (Associative Relay)',
    neuronCountEstimate: '~2,000,000 neurons',
    percentageOfNervousSystem: '~0.4% of total nervous system',
    dataClassification: 'known',
    classificationLabel: 'Known Biological Data',
    disclaimer: 'Gross connections and tract topography mapped from Young (1971). Synapse cloud rendered via procedural density modeling.',
    biologicalRole: 'Primary sensory integration hub for visual and chemotactile afferents before transmission to the vertical lobe memory matrix.',
    inputs: ['Optic Lobes', 'Inferior Frontal System'],
    outputs: ['Vertical Lobe Amacrine Matrix'],
    connectedRegions: ['vertical_lobe', 'optic_lobes', 'subfrontal_lobe'],
    keyNeurotransmitters: ['Acetylcholine', 'Glutamate'],
    scientificReferences: ['Young, J.Z. (1971) Anatomy of Octopus Nervous System.'],
    colorHex: '#facc15' // Radiant Neon Gold
  },

  subfrontal_lobe: {
    id: 'subfrontal_lobe',
    name: 'Subfrontal & Inferior Frontal System',
    systematicName: 'Lobus subfrontalis et inferior frontalis',
    category: 'central_supra',
    categoryLabel: 'Supraesophageal Brain (Tactile Learning & Taste)',
    neuronCountEstimate: '~5,000,000 small interneurons',
    percentageOfNervousSystem: '~1.0% of total nervous system',
    dataClassification: 'known',
    classificationLabel: 'Known Biological Data',
    disclaimer: 'Known tactile learning center (chemotactile memory matrix analogous to vertical lobe). Micro-connectome approximated.',
    biologicalRole: 'Chemotactile memory and taste-by-touch discrimination. Receives afferent fibers from arm sucker receptors and mediates food reward associations.',
    inputs: ['Brachial Nerves from all 8 arms', 'Subesophageal Brachial Centers'],
    outputs: ['Superior Frontal Lobe', 'Posterior Buccal Ganglia'],
    connectedRegions: ['brachial_nerve_ring', 'subesophageal_mass', 'superior_frontal_lobe'],
    keyNeurotransmitters: ['Glutamate', 'Serotonin', 'FMRFamide'],
    scientificReferences: ['Wells, M.J. (1978) Octopus: Physiology and Behaviour of an Advanced Invertebrate.'],
    colorHex: '#f43f5e' // Radiant Crimson
  },

  // --- SUBESOPHAGEAL MASS ---
  subesophageal_mass: {
    id: 'subesophageal_mass',
    name: 'Subesophageal Motor Mass (Brachial / Palliovisceral)',
    systematicName: 'Massa suboesophagea (Lobi brachiales et magnocellularis)',
    category: 'central_sub',
    categoryLabel: 'Subesophageal Brain (Motor / Executive Control)',
    neuronCountEstimate: '~15,000,000 motor & intermediate neurons',
    percentageOfNervousSystem: '~3.0% of total nervous system',
    dataClassification: 'known',
    classificationLabel: 'Known Biological Data',
    disclaimer: 'Motor nuclei borders, brachial nerve roots, and giant fiber system are well established. Individual motoneuron arborizations are simulated.',
    biologicalRole: 'Executive motor coordination: sends high-level motor activation commands to arms, funnel, chromatophores, and mantle without computing local arm muscle kinematics.',
    inputs: ['Vertical Lobe System', 'Basal Lobes', 'Optic Lobes', 'Ascending Brachial Fibers'],
    outputs: ['8 Brachial Nerves to Arms', 'Stellate Ganglia (Mantle)', 'Funnel Nerves'],
    connectedRegions: ['vertical_lobe', 'brachial_nerve_ring', 'axial_nerve_cords'],
    keyNeurotransmitters: ['Acetylcholine', 'Glutamate', 'Dopamine', 'Noradrenaline'],
    scientificReferences: [
      'Budelmann, B.U. (1995) The Cephalopod Nervous System: Higher Motor Centers.',
      'Zullo, L. et al. (2009) Higher-order motor control in the octopus. J. Exp. Biol.'
    ],
    colorHex: '#3b82f6' // Electric Cobalt Blue
  },

  // --- OPTIC LOBES ---
  optic_lobes: {
    id: 'optic_lobes',
    name: 'Left & Right Optic Lobes (Visual Cortex)',
    systematicName: 'Lobi optici dextri et sinistri',
    category: 'optic',
    categoryLabel: 'Optic Lobes (Massive Visual Processing)',
    neuronCountEstimate: '~120,000,000 neurons (~60M per lobe; exceeds central brain!)',
    percentageOfNervousSystem: '~24.0% of total nervous system',
    dataClassification: 'known',
    classificationLabel: 'Known Biological Data (Stratified Deep Retina)',
    disclaimer: 'Outer granular, plexiform, and deep medullary zones are well documented. High-density connectome rendering is a computational approximation based on known layer thickness.',
    biologicalRole: 'Massive visual feature extraction (polarization vision, motion, shape, spatial contrast), camouflage pattern generation, and visual memory pre-processing.',
    inputs: ['Optic Nerves from Retinal Photoreceptors', 'Peduncle Lobe Feedback'],
    outputs: ['Optic Tracts to Supraesophageal and Subesophageal Masses'],
    connectedRegions: ['vertical_lobe', 'superior_frontal_lobe', 'subesophageal_mass'],
    keyNeurotransmitters: ['Acetylcholine', 'Dopamine', 'Octopamine', 'Histamine'],
    scientificReferences: [
      'Young, J.Z. (1962) The visual system of Octopus. Nature.',
      'Wang, Z.Y. et al. (2023) Single-cell transcriptomics of the octopus optic lobe.'
    ],
    colorHex: '#ec4899' // Radiant Magenta / Deep Retina Pink
  },

  // --- INTERBRACHIAL COMMISSURAL RING ---
  brachial_nerve_ring: {
    id: 'brachial_nerve_ring',
    name: 'Interbrachial Commissural Ring',
    systematicName: 'Commissura interbrachialis circularis',
    category: 'commissure',
    categoryLabel: 'Peripheral Inter-Arm Neural Highway',
    neuronCountEstimate: '~3,000,000 fibers & bridge interneurons',
    percentageOfNervousSystem: '~0.6% of total nervous system',
    dataClassification: 'known',
    classificationLabel: 'Known Biological Data',
    disclaimer: 'Circular commissure connecting adjacent and opposite arm bases. Tracts verified via neuro-tracing (Richter et al. 2015).',
    biologicalRole: 'Direct arm-to-arm lateral communication ring without central brain intervention. Enables traveling peristaltic waves, inter-arm cooperation, and reflex handovers.',
    inputs: ['Axial Nerve Cords of Arms 1 through 8', 'Subesophageal Brachial Nuclei'],
    outputs: ['Adjacent Arm Axial Nerve Cords (Left & Right Neighbors)'],
    connectedRegions: ['axial_nerve_cords', 'subesophageal_mass'],
    keyNeurotransmitters: ['Acetylcholine', 'Glutamate'],
    scientificReferences: ['Richter, S. et al. (2015) The peripheral nervous system of cephalopods. Front. Zool.'],
    colorHex: '#2dd4bf' // Radiant Turquoise/Teal
  },

  // --- AXIAL NERVE CORDS (ARMS 1-8) ---
  axial_nerve_cords: {
    id: 'axial_nerve_cords',
    name: 'Arm Axial Nerve Cords (8 Arms)',
    systematicName: 'Chorda nervosa axialis brachiorum I-VIII',
    category: 'arm_axial',
    categoryLabel: 'Arm Peripheral Brains (60% of Total Neurons!)',
    neuronCountEstimate: '~300,000,000 neurons (~35-40M per arm)',
    percentageOfNervousSystem: '~60.0% of total nervous system',
    dataClassification: 'known',
    classificationLabel: 'Known Biological Data (Central Neuropil + Cortical Ring)',
    disclaimer: 'Segmented ganglionic swellings, central neuropil core, and peripheral cell body rind are anatomically verified. Micro-synaptic wiring within the neuropil is a computational approximation.',
    biologicalRole: 'Autonomous peripheral motor computers. Computes high-degree-of-freedom muscle recruitment (elongation, bend, torsion, shortening) via muscular hydrostat kinematics locally without central trajectory planning.',
    inputs: ['Local Sucker Ganglia Sensory Afferents', 'Intramuscular Receptors', 'Subesophageal Motor Commands', 'Adjacent Arm Ring Messages'],
    outputs: ['Intramuscular Nerve Cords (Arm Muscles)', 'Sucker Ganglion Motor Sphincters', 'Ascending Tactile Afferents'],
    connectedRegions: ['sucker_ganglia', 'intramuscular_cords', 'brachial_nerve_ring', 'subesophageal_mass'],
    keyNeurotransmitters: ['Acetylcholine', 'Glutamate', '5-HT (Serotonin)', 'FMRFamide-related peptides', 'Octopamine'],
    scientificReferences: [
      'Gutfreund, Y. et al. (1996) Organization of muscle motor programs in octopus arms. J. Exp. Biol.',
      'Sumbre, G. et al. (2001) Control of octopus arm extension by a peripheral motor program. Science.',
      'Zullo, L. & Hochner, B. (2011) A new perspective on the organization of an invertebrate brain. Commun. Integr. Biol.'
    ],
    colorHex: '#38bdf8' // Electric Sky Cyan
  },

  // --- SUCKER GANGLIA & SENSORY NETWORKS ---
  sucker_ganglia: {
    id: 'sucker_ganglia',
    name: 'Sucker Ganglia & Chemotactile Networks',
    systematicName: 'Ganglia acetabulorum et plexus sensoria',
    category: 'sucker',
    categoryLabel: 'Sucker Micro-Ganglia (Taste-by-Touch & Adhesion)',
    neuronCountEstimate: '~40,000,000 neurons (~200 suckers/arm × ~25,000 neurons/sucker)',
    percentageOfNervousSystem: '~8.0% of total nervous system',
    dataClassification: 'known',
    classificationLabel: 'Known Biological Data (Ganglion Ring + Sensory Rim)',
    disclaimer: 'Sucker ganglion structure, rim sensory receptors, and intrinsic sphincter motor loops are biologically verified (Graziadei 1971; Allard et al. 2020). Micro-branching is procedurally rendered.',
    biologicalRole: 'Autonomous chemo-tactile sensing ("taste-by-touch" via contact chemoreceptors), pressure sensing, suction vacuum control, and local grasping reflexes.',
    inputs: ['Sucker Rim Chemosensory Cilia', 'Mechanical Strain Receptors'],
    outputs: ['Axial Nerve Cord Segmental Root', 'Sucker Sphincter/Meridian Muscles'],
    connectedRegions: ['axial_nerve_cords'],
    keyNeurotransmitters: ['Acetylcholine', 'Nicotinic receptors', 'Glutamate', 'Nitric Oxide'],
    scientificReferences: [
      'Graziadei, P. (1971) The nervous system of the arms of Octopus vulgaris.',
      'Allard, C.A.H. et al. (2020) Sensory specialization in the octopus sucker. Cell.'
    ],
    colorHex: '#10b981' // Radiant Neon Emerald
  },

  // --- INTRAMUSCULAR NERVE CORDS ---
  intramuscular_cords: {
    id: 'intramuscular_cords',
    name: 'Intramuscular Longitudinal Nerve Cords (4 per arm)',
    systematicName: 'Chordae nervosae intramusculares (4 per brachium)',
    category: 'intramuscular',
    categoryLabel: 'Muscular Hydrostat Motor Pathways',
    neuronCountEstimate: '~10,000,000 axons and peripheral motor terminals',
    percentageOfNervousSystem: '~2.0% of total nervous system',
    dataClassification: 'inferred',
    classificationLabel: 'Scientifically Inferred & Mapped Pathways',
    disclaimer: '4 longitudinal cords (2 lateral, 2 aboral) per arm running parallel to the axial cord. Branching motor arborizations into transverse/oblique muscle bundles are computational approximations.',
    biologicalRole: 'Fast conduction highways activating longitudinal, transverse, and helical/oblique arm muscles for stiffening waves, striking, and crawling.',
    inputs: ['Segmental Motor Roots from Axial Nerve Cord'],
    outputs: ['Longitudinal, Transverse, and Oblique Arm Muscle Fibers'],
    connectedRegions: ['axial_nerve_cords'],
    keyNeurotransmitters: ['Acetylcholine', 'Glutamate'],
    scientificReferences: ['Matzner, H. et al. (2000) Peripheral motor control in the octopus arm. J. Neurophysiol.'],
    colorHex: '#f59e0b' // Neon Amber
  }
};
