/**
 * Token Receipt Modal & Summary Panel (P7.1).
 *
 * Displays a truthful, transparent accounting of token expenditures,
 * estimated tokens avoided via event-triggered sensory surprise gating,
 * empirical benchmark baseline linkages, and per-arm allocations.
 * Fully keyboard and screen-reader accessible (WCAG 2.2 AA).
 */

export interface ArmReceiptItem {
  arm_id: number;
  role: string;
  llm_calls: number;
  tokens_in: number;
  tokens_out: number;
  tokens_total: number;
  reflexes: number;
  escalations: number;
  avoided_tokens_estimated: number;
  is_estimated: boolean;
}

export interface BaselineComparisonItem {
  task: string;
  gated_tokens_median: number;
  ungated_tokens_median: number;
  run_count: number;
  model: string;
  label: string;
}

export interface ReceiptData {
  run_id: string;
  mode?: string;
  provider?: string;
  model?: string;
  duration_seconds?: number;
  dry_run?: boolean;
  llm_calls: number;
  tokens_in: number;
  tokens_out: number;
  tokens_total: number;
  tokens_measured?: number;
  tokens_estimated?: number;
  gate_evaluations: number;
  reflexes: number;
  escalations: number;
  avoided_tokens_estimated: number;
  per_arm?: ArmReceiptItem[];
  baseline_comparison?: BaselineComparisonItem | null;
  method?: string;
  confidence?: string;
}

export class ReceiptPanel {
  private container: HTMLElement;
  private currentReceipt: ReceiptData | null = null;
  private isVisible: boolean = false;
  private previouslyFocusedElement: HTMLElement | null = null;

  constructor(containerId: string = 'token-receipt-modal') {
    let el = document.getElementById(containerId);
    if (!el) {
      el = document.createElement('div');
      el.id = containerId;
      document.body.appendChild(el);
    }
    el.className = 'receipt-modal-backdrop hidden';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-labelledby', 'receipt-modal-title');
    this.container = el;
    this.bindEvents();
  }

  private bindEvents(): void {
    if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
      window.addEventListener('keydown', (e: KeyboardEvent) => {
        if (e.key === 'Escape' && this.isVisible) {
          this.hide();
        }
      });
    }

    if (this.container && typeof this.container.addEventListener === 'function') {
      this.container.addEventListener('click', (e: MouseEvent) => {
        if (e.target === this.container) {
          this.hide();
        }
      });
    }
  }

  public show(receipt: ReceiptData): void {
    this.currentReceipt = receipt;
    this.previouslyFocusedElement = document.activeElement as HTMLElement | null;
    this.render();
    this.container.classList.remove('hidden');
    this.isVisible = true;

    const closeBtn = this.container.querySelector<HTMLButtonElement>('#btn-close-receipt');
    if (closeBtn) {
      closeBtn.focus();
    }
  }

  public hide(): void {
    this.container.classList.add('hidden');
    this.isVisible = false;
    if (this.previouslyFocusedElement && typeof this.previouslyFocusedElement.focus === 'function') {
      this.previouslyFocusedElement.focus();
    }
  }

  public isOpen(): boolean {
    return this.isVisible;
  }

  public getReceipt(): ReceiptData | null {
    return this.currentReceipt;
  }

  public render(): void {
    if (!this.currentReceipt) return;

    const r = this.currentReceipt;
    const isDry = Boolean(r.dry_run);
    const spentLabel = isDry
      ? '0 provider tokens (dry-run: simulation)'
      : `${(r.tokens_total || 0).toLocaleString()} tokens (${r.confidence || 'estimated'})`;
    const avoidedLabel = `${(r.avoided_tokens_estimated || 0).toLocaleString()} tokens (estimated avoided)`;

    const arms = r.per_arm || [];
    const sortedArms = [...arms].sort((a, b) => b.tokens_total - a.tokens_total);

    const rowsHtml = sortedArms
      .map(
        (a) => `
        <tr>
          <td><span class="arm-code">[Arm ${a.arm_id}]</span> ${a.role}</td>
          <td class="text-right font-mono">${(a.tokens_total || 0).toLocaleString()}</td>
          <td class="text-right font-mono">${a.llm_calls || 0}</td>
          <td class="text-right font-mono">${a.reflexes || 0} / ${a.escalations || 0}</td>
          <td class="text-right font-mono">${(a.avoided_tokens_estimated || 0).toLocaleString()}</td>
        </tr>
      `
      )
      .join('');

    const baselineHtml = r.baseline_comparison
      ? `
      <div class="receipt-baseline-callout">
        <span class="baseline-tag">BENCHMARK BASELINE</span>
        <span class="baseline-text">${r.baseline_comparison.label}</span>
      </div>
    `
      : '';

    this.container.innerHTML = `
      <div class="receipt-card glass-panel" role="document">
        <div class="receipt-header">
          <div>
            <div class="receipt-badge">TRUTHFUL TOKEN RECEIPT</div>
            <h2 id="receipt-modal-title" class="receipt-title">Run: ${r.run_id}</h2>
            <div class="receipt-meta">
              <span>Mode: <code>${r.mode || 'software_dev'}</code></span>
              <span>Provider: <code>${r.provider || 'mock'}:${r.model || 'default'}</code></span>
              <span>Duration: <strong>${r.duration_seconds || 0}s</strong></span>
            </div>
          </div>
          <button id="btn-close-receipt" class="btn-receipt-close" aria-label="Close Token Receipt">✕</button>
        </div>

        <div class="receipt-metrics-grid">
          <div class="metric-card">
            <div class="metric-label">Tokens Spent (${r.confidence || 'estimated'})</div>
            <div class="metric-value spent-value">${isDry ? '0' : (r.tokens_total || 0).toLocaleString()}</div>
            <div class="metric-sub">${spentLabel}</div>
          </div>

          <div class="metric-card">
            <div class="metric-label">Estimated Avoided Tokens</div>
            <div class="metric-value avoided-value">${(r.avoided_tokens_estimated || 0).toLocaleString()}</div>
            <div class="metric-sub">${avoidedLabel}</div>
          </div>

          <div class="metric-card">
            <div class="metric-label">LLM Calls & Gate</div>
            <div class="metric-value">${r.llm_calls || 0}</div>
            <div class="metric-sub">${r.gate_evaluations || 0} gate evals (${r.reflexes || 0} reflexes, ${r.escalations || 0} escalations)</div>
          </div>
        </div>

        ${baselineHtml}

        ${
          arms.length > 0
            ? `
          <div class="receipt-table-wrapper">
            <h3 class="table-heading">Arm Allocations & Gate Decisions</h3>
            <table class="receipt-table">
              <thead>
                <tr>
                  <th scope="col">Specialist Arm</th>
                  <th scope="col" class="text-right">Tokens Total</th>
                  <th scope="col" class="text-right">Calls</th>
                  <th scope="col" class="text-right">Reflex / Escalate</th>
                  <th scope="col" class="text-right">Avoided (est)</th>
                </tr>
              </thead>
              <tbody>
                ${rowsHtml}
              </tbody>
            </table>
          </div>
        `
            : ''
        }

        <div class="receipt-methodology-note">
          <div class="method-title">Calculation Methodology:</div>
          <p class="method-text">${r.method || 'Token usage is collected from provider API responses or estimated using character heuristics (ceil(chars/4)). Avoided tokens are estimated as the prompt size that would have been dispatched to the central conductor for each gate evaluation classified as a local reflex.'}</p>
        </div>
      </div>
    `;

    const closeBtn = this.container.querySelector('#btn-close-receipt');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hide());
    }
  }
}

