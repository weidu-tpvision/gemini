# Google Text-to-Speech & Live Translation Studio

An interactive application and testing suite for evaluating **Google Text-to-Speech and Real-Time Speech Translation options powered by the Google Gemini API**.

---

## 🚀 Interactive Applications

### 1. 🎤 Gemini 3.5 Live Voice Interpreter (Microphone to Speech-to-Speech)
A dedicated, real-time voice interpreter that streams your **microphone audio directly into `gemini-3.5-live-translate-preview`** over WebSockets and speaks the translated voice back to you in real time with live bilingual subtitles.

```bash
python live_translate_app.py
```
- Open URL: `http://127.0.0.1:8081`
- **Features**:
  - Live microphone streaming via Web Audio (`getUserMedia` ➔ 16kHz PCM stream).
  - Target language selector (Spanish, Chinese, Japanese, French, German, Italian, Korean, Arabic, Russian, Portuguese, etc.).
  - Visual volume / audio level meter.
  - Side-by-side real-time bilingual subtitles (Original Speech vs. Translated Speech).
  - Instant, low-latency audio playback of the translated speech through your browser/speakers.
  - One-click navigation link to jump to the TTS Studio.

---

### 2. 🎙️ Google TTS & Translation Studio App (Browser Interface)
A multi-engine text-to-speech studio allowing you to type or paste text in any language and compare synthesis models.

```bash
python app.py
```
- Open URL: `http://127.0.0.1:8080`
- **Features**:
  - **Gemini TTS**: 30 expressive voices (`Puck`, `Kore`, `Zephyr`, `Charon`, `Fenrir`, etc.) + emotional/stylistic steering.
  - **Gemini 3.5 Live Translate**: Translate text/speech into 70+ languages with bilingual transcripts.
  - **gTTS**: Free Google Translate standard voice synthesis (100+ languages, accents, slow speed).
  - Audio player with scrub bar, rate controls, and download button.
  - Host speaker playback via `ffplay`.

---

### 3. 🖥️ Desktop GUI App (Tkinter Native Window)
```bash
python app_gui.py
```
- Native desktop application supporting Gemini TTS, Live Translate, and gTTS.

---

## 🛠️ CLI Test Scripts

```bash
# 1. Translate speech and play immediately via CLI:
python test_live_translate.py -t "Good morning, welcome to our office!" --target es --play

# 2. Synthesize Gemini TTS with specific voice & emotion:
python test_gemini_tts.py -t "Attention everyone!" -v Zephyr --style "Enthusiastic" -p

# 3. Synthesize gTTS with British accent:
python test_gtts.py -t "Mind the gap please." --tld co.uk -p

# 4. Synthesize Spanish with gTTS:
python test_gtts.py -t "Buenos dias, bienvenidos a nuestra oficina." -l es -p
```
