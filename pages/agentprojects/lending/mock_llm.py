"""Mock LLM: loan-product interpretation and underwriting narration."""

from __future__ import annotations

import re
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


_LOAN_PRODUCT_KW: dict[str, list[str]] = {
    "debt_consolidation": [
        "debt",
        "consolidat",
        "pay off",
        "credit card",
        "combine",
    ],
    "auto_loan": [
        "auto",
        "car",
        "vehicle",
        "truck",
        "suv",
    ],
    "home_improvement": [
        "home",
        "improvement",
        "renovation",
        "remodel",
        "heloc",
        "equity",
        "kitchen",
        "bathroom",
    ],
}

_NARRATION: dict[str, dict[str, str]] = {
    "debt_consolidation": {
        "approved": (
            "Debt consolidation fits your profile. Unsecured balances can be rolled into "
            "one payment within policy DTI and your savings cushion supports the request."
        ),
        "declined": (
            "Debt consolidation is not recommended right now. Unsecured balances are high "
            "relative to savings or the projected payment exceeds policy DTI."
        ),
        "manual_review": (
            "Debt consolidation needs analyst review. Balances and savings are borderline "
            "for the proposed consolidation amount."
        ),
    },
    "auto_loan": {
        "approved": (
            "Auto loan pre-qualification is favorable. Verified direct deposits support "
            "the maximum monthly payment shown below."
        ),
        "declined": (
            "Auto financing is not available at this payment level. Direct-deposit income "
            "does not support an additional car payment within bank policy."
        ),
        "manual_review": (
            "Auto loan request needs review. Deposit income supports a modest payment but "
            "is below the preferred auto threshold."
        ),
    },
    "home_improvement": {
        "approved": (
            "Home improvement equity line is available. Property value, mortgage balance, "
            "and equity support a secured line for renovations."
        ),
        "declined": (
            "Home improvement line cannot be offered. Available equity or credit profile "
            "does not meet secured-line policy."
        ),
        "manual_review": (
            "Home improvement request needs review. Equity is present but the approved "
            "line amount is below the preferred renovation threshold."
        ),
    },
}


def interpret_loan_product(prompt: str) -> dict:
    """Classify natural-language request into a loan product."""
    text = prompt.lower()
    scores: dict[str, int] = {}
    for product, keywords in _LOAN_PRODUCT_KW.items():
        scores[product] = sum(1 for kw in keywords if kw in text)

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return {
            "loan_product": "unknown",
            "confidence": 0.0,
            "reason": "Could not match debt consolidation, auto loan, or home improvement.",
        }

    confidence = min(0.95, 0.55 + scores[best] * 0.15)
    return {
        "loan_product": best,
        "confidence": round(confidence, 2),
        "reason": f"Matched {scores[best]} keyword(s) for {best.replace('_', ' ')}.",
    }


def _extract_amount(prompt: str) -> int | None:
    match = re.search(r"\$?\s*([\d,]+)\s*k?\b", prompt.lower())
    if not match:
        return None
    raw = match.group(1).replace(",", "")
    amount = int(raw)
    if "k" in prompt.lower()[match.end() - 2 : match.end() + 1]:
        amount *= 1000
    return amount


class MockLLM:
    def __init__(self) -> None:
        self.provider = "mock"

    def interpret_request(self, prompt: str) -> dict:
        result = interpret_loan_product(prompt)
        result["requested_amount"] = _extract_amount(prompt)
        return result

    def generate(self, prompt: str, **kwargs) -> MockResponse:
        if kwargs.get("decision") == "recall":
            return MockResponse(
                content=(
                    "Reviewed prior lending interactions at the bank to inform this request."
                ),
                intent="memory_recall",
                confidence=0.8,
                strategy="episodic_memory",
                metadata={"provider": "mock"},
            )

        loan_product = kwargs.get("loan_product", "unknown")
        decision = kwargs.get("decision", "manual_review")
        narration = _NARRATION.get(loan_product, {}).get(
            decision,
            "Request received. Additional review is required.",
        )
        return MockResponse(
            content=narration,
            intent=f"{loan_product}_{decision}",
            confidence=0.85,
            strategy="product_specific_underwriting",
            reasoning_steps=[
                f"Loan product: {loan_product}",
                f"Decision: {decision}",
            ],
            metadata={"loan_product": loan_product, "decision": decision, "provider": "mock"},
        )
