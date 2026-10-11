# Google Gemini & Multimodal AI Studio Hub

A comprehensive, modular collection of interactive applications and CLI tools leveraging **Google Gemini & AI Studio APIs** that are **100% free and require NO credit card**.

---

## 📁 Project Architecture

```text
gemini/ (or google_tts/)
├── tts/                  # Text-to-Speech & Real-Time Voice Translation
│   ├── app.py                   # Multi-Engine Web Studio (Port 8080)
│   ├── live_translate_app.py    # Real-Time Microphone Speech-to-Speech Interpreter (Port 8081)
│   ├── app_gui.py               # Native Windows Desktop GUI (Tkinter)
│   ├── test_gemini_tts.py       # Gemini 3.1 Flash TTS CLI (30 expressive voices)
│   ├── test_live_translate.py   # Gemini 3.5 Live Voice Translate CLI
│   ├── test_gtts.py             # Google Translate TTS CLI (100+ languages & accents)
│   ├── test_browser_tts.html    # Chrome Web Speech API in-browser tester
│   ├── output/                  # Generated audio files (.wav & .mp3)
│   └── README.md                # Dedicated TTS documentation
│
├── video/                # Video Generation (Google Veo)
│   ├── generate_video.py        # Text-to-Video & Image-to-Video CLI (Veo 3.1)
│   ├── output/                  # Generated video files (.mp4)
│   └── README.md                # Video generation documentation
│
├── music/                # Music & Audio Generation (Google Lyria)
│   ├── generate_music.py        # Instrumental & ambient music generation CLI (Lyria 3.5)
│   ├── output/                  # Generated music files (.mp3)
│   └── README.md                # Music generation documentation
│
├── transcribe/           # Audio Transcription & Speaker Diarization
│   ├── transcribe_audio.py      # Audio-to-text with timestamps & speaker identification
│   ├── output/                  # Transcripts and sample output
│   └── README.md                # Transcription documentation
│
├── grounding/            # Real-Time Google Search Grounding
│   ├── search_and_maps.py       # Live web retrieval with verified citations and links
│   └── README.md                # Grounding documentation
│
├── requirements.txt      # Python dependencies
└── README.md             # Master documentation (this file)
```

---

## 🚀 Quick Launch Guide

### 1. 🎤 Live Voice Interpreter (Real-Time Microphone)
Translate your spoken words in real time with audio output and bilingual subtitles:
```powershell
cd tts
& "$HOME\venv\google_tts\Scripts\python.exe" live_translate_app.py
```
👉 Open browser: `http://127.0.0.1:8081`

### 2. 🎙️ Text-to-Speech Web Studio
Interactive web app to synthesize, compare voices, and play/download audio:
```powershell
cd tts
& "$HOME\venv\google_tts\Scripts\python.exe" app.py
```
👉 Open browser: `http://127.0.0.1:8080`

### 3. 🖥️ Native Desktop GUI
Tkinter Windows desktop app:
```powershell
cd tts
& "$HOME\venv\google_tts\Scripts\python.exe" app_gui.py
```

### 4. 📝 Audio Transcription with Speaker Diarization
Transcribe any meeting or dialogue recording with speaker labels and timestamps:
```powershell
cd transcribe
& "$HOME\venv\google_tts\Scripts\python.exe" transcribe_audio.py -i ..\tts\output\gemini_multispeaker_sample.wav --timestamps
```

### 5. 🌐 Real-Time Search Grounding
Query live, grounded facts from Google Search with verified source URLs:
```powershell
cd grounding
& "$HOME\venv\google_tts\Scripts\python.exe" search_and_maps.py "What are the latest announcements for Google Gemini?"
```

### 6. 🎬 Video Generation (Google Veo)
```powershell
cd video
& "$HOME\venv\google_tts\Scripts\python.exe" generate_video.py -p "A cinematic drone shot of a futuristic neon city in the rain" --play
```

### 7. 🎵 Music Generation (Google Lyria)
```powershell
cd music
& "$HOME\venv\google_tts\Scripts\python.exe" generate_music.py -p "Lofi hip hop chill beats with gentle piano and vinyl crackle" --play
```

---

## 🔑 Authentication & Prerequisites

1. **Python Environment**: All packages are installed in `$HOME\venv\google_tts`.
2. **API Key**: `GEMINI_API_KEY` is permanently stored in Windows User Environment variables and PowerShell `$PROFILE`.
3. **Media Tools**: `ffmpeg` and `ffplay` are installed via WinGet and available globally.
