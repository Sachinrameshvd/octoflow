/** Signal Propagator & Action Potential Streaming Engine.
 * Simulates high-density traveling synaptic waves, directed axonal streams,
 * smooth anatomical tract flow, and living biological oscillations.
 */

import * as THREE from 'three';
import { SIGNAL_PATHWAYS } from '../data/pathways';
import type { NeuralPathway } from '../data/pathways';
import type { OctopusConnectomeData } from './octopus-generator';
import { ActionPotentialParticleShader } from './shaders';

interface ActionPotentialPacket {
  path: THREE.Vector3[];
  progress: number; // 0.0 -> 1.0
  speed: number;
  color: THREE.Color;
  life: number;
  numTrails: number;
  trailSpacing: number;
  isLoop?: boolean;
}

interface DendriticSpark {
  position: THREE.Vector3;
  target: THREE.Vector3;
  progress: number;
  speed: number;
  color: THREE.Color;
  life: number;
  hopsLeft: number;
  currentNodeIdx: number;
}

export class SignalPropagator {
  public group: THREE.Group;
  private connectome: OctopusConnectomeData;
  private activePackets: ActionPotentialPacket[] = [];
  private activeSparks: DendriticSpark[] = [];
  private maxParticles = 4000;

  private particlePositions: Float32Array;
  private particleColors: Float32Array;
  private particleLives: Float32Array;
  private particleGeometry: THREE.BufferGeometry;
  private particleMaterial: THREE.ShaderMaterial;
  private particlePoints: THREE.Points;

  // Active pathway tracking
  private currentPathway: NeuralPathway | null = null;
  private currentStepIndex: number = 0;
  private stepTimer: number = 0;
  private ambientTimer: number = 0;

  // Precomputed physiological tracks
  private armAxialTracks: THREE.Vector3[][] = []; // [armIdx] -> points from base (0) to tip (27)
  private armSuckerGangliaTracks: { [armSegKey: string]: THREE.Vector3[] } = {};
  private ringTrack: THREE.Vector3[] = [];
  private opticLeftTract: THREE.Vector3[] = [];
  private opticRightTract: THREE.Vector3[] = [];
  private brainAssociativeTracks: THREE.Vector3[][] = [];

  public onStepChange?: (stepIndex: number, stepLabel: string, description: string) => void;
  public onPathwayComplete?: () => void;

  // Wavefront shockwave uniforms for neuron flash
  public stimulusOrigin = new THREE.Vector3(0, 0, 0);
  public stimulusWaveRadius = 0.0;
  public stimulusIntensity = 0.0;
  public themeColor: THREE.Color | null = null;

  constructor(connectome: OctopusConnectomeData, themeColorHex?: string) {
    this.connectome = connectome;
    this.themeColor = themeColorHex ? new THREE.Color(themeColorHex) : null;
    this.group = new THREE.Group();

    this.particlePositions = new Float32Array(this.maxParticles * 3);
    this.particleColors = new Float32Array(this.maxParticles * 3);
    this.particleLives = new Float32Array(this.maxParticles);

    this.particleGeometry = new THREE.BufferGeometry();
    this.particleGeometry.setAttribute(
      'position',
      new THREE.BufferAttribute(this.particlePositions, 3)
    );
    this.particleGeometry.setAttribute(
      'aSignalColor',
      new THREE.BufferAttribute(this.particleColors, 3)
    );
    this.particleGeometry.setAttribute(
      'aLife',
      new THREE.BufferAttribute(this.particleLives, 1)
    );

    this.particleMaterial = new THREE.ShaderMaterial({
      vertexShader: ActionPotentialParticleShader.vertexShader,
      fragmentShader: ActionPotentialParticleShader.fragmentShader,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    this.particlePoints = new THREE.Points(this.particleGeometry, this.particleMaterial);
    this.group.add(this.particlePoints);

    this.extractAnatomicalTracks();
    this.initAmbientCirculation();
  }

  public triggerSpontaneousActivity() {
    const randomArm = Math.floor(Math.random() * 8);
    const color = this.themeColor ? `#${this.themeColor.getHexString()}` : '#38bdf8';
    this.triggerArmAxialStream(randomArm, false, color);
  }

  public triggerArmCascade(_burstCount: number = 80) {
    const color = this.themeColor ? `#${this.themeColor.getHexString()}` : '#38bdf8';
    for (let a = 0; a < 8; a++) {
      this.triggerArmAxialStream(a, false, color);
    }
  }

  private extractAnatomicalTracks() {
    // 1. Extract 8 Arm Axial Cord sequences (Base -> Tip)
    this.armAxialTracks = Array.from({ length: 8 }, () => []);
    for (let a = 0; a < 8; a++) {
      const armNodes = this.connectome.armNodeIndices[a] || [];
      // Group by segment and pick axial center hubs
      const segMap: { [seg: number]: THREE.Vector3 } = {};
      for (const idx of armNodes) {
        const node = this.connectome.nodes[idx];
        if (node.regionId === 'axial_nerve_cords' && node.type === 'ganglion_hub') {
          segMap[node.segmentIndex] = node.position;
        }
      }
      const segKeys = Object.keys(segMap).map(Number).sort((x, y) => x - y);
      for (const k of segKeys) {
        this.armAxialTracks[a].push(segMap[k]);
      }
    }

    // 2. Extract Sucker reflex tracks: Sucker rim -> Sucker ganglion -> Axial cord -> Intramuscular
    for (let a = 0; a < 8; a++) {
      const armNodes = this.connectome.armNodeIndices[a] || [];
      const segGroups: { [seg: number]: { rim?: THREE.Vector3; ganglion?: THREE.Vector3; anc?: THREE.Vector3; inc?: THREE.Vector3 } } = {};
      for (const idx of armNodes) {
        const node = this.connectome.nodes[idx];
        if (!segGroups[node.segmentIndex]) segGroups[node.segmentIndex] = {};
        const g = segGroups[node.segmentIndex];
        if (node.regionId === 'sucker_ganglia' && node.type === 'sucker_receptor' && !g.rim) {
          g.rim = node.position;
        } else if (node.regionId === 'sucker_ganglia' && node.type === 'ganglion_hub') {
          g.ganglion = node.position;
        } else if (node.regionId === 'axial_nerve_cords' && node.type === 'ganglion_hub') {
          g.anc = node.position;
        } else if (node.regionId === 'intramuscular_cords' && !g.inc) {
          g.inc = node.position;
        }
      }
      for (const seg in segGroups) {
        const g = segGroups[seg];
        if (g.rim && g.ganglion && g.anc) {
          const track = [g.rim, g.ganglion, g.anc];
          if (g.inc) track.push(g.inc);
          this.armSuckerGangliaTracks[`${a}_${seg}`] = track;
        }
      }
    }

    // 3. Extract Interbrachial Nerve Ring circular track
    const ringIndices = this.connectome.regionNodeIndices['brachial_nerve_ring'] || [];
    const ringPositions = ringIndices.map((idx) => this.connectome.nodes[idx].position);
    // Sort around origin by angle
    this.ringTrack = ringPositions.sort((p1, p2) => Math.atan2(p1.z, p1.x) - Math.atan2(p2.z, p2.x));

    // 4. Extract Optic Tracts (Left/Right cortex -> Optic Tract -> Superior Frontal -> Vertical Lobe)
    const opticIndices = this.connectome.regionNodeIndices['optic_lobes'] || [];
    const leftOpticNodes = opticIndices.filter((idx) => this.connectome.nodes[idx].position.x < -10);
    const rightOpticNodes = opticIndices.filter((idx) => this.connectome.nodes[idx].position.x > 10);
    const sflNodes = this.connectome.regionNodeIndices['superior_frontal_lobe'] || [];
    const vlNodes = this.connectome.regionNodeIndices['vertical_lobe'] || [];
    const subNodes = this.connectome.regionNodeIndices['subesophageal_mass'] || [];

    if (leftOpticNodes.length > 0 && sflNodes.length > 0 && vlNodes.length > 0) {
      this.opticLeftTract = [
        this.connectome.nodes[leftOpticNodes[0]].position,
        new THREE.Vector3(-10, 3.5, 0),
        new THREE.Vector3(-4, 4.5, -2),
        this.connectome.nodes[sflNodes[0]].position,
        this.connectome.nodes[vlNodes[0]].position,
      ];
    }
    if (rightOpticNodes.length > 0 && sflNodes.length > 0 && vlNodes.length > 0) {
      this.opticRightTract = [
        this.connectome.nodes[rightOpticNodes[0]].position,
        new THREE.Vector3(10, 3.5, 0),
        new THREE.Vector3(4, 4.5, -2),
        this.connectome.nodes[sflNodes[0]].position,
        this.connectome.nodes[vlNodes[0]].position,
      ];
    }

    // 5. Associative central tracks
    if (vlNodes.length > 0 && subNodes.length > 0) {
      for (let i = 0; i < 6; i++) {
        const vl = this.connectome.nodes[vlNodes[Math.floor(Math.random() * vlNodes.length)]].position;
        const sub = this.connectome.nodes[subNodes[Math.floor(Math.random() * subNodes.length)]].position;
        this.brainAssociativeTracks.push([vl, new THREE.Vector3(vl.x * 0.5, 0, vl.z * 0.5), sub]);
      }
    }
  }

  private initAmbientCirculation() {
    // Spawn baseline circulating pulses along the ring (rhythmic resting brainwaves)
    const c1 = this.themeColor ? `#${this.themeColor.getHexString()}` : '#38bdf8';
    const c2 = this.themeColor ? `#${this.themeColor.clone().offsetHSL(0.08, 0, 0.1).getHexString()}` : '#00f59b';
    if (this.ringTrack.length > 3) {
      this.spawnRingPacket(c1, 0.16, true, 0.0);
      this.spawnRingPacket(c2, 0.16, true, 0.5);
    }
  }

  public getLeadPulsePosition(): THREE.Vector3 | null {
    if (this.activePackets.length > 0) {
      const p = this.activePackets[0];
      return this.interpolateTrack(p.path, p.progress);
    }
    if (this.activeSparks.length > 0) {
      return this.activeSparks[0].position;
    }
    return null;
  }

  public triggerPathway(pathwayId: string) {
    const pathway = SIGNAL_PATHWAYS[pathwayId];
    if (!pathway) return;

    this.currentPathway = pathway;
    this.currentStepIndex = 0;
    this.stepTimer = 0;

    this.executeCurrentStep();
  }

  public triggerArmAxialStream(armIndex: number, ascending: boolean = true, colorHex: string = '#89b4fa') {
    if (armIndex < 0 || armIndex >= 8) return;
    const track = this.armAxialTracks[armIndex];
    if (track && track.length > 2) {
      const pts = ascending ? [...track].reverse() : track;
      this.spawnStream(pts, colorHex, 2.2, 8, 0.04);
    }
  }

  public triggerLateralRingPulse(armA: number, armB: number, colorHex: string = '#cba6f7') {
    const startProgressA = (armA / 8.0) % 1.0;
    const startProgressB = (armB / 8.0) % 1.0;
    this.spawnRingPacket(colorHex, 0.8, false, startProgressA);
    this.spawnRingPacket(colorHex, 0.8, false, startProgressB);
  }

  public triggerSingleFiberStimulus(fiberIndex: number, colorHex: string = '#facc15') {
    if (fiberIndex < 0 || fiberIndex >= this.connectome.fibers.length) return;
    const fiber = this.connectome.fibers[fiberIndex];
    const srcNode = this.connectome.nodes[fiber.sourceIndex];
    const tgtNode = this.connectome.nodes[fiber.targetIndex];

    this.stimulusOrigin.copy(srcNode.position);
    this.stimulusWaveRadius = 0.1;
    this.stimulusIntensity = 1.6;

    // Stream 3 consecutive glowing packets along the fiber line
    this.spawnStream([srcNode.position, tgtNode.position], colorHex, 2.5, 6, 0.06);
  }

  public triggerNeuronMicrocircuitCascade(nodeIndex: number, burstCount: number = 30) {
    const node = this.connectome.nodes[nodeIndex];
    if (!node) return;

    this.stimulusOrigin.copy(node.position);
    this.stimulusWaveRadius = 0.2;
    this.stimulusIntensity = 1.8;

    const downstream = node.downstreamNeighbors.length > 0 ? node.downstreamNeighbors : node.neighbors;
    if (downstream.length === 0) return;

    const colorHex = node.regionId === 'vertical_lobe' ? '#f59e0b' : (node.regionId === 'optic_lobes' ? '#8b5cf6' : '#38bdf8');

    for (let b = 0; b < Math.min(burstCount, downstream.length * 4); b++) {
      const tgtIdx = downstream[b % downstream.length];
      const tgtNode = this.connectome.nodes[tgtIdx];
      this.spawnSpark(node.position, tgtNode.position, tgtIdx, colorHex, 4);
    }
  }

  public triggerNodeStimulus(nodeIndex: number, burstCount: number = 35) {
    this.triggerNeuronMicrocircuitCascade(nodeIndex, burstCount);
  }

  private executeCurrentStep() {
    if (!this.currentPathway) return;
    const step = this.currentPathway.steps[this.currentStepIndex];
    if (!step) return;

    const pathwayId = this.currentPathway.id;
    const colorHex = step.highlightColorHex;

    // 1. Anatomical directed signal execution based on pathway & step
    if (pathwayId === 'touch_sucker') {
      const armIdx = step.armIndex ?? 0;
      const segIdx = step.startSegment ?? 18;

      if (step.regionId === 'sucker_ganglia') {
        const track = this.armSuckerGangliaTracks[`${armIdx}_${segIdx}`];
        if (track) {
          this.spawnStream(track, colorHex, 1.8, 8, 0.05);
          this.stimulusOrigin.copy(track[0]);
          this.stimulusWaveRadius = 0.2;
          this.stimulusIntensity = 1.8;
        }
      } else if (step.regionId === 'axial_nerve_cords') {
        // Ascending volley along axial cord (Segment 18 -> 0 base)
        const fullTrack = this.armAxialTracks[armIdx];
        if (fullTrack && fullTrack.length > 0) {
          const subTrack = fullTrack.slice(0, Math.min(segIdx + 1, fullTrack.length)).reverse();
          this.spawnStream(subTrack, colorHex, 1.4, 10, 0.04);
          if (subTrack.length > 0) this.stimulusOrigin.copy(subTrack[0]);
          this.stimulusIntensity = 1.5;
        }
      } else if (step.regionId === 'intramuscular_cords') {
        // Local intramuscular motor activation
        const armNodes = this.connectome.armNodeIndices[armIdx] || [];
        const incNodes = armNodes.filter((i) => this.connectome.nodes[i].regionId === 'intramuscular_cords');
        for (let i = 0; i < Math.min(8, incNodes.length); i++) {
          const n = this.connectome.nodes[incNodes[i]];
          if (n.neighbors.length > 0) {
            const tgt = this.connectome.nodes[n.neighbors[0]];
            this.spawnStream([n.position, tgt.position], colorHex, 2.2, 5, 0.06);
          }
        }
      } else if (step.regionId === 'brachial_nerve_ring') {
        // Split wave around interbrachial ring
        this.spawnRingPacket(colorHex, 0.6, false, 0.0);
        this.spawnRingPacket(colorHex, 0.6, false, 0.5);
      } else if (step.regionId === 'subfrontal_lobe' || step.regionId === 'subesophageal_mass') {
        // Feed into central brain lobes
        for (const track of this.brainAssociativeTracks) {
          this.spawnStream(track, colorHex, 1.8, 6, 0.06);
        }
      }
    } else if (pathwayId === 'visual_stimulus' || pathwayId === 'visual_hunt') {
      if (step.regionId === 'optic_lobes') {
        if (this.opticLeftTract.length > 0) this.spawnStream(this.opticLeftTract, colorHex, 1.2, 10, 0.04);
        if (this.opticRightTract.length > 0) this.spawnStream(this.opticRightTract, colorHex, 1.2, 10, 0.04);
        this.stimulusOrigin.set(-18, 3.5, 0);
        this.stimulusWaveRadius = 0.5;
        this.stimulusIntensity = 1.8;
      } else if (step.regionId === 'superior_frontal_lobe' || step.regionId === 'vertical_lobe') {
        // Vertical Lobe memory explosion
        const vlIndices = this.connectome.regionNodeIndices['vertical_lobe'] || [];
        for (let i = 0; i < 8; i++) {
          const srcIdx = vlIndices[Math.floor(Math.random() * vlIndices.length)];
          const node = this.connectome.nodes[srcIdx];
          if (node.neighbors.length > 0) {
            const tgt = this.connectome.nodes[node.neighbors[0]];
            this.spawnStream([node.position, tgt.position], colorHex, 2.0, 6, 0.05);
          }
        }
        this.stimulusOrigin.set(0, 8.5, 1.5);
        this.stimulusWaveRadius = 0.5;
        this.stimulusIntensity = 2.0;
      } else if (step.regionId === 'subesophageal_mass') {
        // Executive motor commands discharging to ring
        for (const track of this.brainAssociativeTracks) {
          this.spawnStream(track, colorHex, 1.8, 8, 0.04);
        }
      } else if (step.regionId === 'brachial_nerve_ring') {
        this.spawnRingPacket(colorHex, 0.7, false, 0.0);
      } else if (step.regionId === 'axial_nerve_cords') {
        // Descending strike pulses along front arms (Arms 0 and 1)
        if (this.armAxialTracks[0]) this.spawnStream(this.armAxialTracks[0], colorHex, 1.4, 12, 0.03);
        if (this.armAxialTracks[1]) this.spawnStream(this.armAxialTracks[1], colorHex, 1.4, 12, 0.03);
      } else if (step.regionId === 'intramuscular_cords') {
        if (this.armAxialTracks[0]) this.spawnStream(this.armAxialTracks[0].slice(12), colorHex, 2.0, 10, 0.04);
        if (this.armAxialTracks[1]) this.spawnStream(this.armAxialTracks[1].slice(12), colorHex, 2.0, 10, 0.04);
      }
    } else if (pathwayId === 'arm_stimulation' || pathwayId === 'arm_tactile_transfer') {
      const armIdx = step.armIndex ?? 2;
      if (step.regionId === 'axial_nerve_cords') {
        const fullTrack = this.armAxialTracks[armIdx];
        if (fullTrack) {
          const subTrack = step.startSegment !== undefined && step.endSegment !== undefined
            ? (step.startSegment < step.endSegment ? fullTrack.slice(step.startSegment, step.endSegment + 1) : fullTrack.slice(step.endSegment, step.startSegment + 1).reverse())
            : fullTrack;
          this.spawnStream(subTrack, colorHex, 1.5, 8, 0.04);
        }
      } else if (step.regionId === 'intramuscular_cords') {
        const fullTrack = this.armAxialTracks[armIdx];
        if (fullTrack) this.spawnStream(fullTrack.slice(10, 24), colorHex, 2.0, 8, 0.05);
      } else if (step.regionId === 'brachial_nerve_ring') {
        this.spawnRingPacket(colorHex, 0.65, false, 0.25);
      }
    } else if (pathwayId === 'escape_jet') {
      if (step.regionId === 'subesophageal_mass') {
        this.stimulusOrigin.set(0, -4.5, 0);
        this.stimulusWaveRadius = 0.5;
        this.stimulusIntensity = 2.4;
      } else if (step.regionId === 'brachial_nerve_ring') {
        this.spawnRingPacket(colorHex, 0.9, false, 0.0);
        this.spawnRingPacket(colorHex, 0.9, false, 0.5);
      } else if (step.regionId === 'axial_nerve_cords' || step.regionId === 'intramuscular_cords') {
        // Synchronous massive discharge down ALL 8 ARMS simultaneously
        for (let a = 0; a < 8; a++) {
          if (this.armAxialTracks[a] && this.armAxialTracks[a].length > 0) {
            this.spawnStream(this.armAxialTracks[a], colorHex, 1.6, 12, 0.03);
          }
        }
      }
    } else {
      // General fallback
      const regionNodes = this.connectome.regionNodeIndices[step.regionId] || [];
      if (regionNodes.length > 0) {
        for (let s = 0; s < Math.min(10, regionNodes.length); s++) {
          const srcIdx = regionNodes[s];
          const srcNode = this.connectome.nodes[srcIdx];
          if (srcNode.neighbors.length > 0) {
            const tgtNode = this.connectome.nodes[srcNode.neighbors[0]];
            this.spawnStream([srcNode.position, tgtNode.position], colorHex, 2.0, 5, 0.06);
          }
        }
      }
    }

    if (this.onStepChange) {
      this.onStepChange(this.currentStepIndex, step.label, step.description);
    }
  }

  public spawnStream(
    points: THREE.Vector3[],
    colorHex: string,
    speed: number = 1.5,
    numTrails: number = 8,
    trailSpacing: number = 0.04
  ) {
    if (points.length < 2) return;
    this.activePackets.push({
      path: points.map((p) => p.clone()),
      progress: 0.0,
      speed,
      color: new THREE.Color(colorHex),
      life: 1.0,
      numTrails,
      trailSpacing,
      isLoop: false,
    });
  }

  private spawnRingPacket(colorHex: string, speed: number = 0.25, isLoop: boolean = false, startProgress: number = 0.0) {
    if (this.ringTrack.length < 3) return;
    this.activePackets.push({
      path: this.ringTrack.map((p) => p.clone()),
      progress: startProgress,
      speed,
      color: new THREE.Color(colorHex),
      life: 1.0,
      numTrails: 8,
      trailSpacing: 0.025,
      isLoop,
    });
  }

  private spawnSpark(
    srcPos: THREE.Vector3,
    tgtPos: THREE.Vector3,
    tgtIdx: number,
    colorHex: string,
    hops: number
  ) {
    if (this.activeSparks.length > 400) return;
    this.activeSparks.push({
      position: srcPos.clone(),
      target: tgtPos.clone(),
      progress: 0.0,
      speed: 2.5 + Math.random() * 1.5,
      color: new THREE.Color(colorHex),
      life: 1.0,
      hopsLeft: hops,
      currentNodeIdx: tgtIdx,
    });
  }

  public update(deltaTime: number, speedMultiplier: number = 1.0) {
    const dt = deltaTime * speedMultiplier;

    // 0. Ambient living nervous system pulses (gentle rhythmic biological field)
    this.ambientTimer += dt;
    if (this.ambientTimer > 1.8) {
      this.ambientTimer = 0;
      // Spawn gentle pulse on a random arm axial cord
      const randArm = Math.floor(Math.random() * 8);
      const armTrack = this.armAxialTracks[randArm];
      if (armTrack && armTrack.length > 4) {
        const isAscending = Math.random() > 0.5;
        const pts = isAscending ? [...armTrack].reverse() : armTrack;
        const colorHex = isAscending ? '#38bdf8' : '#00f59b';
        this.spawnStream(pts, colorHex, 0.45, 6, 0.035);
      }
    }

    // 1. Advance Pathway Sequence
    if (this.currentPathway) {
      const step = this.currentPathway.steps[this.currentStepIndex];
      this.stepTimer += dt * 1000;
      if (this.stepTimer >= step.durationMs) {
        this.stepTimer = 0;
        this.currentStepIndex++;
        if (this.currentStepIndex < this.currentPathway.steps.length) {
          this.executeCurrentStep();
        } else {
          this.currentPathway = null;
          if (this.onPathwayComplete) this.onPathwayComplete();
        }
      }
    }

    // 2. Expand stimulus shockwave radius
    if (this.stimulusIntensity > 0.01) {
      this.stimulusWaveRadius += dt * 38.0;
      this.stimulusIntensity = Math.max(0.0, this.stimulusIntensity - dt * 1.5);
    }

    // 3. Update Directed Stream Packets
    const remainingPackets: ActionPotentialPacket[] = [];
    for (let i = 0; i < this.activePackets.length; i++) {
      const p = this.activePackets[i];
      p.progress += dt * p.speed * 0.5;

      if (p.isLoop) {
        if (p.progress >= 1.0) p.progress -= 1.0;
        remainingPackets.push(p);
      } else {
        if (p.progress < 1.0) {
          remainingPackets.push(p);
        }
      }
    }
    this.activePackets = remainingPackets;

    // 4. Update Dendritic Sparks
    const remainingSparks: DendriticSpark[] = [];
    for (let i = 0; i < this.activeSparks.length; i++) {
      const s = this.activeSparks[i];
      s.progress += dt * s.speed;

      if (s.progress < 1.0) {
        s.position.lerp(s.target, s.progress);
        remainingSparks.push(s);
      } else {
        if (s.hopsLeft > 1) {
          const node = this.connectome.nodes[s.currentNodeIdx];
          if (node) {
            const nextList = node.downstreamNeighbors.length > 0 ? node.downstreamNeighbors : node.neighbors;
            if (nextList.length > 0) {
              const nextIdx = nextList[Math.floor(Math.random() * nextList.length)];
              const nextNode = this.connectome.nodes[nextIdx];
              s.position.copy(node.position);
              s.target.copy(nextNode.position);
              s.progress = 0.0;
              s.hopsLeft--;
              s.currentNodeIdx = nextIdx;
              s.life *= 0.85;
              remainingSparks.push(s);
            }
          }
        }
      }
    }
    this.activeSparks = remainingSparks;

    // 5. Build GPU Particle Buffer
    let particleIdx = 0;

    // A. Render Stream Packets with Comet Glow Tails
    for (const pkt of this.activePackets) {
      for (let t = 0; t < pkt.numTrails; t++) {
        if (particleIdx >= this.maxParticles) break;

        const trailProgress = pkt.progress - t * pkt.trailSpacing;
        let actualProgress = trailProgress;
        if (pkt.isLoop) {
          if (actualProgress < 0.0) actualProgress += 1.0;
        }

        if (actualProgress >= 0.0 && actualProgress <= 1.0) {
          const pos = this.interpolateTrack(pkt.path, actualProgress);
          const trailFade = Math.pow(1.0 - t / pkt.numTrails, 1.8);

          this.particlePositions[particleIdx * 3 + 0] = pos.x;
          this.particlePositions[particleIdx * 3 + 1] = pos.y;
          this.particlePositions[particleIdx * 3 + 2] = pos.z;

          this.particleColors[particleIdx * 3 + 0] = pkt.color.r;
          this.particleColors[particleIdx * 3 + 1] = pkt.color.g;
          this.particleColors[particleIdx * 3 + 2] = pkt.color.b;

          this.particleLives[particleIdx] = pkt.life * trailFade;
          particleIdx++;
        }
      }
    }

    // B. Render Dendritic Sparks
    for (const spk of this.activeSparks) {
      if (particleIdx >= this.maxParticles) break;

      this.particlePositions[particleIdx * 3 + 0] = spk.position.x;
      this.particlePositions[particleIdx * 3 + 1] = spk.position.y;
      this.particlePositions[particleIdx * 3 + 2] = spk.position.z;

      this.particleColors[particleIdx * 3 + 0] = spk.color.r;
      this.particleColors[particleIdx * 3 + 1] = spk.color.g;
      this.particleColors[particleIdx * 3 + 2] = spk.color.b;

      this.particleLives[particleIdx] = spk.life;
      particleIdx++;
    }

    // Zero out unused slots
    for (let i = particleIdx; i < this.maxParticles; i++) {
      this.particleLives[i] = 0.0;
    }

    this.particleGeometry.attributes.position.needsUpdate = true;
    this.particleGeometry.attributes.aSignalColor.needsUpdate = true;
    this.particleGeometry.attributes.aLife.needsUpdate = true;
  }

  private interpolateTrack(path: THREE.Vector3[], progress: number): THREE.Vector3 {
    if (path.length === 0) return new THREE.Vector3();
    if (path.length === 1) return path[0].clone();

    const totalSegments = path.length - 1;
    const scaledProgress = THREE.MathUtils.clamp(progress, 0.0, 1.0) * totalSegments;
    const segIdx = Math.min(Math.floor(scaledProgress), totalSegments - 1);
    const localT = scaledProgress - segIdx;

    return new THREE.Vector3().lerpVectors(path[segIdx], path[segIdx + 1], localT);
  }
}
