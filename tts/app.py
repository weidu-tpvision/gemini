"""
Google Text-to-Speech & Live Translation Studio (Local Web App)
Supports:
1. Gemini TTS (30 Lifelike Voices + Emotional Direction)
2. gTTS (Google Translate Standard)
3. Gemini 3.5 Live Translate (Real-Time Speech-to-Speech Translation)
"""

import os
import sys
import json
import wave
import shutil
import asyncio
import urllib.parse
import subprocess
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from gtts import gTTS
from google import genai
from google.genai import types

PORT = 8080
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TTS_MODEL = "gemini-3.1-flash-tts-preview"
LIVE_TRANSLATE_MODEL = "gemini-3.5-live-translate-preview"

GEMINI_VOICES = [
    {"name": "Puck", "trait": "Upbeat, lively"},
    {"name": "Kore", "trait": "Firm, confident"},
    {"name": "Zephyr", "trait": "Bright, warm"},
    {"name": "Charon", "trait": "Informative, steady"},
    {"name": "Fenrir", "trait": "Excitable, energetic"},
    {"name": "Leda", "trait": "Youthful, fresh"},
    {"name": "Aoede", "trait": "Breezy, casual"},
    {"name": "Achernar", "trait": "Soft, gentle"},
    {"name": "Despina", "trait": "Smooth, polished"},
    {"name": "Enceladus", "trait": "Breathy, intimate"},
    {"name": "Algieba", "trait": "Smooth, mellow"},
    {"name": "Orus", "trait": "Firm, direct"},
    {"name": "Callirrhoe", "trait": "Easy-going"},
    {"name": "Autonoe", "trait": "Bright, enthusiastic"},
    {"name": "Iapetus", "trait": "Clear, articulate"},
    {"name": "Umbriel", "trait": "Relaxed, natural"},
    {"name": "Erinome", "trait": "Crisp, clear"},
    {"name": "Algenib", "trait": "Gravelly, deep"},
    {"name": "Rasalgethi", "trait": "Informative, authoritative"},
    {"name": "Laomedeia", "trait": "Upbeat, friendly"},
]

GTTS_LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "zh-CN", "name": "Chinese (Mandarin)"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "it", "name": "Italian"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "ru", "name": "Russian"},
    {"code": "nl", "name": "Dutch"},
    {"code": "ar", "name": "Arabic"},
    {"code": "hi", "name": "Hindi"},
    {"code": "pl", "name": "Polish"},
    {"code": "tr", "name": "Turkish"},
    {"code": "vi", "name": "Vietnamese"},
]

TRANSLATE_TARGET_LANGUAGES = [
    {"code": "es", "name": "Spanish (Español)"},
    {"code": "zh", "name": "Chinese (中文)"},
    {"code": "fr", "name": "French (Français)"},
    {"code": "de", "name": "German (Deutsch)"},
    {"code": "ja", "name": "Japanese (日本語)"},
    {"code": "ko", "name": "Korean (한국어)"},
    {"code": "it", "name": "Italian (Italiano)"},
    {"code": "pt", "name": "Portuguese (Português)"},
    {"code": "ru", "name": "Russian (Русский)"},
    {"code": "ar", "name": "Arabic (العربية)"},
    {"code": "hi", "name": "Hindi (हिन्दी)"},
    {"code": "nl", "name": "Dutch (Nederlands)"},
    {"code": "pl", "name": "Polish (Polski)"},
    {"code": "tr", "name": "Turkish (Türkçe)"},
    {"code": "en", "name": "English"},
]


def find_tool(name: str):
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
    ffmpeg_cmd = find_tool("ffmpeg")
    if not ffmpeg_cmd:
        raise RuntimeError("ffmpeg is required for audio format conversion.")
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
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


def synthesize_gtts(text: str, lang: str, tld: str, slow: bool) -> Path:
    safe_name = f"gtts_{lang}_{int(os.times().system * 1000) % 100000}.mp3"
    out_path = OUTPUT_DIR / safe_name
    tts = gTTS(text=text, lang=lang, tld=tld, slow=slow)
    tts.save(str(out_path))
    return out_path


def synthesize_gemini_tts(text: str, voice: str, style: str) -> Path:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    client = genai.Client(api_key=api_key)

    if style and style.strip():
        prompt = f"### DIRECTOR'S NOTES\nStyle: {style.strip()}\nTranscript:\n{text.strip()}"
    else:
        prompt = text.strip()

    response = client.models.generate_content(
        model=TTS_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        ),
    )

    audio_bytes = b""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            audio_bytes += part.inline_data.data

    if not audio_bytes:
        raise RuntimeError("No audio stream received from Gemini TTS.")

    safe_name = f"gemini_{voice.lower()}_{int(os.times().system * 1000) % 100000}.wav"
    out_path = OUTPUT_DIR / safe_name
    save_pcm_to_wav(audio_bytes, out_path)
    return out_path


async def async_live_translate(text: str, target_lang: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    # 1. Synthesize intermediate speech for text input
    temp_source_mp3 = OUTPUT_DIR / f"temp_src_{int(os.times().system * 1000) % 100000}.mp3"
    temp_pcm = OUTPUT_DIR / f"temp_pcm_{int(os.times().system * 1000) % 100000}.pcm"

    tts = gTTS(text=text, lang="en")
    tts.save(str(temp_source_mp3))
    convert_to_16k_pcm(temp_source_mp3, temp_pcm)

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

    pcm_bytes = temp_pcm.read_bytes()
    chunk_size = 3200
    translated_audio = b""
    input_transcripts = []
    output_transcripts = []

    async with client.aio.live.connect(model=LIVE_TRANSLATE_MODEL, config=config) as session:
        async def receiver():
            nonlocal translated_audio
            try:
                async for response in session.receive():
                    sc = response.server_content
                    if sc:
                        if sc.input_transcription and sc.input_transcription.text:
                            input_transcripts.append(sc.input_transcription.text)
                        if sc.output_transcription and sc.output_transcription.text:
                            output_transcripts.append(sc.output_transcription.text)
                        if sc.model_turn:
                            for part in sc.model_turn.parts:
                                if hasattr(part, "inline_data") and part.inline_data:
                                    translated_audio += part.inline_data.data
            except Exception:
                pass

        recv_task = asyncio.create_task(receiver())

        for i in range(0, len(pcm_bytes), chunk_size):
            chunk = pcm_bytes[i:i + chunk_size]
            await session.send_realtime_input(
                audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
            )
            await asyncio.sleep(0.08)

        await asyncio.sleep(2.0)
        recv_task.cancel()

    # Cleanup temporary files
    try:
        temp_source_mp3.unlink(missing_ok=True)
        temp_pcm.unlink(missing_ok=True)
    except Exception:
        pass

    if not translated_audio:
        raise RuntimeError("No translated audio returned from Gemini 3.5 Live Translate.")

    out_name = f"live_translate_{target_lang}_{int(os.times().system * 1000) % 100000}.wav"
    out_wav = OUTPUT_DIR / out_name
    save_pcm_to_wav(translated_audio, out_wav, sample_rate=24000)

    in_txt = " ".join(input_transcripts).strip() or text
    out_txt = " ".join(output_transcripts).strip() or f"Translated into {target_lang.upper()}"

    return {
        "out_path": out_wav,
        "input_transcript": in_txt,
        "output_transcript": out_txt
    }


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Google Text-to-Speech & Live Translation Studio</title>
  <style>
    :root {
      --bg: #f8f9fa;
      --card-bg: #ffffff;
      --text: #202124;
      --text-muted: #5f6368;
      --primary: #1a73e8;
      --primary-hover: #1557b0;
      --border: #dadce0;
      --accent: #e8f0fe;
      --success: #137333;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 24px;
    }
    .container {
      max-width: 920px;
      margin: 0 auto;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }
    h1 {
      margin: 0;
      font-size: 26px;
      color: var(--primary);
    }
    .badge-free {
      background: #e6f4ea;
      color: var(--success);
      font-size: 13px;
      padding: 4px 10px;
      border-radius: 12px;
      font-weight: 600;
    }
    .card {
      background: var(--card-bg);
      border-radius: 14px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.06);
      padding: 24px;
      margin-bottom: 24px;
    }
    /* Tabs */
    .tabs {
      display: flex;
      gap: 8px;
      background: #eef2f6;
      padding: 6px;
      border-radius: 10px;
      margin-bottom: 20px;
    }
    .tab-btn {
      flex: 1;
      padding: 12px 8px;
      border: none;
      background: transparent;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      color: var(--text-muted);
      transition: all 0.2s;
      text-align: center;
    }
    .tab-btn.active {
      background: white;
      color: var(--primary);
      box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    label {
      display: block;
      font-size: 14px;
      font-weight: 600;
      margin: 14px 0 6px;
    }
    textarea, select, input[type="text"] {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      font-size: 14px;
      outline: none;
    }
    textarea:focus, select:focus, input[type="text"]:focus {
      border-color: var(--primary);
    }
    textarea {
      min-height: 110px;
      resize: vertical;
      line-height: 1.5;
    }
    .presets {
      display: flex;
      gap: 8px;
      margin-top: 8px;
      flex-wrap: wrap;
    }
    .preset-chip {
      background: #f1f3f4;
      border: 1px solid #e0e0e0;
      padding: 4px 10px;
      border-radius: 16px;
      font-size: 12px;
      cursor: pointer;
      color: var(--text-muted);
    }
    .preset-chip:hover {
      background: var(--accent);
      color: var(--primary);
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    .checkbox-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
    }
    .btn-submit {
      background: var(--primary);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 14px 28px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      margin-top: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      transition: background 0.2s;
    }
    .btn-submit:hover {
      background: var(--primary-hover);
    }
    .btn-submit:disabled {
      background: #ccc;
      cursor: not-allowed;
    }
    /* Player & Translation Cards */
    .player-card {
      display: none;
      border-left: 4px solid var(--primary);
    }
    .transcript-box {
      background: #f1f3f4;
      border-radius: 8px;
      padding: 14px;
      margin: 14px 0;
      font-size: 14px;
      line-height: 1.6;
    }
    .transcript-item {
      margin-bottom: 8px;
    }
    .transcript-item:last-child {
      margin-bottom: 0;
    }
    .player-controls {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-top: 16px;
      flex-wrap: wrap;
    }
    audio {
      flex: 1;
      min-width: 250px;
    }
    .btn-secondary {
      background: #e8eaed;
      color: var(--text);
      border: none;
      border-radius: 8px;
      padding: 10px 16px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .btn-secondary:hover {
      background: #dadce0;
    }
    .spinner {
      display: inline-block;
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: white;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .status-msg {
      margin-top: 10px;
      font-size: 13px;
    }
    .error-msg {
      color: #d93025;
    }
    .success-msg {
      color: var(--success);
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🎙️ Google TTS & Live Translation Studio</h1>
      <div style="display: flex; gap: 10px; align-items: center;">
        <span class="badge-free">100% Free / No Card Required</span>
        <a href="http://127.0.0.1:8081" class="btn-secondary" style="text-decoration:none; padding: 6px 12px; font-size:13px; font-weight:600;" target="_blank">🎤 Open Live Mic App</a>
      </div>
    </header>

    <div class="card">
      <div class="tabs">
        <button class="tab-btn active" id="tab-gemini" onclick="switchMethod('gemini')">
          ✨ Gemini TTS
        </button>
        <button class="tab-btn" id="tab-translate" onclick="switchMethod('translate')">
          🌍 Gemini 3.5 Live Translate
        </button>
        <button class="tab-btn" id="tab-gtts" onclick="switchMethod('gtts')">
          🌐 gTTS (Translate)
        </button>
      </div>

      <!-- Text Input -->
      <label for="text-input" id="text-label">Input Text (Any language supported):</label>
      <textarea id="text-input" placeholder="Type or paste your text here...">Welcome everyone! Today we are exploring the future of artificial intelligence speech synthesis.</textarea>
      
      <div class="presets">
        <span class="preset-chip" onclick="setPreset('intro')">English Intro</span>
        <span class="preset-chip" onclick="setPreset('hotel')">Hotel Reception</span>
        <span class="preset-chip" onclick="setPreset('news')">News Report</span>
        <span class="preset-chip" onclick="setPreset('zh')">Chinese (中文)</span>
        <span class="preset-chip" onclick="setPreset('es')">Spanish (Español)</span>
        <span class="preset-chip" onclick="setPreset('ja')">Japanese (日本語)</span>
      </div>

      <!-- Panel 1: Gemini TTS -->
      <div id="gemini-panel">
        <div class="grid-2">
          <div>
            <label for="gemini-voice">Voice Selection (30 Expressive Voices):</label>
            <select id="gemini-voice"></select>
          </div>
          <div>
            <label for="gemini-style">Emotional / Stylistic Direction (Optional):</label>
            <input type="text" id="gemini-style" placeholder="e.g. Energetic & cheerful, Whisper, Formal news anchor" />
          </div>
        </div>
      </div>

      <!-- Panel 2: Gemini 3.5 Live Translate -->
      <div id="translate-panel" style="display: none;">
        <div class="grid-2">
          <div>
            <label for="target-lang">Translate Speech Into (Target Language):</label>
            <select id="target-lang"></select>
          </div>
          <div>
            <label style="color: var(--text-muted);">Model Engine:</label>
            <div style="padding: 12px; background:#f1f3f4; border-radius:8px; font-size:13px; font-weight:600; color:#1a73e8;">
              gemini-3.5-live-translate-preview (Speech-to-Speech)
            </div>
          </div>
        </div>
        <p style="font-size: 13px; color: var(--text-muted); margin-top: 10px;">
          ℹ️ The model acts as a real-time interpreter: your input speech is translated and synthesized into the target language with real-time bilingual transcripts.
        </p>
      </div>

      <!-- Panel 3: gTTS -->
      <div id="gtts-panel" style="display: none;">
        <div class="grid-2">
          <div>
            <label for="gtts-lang">Language:</label>
            <select id="gtts-lang"></select>
          </div>
          <div>
            <label for="gtts-tld">English Accent (TLD):</label>
            <select id="gtts-tld">
              <option value="com">United States (.com)</option>
              <option value="co.uk">United Kingdom (.co.uk)</option>
              <option value="com.au">Australia (.com.au)</option>
              <option value="co.in">India (.co.in)</option>
              <option value="ca">Canada (.ca)</option>
            </select>
          </div>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="gtts-slow" />
          <label for="gtts-slow" style="margin: 0; font-weight: normal;">Speak slowly</label>
        </div>
      </div>

      <button class="btn-submit" id="btn-generate" onclick="generateSpeech()">
        <span id="btn-icon">⚡</span> <span id="btn-text">Synthesize Speech</span>
      </button>

      <div id="status-box" class="status-msg"></div>
    </div>

    <!-- Active Audio Player & Transcript Card -->
    <div class="card player-card" id="player-card">
      <h3 style="margin-top: 0; font-size: 16px;">🔊 Result: <span id="player-title" style="font-weight: normal; color: var(--text-muted);"></span></h3>
      
      <div id="transcript-container" style="display: none;" class="transcript-box">
        <div class="transcript-item"><strong>🎤 Original Speech:</strong> <span id="in-transcript"></span></div>
        <div class="transcript-item"><strong>🌍 Translated Speech:</strong> <span id="out-transcript" style="color: #1a73e8; font-weight: bold;"></span></div>
      </div>

      <div class="player-controls">
        <audio id="audio-element" controls autoplay></audio>
        <button class="btn-secondary" id="btn-ffplay" onclick="playOnSpeakers()">
          🔊 Play via ffplay
        </button>
        <a id="btn-download" class="btn-secondary" download style="text-decoration: none;">
          ⬇️ Download Audio
        </a>
      </div>
    </div>
  </div>

  <script>
    let currentMethod = 'gemini';
    let currentAudioFilename = '';

    const geminiVoices = """ + json.dumps(GEMINI_VOICES) + """;
    const gttsLanguages = """ + json.dumps(GTTS_LANGUAGES) + """;
    const targetLangs = """ + json.dumps(TRANSLATE_TARGET_LANGUAGES) + """;

    // Populate voices & dropdowns
    const geminiSelect = document.getElementById('gemini-voice');
    geminiVoices.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.name;
      opt.textContent = `${v.name} — ${v.trait}`;
      if (v.name === 'Puck') opt.selected = true;
      geminiSelect.appendChild(opt);
    });

    const gttsSelect = document.getElementById('gtts-lang');
    gttsLanguages.forEach(l => {
      const opt = document.createElement('option');
      opt.value = l.code;
      opt.textContent = `${l.name} (${l.code})`;
      if (l.code === 'en') opt.selected = true;
      gttsSelect.appendChild(opt);
    });

    const targetSelect = document.getElementById('target-lang');
    targetLangs.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.code;
      opt.textContent = `${t.name} [${t.code}]`;
      if (t.code === 'es') opt.selected = true;
      targetSelect.appendChild(opt);
    });

    function switchMethod(method) {
      currentMethod = method;
      document.getElementById('tab-gemini').classList.toggle('active', method === 'gemini');
      document.getElementById('tab-translate').classList.toggle('active', method === 'translate');
      document.getElementById('tab-gtts').classList.toggle('active', method === 'gtts');

      document.getElementById('gemini-panel').style.display = method === 'gemini' ? 'block' : 'none';
      document.getElementById('translate-panel').style.display = method === 'translate' ? 'block' : 'none';
      document.getElementById('gtts-panel').style.display = method === 'gtts' ? 'block' : 'none';

      const btnText = document.getElementById('btn-text');
      if (method === 'translate') {
        btnText.textContent = 'Translate & Synthesize Live Voice';
      } else {
        btnText.textContent = 'Synthesize Speech';
      }
    }

    function setPreset(type) {
      const textarea = document.getElementById('text-input');
      if (type === 'intro') {
        textarea.value = "Hello! Welcome to our international conference. We are delighted to host you today.";
      } else if (type === 'hotel') {
        textarea.value = "Good afternoon! Welcome to the Grand Plaza Hotel. How may I assist with your check-in?";
        if (currentMethod === 'translate') document.getElementById('target-lang').value = 'ja';
      } else if (type === 'news') {
        textarea.value = "Good evening. Tonight, researchers announced major breakthroughs in real-time voice translation.";
        if (currentMethod === 'gemini') document.getElementById('gemini-style').value = 'Formal news anchor';
      } else if (type === 'zh') {
        textarea.value = "您好！欢迎使用谷歌文本转语音与即时翻译工作室。";
      } else if (type === 'es') {
        textarea.value = "¡Hola! Bienvenidos a nuestra prueba de síntesis y traducción en tiempo real.";
      } else if (type === 'ja') {
        textarea.value = "こんにちは！リアルタイム音声合成および翻訳スタジオへようこそ。";
      }
    }

    async function generateSpeech() {
      const text = document.getElementById('text-input').value.trim();
      const statusBox = document.getElementById('status-box');
      const btn = document.getElementById('btn-generate');

      if (!text) {
        statusBox.textContent = 'Please enter some text.';
        statusBox.className = 'status-msg error-msg';
        return;
      }

      btn.disabled = true;
      document.getElementById('btn-icon').innerHTML = '<span class="spinner"></span>';
      document.getElementById('btn-text').textContent = currentMethod === 'translate' ? 'Translating & Streaming Voice...' : 'Synthesizing Audio...';
      statusBox.textContent = 'Processing request...';
      statusBox.className = 'status-msg';

      const payload = {
        method: currentMethod,
        text: text,
        voice: document.getElementById('gemini-voice').value,
        style: document.getElementById('gemini-style').value,
        target_lang: document.getElementById('target-lang').value,
        lang: document.getElementById('gtts-lang').value,
        tld: document.getElementById('gtts-tld').value,
        slow: document.getElementById('gtts-slow').checked
      };

      try {
        const res = await fetch('/api/synthesize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok || data.error) {
          throw new Error(data.error || 'Operation failed');
        }

        statusBox.textContent = `[OK] Generated successfully (${data.filename}, ${Math.round(data.size / 1024)} KB)`;
        statusBox.className = 'status-msg success-msg';

        // Update player
        currentAudioFilename = data.filename;
        const playerCard = document.getElementById('player-card');
        playerCard.style.display = 'block';
        document.getElementById('player-title').textContent = data.filename;
        
        const transcriptBox = document.getElementById('transcript-container');
        if (data.input_transcript && data.output_transcript) {
          transcriptBox.style.display = 'block';
          document.getElementById('in-transcript').textContent = data.input_transcript;
          document.getElementById('out-transcript').textContent = data.output_transcript;
        } else {
          transcriptBox.style.display = 'none';
        }

        const audioEl = document.getElementById('audio-element');
        audioEl.src = data.audio_url;
        audioEl.play();

        const dlBtn = document.getElementById('btn-download');
        dlBtn.href = data.audio_url;
        dlBtn.download = data.filename;
      } catch (err) {
        statusBox.textContent = 'Error: ' + err.message;
        statusBox.className = 'status-msg error-msg';
      } finally {
        btn.disabled = false;
        document.getElementById('btn-icon').textContent = '⚡';
        document.getElementById('btn-text').textContent = currentMethod === 'translate' ? 'Translate & Synthesize Live Voice' : 'Synthesize Speech';
      }
    }

    async function playOnSpeakers() {
      if (!currentAudioFilename) return;
      try {
        await fetch('/api/play-cli', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: currentAudioFilename })
        });
      } catch (err) {
        console.error(err);
      }
    }
  </script>
</body>
</html>
"""


class TTSRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        if path.startswith("/audio/"):
            filename = os.path.basename(path)
            file_path = OUTPUT_DIR / filename
            if file_path.exists() and file_path.is_file():
                mime = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
                data = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                self.wfile.write(data)
                return
            else:
                self.send_error(404, "File Not Found")
                return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/synthesize":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)

            method = data.get("method", "gemini")
            text = data.get("text", "").strip()

            if not text:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Empty text provided."}).encode("utf-8"))
                return

            try:
                if method == "gemini":
                    voice = data.get("voice", "Puck")
                    style = data.get("style", "")
                    out_path = synthesize_gemini_tts(text=text, voice=voice, style=style)
                    resp = {
                        "success": True,
                        "filename": out_path.name,
                        "size": out_path.stat().st_size,
                        "audio_url": f"/audio/{out_path.name}",
                    }
                elif method == "translate":
                    target_lang = data.get("target_lang", "es")
                    result = asyncio.run(async_live_translate(text=text, target_lang=target_lang))
                    out_path = result["out_path"]
                    resp = {
                        "success": True,
                        "filename": out_path.name,
                        "size": out_path.stat().st_size,
                        "audio_url": f"/audio/{out_path.name}",
                        "input_transcript": result["input_transcript"],
                        "output_transcript": result["output_transcript"],
                    }
                else:
                    lang = data.get("lang", "en")
                    tld = data.get("tld", "com")
                    slow = bool(data.get("slow", False))
                    out_path = synthesize_gtts(text=text, lang=lang, tld=tld, slow=slow)
                    resp = {
                        "success": True,
                        "filename": out_path.name,
                        "size": out_path.stat().st_size,
                        "audio_url": f"/audio/{out_path.name}",
                    }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/play-cli":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            filename = os.path.basename(data.get("filename", ""))
            file_path = OUTPUT_DIR / filename
            if file_path.exists():
                ffplay_cmd = find_tool("ffplay")
                if ffplay_cmd:
                    subprocess.Popen([ffplay_cmd, "-nodisp", "-autoexit", "-loglevel", "quiet", str(file_path)])
                else:
                    subprocess.Popen(["powershell", "-c", f"Start-Process '{file_path}'"])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                return
            else:
                self.send_error(404, "Audio file not found")
                return

        self.send_error(404, "Endpoint Not Found")


def main():
    server_address = ("127.0.0.1", PORT)
    httpd = ThreadingHTTPServer(server_address, TTSRequestHandler)
    url = f"http://127.0.0.1:{PORT}"
    print("=" * 70)
    print("Google Text-to-Speech & Live Translation Studio Running")
    print(f"URL: {url}")
    print("Press Ctrl+C in this terminal to stop.")
    print("=" * 70)

    webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    main()
