/**
 * Accessible Activity Log and Arm Overview Panel (P6.4).
 *
 * Implements WCAG 2.2 AA non-visual alternative:
 * - Rate-limited live announcement region (role="log", aria-live="polite", <= 1 announcement/sec).
 * - Full semantic table summarizing all 8 arms, roles, statuses, and entropy metrics.
 * - Screen-reader and keyboard accessible; completely readable without WebGL canvas.
 */

import { ARM_A11Y_PROFILES, getArmProfile } from './arm-profiles';

export interface ArmLogEvent {
  octopus_id?: number;
  arm_id?: number;
  role?: string;
  status?: string;
  summary?: string;
  surprise?: number;
  threshold?: number;
  tool_name?: string;
  decision?: 'reflex' | 'escalate';
  timestamp?: number;
}

export interface ArmStateRow {
  id: number;
  name: string;
  code: string;
  symbol: string;
  colorHex: string;
  department: string;
  status: string;
  decision: 'REFLEX' | 'ESCALATE';
  surprise: number;
  threshold: number;
  currentAction: string;
}

export class ActivityLogPanel {
  private container: HTMLElement;
  private logElement!: HTMLElement;
  private tbodyElement!: HTMLElement;
  private toggleButton: HTMLElement | null = null;
  private isVisible: boolean = false;

  // Rate limiter & event batching buffer (<= 1 announcement per second)
  private pendingEvents: ArmLogEvent[] = [];
  private batchIntervalId: number | null = null;
  private armStates: Map<number, ArmStateRow> = new Map();

  constructor(containerId: string = 'activity-log-panel') {
    let el = document.getElementById(containerId);
    if (!el) {
      el = document.createElement('section');
      el.id = containerId;
      document.body.appendChild(el);
    }
    this.container = el;
    this.initArmStates();
    this.render();
    this.startRateLimiter();
  }

  private initArmStates(): void {
    for (const p of ARM_A11Y_PROFILES) {
      this.armStates.set(p.id, {
        id: p.id,
        name: p.name,
        code: p.code,
        symbol: p.symbol,
        colorHex: p.colorHex,
        department: p.department,
        status: 'IDLE',
        decision: 'REFLEX',
        surprise: 0.05,
        threshold: 0.35,
        currentAction: 'Quiescent - awaiting mission task',
      });
    }
  }

  private render(): void {
    this.container.className = 'glass-panel activity-log-drawer';
    this.container.setAttribute('role', 'region');
    this.container.setAttribute('aria-label', 'Swarm Activity and Arm Status');
    this.container.style.display = this.isVisible ? 'flex' : 'none';

    this.container.innerHTML = `
      <div class="activity-header">
        <div class="activity-title-wrap">
          <div class="activity-badge">ACCESSIBLE TEXT TELEMETRY</div>
          <h2 class="activity-title">SWARM ACTIVITY & ARM STATUS</h2>
          <p class="activity-subtitle">Real-time non-visual stream of autonomous agent actions, entropy decisions, and state ledger.</p>
        </div>
        <button id="btn-close-activity-log" class="btn-activity-close" aria-label="Close activity log panel">
          &times;
        </button>
      </div>

      <div class="activity-body">
        <!-- 1. Semantic Overview Table -->
        <div class="activity-table-section">
          <h3 class="activity-section-heading">8-Arm Swarm Consortium Overview</h3>
          <div class="activity-table-wrapper" tabindex="0" role="region" aria-label="Scrollable Arm Status Table">
            <table class="arm-status-table">
              <caption class="sr-only">Detailed status and entropy decisions across all 8 cephalopod arms</caption>
              <thead>
                <tr>
                  <th scope="col">Arm / ID</th>
                  <th scope="col">Symbol</th>
                  <th scope="col">Code</th>
                  <th scope="col">Role & Department</th>
                  <th scope="col">Status</th>
                  <th scope="col">Decision</th>
                  <th scope="col">Entropy (dS / θ)</th>
                  <th scope="col">Active Action / Tool</th>
                </tr>
              </thead>
              <tbody id="arm-status-tbody">
              </tbody>
            </table>
          </div>
        </div>

        <!-- 2. Rate-limited Live Announcement Stream -->
        <div class="activity-feed-section">
          <div class="feed-header">
            <h3 class="activity-section-heading">Live Autonomous Action Log</h3>
            <span class="feed-rate-pill">Rate: &le; 1 msg/sec (Batched)</span>
          </div>
          <div
            id="activity-log-feed"
            class="activity-log-feed"
            role="log"
            aria-live="polite"
            aria-atomic="false"
            tabindex="0"
            aria-label="Real-time swarm activity log"
          >
            <div class="log-entry initial-entry">
              <span class="log-time">[INIT]</span>
              <span class="log-text">Telemetry monitor engaged. Waiting for swarm activation events...</span>
            </div>
          </div>
        </div>
      </div>
    `;

    this.logElement = this.container.querySelector('#activity-log-feed') as HTMLElement;
    this.tbodyElement = this.container.querySelector('#arm-status-tbody') as HTMLElement;

    const closeBtn = this.container.querySelector('#btn-close-activity-log');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hide());
    }

    this.renderTableRows();
  }

  private renderTableRows(): void {
    if (!this.tbodyElement) return;
    let html = '';
    for (const p of ARM_A11Y_PROFILES) {
      const state = this.armStates.get(p.id)!;
      const isReflex = state.decision === 'REFLEX';
      const decClass = isReflex ? 'decision-reflex' : 'decision-escalate';
      html += `
        <tr id="arm-row-${p.id}">
          <td class="col-arm-id" style="color: ${p.colorHex}; font-weight: 700;">
            Arm ${p.id}
          </td>
          <td class="col-symbol" style="color: ${p.colorHex}; font-size: 14px;" aria-label="Shape ${p.symbolName}">
            ${p.symbol}
          </td>
          <td class="col-code">
            <span class="arm-code-badge" style="border-color: ${p.colorHex}; color: ${p.colorHex};">
              ${p.code}
            </span>
          </td>
          <td class="col-role">
            <div class="role-name">${p.name}</div>
            <div class="role-dept">${p.department}</div>
          </td>
          <td class="col-status">
            <span class="status-pill status-${state.status.toLowerCase()}">${state.status}</span>
          </td>
          <td class="col-decision">
            <span class="decision-pill ${decClass}">${state.decision}</span>
          </td>
          <td class="col-entropy">
            <span class="entropy-val">dS: ${state.surprise.toFixed(2)}</span>
            <span class="entropy-delim">/</span>
            <span class="threshold-val">&theta;: ${state.threshold.toFixed(2)}</span>
          </td>
          <td class="col-action" title="${state.currentAction}">
            ${state.currentAction}
          </td>
        </tr>
      `;
    }
    this.tbodyElement.innerHTML = html;
  }

  /**
   * Enqueue incoming telemetry event for batched rate-limited announcement.
   */
  public recordEvent(evt: ArmLogEvent): void {
    const armId = evt.arm_id ?? evt.octopus_id ?? 0;

    // Compute decision based on surprise vs threshold if not explicitly supplied
    const surprise = evt.surprise ?? 0.05;
    const threshold = evt.threshold ?? 0.35;
    const decision: 'REFLEX' | 'ESCALATE' =
      evt.decision?.toUpperCase() === 'ESCALATE' || surprise > threshold
        ? 'ESCALATE'
        : 'REFLEX';

    // Update active table state
    const current = this.armStates.get(armId);
    if (current) {
      current.status = evt.status || current.status;
      current.decision = decision;
      current.surprise = surprise;
      current.threshold = threshold;
      current.currentAction = evt.tool_name
        ? `Tool: ${evt.tool_name}`
        : evt.summary || current.currentAction;
      this.updateTableRow(armId, current);
    }

    // Queue for rate-limited announcement
    this.pendingEvents.push({
      ...evt,
      arm_id: armId,
      decision: decision.toLowerCase() as 'reflex' | 'escalate',
      surprise,
      threshold,
      timestamp: evt.timestamp ?? Date.now(),
    });
  }

  private updateTableRow(armId: number, state: ArmStateRow): void {
    const row = document.getElementById(`arm-row-${armId}`);
    if (!row) return;

    const statusEl = row.querySelector('.col-status');
    if (statusEl) {
      statusEl.innerHTML = `<span class="status-pill status-${state.status.toLowerCase()}">${state.status}</span>`;
    }

    const decEl = row.querySelector('.col-decision');
    if (decEl) {
      const decClass = state.decision === 'REFLEX' ? 'decision-reflex' : 'decision-escalate';
      decEl.innerHTML = `<span class="decision-pill ${decClass}">${state.decision}</span>`;
    }

    const entEl = row.querySelector('.col-entropy');
    if (entEl) {
      entEl.innerHTML = `
        <span class="entropy-val">dS: ${state.surprise.toFixed(2)}</span>
        <span class="entropy-delim">/</span>
        <span class="threshold-val">&theta;: ${state.threshold.toFixed(2)}</span>
      `;
    }

    const actionEl = row.querySelector('.col-action');
    if (actionEl) {
      actionEl.textContent = state.currentAction;
      actionEl.setAttribute('title', state.currentAction);
    }
  }

  /**
   * Flush queued events once every second to avoid flooding screen readers.
   */
  public flushBatch(): void {
    if (this.pendingEvents.length === 0) return;

    const batch = [...this.pendingEvents];
    this.pendingEvents = [];

    // If multiple events arrived in the 1-second window, batch them cleanly
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];

    const lines: string[] = batch.map((ev) => {
      const arm = getArmProfile(ev.arm_id ?? 0);
      const decStr = ev.decision === 'escalate' ? 'ESCALATE' : 'REFLEX';
      const surprise = (ev.surprise ?? 0).toFixed(2);
      const threshold = (ev.threshold ?? 0.35).toFixed(2);
      const action = ev.tool_name ? `Tool: ${ev.tool_name}` : ev.summary || 'Working';
      return `${arm.symbol} [${arm.code}] Arm ${arm.id} (${arm.name}): ${decStr} (dS: ${surprise} vs θ: ${threshold}) - ${action}`;
    });

    const entryDiv = document.createElement('div');
    entryDiv.className = 'log-entry';

    if (lines.length === 1) {
      entryDiv.innerHTML = `
        <span class="log-time">[${timeStr}]</span>
        <span class="log-text">${this.escapeHtml(lines[0])}</span>
      `;
    } else {
      entryDiv.innerHTML = `
        <span class="log-time">[${timeStr}]</span>
        <span class="log-batch-tag">BATCH (${lines.length} events)</span>
        <div class="log-batch-content">
          ${lines.map((l) => `<div class="batch-line">${this.escapeHtml(l)}</div>`).join('')}
        </div>
      `;
    }

    if (this.logElement) {
      this.logElement.insertBefore(entryDiv, this.logElement.firstChild);
      // Cap log length to 50 items
      while (this.logElement.children.length > 50) {
        this.logElement.removeChild(this.logElement.lastChild!);
      }
    }
  }

  private startRateLimiter(): void {
    if (this.batchIntervalId !== null) return;
    this.batchIntervalId = window.setInterval(() => {
      this.flushBatch();
    }, 1000);
  }

  public stopRateLimiter(): void {
    if (this.batchIntervalId !== null) {
      clearInterval(this.batchIntervalId);
      this.batchIntervalId = null;
    }
  }

  public bindToggleButton(btn: HTMLElement): void {
    this.toggleButton = btn;
    btn.setAttribute('aria-expanded', String(this.isVisible));
    btn.setAttribute('aria-controls', this.container.id);
    btn.addEventListener('click', () => this.toggle());
  }

  public toggle(): boolean {
    if (this.isVisible) {
      this.hide();
    } else {
      this.show();
    }
    return this.isVisible;
  }

  public show(): void {
    this.isVisible = true;
    this.container.style.display = 'flex';
    this.container.classList.add('visible');
    if (this.toggleButton) {
      this.toggleButton.setAttribute('aria-expanded', 'true');
      this.toggleButton.classList.add('active');
    }
    // Focus close button for keyboard users
    const closeBtn = this.container.querySelector('#btn-close-activity-log') as HTMLElement;
    closeBtn?.focus();
  }

  public hide(): void {
    this.isVisible = false;
    this.container.style.display = 'none';
    this.container.classList.remove('visible');
    if (this.toggleButton) {
      this.toggleButton.setAttribute('aria-expanded', 'false');
      this.toggleButton.classList.remove('active');
      this.toggleButton.focus();
    }
  }

  public isOpen(): boolean {
    return this.isVisible;
  }

  public getPendingEventsCount(): number {
    return this.pendingEvents.length;
  }

  public getArmState(armId: number): ArmStateRow | undefined {
    return this.armStates.get(armId);
  }

  private escapeHtml(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
}
