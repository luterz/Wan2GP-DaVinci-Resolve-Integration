import os
import time
import json
import shutil
from datetime import datetime

# Import paths and models from main (if needed) or define here
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import JobStatus, RenderManifest, OutputPolicy, ResolveMetadata
from adapters.wangp_adapter import WanGPAdapter
from adapters.deepy_adapter import DeepyAdapter

DATA_DIR = os.path.join(os.path.expanduser("~"), "WanGP_Resolve_Data")
JOBS_DIR = os.path.join(DATA_DIR, "jobs")

def read_status(job_id: str) -> JobStatus | None:
    path = os.path.join(JOBS_DIR, "status", f"{job_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return JobStatus.model_validate_json(f.read())

def write_status(job_id: str, status_obj: JobStatus):
    path = os.path.join(JOBS_DIR, "status", f"{job_id}.json")
    with open(path, "w") as f:
        f.write(status_obj.model_dump_json())

def process_pending_jobs():
    wangp_adapter = WanGPAdapter()
    deepy_adapter = DeepyAdapter()
    pending_dir = os.path.join(JOBS_DIR, "pending")
    processing_dir = os.path.join(JOBS_DIR, "processing")
    completed_dir = os.path.join(JOBS_DIR, "completed")
    failed_dir = os.path.join(JOBS_DIR, "failed")
    
    print("[Job Processor] Waiting for jobs...")
    
    while True:
        try:
            for filename in os.listdir(pending_dir):
                if not filename.endswith(".json"):
                    continue
                    
                job_id = filename.replace(".json", "")
                src_path = os.path.join(pending_dir, filename)
                dst_path = os.path.join(processing_dir, filename)
                
                # Move to processing
                shutil.move(src_path, dst_path)
                
                # Read job data
                with open(dst_path, "r") as f:
                    job_data = json.load(f)
                    
                # Update status
                status = read_status(job_id)
                if status:
                    status.status = "processing"
                    status.timestamps.started_at = datetime.now()
                    write_status(job_id, status)
                
                # Call Adapter based on backend
                backend = job_data.get("backend", "wangp")
                if backend == "deepy":
                    result = deepy_adapter.process_job(job_data)
                else:
                    result = wangp_adapter.process_job(job_data)
                
                if result.get("status") == "success":
                    # Move to completed
                    shutil.move(dst_path, os.path.join(completed_dir, filename))
                    if status:
                        status.status = "done"
                        status.timestamps.completed_at = datetime.now()
                        status.manifest = RenderManifest(
                            job_id=job_id,
                            output_media_path=result["output_path"],
                            insertion_policy="overlay",
                            audio_policy="mute_new",
                            output_policy=OutputPolicy(container="mov", codec="ProRes422"),
                            resolve_metadata=ResolveMetadata(
                                target_timeline="Timeline 1", # Hardcoded for now
                                target_track_index=2,
                                target_start_frame=0, 
                                duration_frames=job_data.get("input_media", {}).get("duration_frames", 100)
                            )
                        )
                        write_status(job_id, status)
                else:
                    # Move to failed
                    shutil.move(dst_path, os.path.join(failed_dir, filename))
                    if status:
                        status.status = "error"
                        status.error = result.get("error", "Unknown error")
                        status.timestamps.completed_at = datetime.now()
                        write_status(job_id, status)
                        
        except Exception as e:
            print(f"[Job Processor] Error in poll loop: {e}")
            
        time.sleep(2) # Poll interval

if __name__ == "__main__":
    process_pending_jobs()
