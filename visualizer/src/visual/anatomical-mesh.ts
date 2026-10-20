/** Ghosted Anatomical Silhouette and Spatial Reference Mesh for Octopus. */

import * as THREE from 'three';

export class AnatomicalMeshGenerator {
  public group: THREE.Group;
  public mantleMesh!: THREE.Mesh;
  public headMesh!: THREE.Mesh;
  public armMeshes: THREE.Mesh[] = [];
  private materials: THREE.MeshPhysicalMaterial[] = [];

  constructor(themeColorHex: string | number = 0x0ea5e9) {
    this.group = new THREE.Group();
    this.buildAnatomicalMesh(themeColorHex);
  }

  private buildAnatomicalMesh(themeColorHex: string | number) {
    const baseColor = new THREE.Color(themeColorHex);
    // Translucent glassmorphic material with subtle oceanic rim glow
    const mantleMat = new THREE.MeshPhysicalMaterial({
      color: baseColor,
      roughness: 0.2,
      metalness: 0.1,
      transmission: 0.85,
      ior: 1.33,
      transparent: true,
      opacity: 0.14,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    this.materials.push(mantleMat);

    const eyeMat = new THREE.MeshPhysicalMaterial({
      color: baseColor.clone().offsetHSL(0.05, 0.2, 0.1),
      roughness: 0.1,
      transmission: 0.9,
      transparent: true,
      opacity: 0.35,
      depthWrite: false,
    });
    this.materials.push(eyeMat);

    // 1. Mantle (Dorsal head & visceral sac)
    const mantleGeo = new THREE.SphereGeometry(14.0, 32, 24);
    mantleGeo.scale(1.0, 1.45, 1.1);
    this.mantleMesh = new THREE.Mesh(mantleGeo, mantleMat);
    this.mantleMesh.position.set(0, 16.0, 2.0);
    this.group.add(this.mantleMesh);

    // 2. Head / Central Brain Capsule
    const headGeo = new THREE.SphereGeometry(12.0, 28, 20);
    headGeo.scale(1.2, 0.9, 1.0);
    this.headMesh = new THREE.Mesh(headGeo, mantleMat);
    this.headMesh.position.set(0, 3.0, 0);
    this.group.add(this.headMesh);

    // 3. Bilateral Eyes (Outer visual reference flanking optic lobes)
    const eyeGeo = new THREE.SphereGeometry(4.5, 20, 20);
    const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
    leftEye.position.set(-24.0, 4.0, -1.0);
    const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
    rightEye.position.set(24.0, 4.0, -1.0);
    this.group.add(leftEye, rightEye);

    // 4. 8 Arm Silhouettes (Tapering curved tubes hugging the neural cords)
    const numArms = 8;
    const armAngles = Array.from({ length: 8 }, (_, i) => (i / 8) * Math.PI * 2);

    for (let armIdx = 0; armIdx < numArms; armIdx++) {
      const baseAngle = armAngles[armIdx];
      const ringRadius = 13.0;
      const startY = -5.5;

      const splinePoints: THREE.Vector3[] = [];
      const numCtrl = 6;
      const armLength = 55.0;

      for (let c = 0; c < numCtrl; c++) {
        const t = c / (numCtrl - 1);
        const curveAngle = baseAngle + t * 0.45 * ((armIdx % 2 === 0) ? 1 : -1);
        const r = ringRadius + t * armLength * 0.9;
        const x = r * Math.cos(curveAngle);
        const z = r * Math.sin(curveAngle);
        const y = startY - t * (armLength * 0.45) + Math.sin(t * Math.PI) * 4.0;
        splinePoints.push(new THREE.Vector3(x, y, z));
      }

      const armCurve = new THREE.CatmullRomCurve3(splinePoints);
      const armTubeGeo = new THREE.TubeGeometry(armCurve, 36, 3.2, 12, false);
      const armMesh = new THREE.Mesh(armTubeGeo, mantleMat);
      this.group.add(armMesh);
      this.armMeshes.push(armMesh);
    }
  }

  public update(elapsedTime: number, phaseOffset: number = 0) {
    // 1. Biological Mantle Breathing (expansion & contraction)
    const breath = 1.0 + Math.sin(elapsedTime * 1.8 + phaseOffset) * 0.045;
    if (this.mantleMesh) {
      this.mantleMesh.scale.set(1.0 * breath, 1.45 * breath, 1.1 * breath);
    }
    if (this.headMesh) {
      this.headMesh.scale.set(1.2 * breath, 0.9 * breath, 1.0 * breath);
    }

    // 2. Fluid 8-Tentacle Undulating Ripple
    this.armMeshes.forEach((arm, i) => {
      const armWave = Math.sin(elapsedTime * 2.2 + i * 0.78 + phaseOffset) * 0.07;
      arm.rotation.z = armWave;
      arm.rotation.y = Math.cos(elapsedTime * 1.5 + i * 0.5 + phaseOffset) * 0.04;
    });
  }

  public setOpacity(opacity: number) {
    for (const mat of this.materials) {
      mat.opacity = opacity;
      mat.visible = opacity > 0.001;
    }
  }

  public setVisible(visible: boolean) {
    this.group.visible = visible;
  }
}
