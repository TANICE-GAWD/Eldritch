from __future__ import annotations

from pydantic_ai import Agent

from backend.model import claude
from backend.p5.models import ThreadExtraction

_SYSTEM_PROMPT = """
You are a scheduling intelligence engine. Given a raw email thread, extract structured scheduling state.

Classify the thread intent based on the INITIAL PURPOSE of the thread — why the conversation was started — not its final state.

- scheduling_request: the thread was initiated to set up a meeting (even if a time was eventually confirmed)
- counter_proposal: the thread was initiated or pivoted because someone proposed alternative times
- confirmation: the sole purpose of the thread is confirming an already-agreed time (e.g. a calendar acceptance, a "see you then" reply)
- rejection: someone declined, cancelled, or withdrew
- ghost: one side stopped replying; thread went silent

A thread that starts with a scheduling request and ends with both parties agreeing on a time is still scheduling_request — the confirmation is the outcome, not the intent.

For proposed_slots:
- If a specific time was agreed upon or chosen by any party, return ONLY that slot at confidence 1.0. Do not include the rejected alternatives.
- If no time has been chosen yet, return all proposed slots with appropriate confidence scores (lower for vague times like "sometime next week").
- If the thread is a ghost or rejection, return an empty list.

Identify all participants and their roles (organizer, required, optional).
Provide a clear next_action recommendation for the scheduling agent.

Examples:

Thread: "Hi Alex, are you free Thursday at 2pm or Friday morning for a quick call? - Sarah"
→ intent: scheduling_request, proposed_slots: [Thu 2pm, Fri morning], next_action: "Await Alex's reply"

Thread: "Thanks for the invite but I'm unavailable that week. - Jordan"
→ intent: rejection, proposed_slots: [], next_action: "Propose alternate dates to Jordan"

Thread: "Sounds good, locked in for Tuesday 3pm EST. Calendar invite sent."
→ intent: confirmation, proposed_slots: [Tue 3pm EST, confidence 1.0], next_action: "No action needed"

Thread: [Email sent 3 days ago, no reply]
→ intent: ghost, proposed_slots: [], next_action: "Follow up via alternate channel"

CRITICAL datetime rules:
- ALWAYS output start and end as ISO 8601 strings: "2026-05-21T14:00:00" — never natural language like "next Monday at 10am"
- ALWAYS include both start and end. If only a start is mentioned, add 1 hour for end.
- If the date is relative ("next Monday", "Thursday"), resolve it to an absolute date. Assume today is 2026-05-28 if no reference date is available.
- Use UTC if no timezone is mentioned. Format: "2026-05-21T14:00:00"
- ALWAYS include the email field for participants. Use empty string "" if unknown.
- Return confidence < 0.6 for vague slots like "sometime next week".
"""

extractor_agent = Agent(
    model=claude,
    output_type=ThreadExtraction,
    system_prompt=_SYSTEM_PROMPT,
)


async def extract_thread(email_text: str) -> ThreadExtraction:
    result = await extractor_agent.run(email_text)
    return result.output
