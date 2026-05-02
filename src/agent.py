"""
VibeFinder AI Agent — multi-step agentic pipeline powered by Claude.

Flow:
  Step 1 — extract_music_preferences tool call: NL query → structured prefs
  Step 2 — optional refinement if confidence < 0.6
  Step 3 — rule-based recommender: structured prefs → ranked songs
  Step 4 — natural language explanation of results
"""

import logging
import os
from pathlib import Path

import anthropic

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

EXTRACT_TOOL = {
    "name": "extract_music_preferences",
    "description": (
        "Parse a natural language music request into structured audio feature preferences. "
        "Infer reasonable values from context clues: activity, time of day, mood, or explicit "
        "genre/style mentions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "genre": {
                "type": "string",
                "description": (
                    "Best-matching genre. Choose from: pop, lofi, rock, ambient, jazz, "
                    "indie pop, synthwave, hip hop, country, metal, r&b, edm, latin, "
                    "classical, folk"
                ),
            },
            "mood": {
                "type": "string",
                "description": (
                    "Best-matching mood. Choose from: happy, chill, intense, relaxed, "
                    "focused, moody, confident, melancholic, aggressive, romantic, "
                    "euphoric, nostalgic, playful, reflective"
                ),
            },
            "energy": {
                "type": "number",
                "description": "Energy level from 0.0 (very calm) to 1.0 (extremely energetic)",
            },
            "tempo_bpm": {
                "type": "number",
                "description": "Expected tempo in beats per minute (typical range 60–180)",
            },
            "valence": {
                "type": "number",
                "description": "Musical positivity 0.0 (sad/negative) to 1.0 (happy/positive)",
            },
            "danceability": {
                "type": "number",
                "description": "Suitability for dancing from 0.0 to 1.0",
            },
            "acousticness": {
                "type": "number",
                "description": "0.0 = fully electronic, 1.0 = fully acoustic",
            },
            "confidence": {
                "type": "number",
                "description": (
                    "Your confidence in this extraction 0.0–1.0. "
                    "Use lower values when the query is vague or ambiguous."
                ),
            },
            "reasoning": {
                "type": "string",
                "description": "One or two sentences explaining how you interpreted the query.",
            },
        },
        "required": [
            "genre", "mood", "energy", "tempo_bpm",
            "valence", "danceability", "acousticness",
            "confidence", "reasoning",
        ],
    },
}

_EXTRACT_PROMPT = (
    'A user wants music recommendations based on this request:\n\n"{query}"\n\n'
    "Use the extract_music_preferences tool to translate this into structured audio features."
)


def _extract(client: anthropic.Anthropic, query: str, extra_context: str = "") -> dict:
    content = _EXTRACT_PROMPT.format(query=query)
    if extra_context:
        content += f"\n\nAdditional context: {extra_context}"
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "required"},
        messages=[{"role": "user", "content": content}],
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return tool_block.input


def run_agent(query: str, songs: list, k: int = 5) -> dict:
    """
    Run the full agent pipeline on a natural language query.

    Returns a dict with:
      query, preferences, confidence, reasoning, recommendations,
      explanation, steps
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill in your key."
        )

    client = anthropic.Anthropic(api_key=api_key)
    steps: list[dict] = []
    logger.info("Agent query: %r", query)

    # Step 1: extract preferences
    prefs = _extract(client, query)
    conf = prefs.get("confidence", 1.0)
    steps.append({
        "step": 1,
        "action": "extract_music_preferences",
        "result": {k: v for k, v in prefs.items() if k != "reasoning"},
    })
    logger.info(
        "Extracted: genre=%s mood=%s energy=%.2f confidence=%.2f",
        prefs["genre"], prefs["mood"], prefs["energy"], conf,
    )

    # Step 2: optional refinement
    if conf < CONFIDENCE_REFINE_THRESHOLD:
        logger.info("Low confidence (%.2f) — refining", conf)
        context = (
            f"Your previous extraction had confidence {conf:.2f}. "
            "Reconsider carefully — what genre and mood most likely match the underlying intent?"
        )
        prefs = _extract(client, query, extra_context=context)
        conf = prefs.get("confidence", conf)
        steps.append({
            "step": 2,
            "action": "refine_preferences",
            "result": {k: v for k, v in prefs.items() if k != "reasoning"},
        })
        logger.info(
            "Refined: genre=%s mood=%s energy=%.2f confidence=%.2f",
            prefs["genre"], prefs["mood"], prefs["energy"], conf,
        )

    # Step 3: rule-based recommender
    user_prefs = {
        "genre": prefs["genre"],
        "mood": prefs["mood"],
        "energy": prefs["energy"],
        "tempo_bpm": prefs["tempo_bpm"],
        "valence": prefs["valence"],
        "danceability": prefs["danceability"],
        "acousticness": prefs["acousticness"],
    }
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

    # Step 4: natural language explanation
    rec_lines = "\n".join(
        f'{i + 1}. "{s["title"]}" by {s["artist"]} '
        f"({s['genre']}, {s['mood']}, energy={s['energy']:.2f})"
        for i, (s, _, _) in enumerate(recommendations)
    )
    explanation_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": (
                    f'User asked: "{query}"\n\n'
                    f"Top {len(recommendations)} recommendations:\n{rec_lines}\n\n"
                    "Write a warm, 2–3 sentence response that introduces the top 2–3 songs "
                    "and explains why they fit. Be friendly and conversational."
                ),
            }
        ],
    )
    explanation = explanation_response.content[0].text
    steps.append({"step": len(steps) + 1, "action": "generate_explanation", "result": "done"})
    logger.info("Explanation generated")

    return {
        "query": query,
        "preferences": user_prefs,
        "confidence": conf,
        "reasoning": prefs.get("reasoning", ""),
        "recommendations": [
            {
                "title": s["title"],
                "artist": s["artist"],
                "genre": s["genre"],
                "mood": s["mood"],
                "score": round(score, 3),
                "explanation": expl,
            }
            for s, score, expl in recommendations
        ],
        "explanation": explanation,
        "steps": steps,
    }
