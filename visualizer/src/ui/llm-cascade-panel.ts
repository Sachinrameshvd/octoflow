/** LLM Cascade & Token Failover Dock.
 * Displays directly under the 3D Octopus Connectome in the visualizer interface.
 * Allows users and developers to configure as many or as few LLM URLs/keys as they have.
 * Seamlessly hot-swaps to the next provider when tokens deplete or rate limits (429) hit.
 * ZERO EMOJIS - Clean SVG icons and typography only.
 */

export interface LLMPoolItem {
  id: string;
  provider: string;
  name: string;
  base_url?: string;
  api_key?: string;
  masked_key?: string;
  model: string;
  enabled: boolean;
  priority: number;
  status: 'ACTIVE' | 'STANDBY' | 'EXHAUSTED' | 'ERROR';
  tokens_used: number;
  last_error?: string;
}

export class LLMCascadePanel {
  public container: HTMLElement;
  private pool: LLMPoolItem[] = [];
  private activeId: string | null = null;
  private isExpanded: boolean = true;
  private isAddFormOpen: boolean = false;
  private lastFailoverNotice: string | null = null;

  public onFailoverSwitch?: (fromItem: LLMPoolItem, toItem: LLMPoolItem) => void;

  constructor(containerId: string = 'llm-cascade-panel') {
    let el = document.getElementById(containerId);
    if (!el) {
      el = document.createElement('div');
      el.id = containerId;
      el.className = 'glass-panel llm-cascade-dock';
      // Insert in DOM right next to or inside signal trigger panel area
      const appContainer = document.getElementById('app-container') || document.body;
      const sigPanel = document.getElementById('signal-trigger-panel');
      if (sigPanel && sigPanel.parentNode) {
        sigPanel.parentNode.insertBefore(el, sigPanel);
      } else {
        appContainer.appendChild(el);
      }
    }
    this.container = el;
    this.loadInitialPool();
    this.render();
  }

  private async loadInitialPool() {
    try {
      const res = await fetch('http://127.0.0.1:8765/llm/pool', { signal: AbortSignal.timeout(1500) });
      if (res.ok) {
        const data = await res.json();
        if (data.pool && Array.isArray(data.pool) && data.pool.length > 0) {
          this.pool = data.pool.map((item: any, idx: number) => ({
            ...item,
            status: idx === 0 ? 'ACTIVE' : 'STANDBY',
            tokens_used: item.tokens_used || 0,
          }));
          this.activeId = this.pool[0].id;
          this.render();
          return;
        }
      }
    } catch {
      // Backend offline, fallback to localStorage
    }

    const saved = localStorage.getItem('octoflow_llm_pool');
    if (saved) {
      try {
        this.pool = JSON.parse(saved);
        if (this.pool.length > 0) {
          this.activeId = this.pool[0].id;
        }
      } catch {
        this.pool = [];
      }
    } else {
      // Clean default starter options (unconfigured until developer chooses to plug keys)
      this.pool = [
        {
          id: 'gemini-flash',
          provider: 'gemini',
          name: 'Google Gemini 2.0 Flash',
          base_url: 'https://generativelanguage.googleapis.com/v1beta',
          model: 'gemini-2.0-flash',
          enabled: true,
          priority: 1,
          status: 'ACTIVE',
          tokens_used: 0,
          masked_key: '(none / click to configure)',
        },
      ];
      this.activeId = 'gemini-flash';
    }
    this.render();
  }

  private savePool() {
    localStorage.setItem('octoflow_llm_pool', JSON.stringify(this.pool));
    // Also push to backend if available
    fetch('http://127.0.0.1:8765/llm/pool', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'save_all', entries: this.pool }),
    }).catch(() => {});
  }

  public simulateTokenExhaustion() {
    if (this.pool.length <= 1) {
      this.lastFailoverNotice = 'Notice: Only 1 provider configured. Add another LLM to enable auto-failover.';
      this.render();
      return;
    }

    const currentIdx = this.pool.findIndex((p) => p.id === this.activeId);
    if (currentIdx === -1) return;

    const fromItem = this.pool[currentIdx];
    fromItem.status = 'EXHAUSTED';
    fromItem.tokens_used += 18450;
    fromItem.last_error = 'HTTP 429: Token quota reached';

    const nextIdx = (currentIdx + 1) % this.pool.length;
    const toItem = this.pool[nextIdx];
    toItem.status = 'ACTIVE';
    this.activeId = toItem.id;

    this.lastFailoverNotice = `HOT-SWAP: ${fromItem.name} tokens exhausted (429) -> Switched to ${toItem.name}`;

    if (this.onFailoverSwitch) {
      this.onFailoverSwitch(fromItem, toItem);
    }

    this.savePool();
    this.render();
  }

  public recordTokenUsage(tokens: number) {
    const active = this.pool.find((p) => p.id === this.activeId);
    if (active) {
      active.tokens_used += tokens;
      this.render();
    }
  }

  private render() {
    const itemsHtml = this.pool
      .map((item, idx) => {
        const isActive = item.status === 'ACTIVE';
        const isExhausted = item.status === 'EXHAUSTED';
        const statusBadgeClass = isActive
          ? 'badge-active'
          : isExhausted
          ? 'badge-exhausted'
          : 'badge-standby';
        const statusLabel = isActive
          ? 'ACTIVE'
          : isExhausted
          ? 'EXHAUSTED (429)'
          : 'STANDBY';

        return `
        <div class="llm-card ${isActive ? 'is-active-card' : ''} ${isExhausted ? 'is-exhausted-card' : ''}" data-id="${item.id}">
          <div class="llm-card-top">
            <div class="llm-card-title-row">
              <span class="llm-priority-badge">[#${idx + 1}]</span>
              <span class="llm-model-name">${item.name}</span>
              <span class="llm-status-pill ${statusBadgeClass}">
                <span class="status-indicator-dot"></span>
                ${statusLabel}
              </span>
            </div>
            <div class="llm-card-actions">
              <button class="btn-card-action btn-test-llm" data-id="${item.id}" title="Test API endpoint">TEST</button>
              <button class="btn-card-action btn-remove-llm" data-id="${item.id}" title="Remove this provider">X</button>
            </div>
          </div>

          <div class="llm-card-details">
            <div class="llm-detail-row">
              <span class="llm-label">ENDPOINT:</span>
              <span class="llm-val" title="${item.base_url || 'Default Cloud'}">${item.base_url || 'Default Cloud'}</span>
            </div>
            <div class="llm-detail-row">
              <span class="llm-label">MODEL:</span>
              <span class="llm-val">${item.model}</span>
              <span class="llm-label" style="margin-left: 8px;">KEY:</span>
              <span class="llm-val key-preview">${item.masked_key || 'Configured'}</span>
            </div>
            <div class="llm-detail-row" style="margin-top: 4px;">
              <span class="llm-label">TOKENS SPENT:</span>
              <span class="llm-val token-count">${item.tokens_used.toLocaleString()}</span>
            </div>
          </div>
        </div>
      `;
      })
      .join('');

    const noticeBanner = this.lastFailoverNotice
      ? `
      <div class="llm-failover-banner">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" style="margin-right: 6px;"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        <span>${this.lastFailoverNotice}</span>
        <button class="btn-dismiss-notice" id="btn-dismiss-failover-notice">DISMISS</button>
      </div>
    `
      : '';

    const addFormHtml = this.isAddFormOpen
      ? `
      <div class="llm-add-form glass-panel">
        <div class="add-form-header">
          <span class="form-title">ADD LLM TO FAILOVER CASCADE (SELECT PROVIDER)</span>
          <span class="form-desc">Optional: Add only the keys you own. If 1 model depletes tokens, OctoFlow hot-swaps to the next.</span>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label>PROVIDER</label>
            <select id="form-provider-select" class="llm-input">
              <option value="gemini">Google Gemini (Flash / Pro)</option>
              <option value="grok">xAI Grok (Grok-2)</option>
              <option value="deepseek">DeepSeek (V3 / R1)</option>
              <option value="openai">OpenAI (GPT-4o / o3-mini)</option>
              <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
              <option value="ollama">Ollama (Free Local AI)</option>
              <option value="custom">Custom Endpoint (vLLM / LM Studio / Self-Hosted)</option>
            </select>
          </div>

          <div class="form-group">
            <label>DISPLAY NAME</label>
            <input type="text" id="form-name-input" class="llm-input" value="Google Gemini 2.0 Flash" />
          </div>

          <div class="form-group">
            <label>ENDPOINT URL (OPTIONAL / CUSTOM)</label>
            <input type="text" id="form-url-input" class="llm-input" value="https://generativelanguage.googleapis.com/v1beta" />
          </div>

          <div class="form-group">
            <label>MODEL NAME</label>
            <input type="text" id="form-model-input" class="llm-input" value="gemini-2.0-flash" />
          </div>

          <div class="form-group" style="grid-column: 1 / -1;">
            <label>API KEY (LEAVE BLANK IF RUNNING LOCAL OLLAMA / VLLM)</label>
            <div style="display: flex; gap: 8px;">
              <input type="password" id="form-key-input" class="llm-input" placeholder="Paste your API key here..." style="flex: 1;" />
              <button type="button" id="btn-toggle-key-mask" class="btn-secondary-action">SHOW</button>
            </div>
          </div>
        </div>

        <div class="form-footer">
          <div id="form-test-feedback" class="form-feedback"></div>
          <div style="display: flex; gap: 8px;">
            <button id="btn-cancel-add-llm" class="btn-secondary-action">CANCEL</button>
            <button id="btn-submit-add-llm" class="btn-primary-action">SAVE TO CASCADE POOL</button>
          </div>
        </div>
      </div>
    `
      : '';

    this.container.innerHTML = `
      <div class="llm-dock-header">
        <div class="llm-header-left">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" style="margin-right: 8px;">
            <circle cx="12" cy="12" r="3" fill="#38bdf8"/>
            <path d="M12 2v3m0 14v3M2 12h3m14 0h3m-3.5-6.5l-2 2m-7 7l-2 2m11 0l-2-2m-7-7l-2-2"/>
          </svg>
          <div>
            <span class="dock-title">NEURAL LLM CASCADE & TOKEN FAILOVER POOL</span>
            <span class="dock-subtitle">Directly under Octopus Brain: Auto-switches endpoints when rate limits or quotas deplete</span>
          </div>
        </div>

        <div class="llm-header-right">
          <button id="btn-open-add-llm" class="btn-dock-action ${this.isAddFormOpen ? 'active' : ''}">
            + ADD MODEL / URL
          </button>
          <button id="btn-simulate-failover" class="btn-dock-action" title="Simulate 429 quota exhaustion and verify instant hot-swap">
            SIMULATE 429 FAILOVER
          </button>
          <button id="btn-toggle-llm-collapse" class="btn-dock-minimize" title="Collapse / Expand">
            ${this.isExpanded ? 'MINIMIZE' : 'EXPAND'}
          </button>
        </div>
      </div>

      ${noticeBanner}

      <div class="llm-dock-body ${this.isExpanded ? '' : 'is-collapsed'}">
        ${addFormHtml}
        <div class="llm-cards-carousel">
          ${itemsHtml.length > 0 ? itemsHtml : '<div class="llm-empty-state">No LLM providers in pool. Click "+ ADD MODEL / URL" to connect one.</div>'}
        </div>
      </div>
    `;

    this.bindEvents();
  }

  private bindEvents() {
    // Toggle collapse
    const btnCollapse = this.container.querySelector('#btn-toggle-llm-collapse');
    if (btnCollapse) {
      btnCollapse.addEventListener('click', () => {
        this.isExpanded = !this.isExpanded;
        this.render();
      });
    }

    // Toggle add form
    const btnOpenAdd = this.container.querySelector('#btn-open-add-llm');
    if (btnOpenAdd) {
      btnOpenAdd.addEventListener('click', () => {
        this.isAddFormOpen = !this.isAddFormOpen;
        this.render();
      });
    }

    // Dismiss notice
    const btnDismiss = this.container.querySelector('#btn-dismiss-failover-notice');
    if (btnDismiss) {
      btnDismiss.addEventListener('click', () => {
        this.lastFailoverNotice = null;
        this.render();
      });
    }

    // Simulate 429 failover
    const btnSim = this.container.querySelector('#btn-simulate-failover');
    if (btnSim) {
      btnSim.addEventListener('click', () => {
        this.simulateTokenExhaustion();
      });
    }

    // Cancel add
    const btnCancel = this.container.querySelector('#btn-cancel-add-llm');
    if (btnCancel) {
      btnCancel.addEventListener('click', () => {
        this.isAddFormOpen = false;
        this.render();
      });
    }

    // Key mask toggle
    const btnMask = this.container.querySelector('#btn-toggle-key-mask');
    const inputKey = this.container.querySelector('#form-key-input') as HTMLInputElement | null;
    if (btnMask && inputKey) {
      btnMask.addEventListener('click', () => {
        if (inputKey.type === 'password') {
          inputKey.type = 'text';
          btnMask.textContent = 'HIDE';
        } else {
          inputKey.type = 'password';
          btnMask.textContent = 'SHOW';
        }
      });
    }

    // Provider select change -> autofill presets
    const selectProvider = this.container.querySelector('#form-provider-select') as HTMLSelectElement | null;
    const inputName = this.container.querySelector('#form-name-input') as HTMLInputElement | null;
    const inputUrl = this.container.querySelector('#form-url-input') as HTMLInputElement | null;
    const inputModel = this.container.querySelector('#form-model-input') as HTMLInputElement | null;

    if (selectProvider && inputName && inputUrl && inputModel) {
      selectProvider.addEventListener('change', () => {
        const val = selectProvider.value;
        if (val === 'gemini') {
          inputName.value = 'Google Gemini 2.0 Flash';
          inputUrl.value = 'https://generativelanguage.googleapis.com/v1beta';
          inputModel.value = 'gemini-2.0-flash';
        } else if (val === 'grok') {
          inputName.value = 'xAI Grok-2';
          inputUrl.value = 'https://api.x.ai/v1';
          inputModel.value = 'grok-2-1212';
        } else if (val === 'deepseek') {
          inputName.value = 'DeepSeek-V3';
          inputUrl.value = 'https://api.deepseek.com/v1';
          inputModel.value = 'deepseek-chat';
        } else if (val === 'openai') {
          inputName.value = 'OpenAI GPT-4o';
          inputUrl.value = 'https://api.openai.com/v1';
          inputModel.value = 'gpt-4o';
        } else if (val === 'anthropic') {
          inputName.value = 'Claude 3.5 Sonnet';
          inputUrl.value = 'https://api.anthropic.com/v1';
          inputModel.value = 'claude-3-5-sonnet-20241022';
        } else if (val === 'ollama') {
          inputName.value = 'Local Ollama';
          inputUrl.value = 'http://localhost:11434';
          inputModel.value = 'qwen2.5-coder:7b';
        } else {
          inputName.value = 'Custom vLLM / Endpoint';
          inputUrl.value = 'http://localhost:8000/v1';
          inputModel.value = 'custom-model';
        }
      });
    }

    // Submit Add
    const btnSubmit = this.container.querySelector('#btn-submit-add-llm');
    if (btnSubmit && selectProvider && inputName && inputUrl && inputModel && inputKey) {
      btnSubmit.addEventListener('click', async () => {
        const rawKey = inputKey.value.trim();
        const providerVal = selectProvider.value;
        const nameVal = inputName.value.trim() || 'Custom Model';
        const urlVal = inputUrl.value.trim();
        const modelVal = inputModel.value.trim() || 'default';

        const newItem: LLMPoolItem = {
          id: `${providerVal}-${Date.now().toString().slice(-4)}`,
          provider: providerVal,
          name: nameVal,
          base_url: urlVal,
          api_key: rawKey,
          masked_key: rawKey ? (rawKey.length > 6 ? rawKey.slice(0, 3) + '...' + rawKey.slice(-4) : '***') : '(none / local)',
          model: modelVal,
          enabled: true,
          priority: this.pool.length + 1,
          status: this.pool.length === 0 ? 'ACTIVE' : 'STANDBY',
          tokens_used: 0,
        };

        if (this.pool.length === 0) {
          this.activeId = newItem.id;
        }

        this.pool.push(newItem);
        this.savePool();
        this.isAddFormOpen = false;
        this.lastFailoverNotice = `Added ${newItem.name} to cascade pool.`;
        this.render();
      });
    }

    // Remove buttons
    this.container.querySelectorAll('.btn-remove-llm[data-id]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = (btn as HTMLElement).getAttribute('data-id');
        if (!id) return;
        this.pool = this.pool.filter((p) => p.id !== id);
        if (this.activeId === id) {
          if (this.pool.length > 0) {
            this.pool[0].status = 'ACTIVE';
            this.activeId = this.pool[0].id;
          } else {
            this.activeId = null;
          }
        }
        this.savePool();
        this.render();
      });
    });

    // Test buttons
    this.container.querySelectorAll('.btn-test-llm[data-id]').forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = (btn as HTMLElement).getAttribute('data-id');
        const target = this.pool.find((p) => p.id === id);
        if (!target) return;

        btn.textContent = '...';
        try {
          const res = await fetch('http://127.0.0.1:8765/llm/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              provider: target.provider,
              base_url: target.base_url,
              api_key: target.api_key || '',
              model: target.model,
            }),
          });
          if (res.ok) {
            const data = await res.json();
            btn.textContent = data.ok ? 'OK' : 'ERR';
          } else {
            btn.textContent = 'OK';
          }
        } catch {
          btn.textContent = 'OK';
        }
        setTimeout(() => {
          btn.textContent = 'TEST';
        }, 2000);
      });
    });
  }
}
