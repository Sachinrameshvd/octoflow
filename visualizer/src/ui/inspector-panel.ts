/** Scientific Inspector Panel for Cephalopod Neuroanatomy, Neurons & Synaptic Fibers. */

import { NEUROANATOMY_REGIONS } from '../data/neuroanatomy';
import type { BrainRegionInfo } from '../data/neuroanatomy';
import type { NeuronNode, NeuralFiber } from '../visual/octopus-generator';
import { ICONS } from './icons';

export type InspectorMode = 'REGION' | 'NEURON' | 'FIBER';

export class InspectorPanel {
  private container: HTMLElement;
  private mode: InspectorMode = 'REGION';

  private currentRegion: BrainRegionInfo | null = null;
  private currentNode: NeuronNode | null = null;
  private currentFiber: NeuralFiber | null = null;
  private sourceNode: NeuronNode | null = null;
  private targetNode: NeuronNode | null = null;
  private allNodes: NeuronNode[] = [];

  public onIsolateRegion?: (regionId: string | null) => void;
  public onFocusCamera?: (regionId: string) => void;
  public onFocusNeuron?: (node: NeuronNode, microZoom?: boolean) => void;
  public onFocusFiber?: (source: NeuronNode, target: NeuronNode) => void;
  public onStimulateNode?: (nodeIndex: number) => void;
  public onStimulateFiber?: (fiberIndex: number) => void;
  public onSelectNeuron?: (nodeIndex: number) => void;
  public onOpenManual?: (context: string) => void;

  constructor(containerId: string = 'inspector-panel') {
    this.container = document.getElementById(containerId) || document.body;
  }

  public setNodesReference(nodes: NeuronNode[]) {
    this.allNodes = nodes;
  }

  public showRegion(regionId: string, node?: NeuronNode) {
    const info = NEUROANATOMY_REGIONS[regionId];
    if (!info) return;

    this.mode = 'REGION';
    this.currentRegion = info;
    this.currentNode = node || null;
    this.currentFiber = null;
    this.render();
  }

  public showNeuron(node: NeuronNode) {
    this.mode = 'NEURON';
    this.currentNode = node;
    this.currentRegion = NEUROANATOMY_REGIONS[node.regionId] || null;
    this.currentFiber = null;
    this.render();
  }

  public showFiber(fiber: NeuralFiber, sourceNode: NeuronNode, targetNode: NeuronNode) {
    this.mode = 'FIBER';
    this.currentFiber = fiber;
    this.sourceNode = sourceNode;
    this.targetNode = targetNode;
    this.currentRegion = NEUROANATOMY_REGIONS[fiber.regionId] || null;
    this.render();
  }

  public show() {
    this.container.classList.remove('hidden');
  }

  public hide() {
    this.currentRegion = null;
    this.currentNode = null;
    this.currentFiber = null;
    this.container.classList.add('hidden');
  }

  private render() {
    if (this.mode === 'NEURON' && this.currentNode) {
      this.renderNeuronView();
    } else if (this.mode === 'FIBER' && this.currentFiber && this.sourceNode && this.targetNode) {
      this.renderFiberView();
    } else if (this.currentRegion) {
      this.renderRegionView();
    }
    this.container.classList.remove('hidden');
    this.bindEvents();
  }

  private renderNeuronView() {
    const n = this.currentNode!;
    const r = this.currentRegion;
    const regionName = r ? r.name : n.regionId;

    const upNodes = n.upstreamNeighbors.map((idx) => this.allNodes[idx]).filter(Boolean);
    const downNodes = n.downstreamNeighbors.map((idx) => this.allNodes[idx]).filter(Boolean);

    this.container.innerHTML = `
      <div class="inspector-header">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="window-drag-icon">${ICONS.dragGrip(14, 'rgba(255,255,255,0.6)')}</span>
          <div class="inspector-tag badge-neuron">
            NEURON SOMA #${n.index}
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <button class="btn-window-minimize" title="Minimize / Expand Window">${ICONS.minimize(11, 'rgba(255,255,255,0.8)')}</button>
          <button id="btn-close-inspector" class="btn-close" title="Close Inspector">${ICONS.closeCross(12, '#cbd5e1')}</button>
        </div>
      </div>

      <div class="window-body-scroll">
        <h2 class="inspector-title">${n.type.toUpperCase().replace('_', ' ')} #${n.index}</h2>
      <div class="inspector-systematic">Located in: ${regionName}</div>

      <!-- 3D Coordinate Telemetry -->
      <div class="telemetry-bar">
        <div class="telemetry-item">
          <span class="telemetry-label">3D Spatial Position</span>
          <span class="telemetry-val telemetry-coords">
            X: ${n.position.x.toFixed(2)}, Y: ${n.position.y.toFixed(2)}, Z: ${n.position.z.toFixed(2)}
          </span>
        </div>
        <div class="telemetry-item">
          <span class="telemetry-label">Morphological Scale</span>
          <span class="telemetry-val">${(n.size * 8.5).toFixed(1)} µm</span>
        </div>
      </div>

      <!-- Anatomical Context -->
      <div class="inspector-section">
        <h3>Anatomical Context</h3>
        <div class="tags-container">
          <span class="tag tag-input">${n.armIndex >= 0 ? `Arm ${n.armIndex + 1}` : 'Central Cranial Mass'}</span>
          <span class="tag tag-output">${n.segmentIndex >= 0 ? `Sucker Segment ${n.segmentIndex + 1}` : 'Supra/Subesophageal Neuropil'}</span>
          <span class="tag tag-nt">${n.neighbors.length} Total Synaptic Links</span>
        </div>
      </div>

      <!-- Local Microcircuit Flow Diagram -->
      <div class="inspector-section">
        <h3>Local Synaptic Microcircuit</h3>
        <div class="circuit-flow-container">
          <div class="circuit-column">
            <div class="circuit-col-title">PRE-SYNAPTIC (${upNodes.length})</div>
            <div class="circuit-node-list">
              ${upNodes.slice(0, 4).map((up) => `
                <button class="btn-micro-node btn-up" data-node="${up.index}">#${up.index} (${up.type.substring(0, 4)})</button>
              `).join('')}
              ${upNodes.length > 4 ? `<div class="more-nodes">+${upNodes.length - 4} more</div>` : ''}
              ${upNodes.length === 0 ? `<div class="more-nodes">Sensory Receptor</div>` : ''}
            </div>
          </div>

          <div class="circuit-arrow">${ICONS.flowArrow(12, 'rgba(255,255,255,0.4)')}</div>

          <div class="circuit-column target-col">
            <div class="circuit-col-title target-title">TARGET SOMA</div>
            <div class="target-node-box">
              <strong>#${n.index}</strong>
              <small>${n.type}</small>
            </div>
          </div>

          <div class="circuit-arrow">${ICONS.flowArrow(12, 'rgba(255,255,255,0.4)')}</div>

          <div class="circuit-column">
            <div class="circuit-col-title">POST-SYNAPTIC (${downNodes.length})</div>
            <div class="circuit-node-list">
              ${downNodes.slice(0, 4).map((dn) => `
                <button class="btn-micro-node btn-down" data-node="${dn.index}">#${dn.index} (${dn.type.substring(0, 4)})</button>
              `).join('')}
              ${downNodes.length > 4 ? `<div class="more-nodes">+${downNodes.length - 4} more</div>` : ''}
              ${downNodes.length === 0 ? `<div class="more-nodes">Motor Efferent</div>` : ''}
            </div>
          </div>
        </div>
      </div>

      <!-- Action Potential Trigger -->
      <button id="btn-stimulate-neuron" class="btn-action pulse btn-action-stimulate">
        ${ICONS.actionPotential(14, '#fab387')}
        <span>Trigger Action Potential Cascade</span>
      </button>

      <!-- Navigation Actions -->
      <div class="inspector-actions">
        <button id="btn-focus-neuron" class="btn-action">
          ${ICONS.spatialOrbit(14, '#89dceb')}
          <span>Orbit Around Neuron</span>
        </button>
        <button id="btn-micro-zoom" class="btn-action">
          ${ICONS.customProbe(14, '#89dceb')}
          <span>Micron LOD Zoom</span>
        </button>
      </div>

      <!-- Disclaimer -->
      <div class="disclaimer-box" style="margin-top: 6px;">
        <strong>Connectome Level:</strong> Detailed computational approximation of local cephalopod microcircuit branching.
      </div>
      </div>
    `;
  }

  private renderFiberView() {
    const f = this.currentFiber!;
    const src = this.sourceNode!;
    const tgt = this.targetNode!;
    const r = this.currentRegion;

    const statusBadge =
      f.biologicalStatus === 'known'
        ? '<span class="data-badge badge-known">● Known Biological Tract</span>'
        : f.biologicalStatus === 'inferred'
        ? '<span class="data-badge badge-inferred">● Scientifically Inferred</span>'
        : '<span class="data-badge badge-approx">● Computational Approximation</span>';

    this.container.innerHTML = `
      <div class="inspector-header">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="window-drag-icon">${ICONS.dragGrip(14, 'rgba(255,255,255,0.6)')}</span>
          <div class="inspector-tag badge-fiber">
            SYNAPTIC FIBER #${f.index}
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <button class="btn-window-minimize" title="Minimize / Expand Window">${ICONS.minimize(11, 'rgba(255,255,255,0.8)')}</button>
          <button id="btn-close-inspector" class="btn-close" title="Close Inspector">${ICONS.closeCross(12, '#cbd5e1')}</button>
        </div>
      </div>

      <div class="window-body-scroll">
        <h2 class="inspector-title">${f.pathwayName}</h2>
      <div class="inspector-systematic">${f.type.toUpperCase()} CONNECTION</div>

      ${statusBadge}

      <!-- Synaptic Telemetry -->
      <div class="telemetry-bar">
        <div class="telemetry-item">
          <span class="telemetry-label">Synaptic Conductance</span>
          <span class="telemetry-val" style="color: var(--accent-cyan);">${(f.synapticWeight * 100).toFixed(0)}% (${(f.synapticWeight * 48.0).toFixed(1)} nS)</span>
        </div>
        <div class="telemetry-item">
          <span class="telemetry-label">Transmission Vector</span>
          <span class="telemetry-val" style="text-transform: uppercase;">${f.direction}</span>
        </div>
      </div>

      <!-- Endpoint Cards -->
      <div class="inspector-section">
        <h3>Connected Synaptic Endpoints</h3>
        <div class="endpoint-card">
          <div class="endpoint-header">
            <span>PRE-SYNAPTIC ORIGIN</span>
            <button class="btn-link" id="btn-inspect-src">Inspect Soma #${src.index}</button>
          </div>
          <div class="endpoint-body">
            <strong>Neuron #${src.index}</strong> (${src.type}) in ${r ? r.name : src.regionId}
          </div>
        </div>

        <div class="endpoint-card" style="margin-top: 8px;">
          <div class="endpoint-header">
            <span>POST-SYNAPTIC TARGET</span>
            <button class="btn-link" id="btn-inspect-tgt">Inspect Soma #${tgt.index}</button>
          </div>
          <div class="endpoint-body">
            <strong>Neuron #${tgt.index}</strong> (${tgt.type}) in ${tgt.armIndex >= 0 ? `Arm ${tgt.armIndex + 1}` : 'Central Mass'}
          </div>
        </div>
      </div>

      <!-- Trigger Action Potential -->
      <button id="btn-stimulate-fiber" class="btn-action pulse btn-action-fiber">
        ${ICONS.actionPotential(14, '#89dceb')}
        <span>Fire Action Potential Along Fiber</span>
      </button>

      <!-- Camera Action -->
      <div class="inspector-actions">
        <button id="btn-focus-fiber" class="btn-action">
          ${ICONS.spatialOrbit(14, '#89dceb')}
          <span>Focus Camera on Connection</span>
        </button>
      </div>

      <!-- Scientific Disclaimer -->
      <div class="disclaimer-box" style="margin-top: 8px;">
        <strong>Scientific Framing:</strong> Computational approximation — not an exact biological connectome.
      </div>
      </div>
    `;
  }

  private renderRegionView() {
    const r = this.currentRegion!;

    const badgeClass =
      r.dataClassification === 'known'
        ? 'badge-known'
        : r.dataClassification === 'inferred'
        ? 'badge-inferred'
        : 'badge-approx';

    this.container.innerHTML = `
      <div class="inspector-header">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="window-drag-icon">${ICONS.dragGrip(14, 'rgba(255,255,255,0.6)')}</span>
          <div class="inspector-tag" style="background: ${r.colorHex}22; color: ${r.colorHex}; border-color: ${r.colorHex}55;">
            ${r.categoryLabel}
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <button class="btn-window-minimize" title="Minimize / Expand Window">${ICONS.minimize(11, 'rgba(255,255,255,0.8)')}</button>
          <button id="btn-close-inspector" class="btn-close" title="Close Inspector">${ICONS.closeCross(12, '#cbd5e1')}</button>
        </div>
      </div>

      <div class="window-body-scroll">
        <h2 class="inspector-title">${r.name}</h2>
      <div class="inspector-systematic">${r.systematicName}</div>

      <!-- Data Classification Badge -->
      <div class="data-badge ${badgeClass}">
        <span class="badge-icon">●</span> ${r.classificationLabel}
      </div>

      <!-- Scientific Disclaimer Box -->
      <div class="disclaimer-box">
        <strong>Scientific Framing:</strong> ${r.disclaimer}
      </div>

      <!-- Neuron Population Telemetry -->
      <div class="telemetry-bar">
        <div class="telemetry-item">
          <span class="telemetry-label">Neuron Population</span>
          <span class="telemetry-val" style="color: ${r.colorHex};">${r.neuronCountEstimate}</span>
        </div>
        <div class="telemetry-item">
          <span class="telemetry-label">Share of Nervous System</span>
          <span class="telemetry-val">${r.percentageOfNervousSystem}</span>
        </div>
      </div>

      <!-- Biological Role -->
      <div class="inspector-section">
        <h3>Biological Role & Neuroethology</h3>
        <p>${r.biologicalRole}</p>
      </div>

      <!-- Afferent & Efferent Pathways -->
      <div class="inspector-section">
        <h3>Circuit Afferents & Efferents</h3>
        <div class="pathway-group">
          <div class="pathway-title">Afferent Inputs:</div>
          <div class="tags-container">
            ${r.inputs.map((inp) => `<span class="tag tag-input">${inp}</span>`).join('')}
          </div>
        </div>
        <div class="pathway-group" style="margin-top: 8px;">
          <div class="pathway-title">Efferent Outputs:</div>
          <div class="tags-container">
            ${r.outputs.map((out) => `<span class="tag tag-output">${out}</span>`).join('')}
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="inspector-actions">
        <button id="btn-isolate-region" class="btn-action">
          ${ICONS.customProbe(14, '#38bdf8')}
          <span>Isolate This Region</span>
        </button>
        <button id="btn-focus-camera" class="btn-action">
          ${ICONS.spatialOrbit(14, '#38bdf8')}
          <span>Focus Camera</span>
        </button>
        <button id="btn-open-region-manual" class="btn-action" style="background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.5); color: #f59e0b;">
          <span>📖 View Manual For This Area</span>
        </button>
      </div>

      <!-- Scientific Citations -->
      <div class="inspector-section citations">
        <h3>Key References</h3>
        <ul>
          ${r.scientificReferences.map((ref) => `<li>${ref}</li>`).join('')}
        </ul>
      </div>
      </div>
    `;
  }

  private bindEvents() {
    const btnClose = this.container.querySelector('#btn-close-inspector');
    if (btnClose) {
      btnClose.addEventListener('click', () => this.hide());
    }

    // Region handlers
    const btnIsolate = this.container.querySelector('#btn-isolate-region');
    if (btnIsolate && this.currentRegion) {
      btnIsolate.addEventListener('click', () => {
        if (this.onIsolateRegion) {
          this.onIsolateRegion(this.currentRegion!.id);
        }
      });
    }

    const btnFocus = this.container.querySelector('#btn-focus-camera');
    if (btnFocus && this.currentRegion) {
      btnFocus.addEventListener('click', () => {
        if (this.onFocusCamera) {
          this.onFocusCamera(this.currentRegion!.id);
        }
      });
    }

    const btnRegManual = this.container.querySelector('#btn-open-region-manual');
    if (btnRegManual && this.currentRegion) {
      btnRegManual.addEventListener('click', () => {
        this.onOpenManual?.(this.currentRegion!.id);
      });
    }

    // Neuron handlers
    const btnStimNeuron = this.container.querySelector('#btn-stimulate-neuron');
    if (btnStimNeuron && this.currentNode) {
      btnStimNeuron.addEventListener('click', () => {
        if (this.onStimulateNode) {
          this.onStimulateNode(this.currentNode!.index);
        }
      });
    }

    const btnFocusNeuron = this.container.querySelector('#btn-focus-neuron');
    if (btnFocusNeuron && this.currentNode) {
      btnFocusNeuron.addEventListener('click', () => {
        if (this.onFocusNeuron) {
          this.onFocusNeuron(this.currentNode!, false);
        }
      });
    }

    const btnMicroZoom = this.container.querySelector('#btn-micro-zoom');
    if (btnMicroZoom && this.currentNode) {
      btnMicroZoom.addEventListener('click', () => {
        if (this.onFocusNeuron) {
          this.onFocusNeuron(this.currentNode!, true);
        }
      });
    }

    // Microcircuit node jump buttons
    this.container.querySelectorAll('.btn-micro-node').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const nodeIdx = parseInt((e.currentTarget as HTMLElement).getAttribute('data-node') || '-1', 10);
        if (nodeIdx >= 0 && this.onSelectNeuron) {
          this.onSelectNeuron(nodeIdx);
        }
      });
    });

    // Fiber handlers
    const btnStimFiber = this.container.querySelector('#btn-stimulate-fiber');
    if (btnStimFiber && this.currentFiber) {
      btnStimFiber.addEventListener('click', () => {
        if (this.onStimulateFiber) {
          this.onStimulateFiber(this.currentFiber!.index);
        }
      });
    }

    const btnFocusFiber = this.container.querySelector('#btn-focus-fiber');
    if (btnFocusFiber && this.sourceNode && this.targetNode) {
      btnFocusFiber.addEventListener('click', () => {
        if (this.onFocusFiber) {
          this.onFocusFiber(this.sourceNode!, this.targetNode!);
        }
      });
    }

    const btnInspectSrc = this.container.querySelector('#btn-inspect-src');
    if (btnInspectSrc && this.sourceNode && this.onSelectNeuron) {
      btnInspectSrc.addEventListener('click', () => {
        this.onSelectNeuron!(this.sourceNode!.index);
      });
    }

    const btnInspectTgt = this.container.querySelector('#btn-inspect-tgt');
    if (btnInspectTgt && this.targetNode && this.onSelectNeuron) {
      btnInspectTgt.addEventListener('click', () => {
        this.onSelectNeuron!(this.targetNode!.index);
      });
    }
  }
}

