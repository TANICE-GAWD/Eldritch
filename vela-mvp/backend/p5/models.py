from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Intent(str, Enum):
    scheduling_request = "scheduling_request"
    counter_proposal = "counter_proposal"
    confirmation = "confirmation"
    rejection = "rejection"
    ghost = "ghost"


class TimeSlot(BaseModel):
    start: datetime
    end: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    timezone: str = "UTC"


class Participant(BaseModel):
    name: str
    email: str
    role: Literal["organizer", "required", "optional"]


class ThreadExtraction(BaseModel):
    intent: Intent
    proposed_slots: list[TimeSlot]
    participants: list[Participant]
    next_action: str
    raw_summary: str
