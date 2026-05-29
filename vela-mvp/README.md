# Vela MVP — Scheduling Intelligence Engine

P5 (Thread Intelligence) + P4 (Schedule Optimizer) demo for Vela (YC W26).

## What it does

1. **P5 — Thread Intelligence Engine**: Feed a raw email thread >> get structured scheduling state (intent, time slots, participants, next action) via Pydantic AI.
2. **P4 — Schedule Optimizer**: Feed N candidates + M interviewers >> get an optimally assigned schedule via Google OR-Tools CP-SAT + soft constraint interpretation.
3. **Pipeline**: Email threads >> P5 extraction >> P4 optimization >> annotated schedule grid.

## Setup

```bash
cd vela-mvp
pip install -r requirements.txt
```

Run Supabase schema:
```sql
-- paste supabase_schema.sql into your Supabase SQL editor
```

## Run

**Backend:**
```bash
uvicorn backend.api:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev   
```

**Eval harness (P5 accuracy):**
```bash
python -m backend.p5.eval
```

## API

| Endpoint | Description |
|---|---|
| `POST /extract` | P5: email thread text >> ThreadExtraction |
| `POST /schedule` | P4: candidates + interviewers >> ScheduleResult |
| `POST /pipeline/run` | End-to-end: email threads >> schedule |
| `GET /jobs/{id}` | Poll job status |

## Stack

- Python 3.11 + FastAPI
- Pydantic AI >> Claude Sonnet 4.6
- Google OR-Tools CP-SAT
- Supabase (state storage)
- Next.js 14 + Tailwind (schedule grid UI)


curl -s -X POST http://localhost:8000/pipeline/run \
    -H "Content-Type: application/json" \
    -d '{
      "email_threads": [
        "Hi Sam, are you free Thursday at 2pm for an interview? - Jordan at Acme",
        "Can we schedule a call next Monday at 10am? Thanks, Priya"
      ],
      "interviewers": [
        {
          "id": "iv1", "name": "Maya Patel",
          "available_slots": [
            {"start": "2026-05-21T14:00:00", "end": "2026-05-21T15:00:00", "confidence": 1.0, "timezone": "UTC"},
            {"start": "2026-05-25T10:00:00", "end": "2026-05-25T11:00:00", "confidence": 1.0, "timezone": "UTC"}
          ],
          "max_interviews_per_day": 3
        }
      ],
      "soft_constraints": []
    }' | python -m json.tool











curl -s http://localhost:8000/jobs/<job_id_here> | python -m json.tool