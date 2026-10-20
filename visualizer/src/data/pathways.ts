/** Signal pathways and neural propagation sequences for live action potential tracing. */

export interface PathwayStep {
  regionId: string;
  label: string;
  description: string;
  durationMs: number;
  highlightColorHex: string;
  burstParticleCount: number;
  signalType: 'sensory' | 'interneuron' | 'associative' | 'motor' | 'reflex';
  armIndex?: number;
  startSegment?: number;
  endSegment?: number;
}

export interface NeuralPathway {
  id: string;
  title: string;
  shortDescription: string;
  scientificDescription: string;
  pathwayBadge: string;
  steps: PathwayStep[];
}

export const SIGNAL_PATHWAYS: Record<string, NeuralPathway> = {
  touch_sucker: {
    id: 'touch_sucker',
    title: 'Touch Sucker (Chemotactile Reflex + Ascending Relay)',
    shortDescription: 'Sucker Sensor → Local Sucker Ganglion → Axial Nerve Cord → Local Processing → Brachial/Brain Relay → Motor Response',
    scientificDescription: 'Chemotactile sensory cilia on the sucker rim activate local ganglion interneurons. A local reflex arc triggers immediate adhesion/grasping, while an ascending sensory volley travels along the axial nerve cord to the interbrachial ring and central subfrontal learning lobes.',
    pathwayBadge: 'Tactile-Motor Reflex Loop',
    steps: [
      {
        regionId: 'sucker_ganglia',
        label: '1. Sucker Sensory Receptors',
        description: 'Chemotactile receptors on sucker rim detect mechanical contact and chemical solutes.',
        durationMs: 450,
        highlightColorHex: '#f43f5e',
        burstParticleCount: 160,
        signalType: 'sensory',
        armIndex: 0,
        startSegment: 18,
        endSegment: 18,
      },
      {
        regionId: 'sucker_ganglia',
        label: '2. Local Sucker Neural Network',
        description: 'Intrinsic sucker ganglion computes local adhesion pressure and sphincter contraction.',
        durationMs: 500,
        highlightColorHex: '#fb7185',
        burstParticleCount: 180,
        signalType: 'interneuron',
        armIndex: 0,
        startSegment: 18,
        endSegment: 18,
      },
      {
        regionId: 'axial_nerve_cords',
        label: '3. Arm Axial Nerve Cord Neuropil',
        description: 'Signal enters segmental root into axial neuropil; computes local arm bend reflex.',
        durationMs: 750,
        highlightColorHex: '#38bdf8',
        burstParticleCount: 240,
        signalType: 'reflex',
        armIndex: 0,
        startSegment: 18,
        endSegment: 0,
      },
      {
        regionId: 'intramuscular_cords',
        label: '4. Intramuscular Muscle Activation',
        description: 'Local motoneurons recruit longitudinal and oblique muscle fibers to wrap prey.',
        durationMs: 600,
        highlightColorHex: '#a855f7',
        burstParticleCount: 200,
        signalType: 'motor',
        armIndex: 0,
        startSegment: 18,
        endSegment: 10,
      },
      {
        regionId: 'brachial_nerve_ring',
        label: '5. Interbrachial Commissural Ring',
        description: 'Ascending tactile message crosses the inter-arm nerve ring to alert neighbor arms.',
        durationMs: 650,
        highlightColorHex: '#00e5ff',
        burstParticleCount: 220,
        signalType: 'interneuron',
      },
      {
        regionId: 'subfrontal_lobe',
        label: '6. Subfrontal Central Brain Integration',
        description: 'Central brain receives chemotactile value signal, consolidating taste-by-touch memory.',
        durationMs: 750,
        highlightColorHex: '#e11d48',
        burstParticleCount: 260,
        signalType: 'associative',
      },
      {
        regionId: 'subesophageal_mass',
        label: '7. Subesophageal Motor Modulation',
        description: 'Central motor centers send descending bias to sustain prey ingestion posture.',
        durationMs: 650,
        highlightColorHex: '#10b981',
        burstParticleCount: 220,
        signalType: 'motor',
      },
    ],
  },

  visual_stimulus: {
    id: 'visual_stimulus',
    title: 'Visual Stimulation (Prey Detection → Arm Strike)',
    shortDescription: 'Eye → Optic Lobe → Central Processing → Behavioral Processing → Arm Network → Motor Response',
    scientificDescription: 'High-acuity retinal excitation is pre-processed across the multi-layered optic lobe cortex. Visual features (motion, contrast, polarization) project to the vertical lobe memory matrix and basal motor centers, triggering coordinated multi-arm strike commands.',
    pathwayBadge: 'Sensory-Associative-Executive Command',
    steps: [
      {
        regionId: 'optic_lobes',
        label: '1. Optic Lobe Visual Processing',
        description: 'Massive parallel feature extraction (motion, shape, polarization) in deep medullary cortex.',
        durationMs: 650,
        highlightColorHex: '#8b5cf6',
        burstParticleCount: 320,
        signalType: 'sensory',
      },
      {
        regionId: 'superior_frontal_lobe',
        label: '2. Superior Frontal Relay',
        description: 'Visual representations routed into associative learning circuits.',
        durationMs: 450,
        highlightColorHex: '#fbbf24',
        burstParticleCount: 200,
        signalType: 'interneuron',
      },
      {
        regionId: 'vertical_lobe',
        label: '3. Vertical Lobe Associative Memory',
        description: 'Associative recall: evaluates whether visual object is edible prey or threatening predator.',
        durationMs: 750,
        highlightColorHex: '#f59e0b',
        burstParticleCount: 380,
        signalType: 'associative',
      },
      {
        regionId: 'subesophageal_mass',
        label: '4. Subesophageal Executive Motor Command',
        description: 'Issues high-level command: "Deploy front arms (Arms 1 & 2) toward visual target coordinate".',
        durationMs: 650,
        highlightColorHex: '#10b981',
        burstParticleCount: 240,
        signalType: 'motor',
      },
      {
        regionId: 'brachial_nerve_ring',
        label: '5. Brachial Nerve Ring Dispatch',
        description: 'Executive command distributed along interbrachial commissures to recruited target arms.',
        durationMs: 550,
        highlightColorHex: '#00e5ff',
        burstParticleCount: 220,
        signalType: 'interneuron',
      },
      {
        regionId: 'axial_nerve_cords',
        label: '6. Arm Axial Nerve Cord Kinematic Generation',
        description: 'Target arms compute bend-propagation wave locally to extend toward prey.',
        durationMs: 850,
        highlightColorHex: '#38bdf8',
        burstParticleCount: 300,
        signalType: 'motor',
        armIndex: 0,
        startSegment: 0,
        endSegment: 27,
      },
      {
        regionId: 'intramuscular_cords',
        label: '7. Intramuscular Muscle Strike',
        description: 'Simultaneous longitudinal contraction and radial stiffening propels arm tip forward.',
        durationMs: 650,
        highlightColorHex: '#00f59b',
        burstParticleCount: 260,
        signalType: 'motor',
        armIndex: 0,
        startSegment: 12,
        endSegment: 27,
      },
    ],
  },

  arm_stimulation: {
    id: 'arm_stimulation',
    title: 'Autonomous Arm Tactile Reflex & Inter-Arm Handover',
    shortDescription: 'Arm Sensor → Local Arm Network → Local Processing → Other Arm/Brain Communication → Response',
    scientificDescription: 'A nociceptive or mechanical perturbation on Arm 3 generates a local withdrawal reflex computed entirely within the axial nerve cord neuropil, while transmitting lateral inhibitory/warning waves to Arms 2 and 4 via the interbrachial ring without waiting for central brain permission.',
    pathwayBadge: 'Decentralized Peripheral Coordination',
    steps: [
      {
        regionId: 'axial_nerve_cords',
        label: '1. Arm Sensory Receptors & Neuropil',
        description: 'Tactile strain receptors detect mechanical obstacle on arm mid-shaft.',
        durationMs: 500,
        highlightColorHex: '#38bdf8',
        burstParticleCount: 200,
        signalType: 'sensory',
        armIndex: 2,
        startSegment: 14,
        endSegment: 14,
      },
      {
        regionId: 'axial_nerve_cords',
        label: '2. Local Autonomous Processing',
        description: 'Axial cord interneuron ring computes rapid local withdrawal reflex loop.',
        durationMs: 550,
        highlightColorHex: '#0284c7',
        burstParticleCount: 240,
        signalType: 'reflex',
        armIndex: 2,
        startSegment: 14,
        endSegment: 8,
      },
      {
        regionId: 'intramuscular_cords',
        label: '3. Local Motor Retraction',
        description: 'Intramuscular longitudinal motor cords retract arm away from hazard.',
        durationMs: 500,
        highlightColorHex: '#a855f7',
        burstParticleCount: 200,
        signalType: 'motor',
        armIndex: 2,
        startSegment: 14,
        endSegment: 22,
      },
      {
        regionId: 'brachial_nerve_ring',
        label: '4. Inter-Arm Lateral Communication',
        description: 'Direct lateral message propagation across interbrachial commissures to adjacent arms.',
        durationMs: 650,
        highlightColorHex: '#00e5ff',
        burstParticleCount: 260,
        signalType: 'interneuron',
      },
      {
        regionId: 'axial_nerve_cords',
        label: '5. Adjacent Arm Cooperative Adjustment',
        description: 'Neighboring arms compensate posture and extend support tentacles.',
        durationMs: 750,
        highlightColorHex: '#10b981',
        burstParticleCount: 230,
        signalType: 'reflex',
        armIndex: 1,
        startSegment: 0,
        endSegment: 18,
      },
    ],
  },

  escape_jet: {
    id: 'escape_jet',
    title: 'High-Velocity Escape Jet & Statocyst Surge',
    shortDescription: 'Statocyst / Threat → Subesophageal Giant Motor Centers → Siphon & 8-Arm Coordinated Thrust',
    scientificDescription: 'High-threat sensory input directly triggers the giant fiber system in the subesophageal palliovisceral lobes, firing simultaneous descending motor volleys across all 8 arms for instant backward propulsion and funnel jetting.',
    pathwayBadge: 'Emergency Giant Fiber Discharge',
    steps: [
      {
        regionId: 'subesophageal_mass',
        label: '1. Statocyst & Giant Motor Activation',
        description: 'Threat triggers giant axon system within subesophageal motor centers.',
        durationMs: 400,
        highlightColorHex: '#ff3366',
        burstParticleCount: 300,
        signalType: 'sensory',
      },
      {
        regionId: 'brachial_nerve_ring',
        label: '2. Synchronous Interbrachial Dispatch',
        description: 'Simultaneous high-voltage discharge across all 8 brachial nerve roots.',
        durationMs: 450,
        highlightColorHex: '#f97316',
        burstParticleCount: 350,
        signalType: 'interneuron',
      },
      {
        regionId: 'axial_nerve_cords',
        label: '3. All 8 Arms Full-Length Kinematic Lock',
        description: 'Axial nerve cords stream synchronous action potentials from base to tips.',
        durationMs: 650,
        highlightColorHex: '#eab308',
        burstParticleCount: 450,
        signalType: 'motor',
        startSegment: 0,
        endSegment: 27,
      },
      {
        regionId: 'intramuscular_cords',
        label: '4. Full Neuromuscular Jet Thrust',
        description: 'Longitudinal musculature stiffens arms into a hydrodynamic cone for escape.',
        durationMs: 600,
        highlightColorHex: '#00f59b',
        burstParticleCount: 380,
        signalType: 'motor',
        startSegment: 0,
        endSegment: 27,
      },
    ],
  },
};

// Convenient Aliases for Story Tour
SIGNAL_PATHWAYS['visual_hunt'] = SIGNAL_PATHWAYS['visual_stimulus'];
SIGNAL_PATHWAYS['arm_tactile_transfer'] = SIGNAL_PATHWAYS['arm_stimulation'];
