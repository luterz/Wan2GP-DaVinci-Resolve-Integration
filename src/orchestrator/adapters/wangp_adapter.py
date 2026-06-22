import os
import json
import subprocess
import math


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


class WanGPAdapter:
    def __init__(self, api_session=None):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.output_dir = os.path.join(project_root, "data", "cache")
        os.makedirs(self.output_dir, exist_ok=True)
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        self.wan2gp_dir = ""
        self.api_session = api_session
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.wan2gp_dir = json.load(f).get("wan2gp_dir", "")

    def process_job(self, job_data, status_updater=None, current_status=None):
        try:
            job_id = job_data["id"]
            params = job_data["params"]
            input_media = job_data.get("input_media", {})
            mode = params.get("mode")
            model_type = params.get("model_type")
            prompt = params.get("prompt")
            resolution = params.get("resolution", "1280x720")

            if mode == "inpaint":
                settings = self._build_inpaint_settings(params, input_media, job_id, model_type, prompt, resolution)
            elif mode == "generate_i2v":
                settings = self._build_i2v_settings(params, input_media, model_type, prompt, resolution)
            elif mode == "audio_tts":
                settings = self._build_tts_settings(params, model_type, prompt)
            else:
                return {"status": "error", "error": f"Unknown mode: {mode}"}

            if settings is None:
                return {"status": "error", "error": "Failed to build settings"}

            if self.api_session:
                # Use native Python API
                print(f"[{job_id}] Submitting task via Native API...")
                job = self.api_session.submit_task(settings)
                
                for event in job.events.iter():
                    if event.kind == "progress":
                        progress = event.data
                        if status_updater and current_status:
                            pct = progress.progress
                            if pct < 0:
                                pct = 0
                            elif pct > 100:
                                pct = 100
                            current_status.progress = pct
                            current_status.progress_message = f"{progress.phase} ({progress.current_step}/{progress.total_steps})"
                            status_updater(current_status)
                    elif event.kind == "stream":
                        line = event.data
                        # Optional: Print or log stream text
                        pass

                result = job.result()
                if not result.success:
                    error_msg = result.errors[0].message if result.errors else "Unknown error"
                    return {"status": "error", "error": error_msg}
                
                if not result.generated_files:
                    return {"status": "error", "error": "No output file found"}
                return {"status": "success", "output_path": result.generated_files[-1]}

            else:
                # Fallback to subprocess if API not initialized
                # Write settings and run WanGP
                settings_path = os.path.join(self.output_dir, f"job_{job_id}_settings.json")
                with open(settings_path, "w") as f:
                    json.dump(settings, f)
    
                env = os.environ.copy()
                env["PYTHONPATH"] = f"{self.wan2gp_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
                python_exe = get_wan2gp_python(self.wan2gp_dir)
    
                cmd = [python_exe, "wgp.py", "--process", settings_path, "--output-dir", self.output_dir]
                if params.get("fast_attention", True):
                    cmd.extend(["--attention", "sage2"])
    
                process = subprocess.Popen(
                    cmd,
                    cwd=self.wan2gp_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
    
                # Save logs
                log_path = os.path.join(self.output_dir, "last_run.log")
                with open(log_path, "w") as lf:
                    lf.write(f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}")
    
                if process.returncode != 0:
                    error_msg = stderr.strip() if stderr.strip() else stdout.strip()
                    return {"status": "error", "error": f"WanGP failed. Check last_run.log. Error: {error_msg[:500]}"}
    
                # Find output
                if mode == "audio_tts":
                    out_files = [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir)
                                 if f.endswith(".wav") or f.endswith(".mp3") or f.endswith(".flac") or f.endswith(".mp4")]
                else:
                    out_files = [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir)
                                 if f.endswith(".mp4") or f.endswith(".mov")]
    
                if not out_files:
                    return {"status": "error", "error": "No output file found"}
    
                latest = max(out_files, key=os.path.getmtime)
                return {"status": "success", "output_path": latest}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _build_inpaint_settings(self, params, input_media, job_id, model_type, prompt, resolution):
        """Build settings for VACE or LTX-2 inpainting mode."""
        model_type = model_type or "vace_14B_2_2"
        is_ltx2 = "ltx2" in model_type.lower()
        
        settings = {
            "model_type": model_type,
            "prompt": prompt,
            "resolution": resolution,
            "num_inference_steps": params.get("steps", 8 if is_ltx2 else 30),
            "image_mode": 0,
            "video_guide": input_media.get("path", ""),
            "sample_solver": "euler" if is_ltx2 else "unipc",
            "video_source": input_media.get("path", ""),
            "denoising_strength": 1.0 if is_ltx2 else 0.90,
        }

        if not is_ltx2:
            # Set flow_shift based on model variant for VACE
            if "2_2" in model_type:
                settings["flow_shift"] = 2.0
            else:
                settings["flow_shift"] = 5.0
            
        # Calculate video_length from source duration
        duration_seconds = input_media.get("duration_seconds", 4.0)
        
        if is_ltx2:
            # LTX-2: native fps 24, frames 8n+1
            target_frames = max(25, int(duration_seconds * 24))
            settings["video_length"] = ((target_frames - 1 + 7) // 8) * 8 + 1
        else:
            # VACE: native fps 16, frames 4n+1
            target_frames = max(17, int(duration_seconds * 16))
            settings["video_length"] = ((target_frames - 1 + 3) // 4) * 4 + 1

        # Process mask for VACE
        mask_path = ""
        if params.get("mask_base64"):
            import base64
            from PIL import Image
            import io
            mask_data = params["mask_base64"].split(",")[1] if "," in params["mask_base64"] else params["mask_base64"]
            img = Image.open(io.BytesIO(base64.b64decode(mask_data)))
            if img.mode == 'RGBA':
                img = img.split()[3]  # Extract alpha channel
            elif img.mode != 'L':
                img = img.convert('L')
            mask_path = os.path.join(self.output_dir, f"mask_{job_id}.png")
            img.save(mask_path)
            
        # Process reference image for EditAnything
        is_edit_anything = "editanything" in model_type.lower().replace("_", "")
        ref_image_path = ""
        if is_edit_anything and params.get("reference_image_base64"):
            import base64
            from PIL import Image
            import io
            ref_data = params["reference_image_base64"].split(",")[1] if "," in params["reference_image_base64"] else params["reference_image_base64"]
            img = Image.open(io.BytesIO(base64.b64decode(ref_data)))
            ref_image_path = os.path.join(self.output_dir, f"ref_{job_id}.png")
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(ref_image_path)

        if mask_path:
            settings["video_mask"] = mask_path
            settings["masking_strength"] = 1.0

        if is_edit_anything:
            if mask_path:
                settings["video_prompt_type"] = "VGIA"
            else:
                settings["video_prompt_type"] = "VGI"
            settings["audio_prompt_type"] = ""
            if ref_image_path:
                settings["image_refs"] = ref_image_path
        elif mask_path:
            if is_ltx2:
                settings["video_prompt_type"] = "VVA"
            else:
                settings["video_prompt_type"] = "MVA"
        else:
            # MV = M(Inpainting) + V(Control Video), no mask
            settings["video_prompt_type"] = "MV"

        return settings

    def _build_i2v_settings(self, params, input_media, model_type, prompt, resolution):
        """Build settings for LTX-2 image-to-video generation."""
        model_type = model_type or "ltx2_22B_distilled_1_1"
        
        duration_seconds = params.get("duration_seconds", 4)
        target_fps = 24  # LTX-2 native fps
        target_frames = max(25, int(duration_seconds * target_fps))
        # LTX-2: frames must be 8n+1
        target_frames = ((target_frames - 1 + 7) // 8) * 8 + 1

        settings = {
            "model_type": model_type,
            "prompt": prompt,
            "resolution": resolution if resolution != "832x480" else "1280x720",
            "num_inference_steps": params.get("steps", 8),
            "image_mode": 0,
            "video_length": target_frames,
            "image_start": input_media.get("path", "")
        }

        return settings

    def _build_tts_settings(self, params, model_type, prompt):
        """Build settings for TTS audio generation."""
        settings = {
            "model_type": model_type or "qwen3_tts_voicedesign",
            "prompt": prompt,
            "duration_seconds": params.get("duration_seconds", 30),
        }
        
        # Audio generation extras (Language and Style/Prompt)
        if params.get("model_mode"):
            settings["model_mode"] = params["model_mode"]
        if params.get("alt_prompt"):
            settings["alt_prompt"] = params["alt_prompt"]
            
        return settings
