from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.p5.models import TimeSlot


class Candidate(BaseModel):
    id: str
    name: str
    preferred_slots: list[TimeSlot] = Field(default_factory=list)


class Interviewer(BaseModel):
    id: str
    name: str
    available_slots: list[TimeSlot]
    max_interviews_per_day: int = 4


class ScheduleRequest(BaseModel):
    candidates: list[Candidate]
    interviewers: list[Interviewer]
    soft_constraints: list[str] = Field(default_factory=list)
    interview_duration_minutes: int = 45


class Assignment(BaseModel):
    candidate_id: str
    interviewer_id: str
    slot: TimeSlot
    explanation: str = ""


class ScheduleResult(BaseModel):
    assignments: list[Assignment]
    unscheduled: list[str]
    stats: dict[str, Any]
