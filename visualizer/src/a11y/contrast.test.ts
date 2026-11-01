/**
 * Unit Tests for WCAG Contrast Calculation & Palette Verification (P6.4).
 */

import { describe, it, expect } from 'vitest';
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { getRelativeLuminance, getContrastRatio, runContrastCheck, BACKGROUNDS, TEXT_TOKENS, ARM_TOKENS } from '../../scripts/check_contrast.mjs';

describe('Contrast Verification Algorithm & Palette Audit', () => {
  it('correctly calculates relative luminance for boundary colors', () => {
    // Pure Black = 0.0, Pure White = 1.0
    expect(getRelativeLuminance('#000000')).toBeCloseTo(0.0, 4);
    expect(getRelativeLuminance('#ffffff')).toBeCloseTo(1.0, 4);
  });

  it('correctly calculates known contrast ratios', () => {
    // Black on White = 21:1
    const maxRatio = getContrastRatio('#ffffff', '#000000');
    expect(maxRatio).toBeCloseTo(21.0, 1);

    // Same color on itself = 1:1
    const minRatio = getContrastRatio('#38bdf8', '#38bdf8');
    expect(minRatio).toBeCloseTo(1.0, 2);
  });

  it('verifies that all text tokens meet WCAG 2.2 AA (>= 4.5:1 for body, >= 3.0:1 for dim/borders)', () => {
    for (const token of TEXT_TOKENS) {
      const ratio = getContrastRatio(token.hex, BACKGROUNDS.bgSpace);
      expect(
        ratio,
        `Token ${token.name} (${token.hex}) failed contrast requirement >= ${token.minRatio}:1`
      ).toBeGreaterThanOrEqual(token.minRatio);
    }
  });

  it('verifies that all 8 arm consortium identity colors meet or exceed 4.5:1 on space background', () => {
    for (const arm of ARM_TOKENS) {
      const ratio = getContrastRatio(arm.hex, BACKGROUNDS.bgSpace);
      expect(
        ratio,
        `Arm ${arm.name} (${arm.hex}) failed contrast requirement >= 4.5:1`
      ).toBeGreaterThanOrEqual(4.5);
    }
  });

  it('runs complete palette audit check successfully with zero violations', () => {
    const audit = runContrastCheck();
    expect(audit.success).toBe(true);
    expect(audit.results.length).toBeGreaterThanOrEqual(21);
    expect(audit.results.every((r: any) => r.passed)).toBe(true);
  });
});
