# Google Veo Video Generation

Generate cinematic, high-definition videos with natively synchronized audio using **Google Veo 3.1** (`veo-3.1-generate-preview`).

---

## Features
- **Text-to-Video**: Describe lighting, camera movement, scene details, and style.
- **Image-to-Video**: Supply an initial image frame to animate.
- **Synchronized Audio**: Automatically includes matched audio effects and background soundscapes.
- **Automatic Playback**: Preview generated `.mp4` videos immediately via `ffplay`.

---

## Usage

```powershell
# Text to Video:
& "$HOME\venv\google_tts\Scripts\python.exe" generate_video.py -p "Cinematic drone shot flying through a glowing bamboo forest in Kyoto at twilight" --play

# Fast 5-second action scene:
& "$HOME\venv\google_tts\Scripts\python.exe" generate_video.py -p "Futuristic hovercar racing through rainy neon city streets" -d 5 -p

# Image to Video:
& "$HOME\venv\google_tts\Scripts\python.exe" generate_video.py --image landscape.png -p "Golden sunset slowly descending as waves roll onto the beach"
```
