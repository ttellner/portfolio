"""
Lending Underwriting Agent Demo
Single-agent fraud, creditworthiness, default-risk, and cross-sell workflow.
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

APPLICATION_LABELS = {
    "app_1001": "Maria Chen — debt consolidation ($25k)",
    "app_1002": "John Smith — auto loan ($15k) [fraud signals]",
    "app_1003": "Amina Okonkwo — home improvement ($50k) [strong credit]",
}

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
        '<h1 style="text-align:center;color:#1f77b4;">Lending Underwriting Agent Demo - Level 1</h1>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="max-width:900px;margin:0 auto;text-align:justify;">
        Single-agent portfolio demo with a simple cognitive loop:
        <b>perceive</b> → <b>reason</b> → <b>plan</b> → <b>remember</b> → <b>narrate</b>.
        The public demo runs in <b>simulation mode</b>. Invite-only access unlocks
        live Ollama via a configured remote <code>OLLAMA_HOST</code>.
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
    if status["mode"] == "LIVE":
        st.success(status["detail"])
    else:
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

        app_id = st.selectbox(
            "Select application",
            options=list(APPLICATION_LABELS.keys()),
            format_func=lambda x: APPLICATION_LABELS[x],
        )

        run_btn = st.button("Run agent workflow", type="primary", use_container_width=True)

    with col2:
        st.subheader("Architecture")
        st.markdown(
            """
            One **UnderwritingAgent** runs the full loop:

            1. **Perceive** — bureau, fraud, default risk, DTI, identity, sanctions
            2. **Reason** — rules-based approve / decline / review / fraud escalation
            3. **Plan** — decision action plan and origination DAG
            4. **Remember** — episodic memory search and recall
            5. **Narrate** — LLM summary of the underwriting outcome

            This is a hybrid demo: deterministic bank-style control logic with an LLM
            commentary layer on top, not open-ended agent autonomy.
            """
        )

    if not run_btn:
        st.info("Choose an application and click **Run agent workflow**.")
        return

    invite_unlocked = _invite_unlocked()
    with st.spinner("Running agent workflow..."):
        llm = get_llm_client(invite_unlocked=invite_unlocked, model=selected_model)
        result = UnderwritingAgent(llm).cognitive_loop(app_id)
        output = {
            "underwriting": result,
            "llm_backend": {
                "provider": getattr(llm, "provider", "mock"),
                "model": getattr(llm, "model", "mock"),
                "mode": "SIMULATION" if getattr(llm, "provider", "") == "mock" else "LIVE",
                "invite_unlocked": invite_unlocked,
            },
        }

    uw = output["underwriting"]
    st.subheader("Underwriting agent — cognitive loop")
    m1, m2, m3, m4 = st.columns(4)
    p = uw["perception"]
    r = uw["reasoning"]
    m1.metric("FICO", p["fico_score"])
    m2.metric("Fraud score", p["fraud_score"])
    m3.metric("PD (12mo)", f"{p['pd_12mo']:.1%}" if p.get("pd_12mo") is not None else "n/a")
    m4.metric("Decision", r["decision"])

    st.markdown(f"**Strategy:** `{r['strategy']}`")
    st.markdown(f"**LLM summary:** {uw['llm_summary']}")

    backend = output["llm_backend"]
    st.caption(
        f"Generated via {backend['provider']} "
        f"({backend['mode']}, model: {backend.get('model', 'n/a')})"
    )

    st.markdown("**Perception snapshot**")
    st.dataframe(pd.DataFrame([p]), width="stretch")
    st.markdown("**Action plan (DAG)**")
    st.dataframe(pd.DataFrame(uw["action_plan"]), width="stretch")

    if uw["cross_sell_offers"]:
        st.markdown("**Cross-sell offers**")
        st.dataframe(pd.DataFrame(uw["cross_sell_offers"]), width="stretch")

    st.subheader("Origination plan")
    st.dataframe(pd.DataFrame(uw["origination_plan"]), width="stretch")

    st.subheader("Episodic memory")
    mem = uw["relationship_memory"]
    st.markdown(f"**Response:** {mem['response']}")
    if mem["memories"]:
        st.dataframe(pd.DataFrame(mem["memories"]), width="stretch")
    else:
        st.write("No prior episodic memories found for this applicant.")

    with st.expander("Raw JSON output"):
        st.code(json.dumps(output, indent=2, default=str), language="json")

if __name__ == "__main__":
    main()
