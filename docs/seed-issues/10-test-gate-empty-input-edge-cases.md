# Add Edge-Case Parameterized Tests for Sensory Surprise Gate Parity

**Difficulty:** Good First Issue  
**Labels:** `testing`, `good first issue`  
**Mentoring Pointer:** Check out [`tests/test_gate_parity.py`](../../tests/test_gate_parity.py) and [`octoflow/gate.py`](../../octoflow/gate.py) to understand how $\Delta S$ sensory surprise is calculated.

---

## Context
OctoFlow's fundamental token-saving mechanism is the sensory surprise gate ([`octoflow/gate.py`](../../octoflow/gate.py)). It maps environmental states (file trees, diffs, test results) into 16-dimensional observation vectors using both NumPy and PyTorch implementations.

If the calculated surprise $\Delta S$ is less than threshold $\theta$, the swarm executes a fast brachial reflex without consuming expensive LLM prompt tokens.

To prevent regressions across mathematical boundary cases, we need parameterized unit tests asserting behavior on empty inputs, zero-byte files, identical consecutive observation vectors, and very large diff strings.

---

## Objectives & Requirements
1. In [`tests/test_gate_parity.py`](../../tests/test_gate_parity.py), add parameterized tests evaluating edge cases:
   - Empty string diffs (`""`).
   - Completely identical consecutive states (asserting $\Delta S == 0.0$ and reflex trigger).
   - Massive 100k-character diffs (verifying numerical stability and bounded $\Delta S \in [0.0, 1.0]$).
   - High-variance inputs crossing threshold $\theta$ (asserting escalation trigger).
2. Verify mathematical equivalence between NumPy and PyTorch backends across all edge cases (`assert abs(np_delta - torch_delta) < 1e-4`).

---

## Files to Touch
- [`tests/test_gate_parity.py`](../../tests/test_gate_parity.py): Add parameterized edge-case test suite.
- [`octoflow/gate.py`](../../octoflow/gate.py): Ensure boundary checks handle zero division and empty arrays gracefully.

---

## Acceptance Criteria
- [ ] Parameterized tests verify: empty input, zero variance, identical states, large strings.
- [ ] Both NumPy and Torch backends agree within tolerance (`1e-4`).
- [ ] Tests execute in <0.2 seconds.
- [ ] Pytest passes: `pytest tests/test_gate_parity.py`.

