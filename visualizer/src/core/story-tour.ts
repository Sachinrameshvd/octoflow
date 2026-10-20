/** Interactive Guided Story & Animated Tour of Cephalopod Neurobiology.
 * Implements a 7-chapter cinematic walkthrough demonstrating how the entire octopus
 * distributed nervous system operates across arms, ring, and central brain.
 */

import * as THREE from 'three';
import type { CameraController } from './camera-controller';
import type { NeuralNetworkMesh } from '../visual/neural-network';
import type { SignalPropagator } from '../visual/signal-propagator';

export interface TourChapter {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  category: 'DISTRIBUTED' | 'REFLEX' | 'COORDINATION' | 'ASCENDING' | 'CENTRAL' | 'EXECUTIVE' | 'FULL_SYSTEM';
  cameraPos: THREE.Vector3;
  cameraTarget: THREE.Vector3;
  durationSeconds: number;
  highlightRegionId: string | null;
  highlightArmIndex: number | null;
  fiberGlow: number;
  neuropilOpacity: number;
  punctaAlpha: number;
  signalTriggerAction?: (propagator: SignalPropagator, network: NeuralNetworkMesh) => void;
  narration: string[];
  keyConcept: string;
  flowSteps: { step: string; type: 'sensory' | 'inter' | 'motor' | 'central' }[];
}

export class StoryTourManager {
  private cameraController: CameraController;
  private neuralNetwork: NeuralNetworkMesh;
  private signalPropagator: SignalPropagator;

  public chapters: TourChapter[] = [];
  public currentChapterIndex = 0;
  private isRunning = false;
  private isPaused = false;
  private chapterTimeElapsed = 0;
  private playbackSpeed = 1.0;
  private pulseIntervalTimer: number | null = null;

  public onChapterChange?: (chapter: TourChapter, index: number, total: number) => void;
  public onTimeUpdate?: (elapsed: number, duration: number, percent: number) => void;
  public onTourEnd?: () => void;

  constructor(
    cameraController: CameraController,
    neuralNetwork: NeuralNetworkMesh,
    signalPropagator: SignalPropagator
  ) {
    this.cameraController = cameraController;
    this.neuralNetwork = neuralNetwork;
    this.signalPropagator = signalPropagator;
    this.buildChapters();
  }

  private buildChapters() {
    this.chapters = [
      // CHAPTER 1
      {
        id: 'distributed_architecture',
        number: 1,
        title: 'The Distributed Nervous System',
        subtitle: 'The 3/5ths Rule & Arm Sovereignty',
        category: 'DISTRIBUTED',
        cameraPos: new THREE.Vector3(0, 48, 88),
        cameraTarget: new THREE.Vector3(0, -6, 0),
        durationSeconds: 12,
        highlightRegionId: null,
        highlightArmIndex: null,
        fiberGlow: 1.0,
        neuropilOpacity: 0.35,
        punctaAlpha: 0.9,
        keyConcept: '60-70% of all 500M neurons reside inside the 8 arms, not the head.',
        flowSteps: [
          { step: 'Central Brain (~150M)', type: 'central' },
          { step: 'Brachial Ring (~10M)', type: 'inter' },
          { step: '8 Axial Cords (~350M)', type: 'motor' },
          { step: '1,600+ Sucker Ganglia', type: 'sensory' },
        ],
        narration: [
          'Unlike vertebrates whose brain centralizes all sensory processing and motor execution, the octopus operates as a decentralized network of semi-autonomous intelligences.',
          'Each of the 8 arms contains an Axial Nerve Cord packed with cortical and motor neurons, operating alongside hundreds of autonomous sucker micro-ganglia.',
        ],
        signalTriggerAction: (prop, net) => {
          // Fire ambient wandering pulses across all 8 arms
          const armNodes = net.connectome.armNodeIndices;
          for (let a = 0; a < 8; a++) {
            const nodes = armNodes[a];
            if (nodes.length > 0) {
              const start = nodes[Math.floor(Math.random() * nodes.length)];
              prop.triggerNeuronMicrocircuitCascade(start, 12);
            }
          }
        },
      },

      // CHAPTER 2
      {
        id: 'sucker_reflex',
        number: 2,
        title: 'Autonomous Sucker-Level Reflex',
        subtitle: 'Chemotactile Sensing & Local Grip',
        category: 'REFLEX',
        cameraPos: new THREE.Vector3(26, -16, 22),
        cameraTarget: new THREE.Vector3(22, -18, 16),
        durationSeconds: 14,
        highlightRegionId: 'sucker_ganglia',
        highlightArmIndex: 1,
        fiberGlow: 1.3,
        neuropilOpacity: 0.2,
        punctaAlpha: 1.2,
        keyConcept: 'Suckers taste, touch, and grip with zero latency without querying the central head.',
        flowSteps: [
          { step: 'Chemotactile Receptors', type: 'sensory' },
          { step: 'Sucker Ganglion Hub', type: 'inter' },
          { step: 'Axial Cord Neuropil', type: 'inter' },
          { step: 'Intramuscular Flexion', type: 'motor' },
        ],
        narration: [
          'Tens of thousands of chemotactile receptor cells encircle each sucker rim, tasting amino acids and sensing micro-textures in the water.',
          'Sensory input flows into the local Sucker Ganglion, triggering instant reflex arcs to intramuscular nerve cords. The arm wraps and grips prey in milliseconds without waiting for central brain commands.',
        ],
        signalTriggerAction: (prop) => {
          // Trigger sucker sensory reflex pathway
          prop.triggerPathway('touch_sucker');
        },
      },

      // CHAPTER 3
      {
        id: 'ring_coordination',
        number: 3,
        title: 'Inter-Arm Coordination Ring',
        subtitle: 'The Interbrachial Nerve Commissure',
        category: 'COORDINATION',
        cameraPos: new THREE.Vector3(0, -1, 38),
        cameraTarget: new THREE.Vector3(0, -5, 0),
        durationSeconds: 13,
        highlightRegionId: 'brachial_nerve_ring',
        highlightArmIndex: null,
        fiberGlow: 1.2,
        neuropilOpacity: 0.45,
        punctaAlpha: 1.0,
        keyConcept: 'Adjacent arms synchronize walking and prey-handover through a direct circular ring.',
        flowSteps: [
          { step: 'Arm 1 Tactile', type: 'sensory' },
          { step: 'Interbrachial Commissure', type: 'inter' },
          { step: 'Adjacent Arm Cords', type: 'inter' },
          { step: 'Synchronized Crawl', type: 'motor' },
        ],
        narration: [
          'Encircling the base of the esophagus and beak lies the Interbrachial Nerve Ring—a massive neural highway bridging all 8 arm bases together.',
          'Proprioceptive signals and tactile discoveries pass laterally between neighboring arms through this commissural loop, enabling seamless crawling and multi-arm prey manipulation without head intervention.',
        ],
        signalTriggerAction: (prop) => {
          prop.triggerPathway('arm_tactile_transfer');
        },
      },

      // CHAPTER 4
      {
        id: 'ascending_surprises',
        number: 4,
        title: 'Event-Driven Ascending Signals',
        subtitle: 'Sparse Bandwidth & Surprise Summaries',
        category: 'ASCENDING',
        cameraPos: new THREE.Vector3(12, 12, 42),
        cameraTarget: new THREE.Vector3(4, 0, 0),
        durationSeconds: 13,
        highlightRegionId: 'axial_nerve_cords',
        highlightArmIndex: 0,
        fiberGlow: 1.1,
        neuropilOpacity: 0.3,
        punctaAlpha: 1.1,
        keyConcept: 'Arms only send compressed surprise summaries upward when local predictions fail.',
        flowSteps: [
          { step: 'Local Forward Model', type: 'inter' },
          { step: 'High Surprise Event', type: 'sensory' },
          { step: 'Ascending Axial Tract', type: 'inter' },
          { step: 'Subesophageal Intake', type: 'central' },
        ],
        narration: [
          'Streaming raw sensory data from 1,600+ suckers would overwhelm any central processor. Instead, each arm runs a local predictive forward model.',
          'Only when an arm encounters an unexpected load, chemical anomaly, or high surprise does it fire an ascending summary up the axial cord to alert the central brain.',
        ],
        signalTriggerAction: (prop, net) => {
          // Send ascending burst from arm 0 tip to central brain
          const arm0Nodes = net.connectome.armNodeIndices[0];
          if (arm0Nodes.length > 0) {
            const tipNode = arm0Nodes[arm0Nodes.length - 1];
            prop.triggerNeuronMicrocircuitCascade(tipNode, 45);
          }
        },
      },

      // CHAPTER 5
      {
        id: 'vertical_lobe_consolidation',
        number: 5,
        title: 'Central Memory & Coalition Attention',
        subtitle: 'Vertical Lobe Associative Matrices',
        category: 'CENTRAL',
        cameraPos: new THREE.Vector3(0, 18, 22),
        cameraTarget: new THREE.Vector3(0, 6, 0),
        durationSeconds: 15,
        highlightRegionId: 'vertical_lobe',
        highlightArmIndex: null,
        fiberGlow: 1.25,
        neuropilOpacity: 0.55,
        punctaAlpha: 1.2,
        keyConcept: '25M amacrine interneurons bind visual and tactile inputs for associative learning.',
        flowSteps: [
          { step: 'Optic Lobe Visuals', type: 'sensory' },
          { step: 'Superior Frontal Lobe', type: 'inter' },
          { step: 'Vertical Lobe (MSF/VL)', type: 'central' },
          { step: 'Long-Term Memory', type: 'central' },
        ],
        narration: [
          'Inside the dorsal skull sits the Vertical Lobe System (MSF/VL)—the cephalopod equivalent of the vertebrate cerebral cortex and hippocampus.',
          'Containing ~25 million micro-amacrine interneurons, it performs sparse coalition attention over reporting arms, binding visual scene recognition with tactile memory for long-term associative learning.',
        ],
        signalTriggerAction: (prop) => {
          prop.triggerPathway('visual_hunt');
        },
      },

      // CHAPTER 6
      {
        id: 'executive_descending',
        number: 6,
        title: 'Descending High-Level Motor Commands',
        subtitle: 'Subesophageal Motor Roots & Delegation',
        category: 'EXECUTIVE',
        cameraPos: new THREE.Vector3(0, -6, 32),
        cameraTarget: new THREE.Vector3(0, -4, 0),
        durationSeconds: 13,
        highlightRegionId: 'subesophageal_mass',
        highlightArmIndex: null,
        fiberGlow: 1.2,
        neuropilOpacity: 0.45,
        punctaAlpha: 1.1,
        keyConcept: 'The brain sends abstract behavioral goals; arms solve the infinite kinematics.',
        flowSteps: [
          { step: 'Executive Intent', type: 'central' },
          { step: 'Subesophageal Mass', type: 'central' },
          { step: 'Brachial Motor Roots', type: 'inter' },
          { step: 'Autonomous Arm Strike', type: 'motor' },
        ],
        narration: [
          'When deciding to strike, hide, or jet-escape, the Subesophageal Motor Mass fires broad command signals down the brachial nerve roots.',
          'Crucially, the central brain does NOT compute the infinite degrees of freedom of muscular elongation, bending, and torsion. It simply instructs "EXPLORE NORTH" or "ESCAPE", delegating the physics to the arms.',
        ],
        signalTriggerAction: (prop) => {
          prop.triggerPathway('escape_jet');
        },
      },

      // CHAPTER 7
      {
        id: 'full_living_system',
        number: 7,
        title: 'The Living Cephalopod Connectome',
        subtitle: 'Harmonious Multi-Tiered Intelligence',
        category: 'FULL_SYSTEM',
        cameraPos: new THREE.Vector3(0, 42, 85),
        cameraTarget: new THREE.Vector3(0, -4, 0),
        durationSeconds: 16,
        highlightRegionId: null,
        highlightArmIndex: null,
        fiberGlow: 0.95,
        neuropilOpacity: 0.3,
        punctaAlpha: 0.9,
        keyConcept: 'A distributed cognitive architecture: decentralized execution + sparse central memory.',
        flowSteps: [
          { step: '1,600+ Autonomous Suckers', type: 'sensory' },
          { step: '8 Arm Local Planners', type: 'motor' },
          { step: 'Lateral Ring Sync', type: 'inter' },
          { step: 'Sparse Central Memory', type: 'central' },
        ],
        narration: [
          'You are witnessing a complete simulation of the octopus nervous system in real-time.',
          'Autonomous peripheral sensory-motor reflexes, lateral inter-arm coordination, sparse event-triggered communication, and central associative memory working in seamless biological harmony.',
        ],
        signalTriggerAction: (prop) => {
          // Multistage continuous fireworks
          prop.triggerPathway('visual_hunt');
          setTimeout(() => prop.triggerPathway('touch_sucker'), 3000);
          setTimeout(() => prop.triggerPathway('arm_tactile_transfer'), 6000);
        },
      },
    ];
  }

  public startTour() {
    this.isRunning = true;
    this.isPaused = false;
    this.currentChapterIndex = 0;
    this.chapterTimeElapsed = 0;
    this.loadChapter(0);
  }

  public stopTour() {
    this.isRunning = false;
    this.isPaused = false;
    this.clearPulseTimer();
    this.neuralNetwork.setIsolatedRegion(null);
    this.neuralNetwork.setHighlightedArm(null);
    if (this.onTourEnd) this.onTourEnd();
  }

  public togglePlayPause(): boolean {
    this.isPaused = !this.isPaused;
    return this.isPaused;
  }

  public nextChapter() {
    if (this.currentChapterIndex < this.chapters.length - 1) {
      this.currentChapterIndex++;
      this.chapterTimeElapsed = 0;
      this.loadChapter(this.currentChapterIndex);
    } else {
      this.stopTour();
    }
  }

  public prevChapter() {
    if (this.currentChapterIndex > 0) {
      this.currentChapterIndex--;
      this.chapterTimeElapsed = 0;
      this.loadChapter(this.currentChapterIndex);
    }
  }

  public jumpToChapter(index: number) {
    if (index >= 0 && index < this.chapters.length) {
      this.currentChapterIndex = index;
      this.chapterTimeElapsed = 0;
      this.loadChapter(index);
    }
  }

  public setSpeed(speed: number) {
    this.playbackSpeed = speed;
  }

  public setActiveOctopus(neuralNetwork: NeuralNetworkMesh, signalPropagator: SignalPropagator) {
    this.neuralNetwork = neuralNetwork;
    this.signalPropagator = signalPropagator;
  }

  public isTourActive(): boolean {
    return this.isRunning;
  }

  public isTourPaused(): boolean {
    return this.isPaused;
  }

  public getCurrentChapter(): TourChapter {
    return this.chapters[this.currentChapterIndex];
  }

  private loadChapter(index: number) {
    const chapter = this.chapters[index];
    if (!chapter) return;

    this.clearPulseTimer();

    // 1. Animate Camera to Chapter Target (anchored to active octopus)
    const anchor = this.cameraController.anchorPosition;
    this.cameraController.tweenCameraTo(
      chapter.cameraPos.clone().add(anchor),
      chapter.cameraTarget.clone().add(anchor),
      2200
    );

    // 2. Adjust Visualizer Optical Parameters
    this.neuralNetwork.setIsolatedRegion(chapter.highlightRegionId);
    this.neuralNetwork.setHighlightedArm(chapter.highlightArmIndex);
    this.neuralNetwork.setFiberGlow(chapter.fiberGlow);
    this.neuralNetwork.setNeuropilHullOpacity(chapter.neuropilOpacity);
    this.neuralNetwork.setPunctaAlpha(chapter.punctaAlpha);

    // 3. Trigger Chapter Action Potential Cascades
    if (chapter.signalTriggerAction) {
      chapter.signalTriggerAction(this.signalPropagator, this.neuralNetwork);

      // Repeat signals periodically during the chapter
      this.pulseIntervalTimer = window.setInterval(() => {
        if (this.isRunning && !this.isPaused && chapter.signalTriggerAction) {
          chapter.signalTriggerAction(this.signalPropagator, this.neuralNetwork);
        }
      }, 4500);
    }

    // 4. Notify UI
    if (this.onChapterChange) {
      this.onChapterChange(chapter, index, this.chapters.length);
    }
  }

  private clearPulseTimer() {
    if (this.pulseIntervalTimer !== null) {
      clearInterval(this.pulseIntervalTimer);
      this.pulseIntervalTimer = null;
    }
  }

  public update(deltaTime: number) {
    if (!this.isRunning || this.isPaused) return;

    const dt = deltaTime * this.playbackSpeed;
    this.chapterTimeElapsed += dt;

    const chapter = this.chapters[this.currentChapterIndex];
    if (!chapter) return;

    const progress = Math.min(1.0, this.chapterTimeElapsed / chapter.durationSeconds);
    if (this.onTimeUpdate) {
      this.onTimeUpdate(this.chapterTimeElapsed, chapter.durationSeconds, progress);
    }

    // Slow orbit rotation during the chapter to give cinematic feel
    if (this.cameraController) {
      this.cameraController.orbitBy(0.04 * dt, 0.0);
    }

    // Auto advance to next chapter when time expires
    if (this.chapterTimeElapsed >= chapter.durationSeconds) {
      this.nextChapter();
    }
  }
}
