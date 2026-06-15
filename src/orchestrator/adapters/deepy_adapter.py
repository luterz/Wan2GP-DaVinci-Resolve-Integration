import os
import json
import subprocess
import glob

def get_wan2gp_python(wan2gp_dir):
    paths = [
        os.path.join(wan2gp_dir, "wan2gp", "Scripts", "python.exe"),
        os.path.join(wan2gp_dir, "venv", "Scripts", "python.exe"),
        os.path.join(wan2gp_dir, ".venv", "Scripts", "python.exe")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return "python"

class DeepyAdapter:
    def __init__(self):
        self.output_dir = os.path.join(os.path.expanduser("~"), "WanGP_Resolve_Data", "cache")
        os.makedirs(self.output_dir, exist_ok=True)
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        self.wan2gp_dir = ""
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.wan2gp_dir = json.load(f).get("wan2gp_dir", "")
        
    def process_job(self, job_data: dict) -> dict:
        if not self.wan2gp_dir:
            return {"status": "error", "error": "Wan2GP directory not configured"}
            
        params = job_data.get("parameters", {})
        prompt = params.get("prompt", "")
        input_media = job_data.get("input_media", {})
        media_path = input_media.get("path", "")
        mask_base64 = params.get("mask_base64", None)
        
        # Deepy usually works by reading natural language. 
        # We can append path information to the prompt to make Deepy aware of the source clip.
        if media_path:
            prompt += f"\nUse this input media: {media_path}"
        if mask_base64:
            prompt += f"\nA mask is provided via the UI."
            
        try:
            # Prepare Env
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{self.wan2gp_dir};{env.get('PYTHONPATH', '')}"
            python_exe = get_wan2gp_python(self.wan2gp_dir)

            # We use Popen and pass prompt via stdin, then 'quit'
            process = subprocess.Popen(
                [python_exe, "wgp.py", "--ask-deepy", "--output-dir", self.output_dir],
                cwd=self.wan2gp_dir,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send prompt and then quit
            stdout, stderr = process.communicate(input=f"{prompt}\nquit\n")
            
            # Get the most recently created mp4 in output_dir
            mp4_files = glob.glob(os.path.join(self.output_dir, "*.mp4"))
            if not mp4_files:
                return {"status": "error", "error": f"No output video found. stderr: {stderr[:500]}"}
                
            latest_mp4 = max(mp4_files, key=os.path.getmtime)
            return {"status": "success", "output_path": latest_mp4}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
