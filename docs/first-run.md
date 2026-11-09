# OctoFlow Guided First-Run Onboarding

OctoFlow provides an interactive, product-minded guided onboarding flow designed to take new developers from zero to a verified, working cephalopod swarm execution in **under 2 minutes** (target: < 5 minutes).

---

## 1. Trigger Conditions & Non-Interactive Safety

### Automatic Trigger
When running `octoflow` or `./octos` without subcommands:
- If `~/.octoflow/config.json` is missing **OR** `onboarding_completed: false`, OctoFlow automatically launches the guided first-run wizard before starting the interactive cockpit.

### Explicit Triggers
```bash
# Run guided onboarding explicitly
octos first-run

# Run guided onboarding via setup command
octos setup --guided

# Run non-interactively picking local Ollama if available else dry-run
octos first-run --yes
```

### Automatic Non-Interactive Bypass
The wizard is strictly bypassed (never prompts or hangs) when:
- Standard input (`sys.stdin`) is not a TTY (CI/CD environments, background workers, pipes).
- `OCTOFLOW_NONINTERACTIVE=1` is set.
- `OCTOFLOW_SKIP_ONBOARDING=1` is set (escape hatch).

---

## 2. The 3-Question Onboarding Flow

To avoid cognitive overload, the wizard asks **at most three questions**:

1. **Question 1 (Engine Choice)**:
   - `1) Local Ollama`: 100% private, free, runs on-device (`qwen2.5-coder:7b`).
   - `2) Cloud API Key`: Frontier models via Anthropic, OpenAI, or Google Gemini.
   - `3) Dry-Run Demo`: Zero cost, zero dependencies, simulated active inference.
2. **Question 2 (Demo Confirmation)**:
   - `Ready to run the 60-second reverse_words demo? [Y/n]`
3. **Question 3 (Visualizer)**:
   - `Open 3D Visualizer bridge on http://localhost:8088? [y/N]`

---

## 3. Demo Task Execution & Isolation

The wizard executes a tiny, self-contained mission:
- **Goal**: `"create a function that reverses words with a pytest test"`
- **Workspace Confinement**: Strictly isolated under `~/.octoflow/demo` (never touches your current working repository).
- **Enforced Budgets**:
  - Max Wall Clock: `60 seconds`
  - Max Tokens: `8,000`
  - Max LLM Calls: `6`
  - Max Files Written: `3`
- **Deliverables Produced**:
  - `reverse_words.py`: Pure Python word-reversal utility.
  - `test_reverse_words.py`: Full pytest unit test suite verifying contracts.

---

## 4. Transcript: Successful First Run (Local Ollama)

```text
$ octos

╭──────────────────────────────────────────────────────────────────────────────╮
│ ◈ Welcome to OctoFlow: Guided First Run                                      │
│ Setting up your environment, selecting an LLM engine, and validating demo.   │
╰──────────────────────────────────────────────────────────────────────────────╯

                     ◈ Environment Pre-Flight Diagnostics                      
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Subsystem           ┃ Status       ┃ Details & Fix Hints                    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Python Runtime      │ ● PASS       │ v3.12.2 (>= 3.10 required)             │
│ Git Version Control │ ● PASS       │ v2.43.0                                │
│ Local Ollama        │ ● PASS       │ Reachable at http://localhost:11434    │
│                     │              │ (qwen2.5-coder:7b)                     │
└─────────────────────┴──────────────┴────────────────────────────────────────┘

                      Step 1/3: Choose LLM Neural Engine                      
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #  ┃ Engine Option              ┃ Details & Privacy                          ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1  │ Local Ollama (Recommended) │ 100% Free, private, on-device (qwen2.5)    │
│ 2  │ Cloud API Key              │ State-of-the-art frontier models           │
│ 3  │ Dry-Run Demo               │ Zero cost, simulated cephalopod swarm      │
└━━━━┴━━━━━━━━━━━━━━━━━━━━━━━━━━━━┴━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘

Select engine [1-3] (default 1): 1
✔ Local Ollama selected (qwen2.5-coder:7b).

Step 2/3: Ready to run 60-second reverse_words demo? [Y/n]: y

◈ Deploying 8-Arm Swarm in ~/.octoflow/demo...
Goal: 'create a function that reverses words with a pytest test'

✔ OCTOFLOW FIRST-RUN DEMO COMPLETE (4.21s)
  • Files Created in ~/.octoflow/demo:
    - reverse_words.py
    - test_reverse_words.py
  • Token Ledger: 1,420 tokens (Saved 88.2% vs baseline)

✔ Configuration saved: onboarding completed!

Step 3/3: Open 3D Visualizer on http://localhost:8088? [y/N]: n

Transitioning into interactive cephalopod cockpit...
```

---

## 5. Transcript: First Run with Missing Ollama Model (Graceful Fallback)

```text
$ octos first-run

╭──────────────────────────────────────────────────────────────────────────────╮
│ ◈ Welcome to OctoFlow: Guided First Run                                      │
│ Setting up your environment, selecting an LLM engine, and validating demo.   │
╰──────────────────────────────────────────────────────────────────────────────╯

                     ◈ Environment Pre-Flight Diagnostics                      
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Subsystem           ┃ Status       ┃ Details & Fix Hints                    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Python Runtime      │ ● PASS       │ v3.12.2 (>= 3.10 required)             │
│ Git Version Control │ ● PASS       │ v2.43.0                                │
│ Local Ollama        │ ▲ WARN       │ Daemon online, but qwen2.5-coder:7b    │
│                     │              │ missing -> Fix: ollama pull            │
│                     │              │ qwen2.5-coder:7b (~4.7 GB)             │
└─────────────────────┴──────────────┴────────────────────────────────────────┘

Select engine [1-3] (default 3): 1
▲ Ollama is running, but no coder model was found.
  Download command: ollama pull qwen2.5-coder:7b (approx. ~4.7 GB)

Falling back to dry-run demo for this first run.

Step 2/3: Ready to run 60-second reverse_words demo? [Y/n]: y

◈ Deploying 8-Arm Swarm in ~/.octoflow/demo...
Goal: 'create a function that reverses words with a pytest test'

✔ OCTOFLOW FIRST-RUN DEMO COMPLETE (0.42s)
  • Files Created in ~/.octoflow/demo:
    - reverse_words.py
    - test_reverse_words.py
  • Token Ledger: 950 tokens (Saved 91.5% vs baseline)

✔ Configuration saved: onboarding completed!

Step 3/3: Open 3D Visualizer on http://localhost:8088? [y/N]: n
```

---

## 6. Transcript: Handled Failure Path with Recovery

When a network timeout or provider credential failure occurs, the user is **never left at a blank prompt**:

```text
◈ Deploying 8-Arm Swarm in ~/.octoflow/demo...
Goal: 'create a function that reverses words with a pytest test'

✖ Demo task failed using 'anthropic' (Invalid API Key signature).
  Log file: ~/.octoflow/logs/octoflow.log

Would you like to fallback and verify in safe dry-run mode? [Y/n]: y

◈ Deploying 8-Arm Swarm in ~/.octoflow/demo...
✔ OCTOFLOW FIRST-RUN DEMO COMPLETE (0.38s)
  • Files Created in ~/.octoflow/demo:
    - reverse_words.py
    - test_reverse_words.py
  • Token Ledger: 950 tokens (Saved 91.5% vs baseline)

✔ Configuration saved: onboarding completed!
```
