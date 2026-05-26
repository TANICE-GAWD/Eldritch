from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.db import create_job, get_job, update_job
from backend.p4.models import Interviewer, ScheduleRequest
from backend.p4.soft import annotate_assignments, parse_soft_constraints
from backend.p4.solver import solve
from backend.p5.extractor import extract_thread
from backend.p5.models import ThreadExtraction
from backend.pipeline import run_pipeline

app = FastAPI(title="Vela MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractRequest(BaseModel):
    email_text: str


@app.post("/extract", response_model=ThreadExtraction)
async def extract(req: ExtractRequest) -> ThreadExtraction:
    return await extract_thread(req.email_text)


class ScheduleRequestAPI(BaseModel):
    candidates: list[dict[str, Any]]
    interviewers: list[dict[str, Any]]
    soft_constraints: list[str] = []
    interview_duration_minutes: int = 45
    annotate: bool = True


@app.post("/schedule")
async def schedule(req: ScheduleRequestAPI) -> dict[str, Any]:
    from backend.p4.models import Candidate

    candidates = [Candidate(**c) for c in req.candidates]
    interviewers = [Interviewer(**iv) for iv in req.interviewers]

    penalty_weights, constraint_explanation = await parse_soft_constraints(req.soft_constraints)
    schedule_req = ScheduleRequest(
        candidates=candidates,
        interviewers=interviewers,
        soft_constraints=req.soft_constraints,
        interview_duration_minutes=req.interview_duration_minutes,
    )
    result = solve(schedule_req, penalty_weights=penalty_weights)

    if req.annotate and result.assignments:
        result = await annotate_assignments(result, candidates, interviewers)

    return {
        "schedule": result.model_dump(mode="json"),
        "constraint_explanation": constraint_explanation,
    }


class PipelineRequest(BaseModel):
    email_threads: list[str]
    interviewers: list[dict[str, Any]]
    soft_constraints: list[str] = []
    interview_duration_minutes: int = 45


@app.post("/pipeline/run")
async def pipeline_run(req: PipelineRequest) -> dict[str, Any]:
    interviewers = [Interviewer(**iv) for iv in req.interviewers]
    job_id = await create_job(req.model_dump())
    try:
        await update_job(job_id, "running")
        result = await run_pipeline(
            email_threads=req.email_threads,
            interviewers=interviewers,
            soft_constraints=req.soft_constraints,
            interview_duration_minutes=req.interview_duration_minutes,
        )
        await update_job(job_id, "done", result)
        return {"job_id": job_id, **result}
    except Exception as exc:
        await update_job(job_id, "error", {"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict[str, Any]:
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
