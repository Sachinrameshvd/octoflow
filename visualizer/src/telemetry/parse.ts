/**
 * Pure Telemetry Message Parsing and Validation Module (P4.4).
 *
 * Implements runtime validation using hand-written TypeScript type guards
 * with zero external dependencies. Validates all event structures received
 * over the OctoFlow WebSocket telemetry feed.
 */

export interface ThemeTokens {
  primary_hex?: string;
  secondary_hex?: string;
  accent_hex?: string;
  success_hex?: string;
  warning_hex?: string;
  danger_hex?: string;
  bg_hex?: string;
}

export interface ThemeChangeEvent {
  type: 'THEME_CHANGE';
  event_type?: string;
  tokens: ThemeTokens;
  [key: string]: unknown;
}

export interface LiveServiceReadyEvent {
  event_type: 'LIVE_SERVICE_READY' | string;
  service_url?: string;
  service_type?: string;
  payload?: {
    primary_url?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface SwarmStepEvent {
  octopus_id: number;
  arm_id?: number;
  status?: string;
  summary?: string;
  progress_pct?: number;
  surprise?: number;
  mode?: string;
  morphology?: 'aiml_research' | 'software_dev' | 'fullstack_ai' | string;
  event_type?: string;
  type?: string;
  [key: string]: unknown;
}

export type TelemetryEvent =
  | ThemeChangeEvent
  | LiveServiceReadyEvent
  | SwarmStepEvent;

/** Type guard to check if an unknown value is a non-null plain record. */
export function isRecord(val: unknown): val is Record<string, unknown> {
  return typeof val === 'object' && val !== null && !Array.isArray(val);
}

/** Type guard for theme change telemetry messages. */
export function isThemeChangeEvent(val: unknown): val is ThemeChangeEvent {
  if (!isRecord(val)) return false;
  const isType = val.type === 'THEME_CHANGE' || val.event_type === 'THEME_CHANGE';
  if (!isType) return false;
  return isRecord(val.tokens);
}

/** Type guard for live service deployment readiness telemetry messages. */
export function isLiveServiceReadyEvent(val: unknown): val is LiveServiceReadyEvent {
  if (!isRecord(val)) return false;
  if (val.event_type === 'LIVE_SERVICE_READY') return true;
  if (typeof val.service_url === 'string' && val.service_url.length > 0) return true;
  if (isRecord(val.payload) && typeof val.payload.primary_url === 'string') return true;
  return false;
}

/** Type guard for swarm progress, state, and neural activation telemetry messages. */
export function isSwarmStepEvent(val: unknown): val is SwarmStepEvent {
  if (!isRecord(val)) return false;
  if (typeof val.octopus_id === 'number') {
    return Number.isFinite(val.octopus_id);
  }
  // Swarm messages may specify morphology or dry_run mode without explicit octopus_id
  if (typeof val.morphology === 'string' || typeof val.mode === 'string') {
    return true;
  }
  return false;
}

/** Comprehensive type guard verifying if an unknown object is any valid TelemetryEvent. */
export function isTelemetryEvent(val: unknown): val is TelemetryEvent {
  return (
    isThemeChangeEvent(val) ||
    isLiveServiceReadyEvent(val) ||
    isSwarmStepEvent(val)
  );
}

export interface ParseResult<T = TelemetryEvent> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Parses and validates incoming WebSocket messages.
 *
 * Supports stringified JSON or already-decoded objects.
 * Handles malformed JSON, non-object types, missing fields, and preserves unknown fields.
 */
export function parseTelemetryMessage(raw: unknown): ParseResult<TelemetryEvent> {
  let parsed: unknown;

  if (typeof raw === 'string') {
    try {
      parsed = JSON.parse(raw);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return { success: false, error: `Malformed JSON: ${msg}` };
    }
  } else {
    parsed = raw;
  }

  if (!isRecord(parsed)) {
    return {
      success: false,
      error: `Invalid telemetry payload: expected an object, got ${parsed === null ? 'null' : typeof parsed}`,
    };
  }

  if (isThemeChangeEvent(parsed)) {
    return { success: true, data: parsed };
  }

  if (isLiveServiceReadyEvent(parsed)) {
    return { success: true, data: parsed };
  }

  if (isSwarmStepEvent(parsed)) {
    return { success: true, data: parsed };
  }

  return {
    success: false,
    error: 'Unrecognized telemetry schema: payload did not match any known event contract',
  };
}

/** Configuration options for exponential backoff reconnection. */
export interface ReconnectOptions {
  initialDelayMs?: number;
  maxDelayMs?: number;
  backoffMultiplier?: number;
}

/**
 * Manages WebSocket reconnection backoff with deterministic timing and state tracking.
 */
export class ReconnectController {
  public readonly initialDelayMs: number;
  public readonly maxDelayMs: number;
  public readonly backoffMultiplier: number;

  private currentDelay: number;
  private attempts: number = 0;
  private timerId: ReturnType<typeof setTimeout> | null = null;

  constructor(options: ReconnectOptions = {}) {
    this.initialDelayMs = options.initialDelayMs ?? 1000;
    this.maxDelayMs = options.maxDelayMs ?? 15000;
    this.backoffMultiplier = options.backoffMultiplier ?? 1.5;
    this.currentDelay = this.initialDelayMs;
  }

  /** Return the next reconnection delay without advancing the counter. */
  public getNextDelay(): number {
    return this.currentDelay;
  }

  /** Return current failure attempts count. */
  public getAttempts(): number {
    return this.attempts;
  }

  /** Record a connection failure and compute the next backoff delay. */
  public recordFailure(): number {
    this.attempts += 1;
    const delay = this.currentDelay;
    this.currentDelay = Math.min(this.currentDelay * this.backoffMultiplier, this.maxDelayMs);
    return delay;
  }

  /** Record a successful connection, resetting delay and attempts. */
  public recordSuccess(): void {
    this.cancel();
    this.attempts = 0;
    this.currentDelay = this.initialDelayMs;
  }

  /** Schedule a reconnect callback using the current backoff delay. */
  public schedule(connectFn: () => void): number {
    this.cancel();
    const delay = this.recordFailure();
    this.timerId = setTimeout(() => {
      this.timerId = null;
      connectFn();
    }, delay);
    return delay;
  }

  /** Cancel any pending reconnect timer. */
  public cancel(): void {
    if (this.timerId !== null) {
      clearTimeout(this.timerId);
      this.timerId = null;
    }
  }

  /** Fully reset the controller. */
  public reset(): void {
    this.cancel();
    this.attempts = 0;
    this.currentDelay = this.initialDelayMs;
  }
}
