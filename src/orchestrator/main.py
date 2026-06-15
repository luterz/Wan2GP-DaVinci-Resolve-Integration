import asyncio
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import re

from models import JobRequest, JobStatus, JobTimestamps, RenderManifest, OutputPolicy, ResolveMetadata

app = FastAPI(title="WanGP Orchestrator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.expanduser("~"), "WanGP_Resolve_Data")
JOBS_DIR = os.path.join(DATA_DIR, "jobs")
DIRS = ["pending", "processing", "completed", "failed", "status"]

# Ensure directories exist
for d in DIRS:
    os.makedirs(os.path.join(JOBS_DIR, d), exist_ok=True)

def write_status(job_id: str, status_obj: JobStatus):
    path = os.path.join(JOBS_DIR, "status", f"{job_id}.json")
    with open(path, "w") as f:
        f.write(status_obj.model_dump_json())

def read_status(job_id: str) -> JobStatus | None:
    path = os.path.join(JOBS_DIR, "status", f"{job_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return JobStatus.model_validate_json(f.read())

@app.post("/api/v1/jobs", response_model=JobStatus)
async def create_job(request: JobRequest):
    if read_status(request.id):
        raise HTTPException(status_code=400, detail="Job ID already exists")
        
    status = JobStatus(
        id=request.id,
        status="pending",
        timestamps=JobTimestamps(created_at=datetime.now())
    )
    
    # Write status
    write_status(request.id, status)
    
    # Drop job into pending folder
    job_path = os.path.join(JOBS_DIR, "pending", f"{request.id}.json")
    with open(job_path, "w") as f:
        f.write(request.model_dump_json())
        
    return status

@app.get("/api/v1/jobs/{job_id}", response_model=JobStatus)
async def get_job(job_id: str):
    status = read_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

_cached_models = None

@app.get("/api/v1/models")
async def get_models():
    global _cached_models
    if _cached_models is not None:
        return _cached_models

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    wan2gp_dir = ""
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            cfg = json.load(f)
            wan2gp_dir = cfg.get("wan2gp_dir", "")
    
    if not wan2gp_dir:
        raise HTTPException(status_code=500, detail="Wan2GP directory not configured.")

    from adapters.wangp_adapter import get_wan2gp_python
    python_exe = get_wan2gp_python(wan2gp_dir)
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{wan2gp_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

    script = """
import sys, json, os
sys.path.append('.')
import wgp

registry = {}
for model_id, model_def in wgp.models_def.items():
    metadata = model_def.get('metadata', {})
    family = metadata.get('family_label', metadata.get('family', 'Other'))
    version = 'Default'
    
    if family == 'ltx2': family = 'LTX'
    if family == 'wan2': family = 'Wan'
    if family == 'qwen': family = 'Qwen'

    name = model_def.get('name', model_id)
    
    if family not in registry:
        registry[family] = {}
    if version not in registry[family]:
        registry[family][version] = []
        
    registry[family][version].append({
        'label': name,
        'value': model_id
    })
print(json.dumps(registry))
"""
    import subprocess
    try:
        process = subprocess.Popen(
            [python_exe, "-c", script],
            cwd=wan2gp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            return {"error": f"Failed to query WanGP models: {stderr}"}
            
        json_str = stdout[stdout.find('{'):stdout.rfind('}')+1]
        _cached_models = json.loads(json_str)
        return _cached_models
    except Exception as e:
        return {"error": f"{str(e)}. Stdout was: {stdout[:200]}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
