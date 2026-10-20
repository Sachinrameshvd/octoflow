import { ICONS } from './icons';

export type AppMode =
  | 'EXPLORE'
  | 'NEURAL_ACTIVITY'
  | 'TRACE_SIGNAL'
  | 'ARM_MODE'
  | 'BRAIN_MODE'
  | 'NETWORK_MODE'
  | 'COMPARE_ANATOMY';

export type NavigationMode = 'ORBIT' | 'FREE_FLY' | 'FOLLOW_SIGNAL';

export interface ControlState {
  mode: AppMode;
  navMode: NavigationMode;
  neuronDensity: number;
  fiberGlow: number;
  neuropilOpacity: number;
  punctaAlpha: number;
  punctaVisible: boolean;
  anatomyOpacity: number;
  signalSpeed: number;
  activityIntensity: number;
  fibersVisible: boolean;
  isPaused: boolean;
  selectedArmIndex: number;
}

export class ControlPanel {
  private container: HTMLElement;
  private state: ControlState;

  public onStateChange?: (state: ControlState) => void;
  public onResetCamera?: () => void;
  public onSelectPresetView?: (viewKey: string) => void;
  public onSelectPerspectiveAngle?: (angleKey: string) => void;
  public onStartTour?: () => void;

  constructor(containerId: string = 'control-panel') {
    this.container = document.getElementById(containerId) || document.body;
    this.state = {
      mode: 'EXPLORE',
      navMode: 'ORBIT',
      neuronDensity: 1.0,
      fiberGlow: 0.85,
      neuropilOpacity: 0.28,
      punctaAlpha: 0.85,
      punctaVisible: true,
      anatomyOpacity: 0.08,
      signalSpeed: 1.0,
      activityIntensity: 1.0,
      fibersVisible: true,
      isPaused: false,
      selectedArmIndex: 0,
    };
    this.render();
  }

  public setMode(mode: AppMode) {
    this.state.mode = mode;
    this.render();
  }

  public setNavMode(navMode: NavigationMode) {
    this.state.navMode = navMode;
    this.render();
  }

  public getState(): ControlState {
    return { ...this.state };
  }

  private render() {
    const modes: { key: AppMode; label: string; icon: string }[] = [
      { key: 'EXPLORE', label: 'EXPLORE', icon: ICONS.exploreCompass(14, '#89dceb') },
      { key: 'NEURAL_ACTIVITY', label: 'ACTIVITY', icon: ICONS.activityWave(14, '#94e2d5') },
      { key: 'TRACE_SIGNAL', label: 'TRACE SIGNAL', icon: ICONS.actionPotential(14, '#fab387') },
      { key: 'ARM_MODE', label: 'ARM MODE', icon: ICONS.brachialRing(14, '#74c7ec') },
      { key: 'BRAIN_MODE', label: 'BRAIN MODE', icon: ICONS.brainCortex(14, '#cba6f7') },
      { key: 'NETWORK_MODE', label: 'CONNECTOME ONLY', icon: ICONS.connectomeLattice(14, '#89dceb') },
      { key: 'COMPARE_ANATOMY', label: 'ANATOMY + NETWORK', icon: ICONS.anatomyLayer(14, '#f38ba8') },
    ];

    const navModes: { key: NavigationMode; label: string; icon: string; desc: string }[] = [
      { key: 'ORBIT', label: '360° ORBIT', icon: ICONS.spatialOrbit(16, '#89dceb'), desc: 'Drag to rotate, scroll to zoom' },
      { key: 'FREE_FLY', label: 'INSIDE NETWORK', icon: ICONS.freeFlight(16, '#b4befe'), desc: 'WASD flight inside nerves' },
      { key: 'FOLLOW_SIGNAL', label: 'FOLLOW SIGNAL', icon: ICONS.actionPotential(16, '#fab387'), desc: 'Auto-track active action potentials' },
    ];

    this.container.innerHTML = `
      <!-- Window Titlebar with Drag Gripper & Minimize Controls -->
      <div class="window-titlebar">
        <div class="window-titlebar-left">
          <span class="window-drag-icon">${ICONS.dragGrip(14, 'rgba(255,255,255,0.6)')}</span>
          <span class="window-title-text">SYSTEM CONTROLS</span>
        </div>
        <div class="window-titlebar-right">
          <button class="btn-window-minimize" title="Minimize / Expand Window">
            ${ICONS.minimize(11, 'rgba(255,255,255,0.8)')}
          </button>
        </div>
      </div>

      <div class="window-body-scroll">
        <!-- Guided Tour Launcher -->
        <div class="control-section">
          <button id="btn-panel-start-tour">
            ${ICONS.tourPlay(16, '#ffffff')}
            <span>HOW THE BRAIN WORKS (TOUR)</span>
          </button>
        </div>

      <!-- 3D Navigation Mode Selector -->
      <div class="control-section">
        <div class="section-title">3D CAMERA / NAVIGATION</div>
        <div class="nav-modes-grid">
          ${navModes
            .map(
              (n) => `
            <button class="btn-nav-mode ${this.state.navMode === n.key ? 'active' : ''}" data-nav="${n.key}">
              <div class="nav-mode-header">
                <span class="mode-icon">${n.icon}</span> <strong>${n.label}</strong>
              </div>
              <div class="nav-mode-sub">${n.desc}</div>
            </button>
          `
            )
            .join('')}
        </div>
      </div>

      <!-- Interaction Modes -->
      <div class="control-section">
        <div class="section-title">INTERACTION MODES</div>
        <div class="modes-grid">
          ${modes
            .map(
              (m) => `
            <button class="btn-mode ${this.state.mode === m.key ? 'active' : ''}" data-mode="${m.key}">
              <span class="mode-icon">${m.icon}</span> ${m.label}
            </button>
          `
            )
            .join('')}
        </div>
      </div>

      ${
        this.state.mode === 'ARM_MODE'
          ? `
        <div class="control-section arm-selector-section">
          <div class="section-title">SELECT ARM (1 - 8)</div>
          <div class="arm-buttons-grid">
            ${Array.from({ length: 8 }, (_, i) => `
              <button class="btn-arm-select ${this.state.selectedArmIndex === i ? 'active' : ''}" data-arm="${i}">
                Arm ${i + 1}
              </button>
            `).join('')}
          </div>
        </div>
      `
          : ''
      }

      <!-- Perspective Angle Presets -->
      <div class="control-section">
        <div class="section-title">PERSPECTIVE ANGLES</div>
        <div class="angles-grid">
          <button class="btn-angle" data-angle="FRONT">Front</button>
          <button class="btn-angle" data-angle="BACK">Back</button>
          <button class="btn-angle" data-angle="LEFT">Left</button>
          <button class="btn-angle" data-angle="RIGHT">Right</button>
          <button class="btn-angle" data-angle="TOP">Top</button>
          <button class="btn-angle" data-angle="BOTTOM">Bottom</button>
          <button class="btn-angle" data-angle="INSIDE" style="grid-column: span 3; color: #fab387;">
            Inside Brain Cavity
          </button>
        </div>
      </div>

      <!-- FlyWire & Optical Parameters -->
      <div class="control-section">
        <div class="section-title">CONNECTOME VISUAL LAYERS</div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Neuropil Compartment Hulls</span>
            <span class="slider-val" id="val-neuropil-opacity">${Math.round(this.state.neuropilOpacity * 100)}%</span>
          </div>
          <input type="range" id="slider-neuropil-opacity" min="0" max="0.75" step="0.02" value="${this.state.neuropilOpacity}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Synaptic Puncta (EM Boutons)</span>
            <span class="slider-val" id="val-puncta-alpha">${Math.round(this.state.punctaAlpha * 100)}%</span>
          </div>
          <input type="range" id="slider-puncta-alpha" min="0" max="1.5" step="0.05" value="${this.state.punctaAlpha}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Synaptic Fiber Glow</span>
            <span class="slider-val" id="val-fiber-glow">${Math.round(this.state.fiberGlow * 100)}%</span>
          </div>
          <input type="range" id="slider-fiber-glow" min="0" max="1.5" step="0.05" value="${this.state.fiberGlow}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Anatomical Silhouette</span>
            <span class="slider-val" id="val-anatomy-opacity">${Math.round(this.state.anatomyOpacity * 100)}%</span>
          </div>
          <input type="range" id="slider-anatomy-opacity" min="0" max="0.45" step="0.02" value="${this.state.anatomyOpacity}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Signal Propagation Speed</span>
            <span class="slider-val" id="val-signal-speed">${this.state.signalSpeed.toFixed(1)}x</span>
          </div>
          <input type="range" id="slider-signal-speed" min="0.3" max="3.0" step="0.1" value="${this.state.signalSpeed}">
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <span>Spontaneous Activity Waves</span>
            <span class="slider-val" id="val-activity">${Math.round(this.state.activityIntensity * 100)}%</span>
          </div>
          <input type="range" id="slider-activity" min="0" max="2.0" step="0.1" value="${this.state.activityIntensity}">
        </div>
      </div>


      <!-- Hierarchical Region Presets -->
      <div class="control-section">
        <div class="section-title">HIERARCHY PRESETS</div>
        <div class="presets-grid">
          <button class="btn-preset" data-preset="whole">Whole Octopus</button>
          <button class="btn-preset" data-preset="brain">Central Brain</button>
          <button class="btn-preset" data-preset="vertical">Vertical Lobe</button>
          <button class="btn-preset" data-preset="optic_left">Optic Lobe (L)</button>
          <button class="btn-preset" data-preset="optic_right">Optic Lobe (R)</button>
          <button class="btn-preset" data-preset="arm1">Arm 1 (Dorsal)</button>
        </div>
      </div>

      <div class="control-actions">
        <button id="btn-toggle-pause" class="btn-ctrl">
          ${this.state.isPaused ? ICONS.play(12, '#38bdf8') : ICONS.pause(12, '#38bdf8')}
          <span>${this.state.isPaused ? 'Resume Activity' : 'Pause Activity'}</span>
        </button>
        <button id="btn-reset-cam" class="btn-ctrl">
          ${ICONS.exploreCompass(13, '#38bdf8')}
          <span>Reset Camera</span>
        </button>
      </div>
      </div>
    `;

    this.bindEvents();
  }

  private bindEvents() {
    // Navigation mode buttons
    this.container.querySelectorAll('.btn-nav-mode').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const nav = target.getAttribute('data-nav') as NavigationMode;
        if (nav) {
          this.state.navMode = nav;
          this.notifyChange();
          this.render();
        }
      });
    });

    // Mode buttons
    this.container.querySelectorAll('.btn-mode').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const mode = target.getAttribute('data-mode') as AppMode;
        if (mode) {
          this.state.mode = mode;
          if (mode === 'NETWORK_MODE') {
            this.state.anatomyOpacity = 0.0;
          } else if (mode === 'COMPARE_ANATOMY') {
            this.state.anatomyOpacity = 0.18;
          }
          this.notifyChange();
          this.render();
        }
      });
    });

    // Perspective angle buttons
    this.container.querySelectorAll('.btn-angle').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const angle = target.getAttribute('data-angle');
        if (angle && this.onSelectPerspectiveAngle) {
          this.onSelectPerspectiveAngle(angle);
        }
      });
    });

    // Arm selector buttons
    this.container.querySelectorAll('.btn-arm-select').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const armIdx = parseInt(target.getAttribute('data-arm') || '0', 10);
        this.state.selectedArmIndex = armIdx;
        this.notifyChange();
        this.render();
      });
    });

    // Sliders
    const bindSlider = (
      sliderId: string,
      valId: string,
      fmt: (v: number) => string,
      setter: (v: number) => void
    ) => {
      const slider = this.container.querySelector<HTMLInputElement>(`#${sliderId}`);
      const valLabel = this.container.querySelector<HTMLElement>(`#${valId}`);
      if (slider && valLabel) {
        slider.addEventListener('input', () => {
          const val = parseFloat(slider.value);
          valLabel.textContent = fmt(val);
          setter(val);
          this.notifyChange();
        });
      }
    };

    bindSlider('slider-neuropil-opacity', 'val-neuropil-opacity', (v) => `${Math.round(v * 100)}%`, (v) => (this.state.neuropilOpacity = v));
    bindSlider('slider-puncta-alpha', 'val-puncta-alpha', (v) => `${Math.round(v * 100)}%`, (v) => (this.state.punctaAlpha = v));
    bindSlider('slider-fiber-glow', 'val-fiber-glow', (v) => `${Math.round(v * 100)}%`, (v) => (this.state.fiberGlow = v));
    bindSlider('slider-anatomy-opacity', 'val-anatomy-opacity', (v) => `${Math.round(v * 100)}%`, (v) => (this.state.anatomyOpacity = v));
    bindSlider('slider-signal-speed', 'val-signal-speed', (v) => `${v.toFixed(1)}x`, (v) => (this.state.signalSpeed = v));
    bindSlider('slider-activity', 'val-activity', (v) => `${Math.round(v * 100)}%`, (v) => (this.state.activityIntensity = v));

    // Preset camera views
    this.container.querySelectorAll('.btn-preset').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const key = target.getAttribute('data-preset');
        if (key && this.onSelectPresetView) {
          this.onSelectPresetView(key);
        }
      });
    });

    // Action buttons
    const btnTour = this.container.querySelector('#btn-panel-start-tour');
    if (btnTour && this.onStartTour) {
      btnTour.addEventListener('click', () => this.onStartTour!());
    }

    const btnPause = this.container.querySelector('#btn-toggle-pause');
    if (btnPause) {
      btnPause.addEventListener('click', () => {
        this.state.isPaused = !this.state.isPaused;
        this.notifyChange();
        this.render();
      });
    }

    const btnReset = this.container.querySelector('#btn-reset-cam');
    if (btnReset && this.onResetCamera) {
      btnReset.addEventListener('click', () => this.onResetCamera!());
    }
  }

  private notifyChange() {
    if (this.onStateChange) {
      this.onStateChange(this.getState());
    }
  }
}

