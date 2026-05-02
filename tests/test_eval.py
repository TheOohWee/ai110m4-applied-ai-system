"""
Functional tests for VibeFinder AI system.
Covers: song loading, numeric correctness, edge cases, sort ordering.
No API key required.
"""

from pathlib import Path
import pytest
from src.recommender import load_songs, recommend_songs

DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"


class TestLoadSongs:
    def test_loads_expected_count(self):
        assert len(load_songs(str(DATA_PATH))) == 18

    def test_numeric_fields_are_floats(self):
        for song in load_songs(str(DATA_PATH)):
            for field in ("energy", "tempo_bpm", "valence", "danceability", "acousticness"):
                assert isinstance(song[field], float), f"{field} should be float"

    def test_all_required_keys_present(self):
        required = {
            "id", "title", "artist", "genre", "mood",
            "energy", "tempo_bpm", "valence", "danceability", "acousticness",
        }
        for song in load_songs(str(DATA_PATH)):
            assert required.issubset(song.keys())

    def test_energy_values_in_range(self):
        for song in load_songs(str(DATA_PATH)):
            assert 0.0 <= song["energy"] <= 1.0


class TestRecommendSongs:
    @pytest.fixture(autouse=True)
    def songs(self):
        self._songs = load_songs(str(DATA_PATH))

    def _prefs(self, genre="pop", mood="happy", energy=0.8, bpm=120,
               valence=0.8, dance=0.8, acoustic=0.2):
        return {
            "genre": genre, "mood": mood, "energy": energy,
            "tempo_bpm": bpm, "valence": valence,
            "danceability": dance, "acousticness": acoustic,
        }

    def test_returns_k_results(self):
        recs = recommend_songs(self._prefs(), self._songs, k=3)
        assert len(recs) == 3

    def test_results_sorted_descending(self):
        recs = recommend_songs(self._prefs(genre="rock", mood="intense", energy=0.9), self._songs)
        scores = [s for _, s, _ in recs]
        assert scores == sorted(scores, reverse=True)

    def test_genre_match_favors_matching_songs(self):
        recs = recommend_songs(self._prefs(genre="lofi", mood="chill", energy=0.4), self._songs, k=1)
        assert recs[0][0]["genre"].lower() == "lofi"

    def test_empty_songs_returns_empty(self):
        assert recommend_songs(self._prefs(), [], k=5) == []

    def test_k_zero_returns_empty(self):
        assert recommend_songs(self._prefs(), self._songs, k=0) == []

    def test_explanation_is_non_empty_string(self):
        recs = recommend_songs(self._prefs(), self._songs, k=1)
        _, _, expl = recs[0]
        assert isinstance(expl, str) and expl.strip()

    def test_result_tuple_has_three_elements(self):
        recs = recommend_songs(self._prefs(), self._songs, k=2)
        for item in recs:
            assert len(item) == 3
