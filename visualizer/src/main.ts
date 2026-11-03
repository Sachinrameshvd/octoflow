/** Main Application Entrypoint for Octopus Connectome 3D Visualizer & Simulator. */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';

import type { NeuronNode, NeuralFiber } from './visual/octopus-generator';
import { NeuralNetworkMesh } from './visual/neural-network';
import { AnatomicalMeshGenerator } from './visual/anatomical-mesh';
import { SignalPropagator } from './visual/signal-propagator';
import { CameraController } from './core/camera-controller';
import { ConnectomeRaycaster } from './core/raycaster';

import { InspectorPanel } from './ui/inspector-panel';
import { HierarchyBreadcrumbs } from './ui/hierarchy-breadcrumbs';
import type { BreadcrumbItem } from './ui/hierarchy-breadcrumbs';
import { SignalTriggerPanel } from './ui/signal-trigger-panel';
import { ControlPanel } from './ui/control-panel';
import type { ControlState } from './ui/control-panel';
import { StoryTourManager } from './core/story-tour';
import { TourHUD } from './ui/tour-hud';
import { NEUROANATOMY_REGIONS } from './data/neuroanatomy';
import { WindowManager } from './ui/window-manager';
import { CognitiveInspector } from './ui/cognitive-inspector';
import { CephalopodConstellationManager } from './visual/constellation';
import { ICONS } from './ui/icons';
import { CephalopodVoiceSystem } from './audio/speech-synthesizer';
import { ManualModal } from './ui/manual-modal';
import { LLMCascadePanel } from './ui/llm-cascade-panel';
import { MotionPolicy } from './a11y/motion-policy';
import { ActivityLogPanel } from './a11y/activity-log-panel';
import { ReceiptPanel } from './ui/receipt-panel';

class OctopusConnectomeApp {
  private container: HTMLElement;
  private scene!: THREE.Scene;
  private camera!: THREE.PerspectiveCamera;
  private renderer!: THREE.WebGLRenderer;
  private composer!: EffectComposer;
  private controls!: OrbitControls;
  private constellation!: CephalopodConstellationManager;
  private voiceSystem!: CephalopodVoiceSystem;
  private manualModal!: ManualModal;
  private activityLogPanel!: ActivityLogPanel;
  private receiptPanel!: ReceiptPanel;

  private neuralNetwork!: NeuralNetworkMesh;
  private anatomicalMesh!: AnatomicalMeshGenerator;
  private signalPropagator!: SignalPropagator;

  private cameraController!: CameraController;
  private raycaster!: ConnectomeRaycaster;

  private inspectorPanel!: InspectorPanel;
  private breadcrumbs!: HierarchyBreadcrumbs;
  private signalPanel!: SignalTriggerPanel;
  private controlPanel!: ControlPanel;
  private storyTourManager!: StoryTourManager;
  private tourHUD!: TourHUD;
  private windowManager!: WindowManager;
  private cognitiveInspector!: CognitiveInspector;
  private llmCascadePanel!: LLMCascadePanel;

  private tooltipElement: HTMLElement;
  private clock = new THREE.Clock();
  private pointerNDC = new THREE.Vector2(-999, -999);
  private customStimulusMode = false;
  public selectedNode: NeuronNode | null = null;
  public selectedFiber: NeuralFiber | null = null;

  constructor() {
    this.container = document.getElementById('canvas-container') || document.body;
    this.tooltipElement = document.getElementById('hover-tooltip') || document.createElement('div');

    // 0. WCAG WebGL Fallback check
    if (!this.checkWebGLSupport()) {
      console.warn('WebGL 3D hardware acceleration is unavailable. Engaging accessible text telemetry mode.');
      this.renderWebGLFallbackNotice();
      this.activityLogPanel = new ActivityLogPanel('activity-log-panel');
      this.activityLogPanel.show();
      this.voiceSystem = new CephalopodVoiceSystem();
      this.initFallbackUI();
      return;
    }

    // 1. Three.js Scene, Camera, WebGLRenderer
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x020617); // Deep space slate
    this.scene.fog = new THREE.FogExp2(0x020617, 0.0035);

    this.camera = new THREE.PerspectiveCamera(
      45,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    this.camera.position.set(0, 140, 260);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.domElement.setAttribute('role', 'img');
    this.renderer.domElement.setAttribute('aria-label', '3D Cephalopod Swarm Connectome visualization');
    this.renderer.domElement.setAttribute('tabindex', '0');

    this.renderer.domElement.addEventListener('webglcontextlost', (e) => {
      e.preventDefault();
      console.warn('WebGL context lost. Falling back to accessible telemetry view.');
      this.renderWebGLFallbackNotice('WebGL context lost. Rendering in accessible non-visual telemetry mode.');
      this.activityLogPanel.show();
    });

    this.container.appendChild(this.renderer.domElement);

    // 1b. Calibrated Post-Processing (Clean, Subtle Bloom & Tone-Mapping)
    const renderPass = new RenderPass(this.scene, this.camera);
    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      0.38, // Subtle, refined glow (not over-bloomed)
      0.25, // Focused radius
      0.70  // High threshold so only active impulses glow
    );
    const outputPass = new OutputPass();

    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(renderPass);
    this.composer.addPass(bloomPass);
    this.composer.addPass(outputPass);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.maxDistance = 2500;
    this.controls.minDistance = 2.0;
    this.controls.minPolarAngle = 0;
    this.controls.maxPolarAngle = Math.PI;
    this.controls.target.set(0, 0, 0);
    this.controls.enablePan = true;
    this.controls.panSpeed = 1.0;
    this.controls.screenSpacePanning = true;
    this.controls.enableRotate = true;
    this.controls.rotateSpeed = 1.0;
    this.controls.enableZoom = true;
    this.controls.zoomSpeed = 1.0;

    // Subtle atmospheric ambient lighting for anatomical silhouettes
    const ambientLight = new THREE.AmbientLight(0x0ea5e9, 0.6);
    this.scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
    directionalLight.position.set(20, 40, 30);
    this.scene.add(directionalLight);

    // 2. Initialize 3D Cephalopod Constellation Swarm (8 Full Biological Cephalopods)
    this.constellation = new CephalopodConstellationManager(this.scene, this.camera, this.controls);
    const activeOcto = this.constellation.getActiveOctopus();

    this.neuralNetwork = activeOcto.neuralNetwork;
    this.anatomicalMesh = activeOcto.anatomicalMesh;
    this.signalPropagator = activeOcto.signalPropagator;

    this.cameraController = new CameraController(this.camera, this.controls);
    this.constellation.setCameraController(this.cameraController);

    this.raycaster = new ConnectomeRaycaster(this.camera, activeOcto.connectomeData);
    this.raycaster.setConnectome(activeOcto.connectomeData, activeOcto.group.position);

    // 3. Initialize UI Components
    this.voiceSystem = new CephalopodVoiceSystem();
    this.activityLogPanel = new ActivityLogPanel('activity-log-panel');
    this.receiptPanel = new ReceiptPanel('token-receipt-modal');
    this.constellation.onTelemetryEvent = (evt) => {
      this.activityLogPanel.recordEvent(evt);
      this.updateScreenReaderSummary(evt);
      if (evt.event_type === 'FINAL_RECEIPT' || evt.type === 'FINAL_RECEIPT') {
        const receiptData = (evt.payload && evt.payload.receipt) || evt.receipt;
        if (receiptData) {
          this.receiptPanel.show(receiptData);
        }
      }
    };
    this.initUI(activeOcto.connectomeData.nodes);

    this.constellation.onSelectOctopus = (data, octo) => {
      this.selectedNode = null;
      this.selectedFiber = null;
      this.neuralNetwork = octo.neuralNetwork;
      this.anatomicalMesh = octo.anatomicalMesh;
      this.signalPropagator = octo.signalPropagator;

      const worldPos = new THREE.Vector3();
      octo.group.getWorldPosition(worldPos);

      // 1. Sync camera anchor to this octopus
      this.cameraController.setAnchor(worldPos);

      // 2. Sync guided tour manager to this octopus
      if (this.storyTourManager) {
        this.storyTourManager.setActiveOctopus(octo.neuralNetwork, octo.signalPropagator);
      }

      // 3. Sync raycasting & inspector to this octopus's local connectome
      this.raycaster.setConnectome(octo.connectomeData, worldPos);
      this.inspectorPanel.setNodesReference(octo.connectomeData.nodes);
      this.inspectorPanel.show();
      this.updateBreadcrumbs('WHOLE_OCTOPUS', `OCTO_${data.id} // ${data.title.toUpperCase()}`);

      // 4. Apply all active visual layer sliders & mode settings to this octopus
      if (this.controlPanel) {
        this.applyControlState(this.controlPanel.getState());
      }

      // 5. Sync Cognitive Inspector target cephalopod
      if (this.cognitiveInspector) {
        this.cognitiveInspector.setActiveOctopus(data.id, data.title, data.colorHex);
      }

      // 6. Speak octopus role & trigger visual neural audio transmission banner
      this.voiceSystem.speakOctopusRole(data.id);
    };

    // 4. Hook all 8 Signal Propagators to UI step callbacks
    this.constellation.octopuses.forEach((octo) => {
      octo.signalPropagator.onStepChange = (_stepIdx, label, desc) => {
        this.signalPanel.setStepProgress(label, desc);
      };
      octo.signalPropagator.onPathwayComplete = () => {
        this.signalPanel.clearProgress();
      };
    });

    // 4. Bind Events & Resize
    this.bindEvents();

    // 5. Start Animation Loop
    this.animate();
  }

  private initUI(nodes: NeuronNode[]) {
    this.inspectorPanel = new InspectorPanel('inspector-panel');
    this.inspectorPanel.setNodesReference(nodes);

    this.breadcrumbs = new HierarchyBreadcrumbs('hierarchy-breadcrumbs');
    this.signalPanel = new SignalTriggerPanel('signal-trigger-panel');
    this.controlPanel = new ControlPanel('control-panel');
    this.llmCascadePanel = new LLMCascadePanel('llm-cascade-panel');
    this.llmCascadePanel.onFailoverSwitch = (_from, _to) => {
      // Pulse 3D action potential wave across the octopus connectome
      this.signalPropagator.triggerPathway('touch_sucker');
    };

    this.storyTourManager = new StoryTourManager(
      this.cameraController,
      this.neuralNetwork,
      this.signalPropagator
    );
    this.tourHUD = new TourHUD(this.storyTourManager, 'tour-hud-container');

    // Initialize Window Manager for dragging, resizing, and minimizing windows
    this.windowManager = new WindowManager();

    const ctrlEl = document.getElementById('control-panel');
    if (ctrlEl) {
      this.windowManager.registerWindow({
        id: 'control-panel',
        element: ctrlEl,
        title: 'System Controls',
        defaultPosition: { top: 76, left: 20 },
        defaultDimensions: { width: 320, maxHeight: window.innerHeight - 215 },
        minWidth: 260,
        maxWidth: 520,
        minHeight: 180,
        maxHeight: window.innerHeight - 80,
      });
    }

    const inspEl = document.getElementById('inspector-panel');
    if (inspEl) {
      this.windowManager.registerWindow({
        id: 'inspector-panel',
        element: inspEl,
        title: 'Neuroanatomy Inspector',
        defaultPosition: { top: 76, right: 20 },
        defaultDimensions: { width: 390, maxHeight: window.innerHeight - 100 },
        minWidth: 300,
        maxWidth: 620,
        minHeight: 180,
        maxHeight: window.innerHeight - 80,
      });
    }

    const sigEl = document.getElementById('signal-trigger-panel');
    if (sigEl) {
      this.windowManager.registerWindow({
        id: 'signal-trigger-panel',
        element: sigEl,
        title: 'Signal Trigger Dock',
        defaultPosition: { bottom: 20, left: 20, right: 20 },
        defaultDimensions: { width: Math.min(window.innerWidth - 40, 1380) },
        minWidth: 320,
        maxWidth: window.innerWidth - 20,
        minHeight: 90,
        maxHeight: 450,
      });
    }

    const tourEl = document.getElementById('tour-hud-container');
    if (tourEl) {
      this.windowManager.registerWindow({
        id: 'tour-hud-container',
        element: tourEl,
        title: 'How The Brain Works Tour HUD',
        defaultPosition: { top: 68, left: Math.max(20, Math.round(window.innerWidth / 2 - 290)) },
        defaultDimensions: { width: 580, maxHeight: window.innerHeight - 90 },
        minWidth: 340,
        maxWidth: 820,
        minHeight: 200,
        maxHeight: window.innerHeight - 60,
      });
    }

    // Cognitive Flow & Problem Solver Window
    this.cognitiveInspector = new CognitiveInspector();
    const cogEl = document.getElementById('cognitive-inspector');
    if (cogEl) {
      this.windowManager.registerWindow({
        id: 'cognitive-inspector',
        element: cogEl,
        title: 'Cognitive Flow & Problem Solver',
        defaultPosition: { top: 76, left: Math.max(20, Math.round(window.innerWidth / 2 - 280)) },
        defaultDimensions: { width: 560, maxHeight: window.innerHeight - 100 },
        minWidth: 380,
        maxWidth: 720,
        minHeight: 220,
        maxHeight: window.innerHeight - 80,
      });
    }

    const btnCognitive = document.getElementById('btn-toggle-cognitive');
    if (btnCognitive) {
      btnCognitive.addEventListener('click', () => {
        this.cognitiveInspector.toggle();
      });
    }

    this.cognitiveInspector.onVisualPulse = (reportingArms, coalitions, highSurpriseArms) => {
      for (const armIdx of reportingArms) {
        this.signalPropagator.triggerArmAxialStream(armIdx, true, '#89b4fa');
      }
      for (const cluster of coalitions) {
        if (cluster.length >= 2) {
          this.signalPropagator.triggerLateralRingPulse(cluster[0], cluster[1], '#cba6f7');
        }
      }
      if (highSurpriseArms.length > 0) {
        this.signalPropagator.stimulusOrigin.set(0, 0, 0);
        this.signalPropagator.stimulusWaveRadius = 0.5;
        this.signalPropagator.stimulusIntensity = 1.6;
      }
    };

    const btnResetLayout = document.getElementById('btn-reset-layout');
    if (btnResetLayout) {
      btnResetLayout.addEventListener('click', () => {
        this.windowManager.resetAll();
      });
    }

    this.tourHUD.onExitTour = () => {
      const sigContainer = document.getElementById('signal-trigger-panel');
      if (sigContainer) sigContainer.style.display = '';
      const ctrlPanel = document.getElementById('control-panel');
      if (ctrlPanel) ctrlPanel.style.display = '';
      this.cameraController.goToWholeOctopus();
      this.updateBreadcrumbs('WHOLE_OCTOPUS');
    };

    this.updateBreadcrumbs('WHOLE_OCTOPUS');

    // Inspector callbacks
    this.inspectorPanel.onIsolateRegion = (regionId) => {
      this.neuralNetwork.setIsolatedRegion(regionId);
    };

    this.inspectorPanel.onFocusCamera = (regionId) => {
      if (regionId === 'vertical_lobe') this.cameraController.goToVerticalLobe();
      else if (regionId === 'optic_lobes') this.cameraController.goToOpticLobe('left');
      else if (regionId === 'subesophageal_mass' || regionId === 'superior_frontal_lobe' || regionId === 'subfrontal_lobe') {
        this.cameraController.goToCentralBrain();
      } else if (regionId === 'axial_nerve_cords' || regionId === 'sucker_ganglia' || regionId === 'intramuscular_cords') {
        this.cameraController.goToArm(0);
      } else {
        this.cameraController.goToWholeOctopus();
      }
    };

    this.inspectorPanel.onFocusNeuron = (node, microZoom) => {
      this.cameraController.goToIndividualNeuron(node.position, microZoom);
      this.updateBreadcrumbs('INDIVIDUAL_NEURON', `Neuron #${node.index}`);
    };

    this.inspectorPanel.onFocusFiber = (src, tgt) => {
      this.cameraController.goToConnectionFiber(src.position, tgt.position);
      this.updateBreadcrumbs('INDIVIDUAL_CONNECTION', `Synapse #${this.selectedFiber ? this.selectedFiber.index : ''}`);
    };

    this.inspectorPanel.onStimulateNode = (nodeIdx) => {
      this.signalPropagator.triggerNeuronMicrocircuitCascade(nodeIdx, 35);
    };

    this.inspectorPanel.onStimulateFiber = (fiberIdx) => {
      this.signalPropagator.triggerSingleFiberStimulus(fiberIdx);
    };

    this.inspectorPanel.onSelectNeuron = (nodeIdx) => {
      const node = this.neuralNetwork.connectome.nodes[nodeIdx];
      if (node) {
        this.selectedNode = node;
        this.selectedFiber = null;
        this.neuralNetwork.setSelectedNeuron(nodeIdx);
        this.inspectorPanel.showNeuron(node);
        this.updateBreadcrumbs('INDIVIDUAL_NEURON', `Neuron #${nodeIdx}`);
      }
    };

    // Signal Panel callbacks
    this.signalPanel.onTriggerPathway = (pathwayId) => {
      this.signalPropagator.triggerPathway(pathwayId);
    };

    this.signalPanel.onToggleFollowSignal = (enabled) => {
      this.cameraController.setNavigationMode(enabled ? 'FOLLOW_SIGNAL' : 'ORBIT');
      this.controlPanel.setNavMode(enabled ? 'FOLLOW_SIGNAL' : 'ORBIT');
    };

    this.signalPanel.onCustomStimulusMode = () => {
      this.customStimulusMode = true;
      this.tooltipElement.textContent = 'Click any 3D neuron to fire action potential';
      this.tooltipElement.classList.remove('hidden');
    };

    this.signalPropagator.onStepChange = (_stepIdx, label, desc) => {
      this.signalPanel.setStepProgress(label, desc);
    };

    this.signalPropagator.onPathwayComplete = () => {
      this.signalPanel.clearProgress();
    };

    // Control Panel callbacks
    this.controlPanel.onStateChange = (state) => {
      this.applyControlState(state);
    };

    this.controlPanel.onSelectPerspectiveAngle = (angleKey) => {
      this.cameraController.setPerspectiveAngle(angleKey as any);
    };

    this.controlPanel.onResetCamera = () => {
      this.cameraController.goToWholeOctopus();
      this.neuralNetwork.setIsolatedRegion(null);
      this.neuralNetwork.setHighlightedArm(null);
      this.neuralNetwork.setSelectedNeuron(null);
      this.neuralNetwork.setSelectedFiber(null);
      this.inspectorPanel.hide();
      this.updateBreadcrumbs('WHOLE_OCTOPUS');
    };

    this.controlPanel.onSelectPresetView = (key) => {
      if (key === 'whole') {
        this.cameraController.goToWholeOctopus();
        this.updateBreadcrumbs('WHOLE_OCTOPUS');
      } else if (key === 'brain') {
        this.cameraController.goToCentralBrain();
        this.inspectorPanel.showRegion('subesophageal_mass');
        this.updateBreadcrumbs('CENTRAL_BRAIN');
      } else if (key === 'vertical') {
        this.cameraController.goToVerticalLobe();
        this.inspectorPanel.showRegion('vertical_lobe');
        this.updateBreadcrumbs('BRAIN_REGION', 'Vertical Lobe');
      } else if (key === 'optic_left') {
        this.cameraController.goToOpticLobe('left');
        this.inspectorPanel.showRegion('optic_lobes');
        this.updateBreadcrumbs('BRAIN_REGION', 'Optic Lobe (L)');
      } else if (key === 'optic_right') {
        this.cameraController.goToOpticLobe('right');
        this.inspectorPanel.showRegion('optic_lobes');
        this.updateBreadcrumbs('BRAIN_REGION', 'Optic Lobe (R)');
      } else if (key === 'arm1') {
        this.cameraController.goToArm(0);
        this.inspectorPanel.showRegion('axial_nerve_cords');
        this.updateBreadcrumbs('ARM', 'Arm 1');
      }
    };

    // Inspector Deep-Link to Manual
    this.inspectorPanel.onOpenManual = (regionId: string) => {
      this.manualModal.open('arms', regionId.includes('arm') ? 'arm0' : 'arm0');
    };

    // Initialize Master Manual Drawer & HUD Trigger
    this.manualModal = new ManualModal();
    const btnManual = document.getElementById('btn-open-manual');
    if (btnManual) {
      btnManual.addEventListener('click', () => {
        this.manualModal.toggle();
      });
    }

    // Connect Simulation Triggers from Web Manual to 3D Neural Canvas
    this.manualModal.onSimulateCommand = (cmd: string) => {
      if (cmd === '/heal') {
        // Pulse Arm 5 (QA) and Arm 2 (Backend) with action potentials
        this.signalPropagator.triggerArmAxialStream(5, true, '#10b981');
        setTimeout(() => this.signalPropagator.triggerArmAxialStream(2, true, '#f59e0b'), 400);
        this.voiceSystem.speakCustom('Self-Healing Loop Active', 'OctoFlow Self-Healing: Arm 5 executing regression triage; Arm 2 applying AST code repairs.');
      } else if (cmd === '/audit') {
        // Sequential pulse across all 8 arms
        for (let i = 0; i < 8; i++) {
          setTimeout(() => this.signalPropagator.triggerArmAxialStream(i, true, '#00f0ff'), i * 150);
        }
        this.voiceSystem.speakCustom('System Audit', 'OctoFlow 100-Point Audit complete. System readiness: Grade A Plus, Apex Cephalopod.');
      } else if (cmd === '/plan') {
        this.signalPropagator.triggerArmAxialStream(0, true, '#a855f7');
        this.voiceSystem.speakCustom('Consortium Plan', 'Architect Arm 0 decomposing mission requirements into dependency DAG.');
      } else {
        // Universal pulse
        this.signalPropagator.stimulusOrigin.set(0, 0, 0);
        this.signalPropagator.stimulusWaveRadius = 0.5;
        this.signalPropagator.triggerArmAxialStream(0, true, '#38bdf8');
      }
    };

    // Connect Voice Narration from Web Manual to Cephalopod Voice System
    this.manualModal.onVoiceNarrate = (title: string, text: string) => {
      this.voiceSystem.speakCustom(title, text);
    };

    if (window.location.search.includes('manual=1')) {
      this.manualModal.open();
    }
  }

  private applyControlState(state: ControlState) {
    this.neuralNetwork.setFiberGlow(state.fiberGlow);
    this.neuralNetwork.setNeuropilHullOpacity(state.neuropilOpacity);
    this.neuralNetwork.setPunctaAlpha(state.punctaAlpha);
    this.neuralNetwork.setPunctaVisible(state.punctaVisible);
    this.neuralNetwork.setNeuralActivity(state.isPaused ? 0.0 : state.activityIntensity);
    this.anatomicalMesh.setOpacity(state.anatomyOpacity);
    this.cameraController.setNavigationMode(state.navMode);

    if (state.mode === 'ARM_MODE') {
      this.cameraController.goToArm(state.selectedArmIndex);
      this.neuralNetwork.setHighlightedArm(state.selectedArmIndex);
      this.updateBreadcrumbs('ARM', `Arm ${state.selectedArmIndex + 1}`);
    } else if (state.mode === 'BRAIN_MODE') {
      this.cameraController.goToCentralBrain();
      this.neuralNetwork.setHighlightedArm(null);
      this.updateBreadcrumbs('CENTRAL_BRAIN');
    } else if (state.mode === 'NETWORK_MODE') {
      this.anatomicalMesh.setOpacity(0.0);
    } else if (state.mode === 'COMPARE_ANATOMY') {
      this.anatomicalMesh.setOpacity(0.18);
    } else {
      this.neuralNetwork.setHighlightedArm(null);
    }
  }

  private updateBreadcrumbs(level: string, label?: string) {
    const items: BreadcrumbItem[] = [
      {
        level: 'WHOLE_OCTOPUS',
        label: 'WHOLE OCTOPUS',
        onClick: () => {
          this.cameraController.goToWholeOctopus();
          this.neuralNetwork.setIsolatedRegion(null);
          this.neuralNetwork.setHighlightedArm(null);
          this.neuralNetwork.setSelectedNeuron(null);
          this.neuralNetwork.setSelectedFiber(null);
          this.updateBreadcrumbs('WHOLE_OCTOPUS');
        },
      },
    ];

    if (level === 'CENTRAL_BRAIN' || level === 'BRAIN_REGION') {
      items.push({
        level: 'CENTRAL_BRAIN',
        label: 'CENTRAL BRAIN',
        onClick: () => {
          this.cameraController.goToCentralBrain();
          this.updateBreadcrumbs('CENTRAL_BRAIN');
        },
      });
      if (label) {
        items.push({
          level: 'BRAIN_REGION',
          label: label.toUpperCase(),
          onClick: () => {},
        });
      }
    } else if (level === 'ARM') {
      items.push({
        level: 'ARM',
        label: (label || 'ARM 1').toUpperCase(),
        onClick: () => {},
      });
    } else if (level === 'INDIVIDUAL_NEURON') {
      items.push({
        level: 'INDIVIDUAL_NEURON',
        label: (label || 'NEURON').toUpperCase(),
        onClick: () => {},
      });
    } else if (level === 'INDIVIDUAL_CONNECTION') {
      items.push({
        level: 'INDIVIDUAL_CONNECTION',
        label: (label || 'SYNAPTIC CONNECTION').toUpperCase(),
        onClick: () => {},
      });
    }

    this.breadcrumbs.setPath(items);
  }

  private bindEvents() {
    window.addEventListener('resize', () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
      this.composer.setSize(window.innerWidth, window.innerHeight);
    });

    // Universal Trackpad Zoom & Pan (Wheel) - never intercepted or frozen by UI elements
    window.addEventListener(
      'wheel',
      (e: WheelEvent) => {
        // If user is actively scrolling inside an internal scrollable list, allow native scroll
        const target = e.target as HTMLElement | null;
        if (target) {
          const scrollEl = target.closest('.window-body-scroll, .inspector-body, select') as HTMLElement | null;
          if (scrollEl) {
            const hasScrollableContent = scrollEl.scrollHeight > scrollEl.clientHeight;
            if (hasScrollableContent) {
              const canScrollUp = scrollEl.scrollTop > 0 && e.deltaY < 0;
              const canScrollDown =
                scrollEl.scrollTop + scrollEl.clientHeight < scrollEl.scrollHeight - 1 && e.deltaY > 0;
              if (canScrollUp || canScrollDown) {
                return; // Let the internal drawer scroll
              }
            }
          }
        }

        // Prevent native macOS page overscroll bounce and browser pinch-zoom
        e.preventDefault();

        // Always ensure OrbitControls is enabled
        this.controls.enabled = true;

        // User trackpad gesture immediately cancels any automated camera fly-in so they have full control
        this.cameraController.stopActiveTransition();

        // Forward wheel event directly to canvas so OrbitControls zooms seamlessly
        if (e.target !== this.renderer.domElement) {
          this.renderer.domElement.dispatchEvent(
            new WheelEvent('wheel', {
              clientX: e.clientX,
              clientY: e.clientY,
              screenX: e.screenX,
              screenY: e.screenY,
              deltaX: e.deltaX,
              deltaY: e.deltaY,
              deltaZ: e.deltaZ,
              deltaMode: e.deltaMode,
              ctrlKey: e.ctrlKey,
              shiftKey: e.shiftKey,
              altKey: e.altKey,
              metaKey: e.metaKey,
              bubbles: true,
              cancelable: true,
            })
          );
        }
      },
      { passive: false }
    );

    let isForwardingPointer = false;
    let pointerDownCoord = { x: 0, y: 0 };

    window.addEventListener('pointerdown', (e: PointerEvent) => {
      pointerDownCoord = { x: e.clientX, y: e.clientY };
      this.controls.enabled = true;

      const target = e.target as HTMLElement | null;
      if (!target) return;

      // Blur clicked button/anchor to avoid keyboard focus hijacking
      if (document.activeElement && document.activeElement instanceof HTMLElement) {
        if (document.activeElement.tagName === 'BUTTON' || document.activeElement.tagName === 'A') {
          document.activeElement.blur();
        }
      }

      // Check if clicking an interactive control
      const isInteractive = !!target.closest(
        'button, input, select, option, textarea, .window-titlebar, .window-resize-gripper, .window-drag-icon, a, [role="button"], input[type="range"]'
      );

      if (isInteractive) {
        return;
      }

      // If clicking non-interactive surfaces, cancel auto-flight for instant manual orbit
      this.cameraController.stopActiveTransition();

      if (target !== this.renderer.domElement) {
        isForwardingPointer = true;
        this.renderer.domElement.dispatchEvent(
          new PointerEvent('pointerdown', {
            pointerId: e.pointerId,
            clientX: e.clientX,
            clientY: e.clientY,
            screenX: e.screenX,
            screenY: e.screenY,
            button: e.button,
            buttons: e.buttons,
            ctrlKey: e.ctrlKey,
            shiftKey: e.shiftKey,
            altKey: e.altKey,
            metaKey: e.metaKey,
            pointerType: e.pointerType,
            bubbles: true,
            cancelable: true,
          })
        );
      }
    });

    window.addEventListener('pointermove', (e: PointerEvent) => {
      this.pointerNDC.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.pointerNDC.y = -(e.clientY / window.innerHeight) * 2 + 1;

      // Forward active drag to canvas if started outside canvas
      if (isForwardingPointer && e.target !== this.renderer.domElement) {
        this.renderer.domElement.dispatchEvent(
          new PointerEvent('pointermove', {
            pointerId: e.pointerId,
            clientX: e.clientX,
            clientY: e.clientY,
            screenX: e.screenX,
            screenY: e.screenY,
            button: e.button,
            buttons: e.buttons,
            ctrlKey: e.ctrlKey,
            shiftKey: e.shiftKey,
            altKey: e.altKey,
            metaKey: e.metaKey,
            pointerType: e.pointerType,
            bubbles: true,
            cancelable: true,
          })
        );
      }

      // 1. Raycast hover over Cephalopod Constellation 3D Octopuses
      const hoverRaycaster = new THREE.Raycaster();
      hoverRaycaster.setFromCamera(this.pointerNDC, this.camera);
      const hoveredOcto = this.constellation.pickOctopus(hoverRaycaster, false);

      if (hoveredOcto) {
        document.body.style.cursor = 'pointer';
        this.tooltipElement.style.left = `${e.clientX + 14}px`;
        this.tooltipElement.style.top = `${e.clientY + 14}px`;
        const glyphSvg = ICONS.octoGlyph(hoveredOcto.id, 14);
        this.tooltipElement.innerHTML = `
          <div style="font-weight: 700; color: ${hoveredOcto.colorHex}; font-size: 11px; font-family: 'Roboto Mono', monospace; display: flex; align-items: center; gap: 6px;">
            ${glyphSvg}
            <span>OCTO_${hoveredOcto.id} // ${hoveredOcto.title.toUpperCase()}</span>
          </div>
          <div style="font-size: 9.5px; opacity: 0.9; margin-top: 3px; font-family: 'Roboto Mono', monospace; color: #cbd5e1;">
            ${hoveredOcto.coreRole}
          </div>
          <div style="font-size: 8.5px; opacity: 0.65; margin-top: 2px; font-family: 'Roboto Mono', monospace;">
            ${hoveredOcto.department.toUpperCase()} // CLICK TO FOCUS
          </div>
        `;
        this.tooltipElement.classList.remove('hidden');
        return;
      }

      // 2. Raycast hover tooltip for individual neuron/fiber
      const hit = this.raycaster.pick(this.pointerNDC);
      if (hit) {
        document.body.style.cursor = 'pointer';
        this.tooltipElement.style.left = `${e.clientX + 14}px`;
        this.tooltipElement.style.top = `${e.clientY + 14}px`;

        if (hit.type === 'node' && hit.node) {
          const regionInfo = NEUROANATOMY_REGIONS[hit.node.regionId];
          this.tooltipElement.textContent = `Neuron #${hit.node.index} (${hit.node.type}) — ${regionInfo ? regionInfo.name : ''}`;
        } else if (hit.type === 'fiber' && hit.fiber) {
          this.tooltipElement.textContent = `Synapse #${hit.fiber.index} (${hit.fiber.pathwayName})`;
        }
        this.tooltipElement.classList.remove('hidden');
      } else if (!this.customStimulusMode) {
        document.body.style.cursor = 'default';
        this.tooltipElement.classList.add('hidden');
      }
    });

    window.addEventListener('pointerup', (e: PointerEvent) => {
      if (isForwardingPointer) {
        isForwardingPointer = false;
        if (e.target !== this.renderer.domElement) {
          this.renderer.domElement.dispatchEvent(
            new PointerEvent('pointerup', {
              pointerId: e.pointerId,
              clientX: e.clientX,
              clientY: e.clientY,
              button: e.button,
              bubbles: true,
              cancelable: true,
            })
          );
        }
      }
    });

    // Single click for selecting and inspecting
    window.addEventListener('click', (e) => {
      this.controls.enabled = true;
      const target = e.target as HTMLElement;

      // 1. Check if clicking directly on an octopus floating badge card
      const badge = target.closest('.octo-badge') as HTMLElement | null;
      if (badge) {
        const octoIdStr = badge.getAttribute('data-octo-id');
        if (octoIdStr !== null) {
          const id = parseInt(octoIdStr, 10);
          if (!isNaN(id)) {
            this.constellation.focusOnOctopus(id);
            return;
          }
        }
      }

      // If user was dragging trackpad to move left/right/up/down, do not trigger click
      const dragDist = Math.hypot(e.clientX - pointerDownCoord.x, e.clientY - pointerDownCoord.y);
      if (dragDist > 14) {
        return;
      }

      // 2. Ignore clicks on control panels, headers, buttons, inputs, or window titlebars
      if (target.closest('.floating-window, #top-header, button, select, input, .window-titlebar')) {
        return;
      }

      const clickNDC = new THREE.Vector2(
        (e.clientX / window.innerWidth) * 2 - 1,
        -(e.clientY / window.innerHeight) * 2 + 1
      );

      // 3. Check Cephalopod Constellation 3D Octopuses (generous hit collider + arms + head)
      const threeRaycaster = new THREE.Raycaster();
      threeRaycaster.setFromCamera(clickNDC, this.camera);
      const octoHit = this.constellation.pickOctopus(threeRaycaster, true);
      if (octoHit) {
        this.updateBreadcrumbs('WHOLE_OCTOPUS', `OCTO_${octoHit.id} // ${octoHit.title.toUpperCase()}`);
        return;
      }

      // 4. If already focused on an octopus, check individual neurons or fibers
      const hit = this.raycaster.pick(clickNDC);
      if (hit) {
        if (this.customStimulusMode) {
          if (hit.node) {
            this.signalPropagator.triggerNeuronMicrocircuitCascade(hit.node.index, 40);
          } else if (hit.fiber) {
            this.signalPropagator.triggerSingleFiberStimulus(hit.fiber.index);
          }
          this.customStimulusMode = false;
          this.tooltipElement.classList.add('hidden');
        } else if (hit.type === 'node' && hit.node) {
          // Open Inspector Panel for individual neuron
          this.selectedNode = hit.node;
          this.selectedFiber = null;
          this.neuralNetwork.setSelectedNeuron(hit.node.index);
          this.inspectorPanel.showNeuron(hit.node);
          this.updateBreadcrumbs('INDIVIDUAL_NEURON', `Neuron #${hit.node.index}`);
        } else if (hit.type === 'fiber' && hit.fiber && hit.sourceNode && hit.targetNode) {
          // Open Inspector Panel for individual fiber
          this.selectedFiber = hit.fiber;
          this.selectedNode = null;
          this.neuralNetwork.setSelectedFiber(hit.fiber.index);
          this.inspectorPanel.showFiber(hit.fiber, hit.sourceNode, hit.targetNode);
          this.signalPropagator.triggerSingleFiberStimulus(hit.fiber.index);
          this.updateBreadcrumbs('INDIVIDUAL_CONNECTION', `Synapse #${hit.fiber.index}`);
        }
      }
    });

    // Double-click to instantly orbit/focus on clicked neuron or fiber
    window.addEventListener('dblclick', (e) => {
      const target = e.target as HTMLElement;
      if (target.closest('.floating-window, #top-header, button, select, input, .octo-badge')) return;

      const hit = this.raycaster.pick(this.pointerNDC);
      if (hit) {
        if (hit.type === 'node' && hit.node) {
          this.cameraController.goToIndividualNeuron(hit.node.position, false);
          this.neuralNetwork.setSelectedNeuron(hit.node.index);
          this.inspectorPanel.showNeuron(hit.node);
        } else if (hit.type === 'fiber' && hit.sourceNode && hit.targetNode) {
          this.cameraController.goToConnectionFiber(hit.sourceNode.position, hit.targetNode.position);
          this.neuralNetwork.setSelectedFiber(hit.fiber!.index);
          this.inspectorPanel.showFiber(hit.fiber!, hit.sourceNode, hit.targetNode);
        }
      }
    });

    // Constellation View Reset Button
    const btnConstellation = document.getElementById('btn-view-constellation');
    if (btnConstellation) {
      btnConstellation.addEventListener('click', () => {
        this.voiceSystem.stopSpeaking();
        this.voiceSystem.hideBanner();
        this.constellation.resetOrbitView();
        this.updateBreadcrumbs('WHOLE_OCTOPUS', '8-OCTOPUS CONSTELLATION');
      });
    }

    // Voice Audio Mute / Unmute Toggle Button (WCAG Audio Opt-in: Default to Muted/OFF)
    const btnToggleVoice = document.getElementById('btn-toggle-voice');
    const labelVoice = document.getElementById('label-voice-state');
    const iconVoice = document.getElementById('icon-voice-state');

    const updateVoiceUI = (isMuted: boolean) => {
      if (btnToggleVoice) {
        btnToggleVoice.classList.toggle('muted', isMuted);
        btnToggleVoice.setAttribute('aria-pressed', isMuted ? 'false' : 'true');
        btnToggleVoice.setAttribute(
          'aria-label',
          isMuted ? 'Voice narration muted. Click to enable audio.' : 'Voice narration enabled. Click to mute audio.'
        );
      }
      if (labelVoice) {
        labelVoice.textContent = isMuted ? 'VOICE: OFF' : 'VOICE: ON';
      }
      if (iconVoice) {
        iconVoice.innerHTML = isMuted
          ? `<path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><line x1="23" y1="9" x2="17" y2="15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="17" y1="9" x2="23" y2="15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>`
          : `<path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M15.54 8.46C16.48 9.4 17 10.65 17 12C17 13.35 16.48 14.6 15.54 15.54" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M19.07 4.93C20.94 6.8 22 9.35 22 12C22 14.65 20.94 17.2 19.07 19.07" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>`;
      }
    };

    updateVoiceUI(this.voiceSystem.getIsMuted());

    if (btnToggleVoice) {
      btnToggleVoice.addEventListener('click', () => {
        const isMuted = this.voiceSystem.toggleMute();
        updateVoiceUI(isMuted);
      });
    }

    // Accessible Activity Log & Arm Status Toggle Button
    const btnToggleActivityLog = document.getElementById('btn-toggle-activity-log');
    if (btnToggleActivityLog) {
      this.activityLogPanel.bindToggleButton(btnToggleActivityLog);
    }

    // WCAG Reduced Motion Toggle Button
    const btnToggleReducedMotion = document.getElementById('btn-toggle-reduced-motion');
    const labelReducedMotion = document.getElementById('label-reduced-motion');
    const syncMotionState = (reduced: boolean) => {
      if (btnToggleReducedMotion) {
        btnToggleReducedMotion.classList.toggle('active', reduced);
        btnToggleReducedMotion.setAttribute('aria-pressed', String(reduced));
        btnToggleReducedMotion.setAttribute(
          'aria-label',
          reduced ? 'Reduced motion active. Click to restore normal motion.' : 'Normal motion active. Click to reduce motion.'
        );
      }
      if (labelReducedMotion) {
        labelReducedMotion.textContent = reduced ? 'MOTION: REDUCED' : 'MOTION: NORMAL';
      }
    };
    syncMotionState(MotionPolicy.getInstance().isReducedMotion());
    MotionPolicy.getInstance().addListener(syncMotionState);

    if (btnToggleReducedMotion) {
      btnToggleReducedMotion.addEventListener('click', () => {
        const next = MotionPolicy.getInstance().toggleReducedMotion();
        syncMotionState(next);
      });
    }

    // Accessible Global Keyboard Handlers (Escape closes open panels; L toggles Activity Log)
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (this.activityLogPanel?.isOpen()) {
          this.activityLogPanel.hide();
          return;
        }
        if (this.manualModal?.isOpen()) {
          this.manualModal.close();
          return;
        }
        if (this.cognitiveInspector?.container && this.cognitiveInspector.container.style.display !== 'none') {
          this.cognitiveInspector.hide();
          return;
        }
        this.inspectorPanel?.hide();
        const sandbox = document.getElementById('live-sandbox-window');
        if (sandbox && sandbox.style.display !== 'none') {
          sandbox.style.display = 'none';
          sandbox.classList.add('hidden');
        }
      } else if (e.key === 'l' || e.key === 'L') {
        const activeTag = document.activeElement?.tagName;
        if (activeTag !== 'INPUT' && activeTag !== 'TEXTAREA') {
          this.activityLogPanel?.toggle();
        }
      }
    });

    // Adaptive Domain Mode Toggle (DUAL -> SOFTWARE -> AIML)
    const btnDomainMode = document.getElementById('btn-toggle-domain-mode');
    const labelDomain = document.getElementById('label-domain-mode');
    const updateDomainUI = (mode: 'DUAL' | 'SOFTWARE' | 'AIML') => {
      if (labelDomain) {
        labelDomain.textContent =
          mode === 'DUAL'
            ? 'MODE: DUAL (SW + AI/ML)'
            : mode === 'SOFTWARE'
            ? 'MODE: SOFTWARE DEV'
            : 'MODE: AI/ML RESEARCH';
      }
      if (btnDomainMode) {
        btnDomainMode.setAttribute('data-mode', mode.toLowerCase());
      }
    };

    if (btnDomainMode) {
      btnDomainMode.addEventListener('click', () => {
        const cur = this.voiceSystem.getDomainMode();
        const next: 'DUAL' | 'SOFTWARE' | 'AIML' =
          cur === 'DUAL' ? 'SOFTWARE' : cur === 'SOFTWARE' ? 'AIML' : 'DUAL';
        this.voiceSystem.setDomainMode(next);
        this.constellation.setDomainMode(next);
        updateDomainUI(next);
      });
    }

    // When constellation auto-adapts domain mode via incoming WebSocket telemetry
    this.constellation.onDomainModeChange = (mode) => {
      this.voiceSystem.setDomainMode(mode);
      updateDomainUI(mode);
    };

    // Live Application / Model Sandbox Window Elements
    const btnLivePreview = document.getElementById('btn-live-preview');
    const labelLivePreview = document.getElementById('label-live-preview');
    const sandboxWindow = document.getElementById('live-sandbox-window');
    const sandboxIframe = document.getElementById('live-sandbox-iframe') as HTMLIFrameElement | null;
    const sandboxTitle = document.getElementById('sandbox-title');
    const sandboxUrlDisplay = document.getElementById('sandbox-url-display');
    const sandboxServiceType = document.getElementById('sandbox-service-type');
    const sandboxApiLink = document.getElementById('sandbox-api-link') as HTMLAnchorElement | null;
    const btnSandboxClose = document.getElementById('btn-sandbox-close');
    const btnSandboxReload = document.getElementById('btn-sandbox-reload');
    const btnSandboxExternal = document.getElementById('btn-sandbox-open-external') as HTMLAnchorElement | null;

    let currentLiveUrl = '';

    const showLiveSandbox = (url: string, type: string = 'WEB APP', title: string = 'LIVE APPLICATION SANDBOX', apiDocs?: string) => {
      currentLiveUrl = url;
      if (sandboxWindow) {
        sandboxWindow.style.display = 'flex';
        sandboxWindow.classList.remove('hidden');
      }
      if (sandboxIframe && sandboxIframe.src !== url) {
        sandboxIframe.src = url;
      }
      if (sandboxTitle) {
        sandboxTitle.textContent = title.toUpperCase();
      }
      if (sandboxUrlDisplay) {
        sandboxUrlDisplay.textContent = url;
      }
      if (sandboxServiceType) {
        sandboxServiceType.textContent = (type || 'WEB APP').toUpperCase().replace('_', ' ');
      }
      if (btnSandboxExternal) {
        btnSandboxExternal.href = url;
      }
      if (sandboxApiLink) {
        if (apiDocs && apiDocs !== url) {
          sandboxApiLink.href = apiDocs;
          sandboxApiLink.style.display = 'inline-block';
        } else {
          sandboxApiLink.style.display = 'none';
        }
      }
    };

    if (btnLivePreview) {
      btnLivePreview.addEventListener('click', () => {
        if (currentLiveUrl) {
          showLiveSandbox(currentLiveUrl);
        }
      });
    }

    if (btnSandboxClose) {
      btnSandboxClose.addEventListener('click', () => {
        if (sandboxWindow) {
          sandboxWindow.style.display = 'none';
          sandboxWindow.classList.add('hidden');
        }
      });
    }

    if (btnSandboxReload) {
      btnSandboxReload.addEventListener('click', () => {
        if (sandboxIframe && currentLiveUrl) {
          sandboxIframe.src = currentLiveUrl;
        }
      });
    }

    // Connect WebSocket LIVE_SERVICE_READY telemetry
    this.constellation.onLiveServiceReady = (evt: any) => {
      const url = evt.service_url || (evt.payload && evt.payload.primary_url);
      if (!url) return;

      currentLiveUrl = url;
      const portMatch = url.match(/:(\d+)/);
      const portStr = portMatch ? `(:${portMatch[1]})` : '';
      const typeStr = (evt.service_type || 'APP').toUpperCase().replace('_', ' ');

      if (btnLivePreview) {
        btnLivePreview.style.display = 'flex';
        btnLivePreview.classList.remove('hidden');
      }
      if (labelLivePreview) {
        labelLivePreview.textContent = `LIVE ${typeStr} ${portStr}`;
      }

      // Show floating sandbox on ignition
      showLiveSandbox(url, evt.service_type, evt.summary || 'LIVE APPLICATION SANDBOX', evt.api_docs_url);

      // Trigger runner voice announcement
      this.voiceSystem.speakOctopusRole(7);
    };

    // Guided Tour Launchers
    const btnHeaderTour = document.getElementById('btn-start-tour-header');
    if (btnHeaderTour) {
      btnHeaderTour.addEventListener('click', () => this.startGuidedTour());
    }
    this.controlPanel.onStartTour = () => this.startGuidedTour();
  }

  private startGuidedTour() {
    this.selectedNode = null;
    this.selectedFiber = null;
    this.neuralNetwork.setSelectedNeuron(null);
    this.neuralNetwork.setSelectedFiber(null);
    this.inspectorPanel.hide();
    this.signalPanel.clearProgress();
    this.tooltipElement.classList.add('hidden');

    const sigContainer = document.getElementById('signal-trigger-panel');
    if (sigContainer) sigContainer.style.display = 'none';
    const ctrlPanel = document.getElementById('control-panel');
    if (ctrlPanel) ctrlPanel.style.display = 'none';

    this.tourHUD.show();
    this.storyTourManager.startTour();
    this.updateBreadcrumbs('WHOLE_OCTOPUS', 'ANIMATED TOUR');
  }

  private checkWebGLSupport(): boolean {
    if (typeof window === 'undefined') return false;
    try {
      const testCanvas = document.createElement('canvas');
      return !!(
        window.WebGLRenderingContext &&
        (testCanvas.getContext('webgl2') || testCanvas.getContext('webgl'))
      );
    } catch {
      return false;
    }
  }

  private renderWebGLFallbackNotice(customMessage?: string): void {
    let el = document.getElementById('webgl-fallback-notice');
    if (!el) {
      el = document.createElement('div');
      el.id = 'webgl-fallback-notice';
      el.setAttribute('role', 'alert');
      el.style.cssText = `
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(17, 24, 39, 0.95);
        border: 1px solid #fab387;
        color: #ffffff;
        padding: 14px 20px;
        border-radius: 8px;
        font-family: 'Roboto Mono', monospace;
        font-size: 11px;
        z-index: 99999;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.8);
      `;
      document.body.appendChild(el);
    }
    el.innerHTML = `
      <span style="color: #fab387; font-weight: 700;">[A11Y FALLBACK]</span>
      <span>${customMessage || 'WebGL 3D hardware acceleration is unavailable. Displaying real-time accessible text & arm telemetry.'}</span>
      <button id="btn-fallback-view-table" style="background: #38bdf8; color: #0b0f19; border: none; padding: 4px 10px; border-radius: 4px; font-weight: 700; cursor: pointer; font-size: 10px;">
        OPEN TABLE & LOGS
      </button>
    `;
    const btn = el.querySelector('#btn-fallback-view-table');
    if (btn) {
      btn.addEventListener('click', () => {
        this.activityLogPanel?.show();
      });
    }
  }

  private initFallbackUI(): void {
    const btnToggleActivityLog = document.getElementById('btn-toggle-activity-log');
    if (btnToggleActivityLog) {
      this.activityLogPanel.bindToggleButton(btnToggleActivityLog);
    }
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (this.activityLogPanel?.isOpen()) {
          this.activityLogPanel.hide();
        }
      } else if (e.key === 'l' || e.key === 'L') {
        if (document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
          this.activityLogPanel?.toggle();
        }
      }
    });
  }

  private updateScreenReaderSummary(evt?: any): void {
    const el = document.getElementById('canvas-live-summary');
    if (!el) return;
    const activeOcto = this.constellation?.getActiveOctopus();
    const domain = this.voiceSystem?.getDomainMode() || 'DUAL';
    const status = evt?.status || activeOcto?.data.status || 'ONLINE';
    const action = evt?.summary || activeOcto?.data.currentAction || 'Running tasks';
    el.textContent = `OctoFlow Cephalopod Swarm: 8 arms online. Domain: ${domain}. Active Arm ${activeOcto?.data.id ?? 0} (${status}): ${action}.`;
  }

  private animate = () => {
    requestAnimationFrame(this.animate);

    const deltaTime = this.clock.getDelta();
    const elapsedTime = this.clock.getElapsedTime();

    // 0. Update 3D Cephalopod Constellation Swarm & Synaptic Energy Beams
    this.constellation.animate(deltaTime);

    // 0b. Update Story Tour Walkthrough (if active)
    this.storyTourManager.update(deltaTime);

    // 1. Update Camera Controller (Orbit damping, Tween, or First-Person WASD)
    this.cameraController.update(deltaTime);

    // 2. Follow Signal tracking update
    if (this.cameraController.navMode === 'FOLLOW_SIGNAL') {
      const leadPos = this.signalPropagator.getLeadPulsePosition();
      if (leadPos) {
        this.cameraController.updateSignalFollow(leadPos, deltaTime);
      }
    }

    // 3. Update Neural Signal Propagator & Traveling Action Potentials
    const ctrlState = this.controlPanel.getState();
    this.signalPropagator.update(deltaTime, ctrlState.signalSpeed);

    // 4. Update GPU Shaders
    this.neuralNetwork.update(
      elapsedTime,
      this.signalPropagator.stimulusOrigin,
      this.signalPropagator.stimulusWaveRadius,
      this.signalPropagator.stimulusIntensity,
      this.camera
    );

    // 5. Render 3D Scene with FlyWire Cinematic Post-Processing
    this.composer.render();
  };
}

// Initialize Application on Window Load
window.addEventListener('DOMContentLoaded', () => {
  new OctopusConnectomeApp();
});

