import sys
import os
import argparse
import json
import torch

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, required=True, help="Original prompt")
    parser.add_argument("--mode", type=str, default="video", choices=["video", "image", "audio"], help="Generation mode")
    parser.add_argument("--wan2gp_dir", type=str, required=True, help="Path to Wan2GPmain")
    parser.add_argument("--media_path", type=str, default=None, help="Path to reference media")
    args = parser.parse_args()

    # Implement Option A: If an image/video is provided (I2V), bypass Deepy 
    # to avoid hallucinatory text prompts clashing with the input image.
    if args.media_path and os.path.exists(args.media_path):
        print("---DEEPY_OUTPUT_START---")
        print(json.dumps({"prompts": [args.prompt]}))
        print("---DEEPY_OUTPUT_END---")
        return

    sys.path.insert(0, args.wan2gp_dir)

    try:
        from shared.prompt_enhancer.loader import load_prompt_enhancer_runtime
        from shared.prompt_enhancer.prompt_enhance_utils import generate_cinematic_prompt
        from shared.utils.download import process_files_def as shared_process_files_def
        from shared.prompt_enhancer.qwen35_vl import get_qwen35_prompt_enhancer_variant

        # Assuming enhancer_enabled = 3 (Qwen 3.5 4B)
        runtime = load_prompt_enhancer_runtime(shared_process_files_def, enhancer_enabled=3, lm_decoder_engine="", qwen_backend="quanto_int8")
        
        # Move text model to GPU manually. We bypass the vision models entirely.
        if hasattr(runtime, 'llm_model') and runtime.llm_model is not None:
            runtime.llm_model.cuda()
        
        is_video = args.mode == "video"
        is_text = args.mode == "audio"
        
        with torch.inference_mode():
            enhanced_prompts = generate_cinematic_prompt(
                image_caption_model=runtime.image_caption_model,
                llm_model=runtime.llm_model,
                prompt=args.prompt,
                negative_prompt="",
                images=None, # Force T2V
                is_video=is_video,
                is_text=is_text,
                qwen_variant=get_qwen35_prompt_enhancer_variant(3),
            )
            
        print("---DEEPY_OUTPUT_START---")
        print(json.dumps({"prompts": enhanced_prompts}))
        print("---DEEPY_OUTPUT_END---")
        
    except Exception as e:
        print(f"Error running deepy: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
