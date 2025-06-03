import json
import os

HIGHSCORE_FILE = "highscores.json"
MAX_HIGHSCORES = 10

def load_highscores():
    """Loads highscores from the JSON file.

    Returns:
        list: A list of highscore entries (dictionaries with "name" and "score").
              Returns an empty list if the file doesn't exist or is invalid.
    """
    if not os.path.exists(HIGHSCORE_FILE):
        return []
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            scores = json.load(f)
        # Basic validation: check if it's a list of dicts with 'name' and 'score'
        if isinstance(scores, list) and all(
            isinstance(entry, dict) and "name" in entry and "score" in entry
            for entry in scores
        ):
            return scores
        else:
            # Invalid format, treat as empty or corrupted
            print(f"Warning: {HIGHSCORE_FILE} has an invalid format. Starting with empty scores.")
            return []
    except json.JSONDecodeError:
        print(f"Warning: {HIGHSCORE_FILE} is corrupted or not valid JSON. Starting with empty scores.")
        return []
    except Exception as e:
        print(f"Error loading highscores: {e}. Starting with empty scores.")
        return []

def save_highscores(scores):
    """Saves the list of highscore entries to the JSON file.

    Args:
        scores (list): A list of highscore entries to save.
    """
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(scores, f, indent=4)
    except Exception as e:
        print(f"Error saving highscores: {e}")

def add_highscore(name, score):
    """Adds a new highscore entry, keeps the list sorted and limited to MAX_HIGHSCORES.

    Args:
        name (str): The name of the player.
        score (int): The score achieved by the player.
    """
    if not isinstance(name, str) or not name.strip():
        print("Error adding highscore: Player name cannot be empty.")
        return
    if not isinstance(score, (int, float)): # Allow float in case scores can be non-integers
        print("Error adding highscore: Score must be a number.")
        return

    current_scores = load_highscores()

    # Check if player already has a score and if the new one is higher
    existing_player_score_index = -1
    for i, entry in enumerate(current_scores):
        if entry.get("name") == name:
            existing_player_score_index = i
            break

    if existing_player_score_index != -1:
        if score > current_scores[existing_player_score_index]["score"]:
            current_scores[existing_player_score_index]["score"] = score
            print(f"Updated highscore for {name} to {score}.")
        else:
            print(f"New score {score} for {name} is not higher than existing score {current_scores[existing_player_score_index]['score']}. Not updating.")
            # No need to re-sort or save if only an existing score was lower or equal
            return
    else:
        current_scores.append({"name": name, "score": score})
        print(f"Added new highscore for {name}: {score}.")

    # Sort scores in descending order by score
    current_scores.sort(key=lambda x: x["score"], reverse=True)

    # Keep only the top MAX_HIGHSCORES
    updated_scores = current_scores[:MAX_HIGHSCORES]

    save_highscores(updated_scores)
    print(f"Highscores updated. Top {len(updated_scores)} scores saved.")

if __name__ == '__main__':
    # Example usage and basic testing
    print("Testing highscore manager...")
    # Clear existing scores for a clean test
    if os.path.exists(HIGHSCORE_FILE):
        os.remove(HIGHSCORE_FILE)

    add_highscore("Player1", 100)
    add_highscore("Player2", 200)
    add_highscore("Player3", 50)
    add_highscore("Player1", 150) # Update Player1's score

    print("\nFinal scores after initial adds:")
    for s in load_highscores():
        print(s)

    # Add more scores to test MAX_HIGHSCORES limit
    for i in range(4, 15):
        add_highscore(f"Player{i}", i * 10)

    print("\nFinal scores after exceeding MAX_HIGHSCORES:")
    final_scores = load_highscores()
    for s in final_scores:
        print(s)

    assert len(final_scores) == MAX_HIGHSCORES
    assert final_scores[0]["score"] >= final_scores[1]["score"]
    print(f"Number of scores: {len(final_scores)}")
    print("Test completed.")
    # Clean up the test file
    # if os.path.exists(HIGHSCORE_FILE):
    #     os.remove(HIGHSCORE_FILE)
