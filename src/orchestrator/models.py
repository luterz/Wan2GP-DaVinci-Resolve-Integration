from pydantic import BaseModel
from typing import Optional, List, Tuple
from datetime import datetime

class InputMedia(BaseModel):
    path: Optional[str] = ""
    fps: Optional[float] = 24.0
    resolution: Optional[Tuple[int, int]] = (1920, 1080)
    duration_frames: Optional[int] = 100
    duration_seconds: Optional[float] = None

class JobParameters(BaseModel):
    prompt: str = ""
    model_type: Optional[str] = None
    mask_base64: Optional[str] = None
    out_resolution: Optional[str] = None
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None
    duration_seconds: Optional[int] = None
    # Legacy fields
    upscale_factor: Optional[float] = 1.0
    backend_url: Optional[str] = None
    wan_model: Optional[str] = None
    denoising_strength: Optional[float] = None
    gen_audio: Optional[bool] = None

class JobTimestamps(BaseModel):
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class JobRequest(BaseModel):
    id: str
    mode: str = "inpaint"
    input_media: Optional[InputMedia] = None
    parameters: Optional[JobParameters] = None
    # Legacy fields (kept for backward compat)
    backend: Optional[str] = "wangp"
    adapter_mode: Optional[str] = "api"
    operation: Optional[str] = None
    operation_profile: Optional[str] = None
    wangp_settings_ref: Optional[str] = None

class OutputPolicy(BaseModel):
    container: str = "mov"
    codec: str = "ProRes422"

class ResolveMetadata(BaseModel):
    target_timeline: str
    target_track_index: int
    target_start_frame: int
    duration_frames: int

class RenderManifest(BaseModel):
    job_id: str
    output_media_path: str
    insertion_policy: str = "overlay"
    audio_policy: str = "mute_new"
    output_policy: OutputPolicy
    resolve_metadata: ResolveMetadata

class JobStatus(BaseModel):
    id: str
    status: str  # pending, processing, done, error
    error: Optional[str] = None
    timestamps: JobTimestamps
    manifest: Optional[RenderManifest] = None
