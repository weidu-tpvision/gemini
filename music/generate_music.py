"""
Google Lyria Music Generation (lyria-3.5-clip-preview & lyria-3.5-pro-preview)
Generates 44.1 kHz high-fidelity stereo music tracks from text prompts and arrangement tags.

Usage:
  # Generate a 30-second acoustic guitar track:
  python generate_music.py -p "A soothing acoustic fingerstyle guitar piece in open D tuning with warm ambient reverb"

  # Generate electronic / synthwave track:
  python generate_music.py -p "Upbeat 128 BPM retro 80s synthwave with punchy drums, arpeggiated bassline, and warm analog synthesizers" --play

  # Generate cinematic orchestral soundtrack:
  python generate_music.py -p "Epic fantasy cinematic orchestral piece starting with gentle flute and building into massive brass and battle drums" -o output/epic.mp3 -p
"""

import os
import sys
import time
import base64
import argparse
import subprocess
import shutil
from pathlib import Path
from google import genai

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_CLIP = "lyria-3.5-clip-preview"
MODEL_PRO = "lyria-3.5-pro-preview"


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


def generate_music(prompt: str, full_song: bool = False, output_path: Path = None, play: bool = False):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    model = MODEL_PRO if full_song else MODEL_CLIP

    if output_path is None:
        safe_name = f"lyria_{int(time.time())}.mp3"
        output_path = OUTPUT_DIR / safe_name
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("Google Lyria Music Generation")
    print("=" * 65)
    print(f"Model: {model}")
    print(f"Prompt: \"{prompt}\"")
    print(f"Output File: {output_path}")

    print("\nComposing and rendering high-fidelity 44.1 kHz stereo audio...")
    try:
        interaction = client.interactions.create(
            model=model,
            input=prompt,
        )

        audio_block = interaction.output_audio
        if not audio_block:
            print("[ERROR] No audio block returned by Lyria model.")
            return None

        # Decode MP3 data
        audio_bytes = base64.b64decode(audio_block.data)
        output_path.write_bytes(audio_bytes)

        print(f"[OK] Music saved successfully to: {output_path} ({output_path.stat().st_size} bytes)")

        # Print generated song lyrics / arrangement if provided
        lyrics = interaction.output_text
        if lyrics:
            print(f"\n[Generated Structure & Lyrics]:\n{lyrics}")

        if play:
            ffplay_cmd = find_ffplay()
            if ffplay_cmd:
                print(f"\n[Playing music via ffplay: {output_path.name}]")
                subprocess.run([ffplay_cmd, "-nodisp", "-autoexit", str(output_path)])
            else:
                subprocess.run(["powershell", "-c", f"Start-Process '{output_path}'"])

        return output_path

    except Exception as e:
        print(f"[ERROR] Music generation failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Google Lyria Music Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python generate_music.py -p "Lo-fi hip hop beat with smooth rhodes piano, vinyl crackle, and chill bass" --play
  python generate_music.py -p "Energetic cyberpunk dark synthwave with heavy bass drop" -p
  python generate_music.py -p "Acoustic folk song with gentle acoustic guitar and melodic whistling" -o output/folk.mp3
"""
    )
    parser.add_argument("-p", "--prompt", default="A relaxing lo-fi hip hop beat with smooth Rhodes piano, mellow guitar chords, and warm vinyl crackle", help="Description of the music, instruments, genre, and mood")
    parser.add_argument("--full", action="store_true", help="Generate a full-length multi-minute song using lyria-3.5-pro-preview")
    parser.add_argument("-o", "--output", help="Output MP3 file path")
    parser.add_argument("--play", action="store_true", help="Play the track in ffplay after generation")

    args = parser.parse_args()
    out = Path(args.output) if args.output else None
    generate_music(prompt=args.prompt, full_song=args.full, output_path=out, play=args.play)


if __name__ == "__main__":
    main()
