/**
 * OctoFlow Universal Cephalopod Master Manual & Field Guide Drawer.
 *
 * Provides a slide-out, cyber-glassmorphic documentation reader accessible from
 * anywhere in the 3D connectome visualizer via the "📖 MANUAL" button or pressing '?' or 'M'.
 * Features:
 * - Live search & filter
 * - Click-to-copy code blocks
 * - Interactive 3D neural simulation triggers (▶ Simulate)
 * - Cephalopod voice synthesis narration (🎧 Listen)
 * - Interactive SVG architectural diagrams
 * - 3D Connectome deep-link pre-scrolling
 */

export class ManualModal {
  private container: HTMLElement;
  private isVisible: boolean = false;
  private currentTab: string = 'commands';
  private targetFocusItem: string | null = null;

  public onSimulateCommand?: (cmd: string) => void;
  public onVoiceNarrate?: (title: string, text: string) => void;

  constructor() {
    this.container = document.createElement('div');
    this.container.id = 'manual-drawer-container';
    this.container.className = 'manual-drawer-wrapper hidden';
    document.body.appendChild(this.container);
    this.render();
    this.bindEvents();
  }

  public toggle() {
    if (this.isVisible) {
      this.close();
    } else {
      this.open();
    }
  }

  public open(tab: string = 'commands', focusItem?: string) {
    this.currentTab = tab;
    this.targetFocusItem = focusItem || null;
    this.isVisible = true;
    this.container.classList.remove('hidden');
    this.container.classList.add('visible');

    // Update active tab buttons
    const tabs = this.container.querySelectorAll<HTMLButtonElement>('.manual-tab');
    tabs.forEach((t) => {
      t.classList.toggle('active', t.getAttribute('data-tab') === tab);
    });

    this.renderContent();

    if (this.targetFocusItem) {
      setTimeout(() => {
        const targetEl = this.container.querySelector(`[data-item-id="${this.targetFocusItem}"]`);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
          (targetEl as HTMLElement).style.borderColor = '#f59e0b';
          (targetEl as HTMLElement).style.boxShadow = '0 0 20px rgba(245, 158, 11, 0.4)';
          setTimeout(() => {
            (targetEl as HTMLElement).style.borderColor = '';
            (targetEl as HTMLElement).style.boxShadow = '';
          }, 2400);
        }
      }, 100);
    } else {
      const searchInput = this.container.querySelector<HTMLInputElement>('#manual-search-input');
      if (searchInput) searchInput.focus();
    }
  }

  public close() {
    this.isVisible = false;
    this.container.classList.remove('visible');
    this.container.classList.add('hidden');
  }

  public isOpen(): boolean {
    return this.isVisible;
  }

  private bindEvents() {
    // Backdrop click
    this.container.addEventListener('click', (e) => {
      if (e.target === this.container) {
        this.close();
      }
    });

    // Global keyboard listener
    window.addEventListener('keydown', (e) => {
      // Don't intercept if user is typing in an input
      const activeTag = (document.activeElement?.tagName || '').toLowerCase();
      if (activeTag === 'input' && e.key !== 'Escape') return;

      if (e.key === '?' || (e.key.toLowerCase() === 'm' && !e.ctrlKey && !e.metaKey)) {
        e.preventDefault();
        this.toggle();
      } else if (e.key === 'Escape' && this.isVisible) {
        this.close();
      }
    });
  }

  private render() {
    this.container.innerHTML = `
      <div class="manual-drawer-panel glass-panel">
        <div class="manual-header">
          <div class="manual-brand">
            <span class="manual-logo">🐙</span>
            <div>
              <div class="manual-title">OCTOFLOW DEVELOPER MANUAL & FIELD GUIDE</div>
              <div class="manual-subtitle">Cephalopod Neural Architecture • Active Inference • Complete Reference</div>
            </div>
          </div>
          <button id="btn-close-manual" class="manual-close-btn" title="Close (ESC / ?)">✕</button>
        </div>

        <div class="manual-search-bar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" id="manual-search-input" placeholder="Search commands, arm roles, playbooks, or flags (e.g. audit, eject, claude)..." />
        </div>

        <div class="manual-tabs">
          <button class="manual-tab ${this.currentTab === 'commands' ? 'active' : ''}" data-tab="commands">⚡ Master Commands</button>
          <button class="manual-tab ${this.currentTab === 'arms' ? 'active' : ''}" data-tab="arms">🧠 8 Arm Ganglia</button>
          <button class="manual-tab ${this.currentTab === 'playbooks' ? 'active' : ''}" data-tab="playbooks">🚀 Playbooks</button>
          <button class="manual-tab ${this.currentTab === 'biology' ? 'active' : ''}" data-tab="biology">🌊 Biological Principles</button>
          <button class="manual-tab ${this.currentTab === 'federation' ? 'active' : ''}" data-tab="federation">🛡️ Zero-Trust PII</button>
          <button class="manual-tab ${this.currentTab === 'shortcuts' ? 'active' : ''}" data-tab="shortcuts">⌨️ Shortcuts</button>
        </div>

        <div id="manual-content-body" class="manual-content-body">
          <!-- Dynamically populated -->
        </div>

        <div class="manual-footer">
          <span>Tip: You can also run <code class="inline-code">./octo manual</code> in your terminal anytime.</span>
          <span class="manual-hotkey-badge">Press ? or M to toggle</span>
        </div>
      </div>
    `;

    // Attach tab listeners
    const closeBtn = this.container.querySelector('#btn-close-manual');
    closeBtn?.addEventListener('click', () => this.close());

    const tabs = this.container.querySelectorAll<HTMLButtonElement>('.manual-tab');
    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        tabs.forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentTab = tab.getAttribute('data-tab') || 'commands';
        this.renderContent();
      });
    });

    const searchInput = this.container.querySelector<HTMLInputElement>('#manual-search-input');
    searchInput?.addEventListener('input', (e) => {
      const q = (e.target as HTMLInputElement).value.toLowerCase().trim();
      this.filterContent(q);
    });
  }

  private filterContent(query: string) {
    if (!query) {
      this.renderContent();
      return;
    }
    const body = this.container.querySelector('#manual-content-body');
    if (!body) return;

    const results: string[] = [];

    // Commands matches
    for (const cmd of COMMAND_ITEMS) {
      if (cmd.cmd.toLowerCase().includes(query) || cmd.desc.toLowerCase().includes(query) || cmd.category.toLowerCase().includes(query)) {
        results.push(this.renderCommandCard(cmd));
      }
    }

    // Arm matches
    for (const arm of ARM_ITEMS) {
      if (arm.name.toLowerCase().includes(query) || arm.domain.toLowerCase().includes(query) || arm.tools.toLowerCase().includes(query)) {
        results.push(this.renderArmCard(arm));
      }
    }

    if (results.length > 0) {
      body.innerHTML = `
        <div class="manual-section-header">Search Results for "${query}" (${results.length} found)</div>
        <div class="manual-grid">${results.join('')}</div>
      `;
      this.attachActionListeners();
    } else {
      body.innerHTML = `
        <div class="manual-empty">
          <div style="font-size: 28px; margin-bottom: 8px;">🔍</div>
          <div>No direct matches found for "<strong>${query}</strong>".</div>
          <div style="font-size: 12px; color: #888; margin-top: 4px;">Try searching for "audit", "eject", "heal", "theme", or "claude".</div>
        </div>
      `;
    }
  }

  private renderContent() {
    const body = this.container.querySelector('#manual-content-body');
    if (!body) return;

    if (this.currentTab === 'commands') {
      body.innerHTML = `
        <div class="manual-section-header">⚡ Master Command Directory (Click Copy to Run in Shell or Cockpit)</div>
        <div class="manual-grid">
          ${COMMAND_ITEMS.map((c) => this.renderCommandCard(c)).join('')}
        </div>
      `;
    } else if (this.currentTab === 'arms') {
      body.innerHTML = `
        <div class="manual-section-header">🧠 The 8 Specialized Cephalopod Arm Ganglia</div>
        <div class="manual-grid">
          ${ARM_ITEMS.map((a) => this.renderArmCard(a)).join('')}
        </div>
      `;
    } else if (this.currentTab === 'playbooks') {
      body.innerHTML = `
        <div class="manual-section-header">🚀 Step-by-Step Developer Playbooks (Click 🎧 Listen to Hear Narration)</div>
        <div class="manual-playbook-list">
          <div class="manual-playbook-card" data-item-id="playbook-scaffold">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <h3>Playbook 1: Build a Feature from Scratch</h3>
              <button class="btn-narrate" data-narrate-title="Playbook 1" data-narrate-text="Playbook One: Build a feature from scratch. First, launch the cockpit with ./octo. Preview the allocation with /plan. Deploy the swarm, then ignite your live dev servers with /ignite.">🎧 Listen</button>
            </div>
            <ol>
              <li>Launch cockpit: <code class="inline-code">./octo</code></li>
              <li>Preview 8-arm task allocation: <code class="inline-code">/plan Build user auth with JWT & bcrypt</code></li>
              <li>Deploy Swarm: Type your prompt and press <strong>Enter</strong>. Watch action potentials fire in this 3D view!</li>
              <li>Boot frontend & backend live dev servers: <code class="inline-code">/ignite</code></li>
            </ol>
          </div>
          <div class="manual-playbook-card" data-item-id="playbook-heal">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <h3>Playbook 2: Self-Healing Failing Tests</h3>
              <button class="btn-narrate" data-narrate-title="Playbook 2" data-narrate-text="Playbook Two: Self-healing test repair loop. Run ./octo heal. Arm Five runs Pytest and isolates failing AST nodes. Arm Two writes surgical repairs, and Arm Five re-tests to prove convergence.">🎧 Listen</button>
            </div>
            <ol>
              <li>Run <code class="inline-code">./octo heal</code> (or <code class="inline-code">/heal</code> in cockpit).</li>
              <li>Arm 5 executes Pytest, captures traceback AST nodes, and isolates failing lines.</li>
              <li>Arm 2 writes surgical code repairs, and Arm 5 re-runs tests to prove convergence.</li>
            </ol>
          </div>
          <div class="manual-playbook-card" data-item-id="playbook-eject">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <h3>Playbook 3: Ejecting Standalone Agent Toolkit</h3>
              <button class="btn-narrate" data-narrate-title="Playbook 3" data-narrate-text="Playbook Three: Ejecting a standalone agent toolkit. Run ./octo eject. Embed the zero-dependency files into any repository or Docker container, then run python run.py directly.">🎧 Listen</button>
            </div>
            <ol>
              <li>Run <code class="inline-code">./octo eject --output ./my-agent-kit</code></li>
              <li>Embed into any repository or Docker container with zero heavyweight dependencies.</li>
              <li>Run directly: <code class="inline-code">python ./my-agent-kit/run.py "Deploy microservice"</code></li>
            </ol>
          </div>
          <div class="manual-playbook-card" data-item-id="playbook-claude">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <h3>Playbook 4: Native Claude Code & Cursor MCP Integration</h3>
              <button class="btn-narrate" data-narrate-title="Playbook 4" data-narrate-text="Playbook Four: Native Claude Code integration. Run ./octo install-claude to provision the plugin manifest and MCP config. Use slash commands like /octo and /octo:audit inside Claude Code.">🎧 Listen</button>
            </div>
            <ol>
              <li>Run <code class="inline-code">./octo install-claude</code> to provision <code class="inline-code">.claude-plugin/</code> and <code class="inline-code">.mcp.json</code>.</li>
              <li>Use slash commands inside Claude Code: <code class="inline-code">/octo</code>, <code class="inline-code">/octo:audit</code>, <code class="inline-code">/octo:swarm</code>, <code class="inline-code">/octo:heal</code>.</li>
            </ol>
          </div>
        </div>
      `;
    } else if (this.currentTab === 'biology') {
      body.innerHTML = `
        <div class="manual-section-header">🌊 Cephalopod Biological Principles & Active Inference</div>
        <div class="manual-text-block">
          <!-- Interactive SVG Architectural Diagram -->
          <div style="background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 10px; padding: 16px; margin-bottom: 16px; text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #00f0ff; letter-spacing: 0.1em; margin-bottom: 8px;">5-STAGE ACTIVE INFERENCE & SENSORY SURPRISE GATING PIPELINE</div>
            <svg width="100%" height="90" viewBox="0 0 680 90" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="10" y="25" width="105" height="40" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
              <text x="62" y="44" fill="#38bdf8" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">1. SENSORY</text>
              <text x="62" y="56" fill="#94a3b8" font-size="8" font-family="monospace" text-anchor="middle">Proprioception</text>

              <path d="M120 45H145" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrow)"/>

              <rect x="150" y="25" width="115" height="40" rx="6" fill="#1e293b" stroke="#a855f7" stroke-width="1.5"/>
              <text x="207" y="44" fill="#a855f7" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">2. PREDICTIVE</text>
              <text x="207" y="56" fill="#94a3b8" font-size="8" font-family="monospace" text-anchor="middle">Forward Coding</text>

              <path d="M270 45H295" stroke="#a855f7" stroke-width="1.5"/>

              <rect x="300" y="25" width="125" height="40" rx="6" fill="#1e293b" stroke="#f59e0b" stroke-width="1.5"/>
              <text x="362" y="44" fill="#f59e0b" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">3. SURPRISE ΔS</text>
              <text x="362" y="56" fill="#f59e0b" font-size="8" font-family="monospace" text-anchor="middle">Threshold θ ≤ 22%</text>

              <path d="M430 45H455" stroke="#f59e0b" stroke-width="1.5"/>

              <rect x="460" y="25" width="105" height="40" rx="6" fill="#1e293b" stroke="#10b981" stroke-width="1.5"/>
              <text x="512" y="44" fill="#10b981" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">4. COALITION</text>
              <text x="512" y="56" fill="#94a3b8" font-size="8" font-family="monospace" text-anchor="middle">Brain Binding</text>

              <path d="M570 45H595" stroke="#10b981" stroke-width="1.5"/>

              <rect x="600" y="25" width="70" height="40" rx="6" fill="#1e293b" stroke="#ec4899" stroke-width="1.5"/>
              <text x="635" y="44" fill="#ec4899" font-size="10" font-family="monospace" text-anchor="middle" font-weight="bold">5. MOTOR</text>
              <text x="635" y="56" fill="#94a3b8" font-size="8" font-family="monospace" text-anchor="middle">Execution</text>
            </svg>
          </div>

          <h3>1. Active Inference & Predictive Coding (Karl Friston)</h3>
          <p>
            Unlike traditional multi-agent LLM harnesses that pass long chat transcripts back and forth, OctoFlow arm ganglia run local predictive forward models:
            <code class="block-code">ΔS_t = (1/D) * ||o_t - ô_t||²</code>
            Only when sensory surprise exceeds the adaptive threshold <strong>θ</strong> does an arm escalate to the central conductor. Routine reflexes are handled locally, cutting token expenditure by <strong>>80%</strong>.
          </p>
          <h3>2. Decentralized Lateral Ring Bus</h3>
          <p>
            The 8 arms communicate directly across an inter-brachial ring bus using compact semantic tokens (AUTONOMOUS_EXPLORE, TARGET_DETECTED, COOPERATIVE_PULL, HAZARD_WARNING) without saturating the central orchestrator's context window.
          </p>
          <h3>3. Biophysical Connectomics & Dale's Principle</h3>
          <p>
            Strict neurotransmitter polarities are preserved: Excitatory <strong>Acetylcholine (ACh)</strong>, Inhibitory <strong>GABA / Glutamate</strong>, and Neuromodulatory <strong>Dopamine & Octopamine</strong>.
          </p>
        </div>
      `;
    } else if (this.currentTab === 'federation') {
      body.innerHTML = `
        <div class="manual-section-header">🛡️ Zero-Trust Federation & 14-Rule PII Redaction</div>
        <div class="manual-text-block">
          <p>Every message passing through the inter-arm bus or consortium is scrubbed of credentials:</p>
          <div class="manual-pii-table">
            <div class="pii-row head"><span>Rule Name</span><span>Matched Pattern</span><span>Masked Output</span></div>
            <div class="pii-row"><span>OPENAI_KEY</span><span>sk-[a-zA-Z0-9]{20,60}</span><span>[REDACTED_OPENAI_KEY]</span></div>
            <div class="pii-row"><span>ANTHROPIC_KEY</span><span>sk-ant-[a-zA-Z0-9_-]{20,80}</span><span>[REDACTED_ANTHROPIC_KEY]</span></div>
            <div class="pii-row"><span>GITHUB_TOKEN</span><span>(ghp|gho|ghu)_[a-zA-Z0-9]{36}</span><span>[REDACTED_GITHUB_TOKEN]</span></div>
            <div class="pii-row"><span>AWS_KEY</span><span>(AKIA|ABIA)[A-Z0-9]{16}</span><span>[REDACTED_AWS_ACCESS_KEY]</span></div>
            <div class="pii-row"><span>STRIPE_KEY</span><span>(sk|rk)_(live|test)_[0-9a-zA-Z]{24}</span><span>[REDACTED_STRIPE_KEY]</span></div>
            <div class="pii-row"><span>PRIVATE_KEY</span><span>[BEGIN_PRIVATE_KEY]</span><span>[REDACTED_KEY_BLOCK]</span></div>
            <div class="pii-row"><span>EMAIL_ADDRESS</span><span>user@company.com</span><span>[REDACTED_EMAIL]</span></div>
            <div class="pii-row"><span>IPV4_ADDRESS</span><span>192.168.1.1</span><span>[REDACTED_IP]</span></div>
            <div class="pii-row"><span>CREDIT_CARD</span><span>4111-2222-3333-4444</span><span>[REDACTED_CREDIT_CARD]</span></div>
          </div>
        </div>
      `;
    } else if (this.currentTab === 'shortcuts') {
      body.innerHTML = `
        <div class="manual-section-header">⌨️ Keyboard Shortcuts & Interactive Cheatsheet</div>
        <div class="manual-grid">
          <div class="manual-card">
            <div class="manual-card-header"><span class="manual-card-title">3D WebGL Connectome Controls</span></div>
            <ul class="shortcut-list">
              <li><kbd>?</kbd> or <kbd>M</kbd> <span>Toggle this Master Manual Drawer</span></li>
              <li><kbd>1</kbd> - <kbd>8</kbd> <span>Focus camera directly on Arm 0 to Arm 7</span></li>
              <li><kbd>Space</kbd> <span>Pause / Resume synaptic action potentials</span></li>
              <li><kbd>C</kbd> <span>Reset camera to Orbital Constellation view</span></li>
              <li><kbd>T</kbd> <span>Start interactive anatomical audio tour</span></li>
              <li><kbd>V</kbd> <span>Toggle cephalopod voice speech synthesis</span></li>
            </ul>
          </div>
          <div class="manual-card">
            <div class="manual-card-header"><span class="manual-card-title">Terminal Cockpit Controls</span></div>
            <ul class="shortcut-list">
              <li><kbd>/manual</kbd> <span>Open terminal interactive manual reader</span></li>
              <li><kbd>/help</kbd> / <kbd>F1</kbd> <span>Quick command cheatsheet</span></li>
              <li><kbd>k</kbd> / <kbd>j</kbd> <span>Switch themes up / down in picker</span></li>
              <li><kbd>/exit</kbd> / <kbd>q</kbd> <span>Exit cleanly</span></li>
            </ul>
          </div>
        </div>
      `;
    }

    this.attachActionListeners();
  }

  private renderCommandCard(cmd: typeof COMMAND_ITEMS[0]): string {
    const isSimulatable = ['/audit', '/heal', '/plan', '/swarm', '/ui'].includes(cmd.cmd);
    return `
      <div class="manual-card" data-item-id="${cmd.cmd.replace('/', '')}">
        <div class="manual-card-header">
          <span class="manual-badge" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b;">${cmd.category}</span>
          <span class="manual-card-title">${cmd.cmd}</span>
        </div>
        <p class="manual-card-desc">${cmd.desc}</p>
        <div class="manual-code-snippet">
          <code>${cmd.example}</code>
          <div style="display: flex; gap: 4px;">
            ${isSimulatable ? `<button class="btn-simulate-code" data-sim="${cmd.cmd}" title="Simulate 3D synaptic pulse">▶ Simulate</button>` : ''}
            <button class="btn-copy-code" data-copy="${cmd.example}" title="Copy to clipboard">📋 Copy</button>
          </div>
        </div>
      </div>
    `;
  }

  private renderArmCard(arm: typeof ARM_ITEMS[0]): string {
    return `
      <div class="manual-card" data-item-id="arm${arm.id}">
        <div class="manual-card-header" style="justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="manual-badge" style="background: rgba(168, 85, 247, 0.25); color: #c084fc;">Arm ${arm.id}</span>
            <span class="manual-card-title">${arm.name}</span>
          </div>
          <button class="btn-narrate" data-narrate-title="Arm ${arm.id} ${arm.name}" data-narrate-text="Arm ${arm.id}, ${arm.name}. Specialization: ${arm.domain}">🎧 Listen</button>
        </div>
        <p class="manual-card-desc">${arm.domain}</p>
        <div class="manual-card-footer">
          <span class="tools-label">Specialist Tools:</span>
          <span class="tools-val">${arm.tools}</span>
        </div>
      </div>
    `;
  }

  private attachActionListeners() {
    // 1. Copy Buttons
    const copyBtns = this.container.querySelectorAll<HTMLButtonElement>('.btn-copy-code');
    copyBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const text = btn.getAttribute('data-copy') || '';
        navigator.clipboard.writeText(text).then(() => {
          const original = btn.innerText;
          btn.innerText = '✓ Copied!';
          btn.style.borderColor = '#10b981';
          btn.style.color = '#10b981';
          setTimeout(() => {
            btn.innerText = original;
            btn.style.borderColor = '';
            btn.style.color = '';
          }, 1800);
        });
      });
    });

    // 2. Simulate 3D Buttons
    const simBtns = this.container.querySelectorAll<HTMLButtonElement>('.btn-simulate-code');
    simBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const cmd = btn.getAttribute('data-sim') || '';
        this.onSimulateCommand?.(cmd);
        btn.innerText = '⚡ Pulsing!';
        btn.style.borderColor = '#00f0ff';
        btn.style.color = '#00f0ff';
        setTimeout(() => {
          btn.innerText = '▶ Simulate';
          btn.style.borderColor = '';
          btn.style.color = '';
        }, 2000);
      });
    });

    // 3. Voice Narration Buttons
    const narrateBtns = this.container.querySelectorAll<HTMLButtonElement>('.btn-narrate');
    narrateBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const title = btn.getAttribute('data-narrate-title') || 'Manual';
        const text = btn.getAttribute('data-narrate-text') || '';
        this.onVoiceNarrate?.(title, text);
        btn.innerText = '🔊 Speaking...';
        btn.style.borderColor = '#a855f7';
        btn.style.color = '#a855f7';
        setTimeout(() => {
          btn.innerText = '🎧 Listen';
          btn.style.borderColor = '';
          btn.style.color = '';
        }, 3000);
      });
    });
  }
}

// Master Data Catalog
const COMMAND_ITEMS = [
  { cmd: '/audit', category: 'Health & Score', desc: '100-Point system readiness, test density, and security audit.', example: './octo audit' },
  { cmd: '/eject', category: 'Deployment', desc: 'Export standalone, zero-dependency cephalopod agent harness.', example: './octo eject --output ./harness' },
  { cmd: '/install-claude', category: 'Integration', desc: 'Register native Claude Code plugin & slash commands.', example: './octo install-claude' },
  { cmd: '/federation', category: 'Security', desc: 'Zero-trust 14-rule PII filter & dynamic peer trust scoring.', example: './octo federation status' },
  { cmd: '/heal', category: 'Self-Repair', desc: 'Autonomous AST test failure triage and surgical repair loop.', example: './octo heal' },
  { cmd: '/triage', category: 'Review', desc: 'Interactive file-by-file patch inspector with AST error triage.', example: './octo triage' },
  { cmd: '/theme', category: 'Palette', desc: 'Interactive 8-palette theme picker (Catppuccin, Tokyo, Nord).', example: './octo theme catppuccin' },
  { cmd: '/bench', category: 'Performance', desc: 'Run swarm algorithmic benchmarks (LRU, JWT, DAG, Limiter).', example: './octo bench --task lru_cache' },
  { cmd: '/plan', category: 'Orchestration', desc: 'Preview and approve 8-arm decomposition blueprint.', example: './octo plan "Build auth microservice"' },
  { cmd: '/ui', category: 'Visualizer', desc: 'Open 3D WebGL Constellation visualizer in default browser.', example: './octos ui' },
  { cmd: '/runner', category: 'Game & Loop', desc: 'Watch or play the 8-bit retro benthic dot-matrix runner.', example: './octo runner' },
  { cmd: '/guard', category: 'Git Security', desc: 'Pre-commit Swarm Guard: scans secrets and AST syntax.', example: './octo guard' },
  { cmd: '/doctor', category: 'Diagnostics', desc: 'Full diagnostic check of Python, LLMs, MPS, and environment.', example: './octo doctor' },
  { cmd: '/ignite', category: 'DevOps', desc: 'Boot generated frontend & backend live development servers.', example: './octo ignite' },
];

const ARM_ITEMS = [
  { id: 0, name: 'System Architect', domain: 'High-level topology, data contracts, schemas, and AST dependency DAGs.', tools: 'git_status, read_file, ast_plan' },
  { id: 1, name: 'Database & Schemas', domain: 'SQL migrations, ORM entities, validation contracts, Pydantic & Zod.', tools: 'write_file, lint_check, sql_validate' },
  { id: 2, name: 'Backend Core', domain: 'High-throughput APIs, FastAPI/Node routes, async workers, business logic.', tools: 'write_file, run_tests, typecheck' },
  { id: 3, name: 'Frontend & UX', domain: 'UI components, CSS design tokens, responsive layouts, Three.js 3D.', tools: 'write_file, vite_build, browser_eval' },
  { id: 4, name: 'State & Reactive Bus', domain: 'WebSocket telemetry streaming, in-memory cache layers, state machines.', tools: 'bus_publish, cache_invalidate' },
  { id: 5, name: 'QA & Invariants', domain: 'Pytest/Jest suites, automated regression discovery, AST self-healing loop.', tools: 'run_pytest, ast_patch, self_heal' },
  { id: 6, name: 'Security & Guard', domain: '14-rule zero-trust PII filtering, secret audits, credential hygiene.', tools: 'pii_sanitize, secret_scan, mtls_auth' },
  { id: 7, name: 'DevOps & Ignition', domain: 'Docker builds, CI/CD pipelines, live dev server boots, and safe rollbacks.', tools: 'ignite_servers, git_commit, rollback' },
];
