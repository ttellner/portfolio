"""Single-agent lending architecture with perceive, reason, plan, remember, and narrate."""

from __future__ import annotations

from datetime import datetime

from .mock_databases import MockVectorDB
from .llm_client import LendingLLM, get_llm_client
from .fallout import coalesce
from .mock_tools import (
    calculate_dti,
    check_fraud_signals,
    check_sanctions,
    estimate_monthly_payment,
    get_application,
    pull_credit_bureau,
    recommend_products,
    score_default_risk,
    verify_identity,
)


def build_perception(application_id: str) -> dict:
    app = get_application(application_id)
    applicant_id = app["applicant_id"]
    bureau = pull_credit_bureau(applicant_id)
    fraud = check_fraud_signals(application_id, app["device_id"], applicant_id)
    pd = score_default_risk(applicant_id, app["requested_amount"])
    payment = estimate_monthly_payment(app["requested_amount"])
    dti = calculate_dti(applicant_id, app["stated_income"], payment)
    identity = verify_identity(applicant_id)
    sanctions = check_sanctions(app["name"])

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "application_id": application_id,
        "applicant_id": applicant_id,
        "name": app["name"],
        "purpose": app["purpose"],
        "requested_amount": app["requested_amount"],
        "stated_income": app["stated_income"],
        "fico_score": coalesce(bureau, "fico_score", 650),
        "fraud_score": coalesce(fraud, "fraud_score", 0.0),
        "fraud_flags": fraud.get("flags") or [],
        "pd_12mo": coalesce(pd, "pd_12mo", 0.5),
        "risk_band": coalesce(pd, "risk_band", "unknown"),
        "dti": coalesce(dti, "dti", 0.5),
        "dti_within_policy": bool(coalesce(dti, "within_policy", False)),
        "identity_verified": bool(coalesce(identity, "verified", False)),
        "sanctions_hit": bool(coalesce(sanctions, "hit", False)),
        "estimated_monthly_payment": payment,
    }


def select_strategy(perception: dict) -> dict:
    fraud_score = coalesce(perception, "fraud_score", 1.0)
    pd_12mo = coalesce(perception, "pd_12mo", 1.0)
    fico_score = coalesce(perception, "fico_score", 0)
    dti_within_policy = bool(coalesce(perception, "dti_within_policy", False))
    identity_verified = bool(coalesce(perception, "identity_verified", False))
    sanctions_hit = bool(coalesce(perception, "sanctions_hit", False))

    if fraud_score >= 0.7 or sanctions_hit:
        decision = "escalate_fraud"
        strategy = "immediate_escalation"
    elif pd_12mo >= 0.20 or fico_score < 600:
        decision = "declined"
        strategy = "reject_with_explanation"
    elif (
        pd_12mo < 0.08
        and fico_score >= 700
        and dti_within_policy
        and identity_verified
    ):
        decision = "approved"
        strategy = "full_autonomous_resolution"
    else:
        decision = "manual_review"
        strategy = "guided_autonomous_resolution"

    return {
        "decision": decision,
        "strategy": strategy,
        "priority": 5 if decision == "escalate_fraud" else 3,
    }


def build_action_plan(decision: str) -> list[dict]:
    if decision == "escalate_fraud":
        return [
            {"id": "T1", "action": "freeze_application", "depends_on": []},
            {"id": "T2", "action": "notify_fraud_ops", "depends_on": ["T1"]},
            {"id": "T3", "action": "request_document_upload", "depends_on": ["T2"]},
        ]
    if decision == "declined":
        return [
            {"id": "T1", "action": "generate_adverse_action_notice", "depends_on": []},
            {"id": "T2", "action": "log_decline_reason_codes", "depends_on": ["T1"]},
        ]
    if decision == "approved":
        return [
            {"id": "T1", "action": "finalize_credit_decision", "depends_on": []},
            {"id": "T2", "action": "generate_loan_terms", "depends_on": ["T1"]},
            {"id": "T3", "action": "trigger_cross_sell_offers", "depends_on": ["T2"]},
        ]
    return [
        {"id": "T1", "action": "queue_analyst_review", "depends_on": []},
        {"id": "T2", "action": "request_income_verification", "depends_on": ["T1"]},
    ]


def build_origination_plan(application_id: str) -> list[dict]:
    """Origination DAG template (KYC through cross-sell)."""
    return [
        {"phase": 1, "id": "G-T1", "action": "verify_identity", "depends_on": []},
        {"phase": 2, "id": "G-T2", "action": "pull_credit_bureau", "depends_on": ["G-T1"]},
        {"phase": 3, "id": "G-T3", "action": "score_default_risk", "depends_on": ["G-T2"]},
        {"phase": 4, "id": "G-T4", "action": "calculate_dti", "depends_on": ["G-T2"]},
        {"phase": 5, "id": "G-T5", "action": "credit_decision", "depends_on": ["G-T3", "G-T4"]},
        {"phase": 6, "id": "G-T6", "action": "cross_sell_recommendation", "depends_on": ["G-T5"]},
    ]


def recall_and_respond(
    vector_db: MockVectorDB,
    llm: LendingLLM,
    applicant_id: str,
    applicant_name: str,
) -> dict:
    """Search episodic memory and narrate relationship context."""
    query = f"What is the lending history and next best offer for {applicant_name}?"
    memories = vector_db.search(applicant_id, query, top_k=3)
    llm_response = llm.generate(
        f"Applicant {applicant_id} asks: {query}. Memories: {memories}"
    )
    vector_db.add(applicant_id, query, llm_response.content[:120])
    return {
        "memories": memories,
        "response": llm_response.content,
        "intent": llm_response.intent,
    }


class UnderwritingAgent:
    """Single underwriting agent: perceive, reason, plan, remember, narrate."""

    def __init__(
        self,
        llm: LendingLLM | None = None,
        vector_db: MockVectorDB | None = None,
    ) -> None:
        self.llm = llm or get_llm_client()
        self.vector_db = vector_db or MockVectorDB()
        self.decision_history: list[dict] = []

    def cognitive_loop(self, application_id: str) -> dict:
        perception = build_perception(application_id)
        reasoning = select_strategy(perception)
        action_plan = build_action_plan(reasoning["decision"])
        origination_plan = build_origination_plan(application_id)

        prompt = (
            f"Underwrite application {application_id} for {perception['name']}. "
            f"Fraud={perception['fraud_score']}, PD={perception['pd_12mo']}, "
            f"FICO={perception['fico_score']}, decision={reasoning['decision']}"
        )
        llm_response = self.llm.generate(prompt)

        relationship_memory = recall_and_respond(
            self.vector_db,
            self.llm,
            perception["applicant_id"],
            perception["name"],
        )

        bureau = pull_credit_bureau(perception["applicant_id"])
        offers = recommend_products(
            perception["applicant_id"],
            "approved" if reasoning["decision"] == "approved" else reasoning["decision"],
            bureau,
            {"pd_12mo": perception["pd_12mo"], "risk_band": perception["risk_band"]},
        )

        result = {
            "perception": perception,
            "reasoning": reasoning,
            "action_plan": action_plan,
            "origination_plan": origination_plan,
            "relationship_memory": relationship_memory,
            "llm_summary": llm_response.content,
            "llm_intent": llm_response.intent,
            "cross_sell_offers": offers.get("offers", []),
            "tasks_completed": [step["action"] for step in action_plan],
        }
        self.decision_history.append(result)
        return result
