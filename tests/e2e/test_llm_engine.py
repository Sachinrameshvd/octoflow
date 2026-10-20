from octopus_brain import LLMEngine
from octoflow.conductor import Conductor

def test_llm_engine_integration():
    engine = LLMEngine()
    conductor = Conductor()
    result = conductor.run(engine)
    assert result is not None