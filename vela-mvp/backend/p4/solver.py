from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ortools.sat.python import cp_model

from backend.p4.models import (
    Assignment,
    Candidate,
    Interviewer,
    ScheduleRequest,
    ScheduleResult,
)
from backend.p5.models import TimeSlot


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _slots_overlap(a: TimeSlot, b: TimeSlot, buffer_minutes: int = 15) -> bool:
    buffer = timedelta(minutes=buffer_minutes)
    return _utc(a.start) < _utc(b.end) + buffer and _utc(b.start) < _utc(a.end) + buffer


def _slots_same_day(a: TimeSlot, b: TimeSlot) -> bool:
    return _utc(a.start).date() == _utc(b.start).date()


def solve(request: ScheduleRequest, penalty_weights: dict[str, int] | None = None) -> ScheduleResult:
    """
    CP-SAT solver for interview scheduling.

    Hard constraints:
    - Each candidate assigned to exactly one slot + one interviewer (or unscheduled)
    - No interviewer double-booked (with 15-min buffer)
    - Interviewer slot must be in their availability
    - Candidate slot must overlap with their preferred slots (if any)

    Soft constraints (via penalty_weights):
    - max_interviews_per_day: penalise assignments that exceed interviewer's daily cap
    """
    model = cp_model.CpModel()

    candidates = request.candidates
    interviewers = request.interviewers
    duration = request.interview_duration_minutes

    # Collect all candidate slots: prefer their preferred slots, else use all interviewer slots
    all_interviewer_slots: list[TimeSlot] = []
    for iv in interviewers:
        all_interviewer_slots.extend(iv.available_slots)

    # x[c][i][s] = 1 if candidate c is assigned to interviewer i at slot s
    # We enumerate (candidate, interviewer, slot) triples where the slot is valid for both
    triples: list[tuple[int, int, int, TimeSlot]] = []  # (c_idx, i_idx, s_idx, slot)
    slot_pool: list[TimeSlot] = []
    slot_index: dict[int, TimeSlot] = {}

    for c_idx, candidate in enumerate(candidates):
        for i_idx, interviewer in enumerate(interviewers):
            for slot in interviewer.available_slots:
                # Check slot duration fits
                if (slot.end - slot.start) < timedelta(minutes=duration):
                    continue
                # If candidate has preferences, slot must overlap
                if candidate.preferred_slots:
                    overlap = any(
                        not _slots_overlap(slot, ps, buffer_minutes=0)
                        and slot.start <= ps.start and slot.end >= ps.end
                        or (slot.start <= ps.start < slot.end)
                        or (ps.start <= slot.start < ps.end)
                        for ps in candidate.preferred_slots
                    )
                    if not overlap:
                        continue
                s_idx = len(slot_pool)
                slot_pool.append(slot)
                slot_index[s_idx] = slot
                triples.append((c_idx, i_idx, s_idx, slot))

    # Decision variables
    x: dict[tuple[int, int, int], cp_model.IntVar] = {}
    for c_idx, i_idx, s_idx, _ in triples:
        x[(c_idx, i_idx, s_idx)] = model.new_bool_var(f"x_{c_idx}_{i_idx}_{s_idx}")

    # Each candidate assigned at most once
    for c_idx in range(len(candidates)):
        model.add_at_most_one(
            x[(c_idx, i_idx, s_idx)]
            for (ci, i_idx, s_idx, _) in triples
            if ci == c_idx
        )

    # No interviewer double-booked (accounting for buffer)
    for i_idx in range(len(interviewers)):
        i_triples = [(c_idx, s_idx, slot) for (c_idx, ii, s_idx, slot) in triples if ii == i_idx]
        for idx_a in range(len(i_triples)):
            for idx_b in range(idx_a + 1, len(i_triples)):
                c_a, s_a, slot_a = i_triples[idx_a]
                c_b, s_b, slot_b = i_triples[idx_b]
                if _slots_overlap(slot_a, slot_b):
                    model.add(x[(c_a, i_idx, s_a)] + x[(c_b, i_idx, s_b)] <= 1)

    # Soft: penalise exceeding max_interviews_per_day
    penalty_terms = []
    pw = penalty_weights or {}
    daily_penalty = pw.get("max_interviews_per_day", 10)

    for i_idx, interviewer in enumerate(interviewers):
        # Group triples by day
        days: dict[str, list[tuple[int, int]]] = {}
        for (c_idx, ii, s_idx, slot) in triples:
            if ii != i_idx:
                continue
            day_key = slot.start.date().isoformat()
            days.setdefault(day_key, []).append((c_idx, s_idx))
        for day_key, day_triples in days.items():
            daily_sum = sum(x[(c_idx, i_idx, s_idx)] for (c_idx, s_idx) in day_triples)
            overflow = model.new_int_var(0, len(day_triples), f"overflow_{i_idx}_{day_key}")
            model.add(overflow >= daily_sum - interviewer.max_interviews_per_day)
            penalty_terms.append(overflow * daily_penalty)

    # Objective: maximise scheduled candidates, minimise penalties
    scheduled_sum = sum(x.values())
    if penalty_terms:
        model.maximize(scheduled_sum * 100 - sum(penalty_terms))
    else:
        model.maximize(scheduled_sum)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.solve(model)

    assignments: list[Assignment] = []
    scheduled_ids: set[str] = set()

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for (c_idx, i_idx, s_idx), var in x.items():
            if solver.value(var):
                candidate = candidates[c_idx]
                interviewer = interviewers[i_idx]
                slot = slot_index[s_idx]
                assignments.append(Assignment(
                    candidate_id=candidate.id,
                    interviewer_id=interviewer.id,
                    slot=slot,
                ))
                scheduled_ids.add(candidate.id)

    unscheduled = [c.id for c in candidates if c.id not in scheduled_ids]

    # Stats
    interviewer_loads: dict[str, int] = {iv.id: 0 for iv in interviewers}
    for a in assignments:
        interviewer_loads[a.interviewer_id] += 1
    avg_load = sum(interviewer_loads.values()) / len(interviewers) if interviewers else 0

    return ScheduleResult(
        assignments=assignments,
        unscheduled=unscheduled,
        stats={
            "total_scheduled": len(assignments),
            "total_unscheduled": len(unscheduled),
            "avg_interviewer_load": round(avg_load, 2),
            "interviewer_loads": interviewer_loads,
        },
    )
