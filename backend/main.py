"""
Parallax backend — FastAPI skeleton matching CONTRACT.md.

What's real here: the API surface, async job queue, CORS, and /files static
serving. What's stubbed (marked TODO): PartCrafter on GMI (image -> parts) and
the GMI LLM agent. The frontend can build against this immediately; swap the
stubs for real GMI calls without touching the contract.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from contract import (
    AgentRequest,
    AgentResponse,
    BBox,
    Job,
    ModelResult,
    Part,
    ResetAction,
)

load_dotenv()

FILES_DIR = Path(__file__).parent / "files"
FILES_DIR.mkdir(exist_ok=True)

# CORS: allow the Vercel frontend + local dev. Add the prod domain here.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000"
    ).split(",")
    if o.strip()
]

app = FastAPI(title="Parallax Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",  # preview deploys
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static binaries: input image + part GLBs, served at /files/<model_id>/...
app.mount("/files", StaticFiles(directory=str(FILES_DIR)), name="files")

# In-memory job store. Fine for a hackathon; swap for SQLite/Redis if needed.
JOBS: dict[str, Job] = {}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/generate", status_code=202)
async def generate(image: UploadFile = File(...)) -> Job:
    """Accept an image, queue a generation job, return immediately."""
    job_id = str(uuid.uuid4())
    model_id = str(uuid.uuid4())

    model_dir = FILES_DIR / model_id
    model_dir.mkdir(parents=True, exist_ok=True)
    input_path = model_dir / "input.png"
    with input_path.open("wb") as f:
        shutil.copyfileobj(image.file, f)

    job = Job(job_id=job_id, status="queued", progress=0)
    JOBS[job_id] = job
    asyncio.create_task(_run_generation(job_id, model_id))
    return job


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> Job:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/api/agent")
async def agent(req: AgentRequest) -> AgentResponse:
    """
    TODO: call the GMI serverless LLM (OpenAI-compatible, api.gmi-serving.com/v1)
    with the part inventory + the user's message, parse + validate its JSON
    actions against the schema in contract.py, drop unknown action types.

    Stub: echo the message and return a no-op reset so the loop is wired.
    """
    return AgentResponse(
        reply=f"(stub) You asked: {req.message!r}. Wire GMI in main.py:agent().",
        actions=[ResetAction(type="reset")],
    )


async def _run_generation(job_id: str, model_id: str) -> None:
    """
    Background generation. Replace the simulated steps with:
      1. POST the image to PartCrafter on GMI (PARTCRAFTER_URL).
      2. Receive per-part GLBs + a shared canonical frame.
      3. Save GLBs under files/<model_id>/p{i}.glb, build ModelResult.
    Fallback: a single fused mesh (GMI library model / Meshy) as a one-part
    result — same shape, parts length 1.
    """
    job = JOBS[job_id]
    try:
        job.status = "running"
        for pct in (20, 50, 80):
            await asyncio.sleep(1.0)
            job.progress = pct

        # TODO: real PartCrafter output goes here. Stubbed one-part result.
        job.result = ModelResult(
            model_id=model_id,
            source_image_url=f"/files/{model_id}/input.png",
            center=(0.0, 0.0, 0.0),
            bbox=BBox(min=(-1, -1, -1), max=(1, 1, 1)),
            parts=[
                Part(
                    part_id="p0",
                    label="part_0",
                    model_url=f"/files/{model_id}/p0.glb",  # not yet written
                    centroid=(0.0, 0.0, 0.0),
                    bbox=BBox(min=(-1, -1, -1), max=(1, 1, 1)),
                )
            ],
        )
        job.progress = 100
        job.status = "done"
    except Exception as exc:  # never let a job hang
        job.status = "error"
        job.error = str(exc)
