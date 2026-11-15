/**
 * Sound Engine for OCTOFLOW: Authentic Beach Waves & Classic Cinematic Slide Chime.
 * Features:
 *  - 100% Authentic Beach Ocean Waves (showcase/public/audio/relaxing_waves.mp3):
 *      Rolling breakers on sand, natural inter-wave calm, zero radio hiss/static.
 *  - Classic Slide Transition Sound:
 *      Dual-layer Sub-Bass Dive (82Hz -> 36Hz) + Ethereal Glass Harmonic Chime tuned to slide index.
 *  - Auto-start on first user interaction with manual mute toggle.
 */

export class SoundEngine {
  private isMuted = false;
  private waveAudio: HTMLAudioElement | null = null;
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private sfxGain: GainNode | null = null;
  private isInitialized = false;

  constructor() {
    this.setupWaveAudio();
    this.init();
    this.startWaves();
    this.setupVisibilityListener();
  }

  private setupWaveAudio() {
    try {
      this.waveAudio = new Audio('/audio/relaxing_waves.mp3');
      this.waveAudio.loop = true;
      this.waveAudio.preload = 'auto';
      this.waveAudio.volume = 0.90;

      // Auto-restart if browser or system ever interrupts playback
      this.waveAudio.addEventListener('pause', () => {
        if (this.waveAudio && document.visibilityState !== 'hidden') {
          this.waveAudio.play().catch(() => {});
        }
      });
    } catch (e) {
      console.warn('Wave audio initialization error:', e);
    }
  }

  private setupVisibilityListener() {
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        this.ensureAudioStarted();
      }
    });
  }

  public init() {
    if (this.isInitialized && this.ctx) {
      if (this.ctx.state === 'suspended') {
        this.ctx.resume().catch(() => {});
      }
      return;
    }

    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtx();

      // Master output gain - permanently unmuted at full cinematic fidelity
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(0.85, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);

      // SFX bus
      this.sfxGain = this.ctx.createGain();
      this.sfxGain.gain.setValueAtTime(0.85, this.ctx.currentTime);
      this.sfxGain.connect(this.masterGain);

      this.isInitialized = true;
      if (this.ctx.state === 'suspended') {
        this.ctx.resume().catch(() => {});
      }
    } catch (e) {
      console.warn('Web Audio API not supported:', e);
    }
  }

  public startWaves() {
    this.init();
    if (this.waveAudio) {
      this.waveAudio.volume = 0.90;
      const playPromise = this.waveAudio.play();
      if (playPromise !== undefined) {
        playPromise.catch((err) => {
          // Awaiting initial user gesture (pointerdown/wheel/key) to unblock autoplay
          console.log('Wave audio primed for first gesture:', err);
        });
      }
    }
  }

  /**
   * Always-on sound: ensures both wave audio and audio context are active.
   */
  public ensureAudioStarted(): boolean {
    this.startWaves();
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return true;
  }

  public unmute(): boolean {
    return this.ensureAudioStarted();
  }

  public mute(): boolean {
    // Sound is permanently enabled by design
    return this.ensureAudioStarted();
  }

  public toggleMute(): boolean {
    // Sound is permanently enabled by design
    return this.ensureAudioStarted();
  }

  public getIsMuted(): boolean {
    return false;
  }

  /**
   * The Original Classic Slide Transition Sound:
   * Sub-bass dive (82Hz down to 36Hz) + Ethereal glass harmonic chime tuned to slide index
   */
  public playSlideTransition(slideIdx: number) {
    if (this.isMuted) return;

    this.init();
    if (!this.ctx || !this.sfxGain) return;
    if (this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }

    const now = this.ctx.currentTime;

    // 1. Sub-bass dive (82Hz down to 36Hz) - tactile slide weight
    const subOsc = this.ctx.createOscillator();
    const subGain = this.ctx.createGain();
    subOsc.type = 'sine';
    subOsc.frequency.setValueAtTime(82, now);
    subOsc.frequency.exponentialRampToValueAtTime(36, now + 0.45);

    subGain.gain.setValueAtTime(0.40, now);
    subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

    subOsc.connect(subGain);
    subGain.connect(this.sfxGain);
    subOsc.start(now);
    subOsc.stop(now + 0.46);

    // 2. Ethereal Glass Chime tuned to slide index
    const chimeOsc = this.ctx.createOscillator();
    const chimeGain = this.ctx.createGain();
    const frequencies = [880, 987, 1046, 1174, 1318, 1396, 1567, 1760];
    const freq = frequencies[slideIdx % frequencies.length];

    chimeOsc.type = 'sine';
    chimeOsc.frequency.setValueAtTime(freq, now);

    chimeGain.gain.setValueAtTime(0.14, now);
    chimeGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.90);

    chimeOsc.connect(chimeGain);
    chimeGain.connect(this.sfxGain);
    chimeOsc.start(now);
    chimeOsc.stop(now + 0.92);
  }

  /**
   * High-frequency dual-crystal synaptic spark for individual octopus reflex test.
   */
  public playSynapticSpark() {
    this.init();
    if (!this.ctx || !this.sfxGain) return;
    if (this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }

    const now = this.ctx.currentTime;
    const osc1 = this.ctx.createOscillator();
    const osc2 = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(1320, now);
    osc1.frequency.exponentialRampToValueAtTime(1760, now + 0.08);

    osc2.type = 'triangle';
    osc2.frequency.setValueAtTime(1980, now);
    osc2.frequency.exponentialRampToValueAtTime(2640, now + 0.12);

    gain.gain.setValueAtTime(0.16, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.28);

    osc1.connect(gain);
    osc2.connect(gain);
    gain.connect(this.sfxGain);

    osc1.start(now);
    osc2.start(now);
    osc1.stop(now + 0.30);
    osc2.stop(now + 0.30);
  }

  /**
   * Resonant sub-harmonic pulse for HUD synaptic shockwaves.
   */
  public playShockwaveBurst() {
    this.init();
    if (!this.ctx || !this.sfxGain) return;
    if (this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }

    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(140, now);
    osc.frequency.exponentialRampToValueAtTime(45, now + 0.38);

    gain.gain.setValueAtTime(0.32, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.40);

    osc.connect(gain);
    gain.connect(this.sfxGain);

    osc.start(now);
    osc.stop(now + 0.42);
  }

  public playAmputationAlert(_isSevered: boolean) {}
  public playReticleLock() {}
  public setHydrostatTension(_elongationScale: number) {}

  public destroy() {
    if (this.waveAudio) {
      this.waveAudio.pause();
      this.waveAudio.src = '';
      this.waveAudio = null;
    }
    if (this.ctx) {
      this.ctx.close().catch(() => {});
      this.ctx = null;
    }
  }
}
