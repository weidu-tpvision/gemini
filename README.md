# Gemini Multimodal AI Studio Hub

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Google GenAI SDK](https://img.shields.io/badge/google--genai-v1.0%2B-orange.svg)](https://github.com/google-gemini/generative-ai-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

An all-in-one, modular open-source suite of **interactive web applications, desktop GUIs, and CLI tools** powered by the **Google Gemini Multimodal API** (`google-genai` SDK).

Explore and experiment with speech-to-speech translation, expressive text-to-speech, audio transcription with speaker diarization, AI video generation, music composition, and search-grounded reasoning.

---

## ✨ Features Overview

| Feature | Tech / Model | Description |
| :--- | :--- | :--- |
| 🎤 **Live Voice Interpreter** | `gemini-3.5-live-translate-preview` | Real-time speech-to-speech microphone translation with live bilingual subtitles over WebSockets. |
| 🎙️ **TTS Web Studio** | `gemini-3.1-flash` & `gTTS` | Multi-engine voice synthesizer with 30 expressive voices, emotional tone steering, and gTTS fallback. |
| 🖥️ **Desktop GUI** | Tkinter & `google-genai` | Native Windows/cross-platform desktop interface for TTS synthesis and voice testing. |
| 📝 **Transcription & Diarization** | `gemini-2.5-flash` / `gemini-3.1-flash` | Automatic speech-to-text with millisecond timestamps and multi-speaker separation. |
| 🌐 **Search Grounding** | Google Search Tool | Fact-based queries grounded with real-time web retrieval, complete with citations and source URLs. |
| 🎬 **Video Generation** | Google Veo (`veo-3.1-generate-preview`) | Text-to-video and image-to-video generation with matched synchronized audio. |
| 🎵 **Music Generation** | Google Lyria (`lyria-3.5`) | Instrumental tracks, ambient soundscapes, lo-fi beats, and structured multi-section compositions. |

---

## 📁 Repository Structure

```text
gemini/
├── tts/                  # Speech Synthesis & Real-Time Voice Translation
│   ├── app.py                   # Multi-Engine Web Studio (Port 8080)
│   ├── live_translate_app.py    # Real-Time Microphone Speech-to-Speech Web App (Port 8081)
│   ├── app_gui.py               # Native Desktop GUI (Tkinter)
│   ├── test_gemini_tts.py       # Gemini 3.1 Flash TTS CLI (30 expressive voices)
│   ├── test_live_translate.py   # Gemini 3.5 Live Voice Translate CLI
│   ├── test_gtts.py             # Google Translate TTS CLI (100+ languages & accents)
│   ├── test_browser_tts.html    # Chrome Web Speech API in-browser tester
│   └── output/                  # Generated sample audio (.wav / .mp3)
│
├── transcribe/           # Audio Transcription & Speaker Diarization
│   ├── transcribe_audio.py      # Audio-to-text CLI with timestamps & speaker labels
│   └── output/                  # Transcripts and sample output
│
├── grounding/            # Real-Time Google Search Grounding
│   └── search_and_maps.py       # Live web retrieval with verified citations and links
│
├── video/                # AI Video Generation (Google Veo)
│   ├── generate_video.py        # Text-to-Video & Image-to-Video CLI
│   └── output/                  # Generated video files (.mp4)
│
├── music/                # AI Music & Audio Generation (Google Lyria)
│   ├── generate_music.py        # Instrumental & ambient music generation CLI
│   └── output/                  # Generated music files (.mp3)
│
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: Version 3.10 or higher.
- **FFmpeg**: Required for audio format conversion and media playback (`ffplay`).
  - **Windows**: `winget install Gyan.FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html).
  - **macOS**: `brew install ffmpeg`
  - **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install ffmpeg`
- **Google AI Studio API Key**: A free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 2. Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/weidu-tpvision/gemini.git
   cd gemini
   ```

2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configure Your API Key

Obtain your API key from [Google AI Studio](https://aistudio.google.com/app/apikey), then export it as an environment variable:

- **Windows (PowerShell):**
  ```powershell
  $env:GEMINI_API_KEY = "your_api_key_here"
  
  # Or set permanently for your user account:
  [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your_api_key_here", "User")
  ```

- **macOS / Linux (Bash / Zsh):**
  ```bash
  export GEMINI_API_KEY="your_api_key_here"
  
  # Or add to ~/.bashrc or ~/.zshrc for permanent access
  ```

---

## 🎯 Quickstart Guide

### 🎤 1. Real-Time Voice Interpreter (Live Microphone)
Stream your spoken voice directly into Gemini 3.5 Live over WebSockets and receive spoken translations with bilingual subtitles:

```bash
cd tts
python live_translate_app.py
```
👉 Open your browser at **[http://127.0.0.1:8081](http://127.0.0.1:8081)**. Allow microphone access, choose your target language, and start speaking.

---

### 🎙️ 2. Text-to-Speech Web Studio
A browser interface for synthesizing, comparing voices, testing emotional styles, and downloading audio:

```bash
cd tts
python app.py
```
👉 Open your browser at **[http://127.0.0.1:8080](http://127.0.0.1:8080)**.

---

### 🖥️ 3. Native Desktop GUI
A lightweight desktop app for quick TTS experiments:

```bash
cd tts
python app_gui.py
```

---

### 📝 4. Audio Transcription & Diarization
Transcribe audio files with automatic speaker separation and millisecond timestamps:

```bash
cd transcribe

# Transcribe sample file with speaker labels:
python transcribe_audio.py -i ../tts/output/gemini_multispeaker_sample.wav

# Include precise timestamps:
python transcribe_audio.py -i ../tts/output/gemini_multispeaker_sample.wav --timestamps
```

---

### 🌐 5. Real-Time Google Search Grounding
Ask questions that require live, real-time facts with verified web links and sources:

```bash
cd grounding
python search_and_maps.py "What are the latest announcements regarding Google Gemini?"
```

---

### 🎬 6. AI Video Generation (Google Veo)
Generate high-definition videos from text prompts or reference images:

```bash
cd video

# Generate a 5-second cinematic clip and preview with ffplay:
python generate_video.py -p "A cinematic drone shot of a futuristic neon city in the rain" --play
```

---

### 🎵 7. AI Music Generation (Google Lyria)
Create instrumental music and ambient loops from text prompts:

```bash
cd music

# Generate a lo-fi beat and play immediately:
python generate_music.py -p "Lofi hip hop chill beats with gentle piano and vinyl crackle" --play
```

---

## ⚙️ Troubleshooting

- **Microphone not working in Live Interpreter**:
  - Ensure browser permissions allow microphone access for `http://127.0.0.1:8081`.
  - In Chrome, navigate to `chrome://settings/content/microphone` to confirm your default input device.
- **FFmpeg not recognized**:
  - Verify that `ffmpeg` is in your system's PATH by running `ffmpeg -version` in your terminal.
- **API Key Errors (`GEMINI_API_KEY is not set`)**:
  - Ensure the variable is set in the same terminal session running the scripts (`echo $env:GEMINI_API_KEY` or `echo $GEMINI_API_KEY`).

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
