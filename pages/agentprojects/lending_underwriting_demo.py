"""
Lending Underwriting Agent Demo
Single-customer, prompt-driven debt consolidation, auto, and home improvement workflow.
https://via.placeholder.com/400x200?text=AI+Lending+Agent
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

CURRENT_DIR = Path(__file__).parent.absolute()

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from lending.agents import UnderwritingAgent
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

    if not run_btn:
        st.info("Enter a loan request and click **Run agent workflow**.")
        return

    if not user_prompt.strip():
        st.warning("Please enter a loan request.")
        return

    invite_unlocked = _invite_unlocked()
    with st.spinner("Running agent workflow..."):
        llm = get_llm_client(invite_unlocked=invite_unlocked, model=selected_model if live_ollama else None)
        result = UnderwritingAgent(llm).cognitive_loop(user_prompt.strip())

    if result.get("reasoning", {}).get("decision") == "unsupported_request":
        st.error(result["llm_summary"])
        with st.expander("Raw JSON output"):
            st.code(json.dumps(result, indent=2, default=str), language="json")
        return

    interp = result["perception"]["interpretation"]
    analysis = result["analysis"]
    reasoning = result["reasoning"]

    st.subheader("Interpreted request")
    st.markdown(
        f"**Product:** `{interp['loan_product']}` "
        f"(confidence {interp.get('confidence', 0):.0%}) — {interp.get('reason', '')}"
    )

    st.subheader("Decision")
    m1, m2, m3 = st.columns(3)
    m1.metric("Decision", reasoning["decision"])
    m2.metric("Risk factor", f"{analysis.get('risk_factor', 0):.0%}")
    m3.metric("Loan product", analysis.get("loan_product", "n/a"))

    st.markdown(f"**LLM summary:** {result['llm_summary']}")

    st.markdown("**Product analysis**")
    st.dataframe(pd.DataFrame([analysis]), width="stretch")

    st.markdown("**Bank data used**")
    bank_cols = st.columns(3)
    with bank_cols[0]:
        st.markdown("**Balances**")
        st.dataframe(pd.DataFrame([result["perception"]["balances"]]), width="stretch")
    with bank_cols[1]:
        st.markdown("**Direct deposits**")
        st.dataframe(
            pd.DataFrame(result["perception"]["direct_deposits"]["deposits"]),
            width="stretch",
        )
    with bank_cols[2]:
        st.markdown("**Mortgage / bureau**")
        st.dataframe(
            pd.DataFrame([
                {**result["perception"]["mortgage"], **result["perception"]["credit_bureau"]}
            ]),
            width="stretch",
        )

    st.markdown("**Action plan**")
    st.dataframe(pd.DataFrame(result["action_plan"]), width="stretch")

    mem = result["relationship_memory"]
    st.markdown("**Episodic memory**")
    st.markdown(f"_{mem['response']}_")
    if mem["memories"]:
        st.dataframe(pd.DataFrame(mem["memories"]), width="stretch")

    with st.expander("Raw JSON output"):
        st.code(json.dumps(result, indent=2, default=str), language="json")

if __name__ == "__main__":
    main()
