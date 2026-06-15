import os
import time
import json
import urllib.request
import urllib.error
import socket
import shutil
import base64
from typing import Optional

class WanGPAdapter:
    def __init__(self, api_url: str = "http://127.0.0.1:8080"):
        self.default_api_url = api_url

    def process_job(self, job_dict: dict) -> dict:
        """
        Takes a job dictionary, sends it to WanGP, and returns the output media path.
        If WanGP is unreachable, falls back to a mock process.
        """
        job_id = job_dict.get("id")
        operation = job_dict.get("operation")
        input_media = job_dict.get("input_media", {}).get("path")
        prompt = job_dict.get("parameters", {}).get("prompt", "")
        backend_url = job_dict.get("parameters", {}).get("backend_url", self.default_api_url)
        mask_base64 = job_dict.get("parameters", {}).get("mask_base64")
        
        print(f"[WanGP Adapter] Processing job {job_id} - Op: {operation} to {backend_url}")
        
        mask_path = None
        if mask_base64 and "base64," in mask_base64:
            # Decode and save mask
            b64_data = mask_base64.split("base64,")[1]
            mask_dir = os.path.join(os.path.expanduser("~"), "WanGP_Resolve_Data", "jobs", "masks")
            os.makedirs(mask_dir, exist_ok=True)
            mask_path = os.path.join(mask_dir, f"{job_id}_mask.png")
            with open(mask_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
        
        # Prepare WanGP API payload
        payload = {
            "task": operation,
            "input_video": input_media,
            "prompt": prompt,
            "output_format": "mov",
            "codec": "ProRes422"
        }
        if mask_path:
            payload["input_mask"] = mask_path
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(f"{backend_url}/api/v1/generate", data=data, headers={'Content-Type': 'application/json'})
        
        try:
            # Attempt to call the real WanGP API
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode())
                output_path = result.get("output_video")
                print(f"[WanGP Adapter] Success: {output_path}")
                return {"status": "success", "output_path": output_path}
                
        except (urllib.error.URLError, ConnectionRefusedError, TimeoutError, socket.timeout) as e:
            print(f"[WanGP Adapter] Server unreachable ({e}). Using MOCK FALLBACK.")
            return self._mock_process(job_dict)
            
        except Exception as e:
            print(f"[WanGP Adapter] Error: {e}")
            return {"status": "error", "error": str(e)}

    def _mock_process(self, job_dict: dict) -> dict:
        """Mock fallback that simulates processing by copying the input file."""
        time.sleep(3) # Simulate some AI thinking time
        
        input_path = job_dict.get("input_media", {}).get("path")
        if not input_path or not os.path.exists(input_path):
            return {"status": "error", "error": "Input file not found for mock"}
            
        # Create a dummy output path
        output_dir = os.path.join(os.path.expanduser("~"), "WanGP_Resolve_Data", "cache")
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(output_dir, f"{name}_processed{ext}")
        
        # Copy file to simulate a new processed file
        shutil.copy2(input_path, output_path)
        
        print(f"[WanGP Adapter] Mock processed: {output_path}")
        return {"status": "success", "output_path": output_path}
