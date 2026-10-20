/** Neural Network GPU Renderer for Neuron Clouds, Synaptic Fibers, Neuropil Hulls & Puncta. */

import * as THREE from 'three';
import type { OctopusConnectomeData } from './octopus-generator';
import { NeuronParticleShader, SynapticFiberShader, SynapticPunctaShader } from './shaders';
import { NeuropilHullsManager } from './neuropil-hulls';
import { NEUROANATOMY_REGIONS } from '../data/neuroanatomy';

export class NeuralNetworkMesh {
  public group: THREE.Group;
  public connectome: OctopusConnectomeData;
  public neuropilHulls: NeuropilHullsManager;

  private pointsMesh: THREE.Points;
  private linesMesh: THREE.LineSegments;
  private punctaMesh: THREE.Points;

  private pointsMaterial: THREE.ShaderMaterial;
  private linesMaterial: THREE.ShaderMaterial;
  private punctaMaterial: THREE.ShaderMaterial;

  private highlightRoles: Float32Array;
  private fiberHighlights: Float32Array;

  // 3D Focus Reticle locator ring around selected neuron
  private reticleGroup: THREE.Group;
  private reticleRing: THREE.Mesh;
  private reticleCore: THREE.Mesh;

  private regionIdToIndex: Record<string, number> = {};

  constructor(connectome: OctopusConnectomeData) {
    this.connectome = connectome;
    this.group = new THREE.Group();

    // Map region IDs to uniform float indices
    let idx = 0;
    for (const rid in NEUROANATOMY_REGIONS) {
      this.regionIdToIndex[rid] = idx++;
    }

    const numNodes = connectome.nodes.length;
    const numFibers = connectome.fibers.length;

    this.highlightRoles = new Float32Array(numNodes);
    this.fiberHighlights = new Float32Array(numFibers * 2);

    // 0. Volumetric Neuropil Compartment Hulls (Google FlyWire Connectome style)
    this.neuropilHulls = new NeuropilHullsManager();
    this.group.add(this.neuropilHulls.group);

    // 1. Build Neuron Points Geometry & Shader Material
    const pointsGeo = new THREE.BufferGeometry();
    pointsGeo.setAttribute('position', new THREE.BufferAttribute(connectome.nodePositions, 3));
    pointsGeo.setAttribute('color', new THREE.BufferAttribute(connectome.nodeColors, 3));
    pointsGeo.setAttribute('aSize', new THREE.BufferAttribute(connectome.nodeSizes, 1));
    pointsGeo.setAttribute('aPhase', new THREE.BufferAttribute(connectome.nodePhases, 1));
    pointsGeo.setAttribute('aHighlightRole', new THREE.BufferAttribute(this.highlightRoles, 1));

    const regionIndices = new Float32Array(numNodes);
    const armIndices = new Float32Array(numNodes);

    for (let i = 0; i < numNodes; i++) {
      const n = connectome.nodes[i];
      regionIndices[i] = this.regionIdToIndex[n.regionId] ?? 0.0;
      armIndices[i] = n.armIndex;
    }

    pointsGeo.setAttribute('aRegionIndex', new THREE.BufferAttribute(regionIndices, 1));
    pointsGeo.setAttribute('aArmIndex', new THREE.BufferAttribute(armIndices, 1));

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
        uStimulusOrigin: { value: new THREE.Vector3(0, 0, 0) },
        uStimulusWaveRadius: { value: 0.0 },
        uStimulusIntensity: { value: 0.0 },
        uSelectedNodeIndex: { value: -1.0 },
      },
    });

    this.pointsMesh = new THREE.Points(pointsGeo, this.pointsMaterial);
    this.group.add(this.pointsMesh);

    // 2. Build Synaptic Lines Geometry & Shader Material
    const linesGeo = new THREE.BufferGeometry();
    linesGeo.setAttribute('position', new THREE.BufferAttribute(connectome.fiberLinePositions, 3));
    linesGeo.setAttribute('color', new THREE.BufferAttribute(connectome.fiberLineColors, 3));
    linesGeo.setAttribute('aFiberHighlight', new THREE.BufferAttribute(this.fiberHighlights, 1));

    const numFiberVerts = numFibers * 2;
    const fiberRegionIndices = new Float32Array(numFiberVerts);
    const fiberArmIndices = new Float32Array(numFiberVerts);

    for (let f = 0; f < numFibers; f++) {
      const fiber = connectome.fibers[f];
      const srcNode = connectome.nodes[fiber.sourceIndex];
      const rIdx = this.regionIdToIndex[fiber.regionId] ?? 0.0;
      const armIdx = srcNode.armIndex;

      fiberRegionIndices[f * 2 + 0] = rIdx;
      fiberRegionIndices[f * 2 + 1] = rIdx;
      fiberArmIndices[f * 2 + 0] = armIdx;
      fiberArmIndices[f * 2 + 1] = armIdx;
    }

    linesGeo.setAttribute('aRegionIndex', new THREE.BufferAttribute(fiberRegionIndices, 1));
    linesGeo.setAttribute('aArmIndex', new THREE.BufferAttribute(fiberArmIndices, 1));

    this.linesMaterial = new THREE.ShaderMaterial({
      vertexShader: SynapticFiberShader.vertexShader,
      fragmentShader: SynapticFiberShader.fragmentShader,
      vertexColors: true,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uTime: { value: 0.0 },
        uFiberGlow: { value: 1.0 },
        uIsolatedRegionIndex: { value: -1.0 },
        uHighlightedArmIndex: { value: -1.0 },
      },
    });

    this.linesMesh = new THREE.LineSegments(linesGeo, this.linesMaterial);
    this.group.add(this.linesMesh);

    // 3. Build Synaptic Puncta / Bouton Points (EM Connectome High-Density Synaptic Dots)
    const punctaGeo = new THREE.BufferGeometry();
    punctaGeo.setAttribute('position', new THREE.BufferAttribute(connectome.punctaPositions, 3));
    punctaGeo.setAttribute('color', new THREE.BufferAttribute(connectome.punctaColors, 3));

    this.punctaMaterial = new THREE.ShaderMaterial({
      vertexShader: SynapticPunctaShader.vertexShader,
      fragmentShader: SynapticPunctaShader.fragmentShader,
      vertexColors: true,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uTime: { value: 0.0 },
        uPunctaSize: { value: 2.2 },
        uPunctaAlpha: { value: 0.85 },
        uIsolatedRegionIndex: { value: -1.0 },
      },
    });

    this.punctaMesh = new THREE.Points(punctaGeo, this.punctaMaterial);
    this.group.add(this.punctaMesh);

    // 4. Build 3D Reticle Focus Locator
    this.reticleGroup = new THREE.Group();
    this.reticleGroup.visible = false;

    const ringGeo = new THREE.RingGeometry(0.5, 0.65, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xfacc15,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85,
    });
    this.reticleRing = new THREE.Mesh(ringGeo, ringMat);
    this.reticleGroup.add(this.reticleRing);

    const coreGeo = new THREE.SphereGeometry(0.18, 16, 16);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.95,
    });
    this.reticleCore = new THREE.Mesh(coreGeo, coreMat);
    this.reticleGroup.add(this.reticleCore);

    this.group.add(this.reticleGroup);
  }

  public setSelectedNeuron(nodeIndex: number | null) {
    this.highlightRoles.fill(0.0);
    this.fiberHighlights.fill(0.0);

    if (nodeIndex !== null && this.connectome.nodes[nodeIndex]) {
      const node = this.connectome.nodes[nodeIndex];
      this.highlightRoles[nodeIndex] = 1.0; // Target node

      // Upstream nodes (Cyan)
      for (const upIdx of node.upstreamNeighbors) {
        if (upIdx !== nodeIndex) {
          this.highlightRoles[upIdx] = 2.0;
        }
      }

      // Downstream nodes (Emerald)
      for (const downIdx of node.downstreamNeighbors) {
        if (downIdx !== nodeIndex) {
          this.highlightRoles[downIdx] = 3.0;
        }
      }

      // Highlight local incoming/outgoing fibers
      for (const fibIdx of [...node.incomingFiberIndices, ...node.outgoingFiberIndices]) {
        if (fibIdx < this.connectome.fibers.length) {
          this.fiberHighlights[fibIdx * 2 + 0] = 1.0;
          this.fiberHighlights[fibIdx * 2 + 1] = 1.0;
        }
      }

      // Position reticle
      this.reticleGroup.position.copy(node.position);
      this.reticleGroup.visible = true;
    } else {
      this.reticleGroup.visible = false;
    }

    this.pointsMesh.geometry.attributes.aHighlightRole.needsUpdate = true;
    this.linesMesh.geometry.attributes.aFiberHighlight.needsUpdate = true;
  }

  public setSelectedFiber(fiberIndex: number | null) {
    this.highlightRoles.fill(0.0);
    this.fiberHighlights.fill(0.0);

    if (fiberIndex !== null && this.connectome.fibers[fiberIndex]) {
      const fiber = this.connectome.fibers[fiberIndex];
      this.fiberHighlights[fiberIndex * 2 + 0] = 2.0;
      this.fiberHighlights[fiberIndex * 2 + 1] = 2.0;

      this.highlightRoles[fiber.sourceIndex] = 2.0; // Upstream
      this.highlightRoles[fiber.targetIndex] = 3.0; // Downstream

      const mid = new THREE.Vector3().addVectors(
        this.connectome.nodes[fiber.sourceIndex].position,
        this.connectome.nodes[fiber.targetIndex].position
      ).multiplyScalar(0.5);

      this.reticleGroup.position.copy(mid);
      this.reticleGroup.visible = true;
    } else {
      this.reticleGroup.visible = false;
    }

    this.pointsMesh.geometry.attributes.aHighlightRole.needsUpdate = true;
    this.linesMesh.geometry.attributes.aFiberHighlight.needsUpdate = true;
  }

  public update(time: number, stimulusOrigin: THREE.Vector3, waveRadius: number, stimulusIntensity: number, camera?: THREE.Camera) {
    this.pointsMaterial.uniforms.uTime.value = time;
    this.linesMaterial.uniforms.uTime.value = time;
    this.punctaMaterial.uniforms.uTime.value = time;

    this.pointsMaterial.uniforms.uStimulusOrigin.value.copy(stimulusOrigin);
    this.pointsMaterial.uniforms.uStimulusWaveRadius.value = waveRadius;
    this.pointsMaterial.uniforms.uStimulusIntensity.value = stimulusIntensity;

    if (this.reticleGroup.visible && camera) {
      this.reticleRing.lookAt(camera.position);
      const scale = 1.0 + Math.sin(time * 5.0) * 0.15;
      this.reticleRing.scale.set(scale, scale, scale);
    }
  }

  public setIsolatedRegion(regionId: string | null) {
    const val = regionId ? (this.regionIdToIndex[regionId] ?? -1.0) : -1.0;
    this.pointsMaterial.uniforms.uIsolatedRegionIndex.value = val;
    this.linesMaterial.uniforms.uIsolatedRegionIndex.value = val;
    this.punctaMaterial.uniforms.uIsolatedRegionIndex.value = val;
  }

  public setHighlightedArm(armIndex: number | null) {
    const val = armIndex !== null ? floatValue(armIndex) : -1.0;
    this.pointsMaterial.uniforms.uHighlightedArmIndex.value = val;
    this.linesMaterial.uniforms.uHighlightedArmIndex.value = val;
  }

  public setNeuralActivity(intensity: number) {
    this.pointsMaterial.uniforms.uActivityIntensity.value = intensity;
  }

  public setFiberGlow(glow: number) {
    this.linesMaterial.uniforms.uFiberGlow.value = glow;
  }

  public setFibersVisible(visible: boolean) {
    this.linesMesh.visible = visible;
  }

  public setNeuropilHullOpacity(opacity: number) {
    this.neuropilHulls.setOpacity(opacity);
  }

  public setNeuropilHullsVisible(visible: boolean) {
    this.neuropilHulls.setVisible(visible);
  }

  public setPunctaVisible(visible: boolean) {
    this.punctaMesh.visible = visible;
  }

  public setPunctaAlpha(alpha: number) {
    this.punctaMaterial.uniforms.uPunctaAlpha.value = alpha;
  }
}

function floatValue(val: number): number {
  return typeof val === 'number' ? val : -1.0;
}


