"""LLM client factory: Ollama when reachable, MockLLM otherwise."""

from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.request
from typing import Protocol

from mock_llm import MockLLM, MockResponse


def _ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def _ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "deepseek-v2:16b")


DEFAULT_OLLAMA_MODEL = "deepseek-v2:16b"

_LENDING_INTENT_KW = {
    "fraud_alert": ["fraud", "tor", "velocity", "mismatch", "escalate", "freeze"],
    "credit_decline": ["decline", "reject", "high risk", "charge-off", "adverse"],
    "credit_approve": ["approve", "premium", "strong", "low risk", "cross-sell"],
    "manual_review": ["review", "borderline", "verify", "analyst", "mixed"],
}


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def _is_hosted_deploy() -> bool:
    """True when running on a cloud host where local Ollama is not expected."""
    return any(
        os.getenv(key)
        for key in (
            "RAILWAY_ENVIRONMENT",
            "RAILWAY_SERVICE_NAME",
            "AWS_EXECUTION_ENV",
            "AWS_APP_RUNNER_SERVICE_ID",
        )
    )


def _force_mock_from_env() -> bool:
    return os.getenv("FORCE_MOCK_LLM", "").strip().lower() in {"1", "true", "yes"}


def _ollama_host_explicit() -> bool:
    return bool(os.getenv("OLLAMA_HOST", "").strip())


def _is_local_ollama_host(host: str) -> bool:
    return host.rstrip("/") in {"http://localhost:11434", "http://127.0.0.1:11434"}


def _ollama_invite_password() -> str:
    return os.getenv("OLLAMA_INVITE_PASSWORD", "").strip()


def is_ollama_invite_configured() -> bool:
    """True when server has both a remote host and invite password configured."""
    return bool(_ollama_host_explicit() and _ollama_invite_password())


def verify_ollama_invite_password(password: str) -> bool:
    """Check invite password against OLLAMA_INVITE_PASSWORD (constant-time)."""
    expected = _ollama_invite_password()
    if not expected or not password:
        return False
    return secrets.compare_digest(password, expected)


def _should_use_mock(invite_unlocked: bool) -> bool:
    """Default to mock unless invite password unlocked live Ollama."""
    if _force_mock_from_env():
        return True
    return not invite_unlocked


def _should_skip_ollama_probe(host: str, invite_unlocked: bool = False) -> bool:
    """Skip Ollama probes when mock mode is active or localhost on cloud without invite."""
    if _should_use_mock(invite_unlocked):
        return True
    if invite_unlocked and _ollama_host_explicit():
        return False
    return _is_hosted_deploy() and _is_local_ollama_host(host) and not _ollama_host_explicit()


def is_ollama_available(base_url: str | None = None) -> bool:
    """Return True when an Ollama server responds at base_url."""
    base_url = (base_url or _ollama_host()).rstrip("/")
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=3) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def list_ollama_models(base_url: str | None = None) -> list[str]:
    """Return installed Ollama model names, or an empty list."""
    base_url = (base_url or _ollama_host()).rstrip("/")
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return []


def detect_lending_intent(prompt: str) -> str:
    text = prompt.lower()
    for intent, keywords in _LENDING_INTENT_KW.items():
        if any(keyword in text for keyword in keywords):
            return intent
    return "manual_review"


class LendingLLM(Protocol):
    provider: str

    def generate(self, prompt: str, **kwargs) -> MockResponse: ...


class OllamaLLM:
    """Live Ollama client matching MockLLM.generate() for agent compatibility."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        fallback: MockLLM | None = None,
    ) -> None:
        self.model = model or _ollama_model()
        self.base_url = (base_url or _ollama_host()).rstrip("/")
        self._fallback = fallback or MockLLM()
        self.provider = "ollama"

    def generate(self, prompt: str, **kwargs) -> MockResponse:
        try:
            from openai import OpenAI

            client = OpenAI(base_url=f"{self.base_url}/v1", api_key="ollama")
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a lending underwriting assistant. Respond in 2-4 concise "
                            "sentences with a clear recommendation (approve, decline, manual "
                            "review, or fraud escalation)."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=kwargs.get("max_tokens", 512),
                temperature=kwargs.get("temperature", 0.2),
            )
            content = response.choices[0].message.content or ""
            intent = detect_lending_intent(f"{prompt}\n{content}")
            return MockResponse(
                content=content.strip(),
                intent=intent,
                confidence=0.9,
                strategy="full_autonomous_resolution",
                required_tools=[],
                escalation_risk=0.15 if intent == "fraud_alert" else 0.1,
                reasoning_steps=["Live Ollama inference", f"Model: {self.model}"],
                metadata={"provider": "ollama", "model": self.model, "host": self.base_url},
            )
        except Exception:
            fallback = self._fallback.generate(prompt, **kwargs)
            fallback.metadata = {
                **fallback.metadata,
                "provider": "mock",
                "fallback_from": "ollama",
                "model": self.model,
            }
            return fallback


def get_llm_status(
    invite_unlocked: bool = False,
    base_url: str | None = None,
    model: str | None = None,
) -> dict:
    """Summarize which LLM backend the demo will use."""
    _load_dotenv()
    host = (base_url or _ollama_host()).rstrip("/")
    model = model or _ollama_model()

    if _should_use_mock(invite_unlocked):
        detail = (
            "Simulation mode: mock underwriting narratives are active. "
            "Enter the invite password to use live Ollama."
        )
        hint = ""
        if is_ollama_invite_configured():
            hint = (
                "Invite-only Ollama is configured on this server. "
                "Enter the password above to connect via the configured `OLLAMA_HOST`."
            )
        elif _is_hosted_deploy():
            hint = (
                "Hosted deploy: set `OLLAMA_HOST` and `OLLAMA_INVITE_PASSWORD` in Railway "
                "to enable invite-only live Ollama."
            )
        else:
            hint = (
                "Local dev: set `OLLAMA_HOST` and `OLLAMA_INVITE_PASSWORD` in your `.env` file, "
                "then enter the password above."
            )
        return {
            "mode": "SIMULATION",
            "provider": "mock",
            "host": host,
            "model": model,
            "available_models": [],
            "detail": detail,
            "hint": hint,
            "invite_configured": is_ollama_invite_configured(),
        }

    if not _ollama_host_explicit():
        return {
            "mode": "SIMULATION",
            "provider": "mock",
            "host": host,
            "model": model,
            "available_models": [],
            "detail": (
                "Invite accepted, but `OLLAMA_HOST` is not configured on this server. "
                "Using simulation mode."
            ),
            "hint": "Set `OLLAMA_HOST` to your remote Ollama URL in Railway or `.env`.",
            "invite_configured": False,
        }

    if _should_skip_ollama_probe(host, invite_unlocked=True):
        return {
            "mode": "SIMULATION",
            "provider": "mock",
            "host": host,
            "model": model,
            "available_models": [],
            "detail": "Simulation mode active (Ollama probe skipped).",
            "hint": "",
            "invite_configured": is_ollama_invite_configured(),
        }

    reachable = is_ollama_available(host)
    models = list_ollama_models(host) if reachable else []
    model_ready = any(model in name or name.startswith(model.split(":")[0]) for name in models)

    if reachable and model_ready:
        mode = "LIVE"
        provider = "ollama"
        detail = f"Invite unlocked — Ollama LIVE at `{host}` with model `{model}`."
        hint = ""
    elif reachable:
        mode = "LIVE"
        provider = "ollama"
        detail = (
            f"Invite unlocked — Ollama reachable at `{host}`, but `{model}` is not installed. "
            "Calls will fall back to mock responses on error."
        )
        hint = ""
    else:
        mode = "SIMULATION"
        provider = "mock"
        detail = (
            f"Invite unlocked, but Ollama is not reachable at `{host}`. "
            "Using simulation mode."
        )
        hint = "Verify your remote Ollama server is running and reachable from Railway."

    return {
        "mode": mode,
        "provider": provider,
        "host": host,
        "model": model,
        "available_models": models,
        "detail": detail,
        "hint": hint,
        "invite_configured": is_ollama_invite_configured(),
    }


def get_llm_client(
    invite_unlocked: bool = False,
    model: str | None = None,
    base_url: str | None = None,
) -> LendingLLM:
    """Return OllamaLLM when invite is unlocked and host is reachable, otherwise MockLLM."""
    _load_dotenv()
    if _should_use_mock(invite_unlocked):
        return MockLLM()

    host = (base_url or _ollama_host()).rstrip("/")
    selected_model = model or _ollama_model()
    if _ollama_host_explicit() and is_ollama_available(host):
        return OllamaLLM(model=selected_model, base_url=host)

    return MockLLM()
