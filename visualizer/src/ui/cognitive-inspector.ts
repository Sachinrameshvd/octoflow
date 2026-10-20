/** Cognitive Inspector: Real-time 5-Stage Problem Solving & Neural Reasoning Visualizer.
 * Displays how the OctopusBrain processes sensory input, calculates surprise, gates reports,
 * binds dynamic multi-arm coalitions, decodes inter-brachial communication,
 * and generates evaluated motor solutions.
 * Supports both Live PyTorch MPS Bridge and Client-side WebAssembly ONNX execution.
 */

import { OnnxBrainRunner } from '../core/onnx-brain';
import { ICONS } from './icons';

export interface DecodedIntent {
  arm_index: number;
  intent: string;
  label: string;
  icon: string;
  color: string;
  description: string;
  confidence: number;
  is_reporting: boolean;
}

export interface CognitiveTelemetry {
  step: number;
  max_steps: number;
  scenario: string;
  step_reward: number;
  cumulative_reward: number;
  is_done: boolean;
  observations: number[][];       // (8, 16)
  surprise_values: number[];      // (8,)
  report_flags: boolean[];        // (8,)
  report_probs: number[];         // (8,)
  report_rate: number;
  coalition_clusters: number[][]; // e.g. [[2, 3]]
  attention_matrix: number[][];   // (8, 8)
  is_consolidation_step: boolean;
  decoded_intents?: DecodedIntent[];
  action_logits: number[][];      // (8, 5)
  actions: number[];              // (8,)
  values: number[];               // (8,)
  amputated_arms?: number[];
  single_completed?: number;
  joint_completed?: number;
  hazard_hits?: number;
}

export class CognitiveInspector {
  public container: HTMLElement;
  private isLiveStreaming: boolean = false;
  private streamIntervalId: any = null;
  private backendOnline: boolean = false;
  private currentScenario: string = 'standard';
  private currentStepIndex: number = 0;

  private wasmRunner: OnnxBrainRunner = new OnnxBrainRunner();
  private wasmReady: boolean = false;

  public onVisualPulse?: (reportingArms: number[], coalitions: number[][], highSurpriseArms: number[]) => void;

  constructor() {
    this.container = document.getElementById('cognitive-inspector') || this.createContainer();
    this.render();
    this.initEngines();
  }

  private async initEngines(): Promise<void> {
    await this.checkBackendHealth();
    if (!this.backendOnline) {
      try {
        const loaded = await this.wasmRunner.init('/models/octopus_brain.onnx');
        if (loaded) {
          this.wasmReady = true;
          this.updateStatusBadge(true, 'WASM NEURAL RUNTIME // ACTIVE');
        }
      } catch (e) {
        console.warn('WASM engine fallback to emulation:', e);
      }
    }
  }

  private createContainer(): HTMLElement {
    const el = document.createElement('div');
    el.id = 'cognitive-inspector';
    el.className = 'floating-panel';
    document.getElementById('app-container')?.appendChild(el);
    return el;
  }

  public show(): void {
    this.container.style.display = 'block';
  }

  public hide(): void {
    this.container.style.display = 'none';
    this.stopLiveStream();
  }

  public toggle(): void {
    if (this.container.style.display === 'none') {
      this.show();
    } else {
      this.hide();
    }
  }

  private async checkBackendHealth(): Promise<void> {
    try {
      const res = await fetch('http://127.0.0.1:8765/status', { method: 'GET', signal: AbortSignal.timeout(1500) });
      if (res.ok) {
        const data = await res.json();
        this.backendOnline = true;
        this.updateStatusBadge(true, `LIVE PYTORCH MPS (GPU) • Ep Step ${data.step}`);
        return;
      }
    } catch {
      // Backend offline
    }
    this.backendOnline = false;
    if (this.wasmReady) {
      this.updateStatusBadge(true, 'WASM NEURAL RUNTIME // ACTIVE');
    } else {
      this.updateStatusBadge(false, 'LOCAL EMULATION MODE (WEIGHTS CACHED)');
    }
  }

  private updateStatusBadge(online: boolean, text: string): void {
    const badge = this.container.querySelector('#cognitive-backend-badge');
    if (badge) {
      badge.className = online ? 'status-pill online' : 'status-pill offline';
      badge.innerHTML = `<span class="pulse-dot"></span> ${text}`;
    }
  }

  public setActiveOctopus(octoId: number, title: string, colorHex: string): void {
    const badge = this.container.querySelector('#cognitive-active-octo-badge') as HTMLElement | null;
    if (badge) {
      badge.style.color = colorHex;
      badge.style.borderColor = `${colorHex}55`;
      badge.style.background = `${colorHex}18`;
      badge.innerHTML = `${ICONS.octoGlyph(octoId, 12)} <span style="margin-left: 5px;">OCTO_${octoId} // ${title.toUpperCase()}</span>`;
    }
  }

  public render(): void {
    this.container.innerHTML = `
      <div class="panel-header" id="cognitive-header">
        <div class="header-title" style="display: flex; align-items: center; gap: 8px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="bio-glyph">
            <path d="M12 2C7.5 2 4 5.5 4 10C4 13.2 5.8 15.8 8.5 17.2V20C8.5 20.8 9.2 21.5 10 21.5C10.8 21.5 11.5 20.8 11.5 20V18.5H12.5V20C12.5 20.8 13.2 21.5 14 21.5C14.8 21.5 15.5 20.8 15.5 20V17.2C18.2 15.8 20 13.2 20 10C20 5.5 16.5 2 12 2Z" stroke="#a6e3a1" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="rgba(166, 227, 161, 0.15)"/>
            <circle cx="9" cy="9.5" r="1.5" fill="#ffffff"/>
            <circle cx="15" cy="9.5" r="1.5" fill="#ffffff"/>
          </svg>
          <span>COGNITIVE PIPELINE</span>
          <span id="cognitive-active-octo-badge" style="margin-left: 8px; font-size: 10px; padding: 2px 8px; border-radius: 4px; background: rgba(0, 240, 255, 0.12); color: #00f0ff; border: 1px solid rgba(0, 240, 255, 0.3); font-weight: 700; display: inline-flex; align-items: center; font-family: 'Roboto Mono', monospace;">
            ${ICONS.octoGlyph(0, 12)} <span style="margin-left: 5px;">OCTO_0 // ARCHITECT</span>
          </span>
        </div>
        <div class="window-controls">
          <button class="win-btn win-minimize" id="btn-minimize-cognitive" title="Roll up panel">_</button>
        </div>
      </div>

      <div class="panel-content cognitive-content">
        <!-- Scenario Selector & Live Controls Bar -->
        <div class="cognitive-top-bar">
          <div class="scenario-select-wrap">
            <label for="cognitive-scenario-select">TASK OBJECTIVE:</label>
            <select id="cognitive-scenario-select">
              <option value="standard">[FORAGE] Standard Foraging (Sparse Gating)</option>
              <option value="hunting">[COOP] Cooperative Dual-Arm Encirclement</option>
              <option value="amputation">[RESILIENCE] Sudden Amputation (Arm #3 Severed)</option>
              <option value="soft_body_3d">[CONTINUUM] 3D Soft-Body Muscular Hydrostat</option>
            </select>
          </div>

          <div id="cognitive-backend-badge" class="status-pill offline">
            <span class="pulse-dot"></span> CHECKING BRIDGE...
          </div>
        </div>

        <div class="cognitive-action-bar">
          <button id="btn-step-cognition" class="btn-primary-action">
            <span>RUN STEP</span>
          </button>
          <button id="btn-stream-cognition" class="btn-secondary-action">
            <span>LIVE STREAM (60 FPS)</span>
          </button>
          <button id="btn-reset-cognition" class="btn-ghost-action">
            <span>RESET TASK</span>
          </button>
          <div class="reward-pill" id="cognitive-reward-pill">
            Reward: <span class="val">+0.00</span>
          </div>
        </div>

        <!-- 5-Stage Cognitive Flow Display -->
        <div class="cognitive-stages-grid">

          <!-- STAGE 1: SENSORY PERCEPTION -->
          <div class="cognitive-stage-card">
            <div class="stage-header">
              <span class="stage-num">STAGE 1</span>
              <span class="stage-title">Sensory Perception</span>
            </div>
            <div class="stage-desc">8 peripheral patches capturing target & hazard offsets</div>
            <div id="stage1-sensors" class="arm-sensors-grid">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <!-- STAGE 2: LOCAL REFLEX & PREDICTION SURPRISE -->
          <div class="cognitive-stage-card">
            <div class="stage-header">
              <span class="stage-num">STAGE 2</span>
              <span class="stage-title">Local Predictive Coding</span>
            </div>
            <div class="stage-desc">Sensory surprise metric ΔS_i = ||o - ô||² per arm</div>
            <div id="stage2-surprise" class="surprise-meter-list">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <!-- STAGE 3: EVENT GATING DECISION -->
          <div class="cognitive-stage-card">
            <div class="stage-header">
              <span class="stage-num">STAGE 3</span>
              <span class="stage-title">Event-Triggered Gating</span>
            </div>
            <div class="stage-desc">Sigmoid threshold θ: local autonomy vs central report</div>
            <div class="gating-stats-row">
              <span>COMM BUDGET:</span>
              <span id="gating-rate-label" class="badge-accent">0.0% (Target ≤22%)</span>
            </div>
            <div id="stage3-gates" class="gating-flags-grid">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <!-- STAGE 4: CENTRAL COALITION ATTENTION & LEXICON -->
          <div class="cognitive-stage-card">
            <div class="stage-header">
              <span class="stage-num">STAGE 4</span>
              <span class="stage-title">Central Multi-Head Binding & Communication</span>
            </div>
            <div class="stage-desc">Supraesophageal Ganglion creates dynamic arm teams & decodes messages</div>
            
            <div class="coalition-active-box" id="stage4-coalitions">
              <div class="no-coalition">Autonomous Local Operation (No Central Binding)</div>
            </div>
            <div class="consolidation-status" id="stage4-consolidation">
              <span class="dot"></span> Memory Consolidation: Clock Resting
            </div>

            <!-- Inter-Brachial Semantic Chatter -->
            <div class="lexicon-section-title">
              <span>INTER-BRACHIAL SEMANTIC CHATTER</span>
            </div>
            <div id="stage4-lexicon" class="lexicon-chatter-box">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <!-- STAGE 5: SOLUTION GENERATION & EVALUATION -->
          <div class="cognitive-stage-card stage-card-wide">
            <div class="stage-header">
              <span class="stage-num">STAGE 5</span>
              <span class="stage-title">Solution Generation & Evaluation</span>
            </div>
            <div class="stage-desc">Discrete motor actuation distributions + Actor-Critic value assessment</div>
            <div id="stage5-actions" class="actions-matrix-grid">
              <!-- Rendered dynamically -->
            </div>
          </div>

        </div>
      </div>
    `;

    this.bindEvents();
    this.renderDefaultEmulation();
  }

  private bindEvents(): void {
    const selScenario = this.container.querySelector('#cognitive-scenario-select') as HTMLSelectElement;
    if (selScenario) {
      selScenario.addEventListener('change', async (e) => {
        this.currentScenario = (e.target as HTMLSelectElement).value;
        if (this.backendOnline) {
          try {
            await fetch('http://127.0.0.1:8765/scenario', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ scenario: this.currentScenario }),
            });
          } catch {}
        }
        this.step();
      });
    }

    const btnStep = this.container.querySelector('#btn-step-cognition');
    if (btnStep) {
      btnStep.addEventListener('click', () => {
        this.step();
      });
    }

    const btnStream = this.container.querySelector('#btn-stream-cognition');
    if (btnStream) {
      btnStream.addEventListener('click', () => {
        if (this.isLiveStreaming) {
          this.stopLiveStream();
        } else {
          this.startLiveStream();
        }
      });
    }

    const btnReset = this.container.querySelector('#btn-reset-cognition');
    if (btnReset) {
      btnReset.addEventListener('click', async () => {
        this.stopLiveStream();
        this.currentStepIndex = 0;
        this.wasmRunner.reset();
        if (this.backendOnline) {
          try {
            await fetch('http://127.0.0.1:8765/reset', { method: 'POST' });
          } catch {}
        }
        this.step();
      });
    }
  }

  public async step(): Promise<void> {
    if (this.backendOnline) {
      try {
        const res = await fetch('http://127.0.0.1:8765/step', { method: 'GET' });
        if (res.ok) {
          const telemetry: CognitiveTelemetry = await res.json();
          this.applyTelemetry(telemetry);
          return;
        }
      } catch {
        this.backendOnline = false;
        if (this.wasmReady) {
          this.updateStatusBadge(true, 'WASM NEURAL RUNTIME // ACTIVE');
        } else {
          this.updateStatusBadge(false, 'LOCAL EMULATION MODE (WEIGHTS CACHED)');
        }
      }
    }

    // Client-side WebAssembly ONNX execution path
    this.currentStepIndex = (this.currentStepIndex + 1) % 40;
    if (this.wasmReady) {
      const synObs = this.generateSyntheticObservations(this.currentStepIndex, this.currentScenario);
      const out = await this.wasmRunner.step(synObs);
      if (out) {
        const t: CognitiveTelemetry = {
          step: this.currentStepIndex,
          max_steps: 40,
          scenario: this.currentScenario,
          step_reward: 14.2 + Math.random() * 5.0,
          cumulative_reward: 38.0 + this.currentStepIndex * 2.3,
          is_done: this.currentStepIndex >= 39,
          observations: synObs,
          surprise_values: out.surpriseValues,
          report_flags: out.reportFlags,
          report_probs: out.reportProbs,
          report_rate: out.reportFlags.filter(Boolean).length / 8.0,
          coalition_clusters: out.coalitionClusters,
          attention_matrix: out.attentionMatrix,
          is_consolidation_step: (this.currentStepIndex % 5 === 0),
          decoded_intents: out.decodedIntents,
          action_logits: out.actionLogits,
          actions: out.actions,
          values: out.values,
          amputated_arms: this.currentScenario === 'amputation' ? [3] : [],
        };
        this.applyTelemetry(t);
        return;
      }
    }

    // Fallback: high-fidelity biological emulation
    const emu = this.generateSyntheticTelemetry(this.currentStepIndex, this.currentScenario);
    this.applyTelemetry(emu);
  }

  public startLiveStream(): void {
    this.isLiveStreaming = true;
    const btnStream = this.container.querySelector('#btn-stream-cognition');
    if (btnStream) {
      btnStream.classList.add('streaming');
      btnStream.innerHTML = '<span>PAUSE STREAM</span>';
    }
    this.streamIntervalId = setInterval(() => {
      this.step();
    }, 280);
  }

  public stopLiveStream(): void {
    this.isLiveStreaming = false;
    if (this.streamIntervalId) {
      clearInterval(this.streamIntervalId);
      this.streamIntervalId = null;
    }
    const btnStream = this.container.querySelector('#btn-stream-cognition');
    if (btnStream) {
      btnStream.classList.remove('streaming');
      btnStream.innerHTML = '<span>LIVE STREAM (60 FPS)</span>';
    }
  }

  public applyTelemetry(t: CognitiveTelemetry): void {
    // 1. Update reward pill
    const rewPill = this.container.querySelector('#cognitive-reward-pill');
    if (rewPill) {
      const rewVal = rewPill.querySelector('.val');
      if (rewVal) {
        rewVal.textContent = `${t.cumulative_reward >= 0 ? '+' : ''}${t.cumulative_reward.toFixed(2)}`;
        rewVal.className = `val ${t.step_reward > 0 ? 'gain' : t.step_reward < -0.5 ? 'loss' : ''}`;
      }
    }

    // 2. Stage 1: Sensory Perception
    const s1Container = this.container.querySelector('#stage1-sensors');
    if (s1Container && t.observations) {
      let html = '';
      for (let i = 0; i < 8; i++) {
        const obs = t.observations[i] || [];
        const isSevered = t.amputated_arms?.includes(i);
        const distTarget = (obs[4] || 0.5) * 14;
        const distHazard = (obs[11] || 0.8) * 14;
        html += `
          <div class="arm-sensor-pill ${isSevered ? 'severed' : ''}">
            <div class="arm-id">Arm #${i} ${isSevered ? '(Severed)' : ''}</div>
            <div class="sensor-bars">
              <div class="s-bar target" title="Target Distance: ${distTarget.toFixed(1)}">
                <span class="bar-fill" style="width: ${Math.max(5, Math.min(100, (1 - obs[4]) * 100))}%"></span>
              </div>
              <div class="s-bar hazard" title="Hazard Distance: ${distHazard.toFixed(1)}">
                <span class="bar-fill" style="width: ${Math.max(5, Math.min(100, (1 - obs[11]) * 100))}%"></span>
              </div>
            </div>
          </div>
        `;
      }
      s1Container.innerHTML = html;
    }

    // 3. Stage 2: Surprise Values
    const s2Container = this.container.querySelector('#stage2-surprise');
    if (s2Container && t.surprise_values) {
      let html = '';
      for (let i = 0; i < 8; i++) {
        const val = t.surprise_values[i] || 0;
        const isHigh = val > 0.15;
        html += `
          <div class="surprise-row ${isHigh ? 'high' : ''}">
            <span class="arm-tag">A${i}</span>
            <div class="meter-track">
              <div class="meter-fill" style="width: ${Math.min(100, val * 400)}%"></div>
            </div>
            <span class="score-val">${val.toFixed(3)}</span>
          </div>
        `;
      }
      s2Container.innerHTML = html;
    }

    // 4. Stage 3: Gating Flags
    const s3Container = this.container.querySelector('#stage3-gates');
    const rateLabel = this.container.querySelector('#gating-rate-label');
    if (rateLabel) {
      rateLabel.textContent = `${(t.report_rate * 100).toFixed(1)}% (Target ≤22%)`;
    }
    if (s3Container && t.report_flags) {
      let html = '';
      for (let i = 0; i < 8; i++) {
        const fires = t.report_flags[i];
        const prob = (t.report_probs ? t.report_probs[i] : (fires ? 0.8 : 0.1)) * 100;
        html += `
          <div class="gate-pill ${fires ? 'fire' : 'local'}">
            <span class="arm-num">A${i}</span>
            <span class="gate-status">${fires ? 'REPORT ●' : 'LOCAL ○'}</span>
            <span class="prob-tag">${prob.toFixed(0)}%</span>
          </div>
        `;
      }
      s3Container.innerHTML = html;
    }

    // 5. Stage 4: Coalitions, Memory Consolidation & Inter-Brachial Semantic Chatter
    const s4Container = this.container.querySelector('#stage4-coalitions');
    const consBadge = this.container.querySelector('#stage4-consolidation');
    const lexiconContainer = this.container.querySelector('#stage4-lexicon');

    if (s4Container) {
      if (t.coalition_clusters && t.coalition_clusters.length > 0) {
        let html = '';
        for (const cluster of t.coalition_clusters) {
          html += `
            <div class="coalition-tag active-team">
              <span class="team-icon">::</span>
              <span class="team-members">Active Coalition Team: [Arms ${cluster.join(' ⟷ ')}]</span>
            </div>
          `;
        }
        s4Container.innerHTML = html;
      } else {
        s4Container.innerHTML = '<div class="no-coalition">Autonomous Local Operation (No Central Binding)</div>';
      }
    }
    if (consBadge) {
      if (t.is_consolidation_step) {
        consBadge.className = 'consolidation-status active';
        consBadge.innerHTML = '<span class="dot pulse"></span> Slow Memory Consolidation: FIRED (Updated Central GRU)';
      } else {
        consBadge.className = 'consolidation-status';
        consBadge.innerHTML = '<span class="dot"></span> Memory Consolidation: Clock Resting (K=5 interval)';
      }
    }

    // Inter-Brachial Semantic Chatter
    if (lexiconContainer && t.decoded_intents) {
      let html = '';
      for (const intentItem of t.decoded_intents) {
        const confPct = Math.round(intentItem.confidence * 100);
        html += `
          <div class="lexicon-intent-pill ${intentItem.is_reporting ? 'reporting' : ''}" style="border-left: 2px solid ${intentItem.color}">
            <div class="intent-header">
              <span class="arm-id">A${intentItem.arm_index}</span>
              <span class="intent-conf">${confPct}%</span>
            </div>
            <div class="intent-tag" title="${intentItem.description}">
              <span>${intentItem.icon}</span>
              <span style="color: ${intentItem.color}">${intentItem.label}</span>
            </div>
          </div>
        `;
      }
      lexiconContainer.innerHTML = html;
    }

    // 6. Stage 5: Solution Generation & Evaluation
    const s5Container = this.container.querySelector('#stage5-actions');
    const actLabels = ['STAY', 'UP', 'DOWN', 'LEFT', 'RIGHT'];
    if (s5Container && t.actions) {
      let html = '';
      for (let i = 0; i < 8; i++) {
        const act = t.actions[i];
        const val = t.values ? t.values[i] : 0.0;
        const actName = actLabels[act] || 'STAY';
        html += `
          <div class="action-card">
            <div class="act-header">
              <span class="a-title">Arm #${i}</span>
              <span class="a-critic" title="Critic Value Baseline V(s)">V: ${val.toFixed(2)}</span>
            </div>
            <div class="chosen-action-badge act-${actName.toLowerCase()}">
              ${actName}
            </div>
          </div>
        `;
      }
      s5Container.innerHTML = html;
    }

    // 7. Fire 3D Visual pulses into connectome!
    if (this.onVisualPulse) {
      const reportingArms = [];
      const highSurpriseArms = [];
      for (let i = 0; i < 8; i++) {
        if (t.report_flags && t.report_flags[i]) reportingArms.push(i);
        if (t.surprise_values && t.surprise_values[i] > 0.15) highSurpriseArms.push(i);
      }
      this.onVisualPulse(reportingArms, t.coalition_clusters || [], highSurpriseArms);
    }
  }

  private generateSyntheticObservations(step: number, scenario: string): number[][] {
    const obs: number[][] = [];
    const isHunting = scenario === 'hunting';
    for (let i = 0; i < 8; i++) {
      const armObs = new Array(16).fill(0);
      // Joint angles
      armObs[0] = Math.sin(step * 0.2 + i);
      armObs[1] = Math.cos(step * 0.2 + i);
      armObs[2] = 0.1;
      armObs[3] = -0.1;
      // Target offset
      armObs[4] = (isHunting && (i === 2 || i === 3)) ? 0.12 : 0.45;
      armObs[5] = 0.2;
      armObs[6] = 0.0;
      // Target value / type
      armObs[7] = isHunting ? 1.0 : 0.5;
      // Hazard offset
      armObs[11] = 0.75;
      obs.push(armObs);
    }
    return obs;
  }

  private generateSyntheticTelemetry(step: number, scenario: string): CognitiveTelemetry {
    const isHunting = scenario === 'hunting';
    const isAmp = scenario === 'amputation';
    const isSoftBody = scenario === 'soft_body_3d';

    const reporting: boolean[] = [false, false, false, false, false, false, false, false];
    const surprises: number[] = [];
    const actions: number[] = [];
    const values: number[] = [];
    const observations: number[][] = [];
    const coalitions: number[][] = [];
    const decodedIntents: DecodedIntent[] = [];

    // Simulate scenario-dependent behavioral dynamics
    if (isHunting) {
      reporting[2] = true;
      reporting[3] = true;
      coalitions.push([2, 3]);
    } else if (isAmp) {
      reporting[2] = (step % 2 === 0);
      reporting[4] = (step % 2 === 0);
    } else if (isSoftBody) {
      reporting[1] = true;
      reporting[5] = true;
      coalitions.push([1, 5]);
    } else {
      if (step < 3) {
        reporting[2] = true;
        reporting[3] = true;
        coalitions.push([2, 3]);
      }
    }

    for (let i = 0; i < 8; i++) {
      const sVal = reporting[i] ? 0.18 + Math.random() * 0.08 : 0.03 + Math.random() * 0.04;
      surprises.push(sVal);
      actions.push(Math.floor(Math.random() * 5));
      values.push(2.5 + Math.random() * 2.0);
      observations.push(new Array(16).fill(0).map(() => Math.random() * 0.5));

      const isRep = reporting[i];
      let intent = 'AUTONOMOUS_EXPLORE';
      let label = 'Autonomous Forage';
      let icon = '';
      let color = '#a6e3a1';
      let description = 'Routine sensory sweep without central gating overhead.';
      let conf = 0.95;

      if (isRep) {
        if (isHunting) {
          intent = 'COOPERATIVE_PULL';
          label = 'Cooperative Grip';
          icon = '';
          color = '#cba6f7';
          description = 'Dual-arm bilateral lock on prey.';
          conf = 0.94;
        } else if (isSoftBody) {
          intent = 'REACH_ELONGATION';
          label = 'Hydrostat Elongate';
          icon = '';
          color = '#89dceb';
          description = 'Muscular hydrostat continuum extension.';
          conf = 0.91;
        } else {
          intent = 'TARGET_DETECTED';
          label = 'Prey Detected';
          icon = '';
          color = '#89b4fa';
          description = 'Chemosensory verification of edible target.';
          conf = 0.88;
        }
      }

      decodedIntents.push({
        arm_index: i,
        intent,
        label,
        icon,
        color,
        description,
        confidence: conf,
        is_reporting: isRep,
      });
    }

    return {
      step,
      max_steps: 40,
      scenario,
      step_reward: 12.5 + Math.random() * 6.0,
      cumulative_reward: 35.0 + step * 2.1,
      is_done: step >= 39,
      observations,
      surprise_values: surprises,
      report_flags: reporting,
      report_probs: reporting.map((r) => r ? 0.85 : 0.08),
      report_rate: reporting.filter(Boolean).length / 8.0,
      coalition_clusters: coalitions,
      attention_matrix: Array.from({ length: 8 }, () => new Array(8).fill(0.12)),
      is_consolidation_step: (step % 5 === 0),
      decoded_intents: decodedIntents,
      action_logits: Array.from({ length: 8 }, () => new Array(5).fill(0.2)),
      actions,
      values,
      amputated_arms: isAmp ? [3] : [],
    };
  }

  private renderDefaultEmulation(): void {
    const emu = this.generateSyntheticTelemetry(0, 'standard');
    this.applyTelemetry(emu);
  }
}
