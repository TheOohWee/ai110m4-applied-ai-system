"""
VibeFinder evaluation harness.
Runs predefined test cases and reports pass/fail with confidence scores.

Usage:
    python scripts/eval_harness.py           # recommender + agent tests
    python scripts/eval_harness.py --no-api  # recommender tests only
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.recommender import load_songs, recommend_songs

DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

# ── Recommender test cases (no API required) ──────────────────────────────────

RECOMMENDER_CASES = [
    {
        "id": "REC-01",
        "name": "High-energy pop returns pop top result",
        "prefs": {
            "genre": "pop", "mood": "happy", "energy": 0.9,
            "tempo_bpm": 128, "valence": 0.85, "danceability": 0.85, "acousticness": 0.15,
        },
        "expect_top_genre": "pop",
        "expect_top_energy_min": 0.7,
    },
    {
        "id": "REC-02",
        "name": "Chill lofi returns lofi top result",
        "prefs": {
            "genre": "lofi", "mood": "chill", "energy": 0.4,
            "tempo_bpm": 78, "valence": 0.58, "danceability": 0.58, "acousticness": 0.80,
        },
        "expect_top_genre": "lofi",
        "expect_top_energy_max": 0.5,
    },
    {
        "id": "REC-03",
        "name": "Intense rock returns rock top result",
        "prefs": {
            "genre": "rock", "mood": "intense", "energy": 0.9,
            "tempo_bpm": 150, "valence": 0.4, "danceability": 0.6, "acousticness": 0.1,
        },
        "expect_top_genre": "rock",
        "expect_top_energy_min": 0.8,
    },
    {
        "id": "REC-04",
        "name": "Returns exactly k=3 results",
        "prefs": {
            "genre": "pop", "mood": "happy", "energy": 0.8,
            "tempo_bpm": 120, "valence": 0.8, "danceability": 0.8, "acousticness": 0.2,
        },
        "k": 3,
        "expect_count": 3,
    },
    {
        "id": "REC-05",
        "name": "Empty catalog returns empty list",
        "prefs": {
            "genre": "pop", "mood": "happy", "energy": 0.8,
            "tempo_bpm": 120, "valence": 0.8, "danceability": 0.8, "acousticness": 0.2,
        },
        "songs_override": [],
        "expect_count": 0,
    },
    {
        "id": "REC-06",
        "name": "Scores are in descending order",
        "prefs": {
            "genre": "edm", "mood": "euphoric", "energy": 0.92,
            "tempo_bpm": 128, "valence": 0.86, "danceability": 0.91, "acousticness": 0.08,
        },
        "check_ordering": True,
    },
]

# ── Agent test cases (require ANTHROPIC_API_KEY) ──────────────────────────────

AGENT_CASES = [
    {
        "id": "AGT-01",
        "query": "Something energetic for my morning workout",
        "expect_energy_min": 0.6,
        "expect_mood_in": ["intense", "happy", "confident", "euphoric", "aggressive", "playful"],
    },
    {
        "id": "AGT-02",
        "query": "Late night coding session, need to stay focused",
        "expect_energy_max": 0.65,
        "expect_mood_in": ["focused", "chill", "relaxed"],
    },
    {
        "id": "AGT-03",
        "query": "Road trip with friends, keep it fun and upbeat",
        "expect_energy_min": 0.6,
        "expect_mood_in": ["happy", "playful", "euphoric", "confident"],
    },
    {
        "id": "AGT-04",
        "query": "Rainy Sunday afternoon, feeling a bit nostalgic",
        "expect_energy_max": 0.65,
        "expect_mood_in": [
            "nostalgic", "melancholic", "reflective", "romantic", "relaxed", "moody",
        ],
    },
]


# ── Test runners ──────────────────────────────────────────────────────────────

def run_recommender_tests(songs: list) -> tuple[int, int, list]:
    passed, failed, results = 0, 0, []

    for tc in RECOMMENDER_CASES:
        tc_songs = tc.get("songs_override", songs)
        k = tc.get("k", 5)
        recs = recommend_songs(tc["prefs"], tc_songs, k=k)
        scores = [s for _, s, _ in recs]
        top = recs[0][0] if recs else None
        errors = []

        if "expect_count" in tc and len(recs) != tc["expect_count"]:
            errors.append(f"expected {tc['expect_count']} results, got {len(recs)}")

        if "expect_top_genre" in tc and top:
            if top["genre"].lower() != tc["expect_top_genre"].lower():
                errors.append(f"top genre={top['genre']!r}, expected {tc['expect_top_genre']!r}")

        if "expect_top_energy_min" in tc and top:
            if top["energy"] < tc["expect_top_energy_min"]:
                errors.append(f"top energy={top['energy']:.2f} < {tc['expect_top_energy_min']}")

        if "expect_top_energy_max" in tc and top:
            if top["energy"] > tc["expect_top_energy_max"]:
                errors.append(f"top energy={top['energy']:.2f} > {tc['expect_top_energy_max']}")

        if tc.get("check_ordering") and len(scores) > 1:
            if scores != sorted(scores, reverse=True):
                errors.append("scores not in descending order")

        status = "PASS" if not errors else "FAIL"
        (passed if status == "PASS" else failed).__class__  # type: ignore
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        results.append((tc["id"], tc["name"], status, errors, None))

    return passed, failed, results


def run_agent_tests(songs: list) -> tuple[int, int, list, float]:
    try:
        from src.agent import run_agent
    except ImportError as exc:
        print(f"  [skip] Could not import agent: {exc}")
        return 0, 0, [], 0.0

    passed, failed, results, confidences = 0, 0, [], []

    for tc in AGENT_CASES:
        try:
            result = run_agent(tc["query"], songs, k=5)
        except EnvironmentError as exc:
            print(f"  [skip] {tc['id']}: {exc}")
            return 0, 0, [], 0.0
        except Exception as exc:
            results.append((tc["id"], tc["query"][:40], "ERROR", [str(exc)], None))
            failed += 1
            continue

        prefs = result["preferences"]
        conf = result["confidence"]
        confidences.append(conf)
        errors = []

        if "expect_energy_min" in tc and prefs["energy"] < tc["expect_energy_min"]:
            errors.append(
                f"energy={prefs['energy']:.2f} < expected min {tc['expect_energy_min']}"
            )
        if "expect_energy_max" in tc and prefs["energy"] > tc["expect_energy_max"]:
            errors.append(
                f"energy={prefs['energy']:.2f} > expected max {tc['expect_energy_max']}"
            )
        if "expect_mood_in" in tc:
            valid = [m.lower() for m in tc["expect_mood_in"]]
            if prefs["mood"].lower() not in valid:
                errors.append(f"mood={prefs['mood']!r} not in expected set {tc['expect_mood_in']}")

        if not result["recommendations"]:
            errors.append("no recommendations returned")

        status = "PASS" if not errors else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        results.append((tc["id"], tc["query"][:40], status, errors, conf))

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return passed, failed, results, avg_conf


# ── Output helpers ────────────────────────────────────────────────────────────

def _print_section(title: str, passed: int, failed: int, rows: list) -> None:
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print(f"{'=' * 62}")
    for row in rows:
        tc_id, name, status, errors, conf = row
        mark = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "!")
        conf_str = f"  [conf={conf:.2f}]" if conf is not None else ""
        print(f"  [{mark}] {tc_id}: {name[:44]}{conf_str}")
        for err in errors:
            print(f"       → {err}")
    print(f"\n  {passed} passed  /  {failed} failed  /  {passed + failed} total")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="VibeFinder evaluation harness")
    parser.add_argument("--no-api", action="store_true", help="Skip agent tests")
    args = parser.parse_args()

    print("\nVibeFinder Evaluation Harness")
    print(f"Loading songs from {DATA_PATH} ...")
    songs = load_songs(str(DATA_PATH))
    print(f"Loaded {len(songs)} songs.\n")

    r_pass, r_fail, r_rows = run_recommender_tests(songs)
    _print_section("Recommender Tests  (no API required)", r_pass, r_fail, r_rows)

    a_pass = a_fail = 0
    if not args.no_api and os.getenv("ANTHROPIC_API_KEY"):
        a_pass, a_fail, a_rows, avg_conf = run_agent_tests(songs)
        _print_section("Agent Tests  (Claude API)", a_pass, a_fail, a_rows)
        if a_rows:
            print(f"  Average confidence score: {avg_conf:.2f}")
    else:
        print("\n  [skip] Agent tests skipped — set ANTHROPIC_API_KEY to enable.")

    total_pass = r_pass + a_pass
    total_fail = r_fail + a_fail
    print(f"\n{'=' * 62}")
    print(f"  OVERALL  {total_pass} passed  /  {total_fail} failed")
    print(f"{'=' * 62}\n")

    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
