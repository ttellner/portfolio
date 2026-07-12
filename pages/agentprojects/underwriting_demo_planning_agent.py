"""
Underwriting Close Planning Agent
Monitors home improvement close milestones and reschedules when steps slip past day 20.
https://via.placeholder.com/400x200?text=Close+Planning+Agent
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

CURRENT_DIR = Path(__file__).parent.absolute()

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from lending.display import render_stat_cards, render_table
from lending.llm_client import (
    DEFAULT_OLLAMA_MODEL,
    get_llm_client,
    get_llm_status,
    verify_ollama_invite_password,
)
from lending.mock_databases import CUSTOMER
from lending.planning_agent import CUSTOMER_PROMPT, TARGET_CLOSE_DAYS, CloseSchedulePlanner


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


def _render_results(result: dict) -> None:
    if result.get("status") == "declined":
        st.error(result.get("llm_summary", "Request declined."))
        with st.expander("Raw JSON output"):
            st.code(json.dumps(result, indent=2, default=str), language="json")
        return

    sim = result["simulation"]
    planned = result["planned_schedule"]
    uw = result["underwriting"]
    analysis = uw.get("analysis") or {}

    st.subheader("Credit & capacity check")
    render_stat_cards(
        [
            ("Decision", str(uw.get("decision", "n/a"))),
            ("FICO", str(analysis.get("fico_score", "n/a"))),
            ("Equity line", f"${analysis.get('equity_line_amount', 0):,}"),
            ("Risk factor", f"{analysis.get('risk_factor', 0):.0%}"),
        ]
    )

    st.subheader("Close schedule")
    render_stat_cards(
        [
            ("Target close (day)", str(TARGET_CLOSE_DAYS)),
            ("Projected close (day)", str(sim.get("projected_close_day", "n/a"))),
            ("On track", "Yes" if sim.get("on_track") else "No — rescheduled"),
        ]
    )

    st.markdown(f"**Planner summary:** {result.get('llm_summary', '')}")

    st.markdown("**Planned pipeline (baseline)**")
    render_table(
        result.get("pipeline") or [],
        caption=(
            f"Baseline planned close: day {planned.get('projected_close_day')} "
            f"(target day {planned.get('target_close_day')})"
        ),
    )

    st.markdown("**Simulated actual durations**")
    render_table([sim.get("actual_durations") or {}])

    st.markdown("**Monitor log (progress over time)**")
    render_table(result.get("monitor_log") or [])

    revisions = sim.get("revisions") or []
    if revisions:
        st.markdown("**Reschedule events**")
        render_table(revisions)
    else:
        st.success("No rescheduling required — 20-day close target held.")

    st.markdown("**Bank data used**")
    bank_cols = st.columns(3)
    with bank_cols[0]:
        st.caption("Balances")
        render_table(_balance_summary(uw.get("balances") or {}))
    with bank_cols[1]:
        st.caption("Direct deposits")
        render_table((uw.get("direct_deposits") or {}).get("deposits") or [])
    with bank_cols[2]:
        st.caption("Mortgage / bureau")
        render_table([{**(uw.get("mortgage") or {}), **(uw.get("credit_bureau") or {})}])

    with st.expander("Raw JSON output"):
        st.code(json.dumps(result, indent=2, default=str), language="json")


def main() -> None:
    st.markdown(
        '<h1 style="text-align:center;color:#1f77b4;">Underwriting Close Planning Agent</h1>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="max-width:900px;margin:0 auto;text-align:justify;">
        Interactive close simulation for <b>{CUSTOMER["name"]}</b>.
        Request: <i>"{CUSTOMER_PROMPT}"</i>
        The planner sequences income verification → title review → appraisal sign-off → closing,
        monitors actual durations each run, and reschedules if the day-20 target slips.
        </div>
        """,
        unsafe_allow_html=True,
    )

    invite_password = st.text_input(
        "Enter password for Ollama (Invite Only)",
        type="password",
        help="Leave blank for simulation mode.",
        key="planning_ollama_invite_password_input",
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
            key="planning_ollama_model",
        )

        st.text_area(
            "Customer request (fixed)",
            value=CUSTOMER_PROMPT,
            height=68,
            disabled=True,
        )

        run_btn = st.button(
            "Run close planning simulation",
            type="primary",
            use_container_width=True,
        )

    with col2:
        st.subheader("Pipeline rules")
        st.markdown(
            """
            1. **Income verification** — 5 days planned; must finish before title starts
            2. **Title review** — 10 days planned; must finish before appraisal sign-off
            3. **Appraisal** — 15 days planned; signing waits for title even if field work finishes sooner
            4. **Closing** — 5 days planned; starts only after the first three clear

            Each run draws random actual durations from the assumed baseline up to +3 days (~⅓ chance of delay).
            The agent reschedules closing when the day-20 target is no longer feasible.
            """
        )

    if run_btn:
        invite_unlocked = _invite_unlocked()
        with st.spinner("Running close planning simulation..."):
            try:
                llm = get_llm_client(
                    invite_unlocked=invite_unlocked,
                    model=selected_model if live_ollama else None,
                )
                st.session_state["close_plan_result"] = (
                    CloseSchedulePlanner(llm).orchestrate_close_plan()
                )
                st.session_state["close_plan_error"] = None
            except Exception as exc:
                st.session_state["close_plan_result"] = None
                st.session_state["close_plan_error"] = str(exc)

    if st.session_state.get("close_plan_error"):
        st.error(f"Simulation failed: {st.session_state['close_plan_error']}")
        return

    result = st.session_state.get("close_plan_result")
    if not result:
        st.info("Click **Run close planning simulation** to execute a monitored close plan.")
        return

    _render_results(result)


if __name__ == "__main__":
    main()
