"""Unit tests for octoflow/provider.py to achieve >80% line coverage."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from octoflow.errors import (
    ProviderAuthError,
    ProviderExhaustedError,
    ProviderRateLimitError,
    ProviderTransientError,
)
from octoflow.provider import (
    AnthropicProvider,
    CascadePoolLLMProvider,
    DeepSeekProvider,
    FailoverLLMProvider,
    GeminiProvider,
    GrokProvider,
    LLMConfigEntry,
    LLMResponse,
    MockLLMProvider,
    OllamaProvider,
    OpenAIProvider,
    redact_secrets,
)
from octoflow.usage import UsageLedger


@pytest.mark.unit
def test_redact_secrets():
    text = "Authorization: Bearer sk-1234567890abcdef and x-api-key: sk-ant-api03-abcdefg"
    redacted = redact_secrets(text)
    assert "sk-1234567890abcdef" not in redacted
    assert "[REDACTED" in redacted


@pytest.mark.unit
def test_anthropic_provider_lifecycle(monkeypatch):
    # Missing key raises
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        AnthropicProvider()

    provider = AnthropicProvider(api_key="test-anthropic-key")
    assert provider.provider_name == "anthropic"

    # Mock sync generate with usage
    mock_resp_data = {
        "content": [{"type": "text", "text": "Anthropic sync response"}],
        "usage": {"input_tokens": 15, "output_tokens": 30},
    }
    fake_http_resp = httpx.Response(
        200, json=mock_resp_data, request=httpx.Request("POST", provider.base_url)
    )
    monkeypatch.setattr(httpx.Client, "post", MagicMock(return_value=fake_http_resp))

    resp = provider.generate("hello anthropic", system_prompt="be concise")
    assert resp.content == "Anthropic sync response"
    assert resp.tokens_prompt == 15
    assert resp.tokens_completion == 30
    assert resp.estimated is False

    # Mock sync generate without usage (estimated)
    mock_resp_no_usage = {
        "content": [{"type": "text", "text": "Anthropic estimated"}],
    }
    fake_no_usage_resp = httpx.Response(
        200, json=mock_resp_no_usage, request=httpx.Request("POST", provider.base_url)
    )
    monkeypatch.setattr(httpx.Client, "post", MagicMock(return_value=fake_no_usage_resp))
    resp_est = provider.generate("hello")
    assert resp_est.estimated is True


@pytest.mark.unit
@pytest.mark.anyio
async def test_anthropic_provider_agenerate(monkeypatch):
    provider = AnthropicProvider(api_key="test-key")
    mock_resp_data = {
        "content": [{"type": "text", "text": "Anthropic async"}],
        "usage": {"input_tokens": 20, "output_tokens": 40},
    }
    fake_resp = httpx.Response(
        200, json=mock_resp_data, request=httpx.Request("POST", provider.base_url)
    )
    monkeypatch.setattr(httpx.AsyncClient, "post", AsyncMock(return_value=fake_resp))

    resp = await provider.agenerate("hello async")
    assert resp.content == "Anthropic async"
    assert resp.tokens_prompt == 20


@pytest.mark.unit
def test_openai_provider_lifecycle(monkeypatch):
    # Missing key raises
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIProvider()

    provider = OpenAIProvider(api_key="test-openai-key", base_url="https://api.openai.com/v1")
    assert provider.base_url.endswith("/chat/completions")

    # Mock generate with usage
    mock_resp_data = {
        "choices": [{"message": {"role": "assistant", "content": "OpenAI sync"}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 24},
    }
    fake_resp = httpx.Response(
        200, json=mock_resp_data, request=httpx.Request("POST", provider.base_url)
    )
    monkeypatch.setattr(httpx.Client, "post", MagicMock(return_value=fake_resp))

    resp = provider.generate("prompt", system_prompt="sys")
    assert resp.content == "OpenAI sync"
    assert resp.tokens_prompt == 12
    assert resp.estimated is False

    # Mock generate without usage
    mock_no_usage = {
        "choices": [{"message": {"role": "assistant", "content": "No usage"}}],
    }
    monkeypatch.setattr(
        httpx.Client,
        "post",
        MagicMock(
            return_value=httpx.Response(
                200, json=mock_no_usage, request=httpx.Request("POST", provider.base_url)
            )
        ),
    )
    resp_no_usage = provider.generate("prompt")
    assert resp_no_usage.estimated is True


@pytest.mark.unit
@pytest.mark.anyio
async def test_openai_provider_agenerate(monkeypatch):
    provider = OpenAIProvider(api_key="test-key")
    mock_resp_data = {
        "choices": [{"message": {"role": "assistant", "content": "OpenAI async"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10},
    }
    fake_resp = httpx.Response(
        200, json=mock_resp_data, request=httpx.Request("POST", provider.base_url)
    )
    monkeypatch.setattr(httpx.AsyncClient, "post", AsyncMock(return_value=fake_resp))

    resp = await provider.agenerate("async prompt")
    assert resp.content == "OpenAI async"


@pytest.mark.unit
def test_subclass_providers_gemini_grok_deepseek(monkeypatch):
    # Gemini
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiProvider()
    gem = GeminiProvider(api_key="gem-key")
    assert gem.provider_name == "gemini"
    assert "googleapis.com" in gem.base_url

    # Grok
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    with pytest.raises(ValueError, match="XAI_API_KEY"):
        GrokProvider()
    grok = GrokProvider(api_key="grok-key")
    assert grok.provider_name == "grok"
    assert "x.ai" in grok.base_url

    # DeepSeek
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        DeepSeekProvider()
    ds = DeepSeekProvider(api_key="ds-key")
    assert ds.provider_name == "deepseek"
    assert "deepseek.com" in ds.base_url


@pytest.mark.unit
def test_ollama_provider_lifecycle(monkeypatch):
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3")
    assert provider.provider_name == "ollama"

    mock_resp_data = {
        "response": "Ollama response",
        "prompt_eval_count": 5,
        "eval_count": 15,
    }
    fake_resp = httpx.Response(
        200, json=mock_resp_data, request=httpx.Request("POST", f"{provider.base_url}/api/generate")
    )
    monkeypatch.setattr(httpx.Client, "post", MagicMock(return_value=fake_resp))

    resp = provider.generate("hello ollama")
    assert resp.content == "Ollama response"
    assert resp.tokens_prompt == 5
    assert resp.tokens_completion == 15
    assert resp.estimated is False

    # Without eval counts
    mock_no_eval = {"response": "No eval counts"}
    monkeypatch.setattr(
        httpx.Client,
        "post",
        MagicMock(
            return_value=httpx.Response(
                200,
                json=mock_no_eval,
                request=httpx.Request("POST", f"{provider.base_url}/api/generate"),
            )
        ),
    )
    resp_no_eval = provider.generate("hello")
    assert resp_no_eval.estimated is True


@pytest.mark.unit
@pytest.mark.anyio
async def test_ollama_provider_agenerate(monkeypatch):
    provider = OllamaProvider()
    mock_resp_data = {
        "response": "Async Ollama",
        "prompt_eval_count": 4,
        "eval_count": 8,
    }
    fake_resp = httpx.Response(
        200, json=mock_resp_data, request=httpx.Request("POST", f"{provider.base_url}/api/generate")
    )
    monkeypatch.setattr(httpx.AsyncClient, "post", AsyncMock(return_value=fake_resp))

    resp = await provider.agenerate("async ollama")
    assert resp.content == "Async Ollama"


@pytest.mark.unit
def test_failover_provider_sync_and_async():
    p1 = MockLLMProvider()
    p2 = MockLLMProvider()

    # Fail p1 on generate
    p1.generate = MagicMock(
        side_effect=ProviderTransientError("503 Server Error", provider="mock", status=503)
    )

    failover_log = []

    def on_failover_cb(from_p, to_p, err):
        failover_log.append((from_p, to_p))

    failover = FailoverLLMProvider(primary=p1, fallbacks=[p2], on_failover=on_failover_cb)
    resp = failover.generate("test prompt")
    assert resp is not None
    assert len(failover_log) == 1
    assert failover_log[0] == ("MockLLMProvider", "MockLLMProvider")

    # All providers fail -> ProviderExhaustedError
    p2.generate = MagicMock(
        side_effect=ProviderRateLimitError("429 Too Many Requests", provider="mock", status=429)
    )
    with pytest.raises(ProviderExhaustedError) as exc_info:
        failover.generate("test prompt")
    assert len(exc_info.value.failures) == 2

    # set_ledger propagation
    ledger = UsageLedger()
    failover.set_ledger(ledger)
    assert failover.usage_ledger is ledger
    assert p1.usage_ledger is ledger
    assert p2.usage_ledger is ledger


@pytest.mark.unit
@pytest.mark.anyio
async def test_failover_provider_agenerate_flow():
    p1 = MockLLMProvider()
    p2 = MockLLMProvider()

    p1.agenerate = AsyncMock(
        side_effect=ProviderAuthError("401 Unauthorized", provider="mock", status=401)
    )
    p2.agenerate = AsyncMock(
        return_value=LLMResponse(
            content="fallback async ok", tokens_prompt=5, tokens_completion=5, total_tokens=10
        )
    )

    failover = FailoverLLMProvider(primary=p1, fallbacks=[p2])
    resp = await failover.agenerate("async test")
    assert resp.content == "fallback async ok"
    assert p1.is_disabled is True  # Auth error disables provider

    # Once p1 is disabled, second call skips p1 directly
    resp2 = await failover.agenerate("async test 2")
    assert resp2.content == "fallback async ok"


@pytest.mark.unit
def test_cascade_pool_llm_provider(tmp_path):
    entries = [
        LLMConfigEntry(
            id="entry-1", name="Primary Mock", provider="mock", model="mock-model", priority=1
        ),
        LLMConfigEntry(
            id="entry-2", name="Secondary Mock", provider="mock", model="mock-model-2", priority=2
        ),
    ]

    pool = CascadePoolLLMProvider(entries=entries, dry_run=True)
    summary = pool.get_status_summary()
    assert len(summary) == 2
    assert summary[0]["status"] == "ACTIVE"
    assert summary[1]["status"] == "STANDBY"

    resp = pool.generate("hello cascade")
    assert resp is not None
    assert resp.content

    # Empty pool non-dry-run raises ProviderExhaustedError
    empty_pool = CascadePoolLLMProvider(entries=[], dry_run=False)
    with pytest.raises(ProviderExhaustedError, match="exhausted"):
        empty_pool.generate("hello")

    # Empty pool dry-run generates mock response
    empty_pool_dry = CascadePoolLLMProvider(entries=[], dry_run=True)
    dry_resp = empty_pool_dry.generate("hello dry run")
    assert dry_resp is not None


@pytest.mark.unit
def test_provider_factory_and_single_builder(monkeypatch):
    from octoflow.config import OctoFlowConfig
    from octoflow.provider import _build_single_provider, get_llm_provider

    # Fake / Replay
    fake_p = _build_single_provider("fake", OctoFlowConfig(model_provider="fake"))
    assert fake_p is not None

    # Mock provider dry run
    mock_p = _build_single_provider("mock", OctoFlowConfig(model_provider="mock"), dry_run=True)
    assert isinstance(mock_p, MockLLMProvider)

    # Mock provider without dry run raises
    cfg_mock_nodry = OctoFlowConfig(
        model_provider="mock", allow_mock=False, dry_run=False, is_bench=False
    )
    monkeypatch.delenv("OCTOFLOW_DRY_RUN", raising=False)
    with pytest.raises(ProviderExhaustedError):
        _build_single_provider("mock", cfg_mock_nodry, dry_run=False)

    # Anthropic with API key
    cfg_anthropic = OctoFlowConfig(model_provider="anthropic", anthropic_api_key="test-key")
    ant_p = _build_single_provider("anthropic", cfg_anthropic)
    assert isinstance(ant_p, AnthropicProvider)

    # Anthropic fast tier
    cfg_anthropic_fast = OctoFlowConfig(
        model_provider="anthropic", anthropic_api_key="test-key", fast_model="claude-haiku"
    )
    ant_fast = _build_single_provider("anthropic", cfg_anthropic_fast, tier="fast")
    assert ant_fast.model == "claude-haiku"

    # Anthropic frontier tier
    cfg_anthropic_frontier = OctoFlowConfig(
        model_provider="anthropic", anthropic_api_key="test-key", frontier_model="claude-opus"
    )
    ant_front = _build_single_provider("anthropic", cfg_anthropic_frontier, tier="frontier")
    assert ant_front.model == "claude-opus"

    # Anthropic missing key raises
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_no_ant = OctoFlowConfig(model_provider="anthropic")
    cfg_no_ant.api_key = None
    cfg_no_ant.anthropic_api_key = None
    with pytest.raises(ProviderExhaustedError):
        _build_single_provider("anthropic", cfg_no_ant, dry_run=False)

    # OpenAI with key
    cfg_openai = OctoFlowConfig(model_provider="openai", openai_api_key="test-key")
    oai_p = _build_single_provider("openai", cfg_openai)
    assert isinstance(oai_p, OpenAIProvider)

    # OpenAI tiers
    oai_fast = _build_single_provider(
        "openai", OctoFlowConfig(openai_api_key="k", fast_model="gpt-mini"), tier="fast"
    )
    assert oai_fast.model == "gpt-mini"
    oai_front = _build_single_provider(
        "openai", OctoFlowConfig(openai_api_key="k", frontier_model="o3"), tier="frontier"
    )
    assert oai_front.model == "o3"

    # OpenAI missing key raises
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg_no_oai = OctoFlowConfig(model_provider="openai")
    cfg_no_oai.api_key = None
    cfg_no_oai.openai_api_key = None
    with pytest.raises(ProviderExhaustedError):
        _build_single_provider("openai", cfg_no_oai, dry_run=False)

    # Gemini with key and missing key
    cfg_gem = OctoFlowConfig(gemini_api_key="gem-key")
    gem_p = _build_single_provider("gemini", cfg_gem)
    assert isinstance(gem_p, GeminiProvider)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    cfg_no_gem = OctoFlowConfig(model_provider="gemini")
    cfg_no_gem.api_key = None
    cfg_no_gem.gemini_api_key = None
    with pytest.raises(ProviderExhaustedError):
        _build_single_provider("gemini", cfg_no_gem, dry_run=False)

    # Grok with key and missing key
    cfg_grok = OctoFlowConfig(grok_api_key="grok-key")
    grok_p = _build_single_provider("grok", cfg_grok)
    assert isinstance(grok_p, GrokProvider)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    cfg_no_grok = OctoFlowConfig(model_provider="grok")
    cfg_no_grok.api_key = None
    cfg_no_grok.grok_api_key = None
    with pytest.raises(ProviderExhaustedError):
        _build_single_provider("grok", cfg_no_grok, dry_run=False)

    # DeepSeek with key and missing key
    cfg_ds = OctoFlowConfig(deepseek_api_key="ds-key")
    ds_p = _build_single_provider("deepseek", cfg_ds)
    assert isinstance(ds_p, DeepSeekProvider)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    cfg_no_ds = OctoFlowConfig(model_provider="deepseek")
    cfg_no_ds.api_key = None
    cfg_no_ds.deepseek_api_key = None
    with pytest.raises(ProviderExhaustedError):
        _build_single_provider("deepseek", cfg_no_ds, dry_run=False)

    # Ollama homogeneous & heterogeneous
    cfg_ollama_homo = OctoFlowConfig(model_provider="ollama", model_name="llama3")
    ol_p = _build_single_provider("ollama", cfg_ollama_homo)
    assert isinstance(ol_p, OllamaProvider)
    assert ol_p.model == "llama3"

    cfg_ollama_hetero = OctoFlowConfig(model_provider="anthropic", fast_model="qwen-fast")
    ol_hetero = _build_single_provider("ollama", cfg_ollama_hetero, tier="fast")
    assert ol_hetero.model == "qwen-fast"

    # Unsupported provider
    with pytest.raises(ProviderExhaustedError, match="Unsupported provider backend"):
        _build_single_provider("nonexistent_provider", OctoFlowConfig(), dry_run=False)

    # get_llm_provider with failover
    cfg_failover = OctoFlowConfig(
        model_provider="anthropic",
        anthropic_api_key="ant-key",
        enable_failover=True,
        fallback_providers=["openai", "ollama"],
        openai_api_key="oai-key",
    )
    failover_prov = get_llm_provider(cfg_failover)
    assert isinstance(failover_prov, FailoverLLMProvider)


@pytest.mark.unit
def test_classify_http_error_branches():
    from octoflow.errors import ProviderError, ProviderRequestError
    from octoflow.provider import classify_http_error

    e400 = classify_http_error(400, body="bad payload")
    assert isinstance(e400, ProviderRequestError)

    e_transient = classify_http_error(RuntimeError("connection dropped"))
    assert isinstance(e_transient, ProviderTransientError)

    e_default = classify_http_error("some error message")
    assert isinstance(e_default, ProviderError)

    e429 = classify_http_error(429, headers={"retry-after": "2.5"})
    assert isinstance(e429, ProviderRateLimitError)
    assert e429.retry_after == 2.5


@pytest.mark.unit
def test_retry_http_request_legacy():
    from octoflow.provider import retry_http_request

    fake_resp = MagicMock(spec=httpx.Response)
    fake_resp.raise_for_status = MagicMock()
    res = retry_http_request(lambda: fake_resp)
    assert res is fake_resp


@pytest.mark.unit
@pytest.mark.anyio
async def test_aretry_http_request_legacy():
    from octoflow.provider import aretry_http_request

    fake_resp = MagicMock(spec=httpx.Response)
    fake_resp.raise_for_status = MagicMock()

    async def fake_coro():
        return fake_resp

    res = await aretry_http_request(fake_coro)
    assert res is fake_resp


@pytest.mark.unit
@pytest.mark.anyio
async def test_aexecute_with_retry_flows():
    from octoflow.provider import aexecute_with_retry

    # 1. Rate limit retry then success
    sleep_calls = []

    async def dummy_asleep(d):
        sleep_calls.append(d)

    call_count = [0]
    req1 = httpx.Request("POST", "https://api.openai.com")

    async def rate_limited_coro():
        call_count[0] += 1
        if call_count[0] == 1:
            raise httpx.HTTPStatusError(
                "Rate limited",
                request=req1,
                response=httpx.Response(429, headers={"retry-after": "1"}, request=req1),
            )
        return httpx.Response(200, json={"ok": True}, request=req1)

    res = await aexecute_with_retry(rate_limited_coro, provider="openai", asleep_fn=dummy_asleep)
    assert res.status_code == 200
    assert len(sleep_calls) == 1

    # 2. Transient retry then success
    call_count_transient = [0]
    req2 = httpx.Request("POST", "https://api.anthropic.com")

    async def transient_coro():
        call_count_transient[0] += 1
        if call_count_transient[0] == 1:
            raise httpx.HTTPStatusError(
                "500 Server Error", request=req2, response=httpx.Response(500, request=req2)
            )
        return httpx.Response(200, json={"ok": True}, request=req2)

    res2 = await aexecute_with_retry(transient_coro, provider="anthropic", asleep_fn=dummy_asleep)
    assert res2.status_code == 200

    # 3. Auth error fails immediately and disables provider
    mock_prov = MockLLMProvider()

    async def auth_coro():
        req = httpx.Request("POST", "https://api.anthropic.com")
        raise httpx.HTTPStatusError(
            "401 Unauthorized", request=req, response=httpx.Response(401, request=req)
        )

    with pytest.raises(ProviderAuthError):
        await aexecute_with_retry(auth_coro, provider=mock_prov, asleep_fn=dummy_asleep)
    assert mock_prov.is_disabled is True


@pytest.mark.unit
def test_mock_llm_provider_templates():
    mock = MockLLMProvider()

    # Scripted pattern
    mock.script_responses["custom-marker"] = "Scripted output 123"
    resp_script = mock.generate("Please respond to custom-marker immediately")
    assert resp_script.content == "Scripted output 123"

    # Developer question
    resp_dev = mock.generate(
        "developer question: what is the architecture?",
        system_prompt="You are System Architect (Arm 0)",
    )
    assert "System Architect" in resp_dev.content

    # Test runner prompt
    resp_test = mock.generate("run pytest on the test suite")
    assert "run_command" in resp_test.content

    # Limiter prompt
    resp_limiter = mock.generate("generate a slidingwindowratelimiter class in limiter.py")
    assert "SlidingWindowRateLimiter" in resp_limiter.content


@pytest.mark.unit
def test_cascade_pool_runtime_failover():
    p1 = MockLLMProvider()
    p2 = MockLLMProvider()

    p1.generate = MagicMock(
        side_effect=ProviderRateLimitError("429 Quota exhausted", provider="p1", status=429)
    )
    p2.generate = MagicMock(
        return_value=LLMResponse(
            content="cascade fallback ok", tokens_prompt=10, tokens_completion=10, total_tokens=20
        )
    )

    events = []

    def on_cascade_failover(ev):
        events.append(ev)

    pool = CascadePoolLLMProvider(entries=[], dry_run=False)
    pool.providers = [p1, p2]
    pool.telemetry = [
        {
            "id": "p1",
            "name": "P1",
            "provider": "p1",
            "model": "m1",
            "status": "ACTIVE",
            "tokens_used": 0,
            "failover_count": 0,
        },
        {
            "id": "p2",
            "name": "P2",
            "provider": "p2",
            "model": "m2",
            "status": "STANDBY",
            "tokens_used": 0,
            "failover_count": 0,
        },
    ]
    pool.on_failover = on_cascade_failover

    resp = pool.generate("prompt")
    assert resp.content == "cascade fallback ok"
    assert len(events) == 1
    assert events[0]["from_id"] == "p1"
    assert events[0]["to_id"] == "p2"
    assert pool.telemetry[0]["status"] == "EXHAUSTED"
    assert pool.telemetry[1]["status"] == "ACTIVE"
