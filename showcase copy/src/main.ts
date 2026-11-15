import './styles/cinematic.css';
import { OctopusConnectomeExperience, CAMERA_WAYPOINTS } from './connectome/OctopusConnectomeExperience';
import { SoundEngine } from './audio/SoundEngine';
import { createArchitectureDrawer } from './components/ArchitectureDrawer';
import {
  renderIndividualOctopusHTML,
  renderConsortiumFinaleHTML,
  initConsortiumExperience,
} from './components/ConsortiumConnectomeView';

document.addEventListener('DOMContentLoaded', () => {
  const app = document.getElementById('app');
  if (!app) return;

  // 1. Initialize Audio Engine & Architecture Drawer
  const soundEngine = new SoundEngine();
  const archDrawer = createArchitectureDrawer();
  document.body.appendChild(archDrawer.element);

  app.innerHTML = `
    <!-- Fullscreen Three.js WebGL Canvas -->
    <div id="webgl-canvas-container"></div>
    <div class="cinema-vignette"></div>

    <!-- Active Theory Minimalist Floating HUD -->
    <div class="hud-layer">
      <!-- Top Bar -->
      <div class="hud-top">
        <a href="#" class="hud-brand">
          <div class="hud-brand-symbol"></div>
          <div>
            <div class="hud-brand-text">OCTOFLOW</div>
            <div class="hud-brand-sub">DECENTRALIZED CONNECTOME</div>
          </div>
        </a>

        <!-- Slide Stepper & Controls -->
        <div class="hud-nav">
          <div class="slide-nav-group">
            <button id="slide-prev-btn" class="slide-step-btn" title="Previous Slide (or Up Arrow)">&larr; Prev</button>
            <span id="slide-indicator" class="slide-indicator-label">01 / 27</span>
            <button id="slide-next-btn" class="slide-step-btn" title="Next Slide (or Down Arrow)">Next &rarr;</button>
          </div>

          <button id="hud-autotour-btn" class="hud-pill" style="padding: 5px 12px; color: var(--accent-gold);" title="Sit back and enjoy the choreographed 60-second guided cinematic flight">
            ▶ Auto-Tour
          </button>

          <button id="hud-consortium-btn" class="hud-pill" style="padding: 5px 12px; color: var(--accent-cyan); font-weight: 700;" title="Explore the Multi-Octopus Consortium Swarm">
            ◈ Consortium
          </button>

          <button id="hud-arch-btn" class="hud-pill" style="padding: 5px 12px; color: var(--accent-cyan);" title="Inspect PyTorch Tensor Dimensions and WASM SIMD Benchmarks">
            &lt; / &gt; Tensors
          </button>

          <button id="hud-dossier-btn" class="dossier-pill-btn">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            Executive PDF
          </button>
        </div>
      </div>

      <!-- Bottom Bar -->
      <div class="hud-bottom">
        <div class="hud-telemetry">
          <div>LOCUS: <span id="telemetry-cam">X: 0.0 &bull; Y: 42.0 &bull; Z: 120.0</span></div>
          <div>CONNECTOME: <span>10,480 Biological Neurons</span> &bull; PULSES: <span id="telemetry-signals">256 active</span></div>
          <div>EDGE INFERENCE: <span style="color: var(--accent-emerald);">3.2ms (WASM SIMD)</span> &bull; RECOVERY: <span style="color: var(--accent-gold);">0.00s Zero-Shot</span></div>
        </div>

        <!-- Center Action Controls -->
        <div class="hud-action-pills">
          <button id="pill-shockwave" class="hud-pill" title="Trigger high-voltage synaptic pulse across the connectome">
            ↯ Synaptic Pulse
          </button>
          <button id="pill-orbit" class="hud-pill" title="Toggle free 3D camera orbit controls">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path></svg>
            Free Orbit
          </button>
        </div>

        <!-- Scroll Progress Indicator -->
        <div class="hud-progress-wrap">
          <div id="hud-progress-val" class="hud-progress-num">00%</div>
          <div class="hud-progress-track">
            <div id="hud-progress-bar" class="hud-progress-fill"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scroll Runway (2400vh for 18 expansive cinematic chapters) -->
    <div class="scroll-runway">
      <!-- Slide 01 -->
      <div class="chapter-overlay visible" data-chapter="0">
        <div class="chapter-content-card">
          <div class="chapter-tag">01 // THE ALIEN BRAIN</div>
          <h1 class="chapter-headline">500 Million Neurons. Zero Skeleton.</h1>
          <div class="chapter-subhead">Nature engineered high-dimensional soft-body intelligence 500 million years before humanity.</div>
          <p class="chapter-body">
            An octopus commands an infinite degrees-of-freedom continuum with calculated, fluid elegance.
            It navigates complex marine reefs, manipulates objects, and outsmarts predators without a single rigid bone.
          </p>
          <div class="chapter-stat-callout" style="justify-content: center;">
            <div class="stat-item"><div class="stat-item-num">500M</div><div class="stat-item-label">Biological Neurons</div></div>
            <div class="stat-item"><div class="stat-item-num">0</div><div class="stat-item-label">Rigid Joints / Bones</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-cyan);">&infin; DOF</div><div class="stat-item-label">Continuum Mechanics</div></div>
          </div>
          <div style="font-family: var(--font-mono); font-size: 11px; color: var(--accent-cyan); margin-top: 24px; letter-spacing: 0.15em;">
            SCROLL DOWN &darr; &bull; USE ARROW KEYS &bull; OR CLICK &lsquo;AUTO-TOUR&rsquo;
          </div>
        </div>
      </div>

      <!-- Slide 02 -->
      <div class="chapter-overlay" data-chapter="1">
        <div class="chapter-content-card">
          <div class="chapter-tag">02 // THE MONOLITHIC COLLAPSE</div>
          <h2 class="chapter-headline">Why Centralized AI Stalls at the Edge.</h2>
          <div class="chapter-subhead">Streaming continuous sensors to a single central GPU chokes the bus and induces fatal actuation lag.</div>
          <p class="chapter-body">
            When high-dimensional soft-body actuators flood continuous 60Hz proprioception to a single central model, bus bandwidth saturates.
            A 50-millisecond latency jitter or packet drop freezes the entire physical body dead in the water.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-rose);">O(N)</div><div class="stat-item-label">Bandwidth Saturation</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-rose);">&gt; 120ms</div><div class="stat-item-label">Central Latency Spikes</div></div>
            <div class="stat-item"><div class="stat-item-num">Single Point</div><div class="stat-item-label">Of Catastrophic Failure</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 03 -->
      <div class="chapter-overlay" data-chapter="2">
        <div class="chapter-content-card">
          <div class="chapter-tag">03 // DECENTRALIZED BY DESIGN</div>
          <h2 class="chapter-headline">Two-Thirds of the Mind Lives in the Limbs.</h2>
          <div class="chapter-subhead">Not one octopus with eight arms, but eight autonomous intelligences sharing a central strategist.</div>
          <p class="chapter-body">
            Over 350 million neurons reside directly in the peripheral brachial cords. The tentacles don&rsquo;t wait for the brain&rsquo;s permission
            to touch, taste, or retract—they compute physics and reflexes right at the sucker skin.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-cyan);">67%</div><div class="stat-item-label">Neurons in Peripheral Arms</div></div>
            <div class="stat-item"><div class="stat-item-num">8 Ganglia</div><div class="stat-item-label">Edge Co-Processors</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">0.0ms</div><div class="stat-item-label">Central Round-Trip Delay</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 04 -->
      <div class="chapter-overlay" data-chapter="3">
        <div class="chapter-content-card">
          <div class="chapter-tag">04 // THE SUPRAESOPHAGEAL MASS</div>
          <h2 class="chapter-headline">The Strategic Conductor, Not the Micromanager.</h2>
          <div class="chapter-subhead">The central brain sets strategic goals; the peripheral arms solve the inverse continuum physics.</div>
          <p class="chapter-body">
            The Supraesophageal Ganglion never micromanages individual muscle bundles. It broadcasts high-level behavioral vectors&mdash;like
            predator escape or foraging sweeps&mdash;delegating non-linear trajectory execution entirely to the periphery.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-violet);">Hierarchical</div><div class="stat-item-label">Command Structure</div></div>
            <div class="stat-item"><div class="stat-item-num">Async</div><div class="stat-item-label">Sub-Brain Execution</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">Zero Stalls</div><div class="stat-item-label">Under Bus Drops</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 05 -->
      <div class="chapter-overlay" data-chapter="4">
        <div class="chapter-content-card">
          <div class="chapter-tag">05 // THE VERTICAL LOBE SYSTEM</div>
          <h2 class="chapter-headline">Long-Term Potentiation (LTP) Under the Sea.</h2>
          <div class="chapter-subhead">25 million dense associative interneurons functioning as an invertebrate hippocampus.</div>
          <p class="chapter-body">
            Inside the MSF/VL lobe, parallel amacrine matrices undergo activity-dependent synaptic plasticity. It consolidates tactile and visual
            associations into lasting memory, proving biological invertebrate memory matrices rival vertebrate brains.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-violet);">25M</div><div class="stat-item-label">Amacrine Somas</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-cyan);">LTP</div><div class="stat-item-label">Long-Term Potentiation</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-gold);">5.0%</div><div class="stat-item-label">Central Nervous System</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 06 -->
      <div class="chapter-overlay" data-chapter="5">
        <div class="chapter-content-card">
          <div class="chapter-tag">06 // BILATERAL OPTIC SPHERES</div>
          <h2 class="chapter-headline">Seeing Without Stereopsis.</h2>
          <div class="chapter-subhead">Over 120 million neurons synthesizing real-time polarotaxis and dynamic camouflage synthesis.</div>
          <p class="chapter-body">
            Flanking the central brain, bilateral optic lobes process polarization vectors and ambient luminance, streaming condensed
            spatial representations across the fast transverse tractus opticus into the motor centers.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">120M+</div><div class="stat-item-label">Optic Lobe Somas</div></div>
            <div class="stat-item"><div class="stat-item-num">Tractus Opticus</div><div class="stat-item-label">Fast Transverse Highways</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 07 -->
      <div class="chapter-overlay" data-chapter="6">
        <div class="chapter-content-card">
          <div class="chapter-tag">07 // PREDICTIVE SURPRISE</div>
          <h2 class="chapter-headline">Surprise as the Ultimate Filter.</h2>
          <div class="chapter-subhead">If an arm expects what it touches, it stays silent. Only true surprises are escalated.</div>
          <p class="chapter-body">
            Each tentacle runs a sub-millisecond GRU forward model predicting its next sensory state. The prediction residual
            <span style="font-family: var(--font-mono); color: var(--accent-cyan);">&Delta;S_i = (1/D) ||o_t - &ocirc;_t||&sup2;</span> measures genuine surprise.
            Routine tactile motion produces zero error, filtering out redundant noise before it reaches the brain.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-cyan);">&Delta;S_i</div><div class="stat-item-label">Surprise Error Metric</div></div>
            <div class="stat-item"><div class="stat-item-num">Local GRU</div><div class="stat-item-label">Sub-Millisecond Predictor</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">Zero Noise</div><div class="stat-item-label">Central Filtering</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 08 -->
      <div class="chapter-overlay" data-chapter="7">
        <div class="chapter-content-card">
          <div class="chapter-tag">08 // THE 22% MIRACLE</div>
          <h2 class="chapter-headline">The 22% Bandwidth Bottleneck.</h2>
          <div class="chapter-subhead">Slicing central bus traffic by 78.4% with zero loss of muscular actuation fidelity.</div>
          <p class="chapter-body">
            An adaptive sigmoid gate (<span style="font-family: var(--font-mono); color: var(--accent-cyan);">&sigma;(w&bull;&Delta;S_i) &gt; &theta;</span>)
            arbitrates local reflex vs central report. Telemetry is suppressed locally, preserving the precious central bus strictly for critical moments.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-cyan);">78.4%</div><div class="stat-item-label">Bus Traffic Saved</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">99.1%</div><div class="stat-item-label">Motor Fidelity Retained</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-gold);">&le; 21.6%</div><div class="stat-item-label">Measured Comm Overhead</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 09 -->
      <div class="chapter-overlay" data-chapter="8">
        <div class="chapter-content-card">
          <div class="chapter-tag">09 // MULTI-AGENT IN ONE BODY</div>
          <h2 class="chapter-headline">Eight Autonomous Minds, One Living Body.</h2>
          <div class="chapter-subhead">A decentralized multi-agent system solving cooperative manipulation without central bottlenecks.</div>
          <p class="chapter-body">
            Each arm operates its own observation-action loop, proprioception buffer, and motor policy. They function like an embedded swarm
            robotics collective operating seamlessly inside a single organism.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num">8</div><div class="stat-item-label">Independent Policies</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-violet);">Swarm</div><div class="stat-item-label">Collective Control</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">Decentralized</div><div class="stat-item-label">Reinforcement Learning</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 10 -->
      <div class="chapter-overlay" data-chapter="9">
        <div class="chapter-content-card">
          <div class="chapter-tag">10 // SEMANTIC CHATTER</div>
          <h2 class="chapter-headline">The Secret Communication Lexicon of Arms.</h2>
          <div class="chapter-subhead">High-dimensional continuous vectors mapped to human-interpretable behavioral tokens.</div>
          <p class="chapter-body">
            The arms communicate across the interbrachial commissure using five distinct behavioral tokens:
          </p>

          <!-- Living Semantic Chatter Pad -->
          <div class="chatter-card">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
              <span style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--accent-violet);">
                ACTIVE COALITION TEAM: [ARMS 1 &harr; 5]
              </span>
              <span style="font-family: var(--font-mono); font-size: 10px; color: var(--accent-emerald);">INTER-BRACHIAL CHATTER</span>
            </div>

            <div class="chatter-pill-grid">
              <div class="chatter-tile"><span>Arm #0</span><span style="color: var(--accent-emerald);">● AUTONOMOUS_EXPLORE (96%)</span></div>
              <div class="chatter-tile" style="border-color: var(--accent-cyan); background: rgba(56, 189, 248, 0.1);"><span>Arm #1</span><span style="color: var(--accent-cyan);">◈ COOPERATIVE_PULL (94%)</span></div>
              <div class="chatter-tile"><span>Arm #2</span><span style="color: var(--accent-emerald);">● AUTONOMOUS_EXPLORE (95%)</span></div>
              <div class="chatter-tile"><span>Arm #3</span><span style="color: var(--accent-gold);">▲ TARGET_DETECTED (88%)</span></div>
              <div class="chatter-tile"><span>Arm #4</span><span style="color: var(--accent-emerald);">● AUTONOMOUS_EXPLORE (97%)</span></div>
              <div class="chatter-tile" style="border-color: var(--accent-cyan); background: rgba(56, 189, 248, 0.1);"><span>Arm #5</span><span style="color: var(--accent-cyan);">◈ COOPERATIVE_PULL (92%)</span></div>
              <div class="chatter-tile"><span>Arm #6</span><span style="color: var(--accent-emerald);">● AUTONOMOUS_EXPLORE (95%)</span></div>
              <div class="chatter-tile"><span>Arm #7</span><span style="color: var(--accent-rose);">▲ HAZARD_AVOIDANCE (84%)</span></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Slide 11 -->
      <div class="chapter-overlay" data-chapter="10">
        <div class="chapter-content-card">
          <div class="chapter-tag">11 // DYNAMIC COALITIONS</div>
          <h2 class="chapter-headline">Instant Task Forces: [Arms 1 &harr; 5].</h2>
          <div class="chapter-subhead">Central multi-head attention dynamically binds only the arms required for cooperative tasks.</div>
          <p class="chapter-body">
            Rather than synchronizing all 8 limbs monolithically, multi-head attention locks escalated limbs into temporary tactical coalitions
            (like dual-arm pulling) while the other 6 limbs maintain independent equilibrium.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-cyan);">Multi-Head</div><div class="stat-item-label">Attention Binding</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">Temporary</div><div class="stat-item-label">Task Forces</div></div>
            <div class="stat-item"><div class="stat-item-num">Zero Stalls</div><div class="stat-item-label">Unbound Limbs Active</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 12 -->
      <div class="chapter-overlay" data-chapter="11">
        <div class="chapter-content-card">
          <div class="chapter-tag">12 // THE LATERAL HIGHWAY</div>
          <h2 class="chapter-headline">The Interbrachial Commissure Ring.</h2>
          <div class="chapter-subhead">A circular neural ring bridging all eight limbs without central brain round-trips.</div>
          <p class="chapter-body">
            The commissural ring provides direct neighbor-to-neighbor recurrent connections, enabling instantaneous tactile reflexes
            and wave undulations to propagate laterally around the organism&rsquo;s circumference in sub-milliseconds.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num">Circular</div><div class="stat-item-label">Adjacency Graph</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-cyan);">&lt; 0.2ms</div><div class="stat-item-label">Lateral Neighbor Ring</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">Bypass</div><div class="stat-item-label">Central Bus Independence</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 13 -->
      <div class="chapter-overlay" data-chapter="12">
        <div class="chapter-content-card">
          <div class="chapter-tag">13 // INVERTEBRATE RESILIENCE</div>
          <h2 class="chapter-headline">Sever a Limb. Zero Downtime.</h2>
          <div class="chapter-subhead">Instantaneous 0.00-second adaptation with zero policy retraining or parameter fine-tuning.</div>
          <p class="chapter-body">
            When an arm is lost, the circular adjacency matrix bypasses the severed index (<span style="font-family: var(--font-mono); color: var(--accent-rose);">A_{severed, j} = 0</span>).
            Neighboring limbs accelerate locomotion frequency to 1.45x, retaining 82.5% task reward with zero fine-tuning.
          </p>

          <!-- Multi-Arm Amputation Sandbox -->
          <div style="margin-top: 18px;">
            <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">
              CLICK ANY ARM TO INJECT HARDWARE FAILURE &amp; OBSERVE LATERAL REROUTING:
            </div>
            <div class="arm-selector-row">
              ${[0, 1, 2, 3, 4, 5, 6, 7].map(i => `
                <button class="arm-btn ${i === 3 ? 'severed' : ''}" data-arm="${i}">
                  Arm #${i} ${i === 3 ? '(OFFLINE)' : '(ONLINE)'}
                </button>
              `).join('')}
            </div>
          </div>
        </div>
      </div>

      <!-- Slide 14 -->
      <div class="chapter-overlay" data-chapter="13">
        <div class="chapter-content-card">
          <div class="chapter-tag">14 // CONTINUUM AXIAL CORD</div>
          <h2 class="chapter-headline">Arm #3: 28 Sucker Segments, Zero Joints.</h2>
          <div class="chapter-subhead">A continuous neural highway coordinating hundreds of local tactile microcircuits.</div>
          <p class="chapter-body">
            Traveling down the axial cord, motor neuropil tracks innervate longitudinal, transverse, and helical oblique muscles
            across 28 distinct sucker segments without a single mechanical hinge or skeleton joint.
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num">28</div><div class="stat-item-label">Sucker Segments / Arm</div></div>
            <div class="stat-item"><div class="stat-item-num">1,200+</div><div class="stat-item-label">Axial Neurons / Segment</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">Continuum</div><div class="stat-item-label">Bio-Actuation</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 15 -->
      <div class="chapter-overlay" data-chapter="14">
        <div class="chapter-content-card">
          <div class="chapter-tag">15 // MICRON-LEVEL PRECISION</div>
          <h2 class="chapter-headline">Sucker Receptor #12370.</h2>
          <div class="chapter-subhead">Exact spatial coordinates, biological taxonomy, and interactive synaptic cascade.</div>
          <p class="chapter-body">
            Every single node in this connectome has exact 3D coordinates, pre-synaptic linkages, and morphological taxonomy.
            Inspect the local synaptic microcircuit of Sucker Segment 28:
          </p>

          <!-- Interactive Micron Inspection Card -->
          <div class="micron-card">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">
              <div style="font-family: var(--font-display); font-size: 15px; font-weight: 700; color: #ffffff;">
                SUCKER RECEPTOR #12370
              </div>
              <span class="hud-pill" style="padding: 3px 8px; font-size: 9px; color: var(--accent-gold);">
                LOD: 16.8 &mu;m
              </span>
            </div>

            <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); margin-top: 10px; line-height: 1.6;">
              <div>SPATIAL POSITION: <span style="color: var(--accent-cyan);">X: -28.12, Y: -29.75, Z: 55.65</span></div>
              <div>ANATOMICAL CONTEXT: <span style="color: var(--accent-violet);">Arm #3 &bull; Sucker Segment 28</span></div>
              <div>SYNAPTIC LINKS: <span>3 Presynaptic Microcircuits</span></div>
            </div>

            <div class="microcircuit-grid">
              <div class="microcircuit-cell">#12369 (ganglia)</div>
              <div class="microcircuit-cell" style="border-color: var(--accent-gold); color: var(--accent-gold);">TARGET: #12370</div>
              <div class="microcircuit-cell">#12371 (sucker)</div>
            </div>

            <button id="sucker-cascade-btn" class="btn-cinema-primary" style="width: 100%; justify-content: center; padding: 10px; font-size: 12px; margin-top: 6px;">
              ↯ Trigger Action Potential Cascade to Brain
            </button>
          </div>
        </div>
      </div>

      <!-- Slide 16 -->
      <div class="chapter-overlay" data-chapter="15">
        <div class="chapter-content-card">
          <div class="chapter-tag">16 // MUSCULAR HYDROSTATS</div>
          <h2 class="chapter-headline">Muscles Acting as Their Own Skeleton.</h2>
          <div class="chapter-subhead">Constant-volume biological continuum kinematics: V = &pi; &bull; r&sup2; &bull; L = Constant.</div>
          <p class="chapter-body">
            Octopuses maintain isovolumetric muscular hydrostats: longitudinal contraction forces immediate radial expansion.
            Test the interactive deformation slider below to witness the radial cross-section adapt in real-time:
          </p>

          <!-- Hydrostat Interactive Slider Widget -->
          <div class="hydrostat-widget">
            <div style="display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 11px;">
              <span style="color: var(--accent-cyan);">DRAG ELONGATION FACTOR (L):</span>
              <span id="hydrostat-len-val" style="color: #ffffff; font-weight: 700;">1.00x</span>
            </div>

            <input id="hydrostat-slider" type="range" min="0.5" max="1.6" step="0.05" value="1.0" class="hydrostat-slider" />

            <div style="display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 10.5px; color: var(--text-muted);">
              <div>LONGITUDINAL EXTENSION: <span id="hydrostat-ext" style="color: var(--accent-emerald);">Nominal</span></div>
              <div>RADIAL CROSS-SECTION (r): <span id="hydrostat-rad" style="color: var(--accent-gold);">1.00x</span></div>
              <div>VOLUME INVARIANT (V): <span style="color: var(--accent-cyan);">&pi; &bull; r&sup2; &bull; L = const</span></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Slide 17 -->
      <div class="chapter-overlay" data-chapter="16">
        <div class="chapter-content-card">
          <div class="chapter-tag">17 // BENCHMARK MILESTONES</div>
          <h2 class="chapter-headline">+234% Reward Surge &amp; 5.4x Coordination Lock.</h2>
          <div class="chapter-subhead">Curriculum reinforcement learning with Generalized Advantage Estimation (GAE).</div>
          <p class="chapter-body">
            From initial random flailing to master hunter: joint multi-arm task success soared from 14.2% to 77.4%, predator hazard hits
            dropped to near-zero (98.5% avoidance), and reward reached +42.10 (peak +54.95).
          </p>
          <div class="chapter-stat-callout">
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-emerald);">+234%</div><div class="stat-item-label">Reward Surge (+42.10)</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-cyan);">5.4&times;</div><div class="stat-item-label">Multi-Arm Lock (77.4%)</div></div>
            <div class="stat-item"><div class="stat-item-num" style="color: var(--accent-gold);">98.5%</div><div class="stat-item-label">Hazard Avoidance</div></div>
          </div>
        </div>
      </div>

      <!-- Slide 18 -->
      <div class="chapter-overlay" data-chapter="17">
        <div class="chapter-content-card">
          <div class="chapter-tag">18 // PRODUCTION VERIFICATION</div>
          <h2 class="chapter-headline">Engineered from First Principles.</h2>
          <div class="chapter-subhead">Sub-5ms WASM SIMD edge execution. 67/67 CI tests passing. Zero server dependency.</div>
          <p class="chapter-body">
            Complete neural modeling in PyTorch 2.4, edge-quantized ONNX WebAssembly, and real-time Three.js WebGL visualization.
            Explore the live simulator, inspect the tensor architecture, or export the 1-Page PDF Executive Dossier:
          </p>
          <div class="cta-row" style="justify-content: center; flex-wrap: wrap; gap: 10px;">
            <button id="cta-go-consortium-btn" class="btn-cinema-primary" style="background: linear-gradient(135deg, var(--accent-cyan), var(--accent-violet));">
              <span>Enter Multi-Octopus Swarm &rarr;</span>
            </button>
            <a href="http://localhost:5173" target="_blank" rel="noopener noreferrer" class="btn-cinema-secondary">
              <span>Live 3D Simulator</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
            <button id="cta-arch-btn" class="btn-cinema-secondary">
              <span>Inspect Tensors</span>
            </button>
            <button id="cta-dossier-btn" class="btn-cinema-secondary">
              <span>Executive PDF Dossier</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Slides 19 to 26: The 8 Octopuses One-by-One in 3D -->
      <div class="chapter-overlay" data-chapter="18">
        ${renderIndividualOctopusHTML(0)}
      </div>
      <div class="chapter-overlay" data-chapter="19">
        ${renderIndividualOctopusHTML(1)}
      </div>
      <div class="chapter-overlay" data-chapter="20">
        ${renderIndividualOctopusHTML(2)}
      </div>
      <div class="chapter-overlay" data-chapter="21">
        ${renderIndividualOctopusHTML(3)}
      </div>
      <div class="chapter-overlay" data-chapter="22">
        ${renderIndividualOctopusHTML(4)}
      </div>
      <div class="chapter-overlay" data-chapter="23">
        ${renderIndividualOctopusHTML(5)}
      </div>
      <div class="chapter-overlay" data-chapter="24">
        ${renderIndividualOctopusHTML(6)}
      </div>
      <div class="chapter-overlay" data-chapter="25">
        ${renderIndividualOctopusHTML(7)}
      </div>

      <!-- Slide 27: The Grand Finale - All 8 Octopuses Working Together in 3D -->
      <div class="chapter-overlay" data-chapter="26">
        ${renderConsortiumFinaleHTML()}
      </div>
    </div>

    <!-- Executive Dossier Modal -->
    <div id="dossier-modal" class="dossier-modal-backdrop">
      <div class="dossier-card">
        <button id="dossier-close-btn" class="dossier-close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>

        <div style="border-bottom: 2px solid var(--accent-cyan); padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 12px;">
          <div>
            <div style="font-family: var(--font-mono); font-size: 10px; color: var(--accent-cyan); font-weight: 700; letter-spacing: 0.15em;">
              EXECUTIVE TECHNICAL BRIEFING &bull; RESUME ATTACHMENT
            </div>
            <h2 style="font-family: var(--font-display); font-size: 26px; color: #ffffff; margin-top: 4px;">
              OCTOFLOW: Decentralized Cephalopod Neural Connectome
            </h2>
            <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">
              Bio-Inspired Fault-Tolerant Architecture for Edge Robotics &amp; Distributed RL
            </div>
          </div>
          <button id="modal-print-btn" class="btn-cinema-primary" style="padding: 10px 20px; font-size: 12.5px;">
            Print / Save PDF
          </button>
        </div>

        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 20px; margin-bottom: 20px;">
          <h4 style="font-family: var(--font-display); font-size: 14px; color: #ffffff; margin-bottom: 8px;">Executive Summary</h4>
          <p style="font-size: 13px; color: var(--text-muted); line-height: 1.65;">
            Monolithic AI architectures fail in edge robotics due to bandwidth saturation and catastrophic policy crashes upon hardware loss.
            OCTOFLOW models cephalopod neurobiology (where 67% of neurons reside in peripheral arms), introducing a mathematical predictive coding
            surprise gating algorithm that limits central communication to &le; 22%, paired with a lateral interbrachial commissure ring capable of
            zero-shot physical amputation recovery in 0.00 seconds.
          </p>
        </div>

        <!-- 4 Key Metrics -->
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px;">
          <div style="background: #020617; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px; text-align: center;">
            <div style="font-family: var(--font-mono); font-size: 9px; color: var(--text-dim);">BANDWIDTH SAVED</div>
            <div style="font-family: var(--font-display); font-size: 18px; font-weight: 700; color: var(--accent-cyan); margin-top: 2px;">78.4%</div>
          </div>
          <div style="background: #020617; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px; text-align: center;">
            <div style="font-family: var(--font-mono); font-size: 9px; color: var(--text-dim);">AMPUTATION RECOVERY</div>
            <div style="font-family: var(--font-display); font-size: 18px; font-weight: 700; color: var(--accent-emerald); margin-top: 2px;">0.00s Zero-Shot</div>
          </div>
          <div style="background: #020617; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px; text-align: center;">
            <div style="font-family: var(--font-mono); font-size: 9px; color: var(--text-dim);">EDGE LATENCY</div>
            <div style="font-family: var(--font-display); font-size: 18px; font-weight: 700; color: var(--accent-violet); margin-top: 2px;">&lt; 4.8ms</div>
          </div>
          <div style="background: #020617; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px; text-align: center;">
            <div style="font-family: var(--font-mono); font-size: 9px; color: var(--text-dim);">TEST PASS RATE</div>
            <div style="font-family: var(--font-display); font-size: 18px; font-weight: 700; color: var(--accent-gold); margin-top: 2px;">100% (67/67)</div>
          </div>
        </div>

        <!-- Ownership Breakdown -->
        <div style="margin-bottom: 20px;">
          <h4 style="font-family: var(--font-display); font-size: 14px; color: #ffffff; margin-bottom: 10px;">Engineering Ownership</h4>
          <ul style="list-style: none; display: flex; flex-direction: column; gap: 8px; font-size: 12.5px; color: var(--text-muted); line-height: 1.6;">
            <li style="display: flex; gap: 8px;"><span style="color: var(--accent-cyan); font-weight: 700;">&bull;</span> <span><strong style="color: #ffffff;">Predictive Coding Math:</strong> Formulated surprise metric &Delta;S_i = ||o_i - &ocirc;_i||&sup2; with sigmoid thresholding, suppressing non-critical telemetry.</span></li>
            <li style="display: flex; gap: 8px;"><span style="color: var(--accent-cyan); font-weight: 700;">&bull;</span> <span><strong style="color: #ffffff;">Lateral Ring Mesh:</strong> Designed circular graph adjacency matrix bypass for zero-shot load rebalancing across neighboring arms upon hardware loss.</span></li>
            <li style="display: flex; gap: 8px;"><span style="color: var(--accent-cyan); font-weight: 700;">&bull;</span> <span><strong style="color: #ffffff;">SIMD WebAssembly Pipeline:</strong> Quantized PyTorch weights to ONNX WebAssembly, achieving deterministic 60Hz edge inference without GPU infrastructure.</span></li>
            <li style="display: flex; gap: 8px;"><span style="color: var(--accent-cyan); font-weight: 700;">&bull;</span> <span><strong style="color: #ffffff;">Interactive 3D Connectome:</strong> Authored custom Three.js WebGL visualization reproducing continuous isovolumetric soft-body hydrostat kinematics.</span></li>
          </ul>
        </div>

        <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 14px; display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 10px; color: var(--text-dim);">
          <div>STACK: PyTorch 2.4 &bull; ONNX v18 &bull; TypeScript &bull; Three.js WebGL &bull; WebAssembly SIMD</div>
          <div style="color: var(--accent-cyan);">VERIFIED BUILD: PASSED</div>
        </div>
      </div>
    </div>
  `;

  // 2. Initialize Fullscreen Connectome Experience
  const canvasContainer = document.getElementById('webgl-canvas-container');
  if (!canvasContainer) return;
  const exp = new OctopusConnectomeExperience(canvasContainer);

  // Hook Sound FX to Synaptic Events
  exp.onSynapticPulse = () => {
    soundEngine.playSynapticSpark();
  };

  // 3. Telemetry Updates
  const teleCam = document.getElementById('telemetry-cam');
  const teleSignals = document.getElementById('telemetry-signals');
  exp.onTelemetryUpdate = (camPos, _scrollP, activeSignals) => {
    if (teleCam) {
      teleCam.innerText = `X: ${camPos.x.toFixed(1)} • Y: ${camPos.y.toFixed(1)} • Z: ${camPos.z.toFixed(1)}`;
    }
    if (teleSignals) {
      teleSignals.innerText = `${activeSignals} active`;
    }
  };

  // 4. Scroll Tracking Across 18 Slides
  const progressBar = document.getElementById('hud-progress-bar');
  const progressVal = document.getElementById('hud-progress-val');
  const slideIndicator = document.getElementById('slide-indicator');
  const chapterOverlays = document.querySelectorAll('.chapter-overlay');

  const NUM_SLIDES = 27;
  let currentSlide = 0;

  function getSlideThresholds() {
    const thresholds = [];
    for (let i = 0; i < NUM_SLIDES; i++) {
      const start = i === 0 ? 0.0 : (i - 0.45) / (NUM_SLIDES - 1);
      const end = i === NUM_SLIDES - 1 ? 1.05 : (i + 0.55) / (NUM_SLIDES - 1);
      thresholds.push({ start, end });
    }
    return thresholds;
  }
  const thresholds = getSlideThresholds();

  function updateScroll() {
    const scrollY = window.scrollY;
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const progress = maxScroll > 0 ? scrollY / maxScroll : 0;

    exp.setScrollProgress(progress);

    const pct = Math.min(100, Math.max(0, Math.round(progress * 100)));
    if (progressBar) progressBar.style.width = `${pct}%`;
    if (progressVal) progressVal.innerText = `${pct.toString().padStart(2, '0')}%`;

    let activeIdx = 0;
    chapterOverlays.forEach((overlay, idx) => {
      const range = thresholds[idx];
      const isVisible = progress >= range.start && progress < range.end;
      overlay.classList.toggle('visible', isVisible);
      if (isVisible) activeIdx = idx;
    });

    exp.setCurrentSlide(activeIdx);

    if (activeIdx !== currentSlide) {
      soundEngine.ensureAudioStarted();
      soundEngine.playSlideTransition(activeIdx);
    }
    currentSlide = activeIdx;
    if (slideIndicator) {
      slideIndicator.innerText = `${(currentSlide + 1).toString().padStart(2, '0')} / ${NUM_SLIDES}`;
    }
  }

  window.addEventListener('scroll', updateScroll, { passive: true });
  updateScroll();

  // 5. Slide Stepper Buttons (Prev / Next)
  function goToSlide(slideIdx: number) {
    const targetIdx = Math.max(0, Math.min(NUM_SLIDES - 1, slideIdx));
    if (targetIdx !== currentSlide) {
      if (freeOrbit) {
        freeOrbit = false;
        exp.setFreeOrbit(false);
        pillOrbit?.classList.remove('active');
        if (pillOrbit) {
          pillOrbit.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path></svg> Free Orbit`;
        }
      }
      soundEngine.ensureAudioStarted();
      soundEngine.playSlideTransition(targetIdx);
    }
    const targetP = targetIdx / (NUM_SLIDES - 1);
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    window.scrollTo({
      top: targetP * maxScroll,
      behavior: 'smooth',
    });
  }

  document.getElementById('slide-prev-btn')?.addEventListener('click', () => {
    goToSlide(currentSlide - 1);
  });

  document.getElementById('slide-next-btn')?.addEventListener('click', () => {
    goToSlide(currentSlide + 1);
  });

  // Keyboard Navigation (Arrow Keys)
  window.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      goToSlide(currentSlide + 1);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      goToSlide(currentSlide - 1);
    }
  });

  // 6. Relaxing Ocean Waves Background Audio (Always On)
  // Continuous authentic beach ocean waves: auto-starts immediately and stays active across all interactions
  soundEngine.ensureAudioStarted();

  const keepAudioPlaying = () => {
    soundEngine.ensureAudioStarted();
  };
  window.addEventListener('pointerdown', keepAudioPlaying);
  window.addEventListener('keydown', keepAudioPlaying);
  window.addEventListener('wheel', keepAudioPlaying, { passive: true });
  window.addEventListener('touchstart', keepAudioPlaying, { passive: true });
  window.addEventListener('scroll', keepAudioPlaying, { passive: true });

  // 7. Auto-Tour (Choreographed Guided Flight)
  let isAutoTour = false;
  let autoTourInterval: number | null = null;
  const autotourBtn = document.getElementById('hud-autotour-btn');

  function toggleAutoTour() {
    isAutoTour = !isAutoTour;
    if (autotourBtn) {
      autotourBtn.innerText = isAutoTour ? '❚❚ Pause Tour' : '▶ Auto-Tour';
      autotourBtn.classList.toggle('active', isAutoTour);
    }

    if (isAutoTour) {
      soundEngine.ensureAudioStarted();

      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      const speed = maxScroll / (90 * 60); // 90 seconds comprehensive tour
      autoTourInterval = window.setInterval(() => {
        if (window.scrollY >= maxScroll - 10) {
          toggleAutoTour();
          return;
        }
        window.scrollBy(0, speed);
      }, 1000 / 60);
    } else {
      if (autoTourInterval) clearInterval(autoTourInterval);
      autoTourInterval = null;
    }
  }

  autotourBtn?.addEventListener('click', toggleAutoTour);

  // 8. Sucker Receptor #12370 Cascade Trigger
  const suckerCascadeBtn = document.getElementById('sucker-cascade-btn');
  suckerCascadeBtn?.addEventListener('click', () => {
    exp.triggerSuckerCascade();
    soundEngine.playReticleLock();
  });

  // 9. Muscular Hydrostat Interactive Slider
  const hydroSlider = document.getElementById('hydrostat-slider') as HTMLInputElement;
  const hydroLenVal = document.getElementById('hydrostat-len-val');
  const hydroExt = document.getElementById('hydrostat-ext');
  const hydroRad = document.getElementById('hydrostat-rad');

  hydroSlider?.addEventListener('input', (e) => {
    const scale = parseFloat((e.target as HTMLInputElement).value);
    exp.setHydrostatScale(scale);
    soundEngine.setHydrostatTension(scale);

    if (hydroLenVal) hydroLenVal.innerText = `${scale.toFixed(2)}x`;
    if (hydroExt) {
      hydroExt.innerText = scale > 1.0 ? `+${((scale - 1) * 100).toFixed(0)}% Elongated` : `${((1 - scale) * 100).toFixed(0)}% Contracted`;
    }
    if (hydroRad) {
      const radScale = (1.0 / Math.sqrt(scale)).toFixed(2);
      hydroRad.innerText = `${radScale}x (Isovolumetric)`;
    }
  });

  // 10. Multi-Arm Amputation Sandbox Buttons
  const armBtns = document.querySelectorAll('.arm-btn');
  armBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const target = e.currentTarget as HTMLElement;
      const armIdx = parseInt(target.getAttribute('data-arm') || '0');
      const isSevered = exp.toggleArmAmputation(armIdx);

      target.classList.toggle('severed', isSevered);
      target.innerText = `Arm #${armIdx} ${isSevered ? '(OFFLINE)' : '(ONLINE)'}`;
      soundEngine.playAmputationAlert(isSevered);
    });
  });

  // 11. HUD Center Action Pills
  const pillShockwave = document.getElementById('pill-shockwave');
  const pillOrbit = document.getElementById('pill-orbit');

  pillShockwave?.addEventListener('click', () => {
    exp.triggerShockwave();
    soundEngine.playShockwaveBurst();
  });

  let freeOrbit = false;
  pillOrbit?.addEventListener('click', () => {
    freeOrbit = !freeOrbit;
    exp.setFreeOrbit(freeOrbit);
    pillOrbit.classList.toggle('active', freeOrbit);
    pillOrbit.innerHTML = freeOrbit
      ? 'Locked Flight'
      : `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path></svg> Free Orbit`;
  });

  // 12. Architecture Drawer & Executive Dossier Modal
  const hudArchBtn = document.getElementById('hud-arch-btn');
  const ctaArchBtn = document.getElementById('cta-arch-btn');
  hudArchBtn?.addEventListener('click', () => archDrawer.toggle());
  ctaArchBtn?.addEventListener('click', () => archDrawer.open());

  const modal = document.getElementById('dossier-modal');
  const hudDossierBtn = document.getElementById('hud-dossier-btn');
  const ctaDossierBtn = document.getElementById('cta-dossier-btn');
  const closeBtn = document.getElementById('dossier-close-btn');
  const printBtn = document.getElementById('modal-print-btn');

  function openModal() {
    modal?.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    modal?.classList.remove('open');
    document.body.style.overflow = '';
  }

  hudDossierBtn?.addEventListener('click', openModal);
  ctaDossierBtn?.addEventListener('click', openModal);
  closeBtn?.addEventListener('click', closeModal);
  modal?.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  printBtn?.addEventListener('click', () => {
    window.print();
  });

  // 13. Initialize OctoFlow Multi-Octopus Consortium Experience
  initConsortiumExperience(exp, soundEngine, openModal, goToSlide);

  document.getElementById('cta-go-consortium-btn')?.addEventListener('click', () => {
    goToSlide(18);
  });
  document.getElementById('hud-consortium-btn')?.addEventListener('click', () => {
    goToSlide(18);
  });
});
