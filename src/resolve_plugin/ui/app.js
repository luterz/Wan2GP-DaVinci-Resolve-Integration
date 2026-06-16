const WorkflowIntegration = require('./WorkflowIntegration.node');
WorkflowIntegration.Initialize('com.antigravity.wangp');
const resolve = WorkflowIntegration.GetResolve();
const path = require('path');
const os = require('os');
const fs = require('fs');
const cp = require('child_process');

const ORCHESTRATOR_URL = "http://127.0.0.1:8000";
const START_SCRIPT = os.platform() === 'win32' 
    ? "F:\\progetti antigravity\\wan2gp Davinci\\start_wangp_services.bat"
    : "/Users/Shared/wan2gp_Davinci/start_wangp_services.sh";

// --- DOM Elements ---
const taskProfile = document.getElementById("taskProfile");
const modelSelect = document.getElementById("modelSelect");
const videoParams = document.getElementById("videoParams");
const durationRow = document.getElementById("durationRow");
const durationSlider = document.getElementById("durationSeconds");
const durationVal = document.getElementById("durationVal");
const processBtn = document.getElementById("processBtn");
const submitJobBtn = document.getElementById("submitJobBtn");
const statusLog = document.getElementById("statusLog");
const maskEditor = document.getElementById("maskEditor");
const refVideo = document.getElementById("refVideo");
const maskCanvas = document.getElementById("maskCanvas");
const clearMaskBtn = document.getElementById("clearMaskBtn");
const serverDot = document.getElementById("serverDot");
const serverLabel = document.getElementById("serverLabel");
const restartServerBtn = document.getElementById("restartServerBtn");
const stopServerBtn = document.getElementById("stopServerBtn");
const outResSelect = document.getElementById("outRes");
const stepsSlider = document.getElementById("steps");
const stepsVal = document.getElementById("stepsVal");
const cfgSlider = document.getElementById("cfgScale");
const cfgVal = document.getElementById("cfgVal");
const brushSizeInput = document.getElementById("brushSize");
const brushVal = document.getElementById("brushVal");
const promptInput = document.getElementById("prompt");
const hideTerminalCheckbox = document.getElementById("hideTerminalCheckbox");
const referenceImageRow = document.getElementById("referenceImageRow");
const referenceImageInput = document.getElementById("referenceImageInput");
const referenceImagePreview = document.getElementById("referenceImagePreview");

// Load hide terminal preference
hideTerminalCheckbox.checked = localStorage.getItem("hideTerminal") === "true";
hideTerminalCheckbox.addEventListener("change", () => {
    localStorage.setItem("hideTerminal", hideTerminalCheckbox.checked);
});

// --- Model Definitions per Mode ---
const MODE_MODELS = {
    inpaint: [
        { value: "ltx2_22B_editanything", label: "LTX-2 2.3 EditAnything Ref V2V 22B", steps: 8 },
        { value: "vace_14B_2_2", label: "Wan 2.2 VACE 14B (Quality)", steps: 30 },
        { value: "vace_14B_fusionix", label: "VACE FusioniX 14B (Fast)", steps: 10 },
        { value: "vace_14B_lightning_3p_2_2", label: "VACE Lightning 14B (Ultra-fast)", steps: 8 },
        { value: "vace_14B", label: "VACE 14B (Wan 2.1)", steps: 30 },
        { value: "ltx2_22B_distilled_1_1", label: "LTX-2 2.3 Distilled 1.1 22B (Recommended)", steps: 8 },
        { value: "ltx2_22B_distilled", label: "LTX-2 2.3 Distilled 1.0 22B", steps: 8 },
        { value: "ltx2_22B_distilled_gguf_q8_0", label: "LTX-2 2.3 Distilled GGUF Q8_0 22B", steps: 8 },
        { value: "ltx2_22B_distilled_gguf_q6_k", label: "LTX-2 2.3 Distilled GGUF Q6_K 22B", steps: 8 },
        { value: "ltx2_22B_distilled_gguf_q4_k_m", label: "LTX-2 2.3 Distilled GGUF Q4_K_M 22B", steps: 8 },
        { value: "ltx2_22B_1_1", label: "LTX-2 2.3 Dev 1.1 22B", steps: 30 },
        { value: "ltx2_22B", label: "LTX-2 2.3 Dev 1.0 22B", steps: 30 },
        { value: "ltx2_22B_nvfp4", label: "LTX-2 2.3 Dev NVFP4 22B", steps: 30 },
        { value: "ltx2_19B", label: "LTX-2 2.0 Dev 19B", steps: 30 },
        { value: "ltx2_distilled", label: "LTX-2 2.0 Distilled 19B", steps: 8 },
        { value: "ltx2_distilled_gguf_q8_0", label: "LTX-2 2.0 Distilled GGUF Q8_0 19B", steps: 8 },
        { value: "ltx2_distilled_gguf_q6_k", label: "LTX-2 2.0 Distilled GGUF Q6_K 19B", steps: 8 },
        { value: "ltx2_distilled_gguf_q4_k_m", label: "LTX-2 2.0 Distilled GGUF Q4_K_M 19B", steps: 8 },
        { value: "ltx2_19B_nvfp4", label: "LTX-2 2.0 Dev NVFP4 19B", steps: 30 },
    ],
    generate_i2v: [
        { value: "ltx2_22B_distilled_1_1", label: "LTX-2 2.3 Distilled 1.1 22B (Recommended)", steps: 8 },
        { value: "ltx2_22B_distilled", label: "LTX-2 2.3 Distilled 1.0 22B", steps: 8 },
        { value: "ltx2_22B_distilled_gguf_q8_0", label: "LTX-2 2.3 Distilled GGUF Q8_0 22B", steps: 8 },
        { value: "ltx2_22B_distilled_gguf_q6_k", label: "LTX-2 2.3 Distilled GGUF Q6_K 22B", steps: 8 },
        { value: "ltx2_22B_distilled_gguf_q4_k_m", label: "LTX-2 2.3 Distilled GGUF Q4_K_M 22B", steps: 8 },
        { value: "ltx2_22B_1_1", label: "LTX-2 2.3 Dev 1.1 22B", steps: 30 },
        { value: "ltx2_22B", label: "LTX-2 2.3 Dev 1.0 22B", steps: 30 },
        { value: "ltx2_22B_nvfp4", label: "LTX-2 2.3 Dev NVFP4 22B", steps: 30 },
        { value: "ltx2_19B", label: "LTX-2 2.0 Dev 19B", steps: 30 },
        { value: "ltx2_distilled", label: "LTX-2 2.0 Distilled 19B", steps: 8 },
        { value: "ltx2_distilled_gguf_q8_0", label: "LTX-2 2.0 Distilled GGUF Q8_0 19B", steps: 8 },
        { value: "ltx2_distilled_gguf_q6_k", label: "LTX-2 2.0 Distilled GGUF Q6_K 19B", steps: 8 },
        { value: "ltx2_distilled_gguf_q4_k_m", label: "LTX-2 2.0 Distilled GGUF Q4_K_M 19B", steps: 8 },
        { value: "ltx2_19B_nvfp4", label: "LTX-2 2.0 Dev NVFP4 19B", steps: 30 },
    ],
    audio_tts: [
        { value: "qwen3_tts_voicedesign", label: "Qwen3 VoiceDesign (Style Prompt)" },
        { value: "qwen3_tts_customvoice", label: "Qwen3 CustomVoice (Built-in Speakers)" },
        { value: "index_tts2", label: "Index TTS 2 (Emotions)" },
        { value: "omnivoice", label: "OmniVoice (Zero-shot)" },
        { value: "kugelaudio_0_open", label: "KugelAudio (Dialogue)" },
        { value: "stable_audio3_medium", label: "Stable Audio 3 (Music/SFX)" },
        { value: "scenema_audio", label: "Scenema Audio (Advanced Dialogue)" },
    ]
};

const MODE_DEFAULTS = {
    inpaint: { duration: 4, promptPlaceholder: "Describe what to generate in the masked area...", btnText: "Extract Timeline Clip & Annotate" },
    generate_i2v: { duration: 4, promptPlaceholder: "Describe the video to generate from this frame...", btnText: "Extract First Frame & Generate" },
    audio_tts: { duration: 30, promptPlaceholder: "Enter text to speak or describe the audio/music to generate...", btnText: "Generate Audio" }
};

let currentReferenceImageBase64 = null;

if (referenceImageInput) {
    referenceImageInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                currentReferenceImageBase64 = event.target.result;
                referenceImagePreview.src = currentReferenceImageBase64;
                referenceImagePreview.style.display = "block";
            };
            reader.readAsDataURL(file);
        } else {
            currentReferenceImageBase64 = null;
            referenceImagePreview.style.display = "none";
        }
    });
}

function toggleEditAnything() {
    const isEditAnything = modelSelect.value && modelSelect.value.includes("editanything");
    if (referenceImageRow) {
        referenceImageRow.style.display = isEditAnything ? "flex" : "none";
    }
}

// --- Mode Switching ---
function switchMode(mode) {
    const models = MODE_MODELS[mode] || [];
    const defaults = MODE_DEFAULTS[mode] || {};
    
    // Populate model dropdown
    modelSelect.innerHTML = "";
    models.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m.value;
        opt.textContent = m.label;
        modelSelect.appendChild(opt);
    });
    
    // Show/hide controls based on mode
    const isAudio = mode === "audio_tts";
    const isInpaint = mode === "inpaint";
    const isI2V = mode === "generate_i2v";
    
    videoParams.style.display = isAudio ? "none" : "block";
    durationRow.style.display = (isI2V || isAudio) ? "flex" : "none";
    document.getElementById("audioParams").style.display = isAudio ? "flex" : "none";
    document.getElementById("altPromptRow").style.display = isAudio ? "flex" : "none";
    
    // Set duration default
    durationSlider.value = defaults.duration || 4;
    durationSlider.max = isAudio ? 120 : 30;
    durationVal.textContent = durationSlider.value;
    
    // Set prompt placeholder
    promptInput.placeholder = defaults.promptPlaceholder || "";
    
    // Set button text
    processBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> ${defaults.btnText || 'Process'}`;
    
    // Update steps default when model changes
    if (models.length > 0 && models[0].steps) {
        stepsSlider.value = models[0].steps;
        stepsVal.textContent = models[0].steps;
    }
    
    // Hide mask editor when switching modes
    maskEditor.style.display = "none";
    toggleEditAnything();
}

taskProfile.addEventListener("change", () => switchMode(taskProfile.value));

modelSelect.addEventListener("change", () => {
    const mode = taskProfile.value;
    const models = MODE_MODELS[mode] || [];
    const selected = models.find(m => m.value === modelSelect.value);
    if (selected && selected.steps) {
        stepsSlider.value = selected.steps;
        stepsVal.textContent = selected.steps;
    }
    toggleEditAnything();
});

// Initialize with default mode
switchMode("inpaint");

// --- Slider Listeners ---
stepsSlider.addEventListener("input", (e) => stepsVal.textContent = e.target.value);
cfgSlider.addEventListener("input", (e) => cfgVal.textContent = parseFloat(e.target.value).toFixed(1));
brushSizeInput.addEventListener("input", (e) => brushVal.textContent = e.target.value);
durationSlider.addEventListener("input", (e) => durationVal.textContent = e.target.value);

// --- Logging ---
function log(msg) {
    const time = new Date().toLocaleTimeString();
    statusLog.textContent += `\n[${time}] ${msg}`;
    statusLog.scrollTop = statusLog.scrollHeight;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// --- Server Controls ---
let serverOnline = false;
let autoStartAttempted = false;

function setServerStatus(online) {
    if (online && !serverOnline) {
        serverDot.className = "dot dot-green";
        serverLabel.textContent = "Orchestrator: Online";
        serverOnline = true;
        log("Connected to Orchestrator.");
    } else if (!online && serverOnline) {
        serverDot.className = "dot dot-red";
        serverLabel.textContent = "Orchestrator: Offline";
        serverOnline = false;
        log("Lost connection to Orchestrator.");
    }
}

function stopServer() {
    log("Stopping Orchestrator...");
    if (os.platform() === 'win32') {
        cp.exec(`taskkill /F /IM uvicorn.exe /T`, () => {
            cp.exec(`wmic process where "name='python.exe' and commandline like '%job_processor.py%'" call terminate`, () => {
                cp.exec(`wmic process where "name='python.exe' and commandline like '%deepy_service.py%'" call terminate`, () => log("Server stopped."));
            });
        });
    } else {
        cp.exec(`pkill -f uvicorn`, () => cp.exec(`pkill -f job_processor.py`, () => cp.exec(`pkill -f deepy_service.py`, () => log("Server stopped."))));
    }
}

function startServer() {
    log("Starting Orchestrator...");
    const args = hideTerminalCheckbox.checked ? " --hidden" : "";
    const cmd = os.platform() === 'win32' 
        ? (hideTerminalCheckbox.checked ? `"${START_SCRIPT}" --hidden` : `start "" "${START_SCRIPT}"`)
        : `sh "${START_SCRIPT}"${args} &`;
    cp.exec(cmd, (err) => { if (err) log("Error starting server: " + err.message); });
}

restartServerBtn.addEventListener('click', () => { stopServer(); setTimeout(startServer, 2000); });
stopServerBtn.addEventListener('click', stopServer);

// Health check
setInterval(async () => {
    try {
        const res = await fetch(`${ORCHESTRATOR_URL}/api/v1/models`);
        setServerStatus(res.ok);
    } catch (e) { setServerStatus(false); }
}, 3000);

// Auto-start on load
(async () => {
    try {
        const res = await fetch(`${ORCHESTRATOR_URL}/api/v1/models`);
        if (res.ok) { setServerStatus(true); autoStartAttempted = true; }
        else throw new Error();
    } catch (e) {
        setServerStatus(false);
        if (!autoStartAttempted) {
            log("Orchestrator not found. Attempting auto-start...");
            autoStartAttempted = true;
            startServer();
        }
    }
})();

// --- Canvas / Mask ---
let maskCtx = maskCanvas.getContext("2d");
let isDrawing = false;
let currentExportData = null;

function resizeCanvases() {
    if (refVideo.videoWidth && refVideo.videoHeight) {
        maskCanvas.width = refVideo.videoWidth;
        maskCanvas.height = refVideo.videoHeight;
    } else {
        const rect = maskCanvas.parentElement.getBoundingClientRect();
        maskCanvas.width = rect.width;
        maskCanvas.height = rect.height;
    }
    maskCtx.lineCap = "round";
    maskCtx.lineJoin = "round";
    maskCtx.strokeStyle = "rgba(255, 0, 0, 1.0)";
}

window.addEventListener('resize', resizeCanvases);

function getCoords(e) {
    const rect = maskCanvas.getBoundingClientRect();
    return {
        x: (e.clientX - rect.left) * (maskCanvas.width / rect.width),
        y: (e.clientY - rect.top) * (maskCanvas.height / rect.height)
    };
}

maskCanvas.addEventListener('mousedown', (e) => {
    isDrawing = true;
    maskCtx.lineWidth = parseInt(brushSizeInput.value) || 30;
    maskCtx.strokeStyle = "rgba(255, 0, 0, 1.0)";
    maskCtx.fillStyle = "rgba(255, 0, 0, 1.0)";
    const coords = getCoords(e);
    maskCtx.beginPath();
    maskCtx.arc(coords.x, coords.y, maskCtx.lineWidth / 2, 0, Math.PI * 2);
    maskCtx.fill();
    maskCtx.beginPath();
    maskCtx.moveTo(coords.x, coords.y);
});
maskCanvas.addEventListener('mousemove', (e) => {
    if (!isDrawing) return;
    const coords = getCoords(e);
    maskCtx.lineTo(coords.x, coords.y);
    maskCtx.stroke();
});
maskCanvas.addEventListener('mouseup', () => isDrawing = false);
maskCanvas.addEventListener('mouseleave', () => isDrawing = false);
clearMaskBtn.addEventListener('click', () => maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height));

// --- Process Button ---
processBtn.addEventListener("click", async () => {
    processBtn.disabled = true;
    statusLog.textContent = "Starting process...";
    maskEditor.style.display = "none";
    currentExportData = null;
    
    const mode = taskProfile.value;
    
    try {
        // Audio TTS doesn't need media extraction
        if (mode === "audio_tts") {
            currentExportData = { mode: "audio_tts" };
            submitJobBtn.click();
            return;
        }
        
        log("Calling Resolve API to process selected clip...");
        if (!resolve) throw new Error("DaVinci Resolve API not initialized.");
        
        const project = resolve.GetProjectManager().GetCurrentProject();
        if (!project) throw new Error("No active project found.");
        const timeline = project.GetCurrentTimeline();
        if (!timeline) throw new Error("No active timeline found.");
        
        let targetClip = timeline.GetCurrentVideoItem();
        if (!targetClip) throw new Error("No video clip selected. Please select a clip.");
        if (Array.isArray(targetClip)) {
            if (targetClip.length === 0) throw new Error("No video clip selected.");
            targetClip = targetClip[0];
        }
        
        const startFrame = targetClip.GetStart();
        const duration = targetClip.GetDuration();
        const timelineFps = parseFloat(timeline.GetSetting("timelineFrameRate") || 24);
        const durationSeconds = duration / timelineFps;
        
        const PROJECT_ROOT = path.dirname(START_SCRIPT);
        const exportDir = path.join(PROJECT_ROOT, "data", "exports");
        if (!fs.existsSync(exportDir)) fs.mkdirSync(exportDir, { recursive: true });
        
        if (mode === "generate_i2v") {
            // Extract first frame as PNG
            const frameName = `frame_${Math.floor(Date.now() / 1000)}`;
            const framePath = path.join(exportDir, frameName + ".png");
            
            project.SetRenderSettings({
                "SelectAllFrames": false,
                "MarkIn": startFrame,
                "MarkOut": startFrame,
                "TargetDir": exportDir,
                "CustomName": frameName,
                "FormatWidth": 1920,
                "FormatHeight": 1080,
                "Format": "png"
            });
            
            const pid = project.AddRenderJob();
            if (!pid) throw new Error("Failed to add render job.");
            project.StartRendering(pid);
            
            while (true) {
                const status = project.GetRenderJobStatus(pid);
                if (status.JobStatus === "Complete") break;
                if (status.JobStatus === "Failed") throw new Error("Rendering failed.");
                if (status.JobStatus === "Cancelled") throw new Error("Rendering cancelled.");
                await sleep(500);
            }
            
            // Find the exported PNG
            const pngFiles = fs.readdirSync(exportDir).filter(f => f.startsWith(frameName) && f.endsWith('.png'));
            const actualFramePath = pngFiles.length > 0 ? path.join(exportDir, pngFiles[0]) : framePath;
            
            currentExportData = {
                mode: "generate_i2v",
                media_path: actualFramePath,
                fps: timelineFps,
                start_frame: startFrame,
                duration_frames: duration,
                duration_seconds: durationSeconds
            };
            
            log(`First frame extracted: ${actualFramePath}`);
            submitJobBtn.click();
            
        } else {
            // Inpaint: export video clip
            const exportFilename = `export_ui_${Math.floor(Date.now() / 1000)}.mp4`;
            const exportPath = path.join(exportDir, exportFilename);
            
            project.SetRenderSettings({
                "SelectAllFrames": false,
                "MarkIn": startFrame,
                "MarkOut": startFrame + duration - 1,
                "TargetDir": exportDir,
                "CustomName": exportFilename.split('.')[0],
                "FormatWidth": 1920,
                "FormatHeight": 1080,
                "Format": "mp4",
                "Codec": "H264"
            });
            
            const pid = project.AddRenderJob();
            if (!pid) throw new Error("Failed to add render job.");
            project.StartRendering(pid);
            
            while (true) {
                const status = project.GetRenderJobStatus(pid);
                if (status.JobStatus === "Complete") break;
                if (status.JobStatus === "Failed") throw new Error("Rendering failed.");
                if (status.JobStatus === "Cancelled") throw new Error("Rendering cancelled.");
                await sleep(500);
            }
            
            currentExportData = {
                mode: "inpaint",
                path: exportPath,
                fps: timelineFps,
                resolution: [1920, 1080],
                duration_frames: duration,
                duration_seconds: durationSeconds,
                start_frame: startFrame
            };
            
            log(`Exported clip: ${exportPath}`);
            log("Loading reference frame for mask drawing...");
            refVideo.src = require('url').pathToFileURL(exportPath).href;
            refVideo.load();
            
            refVideo.onloadeddata = () => { refVideo.currentTime = 0.1; };
            refVideo.onseeked = () => {
                maskEditor.style.display = "block";
                resizeCanvases();
                refVideo.style.display = "block";
                log("Draw the mask on the area you want to modify, then click Send Job to AI.");
            };
            refVideo.onerror = () => {
                log("Warning: Could not load reference. You can still submit.");
                maskEditor.style.display = "block";
            };
        }
    } catch (err) {
        log(`ERROR: ${err.message}`);
        processBtn.disabled = false;
    }
});

// --- Submit Job ---
submitJobBtn.addEventListener("click", async () => {
    if (!currentExportData && taskProfile.value !== "audio_tts") return;
    
    submitJobBtn.disabled = true;
    processBtn.disabled = true;
    
    try {
        log("Submitting job to Orchestrator...");
        
        let maskBase64 = null;
        if (taskProfile.value === "inpaint") {
            maskBase64 = maskCanvas.toDataURL("image/png");
        }
        
        const jobId = `job_${Math.random().toString(36).substring(2, 15)}`;
        const mode = taskProfile.value;
        
        const jobData = {
            id: jobId,
            mode: mode,
            input_media: currentExportData || {},
            parameters: {
                model_type: modelSelect.value,
                prompt: promptInput.value,
                model_mode: document.getElementById("modelMode").value,
                alt_prompt: document.getElementById("altPrompt").value,
                steps: parseInt(stepsSlider.value),
                cfg_scale: parseFloat(cfgSlider.value),
                out_resolution: outResSelect.value,
                mask_base64: maskBase64,
                reference_image_base64: currentReferenceImageBase64,
                duration_seconds: parseInt(durationSlider.value),
                fast_attention: document.getElementById("fastAttention").checked
            }
        };
        
        const jobRes = await fetch(`${ORCHESTRATOR_URL}/api/v1/jobs`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(jobData)
        });
        
        if (!jobRes.ok) throw new Error(`Job submission failed: ${jobRes.statusText}`);
        log(`Job ${jobId} submitted (${mode}). Waiting for completion...`);
        
        maskEditor.style.display = "none";
        
        let manifest = null;
        while (true) {
            await sleep(2000);
            const statusRes = await fetch(`${ORCHESTRATOR_URL}/api/v1/jobs/${jobId}`);
            if (!statusRes.ok) throw new Error("Failed to check status.");
            const statusData = await statusRes.json();
            log(`Status: ${statusData.status}`);
            if (statusData.status === "error") throw new Error(`Error: ${statusData.error}`);
            if (statusData.status === "done") { manifest = statusData.manifest; break; }
        }
        
        log(`Processing complete. Importing ${manifest.output_media_path}...`);
        
        if (!resolve) throw new Error("Resolve API not available.");
        const project = resolve.GetProjectManager().GetCurrentProject();
        const mediaPool = project.GetMediaPool();
        const importedItems = mediaPool.ImportMedia([manifest.output_media_path]);
        if (!importedItems || importedItems.length === 0) throw new Error("Failed to import media.");
        
        const timelineObj = project.GetCurrentTimeline();
        
        if (mode === "audio_tts") {
            // Create a new audio track and place audio there
            timelineObj.AddTrack("audio");
            const audioTrackCount = timelineObj.GetTrackCount("audio");
            const clipInfo = {
                "mediaPoolItem": importedItems[0],
                "trackIndex": audioTrackCount,
                "mediaType": 2  // 2 = Audio Only
            };
            const result = mediaPool.AppendToTimeline([clipInfo]);
            if (!result || result.length === 0) {
                mediaPool.AppendToTimeline(importedItems);
            }
            log("Audio placed on new audio track. Done!");
        } else {
            // Video: place on track 2
            if (timelineObj.GetTrackCount("video") < 2) timelineObj.AddTrack("video");
            const clipInfo = {
                "mediaPoolItem": importedItems[0],
                "startFrame": 0,
                "endFrame": (currentExportData.duration_frames || 100) - 1,
                "trackIndex": 2,
                "recordFrame": currentExportData.start_frame || 0,
                "mediaType": 1  // 1 = Video Only
            };
            const result = mediaPool.AppendToTimeline([clipInfo]);
            if (!result || result.length === 0) {
                log("Warning: Precise placement failed, using basic append.");
                mediaPool.AppendToTimeline(importedItems);
            }
            log("Video placed on timeline. Workflow complete!");
        }
        
    } catch (err) {
        log(`ERROR: ${err.message}`);
    } finally {
        submitJobBtn.disabled = false;
        processBtn.disabled = false;
    }
});

// --- Deepy Integration ---
const deepyBtn = document.getElementById("deepyBtn");
if (deepyBtn) {
    deepyBtn.addEventListener("click", async () => {
        const originalPrompt = promptInput.value.trim();
        if (!originalPrompt) {
            log("Please enter a prompt first before asking Deepy.");
            return;
        }
        
        deepyBtn.disabled = true;
        const originalText = deepyBtn.innerHTML;
        deepyBtn.innerHTML = "✨ Optimizing...";
        log("Sending prompt to Deepy for enhancement...");
        
        try {
            const mode = taskProfile.value === "audio_tts" ? "audio" : "video";
            
            let imageBase64 = null;
            if (mode === "video" && refVideo && refVideo.readyState >= 2) {
                const canvas = document.createElement("canvas");
                canvas.width = refVideo.videoWidth;
                canvas.height = refVideo.videoHeight;
                canvas.getContext("2d").drawImage(refVideo, 0, 0, canvas.width, canvas.height);
                imageBase64 = canvas.toDataURL("image/jpeg", 0.8);
            }
            
            const req = {
                prompt: originalPrompt,
                mode: mode,
                media_path: currentExportData ? currentExportData.path : null,
                image_base64: imageBase64
            };
            
            const res = await fetch(`http://127.0.0.1:8002/api/v1/deepy_enhance`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(req)
            });
            
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Deepy Service Error: ${res.status}`);
            }
            
            const data = await res.json();
            if (data.status === "success" && data.enhanced_prompt) {
                promptInput.value = data.enhanced_prompt;
                log("Prompt successfully enhanced by Deepy!");
            } else {
                throw new Error("Invalid response from Deepy service.");
            }
            
        } catch (err) {
            log(`DEEPY ERROR: ${err.message}`);
        } finally {
            deepyBtn.disabled = false;
            deepyBtn.innerHTML = originalText;
        }
    });
}

