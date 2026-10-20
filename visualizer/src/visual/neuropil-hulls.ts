/** Volumetric Neuropil Compartment Boundary Hulls (Google Connectome / FlyWire Style).
 * Renders translucent, glassmorphic 3D bounding mesh hulls for each functional cephalopod brain lobe.
 */

import * as THREE from 'three';
import { NEUROANATOMY_REGIONS } from '../data/neuroanatomy';

export const NeuropilHullShader = {
  vertexShader: `
    varying vec3 vNormal;
    varying vec3 vViewPosition;

    void main() {
      vNormal = normalize(normalMatrix * normal);
      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
      vViewPosition = -mvPosition.xyz;
      gl_Position = projectionMatrix * mvPosition;
    }
  `,

  fragmentShader: `
    uniform vec3 uHullColor;
    uniform float uOpacity;
    uniform float uFresnelBias;
    uniform float uFresnelScale;
    uniform float uFresnelPower;

    varying vec3 vNormal;
    varying vec3 vViewPosition;

    void main() {
      vec3 normal = normalize(vNormal);
      vec3 viewDir = normalize(vViewPosition);

      // Two-sided Fresnel edge illumination
      float fresnel = uFresnelBias + uFresnelScale * pow(1.0 - abs(dot(normal, viewDir)), uFresnelPower);
      fresnel = clamp(fresnel, 0.0, 1.0);

      // Core interior transparency + vibrant edge glow
      float alpha = (0.04 + fresnel * 0.42) * uOpacity;
      vec3 glowColor = mix(uHullColor, vec3(1.0, 1.0, 1.0), fresnel * 0.35);

      gl_FragColor = vec4(glowColor, alpha);
    }
  `,
};

export class NeuropilHullsManager {
  public group: THREE.Group;
  private materials: THREE.ShaderMaterial[] = [];
  private hullMeshes: Record<string, THREE.Mesh> = {};

  constructor() {
    this.group = new THREE.Group();
    this.buildNeuropilCompartments();
  }

  private createHullMaterial(colorHex: string, opacity: number = 0.22): THREE.ShaderMaterial {
    const mat = new THREE.ShaderMaterial({
      vertexShader: NeuropilHullShader.vertexShader,
      fragmentShader: NeuropilHullShader.fragmentShader,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uHullColor: { value: new THREE.Color(colorHex) },
        uOpacity: { value: opacity },
        uFresnelBias: { value: 0.05 },
        uFresnelScale: { value: 1.2 },
        uFresnelPower: { value: 2.2 },
      },
    });
    this.materials.push(mat);
    return mat;
  }

  private buildNeuropilCompartments() {
    // 1. Vertical Lobe Hull (Top Dorsal Dome)
    const vlMat = this.createHullMaterial(NEUROANATOMY_REGIONS.vertical_lobe.colorHex, 0.28);
    const vlGeo = new THREE.SphereGeometry(6.8, 32, 24);
    vlGeo.scale(0.95, 0.82, 1.15);
    const vlMesh = new THREE.Mesh(vlGeo, vlMat);
    vlMesh.position.set(0, 8.5, 1.5);
    this.group.add(vlMesh);
    this.hullMeshes['vertical_lobe'] = vlMesh;

    // 2. Superior Frontal Lobe Hull (Anterior Associative Mass)
    const sflMat = this.createHullMaterial(NEUROANATOMY_REGIONS.superior_frontal_lobe.colorHex, 0.26);
    const sflGeo = new THREE.SphereGeometry(4.5, 24, 20);
    sflGeo.scale(0.9, 0.72, 0.95);
    const sflMesh = new THREE.Mesh(sflGeo, sflMat);
    sflMesh.position.set(0, 6.0, -4.5);
    this.group.add(sflMesh);
    this.hullMeshes['superior_frontal_lobe'] = sflMesh;

    // 3. Subfrontal & Inferior Frontal Lobe Hull (Tactile Memory Center)
    const subfMat = this.createHullMaterial(NEUROANATOMY_REGIONS.subfrontal_lobe.colorHex, 0.26);
    const subfGeo = new THREE.SphereGeometry(5.2, 24, 20);
    subfGeo.scale(0.92, 0.68, 0.9);
    const subfMesh = new THREE.Mesh(subfGeo, subfMat);
    subfMesh.position.set(0, 2.5, -5.5);
    this.group.add(subfMesh);
    this.hullMeshes['subfrontal_lobe'] = subfMesh;

    // 4. Subesophageal Motor Mass Hull (Ventral Motor Center)
    const subMat = this.createHullMaterial(NEUROANATOMY_REGIONS.subesophageal_mass.colorHex, 0.25);
    const subGeo = new THREE.SphereGeometry(7.8, 32, 24);
    subGeo.scale(1.15, 0.7, 1.05);
    const subMesh = new THREE.Mesh(subGeo, subMat);
    subMesh.position.set(0, -4.5, 0);
    this.group.add(subMesh);
    this.hullMeshes['subesophageal_mass'] = subMesh;

    // 5. Bilateral Optic Lobes Hulls (Left & Right Visual Cortices)
    const opticMat = this.createHullMaterial(NEUROANATOMY_REGIONS.optic_lobes.colorHex, 0.28);
    const sides = [-1, 1];
    for (const side of sides) {
      const opticGeo = new THREE.SphereGeometry(8.8, 32, 24);
      opticGeo.scale(0.98, 1.28, 0.92);
      const opticMesh = new THREE.Mesh(opticGeo, opticMat);
      opticMesh.position.set(side * 18.0, 3.5, -0.5);
      this.group.add(opticMesh);
    }

    // 6. Interbrachial Nerve Ring Tube Hull
    const ringMat = this.createHullMaterial(NEUROANATOMY_REGIONS.brachial_nerve_ring.colorHex, 0.3);
    const ringGeo = new THREE.TorusGeometry(13.0, 1.4, 16, 48);
    ringGeo.rotateX(Math.PI * 0.5);
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.position.set(0, -5.0, 0);
    this.group.add(ringMesh);
    this.hullMeshes['brachial_nerve_ring'] = ringMesh;

    // 7. 8 Arm Axial Nerve Cord Sheath Hulls
    const armMat = this.createHullMaterial(NEUROANATOMY_REGIONS.axial_nerve_cords.colorHex, 0.18);
    this.buildArmSheathHulls(armMat);
  }

  private buildArmSheathHulls(armMat: THREE.ShaderMaterial) {
    const numArms = 8;
    const ringRadius = 13.0;
    const startY = -5.5;
    const armLength = 55.0;

    for (let armIdx = 0; armIdx < numArms; armIdx++) {
      const baseAngle = (armIdx / 8) * Math.PI * 2;
      const numCtrl = 6;
      const splinePoints: THREE.Vector3[] = [];

      for (let c = 0; c < numCtrl; c++) {
        const t = c / (numCtrl - 1);
        const curveAngle = baseAngle + t * 0.45 * (armIdx % 2 === 0 ? 1 : -1);
        const r = ringRadius + t * armLength * 0.9;
        const x = r * Math.cos(curveAngle);
        const z = r * Math.sin(curveAngle);
        const y = startY - t * (armLength * 0.45) + Math.sin(t * Math.PI) * 4.0;
        splinePoints.push(new THREE.Vector3(x, y, z));
      }

      const armCurve = new THREE.CatmullRomCurve3(splinePoints);
      const tubeGeo = new THREE.TubeGeometry(armCurve, 36, 2.2, 12, false);
      const tubeMesh = new THREE.Mesh(tubeGeo, armMat);
      this.group.add(tubeMesh);
    }
  }

  public setOpacity(opacity: number) {
    for (const mat of this.materials) {
      mat.uniforms.uOpacity.value = opacity;
    }
  }

  public setVisible(visible: boolean) {
    this.group.visible = visible;
  }
}
