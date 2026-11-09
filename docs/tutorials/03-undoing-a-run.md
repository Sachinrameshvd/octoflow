# Tutorial 3: Undoing a Run with Atomic Git Rollback

**Estimated Duration:** 4 minutes  
**Verification:** Verified on 2026-11-09, OctoFlow v0.2.0  

This tutorial shows how OctoFlow protects your repository before every swarm mission and how to cleanly rollback any run with a single command.

---

## How Pre-Flight Checkpointing Works

Before modifying any file, OctoFlow's `checkpoint` subsystem:
1. Verifies that the workspace is a Git repository.
2. Captures an atomic stash snapshot of any dirty, uncommitted changes.
3. Records the current branch and HEAD commit hash.
4. Creates a tracking entry in `~/.octoflow/runs/<run_id>/meta.json`.

---

## Step 1: List Recent Runs

Inspect the execution history to see available run checkpoints:

```bash
octoflow runs
```

### Expected Output

```text
                        ◈ OctoFlow Run Provenance Ledger                        
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Run ID            ┃ Status    ┃ Mode         ┃ Created             ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 1794049840-56720e │ COMPLETED │ software_dev │ 2026-11-07 16:40:40 │
│ 1794048922-910979 │ COMPLETED │ software_dev │ 2026-11-07 16:25:22 │
└───────────────────┴───────────┴──────────────┴─────────────────────┘
```

---

## Step 2: Rollback the Most Recent Run

To revert all modifications introduced by the latest run, run `octoflow undo`:

```bash
octoflow undo
```

### Confirmation Prompt

```text
◈ OctoFlow Undo Checkpoint
Target run: 1794049840-56720e (branch: octoflow/run-1794049840)
Original branch: main (HEAD: b7ff24a)

[Notice] Are you sure you want to rollback this run and restore original state? [y/N]: y
✔ Checked out original branch: main
✔ Discarded run branch: octoflow/run-1794049840
✔ Restored working tree stash snapshot.
✔ Rollback complete. Workspace restored to pre-flight state.
```

---

## Step 3: Scripted Rollback (Skip Confirmation)

In automated test harnesses or CI environments, pass `--yes` (or `-y`) to skip the interactive confirmation prompt:

```bash
octoflow undo --yes
```

To rollback a specific historical run by ID rather than the latest:

```bash
octoflow undo 1794048922-910979 --yes
```

---

## Next Steps

- Learn how to define custom 8-arm specialist rosters: [Tutorial 4: Building with a Custom Guild](04-building-with-a-custom-guild.md)
- Learn about workspace security policies: [docs/adr/0005-tool-policy-not-sandbox.md](../adr/0005-tool-policy-not-sandbox.md)
