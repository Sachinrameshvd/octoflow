/**
 * Central Cephalopod Arm Accessibility Profiles (P6.4).
 *
 * Enforces the WCAG 2.2 "Do not rely on color alone" guideline:
 * Every arm is identified by:
 * 1. Numeric ID (0-7)
 * 2. Human-readable Name
 * 3. Short 2-3 letter Code
 * 4. Distinct Geometric Symbol (Circle, Square, Triangle, Diamond, etc.)
 * 5. Theme Color with validated >= 4.5:1 contrast against dark backgrounds
 */

export interface ArmA11yProfile {
  id: number;
  name: string;
  code: string;
  symbol: string;
  symbolName: string;
  colorHex: string;
  department: string;
}

export const ARM_A11Y_PROFILES: ArmA11yProfile[] = [
  {
    id: 0,
    name: 'System Architect',
    code: 'ARC',
    symbol: '○',
    symbolName: 'Circle',
    colorHex: '#00F0FF',
    department: 'Architecture & Data',
  },
  {
    id: 1,
    name: 'Database & Schemas',
    code: 'DB',
    symbol: '□',
    symbolName: 'Square',
    colorHex: '#A855F7',
    department: 'Persistence & Models',
  },
  {
    id: 2,
    name: 'Backend API',
    code: 'BE',
    symbol: '△',
    symbolName: 'Triangle',
    colorHex: '#3B82F6',
    department: 'Core Engine & Compute',
  },
  {
    id: 3,
    name: 'Frontend UI',
    code: 'FE',
    symbol: '◇',
    symbolName: 'Diamond',
    colorHex: '#EC4899',
    department: 'Sensory & Evaluation',
  },
  {
    id: 4,
    name: 'Cognitive Core',
    code: 'COG',
    symbol: '⬡',
    symbolName: 'Hexagon',
    colorHex: '#10B981',
    department: 'Reasoning & Tuning',
  },
  {
    id: 5,
    name: 'Security & Audit',
    code: 'SEC',
    symbol: '▽',
    symbolName: 'Inverted Triangle',
    colorHex: '#EF4444',
    department: 'Guardianship & Quantization',
  },
  {
    id: 6,
    name: 'Chaos & QA',
    code: 'QA',
    symbol: '☆',
    symbolName: 'Star',
    colorHex: '#F59E0B',
    department: 'Verification & Serving',
  },
  {
    id: 7,
    name: 'DevOps & Deployment',
    code: 'OPS',
    symbol: '+',
    symbolName: 'Plus',
    colorHex: '#EAB308',
    department: 'Deployment & MLOps',
  },
];

/** Retrieve an arm profile by ID (defaults to Arm 0 if out of range). */
export function getArmProfile(armId: number): ArmA11yProfile {
  return ARM_A11Y_PROFILES.find((p) => p.id === armId) ?? ARM_A11Y_PROFILES[0];
}

/** Format an accessible string representation of an arm (Name + Code + Symbol). */
export function formatArmLabel(armId: number): string {
  const profile = getArmProfile(armId);
  return `${profile.symbol} [${profile.code}] Arm ${profile.id}: ${profile.name}`;
}

