/**
 * Motion Accessibility Policy Module (P6.4).
 *
 * Implements WCAG 2.2 AA Reduced Motion compliance:
 * - Detects OS-level prefers-reduced-motion media query.
 * - Supports user-toggled override persisted safely in localStorage.
 * - Dispatches updates to visual engines (particle suppression, camera jumps).
 * - Toggles .reduced-motion CSS class on document root.
 */

const STORAGE_KEY = 'octoflow_reduced_motion';

export class MotionPolicy {
  private static instance: MotionPolicy | null = null;
  private listeners: Set<(reduced: boolean) => void> = new Set();
  private userOverride: boolean | null = null;
  private mediaQueryList: MediaQueryList | null = null;

  private constructor() {
    this.init();
  }

  public static getInstance(): MotionPolicy {
    if (!MotionPolicy.instance) {
      MotionPolicy.instance = new MotionPolicy();
    }
    return MotionPolicy.instance;
  }

  /** Reset singleton instance (useful for clean unit test suites). */
  public static resetInstance(): void {
    if (MotionPolicy.instance?.mediaQueryList) {
      try {
        MotionPolicy.instance.mediaQueryList.onchange = null;
      } catch {
        // no-op
      }
    }
    MotionPolicy.instance = null;
  }

  private init(): void {
    // 1. Read persisted user preference
    this.userOverride = this.readStorage();

    // 2. Bind OS media query listener if available in browser
    if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
      try {
        this.mediaQueryList = window.matchMedia('(prefers-reduced-motion: reduce)');
        const handler = () => {
          if (this.userOverride === null) {
            this.syncBodyClass();
            this.notifyListeners();
          }
        };

        if ('addEventListener' in this.mediaQueryList) {
          this.mediaQueryList.addEventListener('change', handler);
        } else {
          // Legacy browsers
          (this.mediaQueryList as any).addListener?.(handler);
        }
      } catch {
        // Environment does not support matchMedia
      }
    }

    this.syncBodyClass();
  }

  private readStorage(): boolean | null {
    if (typeof window === 'undefined' || !window.localStorage) {
      return null;
    }
    try {
      const val = window.localStorage.getItem(STORAGE_KEY);
      if (val === 'true') return true;
      if (val === 'false') return false;
      return null;
    } catch {
      // LocalStorage access restricted (e.g., sandbox or private browsing)
      return null;
    }
  }

  private writeStorage(val: boolean | null): void {
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }
    try {
      if (val === null) {
        window.localStorage.removeItem(STORAGE_KEY);
      } else {
        window.localStorage.setItem(STORAGE_KEY, String(val));
      }
    } catch {
      // LocalStorage access restricted
    }
  }

  /**
   * Determine whether reduced motion is active.
   * User override in localStorage takes precedence; otherwise falls back to OS media query.
   */
  public isReducedMotion(): boolean {
    if (this.userOverride !== null) {
      return this.userOverride;
    }
    if (this.mediaQueryList) {
      return this.mediaQueryList.matches;
    }
    return false;
  }

  /** Set explicit reduced motion override. */
  public setReducedMotion(enabled: boolean): void {
    this.userOverride = enabled;
    this.writeStorage(enabled);
    this.syncBodyClass();
    this.notifyListeners();
  }

  /** Toggle active reduced motion state. Returns new state. */
  public toggleReducedMotion(): boolean {
    const next = !this.isReducedMotion();
    this.setReducedMotion(next);
    return next;
  }

  /** Reset user override to follow system/OS preference. */
  public clearOverride(): void {
    this.userOverride = null;
    this.writeStorage(null);
    this.syncBodyClass();
    this.notifyListeners();
  }

  /** Subscribe to reduced motion state changes. Returns an unsubscribe function. */
  public addListener(callback: (reduced: boolean) => void): () => void {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }

  private notifyListeners(): void {
    const state = this.isReducedMotion();
    for (const listener of this.listeners) {
      try {
        listener(state);
      } catch (err) {
        console.error('Error in motion policy listener:', err);
      }
    }
  }

  private syncBodyClass(): void {
    if (typeof document === 'undefined') return;
    const reduced = this.isReducedMotion();
    if (reduced) {
      document.documentElement.classList.add('reduced-motion');
      document.body?.classList.add('reduced-motion');
    } else {
      document.documentElement.classList.remove('reduced-motion');
      document.body?.classList.remove('reduced-motion');
    }
  }
}

/** Global convenience helpers */
export function isReducedMotion(): boolean {
  return MotionPolicy.getInstance().isReducedMotion();
}

export function setReducedMotion(enabled: boolean): void {
  MotionPolicy.getInstance().setReducedMotion(enabled);
}

export function toggleReducedMotion(): boolean {
  return MotionPolicy.getInstance().toggleReducedMotion();
}

