"""
Test script for gTTS (Google Text-to-Speech).
Uses Google Translate's free web TTS service.
100% free, requires NO API key and NO credit card.

Usage:
  # Quick text synthesis:
  python test_gtts.py "Hello, this is a custom test message!"
  python test_gtts.py "Listen to this!" --play
  python test_gtts.py -t "Good morning London!" --tld co.uk -o output/uk.mp3 --play
  python test_gtts.py -t "Bonjour le monde!" --lang fr -o output/french.mp3 --play

  # Run all preset test benchmarks:
  python test_gtts.py --all-tests
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from gtts import gTTS

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
    """Plays audio file using ffplay or PowerShell fallback."""
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


def synthesize_custom_text(text: str, lang: str = "en", tld: str = "com", slow: bool = False, output_path: Path = None, play: bool = False):
    if output_path is None:
        output_path = OUTPUT_DIR / "gtts_custom.mp3"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n--- Synthesizing Custom Text with gTTS ---")
    print(f"Text: \"{text}\"")
    print(f"Language: {lang} | Accent/TLD: {tld} | Slow: {slow}")
    
    tts = gTTS(text=text, lang=lang, tld=tld, slow=slow)
    tts.save(str(output_path))
    print(f"[OK] Saved audio to: {output_path} ({output_path.stat().st_size} bytes)")

    if play:
        play_audio(output_path)

    return output_path


def test_basic_tts(play: bool = False):
    print("\n--- Test 1: Basic English TTS ---")
    text = "Hello! This is a test of Google Text-to-Speech using the free gTTS library."
    output_path = OUTPUT_DIR / "gtts_basic_en.mp3"
    tts = gTTS(text=text, lang="en")
    tts.save(str(output_path))
    print(f"[OK] Generated: {output_path.name} ({output_path.stat().st_size} bytes)")
    if play:
        play_audio(output_path)


def test_accents():
    print("\n--- Test 2: English Accents via TLD ---")
    text = "Good day! Notice how the accent changes depending on the regional domain."
    accents = [
        ("com", "gtts_accent_us.mp3", "US English"),
        ("co.uk", "gtts_accent_uk.mp3", "British English"),
        ("com.au", "gtts_accent_au.mp3", "Australian English"),
        ("co.in", "gtts_accent_in.mp3", "Indian English"),
    ]
    for tld, filename, label in accents:
        output_path = OUTPUT_DIR / filename
        tts = gTTS(text=text, lang="en", tld=tld)
        tts.save(str(output_path))
        print(f"[OK] {label} ({tld}): {output_path.name} ({output_path.stat().st_size} bytes)")


def test_slow_speed():
    print("\n--- Test 3: Speed Control (Slow Mode) ---")
    text = "This sentence is spoken slowly for language learning or accessibility."
    output_path = OUTPUT_DIR / "gtts_slow.mp3"
    tts = gTTS(text=text, lang="en", slow=True)
    tts.save(str(output_path))
    print(f"[OK] Generated: {output_path.name} ({output_path.stat().st_size} bytes)")


def test_multilingual():
    print("\n--- Test 4: Multilingual Support ---")
    samples = [
        ("es", "Hola, bienvenido al sistema de texto a voz de Google.", "gtts_es.mp3", "Spanish"),
        ("fr", "Bonjour! Ceci est un test de synthèse vocale en français.", "gtts_fr.mp3", "French"),
        ("zh-CN", "你好！这是使用谷歌文字转语音的测试。", "gtts_zh.mp3", "Mandarin"),
        ("ja", "こんにちは！这是Google音声合成的测试。", "gtts_ja.mp3", "Japanese"),
    ]
    for lang, text, filename, label in samples:
        output_path = OUTPUT_DIR / filename
        tts = gTTS(text=text, lang=lang)
        tts.save(str(output_path))
        print(f"[OK] {label} ({lang}): {output_path.name} ({output_path.stat().st_size} bytes)")


def main():
    parser = argparse.ArgumentParser(
        description="Google Text-to-Speech (gTTS) testing utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python test_gtts.py "Hello world!" --play
  python test_gtts.py -t "Welcome to London!" --tld co.uk -p
  python test_gtts.py -t "Hola mundo" --lang es -o output/spanish.mp3 -p
  python test_gtts.py -f input.txt -o output/from_file.mp3
  python test_gtts.py --all-tests
"""
    )
    parser.add_argument("pos_text", nargs="?", default=None, help="Input text to convert to speech")
    parser.add_argument("-t", "--text", dest="opt_text", help="Input text to convert to speech (option flag)")
    parser.add_argument("-f", "--file", help="Path to a text file containing the content to convert")
    parser.add_argument("-l", "--lang", default="en", help="Language code (e.g. en, es, fr, zh-CN, ja, de). Default: en")
    parser.add_argument("--tld", default="com", help="Top-level domain for regional accent (e.g. com, co.uk, com.au, co.in, ca). Default: com")
    parser.add_argument("--slow", action="store_true", help="Read text at a slower pace")
    parser.add_argument("-o", "--output", help="Output MP3 file path (default: output/gtts_custom.mp3)")
    parser.add_argument("-p", "--play", action="store_true", help="Automatically play generated audio in CLI via ffplay")
    parser.add_argument("--all-tests", action="store_true", help="Run the full preset test suite")

    args = parser.parse_args()

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

    print("=" * 60)
    print("Google Text-to-Speech (gTTS - 100% Free, No Credit Card)")
    print("=" * 60)

    if input_text:
        out = Path(args.output) if args.output else None
        synthesize_custom_text(
            text=input_text,
            lang=args.lang,
            tld=args.tld,
            slow=args.slow,
            output_path=out,
            play=args.play
        )
    else:
        test_basic_tts(play=args.play)
        test_accents()
        test_slow_speed()
        test_multilingual()
        print("\n[SUCCESS] All gTTS tests completed successfully! Check the 'output' folder.")


if __name__ == "__main__":
    main()
