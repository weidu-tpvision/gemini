# Google Gemini Real-Time Search Grounding

Connect Google Gemini models directly to live Google Search to eliminate hallucinations, access real-time information, and provide verified source URLs and citations.

---

## Features
- **Real-Time Web Knowledge**: Answers questions about breaking news, live weather, sports, and current events.
- **Grounding Metadata & Citations**: Returns verified web sources with titles and URLs.
- **Powered by `gemini-2.5-flash`**: Fast, efficient, and 100% free under Google AI Studio tier.

---

## Usage

```powershell
# Default query:
& "$HOME\venv\google_tts\Scripts\python.exe" search_and_maps.py

# Custom live queries:
& "$HOME\venv\google_tts\Scripts\python.exe" search_and_maps.py "What is the current time and weather forecast in Amsterdam?"

& "$HOME\venv\google_tts\Scripts\python.exe" search_and_maps.py "What are the latest announcements regarding Google Gemini models?"

& "$HOME\venv\google_tts\Scripts\python.exe" search_and_maps.py "Who won the most recent Champions League match?"
```

---

## How It Works in Code

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Your query here",
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )
)

# Text response
print(response.text)

# Grounding metadata & web sources
candidate = response.candidates[0]
if candidate.grounding_metadata and candidate.grounding_metadata.grounding_chunks:
    for chunk in candidate.grounding_metadata.grounding_chunks:
        if chunk.web:
            print(f"- {chunk.web.title}: {chunk.web.uri}")
```
