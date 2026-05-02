"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from pathlib import Path
from textwrap import wrap

try:
    from .recommender import load_songs, recommend_songs
except ImportError:
    from recommender import load_songs, recommend_songs

_DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"


def _print_recommendation_table(recommendations: list) -> None:
    """Print recommendations as a simple ASCII table."""
    rank_width = 4
    title_width = 22
    score_width = 7
    reason_width = 70

    border = (
        "+"
        + "-" * (rank_width + 2)
        + "+"
        + "-" * (title_width + 2)
        + "+"
        + "-" * (score_width + 2)
        + "+"
        + "-" * (reason_width + 2)
        + "+"
    )

    print(border)
    print(
        f"| {'#':<{rank_width}} | {'Title':<{title_width}} | {'Score':<{score_width}} | {'Reason':<{reason_width}} |"
    )
    print(border)

    for index, rec in enumerate(recommendations, start=1):
        song, score, explanation = rec
        reason_lines = wrap(explanation, width=reason_width) or [""]
        print(
            f"| {index:<{rank_width}} | {song['title'][:title_width]:<{title_width}} | {score:<{score_width}.2f} | {reason_lines[0]:<{reason_width}} |"
        )
        for line in reason_lines[1:]:
            print(
                f"| {'':<{rank_width}} | {'':<{title_width}} | {'':<{score_width}} | {line:<{reason_width}} |"
            )
        print(border)


def main() -> None:
    songs = load_songs(str(_DATA_PATH))
    print(f"Loaded songs: {len(songs)}")

    profiles = {
        "High-Energy Pop": {
            "favorite_genre": "pop",
            "favorite_mood": "happy",
            "target_energy": 0.90,
            "target_tempo_bpm": 128,
            "target_valence": 0.82,
            "target_danceability": 0.84,
            "target_acousticness": 0.18,
        },
        "Chill Lofi": {
            "favorite_genre": "lofi",
            "favorite_mood": "chill",
            "target_energy": 0.35,
            "target_tempo_bpm": 78,
            "target_valence": 0.56,
            "target_danceability": 0.58,
            "target_acousticness": 0.80,
        },
        "Deep Intense Rock": {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 0.92,
            "target_tempo_bpm": 150,
            "target_valence": 0.42,
            "target_danceability": 0.62,
            "target_acousticness": 0.08,
        },
        "Conflicting Edge Case": {
            "favorite_genre": "jazz",
            "favorite_mood": "sad",
            "target_energy": 0.95,
            "target_tempo_bpm": 60,
            "target_valence": 0.20,
            "target_danceability": 0.20,
            "target_acousticness": 0.95,
        },
    }

    for profile_name, user_profile in profiles.items():
        user_prefs = {
            "genre": user_profile["favorite_genre"],
            "mood": user_profile["favorite_mood"],
            "energy": user_profile["target_energy"],
            "tempo_bpm": user_profile["target_tempo_bpm"],
            "valence": user_profile["target_valence"],
            "danceability": user_profile["target_danceability"],
            "acousticness": user_profile["target_acousticness"],
        }

        recommendations = recommend_songs(user_prefs, songs, k=5)

        print(f"\n=== {profile_name} ===\n")
        _print_recommendation_table(recommendations)


if __name__ == "__main__":
    main()
