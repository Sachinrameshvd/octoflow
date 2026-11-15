/** Procedural 3D Cephalopod Neuroanatomy and Connectome Synthesizer. */

import * as THREE from 'three';
import { NEUROANATOMY_REGIONS } from './neuroanatomy';

export interface NeuronNode {
  index: number;
  position: THREE.Vector3;
  regionId: string;
  armIndex: number; // -1 for central/optic, 0-7 for arms
  segmentIndex: number; // -1 for central, 0..N for arm suckers
  color: THREE.Color;
  size: number;
  type: 'soma' | 'ganglion_hub' | 'synaptic_bouton' | 'sucker_receptor' | 'corticoid' | 'interneuron' | 'motor_neuron';
  neighbors: number[]; // All adjacent node indices
  upstreamNeighbors: number[]; // Presynaptic input node indices
  downstreamNeighbors: number[]; // Postsynaptic output node indices
  incomingFiberIndices: number[]; // Fiber indices entering this node
  outgoingFiberIndices: number[]; // Fiber indices leaving this node
}

export interface NeuralFiber {
  index: number;
  sourceIndex: number;
  targetIndex: number;
  regionId: string;
  type: 'tract' | 'commissural' | 'dendritic' | 'segmental' | 'intramuscular' | 'afferent' | 'efferent';
  color: THREE.Color;
  synapticWeight: number; // 0.0 -> 1.0 (relative conductance / synaptic strength)
  direction: 'afferent' | 'efferent' | 'bidirectional';
  pathwayName: string;
  biologicalStatus: 'known' | 'inferred' | 'approx';
}

export interface OctopusConnectomeData {
  nodes: NeuronNode[];
  fibers: NeuralFiber[];
  regionNodeIndices: Record<string, number[]>;
  armNodeIndices: number[][]; // [armIndex] -> node indices
  fiberLinePositions: Float32Array;
  fiberLineColors: Float32Array;
  nodePositions: Float32Array;
  nodeColors: Float32Array;
  nodeSizes: Float32Array;
  nodePhases: Float32Array;
  punctaPositions: Float32Array;
  punctaColors: Float32Array;
}

export class OctopusConnectomeGenerator {
  private nodes: NeuronNode[] = [];
  private fibers: NeuralFiber[] = [];
  private regionNodeIndices: Record<string, number[]> = {};
  private armNodeIndices: number[][] = Array.from({ length: 8 }, () => []);
  private currentTintColor: THREE.Color | null = null;

  constructor() {
    for (const regionId in NEUROANATOMY_REGIONS) {
      this.regionNodeIndices[regionId] = [];
    }
  }

  public generate(neuronDensityScale: number = 1.0, tintColor?: THREE.Color): OctopusConnectomeData {
    this.currentTintColor = tintColor ? tintColor.clone() : null;
    this.nodes = [];
    this.fibers = [];
    for (const regionId in this.regionNodeIndices) {
      this.regionNodeIndices[regionId] = [];
    }
    this.armNodeIndices = Array.from({ length: 8 }, () => []);

    // 1. Generate Central Brain Masses (Supraesophageal & Subesophageal)
    this.generateCentralBrain(neuronDensityScale);

    // 2. Generate Massive Left & Right Optic Lobes
    this.generateOpticLobes(neuronDensityScale);

    // 3. Generate Interbrachial Nerve Ring
    this.generateInterbrachialRing(neuronDensityScale);

    // 4. Generate All 8 Distributed Arms with Axial Cords & Sucker Networks
    this.generateAllArms(neuronDensityScale);

    // 5. Synthesize Synaptic Fibers, Arborized Trees & Inter-regional Tracts
    this.synthesizeSynapticFibers();

    // 6. Build High-Performance Typed Buffer Arrays for GPU Shaders
    return this.buildBufferAttributes();
  }

  private addNode(
    pos: THREE.Vector3,
    regionId: string,
    armIndex: number = -1,
    segmentIndex: number = -1,
    type: NeuronNode['type'] = 'soma',
    sizeScale: number = 1.0
  ): number {
    const nodeIndex = this.nodes.length;
    const baseColorHex = NEUROANATOMY_REGIONS[regionId]?.colorHex || '#38bdf8';
    let color = new THREE.Color(baseColorHex);

    if (this.currentTintColor) {
      // Blend 72% signature tint with 28% anatomical region color for clear, vivid identity
      color = this.currentTintColor.clone().lerp(color, 0.28);
    }

    // Slight organic color variation
    color.offsetHSL(
      (Math.random() - 0.5) * 0.08,
      (Math.random() - 0.5) * 0.1,
      (Math.random() - 0.5) * 0.1
    );

    const node: NeuronNode = {
      index: nodeIndex,
      position: pos,
      regionId,
      armIndex,
      segmentIndex,
      color,
      size: (type === 'ganglion_hub' ? 3.5 : type === 'sucker_receptor' ? 2.2 : 1.6) * sizeScale,
      type,
      neighbors: [],
      upstreamNeighbors: [],
      downstreamNeighbors: [],
      incomingFiberIndices: [],
      outgoingFiberIndices: [],
    };

    this.nodes.push(node);
    if (this.regionNodeIndices[regionId]) {
      this.regionNodeIndices[regionId].push(nodeIndex);
    }
    if (armIndex >= 0 && armIndex < 8) {
      this.armNodeIndices[armIndex].push(nodeIndex);
    }

    return nodeIndex;
  }

  private addFiber(
    sourceIdx: number,
    targetIdx: number,
    regionId: string,
    type: NeuralFiber['type'],
    pathwayName?: string,
    direction: 'afferent' | 'efferent' | 'bidirectional' = 'bidirectional',
    biologicalStatus: 'known' | 'inferred' | 'approx' = 'approx'
  ) {
    const src = this.nodes[sourceIdx];
    const tgt = this.nodes[targetIdx];
    if (!src || !tgt) return;

    const fiberIndex = this.fibers.length;

    src.neighbors.push(targetIdx);
    tgt.neighbors.push(sourceIdx);

    if (direction === 'afferent' || direction === 'bidirectional') {
      src.downstreamNeighbors.push(targetIdx);
      tgt.upstreamNeighbors.push(sourceIdx);
      src.outgoingFiberIndices.push(fiberIndex);
      tgt.incomingFiberIndices.push(fiberIndex);
    }
    if (direction === 'efferent' || direction === 'bidirectional') {
      tgt.downstreamNeighbors.push(sourceIdx);
      src.upstreamNeighbors.push(targetIdx);
      tgt.outgoingFiberIndices.push(fiberIndex);
      src.incomingFiberIndices.push(fiberIndex);
    }

    const fiberColor = src.color.clone().lerp(tgt.color, 0.5);
    const weight = 0.5 + Math.random() * 0.48; // conductance 0.50 - 0.98

    const defaultPathway = pathwayName || (
      type === 'tract' ? 'Axial-Central Connective Tract' :
      type === 'commissural' ? 'Interbrachial Commissure Loop' :
      type === 'intramuscular' ? 'Neuromuscular Motor Pathway' :
      type === 'segmental' ? 'Sensory-Motor Segmental Reflex' :
      'Associative Neuropil Mesh'
    );

    this.fibers.push({
      index: fiberIndex,
      sourceIndex: sourceIdx,
      targetIndex: targetIdx,
      regionId,
      type,
      color: fiberColor,
      synapticWeight: weight,
      direction,
      pathwayName: defaultPathway,
      biologicalStatus,
    });
  }

  private generateCentralBrain(density: number) {
    // Esophagus passage ring at origin
    // Supraesophageal Mass (Y > 0)
    // 1. Vertical Lobe System (Top dorsal dome)
    const vlCount = Math.floor(1800 * density);
    for (let i = 0; i < vlCount; i++) {
      const u = Math.random();
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = Math.cbrt(u) * 6.5;

      // Elongated dorsal-vertical ellipsoid
      const x = r * Math.sin(phi) * Math.cos(theta) * 0.9;
      const y = r * Math.sin(phi) * Math.sin(theta) * 0.75 + 8.5; // Dorsal elevation
      const z = r * Math.cos(phi) * 1.1 + 1.5;

      const type = (i % 25 === 0) ? 'ganglion_hub' : 'soma';
      this.addNode(new THREE.Vector3(x, y, z), 'vertical_lobe', -1, -1, type, 1.2);
    }

    // 2. Superior Frontal Lobe (Anterior to Vertical Lobe)
    const sflCount = Math.floor(650 * density);
    for (let i = 0; i < sflCount; i++) {
      const r = Math.cbrt(Math.random()) * 4.2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      const x = r * Math.sin(phi) * Math.cos(theta) * 0.85;
      const y = r * Math.sin(phi) * Math.sin(theta) * 0.65 + 6.0;
      const z = r * Math.cos(phi) * 0.9 - 4.5; // Anterior offset

      this.addNode(new THREE.Vector3(x, y, z), 'superior_frontal_lobe', -1, -1, 'soma', 1.0);
    }

    // 3. Subfrontal Lobe & Inferior Frontal System (Tactile learning, below Superior Frontal)
    const subfCount = Math.floor(800 * density);
    for (let i = 0; i < subfCount; i++) {
      const r = Math.cbrt(Math.random()) * 4.8;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      const x = r * Math.sin(phi) * Math.cos(theta) * 0.9;
      const y = r * Math.sin(phi) * Math.sin(theta) * 0.6 + 2.5;
      const z = r * Math.cos(phi) * 0.85 - 5.5;

      this.addNode(new THREE.Vector3(x, y, z), 'subfrontal_lobe', -1, -1, 'soma', 1.1);
    }

    // Subesophageal Mass (Y < 0, Ventral to Esophagus)
    // Motor centers: Anterior Brachial centers + Posterior Palliovisceral
    const subCount = Math.floor(1600 * density);
    for (let i = 0; i < subCount; i++) {
      const u = Math.random();
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = Math.cbrt(u) * 7.5;

      const x = r * Math.sin(phi) * Math.cos(theta) * 1.1;
      const y = r * Math.sin(phi) * Math.sin(theta) * 0.65 - 4.5; // Ventral
      const z = r * Math.cos(phi) * 1.0;

      const type = (i % 20 === 0) ? 'ganglion_hub' : 'soma';
      this.addNode(new THREE.Vector3(x, y, z), 'subesophageal_mass', -1, -1, type, 1.3);
    }
  }

  private generateOpticLobes(density: number) {
    // Massive lateral lobes on Left (X = -20) and Right (X = +20)
    const sides = [-1, 1]; // Left (-1), Right (+1)
    const countPerLobe = Math.floor(2800 * density);

    for (const side of sides) {
      const centerX = side * 18.0;
      const centerY = 3.5;
      const centerZ = -0.5;

      for (let i = 0; i < countPerLobe; i++) {
        // Kidney bean / stratified visual cortex shape
        const u = Math.random();
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        const r = Math.cbrt(u) * 8.5;

        // Stratified cortex layers (outer granular layer vs inner deep medulla)
        const layerR = (i < countPerLobe * 0.6) ? r : (r * 0.6 + 3.0);
        const x = centerX + layerR * Math.sin(phi) * Math.cos(theta) * 0.95;
        const y = centerY + layerR * Math.sin(phi) * Math.sin(theta) * 1.25;
        const z = centerZ + layerR * Math.cos(phi) * 0.9;

        const type = (i % 30 === 0) ? 'ganglion_hub' : 'soma';
        this.addNode(new THREE.Vector3(x, y, z), 'optic_lobes', -1, -1, type, 1.15);
      }

      // Optic Tract nerve fibers bridging Optic Lobe to Central Brain
      const tractSteps = 12;
      for (let t = 0; t < 5; t++) {
        const start = new THREE.Vector3(centerX * 0.6, centerY + (t - 2) * 1.2, centerZ);
        const end = new THREE.Vector3(side * 4.5, 3.0 + (t - 2) * 0.8, 0);
        let prevIdx = -1;

        for (let s = 0; s <= tractSteps; s++) {
          const alpha = s / tractSteps;
          const pos = new THREE.Vector3().lerpVectors(start, end, alpha);
          pos.y += Math.sin(alpha * Math.PI) * 1.5;
          const idx = this.addNode(pos, 'optic_lobes', -1, -1, 'synaptic_bouton', 0.9);
          if (prevIdx !== -1) {
            this.addFiber(prevIdx, idx, 'optic_lobes', 'tract');
          }
          prevIdx = idx;
        }
      }
    }
  }

  private generateInterbrachialRing(density: number) {
    // Ring encircling the subesophageal base (radius ~ 13)
    const ringRadius = 13.0;
    const ringY = -5.0;
    const ringSteps = Math.floor(120 * density);

    let prevNodeIdx = -1;
    let firstNodeIdx = -1;

    for (let i = 0; i < ringSteps; i++) {
      const angle = (i / ringSteps) * Math.PI * 2;
      const x = ringRadius * Math.cos(angle);
      const z = ringRadius * Math.sin(angle);
      const y = ringY + Math.sin(angle * 4) * 0.8;

      const idx = this.addNode(
        new THREE.Vector3(x, y, z),
        'brachial_nerve_ring',
        -1,
        -1,
        (i % 15 === 0) ? 'ganglion_hub' : 'soma',
        1.2
      );

      if (i === 0) firstNodeIdx = idx;
      if (prevNodeIdx !== -1) {
        this.addFiber(prevNodeIdx, idx, 'brachial_nerve_ring', 'commissural');
      }
      prevNodeIdx = idx;
    }

    if (prevNodeIdx !== -1 && firstNodeIdx !== -1) {
      this.addFiber(prevNodeIdx, firstNodeIdx, 'brachial_nerve_ring', 'commissural');
    }
  }

  private generateAllArms(density: number) {
    const numArms = 8;
    const armAngles = Array.from({ length: 8 }, (_, i) => (i / 8) * Math.PI * 2);

    for (let armIdx = 0; armIdx < numArms; armIdx++) {
      const baseAngle = armAngles[armIdx];
      this.generateSingleArm(armIdx, baseAngle, density);
    }
  }

  private generateSingleArm(armIdx: number, baseAngle: number, density: number) {
    // Arm originates from interbrachial ring and sweeps outwards and downwards
    const ringRadius = 13.0;
    const startY = -5.5;

    // Spline control points for organic arm curvature
    const armLength = 55.0;
    const segmentsCount = 28; // Metameric sucker segments along arm
    const nodesPerSegment = Math.max(3, Math.floor(8 * density));

    const splinePoints: THREE.Vector3[] = [];
    const numCtrl = 6;
    for (let c = 0; c < numCtrl; c++) {
      const t = c / (numCtrl - 1);
      // Gentle spiral & outward flare
      const curveAngle = baseAngle + t * 0.45 * ((armIdx % 2 === 0) ? 1 : -1);
      const r = ringRadius + t * armLength * 0.9;
      const x = r * Math.cos(curveAngle);
      const z = r * Math.sin(curveAngle);
      const y = startY - t * (armLength * 0.45) + Math.sin(t * Math.PI) * 4.0;
      splinePoints.push(new THREE.Vector3(x, y, z));
    }

    const armCurve = new THREE.CatmullRomCurve3(splinePoints);
    let prevAxialCenterNode = -1;

    for (let seg = 0; seg < segmentsCount; seg++) {
      const t = seg / (segmentsCount - 1);
      const center = armCurve.getPoint(t);
      const tangent = armCurve.getTangent(t).normalize();
      const normal = new THREE.Vector3(0, 1, 0).cross(tangent).normalize();
      const binormal = tangent.clone().cross(normal).normalize();

      const segRadius = THREE.MathUtils.lerp(3.2, 0.8, t); // Tapering arm width

      // 1. Axial Nerve Cord (ANC) Center Neuropil Node
      const axialCenterNode = this.addNode(
        center.clone().add(new THREE.Vector3((Math.random() - 0.5) * 0.3, (Math.random() - 0.5) * 0.3, (Math.random() - 0.5) * 0.3)),
        'axial_nerve_cords',
        armIdx,
        seg,
        'ganglion_hub',
        1.4
      );

      if (prevAxialCenterNode !== -1) {
        this.addFiber(prevAxialCenterNode, axialCenterNode, 'axial_nerve_cords', 'tract');
      }
      prevAxialCenterNode = axialCenterNode;

      // 2. Axial Cortical Neurons surrounding the central neuropil
      for (let n = 0; n < nodesPerSegment; n++) {
        const theta = (n / nodesPerSegment) * Math.PI * 2;
        const rNeuropil = segRadius * 0.35;
        const offset = normal.clone().multiplyScalar(Math.cos(theta) * rNeuropil)
          .add(binormal.clone().multiplyScalar(Math.sin(theta) * rNeuropil));
        const nodePos = center.clone().add(offset);

        const ancNode = this.addNode(nodePos, 'axial_nerve_cords', armIdx, seg, 'soma', 1.0);
        this.addFiber(axialCenterNode, ancNode, 'axial_nerve_cords', 'segmental');
      }

      // 3. Sucker Micro-Ganglion & Chemotactile Sensory Rim (Ventral/Oral side)
      const oralOffset = normal.clone().multiplyScalar(-segRadius * 1.35); // Facing oral surface
      const suckerCenter = center.clone().add(oralOffset);

      // Sucker Ganglion Hub
      const suckerGanglion = this.addNode(
        suckerCenter,
        'sucker_ganglia',
        armIdx,
        seg,
        'ganglion_hub',
        1.5
      );

      // Sucker Nerve Connective: Axial Cord -> Sucker Ganglion
      this.addFiber(axialCenterNode, suckerGanglion, 'sucker_ganglia', 'segmental');

      // Chemosensory receptor rim around sucker
      const rimReceptorCount = Math.max(3, Math.floor(6 * density));
      const rimRadius = segRadius * 0.75;
      let prevRimNode = -1;
      let firstRimNode = -1;

      for (let r = 0; r < rimReceptorCount; r++) {
        const phi = (r / rimReceptorCount) * Math.PI * 2;
        const rimOffset = binormal.clone().multiplyScalar(Math.cos(phi) * rimRadius)
          .add(tangent.clone().multiplyScalar(Math.sin(phi) * rimRadius));
        const rimPos = suckerCenter.clone().add(rimOffset);

        const rimNode = this.addNode(rimPos, 'sucker_ganglia', armIdx, seg, 'sucker_receptor', 0.9);
        this.addFiber(suckerGanglion, rimNode, 'sucker_ganglia', 'segmental');

        if (r === 0) firstRimNode = rimNode;
        if (prevRimNode !== -1) {
          this.addFiber(prevRimNode, rimNode, 'sucker_ganglia', 'dendritic');
        }
        prevRimNode = rimNode;
      }
      if (prevRimNode !== -1 && firstRimNode !== -1) {
        this.addFiber(prevRimNode, firstRimNode, 'sucker_ganglia', 'dendritic');
      }

      // 4. 4 Longitudinal Intramuscular Nerve Cords (INCs) (2 Lateral, 2 Aboral)
      const incAngles = [0, Math.PI * 0.5, Math.PI, Math.PI * 1.5];
      for (const incAngle of incAngles) {
        const incOffset = normal.clone().multiplyScalar(Math.cos(incAngle) * segRadius * 0.95)
          .add(binormal.clone().multiplyScalar(Math.sin(incAngle) * segRadius * 0.95));
        const incPos = center.clone().add(incOffset);

        const incNode = this.addNode(incPos, 'intramuscular_cords', armIdx, seg, 'synaptic_bouton', 1.0);
        // Transverse motor branching to axial cord
        this.addFiber(axialCenterNode, incNode, 'intramuscular_cords', 'intramuscular');
      }
    }
  }

  private synthesizeSynapticFibers() {
    // Connect interbrachial ring nodes to nearest Subesophageal motor centers
    const subNodes = this.regionNodeIndices['subesophageal_mass'] || [];
    const ringNodes = this.regionNodeIndices['brachial_nerve_ring'] || [];
    const vlNodes = this.regionNodeIndices['vertical_lobe'] || [];
    const sflNodes = this.regionNodeIndices['superior_frontal_lobe'] || [];
    const subfNodes = this.regionNodeIndices['subfrontal_lobe'] || [];

    // Brachial ring -> Subesophageal motor roots
    if (subNodes.length > 0 && ringNodes.length > 0) {
      for (let i = 0; i < ringNodes.length; i += 6) {
        const ringIdx = ringNodes[i];
        const rPos = this.nodes[ringIdx].position;
        // Find nearest subesophageal node
        let bestSub = -1;
        let bestDist = Infinity;
        for (let j = 0; j < Math.min(60, subNodes.length); j++) {
          const subIdx = subNodes[j];
          const dist = rPos.distanceTo(this.nodes[subIdx].position);
          if (dist < bestDist) {
            bestDist = dist;
            bestSub = subIdx;
          }
        }
        if (bestSub !== -1) {
          this.addFiber(ringIdx, bestSub, 'brachial_nerve_ring', 'tract');
        }
      }
    }

    // Vertical Lobe <-> Superior Frontal <-> Subfrontal inter-lobe associative tracts
    this.bridgeRegions(sflNodes, vlNodes, 'vertical_lobe', 'dendritic', 45);
    this.bridgeRegions(subfNodes, sflNodes, 'subfrontal_lobe', 'dendritic', 35);
    this.bridgeRegions(vlNodes, subNodes, 'subesophageal_mass', 'tract', 30);
  }

  private bridgeRegions(
    groupA: number[],
    groupB: number[],
    regionId: string,
    type: NeuralFiber['type'],
    numConnections: number
  ) {
    if (groupA.length === 0 || groupB.length === 0) return;
    for (let c = 0; c < numConnections; c++) {
      const idxA = groupA[Math.floor(Math.random() * groupA.length)];
      const idxB = groupB[Math.floor(Math.random() * groupB.length)];
      this.addFiber(idxA, idxB, regionId, type);
    }
  }

  private buildBufferAttributes(): OctopusConnectomeData {
    const numNodes = this.nodes.length;
    const nodePositions = new Float32Array(numNodes * 3);
    const nodeColors = new Float32Array(numNodes * 3);
    const nodeSizes = new Float32Array(numNodes);
    const nodePhases = new Float32Array(numNodes);

    for (let i = 0; i < numNodes; i++) {
      const n = this.nodes[i];
      nodePositions[i * 3 + 0] = n.position.x;
      nodePositions[i * 3 + 1] = n.position.y;
      nodePositions[i * 3 + 2] = n.position.z;

      nodeColors[i * 3 + 0] = n.color.r;
      nodeColors[i * 3 + 1] = n.color.g;
      nodeColors[i * 3 + 2] = n.color.b;

      nodeSizes[i] = n.size;
      nodePhases[i] = Math.random() * Math.PI * 2;
    }

    // Line segments (2 vertices per fiber)
    const numFibers = this.fibers.length;
    const fiberLinePositions = new Float32Array(numFibers * 2 * 3);
    const fiberLineColors = new Float32Array(numFibers * 2 * 3);

    for (let f = 0; f < numFibers; f++) {
      const fiber = this.fibers[f];
      const src = this.nodes[fiber.sourceIndex];
      const tgt = this.nodes[fiber.targetIndex];

      const baseIdx = f * 6;
      // Vertex 1
      fiberLinePositions[baseIdx + 0] = src.position.x;
      fiberLinePositions[baseIdx + 1] = src.position.y;
      fiberLinePositions[baseIdx + 2] = src.position.z;

      fiberLineColors[baseIdx + 0] = src.color.r;
      fiberLineColors[baseIdx + 1] = src.color.g;
      fiberLineColors[baseIdx + 2] = src.color.b;

      // Vertex 2
      fiberLinePositions[baseIdx + 3] = tgt.position.x;
      fiberLinePositions[baseIdx + 4] = tgt.position.y;
      fiberLinePositions[baseIdx + 5] = tgt.position.z;

      fiberLineColors[baseIdx + 3] = tgt.color.r;
      fiberLineColors[baseIdx + 4] = tgt.color.g;
      fiberLineColors[baseIdx + 5] = tgt.color.b;
    }

    // Synaptic Puncta / Boutons (Google EM Connectome puncta dots)
    const numPuncta = numFibers;
    const punctaPositions = new Float32Array(numPuncta * 3);
    const punctaColors = new Float32Array(numPuncta * 3);

    for (let f = 0; f < numFibers; f++) {
      const fiber = this.fibers[f];
      const src = this.nodes[fiber.sourceIndex];
      const tgt = this.nodes[fiber.targetIndex];

      // Punctum placed near terminal (72% along axonal tract)
      const px = THREE.MathUtils.lerp(src.position.x, tgt.position.x, 0.72);
      const py = THREE.MathUtils.lerp(src.position.y, tgt.position.y, 0.72);
      const pz = THREE.MathUtils.lerp(src.position.z, tgt.position.z, 0.72);

      punctaPositions[f * 3 + 0] = px;
      punctaPositions[f * 3 + 1] = py;
      punctaPositions[f * 3 + 2] = pz;

      // Pure glowing white/gold puncta dot
      punctaColors[f * 3 + 0] = Math.min(1.0, tgt.color.r * 1.3 + 0.2);
      punctaColors[f * 3 + 1] = Math.min(1.0, tgt.color.g * 1.3 + 0.2);
      punctaColors[f * 3 + 2] = Math.min(1.0, tgt.color.b * 1.3 + 0.2);
    }

    return {
      nodes: this.nodes,
      fibers: this.fibers,
      regionNodeIndices: this.regionNodeIndices,
      armNodeIndices: this.armNodeIndices,
      nodePositions,
      nodeColors,
      nodeSizes,
      nodePhases,
      fiberLinePositions,
      fiberLineColors,
      punctaPositions,
      punctaColors,
    };
  }
}

