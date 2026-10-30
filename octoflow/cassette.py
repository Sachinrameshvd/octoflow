"""Cassette recording and replay harness for deterministic offline LLM verification.

Stores (request_hash, response) pairs to record live model execution and replay
them offline in CI without external LLM dependencies.
"""

import hashlib
import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

from octoflow.logging_config import get_logger
from octoflow.provider import BaseLLMProvider, LLMResponse, redact_secrets

logger = get_logger("cassette")


def normalize_cassette_text(text: str, workspace_root: str | Path | None = None) -> str:
    """Normalize text by stripping local machine paths, temp dirs, and redacting secrets."""
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n")

    # Replace explicit workspace root if provided
    if workspace_root:
        ws_str = str(Path(workspace_root).resolve())
        normalized = normalized.replace(ws_str, "<WORKSPACE>")
        # Also try non-resolved
        normalized = normalized.replace(str(workspace_root), "<WORKSPACE>")

    # Strip macOS temp folder patterns: /var/folders/... or /private/var/folders/...
    normalized = re.sub(r"/(?:private/)?var/folders/[^\s\"\'\:]+", "<TMPDIR>", normalized)

    # Strip user home path: /Users/username or /home/username
    normalized = re.sub(r"/(?:Users|home)/[a-zA-Z0-9_\-\.]+", "<HOME>", normalized)

    # Scrub secrets
    normalized = redact_secrets(normalized)

    return normalized


def compute_request_hash(prompt: str, system_prompt: str = "") -> str:
    """Compute deterministic SHA-256 hash of normalized system prompt and user prompt."""
    norm_sys = normalize_cassette_text(system_prompt).strip()
    norm_usr = normalize_cassette_text(prompt).strip()
    payload = f"SYS:{norm_sys}\nUSR:{norm_usr}".encode()
    return hashlib.sha256(payload).hexdigest()


class CassetteEntry(BaseModel):
    """Single recorded LLM interaction."""

    request_hash: str
    prompt: str
    system_prompt: str = ""
    temperature: float = 0.0
    response_content: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    total_tokens: int = 0
    estimated_cost_dollars: float = 0.0
    estimated: bool = False


class CassetteData(BaseModel):
    """Container for recorded cassette file."""

    version: int = 1
    entries: list[CassetteEntry] = Field(default_factory=list)


class CassetteRecorder(BaseLLMProvider):
    """Wrapper provider that records LLM request/response pairs to a cassette directory."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        cassette_dir: str | Path,
        workspace_root: str | Path | None = None,
    ):
        super().__init__()
        self.wrapped_provider = provider
        self.provider_name = f"recorder({provider.provider_name})"
        self.model = provider.model
        self.cassette_dir = Path(cassette_dir)
        self.workspace_root = workspace_root
        self.cassette_dir.mkdir(parents=True, exist_ok=True)
        self.cassette_file = self.cassette_dir / "cassette.json"

        # Load existing entries if cassette file already exists
        self.entries: list[CassetteEntry] = []
        if self.cassette_file.exists():
            try:
                raw = json.loads(self.cassette_file.read_text(encoding="utf-8"))
                data = CassetteData.model_validate(raw)
                self.entries = data.entries
            except Exception as e:
                logger.warning(
                    "Failed to load existing cassette from %s: %s", self.cassette_file, e
                )

    def _record_interaction(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float,
        response: LLMResponse,
    ) -> None:
        norm_prompt = normalize_cassette_text(prompt, self.workspace_root)
        norm_sys = normalize_cassette_text(system_prompt, self.workspace_root)
        norm_content = normalize_cassette_text(response.content, self.workspace_root)
        req_hash = compute_request_hash(norm_prompt, norm_sys)

        entry = CassetteEntry(
            request_hash=req_hash,
            prompt=norm_prompt,
            system_prompt=norm_sys,
            temperature=temperature,
            response_content=norm_content,
            tokens_prompt=response.tokens_prompt,
            tokens_completion=response.tokens_completion,
            total_tokens=response.total_tokens,
            estimated_cost_dollars=response.estimated_cost_dollars,
            estimated=response.estimated,
        )
        self.entries.append(entry)
        data = CassetteData(version=1, entries=self.entries)
        self.cassette_file.write_text(json.dumps(data.model_dump(), indent=2), encoding="utf-8")

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        resp = self.wrapped_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.record_usage(resp)
        self._record_interaction(prompt, system_prompt, temperature, resp)
        return resp

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        resp = await self.wrapped_provider.agenerate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.record_usage(resp)
        self._record_interaction(prompt, system_prompt, temperature, resp)
        return resp


class ReplayProvider(BaseLLMProvider):
    """Deterministic offline provider that replays recorded responses from a cassette."""

    def __init__(
        self,
        cassette_dir: str | Path,
        workspace_root: str | Path | None = None,
    ):
        super().__init__()
        self.provider_name = "replay"
        self.model = "cassette-replay"
        self.cassette_dir = Path(cassette_dir)
        self.workspace_root = workspace_root
        self.entries: list[CassetteEntry] = []
        self._by_hash: dict[str, list[CassetteEntry]] = {}
        self._playback_index: int = 0

        cassette_file = self.cassette_dir / "cassette.json"
        if not cassette_file.exists():
            raise FileNotFoundError(f"Cassette file not found: {cassette_file}")

        raw = json.loads(cassette_file.read_text(encoding="utf-8"))
        data = CassetteData.model_validate(raw)
        self.entries = data.entries

        for entry in self.entries:
            self._by_hash.setdefault(entry.request_hash, []).append(entry)

    def _find_matching_entry(self, prompt: str, system_prompt: str) -> CassetteEntry:
        norm_prompt = normalize_cassette_text(prompt, self.workspace_root)
        norm_sys = normalize_cassette_text(system_prompt, self.workspace_root)
        req_hash = compute_request_hash(norm_prompt, norm_sys)

        # 1. Exact hash match
        if req_hash in self._by_hash and self._by_hash[req_hash]:
            # Pop entry if multiple or reuse last
            if len(self._by_hash[req_hash]) > 1:
                return self._by_hash[req_hash].pop(0)
            return self._by_hash[req_hash][0]

        # 2. Objective / prompt keyword similarity match
        p_lower = norm_prompt.lower()
        for entry in self.entries:
            # Check if key objective matches
            if "current arm objective:" in p_lower:
                obj_line = p_lower.split("current arm objective:")[1].split("\n")[0].strip()
                if obj_line and obj_line in entry.prompt.lower():
                    return entry

        # 3. Sequential fallback playback
        if self._playback_index < len(self.entries):
            entry = self.entries[self._playback_index]
            self._playback_index += 1
            return entry

        if self.entries:
            return self.entries[-1]

        raise RuntimeError(
            f"ReplayProvider: No recorded cassette entries available in {self.cassette_dir}"
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        entry = self._find_matching_entry(prompt, system_prompt)
        resp = LLMResponse(
            content=entry.response_content,
            tokens_prompt=entry.tokens_prompt,
            tokens_completion=entry.tokens_completion,
            total_tokens=entry.total_tokens,
            estimated_cost_dollars=entry.estimated_cost_dollars,
            estimated=entry.estimated,
        )
        self.record_usage(resp)
        return resp

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        import asyncio

        await asyncio.sleep(0.001)
        return self.generate(prompt, system_prompt, temperature, max_tokens)
