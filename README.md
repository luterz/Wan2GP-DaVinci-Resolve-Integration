
# Wan2GP DaVinci Resolve Integration

<img width="1006" height="830" alt="interface" src="https://github.com/user-attachments/assets/55661221-b8b3-4316-86fd-cc42c2844595" />
https://github.com/luterz/Wan2GP-DaVinci-Resolve-Integration/blob/main/interface.png

This project integrates Wan2GP (WanGP AI) into DaVinci Resolve, enabling you to use advanced AI models (like Wan2.2, LTX-Video, and EditAnything) to generate, inpaint, and modify clips directly from your DaVinci Resolve timeline.

## Features
- **Direct Timeline Integration**: Send clips from your timeline straight to the WanGP AI engine without manual exports.
- **Inpainting & Object Modification**: Draw a mask directly in the DaVinci Resolve plugin UI, type what you want to generate, and let the AI seamlessly replace or add objects using an FFmpeg perfect-compositing pipeline.
- **Audio Exclusion**: Option to strip audio from the generation to ensure your timeline audio stays intact.
- **Dynamic Resolution Matching**: Automatically detects your DaVinci Resolve timeline resolution to ensure masks and generated videos match perfectly.

## Installation
1. Ensure you have [WanGP](https://github.com/deepbeepmeep/Wan2GP) installed and working on your system.
2. Copy the `DaVinci_Plugin/com.antigravity.wangp` folder into your DaVinci Resolve Workflow Integration Plugins directory:
   - **Windows**: `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Workflow Integration Plugins\`
   - **Mac**: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins/`
3. Run the `start_wangp_services.bat` script to start the bridge server and orchestrator.

## Usage
1. Open DaVinci Resolve, go to `Workspace -> Workflow Integrations -> WanGP AI`.
2. Select a clip on your timeline.
3. Click `Extract Timeline Frame & Annotate`.
4. Draw a mask over the object you want to modify.
5. Type your prompt (e.g., "rayban sunglasses").
6. Click `Send Job to AI`.
7. Once finished, the new clip will be imported into your media pool and placed on top of your original clip in the timeline!


##Work

Generation Audio
Use sage attention
Triton
Generation Clip

## not work

Mask isn't apply to generation

##not tested well but semmes to work ;)

deepy integration 


## Advanced Tips
- **EditAnything Models**: If you are using an `EditAnything Ref V2V` model, keep in mind they are fine-tuned for high-quality edits. If you only want to use a text prompt without an image reference, standard models like `LTX-2 Distilled` or `Wan2.2 Animate` are highly recommended for Text-based inpainting.
- **Perfect Background Preservation**: The plugin uses an `alphamerge` FFmpeg process behind the scenes, meaning the pixels outside your mask will be **100% mathematically identical** to your original clip.

## Requirements
- DaVinci Resolve Studio 18+
- Python 3.10+
- FFmpeg installed and in your system PATH.
