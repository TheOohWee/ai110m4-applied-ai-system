# 🎵 Music Recommender Simulation

## Project Summary

This project is a rule-based music recommender built for classroom exploration. It reads a small song catalog and ranks songs using user preferences for genre, mood, and energy. The system is designed to be easy to understand, test, and explain, with score reasons shown for every recommendation.

I evaluated the recommender with multiple user profiles, including edge cases, and documented observed behavior, bias risks, and improvement ideas in the model card.

## Evaluation Screenshots

These screenshots show the terminal output from the profile stress test. They reflect the temporary experiment where energy was weighted more strongly than genre.

### High-Energy Pop

![High-Energy Pop terminal output](image1.png)

### Chill Lofi

![Chill Lofi terminal output](image2.png)

### Deep Intense Rock

![Deep Intense Rock terminal output](image3.png)

### Conflicting Edge Case

![Conflicting Edge Case terminal output](image4.png)

---

## How The System Works

This recommender follows a simple input -> score -> rank pipeline.

### Features Used

Each song includes metadata (`title`, `artist`, `genre`, `mood`) and numeric audio features (`energy`, `tempo_bpm`, `valence`, `danceability`, `acousticness`).

The active scoring recipe uses:

1. `genre` (categorical match)
2. `mood` (categorical match)
3. `energy` (numeric closeness to user target)

### User Profile

The user profile dictionary stores target preferences, for example:

1. `favorite_genre`
2. `favorite_mood`
3. `target_energy`

These are mapped into the scoring inputs (`genre`, `mood`, `energy`) when recommendations are generated.

### Finalized Algorithm Recipe

1. Load songs from `data/songs.csv`.
2. For each song, initialize score to 0.
3. Add `+2.0` if song genre matches user favorite genre.
4. Add `+1.0` if song mood matches user favorite mood.
5. Add energy similarity points in `[0, 1]` based on closeness to user target energy.
6. Store `(song, score, explanation)`.
7. After all songs are scored, sort by score descending.
8. Return top `k` songs.

Scoring equation:

Final Score = Genre Match Points + Mood Match Points + Energy Similarity Points

Energy similarity is computed with normalized distance:

Energy Similarity Points = 1 - |e_song - e_target| / energy range in dataset

### Potential Bias Note

This system can over-prioritize whichever feature has the biggest weight. In the baseline recipe, genre can dominate the score, which may hide songs that match the user's mood and energy but not the genre. In the temporary experiment run, energy became stronger, so intense songs could rise even when the genre or mood was only a partial match. In both cases, the model still ignores other useful signals like tempo, danceability, and artist diversity.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments Tried

I ran a sensitivity experiment where energy mattered more than genre. That changed the ranking order for mixed profiles and made high-energy songs rise faster even when the genre did not match perfectly.

The biggest difference showed up for the conflicting profile: even though the genre and mood were unusual, the recommender still pushed energetic songs near the top. That told me the score is reacting strongly to energy and can be steered by one feature when the weights are changed.

---

## Limitations and Risks

The recommender only sees a tiny catalog, so it can repeat the same songs for different users. It does not understand lyrics, artist relationships, or whether two moods are related in a subtle way. Because the experiment gave energy extra weight, it can also over-favor songs that feel intense even when the user's genre or mood is a better clue.

You will go deeper on this in the model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this

See [reflection.md](reflection.md) for the pair-by-pair comparison notes.

See [reflection.md](reflection.md) for the profile-by-profile comparison notes.


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card: Music Recommender Simulation

## Model Name

AmirVibe 1.0

## Goal

This system suggests songs a user might like from a small catalog. It uses user preferences to rank songs and return the top results.

## Data Used

The dataset has 18 songs from `data/songs.csv`. Each song has genre, mood, energy, tempo, valence, danceability, and acousticness. The dataset is small, so some tastes are missing or only appear once.

## Algorithm Summary

The recommender gives points for matching genre and matching mood. It also gives energy similarity points based on how close song energy is to the user's target energy. The total score is the sum of those parts, and songs are sorted from highest to lowest score.

## Observed Behavior / Biases

The system is sensitive to feature weights. In the experiment where energy was emphasized, high-energy songs often rose even with weaker genre match. With a small catalog, some songs repeat across profiles, which can create a filter-bubble effect. Conflicting profiles can produce only partial matches because the model has to prioritize one signal over others.

## Evaluation Process

I tested four profiles: High-Energy Pop, Chill Lofi, Deep Intense Rock, and a Conflicting Edge Case. I compared the top 5 recommendations and checked whether they matched intuition. I also ran a sensitivity experiment by increasing energy importance and reducing genre importance to see how rankings changed. Terminal screenshots were saved as `image1.png` to `image4.png`.

## Intended Use and Non-Intended Use

Intended use: classroom exploration of recommendation logic and model documentation.

Non-intended use: real production music recommendations, high-stakes decisions, or personalization for real users.

## Ideas for Improvement

1. Add more songs and better balance across genres and moods.
2. Add diversity rules so the same artist does not appear too often.
3. Use more features in scoring (tempo, valence, danceability, acousticness) with tuned weights.

## Personal Reflection

My biggest learning moment was seeing how a small weight change can completely reshape the ranked list. AI tools helped me move faster when writing and revising code, but I still had to double-check scoring math and outputs in the terminal. I was surprised that a simple rule-based system can still feel "smart" when the profile and dataset line up well. If I extend this project, I would add automatic weight tuning, more diverse data, and clearer explanation outputs for each recommendation.
