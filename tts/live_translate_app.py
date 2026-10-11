"""
Gemini 3.5 Live Voice Interpreter (Microphone to Speech-to-Speech)
Captures live microphone audio in the browser, streams raw 16kHz PCM to
gemini-3.5-live-translate-preview over WebSockets, and plays back the translated
speech in real time with live bilingual subtitles.
"""

import os
import sys
import json
import base64
import asyncio
import shutil
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import websockets
from google import genai
from google.genai import types

HTTP_PORT = 8081
WS_PORT = 8082
MODEL = "gemini-3.5-live-translate-preview"

TARGET_LANGUAGES = [
    {"code": "es", "name": "Spanish (Español)"},
    {"code": "zh", "name": "Chinese (中文)"},
    {"code": "ja", "name": "Japanese (日本語)"},
    {"code": "fr", "name": "French (Français)"},
    {"code": "de", "name": "German (Deutsch)"},
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

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Gemini 3.5 Live Voice Interpreter</title>
  <style>
    :root {
      --bg: #f8f9fa;
      --card-bg: #ffffff;
      --text: #202124;
      --text-muted: #5f6368;
      --primary: #1a73e8;
      --primary-hover: #1557b0;
      --danger: #d93025;
      --danger-hover: #b3261e;
      --success: #137333;
      --border: #dadce0;
      --accent: #e8f0fe;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 24px;
    }
    .container {
      max-width: 960px;
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
      font-size: 24px;
      color: var(--primary);
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .nav-btn {
      text-decoration: none;
      background: #e8eaed;
      color: var(--text);
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
    }
    .nav-btn:hover {
      background: #dadce0;
    }
    .card {
      background: var(--card-bg);
      border-radius: 14px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.06);
      padding: 24px;
      margin-bottom: 24px;
    }
    .controls-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 16px;
      align-items: end;
    }
    label {
      display: block;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 6px;
    }
    select {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      font-size: 14px;
      outline: none;
    }
    .btn-mic {
      background: var(--primary);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 12px 24px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: background 0.2s;
      width: 100%;
      box-sizing: border-box;
    }
    .btn-mic:hover {
      background: var(--primary-hover);
    }
    .btn-mic.recording {
      background: var(--danger);
      animation: pulse 1.5s infinite;
    }
    .btn-mic.recording:hover {
      background: var(--danger-hover);
    }
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(217, 48, 37, 0.4); }
      70% { box-shadow: 0 0 0 10px rgba(217, 48, 37, 0); }
      100% { box-shadow: 0 0 0 0 rgba(217, 48, 37, 0); }
    }
    /* Visualizer */
    .meter-container {
      margin-top: 16px;
      background: #eef2f6;
      border-radius: 6px;
      height: 8px;
      overflow: hidden;
    }
    .meter-bar {
      height: 100%;
      width: 0%;
      background: var(--primary);
      transition: width 0.05s linear;
    }
    /* Subtitles Grid */
    .bilingual-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 10px;
    }
    .column-box {
      background: #f8f9fa;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
      min-height: 280px;
      max-height: 400px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }
    .column-header {
      font-weight: 600;
      font-size: 14px;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
    }
    .transcript-text {
      font-size: 16px;
      line-height: 1.6;
      flex: 1;
      white-space: pre-wrap;
    }
    .source-text {
      color: var(--text);
    }
    .target-text {
      color: var(--primary);
      font-weight: 500;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 500;
      color: var(--text-muted);
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #ccc;
    }
    .dot.live {
      background: #34a853;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🌍 Gemini 3.5 Live Voice Interpreter</h1>
      <div style="display:flex; gap:10px; align-items:center;">
        <span class="status-badge" id="status-badge">
          <span class="dot" id="status-dot"></span> <span id="status-text">Ready</span>
        </span>
        <a href="http://127.0.0.1:8080" class="nav-btn">🎙️ Open TTS Studio</a>
      </div>
    </header>

    <div class="card">
      <div class="controls-grid">
        <div>
          <label for="target-lang">Translate My Speech Into (Target Language):</label>
          <select id="target-lang"></select>
        </div>
        <div>
          <button class="btn-mic" id="btn-mic" onclick="toggleMicrophone()">
            <span id="mic-icon">🎤</span> <span id="mic-text">Start Live Interpretation</span>
          </button>
        </div>
      </div>

      <div class="meter-container">
        <div class="meter-bar" id="meter-bar"></div>
      </div>
    </div>

    <!-- Bilingual Live Subtitles -->
    <div class="card">
      <div class="bilingual-grid">
        <div class="column-box">
          <div class="column-header">
            <span>🎤 What You Spoke</span>
            <span style="font-size:12px; color:var(--text-muted);">Auto-Detected</span>
          </div>
          <div class="transcript-text source-text" id="source-transcript">Click "Start Live Interpretation" and speak naturally into your microphone...</div>
        </div>

        <div class="column-box" style="border-left: 3px solid var(--primary);">
          <div class="column-header">
            <span>🌍 Real-Time Translation & Spoken Voice</span>
            <span id="target-badge" style="font-size:12px; color:var(--primary); font-weight:bold;">SPANISH</span>
          </div>
          <div class="transcript-text target-text" id="target-transcript">The translated voice will be spoken aloud immediately in real-time.</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const targetLangs = """ + json.dumps(TARGET_LANGUAGES) + """;
    const targetSelect = document.getElementById('target-lang');
    const targetBadge = document.getElementById('target-badge');

    targetLangs.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.code;
      opt.textContent = `${t.name} [${t.code}]`;
      if (t.code === 'es') opt.selected = true;
      targetSelect.appendChild(opt);
    });

    targetSelect.addEventListener('change', () => {
      targetBadge.textContent = targetSelect.options[targetSelect.selectedIndex].text.toUpperCase();
    });

    let ws = null;
    let audioContext = null;
    let mediaStream = null;
    let processorNode = null;
    let isInterpreting = false;

    // Output Audio Player Context (24kHz for Gemini output)
    let outputAudioCtx = null;
    let nextPlayTime = 0;

    function initOutputAudio() {
      if (!outputAudioCtx) {
        outputAudioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
      }
      if (outputAudioCtx.state === 'suspended') {
        outputAudioCtx.resume();
      }
    }

    function playTranslatedAudioChunk(pcmBase64) {
      initOutputAudio();
      const binaryString = atob(pcmBase64);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      const int16 = new Int16Array(bytes.buffer);
      const float32 = new Float32Array(int16.length);
      for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 32768.0;
      }

      const audioBuffer = outputAudioCtx.createBuffer(1, float32.length, 24000);
      audioBuffer.getChannelData(0).set(float32);

      const source = outputAudioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(outputAudioCtx.destination);

      nextPlayTime = Math.max(outputAudioCtx.currentTime, nextPlayTime);
      source.start(nextPlayTime);
      nextPlayTime += audioBuffer.duration;
    }

    async function toggleMicrophone() {
      if (isInterpreting) {
        stopInterpretation();
      } else {
        await startInterpretation();
      }
    }

    async function startInterpretation() {
      const targetLang = targetSelect.value;
      const btn = document.getElementById('btn-mic');
      const statusDot = document.getElementById('status-dot');
      const statusText = document.getElementById('status-text');

      statusText.textContent = 'Connecting...';
      document.getElementById('source-transcript').textContent = '';
      document.getElementById('target-transcript').textContent = '';

      // 1. Connect WebSocket
      const wsUrl = `ws://${window.location.hostname}:` + """ + str(WS_PORT) + """;
      ws = new WebSocket(wsUrl);

      ws.onopen = async () => {
        statusText.textContent = 'Live Translating';
        statusDot.className = 'dot live';
        btn.classList.add('recording');
        document.getElementById('mic-icon').textContent = '⏹️';
        document.getElementById('mic-text').textContent = 'Stop Interpretation';
        targetSelect.disabled = true;
        isInterpreting = true;

        // Send start session config
        ws.send(JSON.stringify({
          type: 'start',
          target_lang: targetLang
        }));

        // 2. Start Microphone capture (16kHz mono)
        await startMicrophoneCapture();
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'input_transcript') {
          const el = document.getElementById('source-transcript');
          el.textContent += (el.textContent ? ' ' : '') + msg.text;
          el.parentElement.scrollTop = el.parentElement.scrollHeight;
        } else if (msg.type === 'output_transcript') {
          const el = document.getElementById('target-transcript');
          el.textContent += (el.textContent ? ' ' : '') + msg.text;
          el.parentElement.scrollTop = el.parentElement.scrollHeight;
        } else if (msg.type === 'audio') {
          playTranslatedAudioChunk(msg.data);
        } else if (msg.type === 'error') {
          alert('Interpretation error: ' + msg.message);
          stopInterpretation();
        }
      };

      ws.onclose = () => {
        stopInterpretation();
      };

      ws.onerror = (e) => {
        console.error('WS Error:', e);
        stopInterpretation();
      };
    }

    async function startMicrophoneCapture() {
      audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }
      });

      const source = audioContext.createMediaStreamSource(mediaStream);
      processorNode = audioContext.createScriptProcessor(2048, 1, 1);

      processorNode.onaudioprocess = (e) => {
        if (!isInterpreting || !ws || ws.readyState !== WebSocket.OPEN) return;

        const inputData = e.inputBuffer.getChannelData(0);
        // Compute volume for visualizer
        let sum = 0;
        const pcm16 = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          let s = Math.max(-1, Math.min(1, inputData[i]));
          pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          sum += s * s;
        }

        const rms = Math.sqrt(sum / inputData.length);
        document.getElementById('meter-bar').style.width = Math.min(100, rms * 400) + '%';

        // Send raw 16kHz PCM bytes to server
        ws.send(pcm16.buffer);
      };

      source.connect(processorNode);
      processorNode.connect(audioContext.destination);
    }

    function stopInterpretation() {
      isInterpreting = false;
      const btn = document.getElementById('btn-mic');
      btn.classList.remove('recording');
      document.getElementById('mic-icon').textContent = '🎤';
      document.getElementById('mic-text').textContent = 'Start Live Interpretation';
      document.getElementById('status-dot').className = 'dot';
      document.getElementById('status-text').textContent = 'Ready';
      document.getElementById('meter-bar').style.width = '0%';
      targetSelect.disabled = false;

      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
      }
      if (processorNode) {
        processorNode.disconnect();
        processorNode = null;
      }
      if (audioContext) {
        audioContext.close();
        audioContext = null;
      }
      if (ws) {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'stop' }));
          ws.close();
        }
        ws = null;
      }
    }
  </script>
</body>
</html>
"""


class WebHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))


async def ws_handler(websocket):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        await websocket.send(json.dumps({"type": "error", "message": "GEMINI_API_KEY is not set."}))
        return

    client = genai.Client(api_key=api_key)
    session = None
    receive_task = None
    target_lang = "es"

    try:
        async for message in websocket:
            if isinstance(message, str):
                data = json.loads(message)
                if data.get("type") == "start":
                    target_lang = data.get("target_lang", "es")
                    config = types.LiveConnectConfig(
                        response_modalities=["AUDIO"],
                        input_audio_transcription=types.AudioTranscriptionConfig(),
                        output_audio_transcription=types.AudioTranscriptionConfig(),
                        translation_config=types.TranslationConfig(
                            target_language_code=target_lang,
                            echo_target_language=True
                        )
                    )

                    session_cm = client.aio.live.connect(model=MODEL, config=config)
                    session = await session_cm.__aenter__()

                    async def receive_loop():
                        try:
                            async for response in session.receive():
                                sc = response.server_content
                                if sc:
                                    if sc.input_transcription and sc.input_transcription.text:
                                        await websocket.send(json.dumps({
                                            "type": "input_transcript",
                                            "text": sc.input_transcription.text
                                        }))
                                    if sc.output_transcription and sc.output_transcription.text:
                                        await websocket.send(json.dumps({
                                            "type": "output_transcript",
                                            "text": sc.output_transcription.text
                                        }))
                                    if sc.model_turn:
                                        for part in sc.model_turn.parts:
                                            if hasattr(part, "inline_data") and part.inline_data:
                                                b64_audio = base64.b64encode(part.inline_data.data).decode("ascii")
                                                await websocket.send(json.dumps({
                                                    "type": "audio",
                                                    "data": b64_audio
                                                }))
                        except Exception as e:
                            pass

                    receive_task = asyncio.create_task(receive_loop())

                elif data.get("type") == "stop":
                    if receive_task:
                        receive_task.cancel()
                    if session:
                        await session_cm.__aexit__(None, None, None)
                        session = None

            elif isinstance(message, bytes):
                # Binary audio chunk from microphone (16kHz 16-bit PCM)
                if session:
                    await session.send_realtime_input(
                        audio=types.Blob(
                            data=message,
                            mime_type="audio/pcm;rate=16000"
                        )
                    )
    except Exception as e:
        print(f"WS error: {e}")
    finally:
        if receive_task:
            receive_task.cancel()
        if session:
            try:
                await session_cm.__aexit__(None, None, None)
            except Exception:
                pass


async def main_async():
    # 1. Start HTTP Server for UI
    httpd = ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), WebHandler)
    http_thread = asyncio.to_thread(httpd.serve_forever)
    asyncio.create_task(http_thread)

    # 2. Start WebSocket Server for Microphone Stream
    ws_server = await websockets.serve(ws_handler, "127.0.0.1", WS_PORT)

    url = f"http://127.0.0.1:{HTTP_PORT}"
    print("=" * 70)
    print("Gemini 3.5 Live Voice Interpreter (Microphone Translation) Running")
    print(f"Web Interface: {url}")
    print(f"WebSocket Port: {WS_PORT}")
    print("Press Ctrl+C to stop.")
    print("=" * 70)

    webbrowser.open(url)
    await ws_server.wait_closed()


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nStopping Live Interpreter server...")


if __name__ == "__main__":
    main()
