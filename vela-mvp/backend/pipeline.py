from __future__ import annotations

import asyncio

from backend.p4.models import Candidate, ScheduleRequest, ScheduleResult
from backend.p4.soft import annotate_assignments, parse_soft_constraints
from backend.p4.solver import solve
from backend.p5.extractor import extract_thread
from backend.p5.models import Intent, ThreadExtraction


def _extraction_to_candidate(extraction: ThreadExtraction, candidate_id: str) -> Candidate | None:
    if extraction.intent not in (Intent.scheduling_request, Intent.counter_proposal):
        return None
    organizer = next(
        (p for p in extraction.participants if p.role == "organizer"),
        extraction.participants[0] if extraction.participants else None,
    )
    name = organizer.name if organizer else candidate_id
    return Candidate(
        id=candidate_id,
        name=name,
        preferred_slots=extraction.proposed_slots,
    )


async def run_pipeline(
    email_threads: list[str],
    interviewers: list,
    soft_constraints: list[str] | None = None,
    interview_duration_minutes: int = 45,
) -> dict:
    soft_constraints = soft_constraints or []

    extractions: list[ThreadExtraction] = await asyncio.gather(
        *[extract_thread(text) for text in email_threads]
    )

    candidates: list[Candidate] = []
    skipped: list[dict] = []
    for idx, extraction in enumerate(extractions):
        candidate_id = f"candidate_{idx+1:03d}"
        candidate = _extraction_to_candidate(extraction, candidate_id)
        if candidate:
            candidates.append(candidate)
        else:
            skipped.append({"id": candidate_id, "intent": extraction.intent.value, "reason": "non-actionable intent"})

    if not candidates:
        return {
            "extractions": [e.model_dump(mode="json") for e in extractions],
            "schedule": None,
            "skipped": skipped,
            "message": "No actionable scheduling threads found.",
        }

    penalty_weights, constraint_explanation = await parse_soft_constraints(soft_constraints)

    request = ScheduleRequest(
        candidates=candidates,
        interviewers=interviewers,
        soft_constraints=soft_constraints,
        interview_duration_minutes=interview_duration_minutes,
    )
    schedule_result: ScheduleResult = solve(request, penalty_weights=penalty_weights)
    schedule_result = await annotate_assignments(schedule_result, candidates, interviewers)

    return {
        "extractions": [e.model_dump(mode="json") for e in extractions],
        "schedule": schedule_result.model_dump(mode="json"),
        "skipped": skipped,
        "constraint_explanation": constraint_explanation,
    }
