"""In-memory mock databases for the lending agent portfolio demo."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ApplicantRecord:
    applicant_id: str
    name: str
    stated_income: int
    requested_amount: int
    purpose: str
    employment_years: float
    device_id: str = "dev_mobile_default"


APPLICATIONS: dict[str, dict] = {
    "app_1001": {
        "application_id": "app_1001",
        "applicant_id": "cust_7788",
        "name": "Maria Chen",
        "stated_income": 72000,
        "requested_amount": 25000,
        "purpose": "debt_consolidation",
        "employment_years": 4.0,
        "device_id": "dev_mobile_abc",
    },
    "app_1002": {
        "application_id": "app_1002",
        "applicant_id": "cust_9901",
        "name": "John Smith",
        "stated_income": 95000,
        "requested_amount": 15000,
        "purpose": "auto",
        "employment_years": 0.5,
        "device_id": "dev_tor_exit_node",
    },
    "app_1003": {
        "application_id": "app_1003",
        "applicant_id": "cust_3344",
        "name": "Amina Okonkwo",
        "stated_income": 110000,
        "requested_amount": 50000,
        "purpose": "home_improvement",
        "employment_years": 8.0,
        "device_id": "dev_secure_laptop",
    },
}

CREDIT_PROFILES: dict[str, dict] = {
    "cust_7788": {
        "fico_score": 712,
        "utilization_pct": 34,
        "delinquencies_24mo": 0,
        "bankruptcies": 0,
        "monthly_debt_payment": 980,
    },
    "cust_9901": {
        "fico_score": 598,
        "utilization_pct": 89,
        "delinquencies_24mo": 2,
        "bankruptcies": 0,
        "monthly_debt_payment": 1450,
    },
    "cust_3344": {
        "fico_score": 780,
        "utilization_pct": 12,
        "delinquencies_24mo": 0,
        "bankruptcies": 0,
        "monthly_debt_payment": 620,
    },
}

PAYMENT_HISTORY: dict[str, list[dict]] = {
    "cust_7788": [
        {"month": "2025-10", "on_time": True},
        {"month": "2025-11", "on_time": True},
        {"month": "2025-12", "on_time": True},
        {"month": "2026-01", "on_time": True},
        {"month": "2026-02", "on_time": False, "days_late": 15},
        {"month": "2026-03", "on_time": True},
    ],
    "cust_9901": [
        {"month": "2025-10", "on_time": False, "days_late": 30},
        {"month": "2025-11", "on_time": False, "days_late": 60},
        {"month": "2025-12", "on_time": True},
        {"month": "2026-01", "on_time": False, "days_late": 45},
    ],
    "cust_3344": [
        {"month": "2025-10", "on_time": True},
        {"month": "2025-11", "on_time": True},
        {"month": "2025-12", "on_time": True},
        {"month": "2026-01", "on_time": True},
        {"month": "2026-02", "on_time": True},
        {"month": "2026-03", "on_time": True},
    ],
}

DEVICE_RISK: dict[str, dict] = {
    "dev_tor_exit_node": {"risk_score": 0.92, "flags": ["vpn_tor", "geo_mismatch"]},
    "dev_mobile_abc": {"risk_score": 0.08, "flags": []},
    "dev_secure_laptop": {"risk_score": 0.05, "flags": []},
}

APPLICANT_FRAUD: dict[str, dict] = {
    "cust_9901": {
        "velocity_24h": 4,
        "identity_mismatch": True,
        "ssn_prefill_mismatch": True,
    },
}

VECTOR_SEED_RECORDS: list[dict] = [
    {
        "user_id": "cust_7788",
        "query": "Prior personal loan 12k approved 2024",
        "response_summary": "Paid off early, no delinquencies",
    },
    {
        "user_id": "cust_9901",
        "query": "Charge-off on retail card 2025",
        "response_summary": "Account closed, sent to collections",
    },
    {
        "user_id": "cust_3344",
        "query": "HELOC inquiry only, no draw",
        "response_summary": "Eligible for premium products",
    },
]


class MockVectorDB:
    def __init__(self) -> None:
        self._records = list(VECTOR_SEED_RECORDS)

    def add(self, user_id: str, query: str, response_summary: str) -> None:
        self._records.append(
            {"user_id": user_id, "query": query, "response_summary": response_summary}
        )

    def search(self, user_id: str, query: str, top_k: int = 3) -> list[dict]:
        user_records = [r for r in self._records if r["user_id"] == user_id]
        if not user_records:
            return []

        def score(record: dict) -> float:
            q = set(query.lower().split())
            t = set(record["query"].lower().split())
            if not q or not t:
                return 0.0
            return len(q & t) / len(q | t)

        ranked = sorted(user_records, key=score, reverse=True)
        return ranked[:top_k]
