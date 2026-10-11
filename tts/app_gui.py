"""
Google Text-to-Speech & Live Translation Desktop GUI App (Tkinter)
Allows choosing between:
1. Gemini TTS (30 voices + emotion)
2. Gemini 3.5 Live Translate (Speech-to-Speech live translation)
3. gTTS (Google Translate standard)
"""

import os
import sys
import wave
import shutil
import asyncio
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from gtts import gTTS
from google import genai
from google.genai import types

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TTS_MODEL = "gemini-3.1-flash-tts-preview"
LIVE_TRANSLATE_MODEL = "gemini-3.5-live-translate-preview"

GEMINI_VOICES = [
    "Puck (Upbeat)", "Kore (Firm)", "Zephyr (Bright)", "Charon (Informative)",
    "Fenrir (Excitable)", "Leda (Youthful)", "Aoede (Breezy)", "Achernar (Soft)",
    "Despina (Smooth)", "Enceladus (Breathy)", "Algieba (Smooth)", "Orus (Firm)",
    "Callirrhoe (Easy-going)", "Autonoe (Bright)", "Iapetus (Clear)", "Umbriel (Relaxed)",
    "Erinome (Crisp)", "Algenib (Gravelly)", "Rasalgethi (Authoritative)", "Laomedeia (Upbeat)"
]

TRANSLATE_TARGETS = [
    ("Spanish (Español)", "es"), ("Chinese (中文)", "zh"), ("French (Français)", "fr"),
    ("German (Deutsch)", "de"), ("Japanese (日本語)", "ja"), ("Korean (한국어)", "ko"),
    ("Italian (Italiano)", "it"), ("Portuguese (Português)", "pt"), ("Russian (Русский)", "ru"),
    ("Arabic (العربية)", "ar"), ("Hindi (हिन्दी)", "hi"), ("Dutch (Nederlands)", "nl"),
    ("Polish (Polski)", "pl"), ("Turkish (Türkçe)", "tr"), ("English", "en")
]

GTTS_LANGS = [
    ("English", "en"), ("Chinese (Mandarin)", "zh-CN"), ("Spanish", "es"),
    ("French", "fr"), ("German", "de"), ("Japanese", "ja"), ("Korean", "ko"),
    ("Italian", "it"), ("Portuguese", "pt"), ("Russian", "ru"), ("Arabic", "ar"),
    ("Hindi", "hi"), ("Dutch", "nl"), ("Turkish", "tr"), ("Vietnamese", "vi")
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


def play_audio_file(file_path: Path):
    ffplay_cmd = find_tool("ffplay")
    if ffplay_cmd:
        subprocess.run([ffplay_cmd, "-nodisp", "-autoexit", "-loglevel", "quiet", str(file_path)])
    else:
        subprocess.run(["powershell", "-c", f"Start-Process '{file_path}'"])


def save_pcm_to_wav(pcm_bytes: bytes, wav_path: Path, sample_rate: int = 24000):
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


class TTSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Google Text-to-Speech & Live Translation Studio")
        self.geometry("720x750")
        self.minsize(600, 650)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.method_var = tk.StringVar(value="gemini")
        self.status_var = tk.StringVar(value="Ready")
        self.transcript_var = tk.StringVar(value="")

        self.create_widgets()
        self.toggle_method_ui()

    def create_widgets(self):
        header_frame = ttk.Frame(self, padding="16 12 16 8")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="Google TTS & Translation Studio", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="100% Free", font=("Segoe UI", 9, "bold"), foreground="#137333").pack(side=tk.RIGHT)

        method_frame = ttk.LabelFrame(self, text="Select Engine", padding="12")
        method_frame.pack(fill=tk.X, padx=16, pady=4)

        ttk.Radiobutton(
            method_frame, text="✨ Google Gemini TTS (30 Lifelike Voices + Emotional Direction)",
            variable=self.method_var, value="gemini", command=self.toggle_method_ui
        ).pack(anchor=tk.W, pady=2)

        ttk.Radiobutton(
            method_frame, text="🌍 Gemini 3.5 Live Translate (Speech-to-Speech Real-Time Translation)",
            variable=self.method_var, value="translate", command=self.toggle_method_ui
        ).pack(anchor=tk.W, pady=2)

        ttk.Radiobutton(
            method_frame, text="🌐 gTTS (Google Translate Standard - 100+ Languages)",
            variable=self.method_var, value="gtts", command=self.toggle_method_ui
        ).pack(anchor=tk.W, pady=2)

        text_frame = ttk.LabelFrame(self, text="Input Text", padding="12")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        self.text_box = tk.Text(text_frame, wrap=tk.WORD, font=("Segoe UI", 10), height=5)
        self.text_box.pack(fill=tk.BOTH, expand=True)
        self.text_box.insert(tk.END, "Good morning, welcome to our office!")

        preset_frame = ttk.Frame(text_frame)
        preset_frame.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(preset_frame, text="English", command=lambda: self.set_text("Good morning, welcome to our office!")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="News", command=lambda: self.set_text("Good evening. Researchers announced significant breakthroughs in speech AI.")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Spanish", command=lambda: self.set_text("¡Hola! Bienvenidos a nuestra oficina.")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Chinese", command=lambda: self.set_text("早上好，欢迎光临我们的办公室！")).pack(side=tk.LEFT, padx=2)

        self.params_frame = ttk.LabelFrame(self, text="Parameters", padding="12")
        self.params_frame.pack(fill=tk.X, padx=16, pady=4)

        # 1. Gemini TTS panel
        self.gemini_subframe = ttk.Frame(self.params_frame)
        ttk.Label(self.gemini_subframe, text="Voice:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.voice_cb = ttk.Combobox(self.gemini_subframe, values=GEMINI_VOICES, state="readonly", width=35)
        self.voice_cb.current(0)
        self.voice_cb.grid(row=0, column=1, sticky=tk.W, padx=8, pady=4)

        ttk.Label(self.gemini_subframe, text="Style / Tone:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.style_entry = ttk.Entry(self.gemini_subframe, width=38)
        self.style_entry.insert(0, "Energetic and cheerful")
        self.style_entry.grid(row=1, column=1, sticky=tk.W, padx=8, pady=4)

        # 2. Live Translate panel
        self.translate_subframe = ttk.Frame(self.params_frame)
        ttk.Label(self.translate_subframe, text="Translate Speech Into:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.target_cb = ttk.Combobox(
            self.translate_subframe,
            values=[f"{name} [{code}]" for name, code in TRANSLATE_TARGETS],
            state="readonly",
            width=35
        )
        self.target_cb.current(0)  # Spanish default
        self.target_cb.grid(row=0, column=1, sticky=tk.W, padx=8, pady=4)

        ttk.Label(self.translate_subframe, text="Model: gemini-3.5-live-translate-preview", foreground="#1a73e8").grid(row=1, column=1, sticky=tk.W, padx=8, pady=4)

        # 3. gTTS panel
        self.gtts_subframe = ttk.Frame(self.params_frame)
        ttk.Label(self.gtts_subframe, text="Language:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.lang_cb = ttk.Combobox(self.gtts_subframe, values=[f"{name} ({code})" for name, code in GTTS_LANGS], state="readonly", width=30)
        self.lang_cb.current(0)
        self.lang_cb.grid(row=0, column=1, sticky=tk.W, padx=8, pady=4)

        ttk.Label(self.gtts_subframe, text="Accent (TLD):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.tld_cb = ttk.Combobox(self.gtts_subframe, values=["com (US)", "co.uk (UK)", "com.au (Australia)", "co.in (India)", "ca (Canada)"], state="readonly", width=30)
        self.tld_cb.current(0)
        self.tld_cb.grid(row=1, column=1, sticky=tk.W, padx=8, pady=4)

        self.slow_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.gtts_subframe, text="Speak slowly", variable=self.slow_var).grid(row=2, column=1, sticky=tk.W, padx=8, pady=4)

        # Action Buttons
        action_frame = ttk.Frame(self, padding="16 8")
        action_frame.pack(fill=tk.X)

        self.btn_synth = ttk.Button(action_frame, text="🔊 Synthesize & Play Audio", command=self.on_synthesize)
        self.btn_synth.pack(fill=tk.X, ipady=6)

        # Transcript display label
        self.transcript_lbl = ttk.Label(self, textvariable=self.transcript_var, font=("Segoe UI", 10, "italic"), wraplength=660, foreground="#1a73e8")
        self.transcript_lbl.pack(padx=16, pady=4, anchor=tk.W)

        # Status Bar
        status_bar = ttk.Frame(self, padding="16 4 16 12")
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(status_bar, textvariable=self.status_var, font=("Segoe UI", 9), foreground="#5f6368").pack(anchor=tk.W)

    def set_text(self, text):
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, text)

    def toggle_method_ui(self):
        method = self.method_var.get()
        self.gemini_subframe.pack_forget()
        self.translate_subframe.pack_forget()
        self.gtts_subframe.pack_forget()

        if method == "gemini":
            self.gemini_subframe.pack(fill=tk.X)
            self.btn_synth.config(text="🔊 Synthesize Speech (Gemini)")
        elif method == "translate":
            self.translate_subframe.pack(fill=tk.X)
            self.btn_synth.config(text="🌍 Translate & Play Live Speech (Gemini 3.5)")
        else:
            self.gtts_subframe.pack(fill=tk.X)
            self.btn_synth.config(text="🔊 Synthesize Speech (gTTS)")

    def on_synthesize(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Empty Text", "Please enter some text.")
            return

        method = self.method_var.get()
        self.btn_synth.config(state=tk.DISABLED)
        self.status_var.set("Processing audio, please wait...")
        self.transcript_var.set("")

        threading.Thread(target=self._worker_synthesize, args=(method, text), daemon=True).start()

    def _worker_synthesize(self, method: str, text: str):
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if (method in ["gemini", "translate"]) and not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set.")

            if method == "gemini":
                voice_raw = self.voice_cb.get().split()[0]
                style = self.style_entry.get().strip()

                client = genai.Client(api_key=api_key)
                prompt = f"### DIRECTOR'S NOTES\nStyle: {style}\nTranscript:\n{text}" if style else text

                response = client.models.generate_content(
                    model=TTS_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_raw)
                            )
                        ),
                    ),
                )

                audio_bytes = b""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        audio_bytes += part.inline_data.data

                if not audio_bytes:
                    raise RuntimeError("No audio returned from Gemini.")

                out_file = OUTPUT_DIR / f"gemini_{voice_raw.lower()}_gui.wav"
                save_pcm_to_wav(audio_bytes, out_file)
                self.after(0, lambda: self.transcript_var.set(f"Synthesized: \"{text}\""))

            elif method == "translate":
                target_code = self.target_cb.get().split("[")[-1].strip("]")
                temp_src = OUTPUT_DIR / "gui_temp_src.mp3"
                temp_pcm = OUTPUT_DIR / "gui_temp_pcm.pcm"

                tts = gTTS(text=text, lang="en")
                tts.save(str(temp_src))
                convert_to_16k_pcm(temp_src, temp_pcm)

                client = genai.Client(api_key=api_key)
                config = types.LiveConnectConfig(
                    response_modalities=["AUDIO"],
                    input_audio_transcription=types.AudioTranscriptionConfig(),
                    output_audio_transcription=types.AudioTranscriptionConfig(),
                    translation_config=types.TranslationConfig(
                        target_language_code=target_code,
                        echo_target_language=True
                    )
                )

                pcm_bytes = temp_pcm.read_bytes()
                translated_audio = b""
                in_transcripts = []
                out_transcripts = []

                async def run_live():
                    nonlocal translated_audio
                    async with client.aio.live.connect(model=LIVE_TRANSLATE_MODEL, config=config) as session:
                        async def recv():
                            nonlocal translated_audio
                            try:
                                async for res in session.receive():
                                    sc = res.server_content
                                    if sc:
                                        if sc.input_transcription and sc.input_transcription.text:
                                            in_transcripts.append(sc.input_transcription.text)
                                        if sc.output_transcription and sc.output_transcription.text:
                                            out_transcripts.append(sc.output_transcription.text)
                                        if sc.model_turn:
                                            for part in sc.model_turn.parts:
                                                if hasattr(part, "inline_data") and part.inline_data:
                                                    translated_audio += part.inline_data.data
                            except Exception:
                                pass

                        task = asyncio.create_task(recv())
                        for i in range(0, len(pcm_bytes), 3200):
                            await session.send_realtime_input(
                                audio=types.Blob(data=pcm_bytes[i:i+3200], mime_type="audio/pcm;rate=16000")
                            )
                            await asyncio.sleep(0.08)
                        await asyncio.sleep(2.0)
                        task.cancel()

                asyncio.run(run_live())

                out_file = OUTPUT_DIR / f"gui_live_translate_{target_code}.wav"
                save_pcm_to_wav(translated_audio, out_file)
                trans_text = " ".join(out_transcripts)
                self.after(0, lambda: self.transcript_var.set(f"🌍 Translated Transcript: {trans_text}"))

            else:
                lang_raw = self.lang_cb.get().split("(")[-1].strip(")")
                tld_raw = self.tld_cb.get().split()[0]
                slow = self.slow_var.get()

                out_file = OUTPUT_DIR / f"gtts_{lang_raw}_gui.mp3"
                tts = gTTS(text=text, lang=lang_raw, tld=tld_raw, slow=slow)
                tts.save(str(out_file))
                self.after(0, lambda: self.transcript_var.set(f"Synthesized: \"{text}\""))

            self.after(0, lambda: self.status_var.set(f"[OK] Playing: {out_file.name} ({out_file.stat().st_size} bytes)"))
            play_audio_file(out_file)
            self.after(0, lambda: self.status_var.set(f"Completed: {out_file.name}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.status_var.set(f"Error: {e}"))
        finally:
            self.after(0, lambda: self.btn_synth.config(state=tk.NORMAL))


def main():
    app = TTSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
