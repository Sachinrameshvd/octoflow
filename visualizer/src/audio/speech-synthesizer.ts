/** Neural Voice Transmission & Speech Synthesizer for Cephalopod Swarm.
 * Implements native Web Speech Synthesis with distinct acoustic profiles (pitch, rate, voice timbre)
 * and animated visual telemetry subtitles for each of the 8 octopuses across
 * Software Engineering, AI/ML Research, and Dual-Domain Adaptive modes.
 * 100% Roboto Mono, zero external dependencies, zero emojis.
 */

import { ICONS } from '../ui/icons';

export type SwarmDomainMode = 'DUAL' | 'SOFTWARE' | 'AIML';

export interface OctopusSpeechProfile {
  id: number;
  title: string;
  department: string;
  colorHex: string;
  pitch: number;
  rate: number;
  preferredVoices: string[];
  gender: 'male' | 'female' | 'neutral';

  // Software Dev Domain
  softwareTitle: string;
  softwareRole: string;
  softwareScript: string;

  // AI / ML Research Domain
  aimlTitle: string;
  aimlRole: string;
  aimlScript: string;

  // Dual Domain (Both)
  dualRole: string;
  dualScript: string;
}

export const OCTOPUS_SPEECH_PROFILES: OctopusSpeechProfile[] = [
  {
    id: 0,
    title: 'System Architect',
    department: 'Architecture & Data',
    colorHex: '#00F0FF',
    pitch: 0.84,
    rate: 1.02,
    preferredVoices: ['Daniel', 'Alex', 'Fred', 'Arthur', 'Oliver', 'Google US English'],
    gender: 'male',
    softwareTitle: 'System Architect',
    softwareRole: 'System specifications, directory topology & module contracts',
    softwareScript: 'Octo Zero, Chief Architect. I orchestrate global mission directives and route consensus across the consortium.',
    aimlTitle: 'Data Engineer',
    aimlRole: 'Dataset ETL, PyTorch DataLoaders & data splits',
    aimlScript: 'Octo Zero, Data Engineer. I pipeline dataset ingestion, feature scaling, and PyTorch DataLoaders.',
    dualRole: 'SW: Architecture & specs // AI: Dataset ETL & PyTorch loaders',
    dualScript: 'Octo Zero. In software, I architect system topology; in AI and ML, I pipeline datasets and PyTorch loaders.',
  },
  {
    id: 1,
    title: 'Database & Storage',
    department: 'Persistence & Models',
    colorHex: '#A855F7',
    pitch: 0.94,
    rate: 0.96,
    preferredVoices: ['Samantha', 'Karen', 'Victoria', 'Moira', 'Google UK English Female'],
    gender: 'female',
    softwareTitle: 'Database & Schemas',
    softwareRole: 'SQL/ORM models, database connectors & vector persistence',
    softwareScript: 'Octo One, Synaptic Memory. I manage persistent knowledge graphs, vector recall, and episodic indexing.',
    aimlTitle: 'Model Architect',
    aimlRole: 'Deep neural network topologies, attention layers & weights',
    aimlScript: 'Octo One, Model Architect. I design deep neural network topologies, attention layers, and forward passes.',
    dualRole: 'SW: Vector persistence // AI: Deep neural layers & weights',
    dualScript: 'Octo One. In software, I manage database persistence; in AI and ML, I design neural layers and forward passes.',
  },
  {
    id: 2,
    title: 'Backend & Services',
    department: 'Core Engine & Compute',
    colorHex: '#3B82F6',
    pitch: 0.96,
    rate: 1.06,
    preferredVoices: ['Rishi', 'Daniel', 'Tom', 'George', 'Google UK English Male'],
    gender: 'male',
    softwareTitle: 'Backend API',
    softwareRole: 'REST/WebSocket endpoints & distributed business logic',
    softwareScript: 'Octo Two, Backend Engine. I execute high-throughput asynchronous pipelines and distributed neural compute.',
    aimlTitle: 'Training & Loss Engineer',
    aimlRole: 'GPU training loops, custom loss functions & AMP acceleration',
    aimlScript: 'Octo Two, Training Engineer. I execute GPU training loops, custom loss functions, and gradient optimization.',
    dualRole: 'SW: REST API services // AI: GPU training & hardware compute',
    dualScript: 'Octo Two. In software, I build backend REST endpoints; in AI and ML, I drive GPU training loops and compute.',
  },
  {
    id: 3,
    title: 'Frontend & UI',
    department: 'Sensory & Evaluation',
    colorHex: '#EC4899',
    pitch: 1.18,
    rate: 1.06,
    preferredVoices: ['Tessa', 'Samantha', 'Victoria', 'Fiona', 'Google US English'],
    gender: 'female',
    softwareTitle: 'Frontend UI',
    softwareRole: 'User interface views, React/Vite layout & 3D telepresence',
    softwareScript: 'Octo Three, Sensory Telemetry. I stream real-time spatial connectome visualization and telepresence.',
    aimlTitle: 'Eval & Benchmarks',
    aimlRole: 'Validation metrics, ROC curves, confusion matrices & loss evaluation',
    aimlScript: 'Octo Three, Evaluation and Benchmarks. I calculate validation metrics, ROC curves, and test loss convergence.',
    dualRole: 'SW: 3D UI & telepresence // AI: Accuracy metrics & loss eval',
    dualScript: 'Octo Three. In software, I render 3D frontend visualizers; in AI and ML, I benchmark accuracy and model loss.',
  },
  {
    id: 4,
    title: 'AI & Cognitive Logic',
    department: 'Reasoning & Tuning',
    colorHex: '#10B981',
    pitch: 1.02,
    rate: 1.00,
    preferredVoices: ['Alex', 'Daniel', 'Oliver', 'Google US English'],
    gender: 'neutral',
    softwareTitle: 'State & Client Sync',
    softwareRole: 'Reactive state management, custom hooks & store synchronization',
    softwareScript: 'Octo Four, Cognitive Core. I resolve multi-arm task coalitions and calculate active predictive surprise.',
    aimlTitle: 'HPO / Tuner',
    aimlRole: 'Hyperparameter search spaces & Bayesian surprise tuning',
    aimlScript: 'Octo Four, Hyperparameter Tuner. I optimize hyperparameter search spaces, learning rates, and regularization schedules.',
    dualRole: 'SW: Reactive state & hooks // AI: Hyperparameter tuning & search',
    dualScript: 'Octo Four. In software, I manage reactive state; in AI and ML, I tune hyperparameters and predictive surprise.',
  },
  {
    id: 5,
    title: 'Sentinel & Security',
    department: 'Guardianship & Quantization',
    colorHex: '#EF4444',
    pitch: 0.76,
    rate: 0.98,
    preferredVoices: ['Fred', 'Daniel', 'Arthur', 'Google UK English Male'],
    gender: 'male',
    softwareTitle: 'Security & Audit',
    softwareRole: 'Security guardrails, vulnerability audits & input sanitization',
    softwareScript: 'Octo Five, System Sentinel. I enforce safety boundaries, execution guardrails, and anomaly isolation.',
    aimlTitle: 'Quantization & ONNX',
    aimlRole: 'INT8/FP16 quantization & ONNX Runtime hardware graph export',
    aimlScript: 'Octo Five, Quantization and ONNX. I apply INT8 quantization and export model computation graphs to ONNX runtime.',
    dualRole: 'SW: Security guardrails // AI: INT8 quantization & ONNX export',
    dualScript: 'Octo Five. In software, I enforce security guardrails; in AI and ML, I apply INT8 quantization and ONNX export.',
  },
  {
    id: 6,
    title: 'Chaos & QA Testing',
    department: 'Verification & Serving',
    colorHex: '#F59E0B',
    pitch: 1.24,
    rate: 1.14,
    preferredVoices: ['Moira', 'Karen', 'Tessa', 'Samantha'],
    gender: 'female',
    softwareTitle: 'Chaos & QA Testing',
    softwareRole: 'Unit tests, integration suites & live resilience testing',
    softwareScript: 'Octo Six, Chaos Engine. I inject live edge-case disruptions to stress-test consortium resilience and failover.',
    aimlTitle: 'Inference Serving',
    aimlRole: 'High-throughput FastAPI model endpoints & latency benchmarking',
    aimlScript: 'Octo Six, Inference Serving. I deploy high-throughput FastAPI prediction endpoints and latency benchmarks.',
    dualRole: 'SW: Chaos testing & QA // AI: High-speed inference serving',
    dualScript: 'Octo Six. In software, I stress-test system resilience; in AI and ML, I deploy high-speed model inference.',
  },
  {
    id: 7,
    title: 'Runner & DevOps',
    department: 'Deployment & MLOps',
    colorHex: '#EAB308',
    pitch: 1.12,
    rate: 1.12,
    preferredVoices: ['Rishi', 'Alex', 'Victoria', 'Google US English'],
    gender: 'male',
    softwareTitle: 'DevOps & Deployment',
    softwareRole: 'Docker containerization, CI/CD pipelines & automated workflows',
    softwareScript: 'Octo Seven, Task Runner. I drive sandbox tool execution, code generation, and automated workflows.',
    aimlTitle: 'MLOps & Governance',
    aimlRole: 'Model cards, experiment tracking & reproducibility lockfiles',
    aimlScript: 'Octo Seven, MLOps and Governance. I maintain model cards, experiment versioning, and reproducibility tracking.',
    dualRole: 'SW: Docker & CI/CD // AI: MLOps tracking & model cards',
    dualScript: 'Octo Seven. In software, I automate Docker deployment; in AI and ML, I track experiment reproducibility.',
  },
];

export class CephalopodVoiceSystem {
  private availableVoices: SpeechSynthesisVoice[] = [];
  private isMuted: boolean = false;
  private domainMode: SwarmDomainMode = 'DUAL';
  private bannerContainer: HTMLElement | null = null;
  private hideTimer: number | null = null;
  private typewriterTimer: number | null = null;
  private currentOctoId: number | null = null;
  public onMuteStateChange?: (isMuted: boolean) => void;
  public onDomainModeChange?: (mode: SwarmDomainMode) => void;

  constructor() {
    this.initVoices();
    this.createBannerElement();
  }

  private initVoices() {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      return;
    }

    const loadVoices = () => {
      this.availableVoices = window.speechSynthesis.getVoices();
    };

    loadVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }

  private createBannerElement() {
    let el = document.getElementById('neural-voice-banner');
    if (!el) {
      el = document.createElement('div');
      el.id = 'neural-voice-banner';
      document.body.appendChild(el);
    }
    this.bannerContainer = el;
    this.bannerContainer.style.display = 'none';
  }

  public setDomainMode(mode: SwarmDomainMode) {
    this.domainMode = mode;
    if (this.onDomainModeChange) {
      this.onDomainModeChange(mode);
    }
    // If an octopus is currently open, re-render its banner
    if (this.currentOctoId !== null && this.bannerContainer && this.bannerContainer.style.display !== 'none') {
      const profile = OCTOPUS_SPEECH_PROFILES.find((p) => p.id === this.currentOctoId);
      if (profile) {
        this.showBanner(profile);
      }
    }
  }

  public getDomainMode(): SwarmDomainMode {
    return this.domainMode;
  }

  public toggleMute(): boolean {
    this.isMuted = !this.isMuted;
    if (this.isMuted) {
      this.stopSpeaking();
      this.hideBanner();
    }
    if (this.onMuteStateChange) {
      this.onMuteStateChange(this.isMuted);
    }
    return this.isMuted;
  }

  public getIsMuted(): boolean {
    return this.isMuted;
  }

  public getCurrentOctoId(): number | null {
    return this.currentOctoId;
  }

  private speechQueue: Array<{ profile: OctopusSpeechProfile; textToSpeak: string }> = [];
  private isSpeaking: boolean = false;

  public stopSpeaking() {
    this.speechQueue = [];
    this.isSpeaking = false;
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (this.typewriterTimer !== null) {
      clearInterval(this.typewriterTimer);
      this.typewriterTimer = null;
    }
    if (this.hideTimer !== null) {
      clearTimeout(this.hideTimer);
      this.hideTimer = null;
    }
  }

  private playNeuralChirp() {
    if (this.isMuted) return;
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1400, ctx.currentTime + 0.045);

      gain.gain.setValueAtTime(0.045, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.05);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.055);
    } catch {
      // AudioContext blocked by user interaction policy
    }
  }

  private selectVoiceForOctopus(profile: OctopusSpeechProfile): SpeechSynthesisVoice | null {
    if (this.availableVoices.length === 0) {
      return null;
    }

    for (const name of profile.preferredVoices) {
      const match = this.availableVoices.find(
        (v) => v.name.toLowerCase().includes(name.toLowerCase()) && v.lang.startsWith('en')
      );
      if (match) return match;
    }

    const englishVoices = this.availableVoices.filter((v) => v.lang.startsWith('en'));
    if (englishVoices.length > 0) {
      return englishVoices[profile.id % englishVoices.length];
    }

    return this.availableVoices[profile.id % this.availableVoices.length];
  }

  /**
   * Main Trigger: Speak octopus role using serializing FIFO speech queue to prevent audio collisions.
   */
  public speakOctopusRole(octoId: number) {
    const profile = OCTOPUS_SPEECH_PROFILES.find((p) => p.id === octoId) || OCTOPUS_SPEECH_PROFILES[0];
    const textToSpeak =
      this.domainMode === 'SOFTWARE'
        ? profile.softwareScript
        : this.domainMode === 'AIML'
        ? profile.aimlScript
        : profile.dualScript;

    if (this.isSpeaking) {
      if (!this.speechQueue.some((item) => item.profile.id === octoId)) {
        if (this.speechQueue.length >= 2) {
          this.speechQueue.shift();
        }
        this.speechQueue.push({ profile, textToSpeak });
      }
      return;
    }

    this.executeSpeech(profile, textToSpeak);
  }

  /**
   * Speak arbitrary custom text (e.g. manual playbooks or documentation) with voice narration.
   */
  public speakCustom(title: string, textToSpeak: string, colorHex: string = '#f59e0b') {
    const customProfile: OctopusSpeechProfile = {
      ...OCTOPUS_SPEECH_PROFILES[0],
      title: title,
      colorHex: colorHex,
      softwareScript: textToSpeak,
      aimlScript: textToSpeak,
      dualScript: textToSpeak,
    };
    if (this.isSpeaking) {
      this.speechQueue.push({ profile: customProfile, textToSpeak });
      return;
    }
    this.executeSpeech(customProfile, textToSpeak);
  }

  private executeSpeech(profile: OctopusSpeechProfile, textToSpeak: string) {
    this.currentOctoId = profile.id;
    this.isSpeaking = true;
    this.playNeuralChirp();
    this.showBanner(profile, textToSpeak);

    if (!this.isMuted && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      const chosenVoice = this.selectVoiceForOctopus(profile);

      if (chosenVoice) {
        utterance.voice = chosenVoice;
      }

      utterance.pitch = profile.pitch;
      utterance.rate = profile.rate;
      utterance.volume = 1.0;

      const finishUtterance = () => {
        this.isSpeaking = false;
        this.stopAudioWaveAnimation();
        if (this.speechQueue.length > 0) {
          const next = this.speechQueue.shift()!;
          window.setTimeout(() => this.executeSpeech(next.profile, next.textToSpeak), 650);
        } else {
          this.hideTimer = window.setTimeout(() => {
            this.hideBanner();
          }, 3200);
        }
      };

      utterance.onend = finishUtterance;
      utterance.onerror = finishUtterance;

      window.speechSynthesis.speak(utterance);
    } else {
      this.isSpeaking = false;
      this.stopAudioWaveAnimation();
      if (this.speechQueue.length > 0) {
        const next = this.speechQueue.shift()!;
        window.setTimeout(() => this.executeSpeech(next.profile, next.textToSpeak), 650);
      } else {
        this.hideTimer = window.setTimeout(() => {
          this.hideBanner();
        }, 4500);
      }
    }
  }

  private showBanner(profile: OctopusSpeechProfile, explicitText?: string) {
    if (!this.bannerContainer) return;

    const glyphSvg = ICONS.octoGlyph(profile.id, 16);
    const speechText =
      explicitText ||
      (this.domainMode === 'SOFTWARE'
        ? profile.softwareScript
        : this.domainMode === 'AIML'
        ? profile.aimlScript
        : profile.dualScript);

    this.bannerContainer.style.display = 'block';
    this.bannerContainer.style.borderColor = profile.colorHex;
    this.bannerContainer.style.boxShadow = `0 4px 28px ${profile.colorHex}33, 0 0 1px ${profile.colorHex}`;

    const modeBadge =
      this.domainMode === 'DUAL'
        ? `<span class="mode-tag-dual">DUAL-DOMAIN (SW + AI/ML)</span>`
        : this.domainMode === 'SOFTWARE'
        ? `<span class="mode-tag-sw">SOFTWARE DEV MODE</span>`
        : `<span class="mode-tag-aiml">AI/ML RESEARCH MODE</span>`;

    let rolesHtml: string;
    if (this.domainMode === 'DUAL') {
      rolesHtml = `
        <div class="dual-roles-container">
          <div class="dual-role-line">
            <span class="role-pill sw">SOFTWARE</span>
            <span class="role-spec"><strong>${profile.softwareTitle}:</strong> ${profile.softwareRole}</span>
          </div>
          <div class="dual-role-line">
            <span class="role-pill aiml">AI / ML</span>
            <span class="role-spec"><strong>${profile.aimlTitle}:</strong> ${profile.aimlRole}</span>
          </div>
        </div>
      `;
    } else if (this.domainMode === 'SOFTWARE') {
      rolesHtml = `
        <div class="single-role-line" style="color: ${profile.colorHex};">
          <strong>ROLE:</strong> ${profile.softwareTitle.toUpperCase()} — ${profile.softwareRole}
        </div>
      `;
    } else {
      rolesHtml = `
        <div class="single-role-line" style="color: #a6e3a1;">
          <strong>ROLE:</strong> ${profile.aimlTitle.toUpperCase()} — ${profile.aimlRole}
        </div>
      `;
    }

    this.bannerContainer.innerHTML = `
      <div class="voice-banner-header">
        <div class="voice-banner-title-wrap">
          <span class="voice-glyph">${glyphSvg}</span>
          <span class="voice-tag" style="color: ${profile.colorHex};">
            OCTO_${profile.id} // ${profile.title.toUpperCase()}
          </span>
          ${modeBadge}
        </div>

        <div class="voice-banner-status">
          <div class="audio-wave-bars" id="audio-wave-bars">
            <span style="background: ${profile.colorHex};"></span>
            <span style="background: ${profile.colorHex};"></span>
            <span style="background: ${profile.colorHex};"></span>
            <span style="background: ${profile.colorHex};"></span>
          </div>
          <span class="transmission-live-tag">LIVE TRANSMISSION</span>
          <button class="btn-banner-close" id="btn-banner-close" title="Dismiss subtitle">×</button>
        </div>
      </div>

      <div class="voice-banner-body">
        ${rolesHtml}
        <div class="voice-banner-text" id="voice-banner-text">
          "${speechText}"
        </div>
      </div>
    `;

    const btnClose = this.bannerContainer.querySelector('#btn-banner-close');
    if (btnClose) {
      btnClose.addEventListener('click', (e) => {
        e.stopPropagation();
        this.stopSpeaking();
        this.hideBanner();
      });
    }

    this.runTypewriter(speechText);
  }

  private runTypewriter(fullText: string) {
    const textEl = this.bannerContainer?.querySelector('#voice-banner-text');
    if (!textEl) return;

    textEl.textContent = '"';
    let charIndex = 0;
    const speed = 22;

    this.typewriterTimer = window.setInterval(() => {
      if (charIndex < fullText.length) {
        textEl.textContent = `"${fullText.substring(0, charIndex + 1)}"`;
        charIndex++;
      } else {
        if (this.typewriterTimer !== null) {
          clearInterval(this.typewriterTimer);
          this.typewriterTimer = null;
        }
      }
    }, speed);
  }

  private stopAudioWaveAnimation() {
    const wave = this.bannerContainer?.querySelector('#audio-wave-bars');
    if (wave) {
      wave.classList.add('paused');
    }
  }

  public hideBanner() {
    if (this.bannerContainer) {
      this.bannerContainer.style.display = 'none';
    }
  }
}
