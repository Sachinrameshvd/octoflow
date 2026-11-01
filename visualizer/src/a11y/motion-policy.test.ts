/**
 * Unit Tests for Motion Policy & Reduced Motion (P6.4).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setupMockEnvironment } from './test-dom';
import { MotionPolicy, isReducedMotion, setReducedMotion, toggleReducedMotion } from './motion-policy';

describe('MotionPolicy Module', () => {
  let mockEnv: ReturnType<typeof setupMockEnvironment>;

  beforeEach(() => {
    mockEnv = setupMockEnvironment();
    MotionPolicy.resetInstance();
  });

  it('defaults to false when OS media query is not matched and no override is set', () => {
    mockEnv.win.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    MotionPolicy.resetInstance();
    expect(isReducedMotion()).toBe(false);
  });

  it('detects OS prefers-reduced-motion media query when true', () => {
    mockEnv.win.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes('reduce'),
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    MotionPolicy.resetInstance();
    expect(isReducedMotion()).toBe(true);
  });

  it('user explicit override takes precedence over OS media query', () => {
    mockEnv.win.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    MotionPolicy.resetInstance();
    expect(isReducedMotion()).toBe(true);

    // User disables reduced motion explicitly
    setReducedMotion(false);
    expect(isReducedMotion()).toBe(false);
    expect(mockEnv.storage.getItem('octoflow_reduced_motion')).toBe('false');

    // User re-enables
    toggleReducedMotion();
    expect(isReducedMotion()).toBe(true);
    expect(mockEnv.storage.getItem('octoflow_reduced_motion')).toBe('true');
  });

  it('notifies registered listeners on state change', () => {
    const policy = MotionPolicy.getInstance();
    const listener = vi.fn();
    const unsubscribe = policy.addListener(listener);

    policy.setReducedMotion(true);
    expect(listener).toHaveBeenCalledWith(true);

    policy.setReducedMotion(false);
    expect(listener).toHaveBeenCalledWith(false);

    unsubscribe();
    policy.setReducedMotion(true);
    expect(listener).toHaveBeenCalledTimes(2);
  });

  it('handles restricted localStorage environments safely without throwing', () => {
    mockEnv.storage.getItem = () => {
      throw new Error('Access denied');
    };
    mockEnv.storage.setItem = () => {
      throw new Error('Access denied');
    };

    MotionPolicy.resetInstance();
    expect(() => setReducedMotion(true)).not.toThrow();
    expect(isReducedMotion()).toBe(true);
  });
});
