/**
 * Unit Tests for Audio Opt-In & Speech Default OFF (P6.4).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setupMockEnvironment } from './test-dom';
import { CephalopodVoiceSystem } from '../audio/speech-synthesizer';

describe('CephalopodVoiceSystem Audio Opt-in Policy', () => {
  let mockEnv: ReturnType<typeof setupMockEnvironment>;
  let mockSpeak: any;
  let mockCancel: any;

  beforeEach(() => {
    mockEnv = setupMockEnvironment();
    mockSpeak = vi.fn();
    mockCancel = vi.fn();

    mockEnv.win.speechSynthesis = {
      speak: mockSpeak,
      cancel: mockCancel,
      getVoices: () => [],
      onvoiceschanged: null,
    };
    (globalThis as any).speechSynthesis = mockEnv.win.speechSynthesis;
    (globalThis as any).SpeechSynthesisUtterance = class {
      text: string;
      voice: any = null;
      pitch: number = 1.0;
      rate: number = 1.0;
      volume: number = 1.0;
      onend: any = null;
      onerror: any = null;
      constructor(text: string) {
        this.text = text;
      }
    };
  });

  it('defaults to muted (OFF) on initialization', () => {
    const voiceSystem = new CephalopodVoiceSystem();
    expect(voiceSystem.getIsMuted()).toBe(true);
    // Verified: No speech started on load
    expect(mockSpeak).not.toHaveBeenCalled();
  });

  it('does NOT speak when speakOctopusRole is called while muted', () => {
    const voiceSystem = new CephalopodVoiceSystem();
    expect(voiceSystem.getIsMuted()).toBe(true);

    voiceSystem.speakOctopusRole(7);
    voiceSystem.speakOctopusRole(0);

    // Audio/speech synthesis must not trigger while muted
    expect(mockSpeak).not.toHaveBeenCalled();
  });

  it('does NOT speak when speakCustom is called while muted', () => {
    const voiceSystem = new CephalopodVoiceSystem();
    voiceSystem.speakCustom('System Alert', 'Testing custom speech when muted');
    expect(mockSpeak).not.toHaveBeenCalled();
  });

  it('speaks ONLY after user explicitly enables voice audio', () => {
    const voiceSystem = new CephalopodVoiceSystem();
    expect(voiceSystem.getIsMuted()).toBe(true);

    // User action: toggle voice ON
    const newMuteState = voiceSystem.toggleMute();
    expect(newMuteState).toBe(false);
    expect(voiceSystem.getIsMuted()).toBe(false);
    expect(mockEnv.storage.getItem('octoflow_voice_muted')).toBe('false');

    // Now speaking should invoke speechSynthesis.speak
    voiceSystem.speakOctopusRole(2);
    expect(mockSpeak).toHaveBeenCalledTimes(1);
  });

  it('cancels active speech when user toggles voice back to muted', () => {
    const voiceSystem = new CephalopodVoiceSystem();
    voiceSystem.setMuted(false);
    voiceSystem.speakOctopusRole(1);

    // User mutes again
    voiceSystem.toggleMute();
    expect(voiceSystem.getIsMuted()).toBe(true);
    expect(mockCancel).toHaveBeenCalled();
    expect(mockEnv.storage.getItem('octoflow_voice_muted')).toBe('true');
  });

  it('respects persisted localStorage unmuted preference on subsequent load', () => {
    mockEnv.storage.setItem('octoflow_voice_muted', 'false');
    const voiceSystem = new CephalopodVoiceSystem();
    expect(voiceSystem.getIsMuted()).toBe(false);
  });
});
