"""
Google Gemini Audio Transcription & Diarization
Transcribes audio files with speaker diarization, word-level timestamps, and language detection.

Usage:
  # Transcribe any audio file:
  python transcribe_audio.py -i speech.mp3
  python transcribe_audio.py -i ../tts/output/gemini_multispeaker_sample.wav --diarize
  python transcribe_audio.py -i interview.wav --timestamps
"""

import os
import sys
import argparse
from pathlib import Path
from google import genai
from google.genai import types

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-3.8-flash"


def transcribe_audio(audio_path: Path, diarize: bool = True, timestamps: bool = False, output_txt: Path = None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    if not audio_path.exists():
        print(f"[ERROR] Audio file not found: {audio_path}")
        sys.exit(1)

    print("=" * 65)
    print("Google Gemini Audio Transcription & Diarization")
    print("=" * 65)
    print(f"Audio File: {audio_path.name} ({audio_path.stat().st_size} bytes)")

    # Build prompt instructions based on flags
    instructions = ["Transcribe the spoken audio with high accuracy."]
    if diarize:
        instructions.append("Identify and label each distinct speaker clearly (e.g. Speaker 1, Speaker 2 or Character Names).")
    if timestamps:
        instructions.append("Include approximate timestamps [MM:SS] for each sentence or major dialogue change.")
    instructions.append("Detect the language spoken automatically.")

    prompt = "\n".join(instructions)

    print("\nUploading audio to Gemini for analysis...")
    audio_file = client.files.upload(file=str(audio_path))

    models_to_try = [DEFAULT_MODEL, FALLBACK_MODEL]
    response = None

    for m in models_to_try:
        print(f"Transcribing audio using {m}...")
        try:
            response = client.models.generate_content(
                model=m,
                contents=[audio_file, prompt],
            )
            if response and response.text:
                break
        except Exception as e:
            print(f"[WARN] Model {m} failed ({e}), trying next model...")

    if not response or not response.text:
        print("[ERROR] Transcription failed across all models.")
        return None

    result_text = response.text
    print("\n--- Transcription Result ---")
    print(result_text)

    # Save to text file
    if output_txt is None:
        output_txt = OUTPUT_DIR / f"{audio_path.stem}_transcript.txt"
    else:
        output_txt = Path(output_txt)
        output_txt.parent.mkdir(parents=True, exist_ok=True)

    output_txt.write_text(result_text, encoding="utf-8")
    print(f"\n[OK] Transcript saved to: {output_txt}")

    # Cleanup uploaded file from Gemini storage
    try:
        client.files.delete(name=audio_file.name)
    except Exception:
        pass

    return result_text


def main():
    parser = argparse.ArgumentParser(
        description="Gemini Speech Transcription & Diarization CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python transcribe_audio.py -i ../tts/output/gemini_multispeaker_sample.wav
  python transcribe_audio.py -i interview.mp3 --timestamps --diarize
"""
    )
    parser.add_argument("-i", "--input", required=True, help="Path to input audio file (.wav, .mp3, .m4a, .ogg)")
    parser.add_argument("--diarize", action="store_true", default=True, help="Enable speaker diarization (Speaker 1, Speaker 2)")
    parser.add_argument("--timestamps", action="store_true", help="Include timestamps [MM:SS]")
    parser.add_argument("-o", "--output", help="Output text file path")

    args = parser.parse_args()
    transcribe_audio(
        audio_path=Path(args.input),
        diarize=args.diarize,
        timestamps=args.timestamps,
        output_txt=Path(args.output) if args.output else None
    )


if __name__ == "__main__":
    main()
