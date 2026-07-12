"""Close-schedule planning agent for home improvement origination."""

from __future__ import annotations

import random
from datetime import datetime

from .llm_client import LendingLLM, get_llm_client
from .mock_tools import (
    evaluate_home_improvement,
    get_balances,
    get_customer,
    get_direct_deposits,
    get_mortgage,
    pull_credit_bureau,
)

CUSTOMER_PROMPT = "I am looking for a home improvement loan with a 20-day close"
TARGET_CLOSE_DAYS = 20


def _choose_run_profile(rng: random.Random) -> str:
    """Roughly two-thirds of runs finish on or before day 20; one-third slip."""
    return "at_risk" if rng.random() < 0.33 else "nominal"


def _draw_actual_days(
    planned: int,
    rng: random.Random,
    profile: str,
    force_delay: bool = False,
) -> tuple[int, str]:
    """Draw step duration between planned and planned + 3 days (never under assumed)."""
    if force_delay or (profile == "at_risk" and rng.random() < 0.55):
        return planned + rng.randint(1, 3), "delayed"
    return planned, "on_time"


def gather_underwriting_snapshot() -> dict:
    """Pull Maria Chen bank and credit data; confirm home improvement capacity."""
    try:
        analysis = evaluate_home_improvement()
        return {
            "customer": get_customer(),
            "balances": get_balances(),
            "direct_deposits": get_direct_deposits(),
            "mortgage": get_mortgage(),
            "credit_bureau": pull_credit_bureau(),
            "analysis": analysis,
            "decision": analysis.get("decision", "manual_review"),
        }
    except Exception as exc:
        return {
            "customer": get_customer(),
            "balances": {},
            "direct_deposits": {"monthly_income": 0, "deposits": []},
            "mortgage": {},
            "credit_bureau": {},
            "analysis": {"decision": "manual_review", "error": str(exc)},
            "decision": "manual_review",
        }


def assemble_origination_pipeline() -> list[dict]:
    """Build the four-step close pipeline with dependency metadata."""
    return [
        {
            "id": "INC-1",
            "phase": 1,
            "action": "order_income_verification",
            "planned_days": 5,
            "depends_on": [],
            "blocks": ["TTL-1"],
        },
        {
            "id": "TTL-1",
            "phase": 2,
            "action": "order_title_review",
            "planned_days": 10,
            "depends_on": ["INC-1"],
            "blocks": ["APR-1"],
        },
        {
            "id": "APR-1",
            "phase": 3,
            "action": "order_appraisal",
            "planned_days": 15,
            "depends_on": [],
            "signoff_requires": ["TTL-1"],
            "blocks": ["CLS-1"],
        },
        {
            "id": "CLS-1",
            "phase": 4,
            "action": "closing",
            "planned_days": 5,
            "depends_on": ["INC-1", "TTL-1", "APR-1"],
            "blocks": [],
        },
    ]


def _project_timeline(
    income_days: int,
    title_days: int,
    appraisal_days: int,
    closing_days: int,
) -> dict:
    income_end = income_days
    title_start = income_end
    title_end = title_start + title_days
    appraisal_work_end = appraisal_days
    appraisal_cleared = max(appraisal_work_end, title_end)
    closing_start = appraisal_cleared
    closing_end = closing_start + closing_days
    return {
        "income_end": income_end,
        "title_start": title_start,
        "title_end": title_end,
        "appraisal_work_end": appraisal_work_end,
        "appraisal_cleared": appraisal_cleared,
        "closing_start": closing_start,
        "closing_end": closing_end,
    }


def project_planned_close(pipeline: list[dict]) -> dict:
    """Baseline schedule using planned durations only."""
    by_action = {step["action"]: step["planned_days"] for step in pipeline}
    timeline = _project_timeline(
        by_action["order_income_verification"],
        by_action["order_title_review"],
        by_action["order_appraisal"],
        by_action["closing"],
    )
    return {
        **timeline,
        "target_close_day": TARGET_CLOSE_DAYS,
        "on_track": timeline["closing_end"] <= TARGET_CLOSE_DAYS,
        "projected_close_day": timeline["closing_end"],
    }


class CloseSchedulePlanner:
    """Monitors origination milestones and reschedules close when steps slip."""

    def __init__(
        self,
        llm: LendingLLM | None = None,
        seed: int | None = None,
    ) -> None:
        self.llm = llm or get_llm_client()
        self.rng = random.Random(seed)
        self.monitor_log: list[dict] = []
        self.reschedule_count = 0
        self.execution_log: list[dict] = []

    def track_milestone_progress(
        self,
        day: int,
        message: str,
        step_id: str,
        planned_days: int,
        actual_days: int,
        timing: str,
    ) -> None:
        entry = {
            "day": day,
            "step_id": step_id,
            "message": message,
            "planned_days": planned_days,
            "actual_days": actual_days,
            "timing": timing,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        self.monitor_log.append(entry)

    def reschedule_after_slippage(
        self,
        prior_target: int,
        new_projected_close: int,
        reason: str,
    ) -> dict:
        self.reschedule_count += 1
        revision = {
            "revision": self.reschedule_count,
            "prior_target_day": prior_target,
            "new_projected_close_day": new_projected_close,
            "slip_days": new_projected_close - prior_target,
            "reason": reason,
        }
        self.monitor_log.append(
            {
                "day": new_projected_close,
                "step_id": f"REV-{self.reschedule_count}",
                "message": (
                    f"Close rescheduled from day {prior_target} to day {new_projected_close}: "
                    f"{reason}"
                ),
                "planned_days": prior_target,
                "actual_days": new_projected_close,
                "timing": "rescheduled",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        )
        return revision

    def run_pipeline_with_monitoring(
        self,
        pipeline: list[dict],
        target_close: int = TARGET_CLOSE_DAYS,
    ) -> dict:
        """Simulate actual step durations, monitor progress, and reschedule if needed."""
        self.monitor_log.clear()
        self.execution_log.clear()
        by_id = {step["id"]: step for step in pipeline}

        inc = by_id["INC-1"]
        ttl = by_id["TTL-1"]
        apr = by_id["APR-1"]
        cls = by_id["CLS-1"]

        profile = _choose_run_profile(self.rng)
        slip_steps = (
            self.rng.sample(["INC-1", "TTL-1", "APR-1", "CLS-1"], k=self.rng.randint(1, 2))
            if profile == "at_risk"
            else []
        )

        actual_income, income_timing = _draw_actual_days(
            inc["planned_days"],
            self.rng,
            profile,
            force_delay="INC-1" in slip_steps,
        )
        income_end = actual_income
        self.track_milestone_progress(
            income_end,
            "Income verification complete",
            inc["id"],
            inc["planned_days"],
            actual_income,
            income_timing,
        )
        self.execution_log.append(
            {"task_id": inc["id"], "action": inc["action"], "status": "completed", "end_day": income_end}
        )

        actual_title, title_timing = _draw_actual_days(
            ttl["planned_days"],
            self.rng,
            profile,
            force_delay="TTL-1" in slip_steps,
        )
        title_end = income_end + actual_title
        self.track_milestone_progress(
            title_end,
            "Title review complete (required before appraisal sign-off)",
            ttl["id"],
            ttl["planned_days"],
            actual_title,
            title_timing,
        )
        self.execution_log.append(
            {"task_id": ttl["id"], "action": ttl["action"], "status": "completed", "end_day": title_end}
        )

        actual_appraisal, appraisal_timing = _draw_actual_days(
            apr["planned_days"],
            self.rng,
            profile,
            force_delay="APR-1" in slip_steps,
        )
        appraisal_work_end = actual_appraisal
        if appraisal_work_end < title_end:
            self.track_milestone_progress(
                appraisal_work_end,
                "Appraisal field work complete; awaiting title clearance to sign",
                apr["id"],
                apr["planned_days"],
                actual_appraisal,
                appraisal_timing,
            )
        appraisal_cleared = max(appraisal_work_end, title_end)
        self.track_milestone_progress(
            appraisal_cleared,
            "Appraisal signed and sent to bank",
            apr["id"],
            apr["planned_days"],
            actual_appraisal,
            "cleared" if appraisal_cleared == title_end else appraisal_timing,
        )
        self.execution_log.append(
            {
                "task_id": apr["id"],
                "action": apr["action"],
                "status": "completed",
                "end_day": appraisal_cleared,
            }
        )

        projected_before_close = appraisal_cleared + cls["planned_days"]
        revisions: list[dict] = []
        if projected_before_close > target_close:
            revisions.append(
                self.reschedule_after_slippage(
                    target_close,
                    projected_before_close,
                    "Upstream title or appraisal delay extends earliest closing date",
                )
            )

        actual_closing, closing_timing = _draw_actual_days(
            cls["planned_days"],
            self.rng,
            profile,
            force_delay="CLS-1" in slip_steps,
        )
        closing_end = appraisal_cleared + actual_closing
        self.track_milestone_progress(
            closing_end,
            "Closing complete",
            cls["id"],
            cls["planned_days"],
            actual_closing,
            closing_timing,
        )
        self.execution_log.append(
            {"task_id": cls["id"], "action": cls["action"], "status": "completed", "end_day": closing_end}
        )

        if closing_end > target_close and (
            not revisions or revisions[-1]["new_projected_close_day"] < closing_end
        ):
            revisions.append(
                self.reschedule_after_slippage(
                    target_close,
                    closing_end,
                    "Closing phase ran long after revised appraisal clearance",
                )
            )

        on_track = closing_end <= target_close
        final_target = target_close if on_track else closing_end

        return {
            "run_profile": profile,
            "target_close_day": target_close,
            "projected_close_day": closing_end,
            "final_scheduled_close_day": final_target,
            "on_track": on_track,
            "timeline": _project_timeline(actual_income, actual_title, actual_appraisal, actual_closing),
            "actual_durations": {
                "order_income_verification": actual_income,
                "order_title_review": actual_title,
                "order_appraisal": actual_appraisal,
                "closing": actual_closing,
            },
            "revisions": revisions,
        }

    def orchestrate_close_plan(self) -> dict:
        """Full workflow: credit check, plan assembly, simulated execution, narration."""
        snapshot = gather_underwriting_snapshot()
        pipeline = assemble_origination_pipeline()
        planned = project_planned_close(pipeline)

        if snapshot["decision"] not in {"approved", "manual_review"}:
            return {
                "customer_prompt": CUSTOMER_PROMPT,
                "underwriting": snapshot,
                "pipeline": pipeline,
                "planned_schedule": planned,
                "status": "declined",
                "llm_summary": (
                    "Home improvement capacity check did not pass. "
                    "Close scheduling cannot proceed until credit and equity support the request."
                ),
            }

        simulation = self.run_pipeline_with_monitoring(pipeline)
        decision_label = "on_track" if simulation["on_track"] else "delayed"
        llm_response = self.llm.generate(
            CUSTOMER_PROMPT,
            loan_product="close_planning",
            decision=decision_label,
        )

        return {
            "customer_prompt": CUSTOMER_PROMPT,
            "underwriting": snapshot,
            "pipeline": pipeline,
            "planned_schedule": planned,
            "simulation": simulation,
            "monitor_log": self.monitor_log,
            "execution_log": self.execution_log,
            "reschedule_count": self.reschedule_count,
            "status": decision_label,
            "llm_summary": llm_response.content,
        }
