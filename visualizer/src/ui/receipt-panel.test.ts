/**
 * Unit Tests for Token Receipt Modal Panel Renderer (P7.1).
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { setupMockEnvironment, MockElement } from '../a11y/test-dom';
import { ReceiptPanel, type ReceiptData } from './receipt-panel';

describe('ReceiptPanel Visualizer Component', () => {
  let mockEnv: ReturnType<typeof setupMockEnvironment>;
  let panel: ReceiptPanel;

  const mockReceipt: ReceiptData = {
    run_id: 'run-test-1234',
    mode: 'software_dev',
    provider: 'ollama',
    model: 'qwen2.5-coder:7b',
    duration_seconds: 14.2,
    dry_run: false,
    llm_calls: 16,
    tokens_in: 3200,
    tokens_out: 800,
    tokens_total: 4000,
    tokens_measured: 4000,
    tokens_estimated: 0,
    gate_evaluations: 12,
    reflexes: 9,
    escalations: 3,
    avoided_tokens_estimated: 6750,
    per_arm: [
      {
        arm_id: 2,
        role: 'Backend API Specialist',
        llm_calls: 6,
        tokens_in: 1600,
        tokens_out: 400,
        tokens_total: 2000,
        reflexes: 4,
        escalations: 1,
        avoided_tokens_estimated: 3000,
        is_estimated: false,
      },
      {
        arm_id: 0,
        role: 'System Architect',
        llm_calls: 4,
        tokens_in: 800,
        tokens_out: 200,
        tokens_total: 1000,
        reflexes: 2,
        escalations: 1,
        avoided_tokens_estimated: 1500,
        is_estimated: false,
      },
    ],
    baseline_comparison: {
      task: 'rate_limiter',
      gated_tokens_median: 4120,
      ungated_tokens_median: 8940,
      run_count: 5,
      model: 'qwen2.5-coder:7b',
      label: 'measured in benchmark: gated 4,120 vs ungated 8,940 (median of 5 runs, model qwen2.5-coder:7b)',
    },
    method:
      'Token usage is collected from provider API responses or estimated using character heuristics (ceil(chars/4)). Avoided tokens are estimated as the prompt size that would have been dispatched to the central conductor for each gate evaluation classified as a local reflex.',
    confidence: 'measured',
  };

  beforeEach(() => {
    mockEnv = setupMockEnvironment();

    const container = new MockElement('div');
    container.id = 'token-receipt-modal';
    container.className = 'receipt-modal-backdrop hidden';
    mockEnv.body.appendChild(container);
    mockEnv.doc.registerElement(container);

    panel = new ReceiptPanel('token-receipt-modal');
  });

  it('initializes with accessible modal dialog landmarks', () => {
    const el = mockEnv.doc.getElementById('token-receipt-modal');
    expect(el).not.toBeNull();
    expect(el?.getAttribute('role')).toBe('dialog');
    expect(el?.getAttribute('aria-modal')).toBe('true');
    expect(el?.getAttribute('aria-labelledby')).toBe('receipt-modal-title');
    expect(panel.isOpen()).toBe(false);
  });

  it('renders truthful token numbers and explicit labels upon show()', () => {
    panel.show(mockReceipt);
    expect(panel.isOpen()).toBe(true);

    const el = mockEnv.doc.getElementById('token-receipt-modal');
    expect(el?.textContent).toContain('run-test-1234');
    expect(el?.textContent).toContain('4,000');
    expect(el?.textContent).toContain('measured');
    expect(el?.textContent).toContain('6,750');
    expect(el?.textContent).toContain('estimated avoided');
    expect(el?.textContent).toContain('16');
    expect(el?.textContent).toContain('9 reflexes, 3 escalations');
  });

  it('displays benchmark baseline comparison when present', () => {
    panel.show(mockReceipt);
    const el = mockEnv.doc.getElementById('token-receipt-modal');
    expect(el?.textContent).toContain('BENCHMARK BASELINE');
    expect(el?.textContent).toContain(
      'measured in benchmark: gated 4,120 vs ungated 8,940 (median of 5 runs, model qwen2.5-coder:7b)'
    );
  });

  it('omits benchmark baseline callout when baseline_comparison is null', () => {
    const noBaselineReceipt: ReceiptData = {
      ...mockReceipt,
      baseline_comparison: null,
    };
    panel.show(noBaselineReceipt);
    const el = mockEnv.doc.getElementById('token-receipt-modal');
    expect(el?.textContent).not.toContain('BENCHMARK BASELINE');
  });

  it('renders dry-run receipts with zero provider tokens', () => {
    const dryReceipt: ReceiptData = {
      ...mockReceipt,
      dry_run: true,
      tokens_total: 0,
      confidence: 'measured',
    };
    panel.show(dryReceipt);
    const el = mockEnv.doc.getElementById('token-receipt-modal');
    expect(el?.textContent).toContain('0 provider tokens (dry-run: simulation)');
  });

  it('renders per-arm breakdown table', () => {
    panel.show(mockReceipt);
    const el = mockEnv.doc.getElementById('token-receipt-modal');
    expect(el?.textContent).toContain('[Arm 2]');
    expect(el?.textContent).toContain('Backend API Specialist');
    expect(el?.textContent).toContain('2,000');
    expect(el?.textContent).toContain('[Arm 0]');
    expect(el?.textContent).toContain('System Architect');
    expect(el?.textContent).toContain('1,000');
  });

  it('displays calculation methodology text', () => {
    panel.show(mockReceipt);
    const el = mockEnv.doc.getElementById('token-receipt-modal');
    expect(el?.textContent).toContain('Calculation Methodology:');
    expect(el?.textContent).toContain(
      'Avoided tokens are estimated as the prompt size that would have been dispatched to the central conductor'
    );
  });

  it('closes on Escape key press or hide()', () => {
    panel.show(mockReceipt);
    expect(panel.isOpen()).toBe(true);

    mockEnv.win.dispatchEvent('keydown', { key: 'Escape' });
    expect(panel.isOpen()).toBe(false);
  });
});
