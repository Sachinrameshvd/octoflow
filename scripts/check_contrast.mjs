#!/usr/bin/env node
/* global console, process */
/**
 * WCAG 2.2 AA Contrast Ratio Verification Script (P6.4).
 *
 * Computes exact relative luminance and contrast ratios for all design tokens,
 * text hierarchies, UI accents, and arm colors against terminal/visualizer backgrounds.
 *
 * Thresholds:
 * - Normal text (< 18pt or < 14pt bold): >= 4.5:1
 * - Large text (>= 18pt / 14pt bold) and graphical UI elements: >= 3.0:1
 */

/**
 * Calculates relative luminance of an sRGB hex color according to WCAG 2.2 specification.
 * https://www.w3.org/TR/WCAG22/#dfn-relative-luminance
 */
export function getRelativeLuminance(hex) {
  const cleanHex = hex.replace('#', '').trim();
  const r8 = parseInt(cleanHex.slice(0, 2), 16);
  const g8 = parseInt(cleanHex.slice(2, 4), 16);
  const b8 = parseInt(cleanHex.slice(4, 6), 16);

  const [r, g, b] = [r8, g8, b8].map((c8) => {
    const s = c8 / 255;
    return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Calculates WCAG contrast ratio between two hex colors.
 * Returns ratio as a float (e.g., 4.5 for 4.5:1).
 */
export function getContrastRatio(hex1, hex2) {
  const lum1 = getRelativeLuminance(hex1);
  const lum2 = getRelativeLuminance(hex2);
  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);
  return (lighter + 0.05) / (darker + 0.05);
}

// Visualizer Surface Backgrounds
export const BACKGROUNDS = {
  bgSpace: '#0b0b12',   // Primary space slate
  glassSurface: '#11111b', // Mantle acrylic composite
};

// Typography Tokens
export const TEXT_TOKENS = [
  { name: '--text-primary', hex: '#cdd6f4', minRatio: 4.5, description: 'Primary body text' },
  { name: '--text-secondary', hex: '#a6adc8', minRatio: 4.5, description: 'Secondary labels' },
  { name: '--text-muted', hex: '#787c95', minRatio: 4.5, description: 'Subtle captions & muted text' },
  { name: '--text-dim', hex: '#5e627c', minRatio: 3.0, description: 'UI borders & glyph dividers' },
];

// Accent & Status Colors
export const ACCENT_TOKENS = [
  { name: '--accent-cyan', hex: '#89dceb', minRatio: 4.5, description: 'Active focus ring & highlights' },
  { name: '--accent-sapphire', hex: '#74c7ec', minRatio: 4.5, description: 'Navigation & info' },
  { name: '--accent-blue', hex: '#89b4fa', minRatio: 4.5, description: 'Primary action buttons' },
  { name: '--accent-indigo', hex: '#b4befe', minRatio: 4.5, description: 'Free-fly mode accent' },
  { name: '--accent-purple', hex: '#cba6f7', minRatio: 4.5, description: 'Brain mode / cortex' },
  { name: '--accent-emerald', hex: '#94e2d5', minRatio: 4.5, description: 'Live problem solver' },
  { name: '--accent-amber', hex: '#fab387', minRatio: 4.5, description: 'Warning & fallback banner' },
  { name: '--accent-rose', hex: '#f38ba8', minRatio: 4.5, description: 'Anatomy / danger' },
  { name: '--accent-green', hex: '#a6e3a1', minRatio: 4.5, description: 'Success status & verified' },
];

// 8 Arm Identity Colors
export const ARM_TOKENS = [
  { name: 'Arm 0: System Architect [ARC]', hex: '#00F0FF', minRatio: 4.5 },
  { name: 'Arm 1: Database & Schemas [DB]', hex: '#A855F7', minRatio: 4.5 },
  { name: 'Arm 2: Backend API [BE]', hex: '#3B82F6', minRatio: 4.5 },
  { name: 'Arm 3: Frontend UI [FE]', hex: '#EC4899', minRatio: 4.5 },
  { name: 'Arm 4: Cognitive Core [COG]', hex: '#10B981', minRatio: 4.5 },
  { name: 'Arm 5: Security & Audit [SEC]', hex: '#EF4444', minRatio: 4.5 },
  { name: 'Arm 6: Chaos & QA [QA]', hex: '#F59E0B', minRatio: 4.5 },
  { name: 'Arm 7: DevOps & Deployment [OPS]', hex: '#EAB308', minRatio: 4.5 },
];

export function runContrastCheck() {
  let hasFailure = false;
  const results = [];

  const groups = [
    { title: '1. Typography Hierarchy', tokens: TEXT_TOKENS },
    { title: '2. UI Accent Tokens', tokens: ACCENT_TOKENS },
    { title: '3. 8-Arm Consortium Palette', tokens: ARM_TOKENS },
  ];

  console.log('========================================================================');
  console.log('◈ OctoFlow Visualizer: WCAG 2.2 AA Contrast Audit');
  console.log(`◈ Backgrounds tested: bg-space (${BACKGROUNDS.bgSpace}), glass (${BACKGROUNDS.glassSurface})`);
  console.log('========================================================================\n');

  for (const group of groups) {
    console.log(`--- ${group.title} ---`);
    for (const token of group.tokens) {
      const ratioSpace = getContrastRatio(token.hex, BACKGROUNDS.bgSpace);
      const ratioGlass = getContrastRatio(token.hex, BACKGROUNDS.glassSurface);
      const minRatio = token.minRatio;

      const passSpace = ratioSpace >= minRatio;
      const passGlass = ratioGlass >= minRatio;
      const passed = passSpace && passGlass;

      if (!passed) {
        hasFailure = true;
      }

      const status = passed ? '✓ PASS' : '✗ FAIL';
      const mark = passed ? '' : ' [VIOLATION]';

      results.push({
        token: token.name,
        hex: token.hex,
        target: `${minRatio.toFixed(1)}:1`,
        ratioSpace: `${ratioSpace.toFixed(2)}:1`,
        ratioGlass: `${ratioGlass.toFixed(2)}:1`,
        passed,
      });

      console.log(
        `  ${status} ${token.name.padEnd(34)} (${token.hex}) -> vs bg: ${ratioSpace.toFixed(2)}:1 | vs glass: ${ratioGlass.toFixed(2)}:1 [req: >=${minRatio.toFixed(1)}:1]${mark}`
      );
    }
    console.log('');
  }

  if (hasFailure) {
    console.error('✗ CONTRAST AUDIT FAILED: One or more tokens fall below WCAG 2.2 AA thresholds.\n');
    return { success: false, results };
  } else {
    console.log('✓ CONTRAST AUDIT PASSED: All 21 design tokens meet or exceed WCAG 2.2 AA contrast requirements.\n');
    return { success: true, results };
  }
}

// Direct execution CLI entrypoint
if (typeof process !== 'undefined' && process.argv && process.argv[1] && process.argv[1].endsWith('check_contrast.mjs')) {
  const result = runContrastCheck();
  if (!result.success) {
    process.exit(1);
  }
}
