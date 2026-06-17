# DaVinci Resolve AI Workflow Integration (MVP Plan)

This implementation plan outlines the architecture and execution steps for building a local-first DaVinci Resolve Studio Workflow Integration. The system allows users to select a timeline clip, send it to a local AI backend (e.g., Wan2GP) for processing (upscale, object removal, restyle), and seamlessly re-insert the processed clip back into the timeline.

## Workspace Inspection
I have inspected the current workspace at `f:/progetti antigravity/wan2gp Davinci` and found that **the directory is completely empty**. We are starting from a clean slate.

## Missing Prerequisites and Unknowns
- **Resolve Workflow Integration Paths**: On macOS, workflow integrations are typically installed in `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Workflow Integrations/`. We will need to map our development folder there (e.g., via symlink).
- **Resolve API Clip Export**: DaVinci Resolve's Python API can trigger renders or export clips. Extracting an exact sub-segment of a timeline clip programmatically without triggering a full timeline render can sometimes be tricky. We will need to validate the best approach (Render Job vs. Media Pool export).

## Architecture Proposal

I propose an **Orchestrator Architecture (Variant B)**.

### Overview
1. **Resolve Plugin (Frontend + Bridge)**: An HTML/JS Panel running inside Resolve's UI. A companion Python script (`app.py`) bridges the Panel to the DaVinci Resolve API.
2. **Local Orchestrator (Backend API)**: A lightweight, standalone Python FastAPI server. It manages a job queue, tracks status, and handles file I/O.
3. **Backend Adapters**: Pluggable Python modules within the Orchestrator that interface with specific AI engines (Wan2GP first, ComfyUI later).

### Architectural Tradeoffs (Why Orchestrator?)
- **Variant A (Tightly Coupled)**: The Resolve plugin directly spawns AI inference processes.
  - *Pros*: Single codebase, easy to distribute.
  - *Cons*: Heavy AI processing can block or crash Resolve. Difficult to debug the AI pipeline independently. Extremely hard to scale to remote rendering later.
- **Variant B (Orchestrator - Recommended)**: Resolve plugin communicates via HTTP to a local background server.
  - *Pros*: **Strong separation of concerns**. Resolve is never blocked. The Orchestrator can be tested and debugged completely independently of Resolve. Makes swapping backends (Wan2GP -> ComfyUI) trivial without updating the Resolve plugin. Supports future features like remote rendering and queuing.
  - *Cons*: Requires running a background server alongside Resolve.

### Project Folder Structure
```text
wan2gp-davinci/                 # Main Source Code Repository
├── resolve_plugin/             # The actual Resolve Workflow Integration
│   ├── index.html              # Panel UI
│   ├── app.js                  # Panel logic, calls Orchestrator/Python
│   ├── style.css               # Styling
│   └── resolve_bridge.py       # Python script interacting with Resolve API
├── orchestrator/               # Standalone FastAPI server
│   ├── main.py                 # API Endpoints
│   ├── job_manager.py          # Queue and status tracking
│   └── models.py               # Pydantic schemas (Job, Status, etc.)
└── adapters/                   # AI Backend integrations
    ├── base_adapter.py         # Abstract interface
    ├── wan2gp_adapter.py       # Wan2GP implementation
    └── comfyui_adapter.py      # Future ComfyUI implementation

# Runtime / Config Directories (External to repo)
# e.g., ~/Documents/Wan2GP_Jobs/ or ~/.config/wan2gp_davinci/
runtime_data/
└── jobs/                       # Configurable path for media exchange
    ├── job_<uuid>/
    │   ├── input.mov
    │   ├── mask.png
    │   └── output.mov
```

## Interfaces & Data Formats

### 1. Job JSON (Orchestrator API)
Used for `POST /api/v1/jobs`.
```json
{
  "id": "uuid-1234",
  "operation": "remove", 
  "input_video_path": "/absolute/path/to/jobs/job_1234/input.mov",
  "prompt": "remove the car",
  "upscale_factor": 2.0,
  "status": "pending",
  "output_video_path": null,
  "resolve_metadata": {
    "track_index": 1,
    "start_frame": 100,
    "end_frame": 250
  }
}
```

### 2. Annotation JSON
Used by the frontend to save masking data before sending the job.
```json
{
  "reference_frame_path": "/absolute/path/to/jobs/job_1234/ref.png",
  "mask_path": "/absolute/path/to/jobs/job_1234/mask.png",
  "polygons": [ [x1,y1], [x2,y2] ]
}
```

### 3. Backend Adapter Interface (Python)
```python
class BaseAdapter:
    async def process_job(self, job: JobModel) -> JobResult:
        """Takes a job, runs inference, returns paths to outputs."""
        pass
        
    def cancel_job(self, job_id: str):
        pass
```

### 4. Render Manifest
Returned by Orchestrator on job completion, used by `resolve_bridge.py` to re-import.
```json
{
  "job_id": "uuid-1234",
  "media_path": "/absolute/path/to/jobs/job_1234/output.mov",
  "insertion_mode": "overlay",
  "target_track": 2,
  "target_start_frame": 100
}
```

## End-to-End MVP Workflow
1. User places playhead over a clip in the Resolve timeline.
2. User opens our Workflow Integration Panel.
3. Panel calls `resolve_bridge.py` to extract the clip segment to the `jobs/` directory and extract a reference frame.
4. Panel UI shows the reference frame. User draws a mask (if doing object removal).
5. Panel saves `mask.png` and sends a `POST` request to the Orchestrator with `job.json`.
6. Panel polls Orchestrator for status (`pending` -> `processing`).
7. Orchestrator uses `Wan2GPAdapter` to run the inference locally.
8. Wan2GP generates `output.mov`. Orchestrator marks job `done`.
9. Panel sees `done` status, retrieves the Render Manifest, and calls `resolve_bridge.py`.
10. `resolve_bridge.py` imports `output.mov` into the Media Pool and places it on the timeline as an **overlay** (Track N+1) matching the exact original timing.

## Risks & Technical Spikes
> [!WARNING]
> **Resolve API Export Spike (High Priority)**: Exporting an exact sub-segment of an individual clip directly from the timeline via the API is not a simple one-liner. Resolve's API is robust for full project/timeline renders, but extracting a small timeline slice requires setting In/Out marks and creating a targeted Render Job, or finding a workaround via the Media Pool. **This is a priority technical spike for Phase 1.**
> 
> **Panel-to-Python Interop Risk**: In Resolve Workflow Integrations, the UI is an embedded CEF browser. The assumption that the HTML/JS panel can uniformly "call" external Python scripts across all installations is risky. We must establish a robust, verified communication channel (e.g., via the `window.WorkflowIntegration` API injecting Python execution, or spinning up a local Websocket server from a bootstrap Python script) as our very first technical validation.
> 
> **Framerate/Timecode Mismatches**: AI backends often strip or alter timecode metadata. We must rely on frame counting and explicit placement in Resolve to maintain sync.
> 
> **Wan2GP Integration**: Wan2GP exposes a dedicated **WanGP API** as well as a headless CLI mode. We will need to inspect the API documentation (likely local swagger at `/docs` when running) to format the job requests correctly.

---

## Phased Implementation Plan

### Phase 1: Technical Spikes & Core Scaffolding
- **Spike 1: Sub-segment Export**: Write a raw Python script that connects to an active Resolve session and successfully exports a selected clip segment using the Render Queue (In/Out marks).
- **Spike 2: Panel-to-Python Comm**: Create a minimal HTML Panel and verify the exact mechanism for it to trigger the Python export script (via `window.WorkflowIntegration` or local HTTP).
- Setup project folder structure (keeping `jobs/` out of the repo).
- Implement `resolve_bridge.py` based on Spike 1.
- Implement a mock Orchestrator (FastAPI) that just waits 5 seconds and returns the original video.
- **Goal**: Verify UI -> Python -> API -> Python -> Resolve Timeline loop works reliably.

### Phase 2: Orchestrator & Job Management
- Formalize the FastAPI server.
- Implement job queues and SQLite or in-memory status tracking.
- Implement the `BaseAdapter` interface.

### Phase 3: Wan2GP Adapter Implementation
- Implement `wan2gp_adapter.py`.
- Connect it to the local Wan2GP installation (CLI or API).
- Process real video files.
- **Goal**: Real AI processing on a hardcoded input.

### Phase 4: Annotation UI (Masking)
- Add canvas-based masking to the HTML panel.
- Export drawn masks as `mask.png` to the job folder.
- Ensure Wan2GP adapter consumes the mask correctly for removal/restyle operations.

### Phase 5: Polish & Deployment
- Robust error handling and progress bars.
- Packaging for easy installation on macOS.
- Settings page for API urls, backend paths.

---

## Files to Create in Phase 1
- `resolve_plugin/index.html` (Basic UI with "Process Clip" button)
- `resolve_plugin/app.js` (Fetch API calls)
- `resolve_plugin/resolve_bridge.py` (DaVinci Resolve API scripting)
- `orchestrator/main.py` (FastAPI mock server)
- `orchestrator/models.py` (Job schema)
- `requirements.txt`

## Open Questions
1. Do you have a preference for how the resolve plugin is tested during development? (e.g. symlinking the dev folder into the Resolve plugins folder).
2. Do you want the annotation UI to be built with a specific library (e.g., Fabric.js or just vanilla HTML5 Canvas)?

## Recommended Phase Order
I recommend executing **Phase 1** first to ensure we can programmatically extract and re-insert media from Resolve. Without this, the AI backend is useless.

## Execution prompt for Phase 1
When you are ready to begin, reply with:
> "Approved. Proceed with Phase 1: create the scaffolding, the mock orchestrator, and the resolve bridge to test the round-trip export/import."
