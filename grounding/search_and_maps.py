"""
Google Gemini Real-Time Search Grounding
Connects Gemini directly to live Google Search with verified sources and citations.

Usage:
  python search_and_maps.py "What are the latest news updates about Google Gemini?"
  python search_and_maps.py "Who won the most recent European football championship?"
"""

import os
import sys
import argparse
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"


def run_search_grounding(query: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("=" * 65)
    print("Google Gemini Search Grounding (Live Web Retrieval)")
    print("=" * 65)
    print(f"Query: \"{query}\"")
    print(f"Model: {MODEL}")
    print("\nRetrieving live Google Search results and generating grounded answer...")

    response = client.models.generate_content(
        model=MODEL,
        contents=query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    print("\n--- Answer ---")
    print(response.text)

    # Print grounding citations and web sources
    candidate = response.candidates[0]
    if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
        meta = candidate.grounding_metadata
        if hasattr(meta, "grounding_chunks") and meta.grounding_chunks:
            print("\n--- Verified Web Sources & Citations ---")
            for i, chunk in enumerate(meta.grounding_chunks, 1):
                if hasattr(chunk, "web") and chunk.web:
                    print(f"[{i}] {chunk.web.title}")
                    print(f"    URL: {chunk.web.uri}")


def main():
    parser = argparse.ArgumentParser(
        description="Gemini Google Search Grounding CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python search_and_maps.py "What is the weather and current time in Tokyo?"
  python search_and_maps.py "What are the latest breakthroughs in AI voice synthesis?"
"""
    )
    parser.add_argument("query", nargs="?", default="What are the latest features announced for Google Gemini AI in 2026?", help="Search query")

    args = parser.parse_args()
    run_search_grounding(args.query)


if __name__ == "__main__":
    main()
