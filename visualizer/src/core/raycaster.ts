/** Interactive 3D Raycasting and Spatial Picking Engine for Neurons & Fibers. */

import * as THREE from 'three';
import type { OctopusConnectomeData, NeuronNode, NeuralFiber } from '../visual/octopus-generator';

export interface PickResult {
  type: 'node' | 'fiber';
  node?: NeuronNode;
  fiber?: NeuralFiber;
  sourceNode?: NeuronNode;
  targetNode?: NeuronNode;
  distance: number;
  hitPoint: THREE.Vector3;
}

export class ConnectomeRaycaster {
  private raycaster: THREE.Raycaster;
  private connectome: OctopusConnectomeData;
  private camera: THREE.Camera;
  private nodeThreshold: number = 1.6;
  private fiberThreshold: number = 0.9;
  public worldOffset: THREE.Vector3 = new THREE.Vector3(0, 0, 0);

  constructor(camera: THREE.Camera, connectome: OctopusConnectomeData) {
    this.camera = camera;
    this.connectome = connectome;
    this.raycaster = new THREE.Raycaster();
  }

  public setConnectome(connectome: OctopusConnectomeData, worldOffset?: THREE.Vector3) {
    this.connectome = connectome;
    if (worldOffset) {
      this.worldOffset.copy(worldOffset);
    } else {
      this.worldOffset.set(0, 0, 0);
    }
  }

  public setThreshold(threshold: number) {
    this.nodeThreshold = threshold;
  }

  public pickNode(pointerNDC: THREE.Vector2): { node: NeuronNode; distance: number; hitPoint: THREE.Vector3 } | null {
    this.raycaster.setFromCamera(pointerNDC, this.camera);
    const ray = this.raycaster.ray;

    let closestNode: NeuronNode | null = null;
    let closestRayDist = Infinity;

    const numNodes = this.connectome.nodes.length;
    const nodes = this.connectome.nodes;
    const hasOffset = this.worldOffset.lengthSq() > 0;

    for (let i = 0; i < numNodes; i++) {
      const node = nodes[i];
      const pt = hasOffset ? node.position.clone().add(this.worldOffset) : node.position;

      const distSq = ray.distanceSqToPoint(pt);
      const hitRadius = (node.type === 'ganglion_hub' ? 3.0 : node.type === 'sucker_receptor' ? 2.0 : 1.4) * (this.nodeThreshold * 0.75);

      if (distSq < hitRadius * hitRadius) {
        const rayDist = ray.origin.distanceTo(pt);
        if (rayDist < closestRayDist) {
          closestRayDist = rayDist;
          closestNode = node;
        }
      }
    }

    if (closestNode) {
      return {
        node: closestNode,
        distance: closestRayDist,
        hitPoint: closestNode.position.clone(),
      };
    }
    return null;
  }

  public pickFiber(pointerNDC: THREE.Vector2): { fiber: NeuralFiber; distance: number; hitPoint: THREE.Vector3 } | null {
    this.raycaster.setFromCamera(pointerNDC, this.camera);
    const ray = this.raycaster.ray;

    let closestFiber: NeuralFiber | null = null;
    let closestDist = Infinity;
    const bestHitPoint = new THREE.Vector3();

    const fibers = this.connectome.fibers;
    const numFibers = fibers.length;
    const threshSq = this.fiberThreshold * this.fiberThreshold;

    const vSeg = new THREE.Vector3();
    const vRayToP = new THREE.Vector3();
    const closestOnSeg = new THREE.Vector3();
    const closestOnRay = new THREE.Vector3();

    const hasOffset = this.worldOffset.lengthSq() > 0;

    for (let i = 0; i < numFibers; i++) {
      const fiber = fibers[i];
      const srcPos = this.connectome.nodes[fiber.sourceIndex].position;
      const tgtPos = this.connectome.nodes[fiber.targetIndex].position;
      const p1 = hasOffset ? srcPos.clone().add(this.worldOffset) : srcPos;
      const p2 = hasOffset ? tgtPos.clone().add(this.worldOffset) : tgtPos;

      // Fast midpoint check
      const midX = (p1.x + p2.x) * 0.5;
      const midY = (p1.y + p2.y) * 0.5;
      const midZ = (p1.z + p2.z) * 0.5;
      vSeg.set(midX, midY, midZ);

      if (ray.distanceSqToPoint(vSeg) > 25.0) continue;

      // Segment distance test
      vSeg.subVectors(p2, p1);
      const segLenSq = vSeg.lengthSq();
      if (segLenSq < 1e-4) continue;

      // Distance from ray to segment
      vRayToP.subVectors(p1, ray.origin);
      const d1 = ray.direction.dot(vSeg);
      const d2 = vSeg.dot(vRayToP);
      const d3 = ray.direction.dot(vRayToP);
      const denom = segLenSq - d1 * d1;

      let s = 0.5;
      if (Math.abs(denom) > 1e-5) {
        s = THREE.MathUtils.clamp((d1 * d3 - d2) / denom, 0.0, 1.0);
      }
      closestOnSeg.copy(p1).addScaledVector(vSeg, s);

      const t = Math.max(0, ray.direction.dot(closestOnSeg.clone().sub(ray.origin)));
      closestOnRay.copy(ray.origin).addScaledVector(ray.direction, t);

      const distSq = closestOnSeg.distanceToSquared(closestOnRay);
      if (distSq < threshSq) {
        const camDist = ray.origin.distanceTo(closestOnSeg);
        if (camDist < closestDist) {
          closestDist = camDist;
          closestFiber = fiber;
          bestHitPoint.copy(closestOnSeg);
        }
      }
    }

    if (closestFiber) {
      return {
        fiber: closestFiber,
        distance: closestDist,
        hitPoint: bestHitPoint,
      };
    }
    return null;
  }

  public pick(pointerNDC: THREE.Vector2): PickResult | null {
    const nodeHit = this.pickNode(pointerNDC);
    if (nodeHit) {
      return {
        type: 'node',
        node: nodeHit.node,
        distance: nodeHit.distance,
        hitPoint: nodeHit.hitPoint,
      };
    }

    const fiberHit = this.pickFiber(pointerNDC);
    if (fiberHit) {
      return {
        type: 'fiber',
        fiber: fiberHit.fiber,
        sourceNode: this.connectome.nodes[fiberHit.fiber.sourceIndex],
        targetNode: this.connectome.nodes[fiberHit.fiber.targetIndex],
        distance: fiberHit.distance,
        hitPoint: fiberHit.hitPoint,
      };
    }

    return null;
  }
}

