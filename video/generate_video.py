"""
Google Veo Video Generation (veo-3.1-generate-preview)
Generates high-definition cinematic videos with audio from text prompts or starting images.

Usage:
  # Text to video:
  python generate_video.py -p "A cinematic drone shot flying over ancient stone ruins at sunset with ocean mist"
  python generate_video.py -p "A cute red panda wearing goggles typing rapidly on a miniature laptop" -d 5

  # Image to video:
  python generate_video.py --image photo.png -p "Gentle wind rustling the trees and camera panning slowly"
"""

import os
import sys
import time
import argparse
import subprocess
import shutil
from pathlib import Path
from google import genai
from google.genai import types

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "veo-3.1-generate-preview"


def find_ffplay():
    cmd = shutil.which("ffplay")
    if cmd:
        return cmd
    local_app_data = os.getenv("LOCALAPPDATA", "")
    if local_app_data:
        candidates = list(Path(local_app_data).glob("Microsoft/WinGet/Packages/Gyan.FFmpeg*/**/ffplay.exe"))
        if candidates and candidates[0].exists():
            return str(candidates[0])
    return None


def generate_video(prompt: str, image_path: Path = None, duration: int = 5, output_path: Path = None, play: bool = False):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    if output_path is None:
        safe_name = f"veo_{int(time.time())}.mp4"
        output_path = OUTPUT_DIR / safe_name
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("Google Veo Video Generation (veo-3.1-generate-preview)")
    print("=" * 65)
    print(f"Prompt: \"{prompt}\"")
    print(f"Duration: {duration}s")
    if image_path:
        print(f"Starting Image: {image_path}")

    # Build source
    source_args = {"prompt": prompt}
    if image_path:
        image = types.Image.from_file(location=str(image_path))
        source_args["image"] = image

    source = types.GenerateVideosSource(**source_args)
    config = types.GenerateVideosConfig(
        number_of_videos=1,
        duration_seconds=duration,
        enhance_prompt=True,
    )

    print("\n[1/3] Submitting video generation job to Google Veo...")
    operation = client.models.generate_videos(
        model=MODEL,
        source=source,
        config=config,
    )
    print(f"Operation started: {operation.name}")

    print("\n[2/3] Rendering video (polling operation)...")
    start_time = time.time()
    while not operation.done:
        elapsed = int(time.time() - start_time)
        print(f"  Rendering... ({elapsed}s elapsed)")
        time.sleep(15)
        operation = client.operations.get(operation)

    if operation.error:
        print(f"[ERROR] Video generation failed: {operation.error}")
        return None

    print("\n[3/3] Video rendering complete! Downloading...")
    generated_video = operation.response.generated_videos[0].video
    
    # Save video bytes
    if hasattr(generated_video, "video_bytes") and generated_video.video_bytes:
        output_path.write_bytes(generated_video.video_bytes)
    elif hasattr(generated_video, "save"):
        generated_video.save(str(output_path))
    else:
        # Download via URI or bytes
        data = client.files.download(file=generated_video.uri)
        output_path.write_bytes(data)

    print(f"[OK] Video saved successfully to: {output_path} ({output_path.stat().st_size} bytes)")

    if play:
        ffplay_cmd = find_ffplay()
        if ffplay_cmd:
            print(f"[Playing video via ffplay: {output_path.name}]")
            subprocess.run([ffplay_cmd, "-autoexit", str(output_path)])
        else:
            subprocess.run(["powershell", "-c", f"Start-Process '{output_path}'"])

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Google Veo Cinematic Video Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python generate_video.py -p "A cinematic drone shot flying through a glowing bamboo forest in Kyoto at twilight"
  python generate_video.py -p "Futuristic hovercar racing through rainy neon city streets" -d 5 --play
  python generate_video.py --image scenery.jpg -p "Camera slowly zooming in with sunlight filtering through clouds"
"""
    )
    parser.add_argument("-p", "--prompt", default="A neon hologram of a cybernetic cat driving a retro car at top speed along a futuristic highway", help="Text description of the video")
    parser.add_argument("--image", help="Optional starting image for image-to-video")
    parser.add_argument("-d", "--duration", type=int, default=5, choices=[5, 8, 10], help="Video duration in seconds (default: 5)")
    parser.add_argument("-o", "--output", help="Output MP4 file path")
    parser.add_argument("--play", action="store_true", help="Play the video in ffplay once rendered")

    args = parser.parse_args()

    img_path = Path(args.image) if args.image else None
    out_path = Path(args.output) if args.output else None

    generate_video(prompt=args.prompt, image_path=img_path, duration=args.duration, output_path=out_path, play=args.play)


if __name__ == "__main__":
    main()
