import os
import sys
import json
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Wan2GP Deepy Service")

# Allow CORS for UI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Optional

class EnhanceRequest(BaseModel):
    prompt: str
    mode: str = "video"  # "video", "image", "audio"
    media_path: Optional[str] = None
    image_base64: Optional[str] = None

def get_wan2gp_python(wan2gp_dir):
    is_windows = os.name == 'nt'
    script_dir = "Scripts" if is_windows else "bin"
    exe_name = "python.exe" if is_windows else "python"
    paths = [
        os.path.join(wan2gp_dir, "wan2gp", script_dir, exe_name),
        os.path.join(wan2gp_dir, "venv", script_dir, exe_name),
        os.path.join(wan2gp_dir, ".venv", script_dir, exe_name)
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return "python"

@app.post("/api/v1/deepy_enhance")
async def enhance_prompt(req: EnhanceRequest):
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        wan2gp_dir = ""
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                wan2gp_dir = json.load(f).get("wan2gp_dir", "")
        
        if not wan2gp_dir:
            raise HTTPException(status_code=500, detail="Wan2GP directory not configured")

        python_exe = get_wan2gp_python(wan2gp_dir)
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_deepy.py")
        
        env = os.environ.copy()
        
        # Map task types like V2V, I2V, T2V to 'video' for deepy.py
        deepy_mode = "video"
        if req.mode and req.mode.lower() in ["image", "audio"]:
            deepy_mode = req.mode.lower()
            
        cmd_args = [python_exe, script_path, "--prompt", req.prompt, "--mode", deepy_mode, "--wan2gp_dir", wan2gp_dir]
        
        # If UI sends base64, save it to a file
        media_path_to_use = req.media_path
        if req.image_base64:
            import base64
            img_data = req.image_base64.split(",")[1] if "," in req.image_base64 else req.image_base64
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache")
            os.makedirs(cache_dir, exist_ok=True)
            media_path_to_use = os.path.join(cache_dir, "deepy_ref.jpg")
            with open(media_path_to_use, "wb") as f:
                f.write(base64.b64decode(img_data))
                
        if media_path_to_use:
            cmd_args.extend(["--media_path", media_path_to_use])
        
        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            error_log_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache", "deepy_error.log")
            with open(error_log_path, "w") as f:
                f.write(f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}")
            print("Error running deepy:", stderr)
            raise HTTPException(status_code=500, detail=f"Deepy engine failed to run. Check {error_log_path}")
            
        # Parse stdout to extract between DEEPY_OUTPUT_START and DEEPY_OUTPUT_END
        if "---DEEPY_OUTPUT_START---" in stdout and "---DEEPY_OUTPUT_END---" in stdout:
            start_idx = stdout.find("---DEEPY_OUTPUT_START---") + len("---DEEPY_OUTPUT_START---")
            end_idx = stdout.find("---DEEPY_OUTPUT_END---")
            enhanced = stdout[start_idx:end_idx].strip()
            return {"status": "success", "enhanced_prompt": enhanced}
        else:
            print("Stdout:", stdout)
            print("Stderr:", stderr)
            raise HTTPException(status_code=500, detail="Failed to parse Deepy output")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="127.0.0.1", port=8002)
    except Exception as e:
        print(f"Server crashed: {e}")
        input("Press Enter to exit...")
