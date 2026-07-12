"""Single-customer mock bank database for the lending agent demo."""

from __future__ import annotations

CUSTOMER_ID = "cust_maria_chen"

CUSTOMER: dict = {
    "customer_id": CUSTOMER_ID,
    "name": "Maria Chen",
    "fico_score": 712,
    "employment_years": 4.0,
    "employer": "Northbridge Analytics",
    "device_id": "dev_mobile_abc",
}

# Checking, savings, and liability balances held at the bank.
BALANCES: dict = {
    "checking": 4200,
    "savings": 12500,
    "credit_cards": [
        {"issuer": "Bank Visa", "balance": 5400, "limit": 12000, "apr": 0.2199},
        {"issuer": "Retail Mastercard", "balance": 3000, "limit": 8000, "apr": 0.2499},
    ],
    "personal_loan": {"balance": 6200, "monthly_payment": 185, "months_remaining": 28},
    "total_unsecured_debt": 14600,
}

# Verified income from payroll direct deposits (last 3 months).
DIRECT_DEPOSITS: list[dict] = [
    {"month": "2026-04", "employer": "Northbridge Analytics", "net_amount": 5820},
    {"month": "2026-05", "employer": "Northbridge Analytics", "net_amount": 5795},
    {"month": "2026-06", "employer": "Northbridge Analytics", "net_amount": 5810},
]

MORTGAGE: dict = {
    "lender": "Portfolio Bank",
    "balance": 285000,
    "original_amount": 310000,
    "monthly_payment": 1890,
    "interest_rate": 0.0575,
    "property_value": 420000,
    "equity": 135000,
    "ltv": round(285000 / 420000, 3),
}

CREDIT_PROFILE: dict = {
    "fico_score": 712,
    "utilization_pct": 34,
    "delinquencies_24mo": 0,
    "bankruptcies": 0,
    "monthly_debt_payment": 980,
}

# Product-level base risk factors (12-month PD proxies).
PRODUCT_RISK_FACTORS: dict = {
    "debt_consolidation": 0.12,
    "auto_loan": 0.09,
    "home_improvement": 0.07,
}

VECTOR_SEED_RECORDS: list[dict] = [
    {
        "user_id": CUSTOMER_ID,
        "query": "Prior personal loan 12k approved 2024",
        "response_summary": "Paid off early, no delinquencies",
    },
    {
        "user_id": CUSTOMER_ID,
        "query": "Asked about auto loan pre-qualification 2025",
        "response_summary": "Quoted max payment $640 based on deposits",
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
