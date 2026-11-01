export interface TokenContrastDef {
  name: string;
  hex: string;
  minRatio: number;
  description?: string;
}

export interface ContrastResult {
  token: string;
  hex: string;
  target: string;
  ratioSpace: string;
  ratioGlass: string;
  passed: boolean;
}

export interface ContrastAuditOutcome {
  success: boolean;
  results: ContrastResult[];
}

export declare function getRelativeLuminance(hex: string): number;
export declare function getContrastRatio(hex1: string, hex2: string): number;
export declare const BACKGROUNDS: { bgSpace: string; glassSurface: string };
export declare const TEXT_TOKENS: TokenContrastDef[];
export declare const ACCENT_TOKENS: TokenContrastDef[];
export declare const ARM_TOKENS: TokenContrastDef[];
export declare function runContrastCheck(): ContrastAuditOutcome;

