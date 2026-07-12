"""Single-agent lending architecture: interpret request, gather bank data, decide, narrate."""

from __future__ import annotations

from datetime import datetime

from .mock_databases import CUSTOMER_ID, MockVectorDB
from .llm_client import LendingLLM, get_llm_client
from .mock_tools import (
    evaluate_auto_loan,
    evaluate_debt_consolidation,
    evaluate_home_improvement,
    get_balances,
    get_customer,
    get_direct_deposits,
    get_mortgage,
    pull_credit_bureau,
)


def build_action_plan(decision: str, loan_product: str) -> list[dict]:
    if decision == "declined":
        return [
            {"id": "T1", "action": "generate_adverse_action_notice", "depends_on": []},
            {"id": "T2", "action": "log_decline_reason_codes", "depends_on": ["T1"]},
        ]
    if decision == "approved":
        return [
            {"id": "T1", "action": "finalize_credit_decision", "depends_on": []},
            {"id": "T2", "action": f"generate_{loan_product}_terms", "depends_on": ["T1"]},
            {"id": "T3", "action": "disburse_or_open_line", "depends_on": ["T2"]},
        ]
    return [
        {"id": "T1", "action": "queue_analyst_review", "depends_on": []},
        {"id": "T2", "action": "request_supporting_documents", "depends_on": ["T1"]},
    ]


def _run_product_analysis(loan_product: str) -> dict:
    if loan_product == "debt_consolidation":
        return evaluate_debt_consolidation()
    if loan_product == "auto_loan":
        return evaluate_auto_loan()
    if loan_product == "home_improvement":
        return evaluate_home_improvement()
    return {"decision": "declined", "loan_product": loan_product, "risk_factor": 1.0}


def recall_and_respond(
    vector_db: MockVectorDB,
    llm: LendingLLM,
    user_prompt: str,
    loan_product: str,
) -> dict:
    customer = get_customer()
    memories = vector_db.search(CUSTOMER_ID, user_prompt, top_k=3)
    llm_response = llm.generate(
        user_prompt,
        loan_product=loan_product,
        decision="recall",
    )
    vector_db.add(CUSTOMER_ID, user_prompt, llm_response.content[:120])
    return {
        "memories": memories,
        "response": llm_response.content,
        "customer_name": customer["name"],
    }


class UnderwritingAgent:
    """Single agent: interpret prompt → gather bank data → decide → narrate."""

    def __init__(
        self,
        llm: LendingLLM | None = None,
        vector_db: MockVectorDB | None = None,
    ) -> None:
        self.llm = llm or get_llm_client()
        self.vector_db = vector_db or MockVectorDB()
        self.decision_history: list[dict] = []

    def cognitive_loop(self, user_prompt: str) -> dict:
        customer = get_customer()
        interpretation = self.llm.interpret_request(user_prompt)
        loan_product = interpretation.get("loan_product", "unknown")

        if loan_product == "unknown":
            return {
                "customer": customer,
                "user_prompt": user_prompt,
                "interpretation": interpretation,
                "decision": "unsupported_request",
                "llm_summary": (
                    "I could not determine whether you want debt consolidation, an auto loan, "
                    "or a home improvement line. Try: 'I want a debt consolidation loan.'"
                ),
                "reasoning": {
                    "decision": "unsupported_request",
                    "strategy": "clarify_loan_product",
                },
            }

        analysis = _run_product_analysis(loan_product)
        decision = analysis["decision"]
        action_plan = build_action_plan(decision, loan_product)

        perception = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "customer": customer,
            "user_prompt": user_prompt,
            "interpretation": interpretation,
            "loan_product": loan_product,
            "balances": get_balances(),
            "direct_deposits": get_direct_deposits(),
            "mortgage": get_mortgage(),
            "credit_bureau": pull_credit_bureau(),
            "analysis": analysis,
        }

        reasoning = {
            "decision": decision,
            "strategy": f"{loan_product}_{decision}",
            "risk_factor": analysis.get("risk_factor"),
        }

        llm_response = self.llm.generate(
            user_prompt,
            loan_product=loan_product,
            decision=decision,
        )

        relationship_memory = recall_and_respond(
            self.vector_db, self.llm, user_prompt, loan_product
        )

        result = {
            "perception": perception,
            "reasoning": reasoning,
            "action_plan": action_plan,
            "relationship_memory": relationship_memory,
            "llm_summary": llm_response.content,
            "llm_intent": llm_response.intent,
            "analysis": analysis,
        }
        self.decision_history.append(result)
        return result
