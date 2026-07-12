"""
Lending Underwriting Agent Demo
Single-customer, prompt-driven debt consolidation, auto, and home improvement workflow.
https://via.placeholder.com/400x200?text=AI+Lending+Agent
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

CURRENT_DIR = Path(__file__).parent.absolute()

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from lending.agents import UnderwritingAgent
from lending.display import render_stat_cards, render_table
from lending.llm_client import (
    DEFAULT_OLLAMA_MODEL,
    get_llm_client,
    get_llm_status,
    verify_ollama_invite_password,
)
from lending.mock_databases import CUSTOMER

EXAMPLE_PROMPTS = [
    "I want a debt consolidation loan.",
    "I need a car loan — what payment can I afford?",
    "I'd like a home improvement line for a kitchen remodel.",
]


def _invite_unlocked() -> bool:
    return bool(st.session_state.get("ollama_invite_unlocked", False))


def _handle_invite_password(password: str) -> None:
    if not password:
        st.session_state.ollama_invite_unlocked = False
        return
    if verify_ollama_invite_password(password):
        st.session_state.ollama_invite_unlocked = True
    else:
        st.session_state.ollama_invite_unlocked = False


def _balance_summary(balances: dict) -> dict:
    return {
        "checking": balances.get("checking", 0),
        "savings": balances.get("savings", 0),
        "total_unsecured_debt": balances.get("total_unsecured_debt", 0),
        "credit_card_count": len(balances.get("credit_cards") or []),
        "personal_loan_balance": (balances.get("personal_loan") or {}).get("balance", 0),
    }


def _analysis_summary(analysis: dict) -> dict:
    """Flatten product analysis for safe table rendering."""
    return {key: value for key, value in analysis.items() if not isinstance(value, (list, dict))}


def _render_results(result: dict) -> None:
    if result.get("reasoning", {}).get("decision") == "unsupported_request":
        st.error(result.get("llm_summary", "Unsupported request."))
        with st.expander("Raw JSON output"):
            st.code(json.dumps(result, indent=2, default=str), language="json")
        return

    perception = result.get("perception") or {}
    interp = perception.get("interpretation") or {}
    analysis = result.get("analysis") or {}
    reasoning = result.get("reasoning") or {}

    st.subheader("Interpreted request")
    st.markdown(
        f"**Product:** `{interp.get('loan_product', 'unknown')}` "
        f"(confidence {interp.get('confidence', 0):.0%}) — {interp.get('reason', '')}"
    )

    st.subheader("Decision")
    render_stat_cards(
        [
            ("Decision", str(reasoning.get("decision", "n/a"))),
            ("Risk factor", f"{analysis.get('risk_factor', 0):.0%}"),
            ("Loan product", str(analysis.get("loan_product", "n/a"))),
        ]
    )

    st.markdown(f"**LLM summary:** {result.get('llm_summary', '')}")

    st.markdown("**Product analysis**")
    render_table(_analysis_summary(analysis))

    st.markdown("**Bank data used**")
    bank_cols = st.columns(3)
    with bank_cols[0]:
        st.caption("Balances")
        render_table(_balance_summary(perception.get("balances") or {}))
    with bank_cols[1]:
        st.caption("Direct deposits")
        render_table((perception.get("direct_deposits") or {}).get("deposits") or [])
    with bank_cols[2]:
        st.caption("Mortgage / bureau")
        render_table(
            [{**(perception.get("mortgage") or {}), **(perception.get("credit_bureau") or {})}]
        )

    st.markdown("**Action plan**")
    render_table(result.get("action_plan") or [])

    mem = result.get("relationship_memory") or {}
    st.markdown("**Episodic memory**")
    st.markdown(f"_{mem.get('response', '')}_")
    if mem.get("memories"):
        render_table(mem["memories"])

    with st.expander("Raw JSON output"):
        st.code(json.dumps(result, indent=2, default=str), language="json")


def main() -> None:
    st.markdown(
        '<h1 style="text-align:center;color:#1f77b4;">Lending Underwriting Agent Demo - The Decision Maker</h1>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="max-width:900px;margin:0 auto;text-align:justify;">
        Single customer demo for <b>{CUSTOMER["name"]}</b>. Enter a natural-language loan request;
        the agent interprets it (debt consolidation, auto loan, or home improvement), pulls
        relevant bank data, applies product risk factors, and decides.
        Simulation mode is default; invite-only Ollama unlocks live interpretation.
        </div>
        """,
        unsafe_allow_html=True,
    )

    invite_password = st.text_input(
        "Enter password for Ollama (Invite Only)",
        type="password",
        help="Leave blank for simulation mode. Correct password connects to remote Ollama.",
        key="ollama_invite_password_input",
    )

    _handle_invite_password(invite_password)
    if invite_password and not _invite_unlocked():
        st.warning("Incorrect invite password. Using simulation mode.")

    status = get_llm_status(invite_unlocked=_invite_unlocked())
    st.success(status["detail"])
    if status.get("hint"):
        st.caption(status["hint"])

    col1, col2 = st.columns([1, 2])

    with col1:
        live_ollama = _invite_unlocked() and status["mode"] == "LIVE"
        model_options = status["available_models"] or [DEFAULT_OLLAMA_MODEL]
        selected_model = st.selectbox(
            "Ollama model",
            options=model_options,
            index=0,
            disabled=not live_ollama,
        )

        user_prompt = st.text_area(
            "Your loan request",
            value=EXAMPLE_PROMPTS[0],
            height=100,
            help="Examples: debt consolidation, auto loan, home improvement / HELOC",
        )
        st.caption("Try: " + " | ".join(f'"{p}"' for p in EXAMPLE_PROMPTS))

        run_btn = st.button("Run agent workflow", type="primary", use_container_width=True)

    with col2:
        st.subheader("How it works")
        st.markdown(
            """
            1. **Interpret** — LLM classifies your request into a loan product
            2. **Gather** — pulls Maria's balances, deposits, mortgage, or bureau data
            3. **Decide** — compares bank data to product risk factors
            4. **Narrate** — LLM explains the outcome

            **Debt consolidation** — unsecured balances vs savings and DTI  
            **Auto loan** — max payment from verified direct deposits  
            **Home improvement** — equity line from property value and mortgage
            """
        )

    if run_btn:
        if not user_prompt.strip():
            st.warning("Please enter a loan request.")
            return

        invite_unlocked = _invite_unlocked()
        with st.spinner("Running agent workflow..."):
            try:
                llm = get_llm_client(
                    invite_unlocked=invite_unlocked,
                    model=selected_model if live_ollama else None,
                )
                st.session_state["underwriting_result"] = (
                    UnderwritingAgent(llm).cognitive_loop(user_prompt.strip())
                )
                st.session_state["underwriting_error"] = None
            except Exception as exc:
                st.session_state["underwriting_result"] = None
                st.session_state["underwriting_error"] = str(exc)

    if st.session_state.get("underwriting_error"):
        st.error(f"Workflow failed: {st.session_state['underwriting_error']}")
        return

    result = st.session_state.get("underwriting_result")
    if not result:
        st.info("Enter a loan request and click **Run agent workflow**.")
        return

    _render_results(result)


if __name__ == "__main__":
    main()
