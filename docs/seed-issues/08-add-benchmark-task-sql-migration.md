# Add Idempotent SQL Database Migration Task to Benchmark Suite

**Difficulty:** Intermediate  
**Labels:** `enhancement`, `testing`  
**Mentoring Pointer:** Inspect existing benchmark tasks in [`octoflow/bench.py`](../../octoflow/bench.py) (e.g. `fastapi_todo` and `lru_cache`) and the benchmark harness in [`tests/test_benchmark_harness.py`](../../tests/test_benchmark_harness.py).

---

## Context
OctoFlow's benchmark suite ([`octoflow/bench.py`](../../octoflow/bench.py)) provides standard software engineering tasks used to measure token consumption, gate surprise effectiveness ($\Delta S$), and task completion convergence.

Currently, the tasks focus on backend APIs (`fastapi_todo`) and pure algorithms (`lru_cache`, `rate_limiter`). Adding a database task that requires generating idempotent SQL migration scripts will test the swarm's ability to plan schema mutations, foreign keys, and rollbacks.

---

## Objectives & Requirements
1. In [`octoflow/bench.py`](../../octoflow/bench.py), add a new task `sql_migration` to `BENCHMARK_SUITE`.
2. Specification:
   - **Prompt:** "Create an idempotent SQLite schema migration script in `migration.sql` that defines `users`, `teams`, and `memberships` tables with appropriate foreign keys, timestamps, indexes, and a rollback section."
   - **Reference Solution:** Gold-standard SQL script demonstrating valid syntax, `CREATE TABLE IF NOT EXISTS`, indices, and triggers.
   - **Verification Code:** Python script using standard library `sqlite3` executing the migration twice (asserting idempotency), verifying schema constraints, foreign key cascades, and data integrity.
3. Add cassette recording or mock test in `tests/test_benchmark_harness.py`.

---

## Files to Touch
- [`octoflow/bench.py`](../../octoflow/bench.py): Add `sql_migration` task definition.
- [`tests/test_benchmark_harness.py`](../../tests/test_benchmark_harness.py): Add unit test executing `sql_migration` verification code.
- [`docs/BENCHMARKING.md`](../BENCHMARKING.md): Document the new benchmark task and its evaluation criteria.

---

## Acceptance Criteria
- [ ] `octoflow bench --task sql_migration` executes the benchmark run.
- [ ] Verification script asserts that running `migration.sql` twice does not raise `OperationalError`.
- [ ] Foreign key enforcement and index creation are asserted.
- [ ] Pytest suite in `tests/test_benchmark_harness.py` passes 100%.
