import { ICONS } from './icons';

export class SignalTriggerPanel {
  private container: HTMLElement;
  public onTriggerPathway?: (pathwayId: string) => void;
  public onCustomStimulusMode?: () => void;
  public onToggleFollowSignal?: (enabled: boolean) => void;

  private activePathwayId: string | null = null;
  private isFollowSignalActive: boolean = false;
  private currentStepInfo: { label: string; description: string } | null = null;

  constructor(containerId: string = 'signal-trigger-panel') {
    this.container = document.getElementById(containerId) || document.body;
    this.render();
  }

  public setStepProgress(stepLabel: string, description: string) {
    this.currentStepInfo = { label: stepLabel, description };
    this.render();
  }

  public clearProgress() {
    this.activePathwayId = null;
    this.currentStepInfo = null;
    this.render();
  }

  public setFollowSignal(active: boolean) {
    this.isFollowSignalActive = active;
    this.render();
  }

  private render() {
    const progressCard = this.currentStepInfo
      ? `
      <div class="signal-progress-card">
        <div class="progress-indicator">
          <span class="pulse-dot"></span>
          <strong>PROPAGATING ACTION POTENTIAL:</strong> ${this.currentStepInfo.label}
        </div>
        <div class="progress-desc">${this.currentStepInfo.description}</div>
      </div>
    `
      : '';

    this.container.innerHTML = `
      <div class="signal-panel-header">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="window-drag-icon">${ICONS.dragGrip(14, 'rgba(255,255,255,0.6)')}</span>
          ${ICONS.actionPotential(15, '#fab387')}
          <div>
            <span class="signal-title">NEURAL SIGNAL PROPAGATION & ACTION POTENTIAL TRACING</span>
            <span class="signal-subtitle">Trigger dynamic neural action potentials along real 3D anatomical pathways</span>
          </div>
        </div>

        <div style="display: flex; align-items: center; gap: 8px;">
          <button id="btn-toggle-follow-cam" class="btn-follow-signal ${this.isFollowSignalActive ? 'active' : ''}">
            ${this.isFollowSignalActive ? 'FOLLOWING SIGNAL (ACTIVE)' : 'FOLLOW SIGNAL CAMERA'}
          </button>
          <button class="btn-window-minimize" title="Minimize / Expand Dock">
            ${ICONS.minimize(11, 'rgba(255,255,255,0.8)')}
          </button>
        </div>
      </div>

      <div class="window-body-scroll">
        <div class="signal-buttons-grid">
        <button class="btn-stimulus stimulus-sucker ${this.activePathwayId === 'touch_sucker' ? 'active' : ''}" data-id="touch_sucker">
          <span class="stim-icon">${ICONS.suckerReceptor(18, '#f43f5e')}</span>
          <div class="stim-text">
            <span class="stim-name">TOUCH SUCKER</span>
            <span class="stim-sub">Sucker Receptor → Axial Cord → Motor Arc</span>
          </div>
        </button>

        <button class="btn-stimulus stimulus-optic ${this.activePathwayId === 'visual_stimulus' ? 'active' : ''}" data-id="visual_stimulus">
          <span class="stim-icon">${ICONS.opticLobe(18, '#a855f7')}</span>
          <div class="stim-text">
            <span class="stim-name">VISUAL STIMULATION</span>
            <span class="stim-sub">Eye → Optic Lobe → Vertical Memory → Strike</span>
          </div>
        </button>

        <button class="btn-stimulus stimulus-arm ${this.activePathwayId === 'arm_stimulation' ? 'active' : ''}" data-id="arm_stimulation">
          <span class="stim-icon">${ICONS.brachialRing(18, '#38bdf8')}</span>
          <div class="stim-text">
            <span class="stim-name">ARM TACTILE REFLEX</span>
            <span class="stim-sub">Axial Arc → Interbrachial Ring Handover</span>
          </div>
        </button>

        <button class="btn-stimulus stimulus-escape ${this.activePathwayId === 'escape_jet' ? 'active' : ''}" data-id="escape_jet">
          <span class="stim-icon">${ICONS.escapeJet(18, '#f97316')}</span>
          <div class="stim-text">
            <span class="stim-name">ESCAPE JET REFLEX</span>
            <span class="stim-sub">Statocyst → Stellar Ganglia → Jet Pulse</span>
          </div>
        </button>

        <button class="btn-stimulus stimulus-custom" id="btn-custom-stim">
          <span class="stim-icon">${ICONS.customProbe(18, '#10b981')}</span>
          <div class="stim-text">
            <span class="stim-name">CUSTOM PROBE</span>
            <span class="stim-sub">Click any 3D node</span>
          </div>
        </button>
      </div>

      ${progressCard}
      </div>
    `;

    this.bindEvents();
  }

  private bindEvents() {
    this.container.querySelectorAll('.btn-stimulus[data-id]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const id = target.getAttribute('data-id');
        if (id && this.onTriggerPathway) {
          this.activePathwayId = id;
          this.onTriggerPathway(id);
          this.render();
        }
      });
    });

    const btnCustom = this.container.querySelector('#btn-custom-stim');
    if (btnCustom) {
      btnCustom.addEventListener('click', () => {
        if (this.onCustomStimulusMode) {
          this.onCustomStimulusMode();
        }
      });
    }

    const btnFollow = this.container.querySelector('#btn-toggle-follow-cam');
    if (btnFollow) {
      btnFollow.addEventListener('click', () => {
        this.isFollowSignalActive = !this.isFollowSignalActive;
        if (this.onToggleFollowSignal) {
          this.onToggleFollowSignal(this.isFollowSignalActive);
        }
        this.render();
      });
    }
  }
}

