import pytest

pytestmark = pytest.mark.unit
from octoflow.arm import ArmAgent
from octoflow.bus import InterBrachialBus
from octoflow.config import ArmRoleConfig
from octoflow.encoder import CodeSensoryEncoder
from octoflow.gate import SurpriseGate
from octoflow.memory import VerticalLobeMemory
from octoflow.provider import MockLLMProvider
from octoflow.tools import WorkspaceSandbox


@pytest.fixture
def arm(tmp_path):
    sandbox = WorkspaceSandbox(workspace_dir=tmp_path)
    bus = InterBrachialBus(n_arms=8)
    gate = SurpriseGate(arm_id=2, gate_mode="numpy")
    memory = VerticalLobeMemory()
    encoder = CodeSensoryEncoder()
    provider = MockLLMProvider()
    role = ArmRoleConfig(
        arm_id=2,
        name="backend",
        title="Backend Developer",
        description="Backend logic",
        workspace_domain=["*.py"],
    )
    return ArmAgent(
        role_config=role,
        sandbox=sandbox,
        provider=provider,
        bus=bus,
        memory=memory,
        encoder=encoder,
    )


def test_parse_clean_json(arm):
    sample = '{"action": "write_file", "path": "limiter.py", "content": "class Limiter: pass"}'
    action = arm._parse_llm_action(sample)
    assert action["action"] == "write_file"
    assert action["path"] == "limiter.py"
    assert "class Limiter" in action["content"]


def test_parse_markdown_fenced_json(arm):
    sample = """Here is the implementation:
```json
{
  "action": "write_file",
  "path": "limiter.py",
  "content": "import time\\nclass TokenBucket: pass"
}
```
Let me know if you need more."""
    action = arm._parse_llm_action(sample)
    assert action["action"] == "write_file"
    assert action["path"] == "limiter.py"
    assert "TokenBucket" in action["content"]


def test_parse_trailing_comma_repair(arm):
    sample = """{
  "action": "write_file",
  "path": "limiter.py",
  "content": "x = 1",
}"""
    action = arm._parse_llm_action(sample)
    assert action["action"] == "write_file"
    assert action["path"] == "limiter.py"
    assert action["content"] == "x = 1"


def test_parse_unescaped_control_characters(arm):
    sample = '{"action": "write_file", "path": "limiter.py", "content": "line 1\nline 2\ttab"}'
    action = arm._parse_llm_action(sample)
    assert action["action"] == "write_file"
    assert "line 1" in action["content"]


def test_parse_field_synonyms(arm):
    sample = '{"tool": "write", "file": "app.py", "code": "print(1)", "desc": "write script"}'
    action = arm._parse_llm_action(sample)
    assert action["action"] == "write_file"
    assert action["path"] == "app.py"
    assert action["content"] == "print(1)"
    assert action["explanation"] == "write script"


def test_parse_command_synonyms(arm):
    sample = '{"tool": "shell", "cmd": "pytest tests/test_limiter.py"}'
    action = arm._parse_llm_action(sample)
    assert action["action"] == "run_command"
    assert action["command"] == "pytest tests/test_limiter.py"


def test_parse_completion_synonyms(arm):
    for synonym in ["done", "complete", "finish", "stop", "quiescent"]:
        action = arm._parse_llm_action(f'{{"action": "{synonym}"}}')
        assert action["action"] == "mark_quiescent"


def test_reject_unknown_tool_with_corrective_error(arm):
    sample = '{"action": "browse_web", "url": "https://python.org"}'
    action = arm._parse_llm_action(sample)
    assert action["action"] == "invalid_action"
    assert "Unknown tool 'browse_web'" in action["error"]
    assert "Allowed tools" in action["error"]


def test_missing_command_rejected_with_corrective_error(arm):
    sample = '{"action": "run_command"}'
    action = arm._parse_llm_action(sample)
    assert action["action"] == "invalid_action"
    assert "Missing 'command'" in action["error"]


def test_parse_direct_python_block_fallback(arm):
    sample = """```python
import time

def allow_request():
    return True
```"""
    action = arm._parse_llm_action(sample)
    assert action["action"] == "write_file"
    assert action["path"] == "main.py"
    assert "allow_request" in action["content"]


def test_parse_direct_python_test_block_fallback(arm):
    sample = """```python
import pytest

def test_limiter():
    assert True
```"""
    action = arm._parse_llm_action(sample)
    assert action["action"] == "write_file"
    assert action["path"] == "test_main.py"
    assert "test_limiter" in action["content"]


def test_completely_unparseable_output(arm):
    sample = "I'm not sure how to solve this, can you help me?"
    action = arm._parse_llm_action(sample)
    assert action["action"] == "invalid_action"
    assert "Invalid tool format" in action["error"]
