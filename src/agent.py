"""
VibeFinder AI Agent — multi-step pipeline powered by Gemini.

Flow:
  Step 1 — Gemini parses NL query → structured preferences (JSON)
  Step 2 — optional refinement if confidence < 0.6
  Step 3 — rule-based recommender: structured prefs → ranked songs
  Step 4 — Gemini generates natural language explanation
"""

import json
import logging
import os
import re
from pathlib import Path

import google.generativeai as genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from .recommender import recommend_songs
except ImportError:
    from recommender import recommend_songs

_log_dir = Path(__file__).parent.parent / "logs"
_log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_log_dir / "agent.log"),
    ],
)
logger = logging.getLogger(__name__)

CONFIDENCE_REFINE_THRESHOLD = 0.6

_GENRES = "pop, lofi, rock, ambient, jazz, indie pop, synthwave, hip hop, country, metal, r&b, edm, latin, classical, folk"
_MOODS  = "happy, chill, intense, relaxed, focused, moody, confident, melancholic, aggressive, romantic, euphoric, nostalgic, playful, reflective"

_EXTRACT_PROMPT = """\
You are a music preference parser. Extract structured audio preferences from this request:

"{query}"

{extra}

Return a JSON object with EXACTLY these fields (no extra text, no markdown fences):
{{
  "genre":        "<one of: {genres}>",
  "mood":         "<one of: {moods}>",
  "energy":       <float 0.0-1.0>,
  "tempo_bpm":    <float 60-180>,
  "valence":      <float 0.0-1.0>,
  "danceability": <float 0.0-1.0>,
  "acousticness": <float 0.0-1.0>,
  "confidence":   <float 0.0-1.0>,
  "reasoning":    "<1-2 sentences explaining your interpretation>"
}}\
"""

_EXPLAIN_PROMPT = """\
A user asked: "{query}"

The top song recommendations are:
{rec_lines}

Write a warm, 2-3 sentence response introducing the top 2-3 songs and why they fit the request. \
Be friendly and conversational — like a music-savvy friend texting back.\
"""


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text.strip())


def _extract(model, query: str, extra: str = "") -> dict:
    prompt = _EXTRACT_PROMPT.format(
        query=query, extra=extra, genres=_GENRES, moods=_MOODS
    )
    response = model.generate_content(prompt)
    return _parse_json(response.text)


def run_agent(query: str, songs: list, k: int = 5) -> dict:
    """
    Run the full agent pipeline on a natural language query.

    Returns a dict with:
      query, preferences, confidence, reasoning, recommendations,
      explanation, steps
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY not set. Add it to your .env file."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    steps: list[dict] = []
    logger.info("Agent query: %r", query)

    # Step 1 — extract preferences
    prefs = _extract(model, query)
    conf = float(prefs.get("confidence", 1.0))
    steps.append({
        "step": 1,
        "action": "extract_music_preferences",
        "result": {f: prefs[f] for f in prefs if f != "reasoning"},
    })
    logger.info(
        "Extracted: genre=%s mood=%s energy=%.2f confidence=%.2f",
        prefs["genre"], prefs["mood"], prefs["energy"], conf,
    )

    # Step 2 — optional refinement
    if conf < CONFIDENCE_REFINE_THRESHOLD:
        logger.info("Low confidence (%.2f) — refining", conf)
        extra = (
            f"Your previous extraction had confidence {conf:.2f}. "
            "Reconsider: what genre and mood most likely match the underlying intent?"
        )
        prefs = _extract(model, query, extra=extra)
        conf = float(prefs.get("confidence", conf))
        steps.append({
            "step": 2,
            "action": "refine_preferences",
            "result": {f: prefs[f] for f in prefs if f != "reasoning"},
        })
        logger.info(
            "Refined: genre=%s mood=%s energy=%.2f confidence=%.2f",
            prefs["genre"], prefs["mood"], prefs["energy"], conf,
        )

    # Step 3 — rule-based recommender
    fields = ["genre", "mood", "energy", "tempo_bpm", "valence", "danceability", "acousticness"]
    user_prefs = {f: prefs[f] for f in fields}
    recommendations = recommend_songs(user_prefs, songs, k=k)
    steps.append({
        "step": len(steps) + 1,
        "action": "run_recommender",
        "result": f"{len(recommendations)} songs retrieved",
    })
    logger.info("Recommender returned %d results", len(recommendations))

    if not recommendations:
        return {
            "query": query,
            "preferences": user_prefs,
            "confidence": conf,
            "reasoning": prefs.get("reasoning", ""),
            "recommendations": [],
            "explanation": "No matching songs found in the catalog.",
            "steps": steps,
        }

    # Step 4 — natural language explanation
    rec_lines = "\n".join(
        f'{i+1}. "{s["title"]}" by {s["artist"]} ({s["genre"]}, {s["mood"]}, energy={s["energy"]:.2f})'
        for i, (s, _, _) in enumerate(recommendations)
    )
    explanation = model.generate_content(
        _EXPLAIN_PROMPT.format(query=query, rec_lines=rec_lines)
    ).text.strip()
    steps.append({"step": len(steps) + 1, "action": "generate_explanation", "result": "done"})
    logger.info("Explanation generated")

    return {
        "query": query,
        "preferences": user_prefs,
        "confidence": conf,
        "reasoning": prefs.get("reasoning", ""),
        "recommendations": [
            {
                "title": s["title"], "artist": s["artist"],
                "genre": s["genre"], "mood": s["mood"],
                "score": round(score, 3), "explanation": expl,
            }
            for s, score, expl in recommendations
        ],
        "explanation": explanation,
        "steps": steps,
    }
