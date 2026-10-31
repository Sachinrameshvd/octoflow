/**
 * Unit Tests for Telemetry Parser and Reconnect Controller (P4.4).
 *
 * Verifies:
 * 1. Valid telemetry messages across contracts (THEME_CHANGE, LIVE_SERVICE_READY, SwarmStep).
 * 2. Unknown and extra fields preserved safely.
 * 3. Malformed JSON and non-object inputs rejected with descriptive errors.
 * 4. Missing required fields caught by runtime type guards.
 * 5. ReconnectController exponential backoff and timer cancellation with fake timers.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  parseTelemetryMessage,
  isThemeChangeEvent,
  isLiveServiceReadyEvent,
  isSwarmStepEvent,
  ReconnectController,
} from './parse';

describe('Telemetry Message Parser', () => {
  describe('Valid Messages', () => {
    it('parses valid THEME_CHANGE messages from JSON string', () => {
      const raw = JSON.stringify({
        type: 'THEME_CHANGE',
        tokens: {
          primary_hex: '#38BDF8',
          secondary_hex: '#A855F7',
          bg_hex: '#020617',
        },
      });

      const res = parseTelemetryMessage(raw);
      expect(res.success).toBe(true);
      expect(res.data).toBeDefined();
      expect(res.data?.type).toBe('THEME_CHANGE');
      if (res.data && isThemeChangeEvent(res.data)) {
        expect(res.data.tokens.primary_hex).toBe('#38BDF8');
        expect(res.data.tokens.bg_hex).toBe('#020617');
      }
    });

    it('parses valid LIVE_SERVICE_READY messages with direct service_url', () => {
      const raw = {
        event_type: 'LIVE_SERVICE_READY',
        service_url: 'http://localhost:5173',
        service_type: 'web_dashboard',
      };

      const res = parseTelemetryMessage(raw);
      expect(res.success).toBe(true);
      expect(res.data).toBeDefined();
      if (res.data && isLiveServiceReadyEvent(res.data)) {
        expect(res.data.service_url).toBe('http://localhost:5173');
        expect(res.data.service_type).toBe('web_dashboard');
      }
    });

    it('parses LIVE_SERVICE_READY messages with nested payload.primary_url', () => {
      const raw = {
        event_type: 'DEPLOYMENT_UPDATE',
        payload: {
          primary_url: 'http://127.0.0.1:8000',
        },
      };

      const res = parseTelemetryMessage(raw);
      expect(res.success).toBe(true);
      if (res.data && isLiveServiceReadyEvent(res.data)) {
        expect(res.data.payload?.primary_url).toBe('http://127.0.0.1:8000');
      }
    });

    it('parses valid SwarmStep events with octopus neural state', () => {
      const raw = {
        octopus_id: 2,
        arm_id: 5,
        status: 'ACTIVE',
        summary: 'Synthesizing biophysical synapses',
        progress_pct: 75.5,
        surprise: 0.12,
      };

      const res = parseTelemetryMessage(raw);
      expect(res.success).toBe(true);
      if (res.data && isSwarmStepEvent(res.data)) {
        expect(res.data.octopus_id).toBe(2);
        expect(res.data.arm_id).toBe(5);
        expect(res.data.progress_pct).toBe(75.5);
        expect(res.data.surprise).toBe(0.12);
      }
    });

    it('parses global swarm morphology and dry_run mode updates', () => {
      const raw = {
        morphology: 'aiml_research',
        mode: 'dry_run',
      };

      const res = parseTelemetryMessage(raw);
      expect(res.success).toBe(true);
      if (res.data && isSwarmStepEvent(res.data)) {
        expect(res.data.morphology).toBe('aiml_research');
        expect(res.data.mode).toBe('dry_run');
      }
    });
  });

  describe('Unknown and Extra Fields', () => {
    it('preserves unrecognized extra fields without schema rejection', () => {
      const raw = {
        type: 'THEME_CHANGE',
        tokens: { primary_hex: '#10B981' },
        future_flag_v2: true,
        cluster_region: 'us-west-2',
        telemetry_revision: 42,
      };

      const res = parseTelemetryMessage(raw);
      expect(res.success).toBe(true);
      expect(res.data).toBeDefined();
      expect((res.data as Record<string, unknown>).future_flag_v2).toBe(true);
      expect((res.data as Record<string, unknown>).cluster_region).toBe('us-west-2');
      expect((res.data as Record<string, unknown>).telemetry_revision).toBe(42);
    });
  });

  describe('Malformed JSON', () => {
    it('returns failure for syntactically invalid JSON string without throwing', () => {
      const broken = '{"type": "THEME_CHANGE", tokens: broken';
      const res = parseTelemetryMessage(broken);
      expect(res.success).toBe(false);
      expect(res.error).toMatch(/Malformed JSON/);
      expect(res.data).toBeUndefined();
    });

    it('rejects truncated JSON strings safely', () => {
      const truncated = '{"octopus_id": 1,';
      const res = parseTelemetryMessage(truncated);
      expect(res.success).toBe(false);
      expect(res.error).toMatch(/Malformed JSON/);
    });
  });

  describe('Missing Fields & Invalid Payloads', () => {
    it('rejects null, primitives, and arrays', () => {
      expect(parseTelemetryMessage(null).success).toBe(false);
      expect(parseTelemetryMessage(12345).success).toBe(false);
      expect(parseTelemetryMessage(true).success).toBe(false);
      expect(parseTelemetryMessage(['not', 'an', 'object']).success).toBe(false);
    });

    it('rejects empty plain object matching no contract', () => {
      const res = parseTelemetryMessage({});
      expect(res.success).toBe(false);
      expect(res.error).toMatch(/Unrecognized telemetry schema/);
    });

    it('rejects THEME_CHANGE missing required tokens record', () => {
      const raw = { type: 'THEME_CHANGE', tokens: 'not-an-object' };
      const res = parseTelemetryMessage(raw);
      expect(res.success).toBe(false);
    });

    it('rejects non-numeric octopus_id in step message', () => {
      const raw = { octopus_id: 'arm-two' };
      const res = parseTelemetryMessage(raw);
      expect(res.success).toBe(false);
    });
  });
});

describe('ReconnectController Backoff Logic', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('calculates bounded exponential backoff on consecutive failures', () => {
    const controller = new ReconnectController({
      initialDelayMs: 1000,
      maxDelayMs: 5000,
      backoffMultiplier: 2.0,
    });

    expect(controller.getAttempts()).toBe(0);
    expect(controller.getNextDelay()).toBe(1000);

    // 1st failure: delay used = 1000, next = 2000
    const d1 = controller.recordFailure();
    expect(d1).toBe(1000);
    expect(controller.getAttempts()).toBe(1);
    expect(controller.getNextDelay()).toBe(2000);

    // 2nd failure: delay used = 2000, next = 4000
    const d2 = controller.recordFailure();
    expect(d2).toBe(2000);
    expect(controller.getAttempts()).toBe(2);
    expect(controller.getNextDelay()).toBe(4000);

    // 3rd failure: delay used = 4000, next capped at maxDelayMs = 5000
    const d3 = controller.recordFailure();
    expect(d3).toBe(4000);
    expect(controller.getAttempts()).toBe(3);
    expect(controller.getNextDelay()).toBe(5000);

    // 4th failure: capped at maxDelayMs = 5000
    const d4 = controller.recordFailure();
    expect(d4).toBe(5000);
    expect(controller.getNextDelay()).toBe(5000);
  });

  it('resets attempts and delay to initial values on recordSuccess', () => {
    const controller = new ReconnectController({ initialDelayMs: 800 });
    controller.recordFailure();
    controller.recordFailure();
    expect(controller.getAttempts()).toBe(2);
    expect(controller.getNextDelay()).toBeGreaterThan(800);

    controller.recordSuccess();
    expect(controller.getAttempts()).toBe(0);
    expect(controller.getNextDelay()).toBe(800);
  });

  it('schedules connect callback and triggers with fake timers', () => {
    const controller = new ReconnectController({ initialDelayMs: 1500 });
    const connectSpy = vi.fn();

    const delay = controller.schedule(connectSpy);
    expect(delay).toBe(1500);
    expect(connectSpy).not.toHaveBeenCalled();

    // Advance halfway: still not called
    vi.advanceTimersByTime(1000);
    expect(connectSpy).not.toHaveBeenCalled();

    // Advance remainder: called exactly once
    vi.advanceTimersByTime(500);
    expect(connectSpy).toHaveBeenCalledTimes(1);
  });

  it('cancels scheduled reconnection when cancel() is invoked', () => {
    const controller = new ReconnectController({ initialDelayMs: 2000 });
    const connectSpy = vi.fn();

    controller.schedule(connectSpy);
    vi.advanceTimersByTime(1000);

    controller.cancel();
    vi.advanceTimersByTime(5000);

    expect(connectSpy).not.toHaveBeenCalled();
  });
});
