"""
Interactive CLI for VibeFinder AI.
Accepts natural language music requests and returns recommendations via the agent.

Usage:
    python -m src.cli
"""

import sys
from pathlib import Path
from textwrap import wrap

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from .agent import run_agent
    from .recommender import load_songs
except ImportError:
    from agent import run_agent
    from recommender import load_songs

DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"
MAX_QUERY_LEN = 500
LOW_CONF = 0.6


def _print_recs(recommendations: list) -> None:
    rk, tw, sw, rw = 4, 22, 7, 60
    border = (
        "+" + "-" * (rk + 2)
        + "+" + "-" * (tw + 2)
        + "+" + "-" * (sw + 2)
        + "+" + "-" * (rw + 2) + "+"
    )
    print(border)
    print(f"| {'#':<{rk}} | {'Title':<{tw}} | {'Score':<{sw}} | {'Reason':<{rw}} |")
    print(border)
    for i, rec in enumerate(recommendations, 1):
        lines = wrap(rec["explanation"], width=rw) or [""]
        print(
            f"| {i:<{rk}} | {rec['title'][:tw]:<{tw}} "
            f"| {rec['score']:<{sw}.3f} | {lines[0]:<{rw}} |"
        )
        for line in lines[1:]:
            print(f"| {'':<{rk}} | {'':<{tw}} | {'':<{sw}} | {line:<{rw}} |")
        print(border)


def main() -> None:
    songs = load_songs(str(DATA_PATH))
    print(f"\nVibeFinder AI — Natural Language Music Recommender")
    print(f"Catalog: {len(songs)} songs  |  Type your request below, or 'quit' to exit.\n")

    while True:
        try:
            query = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if len(query) > MAX_QUERY_LEN:
            print(f"[Error] Query too long (max {MAX_QUERY_LEN} chars). Please shorten it.")
            continue

        print("\n[Thinking...]\n")

        try:
            result = run_agent(query, songs, k=5)
        except EnvironmentError as exc:
            print(f"[Setup Error] {exc}")
            sys.exit(1)
        except Exception as exc:
            print(f"[Error] {exc}")
            continue

        conf = result["confidence"]
        prefs = result["preferences"]

        print(f"Interpretation (confidence: {conf:.0%})")
        if conf < LOW_CONF:
            print("  [!] Low confidence — the interpretation may not match your intent.")
        print(
            f"  Genre: {prefs['genre']} | Mood: {prefs['mood']} | "
            f"Energy: {prefs['energy']:.2f} | Tempo: {prefs['tempo_bpm']:.0f} BPM"
        )
        if result.get("reasoning"):
            print(f"  Reasoning: {result['reasoning']}")

        if len(result.get("steps", [])) > 3:
            print("  Agent steps: included refinement pass (low confidence on first attempt)")

        print()
        if result["recommendations"]:
            _print_recs(result["recommendations"])
        else:
            print("No matching songs found in catalog.")

        print(f"\n{result['explanation']}\n")
        print("-" * 80)


if __name__ == "__main__":
    main()
