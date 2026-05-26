"""
Run: python -m backend.p5.eval
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[1] / ".env")

from backend.p5.extractor import extract_thread
from backend.p5.models import Intent, ThreadExtraction

DATA_DIR = Path(__file__).parents[2] / "data" / "emails"

GROUND_TRUTH: dict[str, Intent] = {
    "01": Intent.scheduling_request,
    "02": Intent.scheduling_request,
    "03": Intent.scheduling_request,
    "04": Intent.scheduling_request,
    "05": Intent.counter_proposal,
    "06": Intent.counter_proposal,
    "07": Intent.counter_proposal,
    "08": Intent.counter_proposal,
    "09": Intent.confirmation,
    "10": Intent.confirmation,
    "11": Intent.confirmation,
    "12": Intent.confirmation,
    "13": Intent.rejection,
    "14": Intent.rejection,
    "15": Intent.rejection,
    "16": Intent.rejection,
    "17": Intent.ghost,
    "18": Intent.ghost,
    "19": Intent.ghost,
    "20": Intent.ghost,
}


async def run_case(path: Path) -> tuple[str, Intent, ThreadExtraction]:
    text = path.read_text()
    extraction = await extract_thread(text)
    return path.stem[:2], GROUND_TRUTH[path.stem[:2]], extraction


async def main() -> None:
    files = sorted(DATA_DIR.glob("*.txt"))
    if not files:
        print(f"No email files found in {DATA_DIR}")
        return

    results = await asyncio.gather(*[run_case(f) for f in files])

    correct_intent = 0
    total_slots = 0
    slots_with_high_confidence = 0

    rows = []
    for case_id, expected, extraction in results:
        intent_ok = extraction.intent == expected
        if intent_ok:
            correct_intent += 1

        slot_count = len(extraction.proposed_slots)
        total_slots += slot_count
        high_conf = sum(1 for s in extraction.proposed_slots if s.confidence >= 0.7)
        slots_with_high_confidence += high_conf

        rows.append({
            "case": case_id,
            "expected": expected.value,
            "got": extraction.intent.value,
            "ok": "✓" if intent_ok else "✗",
            "slots": slot_count,
            "participants": len(extraction.participants),
            "next_action": extraction.next_action[:60],
        })

    print("\n=== P5 Eval Results ===\n")
    print(f"{'Case':<6} {'Expected':<22} {'Got':<22} {'OK':<4} {'Slots':<6} {'Ppl':<4} Next Action")
    print("-" * 100)
    for r in rows:
        print(f"{r['case']:<6} {r['expected']:<22} {r['got']:<22} {r['ok']:<4} {r['slots']:<6} {r['participants']:<4} {r['next_action']}")

    n = len(results)
    print(f"\nIntent accuracy:     {correct_intent}/{n} = {correct_intent/n*100:.1f}%")
    print(f"Total slots found:   {total_slots}")
    print(f"High-conf slots:     {slots_with_high_confidence}/{total_slots}" if total_slots else "High-conf slots: N/A")
    print()


if __name__ == "__main__":
    asyncio.run(main())
