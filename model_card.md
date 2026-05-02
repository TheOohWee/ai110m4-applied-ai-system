# Model Card: VibeFinder AI

## Model Name

VibeFinder AI 2.0 — Claude-Augmented Music Recommendation System

## Base Model

`claude-sonnet-4-6` (Anthropic) via the Anthropic Python SDK with tool use

## Goal / Task

Translate natural language music requests into structured audio feature preferences, retrieve matching songs from an 18-track catalog using rule-based scoring, and return conversational recommendations with explanations.

## Data Used

- **Song catalog**: 18 curated tracks in `data/songs.csv` spanning 15 genres. Each entry includes genre, mood, energy (0–1), tempo (BPM), valence (0–1), danceability (0–1), and acousticness (0–1).
- **No fine-tuning**: The Claude model is used out-of-the-box. The system relies on in-context learning — the tool schema and prompt act as the only specialization mechanism.

## Algorithm Summary

Multi-step agentic pipeline:

1. **Extract** — Claude calls `extract_music_preferences` tool to parse NL query → structured preferences + confidence score
2. **Refine** — If confidence < 0.6, a second tool call re-extracts with a focused prompt
3. **Score** — Rule-based recommender: `genre_match (+1.0) + mood_match (+1.0) + energy_similarity (0–2.0)`, sorted descending
4. **Explain** — Claude generates a 2–3 sentence conversational summary of the top picks

## Observed Behavior and Biases

**Western genre bias**: The catalog and genre taxonomy are entirely Western-centric. Queries about K-pop, afrobeats, cumbia, or other global genres are silently mapped to the nearest Western analog. This is a meaningful limitation for any real-world use.

**Energy dominance**: The energy dimension carries twice the weight of genre or mood (0–2.0 vs. 1.0 each). High-energy queries produce reliably good results; mismatches on energy are hard to overcome with strong genre/mood matches.

**Catalog bottleneck**: With 18 songs, certain tracks (Neon Festival, Focus Flow, Starlit Sonatina) appear in almost every profile's top results. True personalization requires a much larger catalog.

**Confidence overconfidence**: In testing, Claude's self-reported confidence scores clustered between 0.80 and 0.95 even for vague queries. The 0.6 refinement threshold was rarely triggered, suggesting Claude is more decisive than its uncertainty actually warrants.

**Consistent genre-energy coupling**: Claude reliably maps "workout" → high energy (0.85+), "coding" → lofi/low energy (0.35–0.45), "rainy day" → classical or folk + low energy. These are reasonable heuristics but will fail for users whose preferences deviate from these cultural defaults.

## Evaluation Process

**Automated tests**: 13 pytest tests covering song loading, field types, score ordering, edge cases.

**Evaluation harness** (`scripts/eval_harness.py`):
- 6 deterministic recommender test cases — all pass, no API needed
- 4 natural language agent test cases — all pass when API key is set

**Harness results summary**:
```
Recommender Tests:  6/6 passed
Agent Tests:        4/4 passed  |  avg confidence: 0.87
```

**Manual exploration**: Four structured profiles run through the original simulation. Three natural language queries tested interactively via the CLI.

The system performed well when the query had a clear activity or emotional context. It struggled most with genre-ambiguous queries like "something mysterious and introspective," where genre mapping varied between runs.

## Intended Use and Non-Intended Use

**Intended**: Educational demonstration of hybrid AI system design (natural language understanding + deterministic retrieval + agentic reasoning). Portfolio artifact for the AI110 course.

**Not intended**: Production music recommendation, real user personalization, commercial use, or high-stakes decisions of any kind.

## AI Collaboration Reflection

### Helpful suggestion

When designing the preference extraction step, Claude (as coding assistant) suggested using `tool_choice={"type": "required"}` instead of `tool_choice={"type": "auto"}` to force the tool call on every invocation. This was exactly right — `"auto"` would allow Claude to sometimes generate a free-form text response instead of calling the tool, which would have broken the downstream recommender pipeline. Making the tool call mandatory made the system deterministic and eliminated a whole class of parsing failures.

### Flawed suggestion

Claude initially suggested adding a third tool — `evaluate_recommendations` — that would have Claude re-score each song and filter out any it considered "clearly wrong" before showing results to the user. I rejected this for two reasons: (1) it would add 1–2 extra API calls per query for marginal quality gains, and (2) it would introduce a second AI opinion that could conflict with the deterministic scorer in unpredictable ways. The rule-based layer is the right place to enforce objective quality criteria (the eval harness does this); letting Claude second-guess the scorer would undermine the hybrid design's main advantage — determinism.

## Ideas for Improvement

1. **Expand catalog** — 100+ songs with balanced genre/mood/energy coverage would dramatically reduce the bottleneck effect and filter-bubble risk.
2. **User feedback loop** — Let users rate results and adjust scoring weights over time (collaborative filtering on top of the rule-based foundation).
3. **Semantic retrieval** — Embed song descriptions as vectors and add cosine similarity search to complement numeric scoring (true RAG).
4. **Streaming output** — Stream Claude's explanation token-by-token so the CLI feels responsive during the multi-step inference pipeline.
5. **Calibrate confidence threshold** — With 18 songs the 0.6 threshold is almost never hit; raise to 0.75 or add a different signal (query length, hedge words) to trigger refinement.
