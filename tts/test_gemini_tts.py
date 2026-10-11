"""
Test script for Gemini TTS (Text-to-Speech) using Google AI Studio API.
100% Free Tier available without entering a credit card.

Usage:
  # Quick text synthesis with automatic playback:
  python test_gemini_tts.py "Hello from Gemini voice synthesis!" --play
  python test_gemini_tts.py -t "This is Kore speaking." -v Kore -p
  python test_gemini_tts.py -t "Attention please!" -v Zephyr --style "Formal and authoritative" -p
  python test_gemini_tts.py -f story.txt -v Charon -o output/story.wav -p

  # Run preset test benchmarks:
  python test_gemini_tts.py --all-tests
"""

import os
import sys
import wave
import shutil
import subprocess
import argparse
from pathlib import Path
from google import genai
from google.genai import types

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Recommended TTS model
TTS_MODEL = "gemini-3.1-flash-tts-preview"


def find_ffplay():
    """Finds ffplay on PATH or directly in WinGet install directory."""
    cmd = shutil.which("ffplay")
    if cmd:
        return cmd
    local_app_data = os.getenv("LOCALAPPDATA", "")
    if local_app_data:
        candidates = list(Path(local_app_data).glob("Microsoft/WinGet/Packages/Gyan.FFmpeg*/**/ffplay.exe"))
        if candidates and candidates[0].exists():
            return str(candidates[0])
    return None


def play_audio(audio_path: Path):
    """Plays audio file using ffplay or system fallback."""
    ffplay_cmd = find_ffplay()
    if ffplay_cmd:
        print(f"[Playing via ffplay: {audio_path.name}]")
        try:
            subprocess.run([ffplay_cmd, "-nodisp", "-autoexit", "-loglevel", "quiet", str(audio_path)], check=True)
            return
        except Exception as e:
            print(f"[WARN] ffplay playback error: {e}")

    print(f"[Opening via system player: {audio_path.name}]")
    try:
        subprocess.run(["powershell", "-c", f"Start-Process '{audio_path}'"], check=True)
    except Exception as e:
        print(f"[ERROR] Playback failed: {e}")


def save_pcm_to_wav(pcm_bytes: bytes, wav_path: Path, sample_rate: int = 24000, channels: int = 1, sampwidth: int = 2):
    """Saves raw 16-bit linear PCM bytes to a standard WAV file."""
    wav_path = Path(wav_path)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)  # 2 bytes = 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


def synthesize_custom_text(client: genai.Client, model: str, text: str, voice: str = "Puck", style: str = None, output_path: Path = None, play: bool = False):
    if output_path is None:
        output_path = OUTPUT_DIR / f"gemini_{voice.lower()}_custom.wav"
    else:
        output_path = Path(output_path)

    if style:
        prompt = f"""### DIRECTOR'S NOTES
Style: {style}
Transcript:
{text}"""
    else:
        prompt = text

    print(f"\n--- Synthesizing Custom Text with Gemini TTS ---")
    print(f"Model: {model} | Voice: {voice}")
    if style:
        print(f"Style Direction: {style}")
    print(f"Input Text: \"{text}\"")

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                ),
            ),
        )

        audio_bytes = b""
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                audio_bytes += part.inline_data.data

        if audio_bytes:
            save_pcm_to_wav(audio_bytes, output_path)
            print(f"[OK] Saved audio to: {output_path} ({output_path.stat().st_size} bytes)")
            if play:
                play_audio(output_path)
            return output_path
        else:
            print("[WARN] No audio bytes returned in response parts.")
            return None
    except Exception as e:
        print(f"[ERROR] Gemini TTS synthesis failed: {e}")
        return None


def run_single_speaker_test(client: genai.Client, model: str, voice: str = "Puck", play: bool = False):
    print(f"\n--- Preset Test 1: Single Speaker TTS (Voice: {voice}) ---")
    text = "Hello! I am Google Gemini, speaking with native voice generation on the free tier."
    output_path = OUTPUT_DIR / f"gemini_{voice.lower()}_sample.wav"

    try:
        response = client.models.generate_content(
            model=model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                ),
            ),
        )

        audio_bytes = b""
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                audio_bytes += part.inline_data.data

        if audio_bytes:
            save_pcm_to_wav(audio_bytes, output_path)
            print(f"[OK] Generated: {output_path.name} ({output_path.stat().st_size} bytes)")
            if play:
                play_audio(output_path)
    except Exception as e:
        print(f"[ERROR] Single speaker test failed: {e}")


def run_emotional_style_test(client: genai.Client, model: str, play: bool = False):
    print("\n--- Preset Test 2: Stylistic & Emotional Direction ---")
    prompt = """### DIRECTOR'S NOTES
Style: Energetic, enthusiastic and cheerful.
Transcript:
Welcome everyone! Today we are exploring the future of artificial intelligence voice synthesis!"""
    output_path = OUTPUT_DIR / "gemini_energetic_sample.wav"

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Zephyr"
                        )
                    )
                ),
            ),
        )

        audio_bytes = b""
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                audio_bytes += part.inline_data.data

        if audio_bytes:
            save_pcm_to_wav(audio_bytes, output_path)
            print(f"[OK] Generated: {output_path.name} ({output_path.stat().st_size} bytes)")
            if play:
                play_audio(output_path)
    except Exception as e:
        print(f"[ERROR] Emotional style test failed: {e}")


def run_multi_speaker_test(client: genai.Client, model: str, play: bool = False):
    print("\n--- Preset Test 3: Multi-Speaker Conversation (Dr. Anya & Liam) ---")
    dialogue = """Dr. Anya: Welcome back! Have you seen the latest speech synthesis benchmarks?
Liam: Yes! It's incredible how natural and responsive multi-speaker conversations sound now."""
    output_path = OUTPUT_DIR / "gemini_multispeaker_sample.wav"

    try:
        response = client.models.generate_content(
            model=model,
            contents=dialogue,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker="Dr. Anya",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name="Kore"
                                    )
                                ),
                            ),
                            types.SpeakerVoiceConfig(
                                speaker="Liam",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name="Puck"
                                    )
                                ),
                            ),
                        ]
                    )
                ),
            ),
        )

        audio_bytes = b""
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                audio_bytes += part.inline_data.data

        if audio_bytes:
            save_pcm_to_wav(audio_bytes, output_path)
            print(f"[OK] Generated: {output_path.name} ({output_path.stat().st_size} bytes)")
            if play:
                play_audio(output_path)
    except Exception as e:
        print(f"[ERROR] Multi-speaker test failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Test Google Gemini Text-to-Speech API (Free Tier)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python test_gemini_tts.py "Hello, this is custom text!" --play
  python test_gemini_tts.py -t "This is Kore speaking." -v Kore -p
  python test_gemini_tts.py -t "Good morning everyone!" -v Zephyr --style "Enthusiastic and upbeat" -p
  python test_gemini_tts.py -f input.txt -v Charon -o output/my_audio.wav -p
  python test_gemini_tts.py --all-tests
"""
    )
    parser.add_argument("pos_text", nargs="?", default=None, help="Input text to convert to speech")
    parser.add_argument("-t", "--text", dest="opt_text", help="Input text to convert to speech (option flag)")
    parser.add_argument("-f", "--file", help="Path to a text file containing the content to convert")
    parser.add_argument("-v", "--voice", default="Puck", help="Prebuilt voice name (e.g. Puck, Kore, Zephyr, Charon, Fenrir, Aoede, Achernar, Despina). Default: Puck")
    parser.add_argument("--style", help="Stylistic or emotional direction (e.g. 'Energetic', 'Whisper', 'Calm and soothing', 'Formal')")
    parser.add_argument("-o", "--output", help="Output WAV file path (default: output/gemini_<voice>_custom.wav)")
    parser.add_argument("-p", "--play", action="store_true", help="Automatically play generated audio in CLI via ffplay")
    parser.add_argument("--key", default=os.getenv("GEMINI_API_KEY"), help="Google AI Studio API Key (defaults to GEMINI_API_KEY env var)")
    parser.add_argument("--model", default=TTS_MODEL, help=f"Model name (default: {TTS_MODEL})")
    parser.add_argument("--all-tests", action="store_true", help="Run the full preset benchmark test suite")

    args = parser.parse_args()

    api_key = args.key

    print("=" * 65)
    print("Google Gemini Text-to-Speech (AI Studio Free Tier)")
    print("=" * 65)

    if not api_key:
        print("\n[!] GEMINI_API_KEY is not set.")
        print("-" * 65)
        print("To test Gemini TTS for free (no credit card required):")
        print("1. Go to: https://aistudio.google.com/app/apikey")
        print("2. Sign in with any Google account (Gmail / Google Workspace).")
        print("3. Click '+ Create API key'.")
        print("4. Set your key in PowerShell:")
        print("     $env:GEMINI_API_KEY = \"AIzaSy...\"")
        print("   Or pass it directly:")
        print("     python test_gemini_tts.py --key \"AIzaSy...\"")
        print("-" * 65)
        return

    client = genai.Client(api_key=api_key)

    input_text = None
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[ERROR] File not found: {args.file}")
            sys.exit(1)
        input_text = file_path.read_text(encoding="utf-8")
    elif args.opt_text:
        input_text = args.opt_text
    elif args.pos_text:
        input_text = args.pos_text

    if input_text:
        out = Path(args.output) if args.output else None
        synthesize_custom_text(
            client=client,
            model=args.model,
            text=input_text,
            voice=args.voice,
            style=args.style,
            output_path=out,
            play=args.play
        )
    else:
        print(f"Using model: {args.model}")
        run_single_speaker_test(client, args.model, voice=args.voice, play=args.play)
        run_emotional_style_test(client, args.model, play=args.play)
        run_multi_speaker_test(client, args.model, play=args.play)
        print("\n[SUCCESS] Gemini TTS testing complete! Check the 'output' folder.")


if __name__ == "__main__":
    main()
