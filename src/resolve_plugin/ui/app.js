const WorkflowIntegration = require('./WorkflowIntegration.node');
WorkflowIntegration.Initialize('com.antigravity.wangp');
const resolve = WorkflowIntegration.GetResolve();
const path = require('path');
const os = require('os');
const fs = require('fs');
const cp = require('child_process');

// --- Config ---
// Read PROJECT_ROOT from plugin_config.json (written by installer), fallback to hardcoded
let PROJECT_ROOT;
try {
    const pluginConfigPath = path.join(__dirname, 'plugin_config.json');
    if (fs.existsSync(pluginConfigPath)) {
        PROJECT_ROOT = JSON.parse(fs.readFileSync(pluginConfigPath, 'utf8')).project_root;
    }
} catch (e) { /* fallback below */ }
if (!PROJECT_ROOT) {
    PROJECT_ROOT = path.dirname(os.platform() === 'win32'
        ? "F:\\progetti antigravity\\wan2gp_Davinci_17_06\\start_wangp_services.bat"
        : "/Users/Shared/wan2gp_Davinci_17_06/start_wangp_services.sh");
}
const START_SCRIPT = path.join(PROJECT_ROOT, os.platform() === 'win32' ? "start_wangp_services.bat" : "start_wangp_services.sh");

let wan2gp_dir = "";
try {
    const configPath = path.join(PROJECT_ROOT, "src", "orchestrator", "config.json");
    if (fs.existsSync(configPath)) {
        wan2gp_dir = JSON.parse(fs.readFileSync(configPath, 'utf8')).wan2gp_dir;
    }
} catch (e) { console.error("Could not read config.json:", e); }

const WAN2GP_URL = "http://127.0.0.1:7860";

// --- DOM Elements ---
const extractBtn = document.getElementById("extractBtn");
const openBrowserBtn = document.getElementById("openBrowserBtn");
const restartServerBtn = document.getElementById("restartServerBtn");
const statusLog = document.getElementById("statusLog");
const galleryContainer = document.getElementById("galleryContainer");
const wanuiIframe = document.getElementById("wanui");
const loadingOverlay = document.getElementById("loadingOverlay");

// --- Logging ---
let logTimeout;
function log(msg) {
    statusLog.textContent = msg;
    statusLog.style.opacity = 1;
    clearTimeout(logTimeout);
    logTimeout = setTimeout(() => { statusLog.style.opacity = 0; }, 5000);
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// --- Server Health Check & Auto-Reload ---
let serverOnline = false;
let autoStartAttempted = false;

function startServer() {
    log("Avvio Wan2GP...");
    if (os.platform() === 'win32') {
        cp.exec(`start "" "${START_SCRIPT}"`);
    }
}

async function checkServer() {
    try {
        const http = require('http');
        return new Promise((resolve) => {
            const req = http.get(WAN2GP_URL, { timeout: 2000 }, (res) => {
                resolve(true);
                res.resume();
            });
            req.on('error', () => resolve(false));
            req.on('timeout', () => { req.destroy(); resolve(false); });
        });
    } catch (e) { return false; }
}

// Health check loop
setInterval(async () => {
    const online = await checkServer();
    if (online && !serverOnline) {
        serverOnline = true;
        log("Wan2GP Online! Caricamento UI...");
        loadingOverlay.style.display = 'none';
        wanuiIframe.src = WAN2GP_URL;
    } else if (!online && serverOnline) {
        serverOnline = false;
        loadingOverlay.style.display = 'flex';
        log("Wan2GP Offline.");
    }
}, 3000);

// Initial check
(async () => {
    const online = await checkServer();
    if (online) {
        serverOnline = true;
        loadingOverlay.style.display = 'none';
        wanuiIframe.src = WAN2GP_URL;
        log("Wan2GP connesso.");
    } else {
        loadingOverlay.style.display = 'flex';
        if (!autoStartAttempted) {
            autoStartAttempted = true;
            log("Wan2GP non trovato. Tentativo di avvio...");
            startServer();
        }
    }
})();

// --- Restart Button (kills only Wan2GP window, not all Python) ---
restartServerBtn.addEventListener('click', () => {
    log("Riavvio Wan2GP...");
    if (os.platform() === 'win32') {
        // Kill only the Wan2GP window by title, not all python processes
        cp.exec(`taskkill /FI "WINDOWTITLE eq Wan2GP*" /F`, (err) => {
            setTimeout(() => {
                cp.exec(`start "" "${START_SCRIPT}"`);
                log("Wan2GP riavviato.");
            }, 1500);
        });
    }
});

// --- Open in Browser ---
openBrowserBtn.addEventListener('click', () => {
    cp.exec(`start ${WAN2GP_URL}`);
    log("Aperto nel browser.");
});

// --- Extract Clip ---
let lastExtractedData = null;

extractBtn.addEventListener('click', async () => {
    extractBtn.disabled = true;
    extractBtn.textContent = "⏳ Esportazione...";
    log("Estrazione clip dalla timeline...");

    try {
        if (!resolve) throw new Error("DaVinci Resolve API non inizializzata.");
        const project = resolve.GetProjectManager().GetCurrentProject();
        if (!project) throw new Error("Nessun progetto attivo.");
        const timeline = project.GetCurrentTimeline();
        if (!timeline) throw new Error("Nessuna timeline attiva.");

        let targetClip = timeline.GetCurrentVideoItem();
        if (!targetClip) throw new Error("Nessuna clip video selezionata.");
        if (Array.isArray(targetClip)) {
            if (targetClip.length === 0) throw new Error("Nessuna clip video selezionata.");
            targetClip = targetClip[0];
        }

        const startFrame = targetClip.GetStart();
        const duration = targetClip.GetDuration();

        // Export to local data/exports
        const exportDir = path.join(PROJECT_ROOT, "data", "exports");
        if (!fs.existsSync(exportDir)) fs.mkdirSync(exportDir, { recursive: true });

        const ts = Math.floor(Date.now() / 1000);
        const exportFilename = `clip_${ts}.mp4`;
        const exportPath = path.join(exportDir, exportFilename);

        project.SetRenderSettings({
            "SelectAllFrames": false,
            "MarkIn": startFrame,
            "MarkOut": startFrame + duration - 1,
            "TargetDir": exportDir,
            "CustomName": exportFilename.split('.')[0],
            "FormatWidth": parseInt(project.GetSetting("timelineResolutionWidth") || 1920),
            "FormatHeight": parseInt(project.GetSetting("timelineResolutionHeight") || 1080),
            "Format": "mp4",
            "Codec": "H264"
        });

        const pid = project.AddRenderJob();
        if (!pid) throw new Error("Impossibile aggiungere il render job.");
        project.StartRendering(pid);

        // Show progress during render
        while (true) {
            const status = project.GetRenderJobStatus(pid);
            if (status.JobStatus === "Complete") break;
            if (status.JobStatus === "Failed") throw new Error("Render fallito.");
            if (status.JobStatus === "Cancelled") throw new Error("Render annullato.");
            const pct = status.CompletionPercentage || 0;
            extractBtn.textContent = `⏳ ${pct}%`;
            await sleep(300);
        }

        lastExtractedData = { path: exportPath, startFrame, duration };

        // Copy to Wan2GP inputs/ folder for easy drag & drop from File Gallery
        let wan2gpCopyPath = null;
        if (wan2gp_dir) {
            const inputsDir = path.join(wan2gp_dir, "inputs");
            if (!fs.existsSync(inputsDir)) fs.mkdirSync(inputsDir, { recursive: true });
            wan2gpCopyPath = path.join(inputsDir, exportFilename);
            fs.copyFileSync(exportPath, wan2gpCopyPath);
        }

        // Copy file path to clipboard (text + file object)
        const clipPath = wan2gpCopyPath || exportPath;
        if (os.platform() === 'win32') {
            cp.exec(`powershell -command "Set-Clipboard -Path '${clipPath}'"`);
        } else {
            cp.spawn('pbcopy').stdin.end(clipPath);
        }

        const inputsNote = wan2gpCopyPath
            ? `Clip copiata in Wan2GP/inputs/${exportFilename}. Aprila dalla File Gallery!`
            : "Clip estratta! Percorso copiato negli appunti.";
        log(inputsNote);

    } catch (err) {
        log(`ERRORE: ${err.message}`);
    } finally {
        extractBtn.disabled = false;
        extractBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg> Estrai Clip`;
    }
});

// --- Gallery & Output Watcher ---
let knownFilesMap = new Map(); // path -> mtime

function findMediaFiles(dir, fileList = []) {
    if (!fs.existsSync(dir)) return fileList;
    try {
        const files = fs.readdirSync(dir);
        for (const file of files) {
            const fullPath = path.join(dir, file);
            const stat = fs.statSync(fullPath); // single stat call
            if (stat.isDirectory()) {
                findMediaFiles(fullPath, fileList);
            } else if (fullPath.endsWith('.mp4') || fullPath.endsWith('.wav')) {
                fileList.push({ path: fullPath, mtime: stat.mtimeMs });
            }
        }
    } catch (e) { /* directory access error, skip */ }
    return fileList;
}

function renderGallery(files) {
    if (files.length === 0) {
        galleryContainer.innerHTML = '<div class="empty-gallery">Nessun output recente. Genera qualcosa in Wan2GP!</div>';
        return;
    }
    galleryContainer.innerHTML = '';
    files.forEach(f => {
        const item = document.createElement('div');
        item.className = 'gallery-item';

        const isAudio = f.path.endsWith('.wav');
        const basename = path.basename(f.path);

        if (!isAudio) {
            const vid = document.createElement('video');
            // Correct file:/// URI format for Windows
            vid.src = "file:///" + f.path.replace(/\\/g, '/');
            vid.loop = true;
            vid.muted = true;
            vid.preload = "metadata";
            item.onmouseenter = () => vid.play().catch(() => {});
            item.onmouseleave = () => { vid.pause(); vid.currentTime = 0; };
            item.appendChild(vid);
        } else {
            const label = document.createElement('div');
            label.style.cssText = "color:var(--accent); font-weight:bold; font-size:12px;";
            label.textContent = `🔊 ${basename}`;
            item.appendChild(label);
        }

        const btn = document.createElement('div');
        btn.className = 'insert-btn';
        btn.textContent = 'Insert in Timeline';
        btn.onclick = (e) => {
            e.stopPropagation();
            insertToTimeline(f.path, isAudio);
        };
        item.appendChild(btn);
        galleryContainer.appendChild(item);
    });
}

function insertToTimeline(filePath, isAudio) {
    try {
        const basename = path.basename(filePath);
        log("Importazione: " + basename);
        if (!resolve) throw new Error("DaVinci Resolve API non inizializzata.");
        const project = resolve.GetProjectManager().GetCurrentProject();
        if (!project) throw new Error("Nessun progetto attivo.");
        const mediaPool = project.GetMediaPool();
        const timelineObj = project.GetCurrentTimeline();
        if (!timelineObj) throw new Error("Nessuna timeline attiva.");

        // Import into Media Pool
        const importedItems = mediaPool.ImportMedia([filePath]);
        if (!importedItems || importedItems.length === 0) throw new Error("Impossibile importare il file.");

        // Simple append to timeline (most reliable method)
        const result = mediaPool.AppendToTimeline(importedItems);

        if (result && result.length > 0) {
            log(`✅ ${basename} inserito nella timeline!`);
        } else {
            // Fallback: at least it's in the Media Pool
            log(`⚠️ ${basename} importato nel Media Pool. Trascinalo nella timeline.`);
        }
    } catch (err) {
        log(`ERRORE: ${err.message}`);
    }
}

function updateGallery() {
    if (!wan2gp_dir) return;
    const outputsDir = path.join(wan2gp_dir, "outputs");
    const allFiles = findMediaFiles(outputsDir);

    // Sort newest first
    allFiles.sort((a, b) => b.mtime - a.mtime);
    const recentFiles = allFiles.slice(0, 12);

    // Detect changes (new files OR updated mtime)
    let hasChanges = false;
    if (recentFiles.length !== knownFilesMap.size) {
        hasChanges = true;
    } else {
        for (const f of recentFiles) {
            const known = knownFilesMap.get(f.path);
            if (known === undefined || known !== f.mtime) {
                hasChanges = true;
                break;
            }
        }
    }

    if (hasChanges) {
        knownFilesMap = new Map(recentFiles.map(f => [f.path, f.mtime]));
        renderGallery(recentFiles);
    }
}

// Poll outputs every 2 seconds
setInterval(updateGallery, 2000);
setTimeout(updateGallery, 500);

log("Pronto. Seleziona una clip e clicca 'Estrai Clip'.");
