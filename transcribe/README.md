# Google Gemini Audio Transcription & Diarization

Transcribe audio files into formatted text with **speaker identification (diarization)**, **millisecond timestamps**, and **automatic language detection**.

---

## Features
- **Speaker Diarization**: Detects and separates Speaker 1, Speaker 2, etc.
- **Accurate Timestamps**: Formats dialogue with `[MM:SS]` or millisecond intervals.
- **Multi-Format**: Supports `.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac`.

---

## Usage

```bash
# Basic Transcription with Speaker Diarization:
python transcribe_audio.py -i ../tts/output/gemini_multispeaker_sample.wav

# With Precise Timestamps:
python transcribe_audio.py -i ../tts/output/gemini_multispeaker_sample.wav --timestamps

# Custom output file:
python transcribe_audio.py -i meeting.mp3 --timestamps -o output/meeting_notes.txt
```
