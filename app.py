import os
import uuid
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

load_dotenv()

RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY", "")
RUNWAY_API_VERSION = os.getenv("RUNWAY_API_VERSION", "2024-11-06")
BASE_URL = "https://api.dev.runwayml.com/v1"

app = FastAPI(title="My AI Text-to-Video App")

jobs = {}


class GenerateRequest(BaseModel):
    prompt: str
    duration: int = 5
    ratio: str = "1280:720"


@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/generate")
def generate(data: GenerateRequest):
    if not RUNWAY_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Add your RUNWAY_API_KEY to the .env file or Render environment variables.",
        )

    if len(data.prompt.strip()) < 5:
        raise HTTPException(status_code=400, detail="Please write a longer prompt.")

    headers = {
        "Authorization": f"Bearer {RUNWAY_API_KEY}",
        "Content-Type": "application/json",
        "X-Runway-Version": RUNWAY_API_VERSION,
    }

    payload = {
        "model": "gen4.5",
        "promptText": data.prompt.strip(),
        "ratio": data.ratio,
        "duration": data.duration,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/image_to_video",
            headers=headers,
            json=payload,
            timeout=30,
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Could not reach the AI video provider.")

    if response.status_code not in (200, 201):
        try:
            message = response.json().get("error", response.text)
        except Exception:
            message = response.text
        raise HTTPException(status_code=response.status_code, detail=str(message))

    task_id = response.json().get("id")
    if not task_id:
        raise HTTPException(status_code=502, detail="Provider did not return a task ID.")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "task_id": task_id,
        "status": "generating",
        "video_url": None,
        "error": None,
    }

    return {"job_id": job_id, "status": "generating"}


@app.get("/api/status/{job_id}")
def status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job["status"] in ("completed", "failed"):
        return job

    headers = {
        "Authorization": f"Bearer {RUNWAY_API_KEY}",
        "X-Runway-Version": RUNWAY_API_VERSION,
    }

    try:
        response = requests.get(
            f"{BASE_URL}/tasks/{job['task_id']}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        task = response.json()
    except requests.RequestException as error:
        job["status"] = "failed"
        job["error"] = f"Provider status check failed: {error}"
        return job

    task_status = task.get("status")

    if task_status == "SUCCEEDED":
        output = task.get("output") or []
        job["status"] = "completed"
        job["video_url"] = output[0] if output else None
        if not job["video_url"]:
            job["status"] = "failed"
            job["error"] = "The provider did not return a video."
    elif task_status == "FAILED":
        job["status"] = "failed"
        job["error"] = task.get("failure", "The AI provider could not generate this video.")
    else:
        job["status"] = "generating"

    return job
