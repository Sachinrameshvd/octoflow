/**
 * Unit Tests for Activity Log Panel, Rate Limiter & Semantic Table (P6.4).
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { setupMockEnvironment, MockElement } from './test-dom';
import { ActivityLogPanel } from './activity-log-panel';
import { ARM_A11Y_PROFILES } from './arm-profiles';

describe('ActivityLogPanel Non-Visual Alternative', () => {
  let mockEnv: ReturnType<typeof setupMockEnvironment>;
  let panel: ActivityLogPanel;

  beforeEach(() => {
    vi.useFakeTimers();
    mockEnv = setupMockEnvironment();

    const container = new MockElement('section');
    container.id = 'test-container';
    mockEnv.body.appendChild(container);
    mockEnv.doc.registerElement(container);

    panel = new ActivityLogPanel('test-container');
  });

  afterEach(() => {
    panel.stopRateLimiter();
    vi.useRealTimers();
  });

  it('initializes with semantic table containing all 8 cephalopod arms', () => {
    for (const p of ARM_A11Y_PROFILES) {
      const row = mockEnv.doc.getElementById(`arm-row-${p.id}`);
      expect(row).not.toBeNull();
      expect(row?.textContent).toContain(`Arm ${p.id}`);
      expect(row?.textContent).toContain(p.code);
      expect(row?.textContent).toContain(p.symbol);
      expect(row?.textContent).toContain(p.name);
    }
  });

  it('has proper accessibility landmarks and attributes', () => {
    const container = mockEnv.doc.getElementById('test-container');
    expect(container?.getAttribute('role')).toBe('region');
    expect(container?.getAttribute('aria-label')).toBe('Swarm Activity and Arm Status');

    const feed = mockEnv.doc.getElementById('activity-log-feed');
    expect(feed?.getAttribute('role')).toBe('log');
    expect(feed?.getAttribute('aria-live')).toBe('polite');
    expect(feed?.getAttribute('aria-atomic')).toBe('false');
  });

  it('rate-limits incoming telemetry: batches events and flushes at most once per second', () => {
    const feed = mockEnv.doc.getElementById('activity-log-feed')!;
    const initialCount = feed.querySelectorAll('.log-entry').length;

    // Enqueue 4 rapid events
    panel.recordEvent({
      arm_id: 0,
      summary: 'Analyzing codebase AST',
      surprise: 0.1,
      threshold: 0.35,
    });
    panel.recordEvent({
      arm_id: 2,
      summary: 'Updating database schema',
      tool_name: 'sql_migrate',
      surprise: 0.12,
      threshold: 0.35,
    });
    panel.recordEvent({
      arm_id: 5,
      summary: 'Vulnerability audit detected potential bypass',
      decision: 'escalate',
      surprise: 0.48,
      threshold: 0.35,
    });
    panel.recordEvent({
      arm_id: 7,
      summary: 'Executing container healthcheck',
      tool_name: 'docker_ps',
      surprise: 0.05,
      threshold: 0.35,
    });

    // Before timer advances: events are buffered, NOT spammed into live region
    expect(feed.querySelectorAll('.log-entry').length).toBe(initialCount);
    expect(panel.getPendingEventsCount()).toBe(4);

    // Advance timer by 1000ms
    vi.advanceTimersByTime(1000);

    // Exactly 1 new batch entry should be emitted in the feed
    const entries = feed.querySelectorAll('.log-entry');
    expect(entries.length).toBe(initialCount + 1);

    const latestEntry = entries[0].innerHTML || '';
    expect(latestEntry).toContain('BATCH (4 events)');
    expect(latestEntry).toContain('[ARC] Arm 0');
    expect(latestEntry).toContain('REFLEX');
    expect(latestEntry).toContain('Tool: sql_migrate');
    expect(latestEntry).toContain('ESCALATE');
    expect(latestEntry).toContain('Tool: docker_ps');
    expect(panel.getPendingEventsCount()).toBe(0);
  });

  it('updates semantic table row metrics and status badges upon telemetry event', () => {
    panel.recordEvent({
      arm_id: 2,
      status: 'ACTIVE',
      tool_name: 'pytest_runner',
      decision: 'reflex',
      surprise: 0.14,
      threshold: 0.35,
    });

    const arm2State = panel.getArmState(2);
    expect(arm2State?.status).toBe('ACTIVE');
    expect(arm2State?.decision).toBe('REFLEX');
    expect(arm2State?.surprise).toBe(0.14);
    expect(arm2State?.currentAction).toContain('pytest_runner');

    const row = mockEnv.doc.getElementById('arm-row-2')!;
    expect(row.textContent).toContain('ACTIVE');
    expect(row.textContent).toContain('REFLEX');
    expect(row.textContent).toContain('0.14');
    expect(row.textContent).toContain('pytest_runner');
  });

  it('correctly classifies ESCALATE when surprise exceeds threshold', () => {
    panel.recordEvent({
      arm_id: 4,
      status: 'ESCALATING',
      surprise: 0.62,
      threshold: 0.35,
      summary: 'Surprise threshold breach on test failure',
    });

    const arm4State = panel.getArmState(4);
    expect(arm4State?.decision).toBe('ESCALATE');

    const row = mockEnv.doc.getElementById('arm-row-4')!;
    expect(row.textContent).toContain('ESCALATE');
    expect(row.textContent).toContain('0.62');
  });

  it('supports toggle, show, and hide states with accessible aria-expanded attributes', () => {
    const toggleBtn = new MockElement('button');
    panel.bindToggleButton(toggleBtn as any);

    expect(toggleBtn.getAttribute('aria-expanded')).toBe('false');
    expect(panel.isOpen()).toBe(false);

    panel.show();
    expect(panel.isOpen()).toBe(true);
    expect(toggleBtn.getAttribute('aria-expanded')).toBe('true');

    panel.hide();
    expect(panel.isOpen()).toBe(false);
    expect(toggleBtn.getAttribute('aria-expanded')).toBe('false');
  });
});
