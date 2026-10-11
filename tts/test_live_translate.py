"""
Test script for Gemini 3.5 Live Translate API (gemini-3.5-live-translate-preview).
Streams real-time speech-to-speech audio translation over WebSockets.

Usage:
  # Translate text (synthesizes speech, translates to Spanish, and plays translated voice):
  python test_live_translate.py -t "Good morning everyone, welcome to our presentation!" --target es --play

  # Translate to Mandarin Chinese:
  python test_live_translate.py -t "Thank you for joining us today." --target zh --play

  # Translate an existing audio file:
  python test_live_translate.py -i output/gtts_basic_en.mp3 --target fr --play
"""

import os
import sys
import wave
import shutil
import asyncio
import subprocess
import argparse
from pathlib import Path
from google import genai
from google.genai import types
from gtts import gTTS

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "gemini-3.5-live-translate-preview"


def find_ffmpeg_tool(name: str):
    cmd = shutil.which(name)
    if cmd:
        return cmd
    local_app_data = os.getenv("LOCALAPPDATA", "")
    if local_app_data:
        candidates = list(Path(local_app_data).glob(f"Microsoft/WinGet/Packages/Gyan.FFmpeg*/**/{name}.exe"))
        if candidates and candidates[0].exists():
            return str(candidates[0])
    return None


def convert_to_16k_pcm(input_audio: Path, output_pcm: Path) -> Path:
    """Converts any audio file to 16kHz mono 16-bit little-endian raw PCM using ffmpeg."""
    ffmpeg_cmd = find_ffmpeg_tool("ffmpeg")
    if not ffmpeg_cmd:
        raise RuntimeError("ffmpeg is required to convert audio to 16kHz PCM.")
    
    cmd = [
        ffmpeg_cmd, "-y",
        "-i", str(input_audio),
        "-ar", "16000",
        "-ac", "1",
        "-f", "s16le",
        str(output_pcm)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_pcm


def save_pcm_to_wav(pcm_bytes: bytes, wav_path: Path, sample_rate: int = 24000):
    wav_path = Path(wav_path)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


def play_audio(audio_path: Path):
    ffplay_cmd = find_ffmpeg_tool("ffplay")
    if ffplay_cmd:
        print(f"[Playing translated audio via ffplay: {audio_path.name}]")
        try:
            subprocess.run([ffplay_cmd, "-nodisp", "-autoexit", "-loglevel", "quiet", str(audio_path)], check=True)
            return
        except Exception as e:
            print(f"[WARN] ffplay error: {e}")
    try:
        subprocess.run(["powershell", "-c", f"Start-Process '{audio_path}'"], check=True)
    except Exception as e:
        print(f"[ERROR] Playback failed: {e}")


async def live_translate_stream(pcm_path: Path, target_lang: str, output_wav: Path):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    client = genai.Client(api_key=api_key)

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        translation_config=types.TranslationConfig(
            target_language_code=target_lang,
            echo_target_language=True
        )
    )

    pcm_bytes = pcm_path.read_bytes()
    chunk_size = 3200  # 100ms at 16kHz 16-bit mono = 1600 samples * 2 bytes
    translated_audio = b""
    input_text_chunks = []
    output_text_chunks = []

    print(f"\n--- Connecting to Gemini 3.5 Live Translate (Target: {target_lang.upper()}) ---")

    async with client.aio.live.connect(model=MODEL, config=config) as session:
        print("[Connected] Streaming audio chunks over WebSockets...")

        # Task to receive translation responses
        async def receive_loop():
            nonlocal translated_audio
            try:
                async for response in session.receive():
                    server_content = response.server_content
                    if server_content:
                        if server_content.input_transcription and server_content.input_transcription.text:
                            txt = server_content.input_transcription.text
                            input_text_chunks.append(txt)
                            print(f"  [Input Audio Transcription]: {txt}")
                        if server_content.output_transcription and server_content.output_transcription.text:
                            txt = server_content.output_transcription.text
                            output_text_chunks.append(txt)
                            print(f"  [Translated Live Transcript]: {txt}")
                        if server_content.model_turn:
                            for part in server_content.model_turn.parts:
                                if hasattr(part, "inline_data") and part.inline_data:
                                    translated_audio += part.inline_data.data
            except asyncio.CancelledError:
                pass
            except Exception as e:
                # Normal close
                pass

        receiver_task = asyncio.create_task(receive_loop())

        # Stream audio chunks into the session
        for i in range(0, len(pcm_bytes), chunk_size):
            chunk = pcm_bytes[i:i + chunk_size]
            await session.send_realtime_input(
                audio=types.Blob(
                    data=chunk,
                    mime_type="audio/pcm;rate=16000"
                )
            )
            await asyncio.sleep(0.08)  # Stream roughly in real-time

        # Allow time for model to finalize translation
        await asyncio.sleep(2.0)
        receiver_task.cancel()

    if translated_audio:
        save_pcm_to_wav(translated_audio, output_wav, sample_rate=24000)
        print(f"\n[OK] Translated speech saved: {output_wav} ({output_wav.stat().st_size} bytes)")
        return {
            "wav_path": output_wav,
            "input_transcript": " ".join(input_text_chunks),
            "output_transcript": " ".join(output_text_chunks)
        }
    else:
        print("\n[WARN] No translated audio was returned.")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Gemini 3.5 Live Translate (Speech-to-Speech) CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python test_live_translate.py -t "Hello! Welcome to our hotel in Tokyo." --target ja -p
  python test_live_translate.py -t "Buenos dias, me gustaria comprar un boleto." --target en -p
  python test_live_translate.py -i speech.mp3 --target zh -p
"""
    )
    parser.add_argument("-t", "--text", help="Text to speak and translate")
    parser.add_argument("-i", "--input-audio", help="Input audio file to translate (WAV, MP3, etc.)")
    parser.add_argument("--target", default="es", help="Target language code (e.g. es, fr, zh, de, ja, it, ru, pl, en). Default: es")
    parser.add_argument("-o", "--output", help="Output translated WAV file path")
    parser.add_argument("-p", "--play", action="store_true", help="Play the translated speech via ffplay")

    args = parser.parse_args()

    if not args.text and not args.input_audio:
        # Default test
        args.text = "Hello! Today we are demonstrating the brand new Gemini 3.5 Live Translate API."

    temp_pcm = OUTPUT_DIR / "temp_input_16k.pcm"
    temp_source_audio = OUTPUT_DIR / "temp_source.mp3"

    if args.input_audio:
        src = Path(args.input_audio)
        if not src.exists():
            print(f"[ERROR] Audio file not found: {args.input_audio}")
            sys.exit(1)
        convert_to_16k_pcm(src, temp_pcm)
    else:
        print(f"Generating source speech for text: \"{args.text}\"")
        tts = gTTS(text=args.text, lang="en")
        tts.save(str(temp_source_audio))
        convert_to_16k_pcm(temp_source_audio, temp_pcm)

    out_wav = Path(args.output) if args.output else (OUTPUT_DIR / f"live_translate_{args.target}.wav")

    result = asyncio.run(live_translate_stream(temp_pcm, args.target, out_wav))

    if result and args.play:
        play_audio(out_wav)


if __name__ == "__main__":
    main()
