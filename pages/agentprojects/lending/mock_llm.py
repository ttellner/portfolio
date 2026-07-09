"""Mock LLM responses for lending agent scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MockResponse:
    content: str
    intent: str
    confidence: float
    strategy: str
    required_tools: list[str] = field(default_factory=list)
    escalation_risk: float = 0.0
    reasoning_steps: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


_SCENARIOS: dict[str, MockResponse] = {
    "fraud_alert": MockResponse(
        content="High fraud risk detected. Escalate to fraud operations and freeze application.",
        intent="fraud_alert",
        confidence=0.94,
        strategy="immediate_escalation",
        required_tools=["check_fraud_signals", "freeze_application", "notify_fraud_ops"],
        escalation_risk=0.9,
        reasoning_steps=["Fraud score above threshold", "Velocity and device flags present"],
    ),
    "credit_decline": MockResponse(
        content="Application exceeds risk appetite. Decline with adverse action notice.",
        intent="credit_decline",
        confidence=0.88,
        strategy="reject_with_explanation",
        required_tools=["pull_credit_bureau", "score_default_risk"],
        escalation_risk=0.2,
        reasoning_steps=["PD above policy", "Weak payment history"],
    ),
    "credit_approve": MockResponse(
        content="Applicant meets policy. Approve with standard pricing and cross-sell review.",
        intent="credit_approve",
        confidence=0.92,
        strategy="full_autonomous_resolution",
        required_tools=["pull_credit_bureau", "score_default_risk", "calculate_dti"],
        escalation_risk=0.1,
        reasoning_steps=["Low PD", "DTI within policy", "Clean fraud screen"],
    ),
    "manual_review": MockResponse(
        content="Borderline profile. Route to analyst queue with guided verification checklist.",
        intent="manual_review",
        confidence=0.8,
        strategy="guided_autonomous_resolution",
        required_tools=["verify_identity", "pull_credit_bureau"],
        escalation_risk=0.45,
        reasoning_steps=["Mixed signals on income and utilization"],
    ),
}


class MockLLM:
    def __init__(self) -> None:
        self.provider = "mock"

    def _route(self, prompt: str) -> str:
        text = prompt.lower()
        if any(k in text for k in ("fraud", "tor", "velocity", "mismatch")):
            return "fraud_alert"
        if any(k in text for k in ("decline", "reject", "high risk", "charge-off")):
            return "credit_decline"
        if any(k in text for k in ("approve", "premium", "strong", "low risk")):
            return "credit_approve"
        return "manual_review"

    def generate(self, prompt: str, **kwargs) -> MockResponse:
        scenario = self._route(prompt)
        response = _SCENARIOS[scenario]
        response.metadata = {"scenario": scenario, "provider": "mock"}
        return response
