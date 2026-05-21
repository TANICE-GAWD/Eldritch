from __future__ import annotations

import asyncio

from pydantic import BaseModel
from pydantic_ai import Agent

from backend.model import claude
from backend.p4.models import Assignment, ScheduleResult


class PenaltyWeights(BaseModel):
    max_interviews_per_day: int = 10
    friday_overload: int = 5
    senior_junior_mismatch: int = 8
    custom: dict[str, int] = {}


class ConstraintParseResult(BaseModel):
    weights: PenaltyWeights
    explanation: str


_SYSTEM_PROMPT = """
You are a scheduling constraint interpreter. Given plain-English scheduling rules,
return penalty weights for a CP-SAT optimizer and a brief explanation.

Penalty weights are integers 1–100. Higher = stronger penalty.

Example:
Rules: ["no more than 3 interviews per interviewer on Fridays", "senior engineers shouldn't interview junior roles"]
→ weights: { max_interviews_per_day: 10, friday_overload: 20, senior_junior_mismatch: 15 }

Return only what applies. Use defaults for unmentioned constraints.
"""

_constraint_agent = Agent(
    model=claude,
    output_type=ConstraintParseResult,
    system_prompt=_SYSTEM_PROMPT,
)


async def parse_soft_constraints(rules: list[str]) -> tuple[dict[str, int], str]:
    if not rules:
        return {}, "No soft constraints provided."
    prompt = "Rules:\n" + "\n".join(f"- {r}" for r in rules)
    result = await _constraint_agent.run(prompt)
    weights = result.output.weights
    return {
        "max_interviews_per_day": weights.max_interviews_per_day,
        "friday_overload": weights.friday_overload,
        "senior_junior_mismatch": weights.senior_junior_mismatch,
        **weights.custom,
    }, result.output.explanation


_EXPLAIN_SYSTEM = """
You are a scheduling explainer. Given an interview assignment (candidate, interviewer, time slot),
write a single concise sentence explaining why this pairing was chosen.
Be specific: mention the time, the interviewer, and any relevant constraint satisfied.
"""

_explain_agent = Agent(
    model=claude,
    output_type=str,
    system_prompt=_EXPLAIN_SYSTEM,
)


async def annotate_assignments(result: ScheduleResult, candidates: list, interviewers: list) -> ScheduleResult:
    candidate_map = {c.id: c.name for c in candidates}
    interviewer_map = {iv.id: iv.name for iv in interviewers}

    async def explain_one(assignment: Assignment) -> Assignment:
        prompt = (
            f"Candidate: {candidate_map.get(assignment.candidate_id, assignment.candidate_id)}\n"
            f"Interviewer: {interviewer_map.get(assignment.interviewer_id, assignment.interviewer_id)}\n"
            f"Slot: {assignment.slot.start.strftime('%A %b %d, %I:%M %p')} – "
            f"{assignment.slot.end.strftime('%I:%M %p')} {assignment.slot.timezone}"
        )
        res = await _explain_agent.run(prompt)
        return assignment.model_copy(update={"explanation": res.output})

    annotated = await asyncio.gather(*[explain_one(a) for a in result.assignments])
    return result.model_copy(update={"assignments": list(annotated)})
