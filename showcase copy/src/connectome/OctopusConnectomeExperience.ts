import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';

import { OctopusConnectomeGenerator } from './octopus-generator';
import type { OctopusConnectomeData } from './octopus-generator';
import {
  NeuronParticleShader,
  SynapticFiberShader,
  SynapticPunctaShader,
  ActionPotentialParticleShader,
} from './shaders';
import { ConsortiumSwarm3D } from './ConsortiumSwarm3D';

export interface CameraWaypoint {
  scrollProgress: number; // 0.0 to 1.0
  position: THREE.Vector3;
  target: THREE.Vector3;
  chapter: string;
  title: string;
}

export const CAMERA_WAYPOINTS: CameraWaypoint[] = [
  {
    scrollProgress: 0.0,
    position: new THREE.Vector3(0, 42, 115),
    target: new THREE.Vector3(0, 0, 0),
    chapter: '01 // AWAKENING',
    title: '500 Million Neurons. Zero Skeleton.',
  },
  {
    scrollProgress: 0.0385,
    position: new THREE.Vector3(24, 28, 65),
    target: new THREE.Vector3(-8, -4, 10),
    chapter: '02 // THE TRAP',
    title: 'Why Centralized AI Collapses at the Edge',
  },
  {
    scrollProgress: 0.0769,
    position: new THREE.Vector3(0, 40, 22),
    target: new THREE.Vector3(0, 16, 0),
    chapter: '03 // THE SECRET',
    title: 'Two-Thirds of the Mind Lives in the Limbs',
  },
  {
    scrollProgress: 0.1154,
    position: new THREE.Vector3(0, 8, 16),
    target: new THREE.Vector3(0, 6, 0),
    chapter: '04 // STRATEGIST',
    title: 'The Central Supraesophageal Ganglion',
  },
  {
    scrollProgress: 0.1538,
    position: new THREE.Vector3(4, 11, 10),
    target: new THREE.Vector3(0, 8.5, 1.5),
    chapter: '05 // MEMORY MATRIX',
    title: 'Vertical Lobe Long-Term Potentiation (LTP)',
  },
  {
    scrollProgress: 0.1923,
    position: new THREE.Vector3(-38, 6, 20),
    target: new THREE.Vector3(-22, 3.5, -0.5),
    chapter: '06 // OPTIC LOBES',
    title: 'Seeing Without Stereopsis (120M+ Somas)',
  },
  {
    scrollProgress: 0.2308,
    position: new THREE.Vector3(38, 6, 20),
    target: new THREE.Vector3(22, 3.5, -0.5),
    chapter: '07 // SURPRISE FILTER',
    title: 'Local Predictive Surprise as the Ultimate Filter',
  },
  {
    scrollProgress: 0.2692,
    position: new THREE.Vector3(0, -14, 20),
    target: new THREE.Vector3(0, -5, 0),
    chapter: '08 // THE MIRACLE',
    title: 'The 22% Bandwidth Bottleneck',
  },
  {
    scrollProgress: 0.3077,
    position: new THREE.Vector3(32, 14, 55),
    target: new THREE.Vector3(0, -4, 0),
    chapter: '09 // THE SWARM',
    title: 'Eight Autonomous Agents, One Body',
  },
  {
    scrollProgress: 0.3462,
    position: new THREE.Vector3(-22, -6, 24),
    target: new THREE.Vector3(0, -5, 0),
    chapter: '10 // SEMANTIC CHATTER',
    title: 'The Secret Communication Lexicon of Arms',
  },
  {
    scrollProgress: 0.3846,
    position: new THREE.Vector3(18, -12, 36),
    target: new THREE.Vector3(8, -8, 18),
    chapter: '11 // COALITIONS',
    title: 'Dynamic Multi-Head Attention Binding',
  },
  {
    scrollProgress: 0.4231,
    position: new THREE.Vector3(30, -16, 28),
    target: new THREE.Vector3(20, -18, 12),
    chapter: '12 // LATERAL RING',
    title: 'The Interbrachial Commissure Highway',
  },
  {
    scrollProgress: 0.4615,
    position: new THREE.Vector3(26, -8, 30),
    target: new THREE.Vector3(10, -4, 10),
    chapter: '13 // ZERO-SHOT RECOVERY',
    title: 'Sever a Limb. Zero Downtime.',
  },
  {
    scrollProgress: 0.5000,
    position: new THREE.Vector3(-26, -26, 60),
    target: new THREE.Vector3(-22, -28, 48),
    chapter: '14 // AXIAL HIGHWAY',
    title: 'Arm #3 Continuum and 28 Sucker Ganglia',
  },
  {
    scrollProgress: 0.5385,
    position: new THREE.Vector3(-20.5, -24.5, 72.0),
    target: new THREE.Vector3(-28.12, -29.75, 55.65),
    chapter: '15 // MICRON PRECISION',
    title: 'Sucker Receptor #12370 Microcircuit',
  },
  {
    scrollProgress: 0.5769,
    position: new THREE.Vector3(44, -18, 26),
    target: new THREE.Vector3(14, -14, 0),
    chapter: '16 // CONTINUUM PHYSICS',
    title: 'Muscular Hydrostat Constant-Volume Law',
  },
  {
    scrollProgress: 0.6154,
    position: new THREE.Vector3(0, -48, 38),
    target: new THREE.Vector3(0, 6, 0),
    chapter: '17 // CURRICULUM SURGE',
    title: '+234% Reward Surge & Multi-Arm Lock',
  },
  {
    scrollProgress: 0.6538,
    position: new THREE.Vector3(0, 18, 105),
    target: new THREE.Vector3(0, -4, 0),
    chapter: '18 // PRODUCTION PROOF',
    title: 'Engineered from First Principles',
  },
  // Slides 19 - 26: The 8 Octopuses One-by-One in 3D (Calibrated Left-Card / Right-Octopus Framing)
  {
    scrollProgress: 0.6923,
    position: new THREE.Vector3(-30.0, -18.0, 318.0),
    target: new THREE.Vector3(-30.0, -24.0, 220.0),
    chapter: '19 // OCTOPUS 1',
    title: 'System Architect & Data Engineer',
  },
  {
    scrollProgress: 0.7308,
    position: new THREE.Vector3(203.6, -5.7, 246.1),
    target: new THREE.Vector3(134.4, -11.7, 176.8),
    chapter: '20 // OCTOPUS 2',
    title: 'Database & Schemas / Model Architect',
  },
  {
    scrollProgress: 0.7692,
    position: new THREE.Vector3(318.0, 24.0, 30.0),
    target: new THREE.Vector3(220.0, 18.0, 30.0),
    chapter: '21 // OCTOPUS 3',
    title: 'Backend API & Training / Loss Loop',
  },
  {
    scrollProgress: 0.8077,
    position: new THREE.Vector3(246.1, 53.7, -203.6),
    target: new THREE.Vector3(176.8, 47.7, -134.4),
    chapter: '22 // OCTOPUS 4',
    title: 'Frontend Client & Evaluation Benchmark',
  },
  {
    scrollProgress: 0.8462,
    position: new THREE.Vector3(30.0, 66.0, -318.0),
    target: new THREE.Vector3(30.0, 60.0, -220.0),
    chapter: '23 // OCTOPUS 5',
    title: 'State & Caching / HPO Hyperparameter Tuner',
  },
  {
    scrollProgress: 0.8846,
    position: new THREE.Vector3(-203.6, 53.7, -246.1),
    target: new THREE.Vector3(-134.4, 47.7, -176.8),
    chapter: '24 // OCTOPUS 6',
    title: 'QA Test Harness & Model Quantization / ONNX',
  },
  {
    scrollProgress: 0.9231,
    position: new THREE.Vector3(-318.0, 24.0, -30.0),
    target: new THREE.Vector3(-220.0, 18.0, -30.0),
    chapter: '25 // OCTOPUS 7',
    title: 'Security AST Guard & Inference Serving',
  },
  {
    scrollProgress: 0.9615,
    position: new THREE.Vector3(-246.1, -5.7, 203.6),
    target: new THREE.Vector3(-176.8, -11.7, 134.4),
    chapter: '26 // OCTOPUS 8',
    title: 'DevOps Live Ignition & ML Governance',
  },
  // Slide 27: The Grand Finale: All 8 Octopuses Working Together (Tiered 3D Amphitheater)
  {
    scrollProgress: 1.0,
    position: new THREE.Vector3(0, 160, 440),
    target: new THREE.Vector3(0, -5, 0),
    chapter: '27 // THE 8-OCTOPUS LIVING SWARM',
    title: 'All 8 Octopuses Working in 3D Unison',
  },
];

export class OctopusConnectomeExperience {
  private container: HTMLElement;
  public scene: THREE.Scene;
  public camera: THREE.PerspectiveCamera;
  public renderer: THREE.WebGLRenderer;
  public composer: EffectComposer;
  public controls: OrbitControls;

  public connectomeData: OctopusConnectomeData;
  private pointsMesh: THREE.Points;
  private linesMesh: THREE.LineSegments;
  private punctaMesh: THREE.Points;
  private signalPoints: THREE.Points;

  private pointsMaterial: THREE.ShaderMaterial;
  private linesMaterial: THREE.ShaderMaterial;
  private punctaMaterial: THREE.ShaderMaterial;
  private signalMaterial: THREE.ShaderMaterial;

  // 3D Micron Reticle around Sucker #12370
  private reticleGroup: THREE.Group;
  private reticleRing: THREE.Mesh;
  private reticleCore: THREE.Mesh;

  // Multi-Arm Amputation Tracking
  public amputatedArms = new Set<number>();

  // Muscular Hydrostat Parameters
  public hydrostatElongation = 1.0;

  // Action Potential Streaming
  private signalPositions: Float32Array;
  private signalColors: Float32Array;
  private signalLives: Float32Array;
  private maxSignals = 4000;
  private activePackets: {
    armIdx: number;
    segIdx: number;
    progress: number;
    speed: number;
    color: THREE.Color;
  }[] = [];

  private clock = new THREE.Clock();
  private scrollProgress = 0.0;
  private targetScrollProgress = 0.0;
  private isFreeOrbit = false;
  private isDestroyed = false;
  private animId: number | null = null;

  // Dynamic Camera Interpolation
  private currentCamPos = new THREE.Vector3(0, 42, 115);
  private currentCamTarget = new THREE.Vector3(0, 0, 0);

  // 3D Multi-Octopus Swarm & Synaptic Bus
  public swarm3D: ConsortiumSwarm3D;
  public currentSlideIndex = 0;

  // Callbacks
  public onTelemetryUpdate?: (camPos: THREE.Vector3, scrollP: number, activeSignals: number) => void;
  public onSynapticPulse?: () => void;

  constructor(container: HTMLElement) {
    this.container = container;

    // 1. Scene, Camera, Renderer
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x020617);
    this.scene.fog = new THREE.FogExp2(0x020617, 0.0016);

    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;

    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.copy(this.currentCamPos);

    this.renderer = new THREE.WebGLRenderer({
      antialias: false,
      powerPreference: 'high-performance',
      alpha: false,
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;
    this.container.appendChild(this.renderer.domElement);

    // 2. Cinema-Grade Post-Processing Bloom
    const renderPass = new RenderPass(this.scene, this.camera);
    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(width, height),
      1.55, // strength
      0.48, // radius
      0.20  // threshold
    );
    const outputPass = new OutputPass();

    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(renderPass);
    this.composer.addPass(bloomPass);
    this.composer.addPass(outputPass);

    // 3. Orbit Controls (Unbounded distance & smooth damping)
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.maxDistance = 2000;
    this.controls.minDistance = 2;
    this.controls.enabled = false;

    // 4. Synthesize Full Biological Connectome (10,480 Neurons)
    const generator = new OctopusConnectomeGenerator();
    this.connectomeData = generator.generate(1.0);

    const numNodes = this.connectomeData.nodes.length;
    const numFibers = this.connectomeData.fibers.length;

    // A. Points Mesh
    const pointsGeo = new THREE.BufferGeometry();
    pointsGeo.setAttribute('position', new THREE.BufferAttribute(this.connectomeData.nodePositions, 3));
    pointsGeo.setAttribute('color', new THREE.BufferAttribute(this.connectomeData.nodeColors, 3));
    pointsGeo.setAttribute('aSize', new THREE.BufferAttribute(this.connectomeData.nodeSizes, 1));
    pointsGeo.setAttribute('aPhase', new THREE.BufferAttribute(this.connectomeData.nodePhases, 1));
    pointsGeo.setAttribute('aHighlightRole', new THREE.BufferAttribute(new Float32Array(numNodes), 1));

    const regionIndices = new Float32Array(numNodes);
    const armIndices = new Float32Array(numNodes);
    const nodeIdxArray = new Float32Array(numNodes);

    for (let i = 0; i < numNodes; i++) {
      armIndices[i] = this.connectomeData.nodes[i].armIndex;
      nodeIdxArray[i] = i;
    }
    pointsGeo.setAttribute('aRegionIndex', new THREE.BufferAttribute(regionIndices, 1));
    pointsGeo.setAttribute('aArmIndex', new THREE.BufferAttribute(armIndices, 1));
    pointsGeo.setAttribute('aNodeIndex', new THREE.BufferAttribute(nodeIdxArray, 1));

    this.pointsMaterial = new THREE.ShaderMaterial({
      vertexShader: NeuronParticleShader.vertexShader,
      fragmentShader: NeuronParticleShader.fragmentShader,
      vertexColors: true,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uTime: { value: 0.0 },
        uActivityIntensity: { value: 1.0 },
        uIsolatedRegionIndex: { value: -1.0 },
        uHighlightedArmIndex: { value: -1.0 },
        uStimulusWaveRadius: { value: -999.0 },
        uStimulusOrigin: { value: new THREE.Vector3(0, 0, 0) },
        uStimulusIntensity: { value: 0.0 },
        uSelectedNodeIndex: { value: -1.0 },
      },
    });
    this.pointsMesh = new THREE.Points(pointsGeo, this.pointsMaterial);
    this.scene.add(this.pointsMesh);

    // B. Synaptic Filament Lines Mesh
    const linesGeo = new THREE.BufferGeometry();
    linesGeo.setAttribute('position', new THREE.BufferAttribute(this.connectomeData.fiberLinePositions, 3));
    linesGeo.setAttribute('color', new THREE.BufferAttribute(this.connectomeData.fiberLineColors, 3));
    linesGeo.setAttribute('aFiberHighlight', new THREE.BufferAttribute(new Float32Array(numFibers * 2), 1));

    this.linesMaterial = new THREE.ShaderMaterial({
      vertexShader: SynapticFiberShader.vertexShader,
      fragmentShader: SynapticFiberShader.fragmentShader,
      vertexColors: true,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uTime: { value: 0.0 },
        uFiberAlpha: { value: 0.44 },
        uIsolatedRegionIndex: { value: -1.0 },
        uHighlightedArmIndex: { value: -1.0 },
      },
    });
    this.linesMesh = new THREE.LineSegments(linesGeo, this.linesMaterial);
    this.scene.add(this.linesMesh);

    // C. Puncta Clouds
    const punctaGeo = new THREE.BufferGeometry();
    punctaGeo.setAttribute('position', new THREE.BufferAttribute(this.connectomeData.punctaPositions, 3));
    punctaGeo.setAttribute('color', new THREE.BufferAttribute(this.connectomeData.punctaColors, 3));

    this.punctaMaterial = new THREE.ShaderMaterial({
      vertexShader: SynapticPunctaShader.vertexShader,
      fragmentShader: SynapticPunctaShader.fragmentShader,
      vertexColors: true,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uTime: { value: 0.0 },
        uPunctaSize: { value: 2.4 },
        uPunctaAlpha: { value: 0.38 },
        uIsolatedRegionIndex: { value: -1.0 },
      },
    });
    this.punctaMesh = new THREE.Points(punctaGeo, this.punctaMaterial);
    this.scene.add(this.punctaMesh);

    // D. Action Potential Particles
    this.signalPositions = new Float32Array(this.maxSignals * 3);
    this.signalColors = new Float32Array(this.maxSignals * 3);
    this.signalLives = new Float32Array(this.maxSignals);

    const signalGeo = new THREE.BufferGeometry();
    signalGeo.setAttribute('position', new THREE.BufferAttribute(this.signalPositions, 3));
    signalGeo.setAttribute('aSignalColor', new THREE.BufferAttribute(this.signalColors, 3));
    signalGeo.setAttribute('aLife', new THREE.BufferAttribute(this.signalLives, 1));

    this.signalMaterial = new THREE.ShaderMaterial({
      vertexShader: ActionPotentialParticleShader.vertexShader,
      fragmentShader: ActionPotentialParticleShader.fragmentShader,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uTime: { value: 0.0 },
      },
    });
    this.signalPoints = new THREE.Points(signalGeo, this.signalMaterial);
    this.scene.add(this.signalPoints);

    // E. 3D Reticle Targeting Sucker Receptor #12370
    this.reticleGroup = new THREE.Group();
    // Position of Sucker #12370 in Arm 3
    this.reticleGroup.position.set(-28.12, -29.75, 55.65);

    const reticleGeo = new THREE.RingGeometry(1.4, 1.65, 32);
    const reticleMat = new THREE.MeshBasicMaterial({
      color: 0xfacc15,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85,
    });
    this.reticleRing = new THREE.Mesh(reticleGeo, reticleMat);
    this.reticleGroup.add(this.reticleRing);

    const coreGeo = new THREE.SphereGeometry(0.35, 16, 16);
    const coreMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    this.reticleCore = new THREE.Mesh(coreGeo, coreMat);
    this.reticleGroup.add(this.reticleCore);

    this.scene.add(this.reticleGroup);

    // F. 3D Multi-Octopus Swarm (Arranged in Orbital Ring R=85)
    this.swarm3D = new ConsortiumSwarm3D();
    this.scene.add(this.swarm3D.group);

    // Seed Initial Continuous Living Action Potentials
    this.seedActionPotentials();

    // Event Listeners
    window.addEventListener('resize', this.onResize);

    // Start Animation Loop
    this.animate();
  }

  private seedActionPotentials() {
    for (let i = 0; i < 60; i++) {
      this.activePackets.push({
        armIdx: i % 8,
        segIdx: 0,
        progress: Math.random(),
        speed: 0.35 + Math.random() * 0.45,
        color: new THREE.Color(i % 2 === 0 ? 0x38bdf8 : 0xc084fc),
      });
    }
  }

  public setScrollProgress(progress: number) {
    this.targetScrollProgress = Math.max(0, Math.min(1, progress));
  }

  public setCurrentSlide(slideIdx: number) {
    this.currentSlideIndex = slideIdx;
  }

  public setFreeOrbit(enabled: boolean) {
    this.isFreeOrbit = enabled;
    this.controls.enabled = enabled;
    document.body.classList.toggle('free-orbit-active', enabled);

    if (enabled) {
      // Synchronize OrbitControls focal target to EXACTLY the current slide / octopus target!
      this.controls.target.copy(this.currentCamTarget);
      this.camera.position.copy(this.currentCamPos);
      this.camera.lookAt(this.currentCamTarget);
      this.controls.update();
    } else {
      // Re-align camera back to the scripted slide waypoint
      this.camera.position.copy(this.currentCamPos);
      this.camera.lookAt(this.currentCamTarget);
      this.controls.target.copy(this.currentCamTarget);
      this.controls.update();
    }
  }

  public triggerShockwave() {
    // 1. Central single octopus shockwave (Slides 01 - 18)
    this.pointsMaterial.uniforms.uStimulusIntensity.value = 1.0;
    this.pointsMaterial.uniforms.uStimulusWaveRadius.value = 0.0;
    this.pointsMaterial.uniforms.uStimulusOrigin.value.set(0, 0, 0);

    // Burst action potentials outward through central connectome
    for (let i = 0; i < 100; i++) {
      this.activePackets.push({
        armIdx: Math.floor(Math.random() * 8),
        segIdx: 0,
        progress: 0.0,
        speed: 0.8 + Math.random() * 0.7,
        color: new THREE.Color(0xfacc15),
      });
    }

    // 2. Swarm 8-Octopus Pulse (Slides 19 - 27)
    if (this.swarm3D) {
      const isIndividualOctoFocus = this.currentSlideIndex >= 18 && this.currentSlideIndex < 26;
      const isFinale = this.currentSlideIndex >= 26;
      if (isIndividualOctoFocus) {
        const octoIdx = this.currentSlideIndex - 18;
        this.swarm3D.triggerPulse(octoIdx);
      } else if (isFinale) {
        this.swarm3D.triggerPulse(-1); // Swarm burst on all 8 octopuses
      } else {
        this.swarm3D.triggerSwarmBurst();
      }
    }

    if (this.onSynapticPulse) this.onSynapticPulse();
  }

  public triggerSuckerCascade() {
    // Fire high-voltage burst directly from Sucker #12370 up along Arm 3 to the Central Brain
    for (let i = 0; i < 25; i++) {
      this.activePackets.push({
        armIdx: 3,
        segIdx: 28,
        progress: 0.0,
        speed: 1.2 + Math.random() * 0.5,
        color: new THREE.Color(0x34d399),
      });
    }
    if (this.onSynapticPulse) this.onSynapticPulse();
  }

  public toggleArmAmputation(armIndex: number): boolean {
    if (this.amputatedArms.has(armIndex)) {
      this.amputatedArms.delete(armIndex);
    } else {
      this.amputatedArms.add(armIndex);
    }
    return this.amputatedArms.has(armIndex);
  }

  public setHydrostatScale(scale: number) {
    this.hydrostatElongation = scale;
  }

  private interpolateCamera(t: number) {
    let idx = 0;
    while (idx < CAMERA_WAYPOINTS.length - 2 && CAMERA_WAYPOINTS[idx + 1].scrollProgress < t) {
      idx++;
    }

    const p0 = CAMERA_WAYPOINTS[idx];
    const p1 = CAMERA_WAYPOINTS[idx + 1];

    const segmentDuration = p1.scrollProgress - p0.scrollProgress;
    const localT = Math.max(0, Math.min(1, segmentDuration > 0.0001 ? (t - p0.scrollProgress) / segmentDuration : 0));
    const smoothT = 0.5 - 0.5 * Math.cos(localT * Math.PI);

    this.currentCamPos.lerpVectors(p0.position, p1.position, smoothT);
    this.currentCamTarget.lerpVectors(p0.target, p1.target, smoothT);

    this.camera.position.copy(this.currentCamPos);
    this.camera.lookAt(this.currentCamTarget);
  }

  private onResize = () => {
    if (this.isDestroyed) return;
    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    this.composer.setSize(width, height);
  };

  private animate = () => {
    if (this.isDestroyed) return;
    this.animId = requestAnimationFrame(this.animate);

    const delta = this.clock.getDelta();
    const time = this.clock.getElapsedTime();

    // 1. Smooth Scroll Interpolation (Active Theory Butter Physics)
    this.scrollProgress += (this.targetScrollProgress - this.scrollProgress) * 0.08;

    if (!this.isFreeOrbit) {
      this.interpolateCamera(this.scrollProgress);
    } else {
      this.controls.update();
    }

    // 2. Uniform Time Updates
    this.pointsMaterial.uniforms.uTime.value = time;
    this.linesMaterial.uniforms.uTime.value = time;
    this.punctaMaterial.uniforms.uTime.value = time;
    this.signalMaterial.uniforms.uTime.value = time;

    // 3. Shockwave Expansion
    if (this.pointsMaterial.uniforms.uStimulusIntensity.value > 0.01) {
      this.pointsMaterial.uniforms.uStimulusWaveRadius.value += delta * 50.0;
      this.pointsMaterial.uniforms.uStimulusIntensity.value -= delta * 0.5;
    }

    // 4. Central Middle Octopus Visibility Management:
    // Slides 01 - 18 (index 0 - 17): fully visible & featured (user rule: "dont change the middle octupus").
    // Slides 19 - 26 (index 18 - 25): hide central middle octopus so it never overlaps or blooms over individual Octo 1 - 8.
    // Slide 27 (index 26, Finale): visible as the core central hub of the 8-octopus swarm.
    const isIndividualOctoFocus = this.currentSlideIndex >= 18 && this.currentSlideIndex < 26;
    const centralOctoVisible = !isIndividualOctoFocus;

    if (this.pointsMesh.visible !== centralOctoVisible) {
      this.pointsMesh.visible = centralOctoVisible;
      this.linesMesh.visible = centralOctoVisible;
      this.punctaMesh.visible = centralOctoVisible;
      this.signalPoints.visible = centralOctoVisible;
    }

    // 4a. Reticle Animation around Sucker #12370 (only visible on Slide 15: Sucker microcircuit)
    if (this.reticleGroup) {
      this.reticleGroup.visible = (this.currentSlideIndex === 14);
    }
    if (this.reticleRing && this.reticleGroup.visible) {
      this.reticleRing.rotation.z += 0.02;
      this.reticleRing.lookAt(this.camera.position);
    }

    // 4b. Update 3D Consortium Swarm & Synaptic Cables
    if (this.swarm3D) {
      this.swarm3D.update(time, delta, this.currentSlideIndex);
    }

    // 5. Action Potential Simulation
    const nodePos = this.connectomeData.nodePositions;
    let signalWriteIdx = 0;

    for (let p = this.activePackets.length - 1; p >= 0; p--) {
      const pkt = this.activePackets[p];

      // If arm is amputated, suppress signals in that arm
      if (this.amputatedArms.has(pkt.armIdx)) {
        pkt.armIdx = (pkt.armIdx + 1) % 8; // Reroute around commissure
        pkt.color = new THREE.Color(0xfab387); // Warning Amber
      }

      pkt.progress += delta * pkt.speed;
      if (pkt.progress >= 1.0) {
        pkt.progress = 0.0;
        pkt.armIdx = Math.floor(Math.random() * 8);
      }

      const armNodes = this.connectomeData.armNodeIndices[pkt.armIdx];
      if (armNodes && armNodes.length > 0) {
        const nodeIndexInArm = Math.floor(pkt.progress * (armNodes.length - 1));
        const realNodeIdx = armNodes[nodeIndexInArm];

        const px = nodePos[realNodeIdx * 3];
        const py = nodePos[realNodeIdx * 3 + 1];
        const pz = nodePos[realNodeIdx * 3 + 2];

        if (signalWriteIdx < this.maxSignals) {
          const i3 = signalWriteIdx * 3;
          this.signalPositions[i3] = px + Math.sin(time * 6.0 + p) * 0.25;
          this.signalPositions[i3 + 1] = py + Math.cos(time * 6.0 + p) * 0.25;
          this.signalPositions[i3 + 2] = pz;

          this.signalColors[i3] = pkt.color.r;
          this.signalColors[i3 + 1] = pkt.color.g;
          this.signalColors[i3 + 2] = pkt.color.b;

          this.signalLives[signalWriteIdx] = 1.0 - pkt.progress * 0.35;
          signalWriteIdx++;
        }
      }
    }

    // Clear unused signals
    for (let i = signalWriteIdx; i < this.maxSignals; i++) {
      this.signalLives[i] = 0.0;
    }

    this.signalPoints.geometry.attributes.position.needsUpdate = true;
    (this.signalPoints.geometry.attributes.aSignalColor as THREE.BufferAttribute).needsUpdate = true;
    (this.signalPoints.geometry.attributes.aLife as THREE.BufferAttribute).needsUpdate = true;

    // Telemetry Callback
    if (this.onTelemetryUpdate) {
      this.onTelemetryUpdate(this.camera.position, this.scrollProgress, signalWriteIdx);
    }

    // Render with Bloom
    this.composer.render();
  };

  public destroy() {
    this.isDestroyed = true;
    if (this.animId !== null) cancelAnimationFrame(this.animId);
    window.removeEventListener('resize', this.onResize);
    if (this.swarm3D) this.swarm3D.destroy();
    this.renderer.dispose();
    this.composer.dispose();
  }
}
