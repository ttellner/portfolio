"""LLM client factory: Ollama when reachable, MockLLM otherwise."""

from __future__ import annotations

import json
import os
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


def get_llm_status(base_url: str | None = None, model: str | None = None) -> dict:
    """Summarize which LLM backend the demo will use."""
    _load_dotenv()
    host = (base_url or _ollama_host()).rstrip("/")
    model = model or _ollama_model()
    reachable = is_ollama_available(host)
    models = list_ollama_models(host) if reachable else []
    model_ready = any(model in name or name.startswith(model.split(":")[0]) for name in models)

    if reachable and model_ready:
        mode = "LIVE"
        provider = "ollama"
        detail = f"Ollama reachable at {host} with model `{model}`."
    elif reachable:
        mode = "LIVE"
        provider = "ollama"
        detail = (
            f"Ollama reachable at {host}, but `{model}` is not installed. "
            "The client will attempt the call and fall back to mock on error."
        )
    else:
        mode = "SIMULATION"
        provider = "mock"
        detail = (
            f"Ollama not reachable at {host}. Using mock responses "
            "(expected on AWS App Runner / GitHub-hosted deploy)."
        )

    return {
        "mode": mode,
        "provider": provider,
        "host": host,
        "model": model,
        "available_models": models,
        "detail": detail,
    }


def get_llm_client(
  prefer_ollama: bool = True,
  force_mock: bool = False,
  model: str | None = None,
  base_url: str | None = None,
) -> LendingLLM:
    """Return OllamaLLM when reachable, otherwise MockLLM."""
    _load_dotenv()
    if force_mock:
        client: LendingLLM = MockLLM()
        return client

    host = (base_url or _ollama_host()).rstrip("/")
    selected_model = model or _ollama_model()
    if prefer_ollama and is_ollama_available(host):
        return OllamaLLM(model=selected_model, base_url=host)

    return MockLLM()
