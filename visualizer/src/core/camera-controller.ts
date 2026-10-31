/** Advanced 3D Connectome Navigation & Camera Controller.
 * Supports:
 *  - 360° Unconstrained Orbit & Microscopic Neuron Focus
 *  - "INSIDE NETWORK" First-Person Free-Fly Mode (WASD + Free Mouselook)
 *  - "FOLLOW SIGNAL" Cinematic Action Potential Tracking Mode
 *  - Instant Perspective Presets (Front, Back, Left, Right, Top, Bottom, Inside Brain)
 */

import * as THREE from 'three';
import * as TWEEN from '@tweenjs/tween.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export type HierarchyLevel =
  | 'WHOLE_OCTOPUS'
  | 'CENTRAL_BRAIN'
  | 'BRAIN_REGION'
  | 'ARM'
  | 'AXIAL_NERVE_CORD'
  | 'NEURAL_SEGMENT'
  | 'SUCKER_NETWORK'
  | 'INDIVIDUAL_NEURON'
  | 'CONNECTED_NEURONS'
  | 'INDIVIDUAL_CONNECTION';

export type NavigationMode = 'ORBIT' | 'FREE_FLY' | 'FOLLOW_SIGNAL';

export class CameraController {
  public camera: THREE.PerspectiveCamera;
  public controls: OrbitControls;
  public currentLevel: HierarchyLevel = 'WHOLE_OCTOPUS';
  public navMode: NavigationMode = 'ORBIT';
  public isTweening: boolean = false;
  private currentTween: TWEEN.Tween<any> | null = null;

  // Free-fly navigation variables
  private flyVelocity = new THREE.Vector3();
  private flySpeed = 22.0;
  private isSprint = false;
  private keyState: Record<string, boolean> = {};
  private euler = new THREE.Euler(0, 0, 0, 'YXZ');
  private isMouseDownForFly = false;
  private lastMouseX = 0;
  private lastMouseY = 0;

  // Signal follow smoothing
  private followTarget = new THREE.Vector3();
  private followCamPos = new THREE.Vector3();

  constructor(camera: THREE.PerspectiveCamera, controls: OrbitControls) {
    this.camera = camera;
    this.controls = controls;

    // Configure OrbitControls for complete 360° unconstrained freedom
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 2.0; // Zoom down to single micron neuron soma level
    this.controls.maxDistance = 2500.0; // Unconstrained zoom-out to view deep space & entire swarm
    this.controls.minPolarAngle = 0; // Full 360 vertical rotation (no angle locks)
    this.controls.maxPolarAngle = Math.PI;
    this.controls.enableRotate = true;
    this.controls.rotateSpeed = 1.0;
    this.controls.enablePan = true;
    this.controls.panSpeed = 1.0;
    this.controls.screenSpacePanning = true;
    this.controls.enableZoom = true;
    this.controls.zoomSpeed = 1.0;

    this.bindKeyboardAndFlyEvents();
  }

  public stopActiveTransition() {
    if (this.currentTween) {
      this.currentTween.stop();
      this.currentTween = null;
    }
    this.isTweening = false;
    this.controls.enabled = true;
    this.controls.update();
  }

  public setNavigationMode(mode: NavigationMode) {
    this.navMode = mode;
    this.controls.enabled = true;
    if (mode === 'FREE_FLY') {
      this.euler.setFromQuaternion(this.camera.quaternion);
    } else if (mode === 'FOLLOW_SIGNAL') {
      // Keep controls enabled so user can still zoom or inspect
    } else {
      this.controls.target.copy(this.camera.position).add(
        this.camera.getWorldDirection(new THREE.Vector3()).multiplyScalar(20.0)
      );
    }
    this.controls.update();
  }

  private bindKeyboardAndFlyEvents() {
    window.addEventListener('keydown', (e) => {
      this.keyState[e.code] = true;
      if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') {
        this.isSprint = true;
      }
    });

    window.addEventListener('keyup', (e) => {
      this.keyState[e.code] = false;
      if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') {
        this.isSprint = false;
      }
    });

    // Mouse drag for Free-Fly look
    window.addEventListener('mousedown', (e) => {
      if (this.navMode === 'FREE_FLY' && (e.button === 0 || e.button === 2)) {
        this.isMouseDownForFly = true;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
      }
    });

    window.addEventListener('mouseup', () => {
      this.isMouseDownForFly = false;
    });

    window.addEventListener('mousemove', (e) => {
      if (this.navMode === 'FREE_FLY' && this.isMouseDownForFly) {
        const deltaX = e.clientX - this.lastMouseX;
        const deltaY = e.clientY - this.lastMouseY;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;

        const lookSpeed = 0.0032;
        this.euler.y -= deltaX * lookSpeed;
        this.euler.x -= deltaY * lookSpeed;
        this.euler.x = Math.max(-Math.PI * 0.48, Math.min(Math.PI * 0.48, this.euler.x));

        this.camera.quaternion.setFromEuler(this.euler);
      }
    });
  }

  public flyTo(
    targetPos: THREE.Vector3,
    lookAtPos: THREE.Vector3,
    durationMs: number = 1300,
    level: HierarchyLevel = 'WHOLE_OCTOPUS',
    onComplete?: () => void
  ) {
    this.currentLevel = level;
    if (this.currentTween) {
      this.currentTween.stop();
      this.currentTween = null;
    }
    this.isTweening = true;
    this.controls.enabled = true;

    const startPos = this.camera.position.clone();
    const startTarget = this.controls.target.clone();

    this.currentTween = new TWEEN.Tween({
      camX: startPos.x,
      camY: startPos.y,
      camZ: startPos.z,
      tgtX: startTarget.x,
      tgtY: startTarget.y,
      tgtZ: startTarget.z,
    })
      .to(
        {
          camX: targetPos.x,
          camY: targetPos.y,
          camZ: targetPos.z,
          tgtX: lookAtPos.x,
          tgtY: lookAtPos.y,
          tgtZ: lookAtPos.z,
        },
        durationMs
      )
      .easing(TWEEN.Easing.Cubic.InOut)
      .onUpdate((obj) => {
        this.camera.position.set(obj.camX, obj.camY, obj.camZ);
        this.controls.target.set(obj.tgtX, obj.tgtY, obj.tgtZ);
        this.camera.lookAt(this.controls.target);
      })
      .onComplete(() => {
        this.currentTween = null;
        this.controls.enabled = true;
        this.controls.update();
        this.isTweening = false;
        if (onComplete) onComplete();
      })
      .start();
  }

  /**
   * GTA V Style Character Switch:
   * Rockets up to high satellite orbit with wide-angle FOV expansion,
   * arcs gracefully across the constellation, and dives straight down into the target octopus.
   */
  public gtaSwitchTo(
    targetPos: THREE.Vector3,
    lookAtPos: THREE.Vector3,
    durationMs: number = 1450,
    onComplete?: () => void
  ) {
    this.currentLevel = 'WHOLE_OCTOPUS';
    if (this.currentTween) {
      this.currentTween.stop();
      this.currentTween = null;
    }
    this.isTweening = true;
    this.controls.enabled = true;

    const startCam = this.camera.position.clone();
    const startTarget = this.controls.target.clone();
    const initialFov = 45;

    // Calculate High-Altitude Apex / Zenith for the GTA V orbit arc
    const midX = (startCam.x + targetPos.x) * 0.5;
    const midZ = (startCam.z + targetPos.z) * 0.5;
    const distanceBetween = startCam.distanceTo(targetPos);

    // Apex height: scale with distance so cross-constellation leaps reach satellite altitude
    const apexHeight = Math.max(startCam.y, targetPos.y) + Math.min(240, Math.max(110, distanceBetween * 0.55));

    // Pull outward from center for a breathtaking panoramic view of the entire swarm at apex
    const radialLen = Math.hypot(midX, midZ);
    const scaleFactor = radialLen > 10 ? Math.max(65, radialLen * 1.3) / radialLen : 1.0;
    const zenithCam = new THREE.Vector3(midX * scaleFactor, apexHeight, midZ * scaleFactor);

    // Zenith look-at tilts towards center of the swarm at peak altitude
    const zenithTarget = new THREE.Vector3(midX * 0.25, 5, midZ * 0.25);

    const animState = { t: 0 };

    this.currentTween = new TWEEN.Tween(animState)
      .to({ t: 1.0 }, durationMs)
      .easing(TWEEN.Easing.Cubic.InOut)
      .onUpdate(({ t }) => {
        // Quadratic Bezier interpolation for GTA V rocket-arc trajectory
        const oneMinusT = 1.0 - t;
        const b0 = oneMinusT * oneMinusT;
        const b1 = 2.0 * oneMinusT * t;
        const b2 = t * t;

        const curCamX = b0 * startCam.x + b1 * zenithCam.x + b2 * targetPos.x;
        const curCamY = b0 * startCam.y + b1 * zenithCam.y + b2 * targetPos.y;
        const curCamZ = b0 * startCam.z + b1 * zenithCam.z + b2 * targetPos.z;

        const curTgtX = b0 * startTarget.x + b1 * zenithTarget.x + b2 * lookAtPos.x;
        const curTgtY = b0 * startTarget.y + b1 * zenithTarget.y + b2 * lookAtPos.y;
        const curTgtZ = b0 * startTarget.z + b1 * zenithTarget.z + b2 * lookAtPos.z;

        this.camera.position.set(curCamX, curCamY, curCamZ);
        this.controls.target.set(curTgtX, curTgtY, curTgtZ);
        this.camera.lookAt(this.controls.target);

        // GTA V Dynamic FOV: punch wide up to 60° at apex, then snap crisply back to 45°
        const fovPunch = Math.sin(t * Math.PI) * 15.0;
        this.camera.fov = initialFov + fovPunch;
        this.camera.updateProjectionMatrix();
      })
      .onComplete(() => {
        this.currentTween = null;
        this.camera.position.copy(targetPos);
        this.controls.target.copy(lookAtPos);
        this.camera.lookAt(lookAtPos);
        this.camera.fov = initialFov;
        this.camera.updateProjectionMatrix();

        this.controls.enabled = true;
        this.controls.update();
        this.isTweening = false;
        if (onComplete) onComplete();
      })
      .start();
  }

  public tweenCameraTo(
    targetPos: THREE.Vector3,
    lookAtPos: THREE.Vector3,
    durationMs: number = 1800,
    onComplete?: () => void
  ) {
    this.flyTo(targetPos, lookAtPos, durationMs, this.currentLevel, onComplete);
  }

  public orbitBy(deltaTheta: number, deltaPhi: number = 0.0) {
    if (this.isTweening || this.navMode !== 'ORBIT') return;
    const offset = this.camera.position.clone().sub(this.controls.target);
    const radius = offset.length();
    let theta = Math.atan2(offset.x, offset.z);
    let phi = Math.acos(Math.max(-1, Math.min(1, offset.y / Math.max(0.001, radius))));

    theta += deltaTheta;
    phi = Math.max(0.05, Math.min(Math.PI - 0.05, phi + deltaPhi));

    offset.x = radius * Math.sin(phi) * Math.sin(theta);
    offset.y = radius * Math.cos(phi);
    offset.z = radius * Math.sin(phi) * Math.cos(theta);

    this.camera.position.copy(this.controls.target).add(offset);
    this.camera.lookAt(this.controls.target);
  }


  // Anchor position for multi-octopus constellation targeting (defaults to 0,0,0)
  public anchorPosition = new THREE.Vector3(0, 0, 0);

  public setAnchor(pos: THREE.Vector3) {
    this.anchorPosition.copy(pos);
  }

  // --- HIERARCHICAL NAVIGATION PRESETS ---

  public goToWholeOctopus() {
    this.flyTo(
      this.anchorPosition.clone().add(new THREE.Vector3(0, 48, 92)),
      this.anchorPosition.clone().add(new THREE.Vector3(0, -2, 0)),
      1400,
      'WHOLE_OCTOPUS'
    );
  }

  public goToCentralBrain() {
    this.flyTo(
      this.anchorPosition.clone().add(new THREE.Vector3(0, 16, 32)),
      this.anchorPosition.clone().add(new THREE.Vector3(0, 3, 0)),
      1300,
      'CENTRAL_BRAIN'
    );
  }

  public goToVerticalLobe() {
    this.flyTo(
      this.anchorPosition.clone().add(new THREE.Vector3(0, 18, 18)),
      this.anchorPosition.clone().add(new THREE.Vector3(0, 8.5, 1.5)),
      1200,
      'BRAIN_REGION'
    );
  }

  public goToOpticLobe(side: 'left' | 'right' = 'left') {
    const x = side === 'left' ? -26 : 26;
    const tgtX = side === 'left' ? -18 : 18;
    this.flyTo(
      this.anchorPosition.clone().add(new THREE.Vector3(x, 10, 20)),
      this.anchorPosition.clone().add(new THREE.Vector3(tgtX, 3.5, 0)),
      1200,
      'BRAIN_REGION'
    );
  }

  public goToArm(armIndex: number) {
    const angle = (armIndex / 8) * Math.PI * 2;
    const camR = 45.0;
    const tgtR = 25.0;

    const camX = camR * Math.cos(angle - 0.2);
    const camZ = camR * Math.sin(angle - 0.2);
    const camY = -12.0;

    const tgtX = tgtR * Math.cos(angle);
    const tgtZ = tgtR * Math.sin(angle);
    const tgtY = -16.0;

    this.flyTo(
      this.anchorPosition.clone().add(new THREE.Vector3(camX, camY, camZ)),
      this.anchorPosition.clone().add(new THREE.Vector3(tgtX, tgtY, tgtZ)),
      1400,
      'ARM'
    );
  }

  public goToAxialCord(armIndex: number, segmentIndex: number = 10) {
    const angle = (armIndex / 8) * Math.PI * 2;
    const r = 16.0 + segmentIndex * 0.7;
    const x = r * Math.cos(angle);
    const z = r * Math.sin(angle);
    const y = -14.0;

    this.flyTo(
      this.anchorPosition.clone().add(new THREE.Vector3(x + 5 * Math.cos(angle + 0.5), y + 4, z + 5 * Math.sin(angle + 0.5))),
      this.anchorPosition.clone().add(new THREE.Vector3(x, y, z)),
      1100,
      'AXIAL_NERVE_CORD'
    );
  }

  public goToSuckerGanglion(armIndex: number, segmentIndex: number = 12) {
    const angle = (armIndex / 8) * Math.PI * 2;
    const r = 18.0 + segmentIndex * 0.8;
    const x = r * Math.cos(angle);
    const z = r * Math.sin(angle);
    const y = -18.0;

    this.flyTo(
      this.anchorPosition.clone().add(new THREE.Vector3(x + 2.5, y + 1.5, z + 2.5)),
      this.anchorPosition.clone().add(new THREE.Vector3(x, y, z)),
      1000,
      'SUCKER_NETWORK'
    );
  }

  public goToIndividualNeuron(nodePosition: THREE.Vector3, microZoom: boolean = false) {
    const dist = microZoom ? 0.65 : 2.2;
    const offset = new THREE.Vector3(dist * 0.7, dist * 0.5, dist * 0.7);
    const worldPos = nodePosition.clone().add(this.anchorPosition);
    this.flyTo(
      worldPos.clone().add(offset),
      worldPos.clone(),
      950,
      'INDIVIDUAL_NEURON'
    );
  }

  public goToConnectionFiber(p1: THREE.Vector3, p2: THREE.Vector3) {
    const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5).add(this.anchorPosition);
    const offset = new THREE.Vector3(1.8, 1.2, 1.8);
    this.flyTo(
      mid.clone().add(offset),
      mid.clone(),
      900,
      'INDIVIDUAL_CONNECTION'
    );
  }

  // --- PERSPECTIVE ANGLE PRESETS (ANY ANGLE FREEDOM - RELATIVE TO ACTIVE OCTOPUS) ---

  public setPerspectiveAngle(preset: 'FRONT' | 'BACK' | 'LEFT' | 'RIGHT' | 'TOP' | 'BOTTOM' | 'INSIDE') {
    const anchor = this.anchorPosition.clone().add(new THREE.Vector3(0, 4, 0));
    const dist = 75.0;

    const camPos = new THREE.Vector3();
    const target = anchor.clone();

    if (preset === 'FRONT') camPos.set(anchor.x, anchor.y + 10, anchor.z + dist);
    else if (preset === 'BACK') camPos.set(anchor.x, anchor.y + 10, anchor.z - dist);
    else if (preset === 'LEFT') camPos.set(anchor.x - dist, anchor.y + 10, anchor.z);
    else if (preset === 'RIGHT') camPos.set(anchor.x + dist, anchor.y + 10, anchor.z);
    else if (preset === 'TOP') camPos.set(anchor.x, anchor.y + dist, anchor.z + 0.1);
    else if (preset === 'BOTTOM') camPos.set(anchor.x, anchor.y - dist, anchor.z + 0.1);
    else if (preset === 'INSIDE') {
      // Travel directly into central brain cavity of active octopus
      camPos.set(this.anchorPosition.x, this.anchorPosition.y + 3.5, this.anchorPosition.z + 0.5);
      target.set(this.anchorPosition.x, this.anchorPosition.y + 7.0, this.anchorPosition.z - 1.0);
    }

    this.flyTo(camPos, target, 1100, this.currentLevel);
  }

  // --- SIGNAL TRACKING UPDATE ---

  public updateSignalFollow(pulsePos: THREE.Vector3, _deltaTime: number = 0.016) {
    if (this.navMode !== 'FOLLOW_SIGNAL') return;

    // Smoothly interpolate target to pulse position
    this.followTarget.lerp(pulsePos, 0.15);

    // Position camera slightly behind and above the pulse along forward vector
    const offset = new THREE.Vector3(0, 3.5, 7.0);
    this.followCamPos.copy(this.followTarget).add(offset);

    this.camera.position.lerp(this.followCamPos, 0.12);
    this.camera.lookAt(this.followTarget);
  }

  // --- PER-FRAME UPDATE LOOP ---

  public update(deltaTime: number = 0.016) {
    TWEEN.update();

    // OrbitControls damping and matrix synchronization always alive
    this.controls.update();

    if (this.navMode === 'FREE_FLY') {
      this.updateFreeFly(deltaTime);
    }
  }

  private updateFreeFly(dt: number) {
    const currentSpeed = this.flySpeed * (this.isSprint ? 2.5 : 1.0);
    const moveVector = new THREE.Vector3();

    // WASD Movement relative to camera heading
    if (this.keyState['KeyW'] || this.keyState['ArrowUp']) moveVector.z -= 1;
    if (this.keyState['KeyS'] || this.keyState['ArrowDown']) moveVector.z += 1;
    if (this.keyState['KeyA'] || this.keyState['ArrowLeft']) moveVector.x -= 1;
    if (this.keyState['KeyD'] || this.keyState['ArrowRight']) moveVector.x += 1;
    if (this.keyState['Space'] || this.keyState['KeyE']) moveVector.y += 1;
    if (this.keyState['KeyC'] || this.keyState['KeyQ']) moveVector.y -= 1;

    if (moveVector.lengthSq() > 0) {
      moveVector.normalize();
      moveVector.applyQuaternion(this.camera.quaternion);

      this.flyVelocity.lerp(moveVector.multiplyScalar(currentSpeed), 0.15);
    } else {
      this.flyVelocity.lerp(new THREE.Vector3(0, 0, 0), 0.12);
    }

    this.camera.position.addScaledVector(this.flyVelocity, dt);
  }
}

