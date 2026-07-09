"""Mock external lending tools (KYC, bureau, fraud, scoring, cross-sell).

Tool failures are handled via the fallout module's with_fallout decorator.
"""

from __future__ import annotations

from .fallout import with_fallout
from .mock_databases import (
    APPLICATIONS,
    APPLICANT_FRAUD,
    CREDIT_PROFILES,
    DEVICE_RISK,
    PAYMENT_HISTORY,
)


@with_fallout(fallback_value={"verified": False, "confidence": 0.0})
def verify_identity(applicant_id: str) -> dict:
    fraud = APPLICANT_FRAUD.get(applicant_id, {})
    if fraud.get("identity_mismatch"):
        return {"verified": False, "confidence": 0.31, "reason": "identity_mismatch"}
    return {"verified": True, "confidence": 0.97, "reason": "document_match"}


@with_fallout(fallback_value={"fico_score": 650, "utilization_pct": 50})
def pull_credit_bureau(applicant_id: str) -> dict:
    return dict(CREDIT_PROFILES.get(applicant_id, {"fico_score": 650, "utilization_pct": 50}))


@with_fallout(fallback_value={"fraud_score": 0.5, "flags": ["lookup_failed"]})
def check_fraud_signals(application_id: str, device_id: str, applicant_id: str) -> dict:
    device = DEVICE_RISK.get(device_id, {"risk_score": 0.2, "flags": []})
    applicant = APPLICANT_FRAUD.get(applicant_id, {})
    flags = list(device.get("flags", []))
    score = device.get("risk_score", 0.2)

    if applicant.get("velocity_24h", 0) >= 3:
        flags.append("velocity_4_apps_24h")
        score = max(score, 0.75)
    if applicant.get("identity_mismatch"):
        flags.append("identity_mismatch")
        score = max(score, 0.8)

    return {"fraud_score": round(score, 2), "flags": sorted(set(flags))}


@with_fallout(fallback_value={"pd_12mo": 0.5, "risk_band": "unknown"})
def score_default_risk(applicant_id: str, loan_amount: float) -> dict:
    bureau = pull_credit_bureau(applicant_id)
    payments = PAYMENT_HISTORY.get(applicant_id, [])
    late_count = sum(1 for p in payments if not p.get("on_time", True))
    utilization = bureau.get("utilization_pct", 50) / 100
    fico_factor = max(0, (700 - bureau.get("fico_score", 650)) / 200)
    amount_factor = min(0.15, loan_amount / 200000)

    pd = min(0.95, 0.05 + late_count * 0.08 + utilization * 0.2 + fico_factor * 0.3 + amount_factor)
    band = "low" if pd < 0.08 else "medium" if pd < 0.20 else "high"
    return {"pd_12mo": round(pd, 3), "risk_band": band}


@with_fallout(fallback_value={"dti": 0.5, "within_policy": False})
def calculate_dti(applicant_id: str, stated_income: int, new_monthly_payment: float) -> dict:
    bureau = pull_credit_bureau(applicant_id)
    monthly_income = max(stated_income / 12, 1)
    existing = bureau.get("monthly_debt_payment", 0)
    dti = (existing + new_monthly_payment) / monthly_income
    return {"dti": round(dti, 3), "within_policy": dti <= 0.43}


@with_fallout(fallback_value={"hit": False})
def check_sanctions(name: str) -> dict:
  return {"hit": False, "list": "OFAC_mock"}


@with_fallout(fallback_value={"offers": []})
def recommend_products(applicant_id: str, decision: str, bureau: dict, pd: dict) -> dict:
    if decision != "approved":
        offers = []
        if pd.get("risk_band") in {"medium", "high"}:
            offers.append(
                {
                    "product": "credit_builder_loan",
                    "reason": "Improve payment history before re-application",
                }
            )
        if bureau.get("fico_score", 0) < 620:
            offers.append(
                {
                    "product": "secured_card",
                    "reason": "Thin or impaired credit file",
                }
            )
        return {"offers": offers}

    offers = [{"product": "personal_loan", "reason": "Primary requested product"}]
    if bureau.get("fico_score", 0) >= 760:
        offers.append({"product": "premium_rewards_card", "reason": "Strong credit profile"})
        offers.append({"product": "heloc_draw", "reason": "Prior HELOC inquiry with no draw"})
    if pd.get("pd_12mo", 1) < 0.06:
        offers.append({"product": "auto_refi_rate_lock", "reason": "Low default risk"})
    return {"offers": offers}


def estimate_monthly_payment(amount: float, annual_rate: float = 0.1199, months: int = 48) -> float:
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return amount / months
    payment = amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
    return round(payment, 2)


def get_application(application_id: str) -> dict:
    return dict(APPLICATIONS[application_id])
