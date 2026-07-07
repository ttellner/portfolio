"""Three-agent lending architecture inspired by Chapter 5 cognitive patterns."""

from __future__ import annotations

from datetime import datetime

from mock_databases import MockVectorDB
from llm_client import LendingLLM, get_llm_client
from mock_llm import MockLLM, MockResponse
from mock_tools import (
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
        "fico_score": bureau.get("fico_score"),
        "fraud_score": fraud.get("fraud_score"),
        "fraud_flags": fraud.get("flags", []),
        "pd_12mo": pd.get("pd_12mo"),
        "risk_band": pd.get("risk_band"),
        "dti": dti.get("dti"),
        "dti_within_policy": dti.get("within_policy"),
        "identity_verified": identity.get("verified"),
        "sanctions_hit": sanctions.get("hit"),
        "estimated_monthly_payment": payment,
    }


def select_strategy(perception: dict) -> dict:
    if perception["fraud_score"] >= 0.7 or perception["sanctions_hit"]:
        decision = "escalate_fraud"
        strategy = "immediate_escalation"
    elif perception["pd_12mo"] >= 0.20 or perception["fico_score"] < 600:
        decision = "declined"
        strategy = "reject_with_explanation"
    elif (
        perception["pd_12mo"] < 0.08
        and perception["fico_score"] >= 700
        and perception["dti_within_policy"]
        and perception["identity_verified"]
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


class UnderwritingAgent:
    """Autonomous decision-making agent (Chapter 5 style cognitive loop)."""

    def __init__(self, llm: LendingLLM | None = None) -> None:
        self.llm = llm or get_llm_client()
        self.decision_history: list[dict] = []

    def cognitive_loop(self, application_id: str) -> dict:
        perception = build_perception(application_id)
        reasoning = select_strategy(perception)
        plan = build_action_plan(reasoning["decision"])

        prompt = (
            f"Underwrite application {application_id} for {perception['name']}. "
            f"Fraud={perception['fraud_score']}, PD={perception['pd_12mo']}, "
            f"FICO={perception['fico_score']}, decision={reasoning['decision']}"
        )
        llm_response = self.llm.generate(prompt)

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
            "action_plan": plan,
            "llm_summary": llm_response.content,
            "llm_intent": llm_response.intent,
            "cross_sell_offers": offers.get("offers", []),
            "tasks_completed": [step["action"] for step in plan],
        }
        self.decision_history.append(result)
        return result


class PlanningAgent:
    """Planning agent that materializes origination DAG steps."""

    def __init__(self, llm: LendingLLM | None = None) -> None:
        self.llm = llm or get_llm_client()

    def decompose_origination(self, application_id: str) -> list[dict]:
        app = get_application(application_id)
        goal = (
            f"Originate {app['purpose']} loan for {app['name']} amount "
            f"{app['requested_amount']}"
        )
        self.llm.generate(goal)
        return [
            {"phase": 1, "id": "G-T1", "action": "verify_identity", "depends_on": []},
            {"phase": 2, "id": "G-T2", "action": "pull_credit_bureau", "depends_on": ["G-T1"]},
            {"phase": 3, "id": "G-T3", "action": "score_default_risk", "depends_on": ["G-T2"]},
            {"phase": 4, "id": "G-T4", "action": "calculate_dti", "depends_on": ["G-T2"]},
            {"phase": 5, "id": "G-T5", "action": "credit_decision", "depends_on": ["G-T3", "G-T4"]},
            {"phase": 6, "id": "G-T6", "action": "cross_sell_recommendation", "depends_on": ["G-T5"]},
        ]


class RelationshipAgent:
    """Memory-augmented agent for episodic applicant context."""

    def __init__(
        self,
        vector_db: MockVectorDB | None = None,
        llm: LendingLLM | None = None,
    ) -> None:
        self.vector_db = vector_db or MockVectorDB()
        self.llm = llm or get_llm_client()

    def handle_interaction(self, applicant_id: str, query: str) -> dict:
        memories = self.vector_db.search(applicant_id, query, top_k=3)
        llm_response = self.llm.generate(
            f"Applicant {applicant_id} asks: {query}. Memories: {memories}"
        )
        self.vector_db.add(applicant_id, query, llm_response.content[:120])
        return {
            "memories": memories,
            "response": llm_response.content,
            "intent": llm_response.intent,
        }


def run_integrated_demo(
    application_id: str,
    llm: LendingLLM | None = None,
    force_mock: bool = False,
    model: str | None = None,
) -> dict:
    llm = llm or get_llm_client(force_mock=force_mock, model=model)
    underwriter = UnderwritingAgent(llm)
    planner = PlanningAgent(llm)
    relationship = RelationshipAgent(llm=llm)

    underwriting = underwriter.cognitive_loop(application_id)
    origination_plan = planner.decompose_origination(application_id)
    app = get_application(application_id)
    memory = relationship.handle_interaction(
        app["applicant_id"],
        f"What is the lending history and next best offer for {app['name']}?",
    )

    return {
        "underwriting": underwriting,
        "origination_plan": origination_plan,
        "relationship_memory": memory,
    }
