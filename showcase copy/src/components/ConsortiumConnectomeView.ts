/**
 * ConsortiumConnectomeView.ts
 * 
 * Interactive Multi-Octopus Swarm & Synaptic Cable Network View.
 * Provides rich dual-morphology presentations for all 8 octopuses (Slides 19-26)
 * covering both Software Engineering and AI/ML Research roles,
 * plus the Grand Finale (Slide 27) showcasing all 8 octopuses working in unison.
 */

import type { OctopusConnectomeExperience } from '../connectome/OctopusConnectomeExperience';
import type { SoundEngine } from '../audio/SoundEngine';

export interface OctopusArmSpec {
  num: number;
  name: string;
  task: string;
  status: string;
}

export interface MorphologySpec {
  roleTitle: string;
  subhead: string;
  description: string;
  arms: OctopusArmSpec[];
  metrics: { label: string; value: string; color: string }[];
  deliverables: string[];
  gatingInfo: string;
}

export interface OctopusSpec {
  id: number;
  numberLabel: string;
  colorHex: string;
  colorInt: number;
  name: string;
  softwareDev: MorphologySpec;
  aimlResearch: MorphologySpec;
}

export const OCTOPUS_SPECS: OctopusSpec[] = [
  // Octopus 1: System Architect (SoftDev) / Data Engineering & ETL (AI/ML)
  {
    id: 0,
    numberLabel: 'OCTOPUS 1',
    name: 'Octo 1',
    colorHex: '#38bdf8',
    colorInt: 0x38bdf8,
    softwareDev: {
      roleTitle: 'System Architect & Schema Topology',
      subhead: 'OpenAPI 3.1 contract locking, Pydantic v2 domain schemas, and async pool initialization.',
      description: 'Orchestrates the macro-architecture and distributed topology, locks deterministic API interface contracts before downstream implementation, and enforces clean boundary decoupling across all services.',
      arms: [
        { num: 1, name: 'OpenAPI 3.1 Spec Generator', task: 'Contract locking & JSON schema export', status: '✓ Locked' },
        { num: 2, name: 'Pydantic v2 Type Validator', task: 'Zero-copy memory parsing & validation', status: '✓ Active' },
        { num: 3, name: 'Asyncio Worker Pool Conductor', task: 'Concurrency pool sizing & life-cycle', status: '✓ Active' },
        { num: 4, name: 'Domain Boundary Enforcer', task: 'Hexagonal clean architecture isolation', status: '✓ Guarded' },
        { num: 5, name: 'Schema Migration Graph Compiler', task: 'Topological DAG dependency resolver', status: '✓ Ready' },
        { num: 6, name: 'Event Bus Schema Registry', task: 'Forward/backward compatibility check', status: '✓ Verified' },
        { num: 7, name: 'Idempotency Token Synthesizer', task: 'Distributed deduplication tokens', status: '✓ Active' },
        { num: 8, name: 'Interface Telemetry Watchdog', task: 'Sub-millisecond protocol health monitor', status: '✓ 0.4ms' },
      ],
      metrics: [
        { label: 'BANDWIDTH SAVED', value: '91.2%', color: 'var(--accent-cyan)' },
        { label: 'GATING THRESHOLD', value: 'θ = 0.45', color: 'var(--accent-emerald)' },
        { label: 'SCHEMA VALIDITY', value: '100% Pass', color: 'var(--accent-violet)' },
        { label: 'INTER-ARM LATENCY', value: '0.4ms', color: 'var(--accent-gold)' },
      ],
      deliverables: ['specs/api_contract.yaml', 'models/domain.py', 'aiosqlite:pool', 'core/topology.py'],
      gatingInfo: 'Local surprise ΔS <= 0.45. Schema reflex quiescent; 0 unnecessary LLM completions burned.',
    },
    aimlResearch: {
      roleTitle: 'Data Engineering & Multi-Modal Dataset Synthesizer',
      subhead: 'Streaming Apache Arrow ingestion, BPE tokenizer calibration, and MinHash LSH deduplication.',
      description: 'Constructs high-throughput ETL data pipelines, purges contamination and duplicates from multi-modal pretraining corpuses, and streams zero-copy columnar batches directly to distributed VRAM buffers.',
      arms: [
        { num: 1, name: 'Corpus Ingestion & Scraping', task: 'Multi-source stream ingestion pipeline', status: '✓ 4.8 GB/s' },
        { num: 2, name: 'MinHash LSH Near-Deduplicator', task: 'Document redundancy & similarity filter', status: '✓ Active' },
        { num: 3, name: 'Byte-Pair Tokenizer Calibration', task: '32k vocabulary entropy optimization', status: '✓ 0.94b' },
        { num: 4, name: 'Apache Arrow & Parquet Serializer', task: 'Zero-copy columnar format serialization', status: '✓ Synced' },
        { num: 5, name: 'Ray Distributed Shuffling Engine', task: 'Out-of-core memory balancer & buffer', status: '✓ Active' },
        { num: 6, name: 'Benchmark Contamination Guard', task: 'N-gram overlap decontamination filter', status: '✓ 100% Clean' },
        { num: 7, name: 'Feature Embedding Extractor', task: 'Multi-modal dense vector representation', status: '✓ Active' },
        { num: 8, name: 'Zero-Copy Streaming DataLoader', task: 'Prefetching NVMe-to-VRAM ring buffer', status: '✓ 0.2ms' },
      ],
      metrics: [
        { label: 'INGESTION RATE', value: '4.8 GB/s', color: 'var(--accent-cyan)' },
        { label: 'VOCAB ENTROPY', value: '0.94 bits', color: 'var(--accent-emerald)' },
        { label: 'DECONTAMINATION', value: '100% Pass', color: 'var(--accent-violet)' },
        { label: 'TOKENS AVOIDED', value: '93.4%', color: 'var(--accent-gold)' },
      ],
      deliverables: ['data/pipeline_etl.py', 'tokenizers/bpe_vocab.json', 'datasets/shard_001.arrow', 'data/decontaminate.py'],
      gatingInfo: 'Sensory gate θ = 0.50 suppresses redundant ETL worker re-allocations.',
    },
  },

  // Octopus 2: Database & Schemas (SoftDev) / Model Architect (AI/ML)
  {
    id: 1,
    numberLabel: 'OCTOPUS 2',
    name: 'Octo 2',
    colorHex: '#34d399',
    colorInt: 0x34d399,
    softwareDev: {
      roleTitle: 'Database Engine & Persistence Specialist',
      subhead: 'ACID compliance, WAL mode concurrency, Alembic migrations, and zero-lock read replicas.',
      description: 'Owns persistent state, executes lossless migration cascades, optimizes B-tree index cardinality, and isolates write-ahead logging for uninterrupted zero-downtime high-throughput transactions.',
      arms: [
        { num: 1, name: 'Relational DDL Generator', task: 'Normalized PostgreSQL & SQLite schemas', status: '✓ DDL Locked' },
        { num: 2, name: 'B-Tree & Hash Index Tuner', task: 'Sub-millisecond query plan optimization', status: '✓ 0.8ms' },
        { num: 3, name: 'Alembic Migration Orchestrator', task: 'Deterministic rollback safe migrations', status: '✓ Synced' },
        { num: 4, name: 'WAL Mode Concurrency Shield', task: 'Zero-lock contention write pipelines', status: '✓ Active' },
        { num: 5, name: 'Connection Pool Gatekeeper', task: 'Adaptive backpressure connection valve', status: '✓ 32 Slots' },
        { num: 6, name: 'Read-Replica Synchronizer', task: 'Consistent eventual replica distribution', status: '✓ 0.0ms Lag' },
        { num: 7, name: 'EXPLAIN ANALYZE Cost Auditor', task: 'AST query cost minimization analysis', status: '✓ Optimal' },
        { num: 8, name: 'Point-in-Time Snapshot Vault', task: 'Cryptographic state integrity backups', status: '✓ Verified' },
      ],
      metrics: [
        { label: 'QUERY LATENCY', value: '0.8ms (p99)', color: 'var(--accent-emerald)' },
        { label: 'LOCK CONTENTION', value: '0.00s Wait', color: 'var(--accent-cyan)' },
        { label: 'SCHEMA DRIFT', value: '0.00%', color: 'var(--accent-violet)' },
        { label: 'REFLEX GATING', value: '87.5% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['alembic/versions/001_core.py', 'db/connection.py', 'db/indices.sql', 'db/wal_config.py'],
      gatingInfo: 'Query plans cached at edge. High-watermark triggers only upon schema drift.',
    },
    aimlResearch: {
      roleTitle: 'Model Architecture & Backbone Engineer',
      subhead: 'FlashAttention-2, SwiGLU activations, Rotary Positional Embeddings, and Sparse MoE.',
      description: 'Formulates the underlying neural network backbone, computes analytical forward passes, stabilizes deep RMSNorm layers, and integrates Sparse Mixture-of-Experts routing for maximum parameter efficiency.',
      arms: [
        { num: 1, name: 'FlashAttention-2 Synthesizer', task: 'O(N) IO-aware attention kernel binding', status: '✓ 2.4x Speed' },
        { num: 2, name: 'Rotary Position Embedding (RoPE)', task: '128k long-context extrapolation grid', status: '✓ 128k Len' },
        { num: 3, name: 'SwiGLU Non-Linear FeedForward', task: 'Gated dimensional expansion blocks', status: '✓ Active' },
        { num: 4, name: 'Sparse MoE Top-K Router', task: 'Auxiliary load-balanced expert gating', status: '✓ 8 Experts' },
        { num: 5, name: 'RMSNorm Gradient Stabilizer', task: 'Pre-norm vanishing prevention filters', status: '✓ Stable' },
        { num: 6, name: 'Paged KV-Cache Architecture', task: 'Zero-fragmentation ring memory buffer', status: '✓ Active' },
        { num: 7, name: 'Orthogonal SVD Initializer', task: 'Isotropic singular value weight seeding', status: '✓ Verified' },
        { num: 8, name: 'Residual Highway Balancer', task: 'Identity skip-connection dynamic scaling', status: '✓ 1.0 Norm' },
      ],
      metrics: [
        { label: 'CONTEXT WINDOW', value: '128k Tokens', color: 'var(--accent-emerald)' },
        { label: 'ATTENTION BOOST', value: '2.4x Flash', color: 'var(--accent-cyan)' },
        { label: 'ROUTING LOSS', value: '< 0.002', color: 'var(--accent-violet)' },
        { label: 'TOKEN GATING', value: '89.0% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['models/backbone.py', 'layers/flash_attention.py', 'layers/moe_router.py', 'config/model_cfg.yaml'],
      gatingInfo: 'Architecture search evaluates latent gradients locally without LLM re-prompting.',
    },
  },

  // Octopus 3: Backend API & Auth (SoftDev) / Training & Loss Loop (AI/ML)
  {
    id: 2,
    numberLabel: 'OCTOPUS 3',
    name: 'Octo 3',
    colorHex: '#c084fc',
    colorInt: 0xc084fc,
    softwareDev: {
      roleTitle: 'Backend API & Authentication Engine',
      subhead: 'FastAPI/Starlette routing, sliding-window JWT sessions, and RBAC permission guards.',
      description: 'Serves high-throughput asynchronous REST and WebSocket channels, validates cryptographically signed session payloads, and protects routes with adaptive leaky-bucket rate limiting.',
      arms: [
        { num: 1, name: 'Asynchronous Route Handler', task: 'High-concurrency IO request dispatching', status: '✓ 1.4ms' },
        { num: 2, name: 'Sliding-Window JWT Vault', task: 'HMAC cryptographic token verification', status: '✓ Signed' },
        { num: 3, name: 'Role-Based Access Control (RBAC)', task: 'Fine-grained permission evaluation matrix', status: '✓ Active' },
        { num: 4, name: 'Leaky-Bucket Rate Limiter', task: 'Token-bucket DDoS & surge suppression', status: '✓ Gated' },
        { num: 5, name: 'Starlette WebSocket Gateway', task: 'Duplex persistent stream pubsub fanout', status: '✓ Streaming' },
        { num: 6, name: 'Request Payload Sanitizer', task: 'Schema coercion & payload bounds checking', status: '✓ Clean' },
        { num: 7, name: 'Unified Error Interceptor', task: 'RFC 7807 problem details formatting', status: '✓ Handled' },
        { num: 8, name: 'Distributed Trace Injector', task: 'OpenTelemetry span propagation headers', status: '✓ Spanning' },
      ],
      metrics: [
        { label: 'ENDPOINT LATENCY', value: '1.4ms (p95)', color: 'var(--accent-violet)' },
        { label: 'AUTH OVERHEAD', value: '0.15ms', color: 'var(--accent-cyan)' },
        { label: 'WEBSOCKET JITTER', value: '< 0.3ms', color: 'var(--accent-emerald)' },
        { label: 'REFLEX GATING', value: '85.3% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['api/routes.py', 'api/auth.py', 'middleware/rate_limit.py', 'ws/broker.py'],
      gatingInfo: 'Local token validation avoids upstream database hits for 98.4% of API traffic.',
    },
    aimlResearch: {
      roleTitle: 'Distributed Training & Loss Loop Engine',
      subhead: 'PyTorch FSDP, DeepSpeed ZeRO-3, Mixed Precision (BF16), and Gradient Clipping.',
      description: 'Drives multi-GPU distributed training clusters, manages optimizer states across ZeRO stages, balances loss objectives, and intercepts numerical anomalies automatically.',
      arms: [
        { num: 1, name: 'PyTorch FSDP Sharder', task: 'Zero-redundancy parameter sharding', status: '✓ Sharded' },
        { num: 2, name: 'DeepSpeed ZeRO-3 Shielder', task: 'Layer-by-layer weight offload & prefetch', status: '✓ Active' },
        { num: 3, name: 'Auto Mixed Precision (BF16)', task: 'Dynamic loss scale adjustment & cast', status: '✓ BF16' },
        { num: 4, name: 'Multi-Task Loss Objective', task: 'Curriculum-weighted loss sum calculator', status: '✓ Converging' },
        { num: 5, name: 'Cosine Annealing LR Scheduler', task: 'Warmup with minimum floor decay schedule', status: '✓ Step 4.2k' },
        { num: 6, name: 'Adaptive Gradient Norm Clipper', task: '||g|| <= 1.0 explosion guard threshold', status: '✓ < 0.85' },
        { num: 7, name: 'Sharded Checkpoint Writer', task: 'Distributed asynchronous state dump', status: '✓ Checkpoint' },
        { num: 8, name: 'NaN / Inf Loss Watchdog', task: 'Auto-revert to safe step on spike', status: '✓ 0 Spikes' },
      ],
      metrics: [
        { label: 'MFU EFFICIENCY', value: '56.8%', color: 'var(--accent-violet)' },
        { label: 'TRAINING SPEED', value: '1,420 tok/s/GPU', color: 'var(--accent-emerald)' },
        { label: 'GRADIENT STABILITY', value: '100% NaN Free', color: 'var(--accent-cyan)' },
        { label: 'COMPUTE GATING', value: '94.1% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['train/train_fsdp.py', 'train/loss_engine.py', 'train/lr_scheduler.py', 'checkpoints/opt_state.pt'],
      gatingInfo: 'Numerical anomalies handled by local reflex rollback without stopping the cluster.',
    },
  },

  // Octopus 4: Frontend UI (SoftDev) / Evaluation & Benchmark (AI/ML)
  {
    id: 3,
    numberLabel: 'OCTOPUS 4',
    name: 'Octo 4',
    colorHex: '#f43f5e',
    colorInt: 0xf43f5e,
    softwareDev: {
      roleTitle: 'Frontend UI & Realtime Client Client',
      subhead: 'Reactive TypeScript components, 60fps WebGL canvas bridge, and glassmorphic HUDs.',
      description: 'Crafts cinematic human-in-the-loop interfaces, binds high-frequency telemetry streams to Three.js canvas shaders, and ensures zero layout shift under extreme event loads.',
      arms: [
        { num: 1, name: 'Reactive Component Core', task: 'Microsecond state-to-DOM reconciler', status: '✓ 60fps' },
        { num: 2, name: 'Three.js Canvas Bridge', task: '60fps render loop synchronization', status: '✓ Synced' },
        { num: 3, name: 'WebSocket Event Buffer', task: 'Packet ingestion queue & throttler', status: '✓ 0 Drops' },
        { num: 4, name: 'VisionOS Glassmorphism Engine', task: 'Backdrop-filter CSS token architecture', status: '✓ Active' },
        { num: 5, name: 'Deterministic Timeline Store', task: 'State travel & action replay buffer', status: '✓ 128 History' },
        { num: 6, name: 'Zero-Layout-Shift DOM Patch', task: 'Virtual reflow isolation & containment', status: '✓ 0.000 CLS' },
        { num: 7, name: 'Keyboard Command Matrix', task: 'Accessibility & focus trapping controller', status: '✓ Accessible' },
        { num: 8, name: 'Frame Budget Guard', task: 'Dynamic level-of-detail auto-scaler', status: '✓ < 16.6ms' },
      ],
      metrics: [
        { label: 'RENDER FRAME RATE', value: '60.0 fps', color: 'var(--accent-rose)' },
        { label: 'LAYOUT SHIFT', value: '0.000 CLS', color: 'var(--accent-cyan)' },
        { label: 'INPUT LATENCY', value: '< 4.2ms', color: 'var(--accent-emerald)' },
        { label: 'GATING EFFICIENCY', value: '88.2% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['src/components/Dashboard.tsx', 'ws/feed.ts', 'styles/theme.css', 'ui/canvas_bridge.ts'],
      gatingInfo: 'UI state updates batch locally in RequestAnimationFrame; only user actions emit upstream.',
    },
    aimlResearch: {
      roleTitle: 'Evaluation & Benchmark Suite Specialist',
      subhead: 'MMLU, GSM8k, HumanEval evaluation pipelines, LLM-as-a-judge Elo scoring.',
      description: 'Subjects models to automated rigorous empirical benchmarks, detects hallucinations, plots Pareto frontiers across latency vs perplexity, and computes statistical confidence intervals.',
      arms: [
        { num: 1, name: 'Multi-Task Reasoning Evaluator', task: 'MMLU benchmark harness execution', status: '✓ 82.4% MMLU' },
        { num: 2, name: 'Math Multi-Step Engine', task: 'GSM8k chain-of-thought verification', status: '✓ 79.1% GSM' },
        { num: 3, name: 'Code Generation Sandbox', task: 'HumanEval pass@1 execution sandbox', status: '✓ 84.2% Code' },
        { num: 4, name: 'Pairwise Elo Matrix Evaluator', task: 'Double-blind model ranking matrix', status: '✓ 1,280 Elo' },
        { num: 5, name: 'Hallucination & Factuality Guard', task: 'Context grounding & citation verifier', status: '✓ r = 0.94' },
        { num: 6, name: 'Pareto Frontier Optimizer', task: 'Latency vs perplexity tradeoff solver', status: '✓ Optimal' },
        { num: 7, name: 'Adversarial Stress Test Suite', task: 'Red-teaming jailbreak prompt suites', status: '✓ Defended' },
        { num: 8, name: 'LaTeX & SVG Report Generator', task: 'Publication-grade metric chart outputs', status: '✓ Exported' },
      ],
      metrics: [
        { label: 'HUMANEVAL PASS@1', value: '84.2%', color: 'var(--accent-rose)' },
        { label: 'FACTUALITY CORR', value: 'r = 0.94', color: 'var(--accent-emerald)' },
        { label: 'EVAL THROUGHPUT', value: '500 q/min', color: 'var(--accent-cyan)' },
        { label: 'TOKEN GATING', value: '90.7% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['eval/benchmark_suite.py', 'eval/leaderboard.json', 'eval/pareto_plot.svg', 'eval/factuality.py'],
      gatingInfo: 'Syntactic and exact-match verification skips calling judge models for obvious outputs.',
    },
  },

  // Octopus 5: State & Caching (SoftDev) / HPO & Architecture Search (AI/ML)
  {
    id: 4,
    numberLabel: 'OCTOPUS 5',
    name: 'Octo 5',
    colorHex: '#facc15',
    colorInt: 0xfacc15,
    softwareDev: {
      roleTitle: 'State, Caching & Message Queue Specialist',
      subhead: 'In-memory Redis PubSub, ephemeral ring buffers, and backpressure rate-matching.',
      description: 'Maintains low-latency distributed memory, decouples inter-service communication with Redis PubSub topics, and enforces strict TTL eviction to prevent memory bloat.',
      arms: [
        { num: 1, name: 'Redis Cluster Key Manager', task: 'Hash slot partitioning & failover', status: '✓ 16k Slots' },
        { num: 2, name: 'PubSub Fanout Multiplexer', task: 'Sub-millisecond topic broadcast fanout', status: '✓ 0.08ms' },
        { num: 3, name: 'Circular Telemetry Ring Buffer', task: 'Fixed-memory metrics storage ring', status: '✓ 64MB Cap' },
        { num: 4, name: 'Sliding Deduplication Engine', task: 'Idempotent message filter window', status: '✓ Filtered' },
        { num: 5, name: 'Reactive Backpressure Throttler', task: 'Consumer speed load balancer valve', status: '✓ Balanced' },
        { num: 6, name: 'TTL & LRU Eviction Sentinel', task: 'Deterministic memory reclamation daemon', status: '✓ Clean' },
        { num: 7, name: 'Distributed Redlock Coordinator', task: 'Multi-node mutual exclusion lock manager', status: '✓ Locked' },
        { num: 8, name: 'Zero-Copy MsgPack Serializer', task: 'Compact binary packet encoder/decoder', status: '✓ Fast' },
      ],
      metrics: [
        { label: 'CACHE HIT RATIO', value: '99.2%', color: 'var(--accent-gold)' },
        { label: 'SERIALIZATION', value: '0.08ms', color: 'var(--accent-cyan)' },
        { label: 'MEMORY CEILING', value: '< 128MB Fixed', color: 'var(--accent-emerald)' },
        { label: 'REFLEX GATING', value: '86.9% Saved', color: 'var(--accent-violet)' },
      ],
      deliverables: ['cache/store.py', 'mq/broker.py', 'mq/backpressure.py', 'cache/redlock.py'],
      gatingInfo: 'Local cache hit directly terminates request; only cold misses escalate to upstream services.',
    },
    aimlResearch: {
      roleTitle: 'Hyperparameter Optimization & Architecture Search',
      subhead: 'Bayesian optimization with Optuna TPE, Population-Based Training, and pruning.',
      description: 'Explores hyperparameter topologies, automatically prunes unpromising training trials, searches learning rate schedules, and plots multi-objective Pareto hypervolumes.',
      arms: [
        { num: 1, name: 'Bayesian TPE Sampler', task: 'Tree-structured Parzen Estimator loop', status: '✓ 4.6x Faster' },
        { num: 2, name: 'Population-Based Training (PBT)', task: 'Dynamic weight mutation & exploitation', status: '✓ Active' },
        { num: 3, name: 'Median Early Stopping Pruner', task: 'Unpromising trial termination sentinel', status: '✓ Pruned' },
        { num: 4, name: 'LR & Batch Grid Explorer', task: 'Logarithmic learning rate searcher', status: '✓ Optimal' },
        { num: 5, name: 'Weight Decay & Dropout Tuner', task: 'Overfitting regularizer parameter scan', status: '✓ 0.01 wd' },
        { num: 6, name: 'Multi-Objective Hypervolume', task: 'Accuracy + latency simultaneous solver', status: '✓ 0.892 HV' },
        { num: 7, name: 'Checkpoint Garbage Collector', task: 'Failed trial storage purge manager', status: '✓ Purged' },
        { num: 8, name: 'Parameter Sensitivity Engine', task: 'Hyperparameter influence graph plotter', status: '✓ Mapped' },
      ],
      metrics: [
        { label: 'SEARCH SPEEDUP', value: '4.6x vs Random', color: 'var(--accent-gold)' },
        { label: 'COMPUTE WASTED', value: '< 3.5%', color: 'var(--accent-emerald)' },
        { label: 'HYPERVOLUME', value: '0.892', color: 'var(--accent-cyan)' },
        { label: 'GATING SAVED', value: '92.3% Tokens', color: 'var(--accent-violet)' },
      ],
      deliverables: ['hpo/optuna_study.py', 'hpo/best_params.yaml', 'hpo/pbt_mutator.py', 'hpo/sensitivity.json'],
      gatingInfo: 'Pruning threshold halts bad training runs automatically on step 100 without manual checks.',
    },
  },

  // Octopus 6: QA & Test Harness (SoftDev) / Model Quantization & ONNX (AI/ML)
  {
    id: 5,
    numberLabel: 'OCTOPUS 6',
    name: 'Octo 6',
    colorHex: '#fb923c',
    colorInt: 0xfb923c,
    softwareDev: {
      roleTitle: 'QA Test Harness & Concurrency Suite Specialist',
      subhead: 'Pytest async runners, high-concurrency stress fixtures, and invariant assertions.',
      description: 'Subjects the codebase to unrelenting automated verification, simulates network latency drops, catches race conditions, and guarantees 100% contract compliance.',
      arms: [
        { num: 1, name: 'Async Pytest Runner', task: 'Parallel test execution test harness', status: '✓ 67/67 Pass' },
        { num: 2, name: 'Concurrency Stress Simulator', task: '500 simultaneous socket clients fixture', status: '✓ 500 Clients' },
        { num: 3, name: 'Invariant Mutation Testing', task: 'Fault injection & assertion integrity audit', status: '✓ 100% Valid' },
        { num: 4, name: 'Flaky Test Quarantine Watchdog', task: 'Statistical retry & flakiness detector', status: '✓ 0 Flakes' },
        { num: 5, name: 'Chaos Latency Injector', task: 'Simulated jitter and 15% packet loss', status: '✓ Resilient' },
        { num: 6, name: 'Differential Coverage Scanner', task: 'AST branch coverage delta scanner', status: '✓ 96.4%' },
        { num: 7, name: 'API Schema Contract Verifier', task: 'OpenAPI schema regression boundary guard', status: '✓ Verified' },
        { num: 8, name: 'Root Cause Failure Isolator', task: 'Automated traceback minimizer & diff', status: '✓ Isolated' },
      ],
      metrics: [
        { label: 'TEST SUITE PASS', value: '100% (67/67)', color: 'var(--accent-gold)' },
        { label: 'SUITE RUNTIME', value: '1.8s Parallel', color: 'var(--accent-cyan)' },
        { label: 'BRANCH COVERAGE', value: '96.4%', color: 'var(--accent-emerald)' },
        { label: 'REFLEX GATING', value: '84.8% Saved', color: 'var(--accent-violet)' },
      ],
      deliverables: ['tests/test_stress.py', 'tests/conftest.py', 'tests/test_contracts.py', 'tests/chaos.py'],
      gatingInfo: 'Unmodified files skipped via AST hash cache; tests run only on modified dependency subgraph.',
    },
    aimlResearch: {
      roleTitle: 'Model Quantization, ONNX & Edge Compilation Specialist',
      subhead: 'INT8 SmoothQuant, Activation-Aware Weight Quantization (AWQ), and WebAssembly SIMD.',
      description: 'Compresses high-parameter neural models into edge-executable binaries, quantizes weights to INT8/FP4 with minimal perplexity degradation, and compiles WASM SIMD kernels.',
      arms: [
        { num: 1, name: 'PyTorch to ONNX Exporter', task: 'Operator fusion & constant folding graph', status: '✓ Exported' },
        { num: 2, name: 'AWQ Weight Quantizer', task: 'Salient weight preservation algorithms', status: '✓ INT4/INT8' },
        { num: 3, name: 'INT8 SmoothQuant Calibrator', task: 'Outlier activation scale balancing', status: '✓ Calibrated' },
        { num: 4, name: 'FP4 / NF4 Micro-Kernel Optimizer', task: 'Sub-byte matrix multiplication kernels', status: '✓ Active' },
        { num: 5, name: 'WebAssembly SIMD Compiler', task: 'Deterministic edge browser runtime code', status: '✓ 3.2ms SIMD' },
        { num: 6, name: 'TensorRT Engine Serializer', task: 'GPU hardware kernel compilation engine', status: '✓ Optimized' },
        { num: 7, name: 'Per-Layer Quantization Profiler', task: 'Layerwise Signal-to-Noise Ratio check', status: '✓ > 38dB' },
        { num: 8, name: 'Edge Hardware Benchmark Suite', task: 'Mobile & CPU execution profiler metrics', status: '✓ Verified' },
      ],
      metrics: [
        { label: 'SIZE REDUCTION', value: '4.1x Smaller', color: 'var(--accent-gold)' },
        { label: 'PPL DEGRADATION', value: '< 0.08 PPL', color: 'var(--accent-emerald)' },
        { label: 'EDGE INFERENCE', value: '3.2ms (SIMD)', color: 'var(--accent-cyan)' },
        { label: 'COMPUTE GATING', value: '91.5% Saved', color: 'var(--accent-violet)' },
      ],
      deliverables: ['quant/export_onnx.py', 'quant/awq_int8.py', 'models/weights_simd.wasm', 'quant/calibration.json'],
      gatingInfo: 'Quantization calibration runs on fixed synthetic tensors without burning external API tokens.',
    },
  },

  // Octopus 7: Security & AST Audit (SoftDev) / Inference Serving & Gateway (AI/ML)
  {
    id: 6,
    numberLabel: 'OCTOPUS 7',
    name: 'Octo 7',
    colorHex: '#e11d48',
    colorInt: 0xe11d48,
    softwareDev: {
      roleTitle: 'Security & Outbound AST Audit Specialist',
      subhead: 'Zero-leak secret quarantine, AST security scanning, and cryptographic receipt generator.',
      description: 'Acts as the impenetrable immune system of the swarm, quarantines credentials before outbound transmission, audits Python AST for dangerous primitives, and signs receipts.',
      arms: [
        { num: 1, name: 'Outbound Secret Sanitizer', task: '12 credential regex patterns quarantine', status: '✓ Zero-Leak' },
        { num: 2, name: 'Python AST Node Inspector', task: 'exec/eval/system primitive lockdown', status: '✓ 0 Violations' },
        { num: 3, name: 'Prompt Injection Defense', task: 'Adversarial jailbreak pattern detector', status: '✓ Guarded' },
        { num: 4, name: 'HMAC Signature Validator', task: 'Cryptographic message integrity signers', status: '✓ SHA-256' },
        { num: 5, name: 'Dependency CVE Scanner', task: 'Supply chain CVE checker & alert daemon', status: '✓ 0 High' },
        { num: 6, name: 'Sandbox Isolation Enforcer', task: 'System call confinement & jail barrier', status: '✓ Sandboxed' },
        { num: 7, name: 'Cryptographic Proof Generator', task: 'SHA-256 verifiable audit receipts', status: '✓ Signed' },
        { num: 8, name: 'Security Quarantine Vault', task: 'Malicious payload containment vault', status: '✓ Active' },
      ],
      metrics: [
        { label: 'SECRET LEAK RATE', value: '0.00% Zero', color: 'var(--accent-rose)' },
        { label: 'AST SCAN TIME', value: '< 0.2ms', color: 'var(--accent-cyan)' },
        { label: 'CVE HAZARDS', value: '0 High / 0 Crit', color: 'var(--accent-emerald)' },
        { label: 'REFLEX GATING', value: '96.2% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['security/sanitizer.py', 'security/ast_guard.py', 'audit/receipt.json', 'security/hmac_auth.py'],
      gatingInfo: 'Deterministic AST rules handle 99.8% of checks locally; zero LLM token cost for security checks.',
    },
    aimlResearch: {
      roleTitle: 'Inference Serving, Speculative Decoding & Gateway Specialist',
      subhead: 'Continuous batching with vLLM/SGLang, speculative decoding, and PagedAttention.',
      description: 'Hosts production-scale LLM inference, implements speculative decoding with lightweight draft models, manages GPU VRAM with PagedAttention, and streams tokens over WebSockets.',
      arms: [
        { num: 1, name: 'Continuous Batching Engine', task: 'vLLM / SGLang dynamic scheduler queue', status: '✓ 3.8k tok/s' },
        { num: 2, name: 'Speculative Decoding Verifier', task: 'Draft model multi-token verification', status: '✓ 2.3x Boost' },
        { num: 3, name: 'PagedAttention Allocator', task: 'Zero VRAM fragmentation block memory', status: '✓ 98% VRAM' },
        { num: 4, name: 'Radix Attention Prefix Cache', task: 'System prompt reuse tree optimization', status: '✓ 84% Hit' },
        { num: 5, name: 'Tensor Parallel Router', task: 'Multi-GPU all-reduce synchronization', status: '✓ 4-Way TP' },
        { num: 6, name: 'Dynamic Temperature Sampler', task: 'Top-P, Min-P & Mirostat token selector', status: '✓ Calibrated' },
        { num: 7, name: 'Streaming WebSocket Gateway', task: 'Sub-millisecond token stream broadcaster', status: '✓ Stream' },
        { num: 8, name: 'TTFT Latency Profiler', task: 'Time-To-First-Token performance tracker', status: '✓ 18ms TTFT' },
      ],
      metrics: [
        { label: 'THROUGHPUT', value: '3,850 tok/s', color: 'var(--accent-rose)' },
        { label: 'TTFT LATENCY', value: '18ms', color: 'var(--accent-cyan)' },
        { label: 'SPECULATIVE BOOST', value: '2.3x Faster', color: 'var(--accent-emerald)' },
        { label: 'TOKEN GATING', value: '93.8% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['serving/vllm_engine.py', 'serving/speculative_decode.py', 'serving/prefix_cache.py', 'serving/stream_gateway.py'],
      gatingInfo: 'Draft model speculative acceptance criteria filters redundant large-model calls.',
    },
  },

  // Octopus 8: DevOps & Ignition (SoftDev) / ML Governance (AI/ML)
  {
    id: 7,
    numberLabel: 'OCTOPUS 8',
    name: 'Octo 8',
    colorHex: '#60a5fa',
    colorInt: 0x60a5fa,
    softwareDev: {
      roleTitle: 'DevOps, CI/CD & Live Ignition Specialist',
      subhead: 'Zero-downtime Uvicorn orchestration, minimal Docker builds, and automated canaries.',
      description: 'Ignites and supervises production services, builds hardened minimal scratch containers, configures health probes, and executes instantaneous canary rollbacks upon error detection.',
      arms: [
        { num: 1, name: 'Daemon Process Supervisor', task: 'Zero-downtime Uvicorn reload conductor', status: '✓ Running' },
        { num: 2, name: 'Docker Multi-Stage Builder', task: 'Minimal < 45MB scratch container images', status: '✓ 38 MB' },
        { num: 3, name: 'Ephemeral Socket Allocator', task: 'Conflict-free socket & port allocation', status: '✓ Bound' },
        { num: 4, name: 'Liveness & Readiness Probes', task: 'Automated heartbeat health monitor checks', status: '✓ Healthy' },
        { num: 5, name: 'Canary Rollback Watchdog', task: 'Sub-second incident canary rollback', status: '✓ 0.4s Rollback' },
        { num: 6, name: 'Fluent Bit Log Shipper', task: 'Structured JSON log streaming shipper', status: '✓ Shipping' },
        { num: 7, name: 'GitHub Actions CI Pipeline', task: 'Automated build, test and deploy checks', status: '✓ 100% Green' },
        { num: 8, name: 'Production Traffic Switcher', task: 'Blue/Green zero-interruption diverter', status: '✓ Active' },
      ],
      metrics: [
        { label: 'DEPLOY DOWNTIME', value: '0.00s Zero', color: 'var(--accent-cyan)' },
        { label: 'CONTAINER SIZE', value: '38 MB', color: 'var(--accent-emerald)' },
        { label: 'ROLLBACK TIME', value: '< 0.4s', color: 'var(--accent-violet)' },
        { label: 'REFLEX GATING', value: '88.0% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['deploy/Dockerfile', 'deploy/supervisor.py', '.github/workflows/ci.yml', 'deploy/probes.py'],
      gatingInfo: 'Health probes run on local TCP pings without calling AI models or cloud APIs.',
    },
    aimlResearch: {
      roleTitle: 'ML Governance, Model Registry & Provenance Specialist',
      subhead: 'MLflow experiment tracking, automated model cards, and dataset lineage DAGs.',
      description: 'Maintains complete audit trails and regulatory provenance for all weights and datasets, detects semantic distribution shift, and generates verifiable compliance documentation.',
      arms: [
        { num: 1, name: 'MLflow & WandB Tracker', task: 'Run metrics, weights and artifact logger', status: '✓ Logged' },
        { num: 2, name: 'Model Card Synthesizer', task: 'Architecture, training & bias specs', status: '✓ Generated' },
        { num: 3, name: 'Dataset Lineage DAG Tracker', task: 'Cryptographic dataset origin tracing', status: '✓ 14 Steps' },
        { num: 4, name: 'Demographic Parity Auditor', task: 'Fairness invariant verification checker', status: '✓ 0 Bias' },
        { num: 5, name: 'Model Registry Versioner', task: 'Staging, Canary & Prod semantic tags', status: '✓ v2.4-Prod' },
        { num: 6, name: 'Shadow Traffic Mirror', task: 'Live candidate model shadow comparison', status: '✓ Mirrored' },
        { num: 7, name: 'Concept Drift Watchdog', task: 'Kolmogorov-Smirnov feature shift detector', status: '✓ < 0.01 KS' },
        { num: 8, name: 'Regulatory Compliance Guard', task: 'EU AI Act & NIST safety checklist audits', status: '✓ Certified' },
      ],
      metrics: [
        { label: 'PROVENANCE AUDIT', value: '100% Verifiable', color: 'var(--accent-cyan)' },
        { label: 'DRIFT LATENCY', value: '< 5s Detection', color: 'var(--accent-emerald)' },
        { label: 'LINEAGE DEPTH', value: '14 Steps', color: 'var(--accent-violet)' },
        { label: 'GOVERNANCE GATE', value: '90.1% Saved', color: 'var(--accent-gold)' },
      ],
      deliverables: ['gov/model_card.json', 'gov/lineage_dag.py', 'gov/fairness_audit.py', 'gov/drift_detector.py'],
      gatingInfo: 'Statistical drift metrics calculated locally via KS-test without LLM querying.',
    },
  },
];

export interface CuteModeSpec {
  nickname: string;
  tagline: string;
  stat1: { label: string; value: string; color: string };
  stat2: { label: string; value: string; color: string };
}

export interface CuteOctopusConfig {
  id: number;
  numberLabel: string;
  name: string;
  colorHex: string;
  softdev: CuteModeSpec;
  aiml: CuteModeSpec;
}

export const CUTE_OCTOPUS_CONFIGS: CuteOctopusConfig[] = [
  {
    id: 0,
    numberLabel: 'OCTOPUS 1',
    name: 'Octo 1',
    colorHex: '#38bdf8',
    softdev: {
      nickname: 'The Blueprint Brain',
      tagline: 'Draws master schemas, validates Pydantic contracts & locks clean API boundaries.',
      stat1: { label: 'LATENCY', value: '0.4ms', color: 'var(--accent-cyan)' },
      stat2: { label: 'GATING', value: '91.2% Saved', color: 'var(--accent-emerald)' },
    },
    aiml: {
      nickname: 'The Data Weaver',
      tagline: 'Streams 4.8 GB/s clean Arrow batches with MinHash deduplication & zero leakage.',
      stat1: { label: 'STREAM', value: '4.8 GB/s', color: 'var(--accent-cyan)' },
      stat2: { label: 'CLEAN', value: '100% Pass', color: 'var(--accent-emerald)' },
    },
  },
  {
    id: 1,
    numberLabel: 'OCTOPUS 2',
    name: 'Octo 2',
    colorHex: '#34d399',
    softdev: {
      nickname: 'The Memory Vault',
      tagline: 'Guards persistent SQL storage with zero lock contention & safe migrations.',
      stat1: { label: 'QUERY', value: '0.8ms', color: 'var(--accent-emerald)' },
      stat2: { label: 'LOCK WAIT', value: '0.00s', color: 'var(--accent-cyan)' },
    },
    aiml: {
      nickname: 'The Neural Sculptor',
      tagline: 'Shapes FlashAttention-2, RoPE embeddings & 8-expert Sparse MoE backbones.',
      stat1: { label: 'CONTEXT', value: '128k', color: 'var(--accent-emerald)' },
      stat2: { label: 'ATTENTION', value: '2.4x Flash', color: 'var(--accent-cyan)' },
    },
  },
  {
    id: 2,
    numberLabel: 'OCTOPUS 3',
    name: 'Octo 3',
    colorHex: '#c084fc',
    softdev: {
      nickname: 'The Gateway Keeper',
      tagline: 'Serves fast asynchronous endpoints with sliding JWT sessions & rate limiters.',
      stat1: { label: 'ENDPOINT', value: '1.4ms', color: 'var(--accent-violet)' },
      stat2: { label: 'AUTH CHECK', value: '0.15ms', color: 'var(--accent-cyan)' },
    },
    aiml: {
      nickname: 'The Engine Room',
      tagline: 'Drives multi-GPU ZeRO-3 clusters, balances loss & auto-recovers from spikes.',
      stat1: { label: 'TRAIN SPEED', value: '1,420 tok/s', color: 'var(--accent-violet)' },
      stat2: { label: 'STABILITY', value: '100% Clean', color: 'var(--accent-cyan)' },
    },
  },
  {
    id: 3,
    numberLabel: 'OCTOPUS 4',
    name: 'Octo 4',
    colorHex: '#f43f5e',
    softdev: {
      nickname: 'The UI Magician',
      tagline: 'Paints 60fps reactive views with zero layout shifts & VisionOS glassmorphism.',
      stat1: { label: 'FRAME RATE', value: '60.0 fps', color: 'var(--accent-rose)' },
      stat2: { label: 'SHIFT', value: '0.000 CLS', color: 'var(--accent-cyan)' },
    },
    aiml: {
      nickname: 'The Judge & Critic',
      tagline: 'Benchmarks multi-step reasoning accuracy and spots subtle hallucinations.',
      stat1: { label: 'HUMANEVAL', value: '84.2%', color: 'var(--accent-rose)' },
      stat2: { label: 'GROUNDING', value: 'r = 0.94', color: 'var(--accent-cyan)' },
    },
  },
  {
    id: 4,
    numberLabel: 'OCTOPUS 5',
    name: 'Octo 5',
    colorHex: '#facc15',
    softdev: {
      nickname: 'The Speed Demon',
      tagline: 'Maintains microsecond Redis cache, pubsub fanouts & squashes duplicate traffic.',
      stat1: { label: 'CACHE TIME', value: '0.08ms', color: 'var(--accent-gold)' },
      stat2: { label: 'HIT RATIO', value: '99.2%', color: 'var(--accent-cyan)' },
    },
    aiml: {
      nickname: 'The Curious Explorer',
      tagline: 'Discovers optimal learning rates & prunes unpromising runs via Bayesian TPE.',
      stat1: { label: 'SEARCH BOOST', value: '4.6x Fast', color: 'var(--accent-gold)' },
      stat2: { label: 'HYPERVOLUME', value: '0.892', color: 'var(--accent-cyan)' },
    },
  },
  {
    id: 5,
    numberLabel: 'OCTOPUS 6',
    name: 'Octo 6',
    colorHex: '#fb923c',
    softdev: {
      nickname: 'The Bug Hunter',
      tagline: 'Runs 67/67 tests in parallel, injects chaos latency & catches race conditions.',
      stat1: { label: 'TEST SUITE', value: '100% Pass', color: 'var(--accent-gold)' },
      stat2: { label: 'RUN TIME', value: '1.8s', color: 'var(--accent-cyan)' },
    },
    aiml: {
      nickname: 'The Nano Compressor',
      tagline: 'Shrinks neural models 4.1x into sub-4ms edge WebAssembly SIMD kernels.',
      stat1: { label: 'SIZE REDUCE', value: '4.1x', color: 'var(--accent-gold)' },
      stat2: { label: 'EDGE SIMD', value: '3.2ms', color: 'var(--accent-cyan)' },
    },
  },
  {
    id: 6,
    numberLabel: 'OCTOPUS 7',
    name: 'Octo 7',
    colorHex: '#e11d48',
    softdev: {
      nickname: 'The Shield Guardian',
      tagline: 'Zero secret leaks, Python AST sandboxing & cryptographic proof receipts.',
      stat1: { label: 'LEAK RATE', value: '0.00%', color: 'var(--accent-rose)' },
      stat2: { label: 'AST AUDIT', value: '< 0.2ms', color: 'var(--accent-cyan)' },
    },
    aiml: {
      nickname: 'The Fast Speaker',
      tagline: 'Streams 3,850 tok/s with speculative decoding, continuous batching & vLLM.',
      stat1: { label: 'THROUGHPUT', value: '3,850 tok/s', color: 'var(--accent-rose)' },
      stat2: { label: 'TTFT LATENCY', value: '18ms', color: 'var(--accent-cyan)' },
    },
  },
  {
    id: 7,
    numberLabel: 'OCTOPUS 8',
    name: 'Octo 8',
    colorHex: '#60a5fa',
    softdev: {
      nickname: 'Captain Ignition',
      tagline: 'Spins up tiny 38MB scratch containers with instant zero-downtime rollback.',
      stat1: { label: 'DOWNTIME', value: '0.00s', color: 'var(--accent-cyan)' },
      stat2: { label: 'CONTAINER', value: '38 MB', color: 'var(--accent-emerald)' },
    },
    aiml: {
      nickname: 'The Deep Historian',
      tagline: 'Tracks 100% verifiable data & weight lineage DAGs and catches concept drift.',
      stat1: { label: 'PROVENANCE', value: '100%', color: 'var(--accent-cyan)' },
      stat2: { label: 'DRIFT CHECK', value: '< 5s', color: 'var(--accent-emerald)' },
    },
  },
];

/**
 * Renders the compact, short, and cute HTML card for an individual octopus (Slides 19 - 26).
 */
export function renderIndividualOctopusHTML(octoIndex: number): string {
  const cfg = CUTE_OCTOPUS_CONFIGS[octoIndex];
  if (!cfg) return '';

  const chapterNum = (19 + octoIndex).toString().padStart(2, '0');
  const slideTarget = 19 + octoIndex; // next slide target

  function renderCuteBlock(spec: CuteModeSpec, typeKey: 'softdev' | 'aiml', isActive: boolean): string {
    return `
      <div id="morph-panel-${typeKey}-${cfg.id}" class="morphology-view-panel ${isActive ? 'active' : ''}">
        <h3 class="cute-octo-title">${cfg.name}: ${spec.nickname}</h3>
        <p class="cute-octo-tagline">${spec.tagline}</p>

        <div class="cute-stats-row">
          <div class="cute-stat-chip">
            <span class="cute-stat-val" style="color: ${spec.stat1.color};">${spec.stat1.value}</span>
            <span class="cute-stat-lbl">${spec.stat1.label}</span>
          </div>
          <div class="cute-stat-chip">
            <span class="cute-stat-val" style="color: ${spec.stat2.color};">${spec.stat2.value}</span>
            <span class="cute-stat-lbl">${spec.stat2.label}</span>
          </div>
        </div>
      </div>
    `;
  }

  return `
    <div class="octopus-individual-card cute-octo-card" style="--card-accent: ${cfg.colorHex};">
      <!-- Top Meta Bar -->
      <div class="cute-octo-top">
        <div class="cute-tag-group">
          <span class="cute-chap-tag font-mono">${chapterNum} // ${cfg.numberLabel}</span>
          <span class="cute-live-pill" style="color: ${cfg.colorHex}; border-color: ${cfg.colorHex}55; background: ${cfg.colorHex}15;">
            <span class="pulse-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 6px ${cfg.colorHex};"></span>
            Active
          </span>
        </div>

        <!-- Dual Mode Switch -->
        <div class="morphology-switcher">
          <button class="morphology-tab-btn tab-softdev active" data-octo="${cfg.id}" data-target="softdev" title="Software Dev Mode">
            <span>◈ SoftDev</span>
          </button>
          <button class="morphology-tab-btn tab-aiml" data-octo="${cfg.id}" data-target="aiml" title="AI/ML Mode">
            <span>○ AI/ML</span>
          </button>
        </div>
      </div>

      <!-- Morphology Views -->
      ${renderCuteBlock(cfg.softdev, 'softdev', true)}
      ${renderCuteBlock(cfg.aiml, 'aiml', false)}

      <!-- Cute 8-Arm Synchronized Meter -->
      <div class="cute-arms-meter">
        <div class="cute-dots-row">
          <span class="cute-arm-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 5px ${cfg.colorHex};" title="Arm 1: Active"></span>
          <span class="cute-arm-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 5px ${cfg.colorHex};" title="Arm 2: Active"></span>
          <span class="cute-arm-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 5px ${cfg.colorHex};" title="Arm 3: Active"></span>
          <span class="cute-arm-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 5px ${cfg.colorHex};" title="Arm 4: Active"></span>
          <span class="cute-arm-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 5px ${cfg.colorHex};" title="Arm 5: Active"></span>
          <span class="cute-arm-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 5px ${cfg.colorHex};" title="Arm 6: Active"></span>
          <span class="cute-arm-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 5px ${cfg.colorHex};" title="Arm 7: Active"></span>
          <span class="cute-arm-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 5px ${cfg.colorHex};" title="Arm 8: Active"></span>
        </div>
        <span class="cute-arms-tag font-mono">8 / 8 Arms Synchronized</span>
      </div>

      <!-- Cute Action Row -->
      <div class="cute-action-row">
        <button class="btn-octo-reflex" data-octo="${cfg.id}" title="Trigger action potential cascade through this octopus">
          <span>↯ Spark Octo</span>
        </button>

        <div style="display: flex; align-items: center; gap: 8px;">
          <button class="btn-cinema-secondary slide-step-action-btn" data-step-to="${slideTarget}" style="padding: 5px 12px; font-size: 11px;">
            <span>${octoIndex < 7 ? `Next: Octo ${octoIndex + 2} &rarr;` : `Enter Swarm &rarr;`}</span>
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Renders Slide 27: The Grand Finale where all 8 octopuses work together.
 */
export function renderConsortiumFinaleHTML(): string {
  return `
    <div class="chapter-content-card consortium-main-card finale-cute-main-card">
      <div class="chapter-tag" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <span>27 // THE 8-OCTOPUS LIVING SWARM</span>
        <span class="consortium-live-pill"><span class="pulse-dot"></span> 64 ARMS SYNCHRONIZED</span>
      </div>

      <h2 class="chapter-headline finale-cute-headline">
        All 8 Octopuses Working as One.
      </h2>
      <div class="chapter-subhead finale-cute-subhead">
        Eight autonomous 3D cephalopods (64 arms) collaborating across 3D synaptic cables with Active Inference sensory gating.
      </div>

      <!-- Controls & Swarm Perspective Selector -->
      <div class="consortium-toolbar finale-cute-toolbar">
        <div class="consortium-mode-switch">
          <button id="btn-scale-softdev" class="mode-btn active" data-morphology="softdev">
            <span class="mode-icon">◈</span> Software Dev (64 Arms)
          </button>
          <button id="btn-scale-aiml" class="mode-btn" data-morphology="aiml">
            <span class="mode-icon">○</span> AI/ML (64 Arms)
          </button>
        </div>

        <div class="consortium-action-triggers">
          <button id="btn-fire-synapse" class="hud-pill btn-action-glow" title="Emit 3D action potential burst across all 8 octopuses">
            <span class="spark-icon">↯</span> Swarm Synapse Burst
          </button>
          <button id="btn-inject-steering" class="hud-pill btn-action-steer" title="Simulate Mid-Flight Human Steering Directive">
            <span class="steer-icon">⇄</span> Steer Swarm
          </button>
        </div>
      </div>

      <!-- Interactive Synaptic Bus Pathway (Animated Strip) -->
      <div class="synaptic-bus-strip finale-cute-bus">
        <div class="synaptic-bus-label">
          <span>3D SYNAPTIC HIGHWAY &amp; ACTION POTENTIAL CHORD</span>
          <span id="bus-throughput-text" style="color: var(--accent-cyan); font-family: var(--font-mono); font-size: 10px;">
            256 pkt/s · 0.2ms Cluster Latency
          </span>
        </div>
        <div class="synaptic-bus-track" id="synaptic-bus-track">
          <div class="bus-line-pulse"></div>
          <div class="bus-particle p1"></div>
          <div class="bus-particle p2"></div>
          <div class="bus-particle p3"></div>
        </div>
      </div>

      <!-- 8-Octopuses Grid (Cute 8-card grid) -->
      <div id="consortium-grid" class="consortium-grid grid-octopolis finale-cute-grid">
        <!-- Rendered dynamically by JS -->
      </div>

      <!-- Compact Finale Economics & Mini Log Bar -->
      <div class="finale-cute-footer-row">
        <div class="cute-eco-badges">
          <div class="cute-eco-chip">
            <span class="c-eco-num font-mono" style="color: var(--accent-emerald);">16,800</span>
            <span class="c-eco-lbl">Tokens Avoided</span>
          </div>
          <div class="cute-eco-chip">
            <span class="c-eco-num font-mono" style="color: var(--accent-gold);">88.7%</span>
            <span class="c-eco-lbl">Reflex Saved</span>
          </div>
          <div class="cute-eco-chip">
            <span class="c-eco-num font-mono" style="color: var(--accent-cyan);">θ = 0.45</span>
            <span class="c-eco-lbl">Sensory Gate</span>
          </div>
        </div>

        <!-- Live Mini Ticker -->
        <div class="synaptic-log-box finale-mini-log">
          <div class="synaptic-log-header">
            <span>LIVE SYNAPTIC FEED</span>
            <span id="log-packet-count" class="log-count-tag font-mono">18 PKTS</span>
          </div>
          <div id="synaptic-feed-container" class="synaptic-feed-list finale-feed-list">
            <!-- Messages added dynamically -->
          </div>
        </div>

        <div class="finale-cta-actions">
          <button id="cta-consortium-dossier" class="btn-cinema-secondary finale-dossier-btn">
            <span>Executive Dossier &rarr;</span>
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Initializes all interactive listeners across Slides 19 - 27:
 * - Morphology toggles for individual slides (Slides 19 - 26)
 * - Synaptic reflex test buttons
 * - Slide navigation helper buttons
 * - Finale slide mode switcher & live packet stream
 */
export function initConsortiumExperience(
  experience: OctopusConnectomeExperience,
  soundEngine: SoundEngine,
  onOpenDossier?: () => void,
  onGoToSlide?: (slideIdx: number) => void
) {
  // Unified morphology state across all 8 octopuses and Grand Finale
  let activeSwarmMorphology: 'softdev' | 'aiml' = 'softdev';

  function applyMorphologyToAll(mode: 'softdev' | 'aiml', octoIdToPulse?: number) {
    activeSwarmMorphology = mode;

    // 1. Synchronize all 8 individual octopus cards (Slides 19 - 26)
    document.querySelectorAll('.octopus-individual-card').forEach((card) => {
      card.querySelectorAll('.morphology-tab-btn').forEach((tb) => {
        const isMatch = tb.getAttribute('data-target') === mode;
        tb.classList.toggle('active', isMatch);
      });

      const softPanel = card.querySelector('.morphology-view-panel[id*="softdev"]');
      const aimlPanel = card.querySelector('.morphology-view-panel[id*="aiml"]');
      if (mode === 'softdev') {
        softPanel?.classList.add('active');
        aimlPanel?.classList.remove('active');
      } else {
        aimlPanel?.classList.add('active');
        softPanel?.classList.remove('active');
      }
    });

    // 2. Synchronize Slide 27 Finale Swarm Perspective Switcher & Grid
    const btnSoftdev = document.getElementById('btn-scale-softdev');
    const btnAiml = document.getElementById('btn-scale-aiml');
    if (btnSoftdev && btnAiml) {
      btnSoftdev.classList.toggle('active', mode === 'softdev');
      btnAiml.classList.toggle('active', mode === 'aiml');
    }
    renderFinaleGrid();

    // 3. Audio & 3D Interactive Feedback
    soundEngine.ensureAudioStarted();
    if (octoIdToPulse !== undefined) {
      soundEngine.playSlideTransition(octoIdToPulse);
      if (experience.swarm3D) {
        experience.swarm3D.triggerPulse(octoIdToPulse);
      }
    } else {
      soundEngine.playSlideTransition(18);
      if (experience.swarm3D) {
        experience.swarm3D.triggerPulse(-1);
      }
    }
  }

  // 1. Dual-Morphology Switchers for Individual Octopus Slides (Slides 19 - 26)
  document.querySelectorAll('.morphology-tab-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const target = e.currentTarget as HTMLElement;
      const octoId = target.getAttribute('data-octo');
      const targetType = target.getAttribute('data-target') as 'softdev' | 'aiml';
      if (!targetType) return;

      const numId = octoId !== null ? parseInt(octoId) : undefined;
      applyMorphologyToAll(targetType, numId);
    });
  });

  // 2. Individual Octopus Reflex Test Buttons
  document.querySelectorAll('.btn-octo-reflex').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const target = e.currentTarget as HTMLElement;
      const octoId = parseInt(target.getAttribute('data-octo') || '0');

      soundEngine.ensureAudioStarted();
      soundEngine.playSynapticSpark();

      // Trigger 3D burst on this specific octopus in swarm
      if (experience.swarm3D) {
        experience.swarm3D.triggerPulse(octoId);
      }
      experience.triggerShockwave();

      // Visual flash on button
      target.classList.add('pulse-glow');
      setTimeout(() => target.classList.remove('pulse-glow'), 800);

      // Visual burst on this card's 8 arm dots
      const parentCard = target.closest('.octopus-individual-card');
      if (parentCard) {
        const dots = parentCard.querySelectorAll('.cute-arm-dot');
        dots.forEach((d) => d.classList.add('spark-active'));
        setTimeout(() => dots.forEach((d) => d.classList.remove('spark-active')), 900);
      }

      // Log to synaptic feed if visible
      addLogMessage(`Octo ${octoId + 1}`, 'Adjacent Arms', `↯ High-frequency action potential burst tested [Arm 1..8 locked]`, 'spark');
    });
  });

  // 3. Mini Step Buttons
  document.querySelectorAll('.slide-step-action-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const target = e.currentTarget as HTMLElement;
      const targetSlide = parseInt(target.getAttribute('data-step-to') || '0');
      if (onGoToSlide) {
        onGoToSlide(targetSlide);
      }
    });
  });

  // 4. Slide 27: Finale Swarm Experience
  const grid = document.getElementById('consortium-grid');
  const feed = document.getElementById('synaptic-feed-container');
  const busThroughputText = document.getElementById('bus-throughput-text');
  const packetCountText = document.getElementById('log-packet-count');

  const initialPackets = [
    { time: '10:14:02', from: 'Octo 1', to: 'Octo 2', msg: 'CONTRACT_LOCKED (OpenAPI 3.1 & Schema v2)', type: 'contract' },
    { time: '10:14:04', from: 'Octo 2', to: 'Octo 3', msg: 'WAL_CONCURRENCY_ACTIVE (0.00s wait on read pool)', type: 'realtime' },
    { time: '10:14:06', from: 'Octo 3', to: 'Octo 4', msg: 'WS_HANDSHAKE_READY (Starlette /ws/feed mounted)', type: 'realtime' },
    { time: '10:14:09', from: 'Sensory Gate', to: 'All 64 Arms', msg: 'ΔS=0.08 <= θ (Reflex silenced · 0 tokens burned)', type: 'gating' },
    { time: '10:14:12', from: 'Octo 6', to: 'Octo 7', msg: 'CI_VERIFIED: 67/67 passing · AST audit clean', type: 'system' },
    { time: '10:14:15', from: 'Synaptic Bus', to: 'Octos 1..8', msg: 'BROADCAST: Phase 1 Consortium Consensus Reached', type: 'system' },
  ];

  let packetCounter = initialPackets.length;

  function renderFinaleGrid() {
    if (!grid) return;

    grid.innerHTML = CUTE_OCTOPUS_CONFIGS.map((cfg) => {
      const isSoftdev = activeSwarmMorphology === 'softdev';
      const spec = isSoftdev ? cfg.softdev : cfg.aiml;
      const roleTitle = isSoftdev 
        ? OCTOPUS_SPECS[cfg.id].softwareDev.roleTitle.split('&')[0].trim()
        : OCTOPUS_SPECS[cfg.id].aimlResearch.roleTitle.split('&')[0].trim();

      return `
        <div class="octopus-unit-card finale-cute-unit-card status-complete" id="card-octo-${cfg.id}" style="--unit-accent: ${cfg.colorHex}; border-top: 2px solid ${cfg.colorHex};">
          <div class="unit-card-header">
            <div class="unit-title-group">
              <div class="unit-name" style="color: ${cfg.colorHex}; font-weight: 700;">
                <span class="unit-dot" style="background: ${cfg.colorHex}; box-shadow: 0 0 6px ${cfg.colorHex};"></span>
                ${cfg.name}
              </div>
              <div class="unit-nickname font-mono" style="font-size: 10px; color: #e2e8f0; font-weight: 600;">${spec.nickname}</div>
            </div>
            <span class="unit-badge badge-complete font-mono">✓ Active</span>
          </div>

          <div class="unit-role-line" style="font-size: 10.5px; color: var(--text-muted); line-height: 1.3;">
            ${roleTitle}
          </div>

          <!-- 8-Arm Synchronized Visual Meter -->
          <div class="unit-arms-matrix finale-arms-box">
            <div class="finale-dots-row">
              <span class="f-dot" style="background: ${cfg.colorHex};"></span>
              <span class="f-dot" style="background: ${cfg.colorHex};"></span>
              <span class="f-dot" style="background: ${cfg.colorHex};"></span>
              <span class="f-dot" style="background: ${cfg.colorHex};"></span>
              <span class="f-dot" style="background: ${cfg.colorHex};"></span>
              <span class="f-dot" style="background: ${cfg.colorHex};"></span>
              <span class="f-dot" style="background: ${cfg.colorHex};"></span>
              <span class="f-dot" style="background: ${cfg.colorHex};"></span>
            </div>
            <span class="f-arms-text font-mono">8 Arms Active</span>
          </div>

          <!-- Hero Metric Tag -->
          <div class="unit-hero-stat">
            <span class="hero-stat-lbl">${spec.stat1.label}</span>
            <span class="hero-stat-val font-mono" style="color: ${spec.stat1.color}; font-weight: 700;">${spec.stat1.value}</span>
          </div>
        </div>
      `;
    }).join('');
  }

  function addLogMessage(from: string, to: string, msg: string, type: 'contract' | 'realtime' | 'gating' | 'system' | 'steer' | 'spark') {
    if (!feed) return;
    packetCounter++;
    if (packetCountText) packetCountText.innerText = `${packetCounter} PACKETS`;

    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];

    const item = document.createElement('div');
    item.className = `synaptic-packet-line type-${type} new-packet`;
    item.innerHTML = `
      <span class="pkt-time font-mono">${timeStr}</span>
      <span class="pkt-route font-mono">[${from} ──► ${to}]</span>
      <span class="pkt-msg font-mono">${msg}</span>
    `;

    feed.prepend(item);

    // Limit log history to 18 lines
    while (feed.children.length > 18) {
      feed.removeChild(feed.lastChild!);
    }
  }

  // Populate Initial Packets
  initialPackets.forEach((p) => addLogMessage(p.from, p.to, p.msg, p.type as any));

  // Render initial grid
  renderFinaleGrid();

  // Finale Swarm Perspective Switcher Handlers
  const btnSoftdev = document.getElementById('btn-scale-softdev');
  const btnAiml = document.getElementById('btn-scale-aiml');

  btnSoftdev?.addEventListener('click', () => {
    applyMorphologyToAll('softdev');
    addLogMessage('Consortium Engine', 'All 8 Nodes', 'Swarm perspective switched: Software Engineering (64 Arms)', 'system');
  });

  btnAiml?.addEventListener('click', () => {
    applyMorphologyToAll('aiml');
    addLogMessage('Consortium Engine', 'All 8 Nodes', 'Swarm perspective switched: AI/ML Research (64 Arms)', 'system');
  });

  // Action 1: Fire Synaptic Pulse Across All 8 Octopuses
  const btnPulse = document.getElementById('btn-fire-synapse');
  btnPulse?.addEventListener('click', () => {
    soundEngine.ensureAudioStarted();
    soundEngine.playSynapticSpark();
    if (experience.swarm3D) {
      experience.swarm3D.triggerSwarmBurst();
    }
    experience.triggerShockwave();

    // Visual shockwave on bus
    const track = document.getElementById('synaptic-bus-track');
    track?.classList.add('pulse-surge');
    setTimeout(() => track?.classList.remove('pulse-surge'), 800);

    // Flash octopuses cards
    document.querySelectorAll('.octopus-unit-card').forEach((card) => {
      card.classList.add('card-shocked');
      setTimeout(() => card.classList.remove('card-shocked'), 600);
    });

    addLogMessage('Central Conductor', 'All 8 Octopuses', '↯ High-frequency synaptic spark broadcasted across all 64 arms', 'spark');

    if (busThroughputText) {
      busThroughputText.innerText = '512 pkt/s · 0.05ms Burst';
      setTimeout(() => {
        if (busThroughputText) busThroughputText.innerText = '256 pkt/s · 0.2ms Cluster Latency';
      }, 1500);
    }
  });

  // Action 2: Mid-Flight Human Steering Simulation
  const btnSteer = document.getElementById('btn-inject-steering');
  const sampleDirectives = [
    'Enforce JWT refresh tokens with sliding-window expiration across Octo 3',
    'Add stress test suite covering 500 concurrent WebSocket clients in Octo 6',
    'Quantize model backbone weights to INT8 SmoothQuant in Octo 6 & 7',
    'Re-calibrate BPE tokenizer vocabulary entropy floor in Octo 1',
    'Lock OpenAPI 3.1 contracts and compile topological DAG in Octo 1',
  ];
  let steerIdx = 0;

  btnSteer?.addEventListener('click', () => {
    soundEngine.ensureAudioStarted();
    soundEngine.playSlideTransition(26);

    const directive = sampleDirectives[steerIdx % sampleDirectives.length];
    steerIdx++;

    // Bus flashes steering violet
    const track = document.getElementById('synaptic-bus-track');
    track?.classList.add('steering-surge');
    setTimeout(() => track?.classList.remove('steering-surge'), 900);

    addLogMessage('Human Architect', 'Consortium Conductor', `[STEERING DIRECTIVE]: "${directive}"`, 'steer');

    // Downstream units acknowledge
    setTimeout(() => {
      addLogMessage('Octo 1 (Architect)', 'Synaptic Bus', 'ACK: Adjusting task graph & updating module boundaries', 'realtime');
    }, 400);

    setTimeout(() => {
      addLogMessage('Octo 6 (QA & AST)', 'Synaptic Bus', 'ACK: Injected verification contracts into Pytest harness', 'system');
    }, 850);
  });

  // Dossier Button
  document.getElementById('cta-consortium-dossier')?.addEventListener('click', () => {
    if (onOpenDossier) onOpenDossier();
  });

  // Automated Background Pulse Stream (every 4.5 seconds to keep the connectome alive)
  const tickerTimer = setInterval(() => {
    if (document.hidden) return;
    const randomPick = [
      { from: 'Octo 1', to: 'Octo 2', msg: 'AST check passed: domain.py (0 schema regressions)', type: 'realtime' },
      { from: 'Sensory Gate', to: 'Octo 4', msg: 'Predictive residual ΔS=0.03 <= θ (Silenced)', type: 'gating' },
      { from: 'Octo 3', to: 'Octo 7', msg: 'Continuous batching queue verified (3.8k tok/s)', type: 'contract' },
      { from: 'Synaptic Bus', to: 'All 8 Octos', msg: 'Heartbeat ping: 64 arms quiescent, 0 packet drops', type: 'system' },
      { from: 'Octo 6', to: 'Octo 8', msg: 'Docker multi-stage container build verified (38 MB)', type: 'system' },
    ][Math.floor(Math.random() * 5)];

    addLogMessage(randomPick.from, randomPick.to, randomPick.msg, randomPick.type as any);
  }, 4800);

  return () => {
    clearInterval(tickerTimer);
  };
}
