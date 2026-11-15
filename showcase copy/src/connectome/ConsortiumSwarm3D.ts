/**
 * ConsortiumSwarm3D.ts
 * 
 * High-Definition 3D Multi-Cephalopod Swarm & Synaptic Cable Network for Three.js.
 * Generates 8 distinct, volumetric biological connectome units arranged in an expansive orbital ring (R = 220),
 * matching the rich anatomical fidelity of the central connectome (nodes, fibers, puncta, and traveling pulses).
 * Connected by 3D Catmull-Rom synaptic nerve cables with continuous action potential traffic.
 */

import * as THREE from 'three';
import { OctopusConnectomeGenerator } from './octopus-generator';
import type { OctopusConnectomeData } from './octopus-generator';
import {
  NeuronParticleShader,
  SynapticFiberShader,
  SynapticPunctaShader,
  ActionPotentialParticleShader,
} from './shaders';

export interface SwarmOctopusConfig {
  id: number;
  name: string;
  softwareRole: string;
  aimlRole: string;
  colorHex: number;
  angle: number;
  pulseSpeed: number;
}

export const SWARM_OCTOPUS_CONFIGS: SwarmOctopusConfig[] = [
  { id: 0, name: 'Octo 1', softwareRole: 'System Architect', aimlRole: 'Data Engineer & ETL', colorHex: 0x38bdf8, angle: 0, pulseSpeed: 3.5 },
  { id: 1, name: 'Octo 2', softwareRole: 'Database & Schemas', aimlRole: 'Model Architect', colorHex: 0x34d399, angle: (1 * Math.PI) / 4, pulseSpeed: 1.6 },
  { id: 2, name: 'Octo 3', softwareRole: 'Backend API & Auth', aimlRole: 'Training & Loss Loop', colorHex: 0xc084fc, angle: (2 * Math.PI) / 4, pulseSpeed: 3.0 },
  { id: 3, name: 'Octo 4', softwareRole: 'Frontend UI & Client', aimlRole: 'Evaluation & Benchmark', colorHex: 0xf43f5e, angle: (3 * Math.PI) / 4, pulseSpeed: 2.4 },
  { id: 4, name: 'Octo 5', softwareRole: 'State & Caching', aimlRole: 'HPO & Hyperparameter Tuner', colorHex: 0xfacc15, angle: (4 * Math.PI) / 4, pulseSpeed: 1.9 },
  { id: 5, name: 'Octo 6', softwareRole: 'QA & Test Harness', aimlRole: 'Model Quantization & ONNX', colorHex: 0xfb923c, angle: (5 * Math.PI) / 4, pulseSpeed: 3.8 },
  { id: 6, name: 'Octo 7', softwareRole: 'Security & AST Audit', aimlRole: 'Inference Serving & Gateway', colorHex: 0xe11d48, angle: (6 * Math.PI) / 4, pulseSpeed: 1.7 },
  { id: 7, name: 'Octo 8', softwareRole: 'DevOps & Live Ignition', aimlRole: 'ML Governance & Provenance', colorHex: 0x60a5fa, angle: (7 * Math.PI) / 4, pulseSpeed: 2.8 },
];

interface CablePacket {
  pathIndex: number;
  t: number;
  speed: number;
  color: THREE.Color;
}

interface SwarmUnit {
  id: number;
  config: SwarmOctopusConfig;
  group: THREE.Group;
  pointsMesh: THREE.Points;
  linesMesh: THREE.LineSegments;
  punctaMesh: THREE.Points;
  signalMesh: THREE.Points;
  ringMesh: THREE.Mesh;
  ringMat: THREE.MeshBasicMaterial;
  pointsMat: THREE.ShaderMaterial;
  linesMat: THREE.ShaderMaterial;
  punctaMat: THREE.ShaderMaterial;
  signalMat: THREE.ShaderMaterial;
  connectomeData: OctopusConnectomeData;
  activePackets: {
    armIdx: number;
    progress: number;
    speed: number;
    color: THREE.Color;
  }[];
  signalPositions: Float32Array;
  signalColors: Float32Array;
  signalLives: Float32Array;
  maxSignals: number;
}

export class ConsortiumSwarm3D {
  public group: THREE.Group;
  private units: SwarmUnit[] = [];
  public octopusGroups: THREE.Group[] = [];
  private cablesMesh: THREE.LineSegments | null = null;
  private packetPointsMesh: THREE.Points | null = null;
  private packetPositions: Float32Array;
  private packetColors: Float32Array;
  private packetSizes: Float32Array;
  private cableCurves: THREE.CatmullRomCurve3[] = [];
  private activePackets: CablePacket[] = [];
  public swarmRadius = 220; // Expansive oceanic spacing to keep octopuses far apart

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'ConsortiumSwarm3D';

    // Build the 8 High-Definition Biological Connectome Octopuses
    this.buildHighDefinitionOctopuses();

    // Build Inter-Octopus 3D Synaptic Bus Cables & Packet System
    const numCableParticles = 240;
    this.packetPositions = new Float32Array(numCableParticles * 3);
    this.packetColors = new Float32Array(numCableParticles * 3);
    this.packetSizes = new Float32Array(numCableParticles);
    this.buildSynapticCables();
    this.buildPacketPoints(numCableParticles);

    this.group.visible = true;
  }

  /**
   * Generates all 8 cephalopods with the same full anatomical connectome fidelity as the central one:
   * 2,800+ soma points, 9,000+ filament lines, 9,000+ puncta clouds, custom shaders, and arm pulses.
   */
  private buildHighDefinitionOctopuses() {
    const generator = new OctopusConnectomeGenerator();
    const densityScale = 0.28; // ~2,900 nodes & ~9,000 fibers per unit = 23,200 nodes total

    SWARM_OCTOPUS_CONFIGS.forEach((cfg) => {
      const octoGroup = new THREE.Group();
      octoGroup.name = `OctoConnectome3D_${cfg.id}`;

      // Place in 3D tiered amphitheater ring R = 220
      // Elevation equation: Y_i = -42.0 * cos(angle) + 18.0
      // Spans smoothly from -24.0 at front (Octo 1) to +60.0 at crown back (Octo 5)
      const x = this.swarmRadius * Math.sin(cfg.angle);
      const z = this.swarmRadius * Math.cos(cfg.angle);
      const y = -42.0 * Math.cos(cfg.angle) + 18.0;
      octoGroup.position.set(x, y, z);

      // Face towards center coordinates with gentle inward amphitheater gaze
      octoGroup.lookAt(0, y * 0.25, 0);

      const signatureColor = new THREE.Color(cfg.colorHex);

      // Generate biological connectome tinted with this octopus's signature color
      const data = generator.generate(densityScale, signatureColor);
      const numNodes = data.nodes.length;
      const numFibers = data.fibers.length;

      // 1. Points Mesh (Neuron Somas) with NeuronParticleShader
      const pointsGeo = new THREE.BufferGeometry();
      pointsGeo.setAttribute('position', new THREE.BufferAttribute(data.nodePositions, 3));
      pointsGeo.setAttribute('color', new THREE.BufferAttribute(data.nodeColors, 3));
      pointsGeo.setAttribute('aSize', new THREE.BufferAttribute(data.nodeSizes, 1));
      pointsGeo.setAttribute('aPhase', new THREE.BufferAttribute(data.nodePhases, 1));
      pointsGeo.setAttribute('aHighlightRole', new THREE.BufferAttribute(new Float32Array(numNodes), 1));
      pointsGeo.setAttribute('aRegionIndex', new THREE.BufferAttribute(new Float32Array(numNodes), 1));
      pointsGeo.setAttribute('aArmIndex', new THREE.BufferAttribute(new Float32Array(numNodes), 1));

      const pointsMat = new THREE.ShaderMaterial({
        vertexShader: NeuronParticleShader.vertexShader,
        fragmentShader: NeuronParticleShader.fragmentShader,
        vertexColors: true,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          uTime: { value: 0.0 },
          uActivityIntensity: { value: 1.15 },
          uIsolatedRegionIndex: { value: -1.0 },
          uHighlightedArmIndex: { value: -1.0 },
          uStimulusWaveRadius: { value: -999.0 },
          uStimulusOrigin: { value: new THREE.Vector3(0, 0, 0) },
          uStimulusIntensity: { value: 0.0 },
          uSelectedNodeIndex: { value: -1.0 },
        },
      });
      const pointsMesh = new THREE.Points(pointsGeo, pointsMat);
      octoGroup.add(pointsMesh);

      // 2. Synaptic Filament Lines with SynapticFiberShader
      const linesGeo = new THREE.BufferGeometry();
      linesGeo.setAttribute('position', new THREE.BufferAttribute(data.fiberLinePositions, 3));
      linesGeo.setAttribute('color', new THREE.BufferAttribute(data.fiberLineColors, 3));
      linesGeo.setAttribute('aFiberHighlight', new THREE.BufferAttribute(new Float32Array(numFibers * 2), 1));
      linesGeo.setAttribute('aRegionIndex', new THREE.BufferAttribute(new Float32Array(numFibers * 2), 1));
      linesGeo.setAttribute('aArmIndex', new THREE.BufferAttribute(new Float32Array(numFibers * 2), 1));

      const linesMat = new THREE.ShaderMaterial({
        vertexShader: SynapticFiberShader.vertexShader,
        fragmentShader: SynapticFiberShader.fragmentShader,
        vertexColors: true,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          uTime: { value: 0.0 },
          uFiberGlow: { value: 1.6 },
          uIsolatedRegionIndex: { value: -1.0 },
          uHighlightedArmIndex: { value: -1.0 },
        },
      });
      const linesMesh = new THREE.LineSegments(linesGeo, linesMat);
      octoGroup.add(linesMesh);

      // 3. Synaptic Puncta Clouds with SynapticPunctaShader
      const punctaGeo = new THREE.BufferGeometry();
      punctaGeo.setAttribute('position', new THREE.BufferAttribute(data.punctaPositions, 3));
      punctaGeo.setAttribute('color', new THREE.BufferAttribute(data.punctaColors, 3));

      const punctaMat = new THREE.ShaderMaterial({
        vertexShader: SynapticPunctaShader.vertexShader,
        fragmentShader: SynapticPunctaShader.fragmentShader,
        vertexColors: true,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          uTime: { value: 0.0 },
          uPunctaSize: { value: 2.2 },
          uPunctaAlpha: { value: 0.42 },
          uIsolatedRegionIndex: { value: -1.0 },
        },
      });
      const punctaMesh = new THREE.Points(punctaGeo, punctaMat);
      octoGroup.add(punctaMesh);

      // 4. Local Action Potential Streamers (Streaming through this octopus's arms)
      const maxSignals = 120;
      const signalPositions = new Float32Array(maxSignals * 3);
      const signalColors = new Float32Array(maxSignals * 3);
      const signalLives = new Float32Array(maxSignals);

      const signalGeo = new THREE.BufferGeometry();
      signalGeo.setAttribute('position', new THREE.BufferAttribute(signalPositions, 3));
      signalGeo.setAttribute('aSignalColor', new THREE.BufferAttribute(signalColors, 3));
      signalGeo.setAttribute('aLife', new THREE.BufferAttribute(signalLives, 1));

      const signalMat = new THREE.ShaderMaterial({
        vertexShader: ActionPotentialParticleShader.vertexShader,
        fragmentShader: ActionPotentialParticleShader.fragmentShader,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          uTime: { value: 0.0 },
        },
      });
      const signalMesh = new THREE.Points(signalGeo, signalMat);
      octoGroup.add(signalMesh);

      // 5. Signature Esophageal Halo Ring
      const ringGeo = new THREE.RingGeometry(3.8, 4.4, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: cfg.colorHex,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = Math.PI / 2;
      octoGroup.add(ringMesh);

      // Seed initial local action packets for this octopus
      const activePackets = [];
      for (let p = 0; p < 45; p++) {
        activePackets.push({
          armIdx: p % 8,
          progress: Math.random(),
          speed: 0.35 + Math.random() * 0.45,
          color: signatureColor.clone().lerp(new THREE.Color(0xffffff), Math.random() * 0.4),
        });
      }

      const unit: SwarmUnit = {
        id: cfg.id,
        config: cfg,
        group: octoGroup,
        pointsMesh,
        linesMesh,
        punctaMesh,
        signalMesh,
        ringMesh,
        ringMat,
        pointsMat,
        linesMat,
        punctaMat,
        signalMat,
        connectomeData: data,
        activePackets,
        signalPositions,
        signalColors,
        signalLives,
        maxSignals,
      };

      this.units.push(unit);
      this.octopusGroups.push(octoGroup);
      this.group.add(octoGroup);
    });
  }

  /**
   * Builds the long 3D Catmull-Rom synaptic nerve cables bridging all 8 distant octopuses.
   */
  private buildSynapticCables() {
    const cablePoints: number[] = [];
    const cableColors: number[] = [];
    const N = SWARM_OCTOPUS_CONFIGS.length;

    // 1. Ring Cables (Connecting Octo k to adjacent Octo k+1 around R=220)
    for (let i = 0; i < N; i++) {
      const next = (i + 1) % N;
      const c1 = SWARM_OCTOPUS_CONFIGS[i];
      const c2 = SWARM_OCTOPUS_CONFIGS[next];

      const p1 = this.octopusGroups[i].position;
      const p2 = this.octopusGroups[next].position;

      // Natural catenary sag / dip into deep abyss
      const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
      mid.multiplyScalar(0.92);
      mid.y -= 12.0;

      const curve = new THREE.CatmullRomCurve3([p1.clone(), mid, p2.clone()]);
      this.cableCurves.push(curve);

      const pts = curve.getPoints(40);
      for (let j = 0; j < pts.length - 1; j++) {
        cablePoints.push(pts[j].x, pts[j].y, pts[j].z);
        cablePoints.push(pts[j + 1].x, pts[j + 1].y, pts[j + 1].z);

        // Medium biological axon glow: vibrant and clear
        const col1 = new THREE.Color(c1.colorHex).multiplyScalar(0.78);
        const col2 = new THREE.Color(c2.colorHex).multiplyScalar(0.78);
        cableColors.push(col1.r, col1.g, col1.b);
        cableColors.push(col2.r, col2.g, col2.b);
      }
    }

    // 2. Cross-Chord Cables (Radiating gently toward central hub)
    const hub = new THREE.Vector3(0, 0, 0);
    for (let i = 0; i < N; i++) {
      const p = this.octopusGroups[i].position;
      const mid = new THREE.Vector3().addVectors(p, hub).multiplyScalar(0.5);
      mid.y -= 8.0;

      const curve = new THREE.CatmullRomCurve3([p.clone(), mid, hub.clone()]);
      this.cableCurves.push(curve);

      const pts = curve.getPoints(32);
      const col = new THREE.Color(SWARM_OCTOPUS_CONFIGS[i].colorHex);
      for (let j = 0; j < pts.length - 1; j++) {
        cablePoints.push(pts[j].x, pts[j].y, pts[j].z);
        cablePoints.push(pts[j + 1].x, pts[j + 1].y, pts[j + 1].z);

        cableColors.push(col.r * 0.50, col.g * 0.50, col.b * 0.50);
        cableColors.push(0.18, 0.45, 0.65);
      }
    }

    const cablesGeo = new THREE.BufferGeometry();
    cablesGeo.setAttribute('position', new THREE.Float32BufferAttribute(cablePoints, 3));
    cablesGeo.setAttribute('color', new THREE.Float32BufferAttribute(cableColors, 3));

    const cablesMat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.36,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    this.cablesMesh = new THREE.LineSegments(cablesGeo, cablesMat);
    this.group.add(this.cablesMesh);
  }

  /**
   * Builds the traveling action potential particle system on the long inter-octopus cables.
   */
  private buildPacketPoints(count: number) {
    const numCurves = this.cableCurves.length;
    for (let i = 0; i < count; i++) {
      const cfg = SWARM_OCTOPUS_CONFIGS[i % SWARM_OCTOPUS_CONFIGS.length];
      this.activePackets.push({
        pathIndex: Math.floor(Math.random() * numCurves),
        t: Math.random(),
        speed: 0.14 + Math.random() * 0.22,
        // Medium bioluminescent spark with gentle luminescence
        color: new THREE.Color(cfg.colorHex).lerp(new THREE.Color(0xffffff), 0.18),
      });
    }

    const packetGeo = new THREE.BufferGeometry();
    packetGeo.setAttribute('position', new THREE.BufferAttribute(this.packetPositions, 3));
    packetGeo.setAttribute('color', new THREE.BufferAttribute(this.packetColors, 3));
    packetGeo.setAttribute('aSize', new THREE.BufferAttribute(this.packetSizes, 1));

    // Refined, medium circular glowing particle shader
    const packetMat = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vColor;
        void main() {
          vColor = color;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          float pSize = 2.8 * (220.0 / -mvPosition.z);
          gl_PointSize = clamp(pSize, 2.0, 5.8);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        uniform float uOpacity;
        void main() {
          float dist = length(gl_PointCoord - vec2(0.5));
          if (dist > 0.5) discard;
          float alpha = smoothstep(0.5, 0.04, dist) * uOpacity;
          gl_FragColor = vec4(vColor, alpha);
        }
      `,
      uniforms: {
        uOpacity: { value: 0.60 },
      },
      vertexColors: true,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    this.packetPointsMesh = new THREE.Points(packetGeo, packetMat);
    this.group.add(this.packetPointsMesh);
  }

  public getOctopusPosition(index: number): THREE.Vector3 {
    const idx = Math.max(0, Math.min(this.octopusGroups.length - 1, index));
    return this.octopusGroups[idx].position.clone();
  }

  /**
   * Triggers a burst of high-voltage golden synaptic packets across all 8 octopuses.
   */
  public triggerSwarmBurst() {
    const numCurves = this.cableCurves.length;
    for (let i = 0; i < 80; i++) {
      this.activePackets.push({
        pathIndex: Math.floor(Math.random() * numCurves),
        t: 0.0,
        speed: 0.65 + Math.random() * 0.75,
        color: new THREE.Color(0xfacc15),
      });
    }

    // Flash all units
    this.units.forEach((u) => {
      u.pointsMat.uniforms.uStimulusIntensity.value = 1.8;
      u.pointsMat.uniforms.uStimulusWaveRadius.value = 0.0;
      u.pointsMat.uniforms.uStimulusOrigin.value.set(0, 0, 0);
      u.ringMat.opacity = 1.0;

      // Fire 16 action potentials in each unit
      for (let i = 0; i < 16; i++) {
        u.activePackets.push({
          armIdx: i % 8,
          progress: 0.0,
          speed: 1.2 + Math.random() * 0.8,
          color: new THREE.Color(0xfacc15),
        });
      }
    });
  }

  /**
   * Triggers high-voltage synaptic pulse across the swarm:
   * - If octoIdx in [0..7]: bursts that specific octopus with intense stimulus ripple,
   *   fires 32 rapid action potentials down all its 8 arms, and shoots synaptic packets on connecting cables!
   * - If octoIdx === -1 (or finale): bursts all 8 octopuses in full unison!
   */
  public triggerPulse(octoIdx: number = -1) {
    if (octoIdx >= 0 && octoIdx < this.units.length) {
      const unit = this.units[octoIdx];
      unit.pointsMat.uniforms.uStimulusIntensity.value = 2.2;
      unit.pointsMat.uniforms.uStimulusWaveRadius.value = 0.0;
      unit.pointsMat.uniforms.uStimulusOrigin.value.set(0, 0, 0);
      unit.ringMat.opacity = 1.0;

      // Burst 32 rapid action potentials down all 8 arms
      for (let i = 0; i < 32; i++) {
        unit.activePackets.push({
          armIdx: i % 8,
          progress: 0.0,
          speed: 1.4 + Math.random() * 0.9,
          color: new THREE.Color(0xfacc15),
        });
      }

      // Cable synaptic burst radiating outwards
      const numCurves = this.cableCurves.length;
      for (let i = 0; i < 25; i++) {
        this.activePackets.push({
          pathIndex: Math.floor(Math.random() * numCurves),
          t: 0.0,
          speed: 0.75 + Math.random() * 0.65,
          color: new THREE.Color(0xfacc15),
        });
      }
    } else {
      this.triggerSwarmBurst();
    }
  }

  public update(time: number, delta: number, currentSlide: number) {
    const isSwarmPhase = currentSlide >= 18;
    const isFinale = currentSlide >= 26;
    const activeOctoIdx = isSwarmPhase && !isFinale ? currentSlide - 18 : -1;

    // 1. Update Each Individual Cephalopod Connectome Unit
    this.units.forEach((unit, idx) => {
      const isFocused = idx === activeOctoIdx;

      // Spotlight vs Sleepy Background Logic:
      // When focused: refined spotlight (1.45), vibrant fibers (1.65), puncta (0.55), ring (0.70)
      // When not focused during slides 19-26: sleepy faint silhouette (0.012), dim fibers (0.025), puncta (0.0), ring (0.0)
      // When finale: all 8 awake in full harmony (1.25)
      let targetScale = 0.55;
      let targetIntensity = 0.012;
      let targetFiberGlow = 0.025;
      let targetPunctaAlpha = 0.0;
      let targetRingOpacity = 0.0;

      if (isFocused) {
        // Spotlighted individual octopus: calibrated scale to fit 100% of body & arms on right side of screen
        targetScale = 0.92;
        targetIntensity = 1.45;
        targetFiberGlow = 1.65;
        targetPunctaAlpha = 0.55;
        targetRingOpacity = 0.70;
      } else if (isFinale) {
        // Grand Finale: all 8 octopuses awakened in unison across the 3D amphitheater
        targetScale = 0.95;
        targetIntensity = 1.25;
        targetFiberGlow = 1.45;
        targetPunctaAlpha = 0.45;
        targetRingOpacity = 0.65;
      } else if (!isSwarmPhase) {
        // Slides 01 - 18: very faint background constellation
        targetScale = 0.50;
        targetIntensity = 0.008;
        targetFiberGlow = 0.012;
        targetPunctaAlpha = 0.0;
        targetRingOpacity = 0.0;
      }

      unit.group.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.08);

      // Subtle gentle biological breathing motion in water around tiered amphitheater base elevation
      const pulseSpeed = unit.config.pulseSpeed;
      const baseTierY = -42.0 * Math.cos(unit.config.angle) + 18.0;
      unit.group.position.y = baseTierY + Math.sin(cfg_angle_y(unit.config.angle, time, pulseSpeed)) * (isFocused ? 1.8 : 1.2);

      // Visibility toggles for accessories (ring and signals)
      unit.ringMesh.visible = isFocused || isFinale;
      unit.signalMesh.visible = isFocused || isFinale;

      // Update unit-specific shaders with its distinctive pulsation frequency
      const unitTime = time * pulseSpeed;
      unit.pointsMat.uniforms.uTime.value = unitTime;
      unit.linesMat.uniforms.uTime.value = unitTime;
      unit.punctaMat.uniforms.uTime.value = unitTime;
      unit.signalMat.uniforms.uTime.value = unitTime;

      // Smoothly interpolate intensity and visibility uniforms
      unit.pointsMat.uniforms.uActivityIntensity.value +=
        (targetIntensity - unit.pointsMat.uniforms.uActivityIntensity.value) * 0.10;
      unit.linesMat.uniforms.uFiberGlow.value +=
        (targetFiberGlow - unit.linesMat.uniforms.uFiberGlow.value) * 0.10;
      unit.punctaMat.uniforms.uPunctaAlpha.value +=
        (targetPunctaAlpha - unit.punctaMat.uniforms.uPunctaAlpha.value) * 0.10;
      unit.ringMat.opacity += (targetRingOpacity - unit.ringMat.opacity) * 0.10;

      // Shockwave decay if active
      if (unit.pointsMat.uniforms.uStimulusIntensity.value > 0.01) {
        unit.pointsMat.uniforms.uStimulusWaveRadius.value += delta * 60.0;
        unit.pointsMat.uniforms.uStimulusIntensity.value -= delta * 0.6;
      }

      // Update Local Action Potentials traveling through this unit's 8 arms
      // Suppress sparks on non-focused units so background stays clean & dim
      const signalLifeMult = isFocused ? 1.0 : (isFinale ? 0.85 : 0.0);
      const nodePos = unit.connectomeData.nodePositions;
      let writeIdx = 0;

      if (signalLifeMult > 0.0) {
        for (let p = unit.activePackets.length - 1; p >= 0; p--) {
          const pkt = unit.activePackets[p];
          pkt.progress += delta * pkt.speed * (isFocused ? 1.4 : 0.4);
          if (pkt.progress >= 1.0) {
            pkt.progress = 0.0;
            pkt.armIdx = Math.floor(Math.random() * 8);
          }

          const armNodes = unit.connectomeData.armNodeIndices[pkt.armIdx];
          if (armNodes && armNodes.length > 0 && writeIdx < unit.maxSignals) {
            const nodeIdxInArm = Math.floor(pkt.progress * (armNodes.length - 1));
            const realNodeIdx = armNodes[nodeIdxInArm];

            const px = nodePos[realNodeIdx * 3];
            const py = nodePos[realNodeIdx * 3 + 1];
            const pz = nodePos[realNodeIdx * 3 + 2];

            const i3 = writeIdx * 3;
            unit.signalPositions[i3] = px + Math.sin(unitTime * 4.0 + p) * 0.2;
            unit.signalPositions[i3 + 1] = py + Math.cos(unitTime * 4.0 + p) * 0.2;
            unit.signalPositions[i3 + 2] = pz;

            unit.signalColors[i3] = pkt.color.r;
            unit.signalColors[i3 + 1] = pkt.color.g;
            unit.signalColors[i3 + 2] = pkt.color.b;

            unit.signalLives[writeIdx] = (1.0 - pkt.progress * 0.3) * signalLifeMult;
            writeIdx++;
          }
        }
      }

      for (let i = writeIdx; i < unit.maxSignals; i++) {
        unit.signalLives[i] = 0.0;
      }

      unit.signalMesh.geometry.attributes.position.needsUpdate = true;
      (unit.signalMesh.geometry.attributes.aSignalColor as THREE.BufferAttribute).needsUpdate = true;
      (unit.signalMesh.geometry.attributes.aLife as THREE.BufferAttribute).needsUpdate = true;
    });

    // 2. Inter-Octopus Synaptic Nerve Cables & Action Potential Sparks:
    // Visible between all 8 octopuses throughout the swarm experience (Slides 19 - 27).
    // Tuned with soft, gentle luminescence so they connect the octopuses gracefully without glowing too much.
    const isSwarmVisible = isSwarmPhase || isFinale;

    if (this.cablesMesh) {
      this.cablesMesh.visible = isSwarmVisible;
      // Medium biological glow: clear and vibrant across the orbital ring
      const targetCableOpacity = isFinale ? 0.48 : (isSwarmPhase ? 0.36 : 0.08);
      const lineMat = this.cablesMesh.material as THREE.LineBasicMaterial;
      lineMat.opacity += (targetCableOpacity - lineMat.opacity) * 0.10;
    }

    if (this.packetPointsMesh) {
      this.packetPointsMesh.visible = isSwarmVisible;
      const targetPacketOpacity = isFinale ? 0.85 : (isSwarmPhase ? 0.62 : 0.12);
      const pMat = this.packetPointsMesh.material as THREE.ShaderMaterial;
      if (pMat.uniforms && pMat.uniforms.uOpacity) {
        pMat.uniforms.uOpacity.value += (targetPacketOpacity - pMat.uniforms.uOpacity.value) * 0.10;
      }
    }

    if (isSwarmVisible && this.packetPointsMesh && this.cableCurves.length > 0) {
      const numPackets = this.activePackets.length;
      const speedScale = isFinale ? 1.3 : 1.0;

      for (let i = 0; i < numPackets && i < 240; i++) {
        const pkt = this.activePackets[i];
        pkt.t += pkt.speed * delta * speedScale;
        if (pkt.t > 1.0) {
          pkt.t = 0.0;
          pkt.pathIndex = Math.floor(Math.random() * this.cableCurves.length);
        }

        const curve = this.cableCurves[pkt.pathIndex];
        if (curve) {
          const pt = curve.getPoint(pkt.t);
          this.packetPositions[i * 3] = pt.x;
          this.packetPositions[i * 3 + 1] = pt.y;
          this.packetPositions[i * 3 + 2] = pt.z;

          this.packetColors[i * 3] = pkt.color.r;
          this.packetColors[i * 3 + 1] = pkt.color.g;
          this.packetColors[i * 3 + 2] = pkt.color.b;
        }
      }
      this.packetPointsMesh.geometry.attributes.position.needsUpdate = true;
      this.packetPointsMesh.geometry.attributes.color.needsUpdate = true;
    }
  }

  public destroy() {
    this.units.forEach((u) => {
      u.pointsMesh.geometry.dispose();
      u.linesMesh.geometry.dispose();
      u.punctaMesh.geometry.dispose();
      u.signalMesh.geometry.dispose();
      u.pointsMat.dispose();
      u.linesMat.dispose();
      u.punctaMat.dispose();
      u.signalMat.dispose();
    });
    if (this.cablesMesh) {
      this.cablesMesh.geometry.dispose();
      (this.cablesMesh.material as THREE.Material).dispose();
    }
    if (this.packetPointsMesh) {
      this.packetPointsMesh.geometry.dispose();
      (this.packetPointsMesh.material as THREE.Material).dispose();
    }
  }
}

function cfg_angle_y(angle: number, time: number, speed: number): number {
  return time * 0.8 * (speed * 0.35) + angle * 2.0;
}
