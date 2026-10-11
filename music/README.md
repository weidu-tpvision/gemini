# Google Lyria Music Generation

Generate 44.1 kHz high-fidelity stereo audio, background loops, soundscapes, and full songs using **Google Lyria 3.5** (`lyria-3.5-clip-preview` and `lyria-3.5-pro-preview`).

---

## Features
- **Instrumental & Vocal Composition**: Direct instruments (guitar, synth, piano, orchestral brass, drums) and musical styles.
- **Structural Tags**: Direct the song structure with tags like `[Intro]`, `[Verse]`, `[Chorus]`, and `[Outro]`.
- **Formats**: Outputs 44.1 kHz stereo `.mp3` files.
- **Instant Playback**: Automatically play via `ffplay` with `--play / -p`.

---

## Usage

```powershell
# 30-Second Ambient Lo-Fi Track:
& "$HOME\venv\google_tts\Scripts\python.exe" generate_music.py -p "Relaxing lo-fi hip hop beat with smooth Rhodes piano, mellow guitar chords, and warm vinyl crackle" --play

# Energetic Synthwave Track:
& "$HOME\venv\google_tts\Scripts\python.exe" generate_music.py -p "Upbeat 128 BPM retro 80s synthwave with punchy drums, arpeggiated bassline, and warm analog synthesizers" -p

# Full-Length Structured Song:
& "$HOME\venv\google_tts\Scripts\python.exe" generate_music.py --full -p "An epic fantasy cinematic orchestral soundtrack starting with flute and building into massive brass and battle drums"
```
