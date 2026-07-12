"""Mock bank tools for the single-customer lending agent demo."""

from __future__ import annotations

from .fallout import coalesce, fallout_shelter
from .mock_databases import (
    BALANCES,
    CREDIT_PROFILE,
    CUSTOMER,
    CUSTOMER_ID,
    DIRECT_DEPOSITS,
    MORTGAGE,
    PRODUCT_RISK_FACTORS,
)


def get_customer() -> dict:
    return dict(CUSTOMER)


@fallout_shelter(fallback_value={"checking": 0, "savings": 0, "total_unsecured_debt": 0})
def get_balances() -> dict:
    cards = [dict(c) for c in BALANCES["credit_cards"]]
    return {
        "checking": BALANCES["checking"],
        "savings": BALANCES["savings"],
        "credit_cards": cards,
        "personal_loan": dict(BALANCES["personal_loan"]),
        "total_unsecured_debt": BALANCES["total_unsecured_debt"],
    }


@fallout_shelter(fallback_value={"monthly_income": 5000, "deposits": []})
def get_direct_deposits() -> dict:
    amounts = [d["net_amount"] for d in DIRECT_DEPOSITS]
    monthly_income = round(sum(amounts) / len(amounts)) if amounts else 5000
    return {"monthly_income": monthly_income, "deposits": list(DIRECT_DEPOSITS)}


@fallout_shelter(fallback_value={"balance": 0, "property_value": 0, "equity": 0})
def get_mortgage() -> dict:
    return dict(MORTGAGE)


@fallout_shelter(fallback_value={"fico_score": 650, "monthly_debt_payment": 0})
def pull_credit_bureau() -> dict:
    return dict(CREDIT_PROFILE)


def get_product_risk_factor(loan_product: str) -> float:
    return PRODUCT_RISK_FACTORS.get(loan_product, 0.15)


def estimate_monthly_payment(
    amount: float, annual_rate: float = 0.1199, months: int = 48
) -> float:
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return round(amount / months, 2)
    payment = amount * (monthly_rate * (1 + monthly_rate) ** months) / (
        (1 + monthly_rate) ** months - 1
    )
    return round(payment, 2)


@fallout_shelter(fallback_value={"decision": "manual_review"})
def evaluate_debt_consolidation() -> dict:
    """Compare unsecured balances to savings and consolidation risk factor."""
    balances = get_balances()
    bureau = pull_credit_bureau()
    deposits = get_direct_deposits()
    risk_factor = get_product_risk_factor("debt_consolidation")

    total_debt = balances["total_unsecured_debt"]
    savings = balances["savings"]
    monthly_income = deposits["monthly_income"]
    proposed_amount = min(total_debt, 25000)
    proposed_payment = estimate_monthly_payment(proposed_amount)
    existing_debt_pay = coalesce(bureau, "monthly_debt_payment", 0)
    post_consolidation_payment = proposed_payment + 200
    dti = (existing_debt_pay + post_consolidation_payment) / max(monthly_income, 1)
    savings_cushion = savings / max(total_debt, 1)

    if risk_factor >= 0.18 or savings_cushion < 0.15:
        decision = "declined"
    elif dti <= 0.40 and savings_cushion >= 0.20 and risk_factor < 0.14:
        decision = "approved"
    else:
        decision = "manual_review"

    return {
        "loan_product": "debt_consolidation",
        "risk_factor": risk_factor,
        "proposed_amount": proposed_amount,
        "proposed_monthly_payment": proposed_payment,
        "post_consolidation_dti": round(dti, 3),
        "savings_cushion_ratio": round(savings_cushion, 2),
        "total_unsecured_debt": total_debt,
        "checking": balances["checking"],
        "savings": savings,
        "decision": decision,
    }


@fallout_shelter(fallback_value={"decision": "manual_review", "max_monthly_payment": 0})
def evaluate_auto_loan() -> dict:
    """Max car payment from verified direct deposits and auto-loan risk factor."""
    deposits = get_direct_deposits()
    bureau = pull_credit_bureau()
    risk_factor = get_product_risk_factor("auto_loan")

    monthly_income = deposits["monthly_income"]
    existing_debt = coalesce(bureau, "monthly_debt_payment", 0)
    max_by_income = round(monthly_income * 0.15)
    max_by_dti = round(monthly_income * 0.43 - existing_debt)
    max_monthly_payment = max(0, min(max_by_income, max_by_dti))
    max_loan_amount = round(max_monthly_payment * 48 * 0.92) if max_monthly_payment else 0

    if risk_factor >= 0.15 or max_monthly_payment < 250:
        decision = "declined"
    elif max_monthly_payment >= 500 and risk_factor < 0.11:
        decision = "approved"
    else:
        decision = "manual_review"

    return {
        "loan_product": "auto_loan",
        "risk_factor": risk_factor,
        "verified_monthly_income": monthly_income,
        "max_monthly_payment": max_monthly_payment,
        "max_loan_amount": max_loan_amount,
        "direct_deposits": deposits["deposits"],
        "decision": decision,
    }


@fallout_shelter(fallback_value={"decision": "manual_review", "equity_line_amount": 0})
def evaluate_home_improvement() -> dict:
    """HELOC-style line from property value, mortgage balance, and equity."""
    mortgage = get_mortgage()
    bureau = pull_credit_bureau()
    deposits = get_direct_deposits()
    risk_factor = get_product_risk_factor("home_improvement")

    property_value = mortgage["property_value"]
    mortgage_balance = mortgage["balance"]
    equity = mortgage["equity"]
    max_ltv_line = round(property_value * 0.85 - mortgage_balance)
    equity_line_amount = max(0, min(max_ltv_line, 50000, round(equity * 0.60)))

    monthly_income = deposits["monthly_income"]
    fico = coalesce(bureau, "fico_score", 650)

    if risk_factor >= 0.12 or equity_line_amount < 10000 or fico < 680:
        decision = "declined"
    elif equity_line_amount >= 25000 and fico >= 700:
        decision = "approved"
    else:
        decision = "manual_review"

    return {
        "loan_product": "home_improvement",
        "risk_factor": risk_factor,
        "property_value": property_value,
        "mortgage_balance": mortgage_balance,
        "equity": equity,
        "ltv": mortgage["ltv"],
        "equity_line_amount": equity_line_amount,
        "verified_monthly_income": monthly_income,
        "fico_score": fico,
        "decision": decision,
    }
