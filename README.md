# Wan2GP DaVinci Resolve Integration

This project integrates **Wan2GP (WanGP AI)** directly into **DaVinci Resolve**, providing the full native AI generator interface and drastically simplifying your workflow (clip extraction, inpainting, re-insertion) without ever having to leave your editing software.

## Key Features

- **Native Integrated UI**: Access all Wan2GP features, models (LTX-Video, VACE, Wan2, Flux 2), and tools (such as Matanyone for masking) directly from the DaVinci Workflow Integrations panel.
- **Smart Extraction**: Select a clip in your timeline and click a button. The plugin automatically exports the clip at the correct timeline resolution and places it straight into the Wan2GP `inputs/` folder.
- **Integrated File Gallery**: Instantly find your extracted clip inside the Wan2GP File Gallery, ready to be dragged and dropped into the "Control Video" or "Image Refs" sections.
- **Gallery Watcher & Auto-Insert**: The plugin constantly monitors the output folder. As soon as the AI finishes generating the video (or audio), it appears in the plugin's bottom gallery. Click "Insert in Timeline" to automatically import the file into the Media Pool and drop it onto the timeline.
- **Audio and Video Support**: Works seamlessly for video generation (inserted onto a higher video track) as well as TTS/Audio models (inserted onto an audio track).
- **Safe Process Management**: Automatically starts and safely restarts the Wan2GP backend interface without freezing your system.

---

## 🛠 Installation (Windows)

Installation is fully automated via a batch script.

1. Ensure you have **Wan2GP** already installed and working on your system.
2. Download or clone this repository to a folder of your choice (e.g., `F:\projects\wan2gp_Davinci`).
3. Double-click on **`install_windows.bat`**.
4. When prompted, **paste the full path to your Wan2GP folder** (for example: `F:\Wan2GPmain`). Don't worry about quotes, the script handles them.
5. The script will perform the following actions:
   - Save the paths to the `plugin_config.json` file.
   - Automatically copy the plugin files into the correct DaVinci Resolve directory (`C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Workflow Integration Plugins\com.antigravity.wangp`).
   - Create a Python virtual environment (if needed for future services).
   - Create a Desktop shortcut named **"Start WanGP Services"**.

### Prerequisites
- **DaVinci Resolve Studio 18+** (Python/API support is required)
- **Windows 10/11**
- A working **Wan2GP** installation

---

## 🚀 How to use the Plugin inside DaVinci Resolve

### 1. Initial Startup
Before opening the panel in DaVinci, double-click the **"Start WanGP Services"** shortcut on your Desktop. This will start the Wan2GP backend in the background.

### 2. Opening the Panel
In DaVinci Resolve, navigate to the top menu:
`Workspace -> Workflow Integrations -> Wan2GP Native PRO`

### 3. Inpainting / Editing Workflow
1. **Extract the Clip**:
   - Go to the **Edit** page.
   - Select a video clip in your timeline.
   - In the plugin panel, click the **"Estrai Clip"** (Extract Clip) button.
   - *The plugin will export the clip and automatically save it into the Wan2GP `inputs/` folder. (For convenience, the file path is also copied to your clipboard).*

2. **Prepare the Job (in Wan2GP)**:
   - Within the Wan2GP interface (inside the plugin), click the **folder icon** at the bottom (File Gallery).
   - Choose the **"inputs"** tab. You will find your newly extracted clip there.
   - Drag the clip into the **"Control Video"** section (or wherever required by your chosen model).
   - If you need to perform Inpainting, use the built-in **Mask Generator (Matanyone)** button in Wan2GP to easily trace the contours of the object/subject you want to modify.

3. **Generate**:
   - Write your prompt, adjust parameters (Model, Steps, LoRA, etc.), and hit **Generate**.

4. **Re-insertion into Timeline**:
   - Keep an eye on the bottom bar of the plugin panel: the **Gallery Watcher** updates in real-time.
   - As soon as the generation is complete, the new video will appear in the bar.
   - Click **"Insert in Timeline"** under the generated video.
   - The plugin will import the file into the Media Pool and automatically place it on an upper video track (V2/V3), perfectly synchronized with the original starting point!

### 4. Troubleshooting
- **The interface says "Wan2GP Offline"**: Make sure you have started the "Start WanGP Services" shortcut from the desktop. If the terminal closed by mistake, you can click **"Restart API"** directly from the plugin to safely restart it.
- **Extract button disabled or error**: Verify that you have actually selected a clip in the timeline (it must have the red outline).
- **Display issues (White Iframe)**: Click the **"Apri nel Browser"** (Open in Browser) button to use the interface comfortably in your default web browser, while keeping the plugin toolbar open for Extraction and Insertion.
