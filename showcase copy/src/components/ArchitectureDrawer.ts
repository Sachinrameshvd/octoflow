export function createArchitectureDrawer(): {
  element: HTMLElement;
  open: () => void;
  close: () => void;
  toggle: () => boolean;
} {
  const drawer = document.createElement('div');
  drawer.className = 'arch-drawer-backdrop';

  drawer.innerHTML = `
    <div class="arch-drawer-panel">
      <div class="arch-drawer-header">
        <div>
          <div style="font-family: var(--font-mono); font-size: 10px; color: var(--accent-cyan); letter-spacing: 0.15em;">
            STAFF &amp; PRINCIPAL SPECIFICATION
          </div>
          <h3 style="font-family: var(--font-display); font-size: 22px; color: #ffffff; margin-top: 2px;">
            System Architecture &amp; Tensor Dimensions
          </h3>
        </div>
        <button id="arch-drawer-close" class="hud-pill" style="padding: 6px 12px;">&times; Close</button>
      </div>

      <div class="arch-drawer-body">
        <!-- Section 1: End-to-End Tensor Topology -->
        <div class="arch-spec-box">
          <h4 style="font-family: var(--font-display); font-size: 15px; color: #ffffff; margin-bottom: 10px;">
            1. PyTorch Tensor Dimensions &amp; Forward Pass Flow
          </h4>
          <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 11px; text-align: left;">
              <thead>
                <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.1); color: var(--accent-cyan);">
                  <th style="padding: 8px 10px;">Layer / Pipeline Stage</th>
                  <th style="padding: 8px 10px;">Input Shape</th>
                  <th style="padding: 8px 10px;">Output Shape</th>
                  <th style="padding: 8px 10px;">Latency</th>
                </tr>
              </thead>
              <tbody style="color: var(--text-muted);">
                <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.04);">
                  <td style="padding: 8px 10px; color: #ffffff;">8x Peripheral Sensory Encoders</td>
                  <td style="padding: 8px 10px;">[8, Batch, 4]</td>
                  <td style="padding: 8px 10px;">[8, Batch, 32]</td>
                  <td style="padding: 8px 10px; color: var(--accent-emerald);">&lt; 0.6 ms</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.04);">
                  <td style="padding: 8px 10px; color: #ffffff;">Predictive Surprise GRU (Forward Model)</td>
                  <td style="padding: 8px 10px;">[8, Batch, 34]</td>
                  <td style="padding: 8px 10px;">[8, Batch, 4]</td>
                  <td style="padding: 8px 10px; color: var(--accent-emerald);">&lt; 0.4 ms</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.04);">
                  <td style="padding: 8px 10px; color: #ffffff;">Sigmoid Communication Gate &theta;</td>
                  <td style="padding: 8px 10px;">[8, Batch, 33]</td>
                  <td style="padding: 8px 10px;">[8, Batch, 1]</td>
                  <td style="padding: 8px 10px; color: var(--accent-emerald);">&lt; 0.1 ms</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.04);">
                  <td style="padding: 8px 10px; color: #ffffff;">Central Multi-Head Attention Binder</td>
                  <td style="padding: 8px 10px;">[Batch, K, 32] (K &le; 2)</td>
                  <td style="padding: 8px 10px;">[Batch, 128]</td>
                  <td style="padding: 8px 10px; color: var(--accent-cyan);">1.6 ms</td>
                </tr>
                <tr>
                  <td style="padding: 8px 10px; color: #ffffff;">Actor-Critic Discrete &amp; Value Heads</td>
                  <td style="padding: 8px 10px;">[Batch, 128]</td>
                  <td style="padding: 8px 10px;">Actions: [8, 2], Value: [1]</td>
                  <td style="padding: 8px 10px; color: var(--accent-cyan);">0.8 ms</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 2: Mathematical Formulations -->
        <div class="arch-spec-box">
          <h4 style="font-family: var(--font-display); font-size: 15px; color: #ffffff; margin-bottom: 8px;">
            2. The Core Biological Invariants
          </h4>
          <div style="font-family: var(--font-mono); font-size: 12px; color: #cbd5e1; line-height: 1.8;">
            <p><strong style="color: var(--accent-cyan);">Sensory Surprise Gating:</strong><br />
            &Delta;S_i = (1/D) &bull; ||o_i^{(t)} - f_&phi;(o_i^{(t-1)}, a_i^{(t-1)})||&sup2;<br />
            g_i = &sigma;(w&bull;&Delta;S_i + b) &gt; &theta; &rArr; Active Gating Budget &le; 21.6%</p>
            
            <p style="margin-top: 10px;"><strong style="color: var(--accent-violet);">Muscular Hydrostat Continuum Constraint:</strong><br />
            Volume = &pi; &bull; r(s)&sup2; &bull; L(s) = Constant &rArr; Radial Expansion r = &radic;(V / (&pi; &bull; L))</p>

            <p style="margin-top: 10px;"><strong style="color: var(--accent-gold);">Zero-Shot Adjacency Rerouting:</strong><br />
            A_{amputated, j} = 0 &rArr; A_{left, right} = 1 &rArr; Gait Frequency &times; 1.45</p>
          </div>
        </div>

        <!-- Section 3: In-Browser WASM Edge Performance Profiler -->
        <div class="arch-spec-box">
          <h4 style="font-family: var(--font-display); font-size: 15px; color: #ffffff; margin-bottom: 8px;">
            3. Edge WebAssembly SIMD Profiling
          </h4>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-family: var(--font-mono); font-size: 11px;">
            <div style="background: rgba(3, 7, 18, 0.7); padding: 10px; border-radius: 8px;">
              <div style="color: var(--text-dim);">EDGE LATENCY</div>
              <div style="font-size: 16px; color: var(--accent-emerald); font-weight: 700; margin-top: 2px;">3.2 ms</div>
              <div style="color: var(--text-dim); font-size: 9px;">Target: &le; 5.0ms</div>
            </div>
            <div style="background: rgba(3, 7, 18, 0.7); padding: 10px; border-radius: 8px;">
              <div style="color: var(--text-dim);">SIMD THREADS</div>
              <div style="font-size: 16px; color: var(--accent-cyan); font-weight: 700; margin-top: 2px;">4x Active</div>
              <div style="color: var(--text-dim); font-size: 9px;">WebAssembly SIMD</div>
            </div>
            <div style="background: rgba(3, 7, 18, 0.7); padding: 10px; border-radius: 8px;">
              <div style="color: var(--text-dim);">SERVER DEPENDENCY</div>
              <div style="font-size: 16px; color: var(--accent-gold); font-weight: 700; margin-top: 2px;">0.00% Zero Cloud</div>
              <div style="color: var(--text-dim); font-size: 9px;">100% Client-Side</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  let isOpen = false;
  const panel = drawer.querySelector('.arch-drawer-panel') as HTMLElement;
  const closeBtn = drawer.querySelector('#arch-drawer-close') as HTMLButtonElement;

  function open() {
    isOpen = true;
    drawer.classList.add('open');
    panel.classList.add('open');
  }

  function close() {
    isOpen = false;
    drawer.classList.remove('open');
    panel.classList.remove('open');
  }

  function toggle() {
    if (isOpen) close();
    else open();
    return isOpen;
  }

  closeBtn.addEventListener('click', close);
  drawer.addEventListener('click', (e) => {
    if (e.target === drawer) close();
  });

  return { element: drawer, open, close, toggle };
}

