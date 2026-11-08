/**
 * OctosFlow 3D Cephalopod Constellation & Live Synaptic Mesh.
 *
 * Renders 8 full biological connectome octopuses in an orbital 3D constellation.
 * Every single octopus is an authentic, living cephalopod with full neuroanatomy
 * (optic lobes, central brain neuropils, vertical memory lobe, 8 neural lattice arms),
 * fluid biological mantle breathing, undulating tentacle ripples, and live action potentials.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import * as TWEEN from '@tweenjs/tween.js';

import { OctopusConnectomeGenerator } from './octopus-generator';
import type { OctopusConnectomeData } from './octopus-generator';
import { NeuralNetworkMesh } from './neural-network';
import { AnatomicalMeshGenerator } from './anatomical-mesh';
import { SignalPropagator } from './signal-propagator';
import type { CameraController } from '../core/camera-controller';
import { ICONS } from '../ui/icons';
import { parseTelemetryMessage, ReconnectController } from '../telemetry/parse';
import { isReducedMotion } from '../a11y/motion-policy';
import { getArmProfile, updateArmProfilesFromGuild } from '../a11y/arm-profiles';

export interface OctopusNodeData {
  id: number;
  title: string;
  department: string;
  colorHex: string;
  icon: string;
  status: string;
  progressPct: number;
  coreRole: string;
  softwareTitle: string;
  softwareRole: string;
  aimlTitle: string;
  aimlRole: string;
  currentAction: string;
  surprise: number;
  threshold: number;
  activeArms: number;
  position: THREE.Vector3;
}

export interface FullCephalopod {
  id: number;
  data: OctopusNodeData;
  group: THREE.Group;
  connectomeData: OctopusConnectomeData;
  neuralNetwork: NeuralNetworkMesh;
  anatomicalMesh: AnatomicalMeshGenerator;
  signalPropagator: SignalPropagator;
  basePosition: THREE.Vector3;
  spontaneousTimer: number;
  badgeCard?: HTMLElement;
}

export const DEFAULT_OCTOPOLIS_DATA: OctopusNodeData[] = [
  {
    id: 0,
    title: 'System Architect',
    department: 'Architecture & Data',
    colorHex: '#00F0FF',
    icon: '',
    status: 'ACTIVE',
    progressPct: 100,
    coreRole: 'Global orchestration & mission planning',
    softwareTitle: 'System Architect',
    softwareRole: 'System specifications & folder topology',
    aimlTitle: 'Data Engineer',
    aimlRole: 'Dataset ETL & PyTorch DataLoaders',
    currentAction: 'Global orchestration & mission planning',
    surprise: 0.12,
    threshold: 0.45,
    activeArms: 8,
    position: new THREE.Vector3(),
  },
  {
    id: 1,
    title: 'Database & Storage',
    department: 'Persistence & Models',
    colorHex: '#A855F7',
    icon: '',
    status: 'ACTIVE',
    progressPct: 90,
    coreRole: 'Vector memory & persistent storage',
    softwareTitle: 'Database & Schemas',
    softwareRole: 'SQL/ORM models & vector persistence',
    aimlTitle: 'Model Architect',
    aimlRole: 'Deep neural layers & forward passes',
    currentAction: 'Vector memory & persistent storage',
    surprise: 0.18,
    threshold: 0.50,
    activeArms: 8,
    position: new THREE.Vector3(),
  },
  {
    id: 2,
    title: 'Backend & Services',
    department: 'Core Engine & Compute',
    colorHex: '#3B82F6',
    icon: '',
    status: 'ACTIVE',
    progressPct: 85,
    coreRole: 'API services & backend compute engine',
    softwareTitle: 'Backend API',
    softwareRole: 'REST endpoints & distributed services',
    aimlTitle: 'Training Engineer',
    aimlRole: 'GPU training loops & hardware compute',
    currentAction: 'API services & backend compute engine',
    surprise: 0.22,
    threshold: 0.50,
    activeArms: 8,
    position: new THREE.Vector3(),
  },
  {
    id: 3,
    title: 'Frontend & UI',
    department: 'Sensory & Evaluation',
    colorHex: '#EC4899',
    icon: '',
    status: 'ACTIVE',
    progressPct: 80,
    coreRole: '3D visualizer & user interface',
    softwareTitle: 'Frontend UI',
    softwareRole: 'User interface views & 3D telepresence',
    aimlTitle: 'Eval & Benchmarks',
    aimlRole: 'Accuracy metrics & ROC validation',
    currentAction: '3D visualizer & user interface',
    surprise: 0.25,
    threshold: 0.55,
    activeArms: 8,
    position: new THREE.Vector3(),
  },
  {
    id: 4,
    title: 'AI & Cognitive Logic',
    department: 'Reasoning & Tuning',
    colorHex: '#10B981',
    icon: '',
    status: 'ACTIVE',
    progressPct: 75,
    coreRole: 'AI reasoning & multi-arm decisions',
    softwareTitle: 'State & Client Sync',
    softwareRole: 'Reactive state & hooks synchronization',
    aimlTitle: 'HPO / Tuner',
    aimlRole: 'Hyperparameter search & Bayesian tuning',
    currentAction: 'AI reasoning & multi-arm decisions',
    surprise: 0.19,
    threshold: 0.50,
    activeArms: 8,
    position: new THREE.Vector3(),
  },
  {
    id: 5,
    title: 'Sentinel & Security',
    department: 'Guardianship & Quantization',
    colorHex: '#EF4444',
    icon: '',
    status: 'ACTIVE',
    progressPct: 95,
    coreRole: 'Security guardrails & policy enforcement',
    softwareTitle: 'Security & Audit',
    softwareRole: 'Security guardrails & vulnerability audit',
    aimlTitle: 'Quantization & ONNX',
    aimlRole: 'INT8 quantization & ONNX Runtime graph',
    currentAction: 'Security guardrails & policy enforcement',
    surprise: 0.08,
    threshold: 0.40,
    activeArms: 8,
    position: new THREE.Vector3(),
  },
  {
    id: 6,
    title: 'Chaos & QA Testing',
    department: 'Verification & Serving',
    colorHex: '#F59E0B',
    icon: '',
    status: 'ACTIVE',
    progressPct: 85,
    coreRole: 'Chaos testing & resilience verification',
    softwareTitle: 'Chaos & QA Testing',
    softwareRole: 'Unit testing & resilience assertions',
    aimlTitle: 'Inference Serving',
    aimlRole: 'FastAPI prediction server & latency benchmarking',
    currentAction: 'Chaos testing & resilience verification',
    surprise: 0.21,
    threshold: 0.40,
    activeArms: 8,
    position: new THREE.Vector3(),
  },
  {
    id: 7,
    title: 'Runner & DevOps',
    department: 'Deployment & MLOps',
    colorHex: '#EAB308',
    icon: '',
    status: 'ACTIVE',
    progressPct: 100,
    coreRole: 'Tool execution & automated workflows',
    softwareTitle: 'DevOps & Deployment',
    softwareRole: 'Docker containers & CI/CD deployment',
    aimlTitle: 'MLOps & Governance',
    aimlRole: 'Model cards, experiment tracking & lockfiles',
    currentAction: 'Tool execution & automated workflows',
    surprise: 0.05,
    threshold: 0.50,
    activeArms: 8,
    position: new THREE.Vector3(),
  },
];

export class CephalopodConstellationManager {
  public group = new THREE.Group();
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private controls?: OrbitControls;
  public cameraController: CameraController | null = null;
  public isOctopusFocused: boolean = false;

  public octopuses: Map<number, FullCephalopod> = new Map();
  public activeOctopusId: number = 0;

  private synapticBeams: {
    line: THREE.Line;
    curve: THREE.CatmullRomCurve3;
    sourceId: number;
    targetId: number;
    color: string;
  }[] = [];

  private energyPackets: {
    mesh: THREE.Mesh;
    curve: THREE.CatmullRomCurve3;
    progress: number;
    speed: number;
  }[] = [];

  private hudOverlayContainer: HTMLElement | null = null;
  private ws: WebSocket | null = null;
  private reconnectController: ReconnectController = new ReconnectController({
    initialDelayMs: 1000,
    maxDelayMs: 10000,
    backoffMultiplier: 1.5,
  });
  public onSelectOctopus: ((data: OctopusNodeData, octo: FullCephalopod) => void) | null = null;

  constructor(scene: THREE.Scene, camera: THREE.PerspectiveCamera, controls?: OrbitControls, cameraController?: CameraController) {
    this.scene = scene;
    this.camera = camera;
    this.controls = controls;
    this.cameraController = cameraController || null;

    this.initConstellation();
    this.createSynapticBeams();
    this.setupHUDOverlay();
    this.connectTelemetryWebSocket();
  }

  public setCameraController(cameraController: CameraController) {
    this.cameraController = cameraController;
  }

  public domainMode: 'DUAL' | 'SOFTWARE' | 'AIML' = 'DUAL';
  public onDomainModeChange?: (mode: 'DUAL' | 'SOFTWARE' | 'AIML') => void;
  public onLiveServiceReady?: (evt: any) => void;
  public onTelemetryEvent?: (evt: any) => void;

  public setDomainMode(mode: 'DUAL' | 'SOFTWARE' | 'AIML') {
    this.domainMode = mode;
    this.updateHUDLabels();
    if (this.onDomainModeChange) {
      this.onDomainModeChange(mode);
    }
  }

  private initConstellation() {
    this.group.name = 'CephalopodConstellation';
    const radius = 120; // Generous orbital radius for 8 full-scale cephalopods
    const count = DEFAULT_OCTOPOLIS_DATA.length;

    DEFAULT_OCTOPOLIS_DATA.forEach((data, index) => {
      const angle = (index / count) * Math.PI * 2;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = Math.sin(index * 1.5) * 10;

      data.position.set(x, y, z);

      const octoGroup = new THREE.Group();
      octoGroup.position.copy(data.position);
      octoGroup.scale.setScalar(0.75); // Majestic proportion
      // Orient facing outwards from ring center
      octoGroup.rotation.y = -angle + Math.PI / 2;
      octoGroup.userData = { octopusId: data.id, isFullCephalopod: true };

      // 0. Hit Collider for 100% reliable 3D click & hover picking across entire cephalopod
      const hitColliderGeo = new THREE.SphereGeometry(48, 16, 16);
      const hitColliderMat = new THREE.MeshBasicMaterial({
        transparent: true,
        opacity: 0.0,
        depthWrite: false,
      });
      const hitCollider = new THREE.Mesh(hitColliderGeo, hitColliderMat);
      hitCollider.visible = true; // Must be true so Three.js Raycaster intersects it!
      hitCollider.name = `hit-collider-${data.id}`;
      hitCollider.userData = { octopusId: data.id, isHitCollider: true };
      octoGroup.add(hitCollider);

      // 1. Generate Full 3D Connectome (Neurons & Synapses) tinted with guild color
      const generator = new OctopusConnectomeGenerator();
      const connectomeData = generator.generate(1.0, data.colorHex);

      // 2. Build GPU Neural Network Mesh
      const neuralNetwork = new NeuralNetworkMesh(connectomeData);
      octoGroup.add(neuralNetwork.group);

      // 3. Build Ghosted Anatomical Silhouette & Mantle tinted with guild color
      const anatomicalMesh = new AnatomicalMeshGenerator(data.colorHex);
      octoGroup.add(anatomicalMesh.group);

      // 4. Build Neural Signal Propagator (Action potentials & impulses)
      const signalPropagator = new SignalPropagator(connectomeData, data.colorHex);
      octoGroup.add(signalPropagator.group);

      this.group.add(octoGroup);

      const cephalopod: FullCephalopod = {
        id: data.id,
        data,
        group: octoGroup,
        connectomeData,
        neuralNetwork,
        anatomicalMesh,
        signalPropagator,
        basePosition: data.position.clone(),
        spontaneousTimer: Math.random() * 2.0,
      };

      this.octopuses.set(data.id, cephalopod);
    });

    this.scene.add(this.group);
  }

  private createSynapticBeams() {
    const octoList = Array.from(this.octopuses.values());
    const count = octoList.length;

    // Connect adjacent nodes in ring plus cross-consortium hubs
    for (let i = 0; i < count; i++) {
      const nextIdx = (i + 1) % count;
      this.addBeam(octoList[i].data.id, octoList[nextIdx].data.id, octoList[i].data.colorHex);

      // Cross-consortium synaptic bridges to Architect (Octo 0) and Backend (Octo 2)
      if (i !== 0 && i !== count - 1) {
        this.addBeam(0, octoList[i].data.id, '#00F0FF');
      }
      if (i !== 2 && (i === 3 || i === 1 || i === 6)) {
        this.addBeam(2, octoList[i].data.id, '#3B82F6');
      }
    }
  }

  private addBeam(sourceId: number, targetId: number, colorHex: string) {
    const src = this.octopuses.get(sourceId);
    const tgt = this.octopuses.get(targetId);
    if (!src || !tgt) return;

    // Arched 3D glowing catenary curve
    const mid = new THREE.Vector3()
      .addVectors(src.basePosition, tgt.basePosition)
      .multiplyScalar(0.5);
    mid.y += (sourceId === 0 || targetId === 0) ? 28 : 16;

    const curve = new THREE.CatmullRomCurve3([src.basePosition, mid, tgt.basePosition]);
    const points = curve.getPoints(36);
    const geo = new THREE.BufferGeometry().setFromPoints(points);

    const mat = new THREE.LineBasicMaterial({
      color: new THREE.Color(colorHex),
      transparent: true,
      opacity: 0.40,
      blending: THREE.AdditiveBlending,
    });

    const line = new THREE.Line(geo, mat);
    this.group.add(line);
    this.synapticBeams.push({ line, curve, sourceId, targetId, color: colorHex });

    // Spawn moving photon energy packet along the beam
    this.spawnPhotonPacket(curve, colorHex);
  }

  private spawnPhotonPacket(curve: THREE.CatmullRomCurve3, colorHex: string) {
    const packetGeo = new THREE.SphereGeometry(1.2, 12, 12);
    const packetMat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(colorHex),
      blending: THREE.AdditiveBlending,
    });
    const packetMesh = new THREE.Mesh(packetGeo, packetMat);
    this.group.add(packetMesh);

    this.energyPackets.push({
      mesh: packetMesh,
      curve,
      progress: Math.random(),
      speed: 0.0018 + Math.random() * 0.0025,
    });
  }

  private setupHUDOverlay() {
    this.hudOverlayContainer = document.getElementById('constellation-hud');
    if (!this.hudOverlayContainer) {
      this.hudOverlayContainer = document.createElement('div');
      this.hudOverlayContainer.id = 'constellation-hud';
      this.hudOverlayContainer.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 100;
        overflow: hidden;
      `;
      document.body.appendChild(this.hudOverlayContainer);
    }
    this.updateHUDLabels();
  }

  private updateHUDLabels() {
    if (!this.hudOverlayContainer) return;
    this.hudOverlayContainer.innerHTML = '';

    this.octopuses.forEach((entry) => {
      const card = document.createElement('div');
      const armProfile = getArmProfile(entry.data.id);
      card.id = `octo-card-${entry.data.id}`;
      card.className = 'glass-panel octo-badge';
      card.setAttribute('data-octo-id', String(entry.data.id));
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
      card.setAttribute('aria-label', `Arm ${entry.data.id}: ${entry.data.title} (${armProfile.code}). Status: ${entry.data.status}`);
      card.style.cssText = `
        position: absolute;
        pointer-events: auto;
        cursor: pointer;
        transform: translate(-50%, -50%);
        padding: 8px 14px;
        background: rgba(11, 15, 25, 0.88);
        border: 1px solid ${entry.data.colorHex};
        border-radius: 10px;
        box-shadow: 0 0 18px ${entry.data.colorHex}55;
        transition: transform 0.2s, box-shadow 0.2s;
        min-width: 200px;
        color: #ffffff;
        font-family: 'Roboto Mono', monospace;
      `;

      const customGlyph = ICONS.octoGlyph(entry.data.id, 15);

        let titleDisplay: string;
        let roleHtml: string;

        if (this.domainMode === 'DUAL') {
          roleHtml = `
            <div style="font-weight: 700; font-size: 11px; letter-spacing: 0.02em; margin-bottom: 3px; font-family: 'Roboto Mono', monospace;">
              ${entry.data.title.toUpperCase()}
            </div>
            <div style="font-size: 8.5px; line-height: 1.35; margin-bottom: 6px; font-family: 'Roboto Mono', monospace;">
              <div style="color: ${entry.data.colorHex}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                <span style="opacity: 0.65; font-size: 7.5px; font-weight: 700;">[SW]</span> ${entry.data.softwareRole}
              </div>
              <div style="color: #a6e3a1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 1px;">
                <span style="opacity: 0.65; font-size: 7.5px; font-weight: 700;">[AI]</span> ${entry.data.aimlRole}
              </div>
            </div>
          `;
        } else if (this.domainMode === 'SOFTWARE') {
          titleDisplay = entry.data.softwareTitle.toUpperCase();
          roleHtml = `
            <div style="font-weight: 700; font-size: 11px; letter-spacing: 0.02em; margin-bottom: 2px; font-family: 'Roboto Mono', monospace;">
              ${titleDisplay}
            </div>
            <div style="font-size: 9.5px; opacity: 0.85; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-family: 'Roboto Mono', monospace; color: ${entry.data.colorHex};">
              ${entry.data.softwareRole}
            </div>
          `;
        } else {
          titleDisplay = entry.data.aimlTitle.toUpperCase();
          roleHtml = `
            <div style="font-weight: 700; font-size: 11px; letter-spacing: 0.02em; margin-bottom: 2px; font-family: 'Roboto Mono', monospace;">
              ${titleDisplay}
            </div>
            <div style="font-size: 9.5px; opacity: 0.85; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-family: 'Roboto Mono', monospace; color: #a6e3a1;">
              ${entry.data.aimlRole}
            </div>
          `;
        }

        card.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;">
            <div style="display: flex; align-items: center; gap: 6px;">
              ${customGlyph}
              <span style="font-weight: 700; font-size: 11px; letter-spacing: 0.04em; color: ${entry.data.colorHex}; font-family: 'Roboto Mono', monospace;">
                <span aria-hidden="true" style="margin-right: 2px;">${armProfile.symbol}</span>[${armProfile.code}] ARM_${entry.data.id}
              </span>
            </div>
            <span style="font-size: 9px; font-weight: 600; padding: 1px 5px; border-radius: 4px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; letter-spacing: 0.04em; font-family: 'Roboto Mono', monospace;">
              ${entry.data.status}
            </span>
          </div>
          ${roleHtml}
          <div style="width: 100%; background: rgba(255, 255, 255, 0.08); height: 3px; border-radius: 2px; overflow: hidden;">
            <div style="width: ${entry.data.progressPct}%; background: ${entry.data.colorHex}; height: 100%; border-radius: 2px;"></div>
          </div>
        `;

      card.addEventListener('mouseenter', () => {
        card.style.transform = 'translate(-50%, -50%) scale(1.08)';
        card.style.boxShadow = `0 0 28px ${entry.data.colorHex}aa`;
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = 'translate(-50%, -50%) scale(1.0)';
        card.style.boxShadow = `0 0 18px ${entry.data.colorHex}55`;
      });

      card.addEventListener('click', (e) => {
        e.stopPropagation();
        this.focusOnOctopus(entry.data.id);
      });

      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          this.focusOnOctopus(entry.data.id);
        }
      });

      entry.badgeCard = card;

      if (this.hudOverlayContainer) {
        this.hudOverlayContainer.appendChild(card);
      }
    });
  }

  public getActiveOctopus(): FullCephalopod {
    return this.octopuses.get(this.activeOctopusId) || this.octopuses.get(0)!;
  }

  /**
   * Single-Octopus Spotlight Isolation:
   * When an octopus is chosen, it is rendered in 100% vibrant brilliance with its badge card highlighted,
   * while the other 7 octopuses fade into subtle ethereal ghost silhouettes in the distant background.
   */
  public applyOctopusSpotlight(activeId: number | null) {
    this.octopuses.forEach((entry, id) => {
      const isTarget = activeId === null || id === activeId;

      if (entry.badgeCard) {
        if (activeId === null) {
          entry.badgeCard.style.display = 'block';
          entry.badgeCard.style.opacity = '1.0';
          entry.badgeCard.style.transform = 'translate(-50%, -50%) scale(1.0)';
          entry.badgeCard.style.boxShadow = `0 0 18px ${entry.data.colorHex}55`;
          entry.badgeCard.style.borderColor = entry.data.colorHex;
        } else if (isTarget) {
          entry.badgeCard.style.display = 'block';
          entry.badgeCard.style.opacity = '1.0';
          entry.badgeCard.style.transform = 'translate(-50%, -50%) scale(1.16)';
          entry.badgeCard.style.boxShadow = `0 0 35px ${entry.data.colorHex}, inset 0 0 12px ${entry.data.colorHex}44`;
          entry.badgeCard.style.borderColor = '#ffffff';
        } else {
          entry.badgeCard.style.opacity = '0.18';
          entry.badgeCard.style.transform = 'translate(-50%, -50%) scale(0.82)';
          entry.badgeCard.style.boxShadow = 'none';
        }
      }

      if (activeId === null) {
        // Full Constellation view: all 8 octopuses fully active
        entry.group.scale.set(1.0, 1.0, 1.0);
        entry.anatomicalMesh.setOpacity(0.14);
        entry.neuralNetwork.setFiberGlow(0.85);
        entry.neuralNetwork.setNeuropilHullOpacity(0.28);
      } else if (isTarget) {
        // Spotlight focused single octopus: high clarity, brilliant synaptic glow
        entry.group.scale.set(1.0, 1.0, 1.0);
        entry.anatomicalMesh.setOpacity(0.22);
        entry.neuralNetwork.setFiberGlow(1.0);
        entry.neuralNetwork.setNeuropilHullOpacity(0.38);
      } else {
        // Ethereal ghost mode for background octopuses
        entry.group.scale.set(0.85, 0.85, 0.85);
        entry.anatomicalMesh.setOpacity(0.02);
        entry.neuralNetwork.setFiberGlow(0.12);
        entry.neuralNetwork.setNeuropilHullOpacity(0.04);
      }
    });
  }

  /**
   * GTA V Style Character Switch to Selected Octopus:
   * 1. Pulls back and rockets into satellite orbit with dynamic wide-angle FOV expansion.
   * 2. Arcs across the galaxy towards target octopus coordinates.
   * 3. Dives straight down into the target octopus, locks OrbitControls pivot on its brain center.
   * 4. Developer can now orbit in 360° directly around this chosen single octopus!
   */
  public focusOnOctopus(octoId: number) {
    const entry = this.octopuses.get(octoId);
    if (!entry) return;

    this.activeOctopusId = octoId;
    this.isOctopusFocused = true;

    // Spotlight the selected octopus and ghost the other 7
    this.applyOctopusSpotlight(octoId);

    if (this.onSelectOctopus) {
      this.onSelectOctopus(entry.data, entry);
    }

    // World position of this octopus in the constellation
    const targetPos = new THREE.Vector3();
    entry.group.getWorldPosition(targetPos);

    // Calculate outward radial direction from ring center (0, 0, 0)
    const radialDir = new THREE.Vector3(targetPos.x, 0, targetPos.z).normalize();
    if (radialDir.lengthSq() < 0.001) radialDir.set(0, 0, 1);

    // Position camera outside the ring, looking back in at the octopus from an elevated 3/4 angle
    const camPos = targetPos.clone()
      .add(radialDir.clone().multiplyScalar(46))
      .add(new THREE.Vector3(0, 20, 0));

    // Focus target is at the center of the octopus brain/mantle
    const lookAtPos = targetPos.clone().add(new THREE.Vector3(0, 4, 0));

    if (this.cameraController) {
      this.cameraController.setAnchor(targetPos);
      // Execute signature GTA V Character Switch Arc!
      this.cameraController.gtaSwitchTo(camPos, lookAtPos, 1450, () => {
        // Trigger action potential cascade across all 8 arms upon landing
        entry.signalPropagator.triggerArmCascade(90);
      });
    } else {
      if (this.controls) this.controls.enabled = true;
      const startCam = this.camera.position.clone();
      const startTarget = this.controls ? this.controls.target.clone() : new THREE.Vector3();

      new TWEEN.Tween({
        camX: startCam.x,
        camY: startCam.y,
        camZ: startCam.z,
        tgtX: startTarget.x,
        tgtY: startTarget.y,
        tgtZ: startTarget.z,
      })
        .to({
          camX: camPos.x,
          camY: camPos.y,
          camZ: camPos.z,
          tgtX: lookAtPos.x,
          tgtY: lookAtPos.y,
          tgtZ: lookAtPos.z,
        }, 1300)
        .easing(TWEEN.Easing.Cubic.InOut)
        .onUpdate((obj) => {
          this.camera.position.set(obj.camX, obj.camY, obj.camZ);
          if (this.controls) {
            this.controls.target.set(obj.tgtX, obj.tgtY, obj.tgtZ);
            this.controls.update();
          }
          this.camera.lookAt(lookAtPos);
        })
        .onComplete(() => {
          if (this.controls) {
            this.controls.enabled = true;
            this.controls.update();
          }
          entry.signalPropagator.triggerArmCascade(90);
        })
        .start();
    }
  }

  /**
   * Return from Single-Octopus Focus to Full 8-Octopus Swarm Orbit.
   * Rockets back to high constellation view, restores all 8 octopuses to full brilliance,
   * and resumes constellation ring rotation.
   */
  public resetOrbitView() {
    this.isOctopusFocused = false;
    this.applyOctopusSpotlight(null);

    const orbitCamPos = new THREE.Vector3(0, 140, 260);
    const orbitTarget = new THREE.Vector3(0, 0, 0);

    if (this.cameraController) {
      this.cameraController.setAnchor(new THREE.Vector3(0, 0, 0));
      this.cameraController.gtaSwitchTo(orbitCamPos, orbitTarget, 1400);
    } else {
      if (this.controls) this.controls.enabled = true;
      const startCam = this.camera.position.clone();
      const startTarget = this.controls ? this.controls.target.clone() : new THREE.Vector3();

      new TWEEN.Tween({
        camX: startCam.x,
        camY: startCam.y,
        camZ: startCam.z,
        tgtX: startTarget.x,
        tgtY: startTarget.y,
        tgtZ: startTarget.z,
      })
        .to({
          camX: orbitCamPos.x,
          camY: orbitCamPos.y,
          camZ: orbitCamPos.z,
          tgtX: orbitTarget.x,
          tgtY: orbitTarget.y,
          tgtZ: orbitTarget.z,
        }, 1400)
        .easing(TWEEN.Easing.Cubic.InOut)
        .onUpdate((obj) => {
          this.camera.position.set(obj.camX, obj.camY, obj.camZ);
          if (this.controls) {
            this.controls.target.set(obj.tgtX, obj.tgtY, obj.tgtZ);
            this.controls.update();
          }
          this.camera.lookAt(orbitTarget);
        })
        .onComplete(() => {
          if (this.controls) {
            this.controls.enabled = true;
            this.controls.update();
          }
        })
        .start();
    }
  }

  public pickOctopus(raycaster: THREE.Raycaster, autoFocus: boolean = true): OctopusNodeData | null {
    const octoGroups = Array.from(this.octopuses.values()).map((entry) => entry.group);

    // 1. Recursive intersection across all cephalopod components (mantle, arms, head, eyes, nerves, collider)
    const intersects = raycaster.intersectObjects(octoGroups, true);

    if (intersects.length > 0) {
      for (const hit of intersects) {
        let curr: THREE.Object3D | null = hit.object;
        while (curr) {
          if (curr.userData && curr.userData.octopusId !== undefined) {
            const octoId = curr.userData.octopusId as number;
            const entry = this.octopuses.get(octoId);
            if (entry) {
              if (autoFocus) {
                this.focusOnOctopus(octoId);
              }
              return entry.data;
            }
          }
          curr = curr.parent;
        }
      }
    }
    return null;
  }

  private connectTelemetryWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host || 'localhost:8088';
    const wsUrl = `${protocol}//${host}/ws/telemetry`;

    try {
      this.ws = new WebSocket(wsUrl);
      this.ws.onopen = () => {
        this.reconnectController.recordSuccess();
      };
      this.ws.onmessage = (msg) => {
        const res = parseTelemetryMessage(msg.data);
        if (res.success && res.data) {
          this.handleTelemetryEvent(res.data);
        }
      };
      this.ws.onclose = () => {
        this.reconnectController.schedule(() => this.connectTelemetryWebSocket());
      };
    } catch {
      this.reconnectController.schedule(() => this.connectTelemetryWebSocket());
    }
  }

  public handleTelemetryEvent(evt: any) {
    if (this.onTelemetryEvent) {
      this.onTelemetryEvent(evt);
    }
    if (evt.type === 'THEME_CHANGE' || evt.event_type === 'THEME_CHANGE') {
      const tokens = evt.tokens;
      if (tokens) {
        const root = document.documentElement;
        if (tokens.primary_hex) root.style.setProperty('--accent-cyan', tokens.primary_hex);
        if (tokens.secondary_hex) root.style.setProperty('--accent-purple', tokens.secondary_hex);
        if (tokens.accent_hex) root.style.setProperty('--accent-blue', tokens.accent_hex);
        if (tokens.success_hex) root.style.setProperty('--accent-green', tokens.success_hex);
        if (tokens.warning_hex) root.style.setProperty('--accent-amber', tokens.warning_hex);
        if (tokens.danger_hex) root.style.setProperty('--accent-rose', tokens.danger_hex);
        if (tokens.bg_hex) {
          root.style.setProperty('--bg-space', tokens.bg_hex);
          if (this.scene) {
            this.scene.background = new THREE.Color(tokens.bg_hex);
            if (this.scene.fog) {
              (this.scene.fog as any).color.set(tokens.bg_hex);
            }
          }
        }
      }
      return;
    }

    if (evt.morphology) {
      if (evt.morphology === 'aiml_research' && this.domainMode !== 'AIML') {
        this.setDomainMode('AIML');
      } else if (evt.morphology === 'software_dev' && this.domainMode !== 'SOFTWARE') {
        this.setDomainMode('SOFTWARE');
      } else if (evt.morphology === 'fullstack_ai' && this.domainMode !== 'DUAL') {
        this.setDomainMode('DUAL');
      }
    }

    if (evt.payload && Array.isArray((evt.payload as any).arms)) {
      updateArmProfilesFromGuild((evt.payload as any).arms);
    } else if (evt.payload && Array.isArray((evt.payload as any).arm_colors)) {
      updateArmProfilesFromGuild(
        ((evt.payload as any).arm_colors as string[]).map((c: string, idx: number) => ({
          id: idx,
          colorHex: c,
        }))
      );
    }

    if (evt.event_type === 'LIVE_SERVICE_READY' || evt.service_url) {
      if (this.onLiveServiceReady) {
        this.onLiveServiceReady(evt);
      }
    }

    if (evt.mode === 'dry_run' || evt.mode === 'DRY_RUN') {
      let badge = document.getElementById('dry-run-indicator-badge');
      if (!badge) {
        badge = document.createElement('div');
        badge.id = 'dry-run-indicator-badge';
        badge.textContent = 'DRY-RUN';
        badge.style.position = 'fixed';
        badge.style.top = '14px';
        badge.style.left = '50%';
        badge.style.transform = 'translateX(-50%)';
        badge.style.background = 'rgba(234, 179, 8, 0.18)';
        badge.style.color = '#FACC15';
        badge.style.border = '1px solid #EAB308';
        badge.style.borderRadius = '4px';
        badge.style.padding = '3px 10px';
        badge.style.fontSize = '11px';
        badge.style.fontWeight = '700';
        badge.style.letterSpacing = '1px';
        badge.style.zIndex = '99999';
        badge.style.pointerEvents = 'none';
        badge.style.fontFamily = 'monospace';
        document.body.appendChild(badge);
      }
    }

    const octId = evt.octopus_id ?? 0;
    const entry = this.octopuses.get(octId);
    if (!entry) return;

    entry.data.status = evt.status || 'ACTIVE';
    entry.data.currentAction = evt.summary || entry.data.coreRole;
    entry.data.progressPct = evt.progress_pct || entry.data.progressPct;
    entry.data.surprise = evt.surprise ?? entry.data.surprise;

    // Fire real-time action potential cascades on active arms
    const activeArm = evt.arm_id ?? Math.floor(Math.random() * 8);
    entry.signalPropagator.triggerArmAxialStream(activeArm, false, entry.data.colorHex);

    // If high surprise / escalation, trigger shockwave flash
    if (entry.data.surprise > entry.data.threshold) {
      entry.signalPropagator.stimulusOrigin.set(0, 8, 0);
      entry.signalPropagator.stimulusWaveRadius = 0.1;
      entry.signalPropagator.stimulusIntensity = 1.0;
    }

    // Fire extra photon packet along connected synaptic beams
    for (const beam of this.synapticBeams) {
      if (beam.sourceId === octId || beam.targetId === octId) {
        this.spawnPhotonPacket(beam.curve, entry.data.colorHex);
      }
    }

    this.updateHUDCard(entry.data);
  }

  private updateHUDCard(data: OctopusNodeData) {
    const card = document.getElementById(`octo-card-${data.id}`);
    if (!card) return;

    const actionEl = card.querySelector('div:nth-child(3)') as HTMLElement;
    if (actionEl) actionEl.textContent = data.currentAction;

    const progressBar = card.querySelector('div:last-child div') as HTMLElement;
    if (progressBar) progressBar.style.width = `${data.progressPct}%`;
  }

  public animate(delta: number) {
    const elapsedTime = performance.now() * 0.001;
    const reduced = isReducedMotion();

    // 1. Slow cosmic orbit rotation of the entire constellation (pauses during close-up inspection or reduced motion)
    if (!this.isOctopusFocused && !reduced) {
      this.group.rotation.y += delta * 0.018;
    }

    // 2. Animate EVERY Cephalopod: biological mantle breathing, fluid tentacle ripple, action potentials
    this.octopuses.forEach((entry, id) => {
      // Biological mantle breathing & 8-tentacle ripple (skip dynamic deformation if reduced motion is requested)
      if (!reduced) {
        entry.anatomicalMesh.update(elapsedTime, id * 0.78);
        entry.group.position.y = entry.basePosition.y + Math.sin(elapsedTime * 1.4 + id * 0.8) * 2.2;
      } else {
        entry.group.position.y = entry.basePosition.y;
      }

      // Update Neural Network GPU Shaders
      entry.neuralNetwork.update(
        elapsedTime,
        entry.signalPropagator.stimulusOrigin,
        entry.signalPropagator.stimulusWaveRadius,
        entry.signalPropagator.stimulusIntensity,
        this.camera
      );

      // Update traveling action potentials and impulses
      entry.signalPropagator.update(delta, 1.0);

      // Spontaneous living neural pulses
      entry.spontaneousTimer += delta;
      if (entry.spontaneousTimer > 2.8 + (id % 3) * 0.5) {
        entry.spontaneousTimer = 0;
        entry.signalPropagator.triggerSpontaneousActivity();
      }
    });

    // 3. Move photon energy packets along synaptic beams
    for (let i = this.energyPackets.length - 1; i >= 0; i--) {
      const packet = this.energyPackets[i];
      packet.progress += packet.speed;
      if (packet.progress >= 1.0) {
        packet.progress = 0;
      }
      const pt = packet.curve.getPointAt(packet.progress);
      packet.mesh.position.copy(pt);
    }

    // 4. Update 2D Screen Positions of HUD Badges
    this.updateBadgeScreenPositions();
  }

  private updateBadgeScreenPositions() {
    if (!this.hudOverlayContainer) return;
    const tempV = new THREE.Vector3();

    this.octopuses.forEach((entry) => {
      const card = document.getElementById(`octo-card-${entry.data.id}`);
      if (!card) return;

      entry.group.getWorldPosition(tempV);
      tempV.y += 24; // Place badge comfortably above the cephalopod head
      tempV.project(this.camera);

      // Check if behind camera
      if (tempV.z > 1.0) {
        card.style.display = 'none';
        return;
      }

      card.style.display = 'block';
      const x = (tempV.x * 0.5 + 0.5) * window.innerWidth;
      const y = (-(tempV.y * 0.5) + 0.5) * window.innerHeight;

      card.style.left = `${x}px`;
      card.style.top = `${y}px`;
    });
  }
}
