import unittest
import os
import json
from highscore_manager import load_highscores, save_highscores, add_highscore, HIGHSCORE_FILE, MAX_HIGHSCORES

class TestHighscoreManager(unittest.TestCase):

    def setUp(self):
        """Set up for each test. Ensures a clean state for HIGHSCORE_FILE."""
        # If HIGHSCORE_FILE exists, back it up or remove it
        if os.path.exists(HIGHSCORE_FILE):
            # For simplicity, we'll remove it. A more robust approach might back it up.
            os.remove(HIGHSCORE_FILE)

    def tearDown(self):
        """Clean up after each test."""
        # Remove the HIGHSCORE_FILE created during tests
        if os.path.exists(HIGHSCORE_FILE):
            os.remove(HIGHSCORE_FILE)

    def test_load_highscores_no_file(self):
        """Test loading highscores when the file does not exist."""
        self.assertEqual(load_highscores(), [])

    def test_load_highscores_empty_file(self):
        """Test loading highscores from an empty (but valid JSON) file."""
        save_highscores([]) # Create an empty list in the file
        self.assertEqual(load_highscores(), [])

    def test_load_highscores_invalid_json(self):
        """Test loading highscores from a file with invalid JSON."""
        with open(HIGHSCORE_FILE, 'w') as f:
            f.write("this is not json")
        self.assertEqual(load_highscores(), []) # Should return empty list and print warning

    def test_load_highscores_invalid_format(self):
        """Test loading highscores from a file with valid JSON but wrong structure."""
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump({"not_a": "list"}, f)
        self.assertEqual(load_highscores(), []) # Should return empty list

        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump([{"name": "test"}, {"score": 100}], f) # Missing score/name
        self.assertEqual(load_highscores(), [])


    def test_save_and_load_highscores(self):
        """Test saving and then loading highscores."""
        scores_to_save = [
            {"name": "Player1", "score": 100},
            {"name": "Player2", "score": 200}
        ]
        save_highscores(scores_to_save)
        loaded_scores = load_highscores()
        # Order might not be guaranteed by simple save/load, but content should match
        self.assertCountEqual(loaded_scores, scores_to_save)

    def test_add_highscore_empty_list(self):
        """Test adding a highscore to an empty list."""
        add_highscore("NewPlayer", 150)
        scores = load_highscores()
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0]["name"], "NewPlayer")
        self.assertEqual(scores[0]["score"], 150)

    def test_add_highscore_sorting(self):
        """Test that scores are correctly sorted after adding."""
        add_highscore("PlayerA", 100)
        add_highscore("PlayerB", 300)
        add_highscore("PlayerC", 200)
        scores = load_highscores()
        self.assertEqual(len(scores), 3)
        self.assertEqual(scores[0]["name"], "PlayerB")
        self.assertEqual(scores[0]["score"], 300)
        self.assertEqual(scores[1]["name"], "PlayerC")
        self.assertEqual(scores[1]["score"], 200)
        self.assertEqual(scores[2]["name"], "PlayerA")
        self.assertEqual(scores[2]["score"], 100)

    def test_add_highscore_limit(self):
        """Test that only the top MAX_HIGHSCORES are kept."""
        for i in range(MAX_HIGHSCORES + 5):
            add_highscore(f"Player{i}", (i + 1) * 10)

        scores = load_highscores()
        self.assertEqual(len(scores), MAX_HIGHSCORES)
        # Scores are (i+1)*10. 'i' ranges from 0 to MAX_HIGHSCORES + 4.
        # Highest score is for i = MAX_HIGHSCORES + 4, so score = (MAX_HIGHSCORES + 4 + 1) * 10 = (MAX_HIGHSCORES + 5) * 10.
        # Lowest score in the top MAX_HIGHSCORES:
        # The players are Player0, ..., Player(MAX_HIGHSCORES+4).
        # Top 10 scores are from players:
        # Player(MAX_HIGHSCORES+4), Player(MAX_HIGHSCORES+3), ..., Player( (MAX_HIGHSCORES+4) - (MAX_HIGHSCORES-1) )
        # which is Player(5) if MAX_HIGHSCORES=10.
        # Score for Player(5) is (5+1)*10 = 60.
        # So, scores[0]["score"] should be (MAX_HIGHSCORES + 5) * 10
        # scores[MAX_HIGHSCORES - 1]["score"] should be ( (MAX_HIGHSCORES + 5 - MAX_HIGHSCORES) + 1) * 10
        self.assertEqual(scores[0]["score"], (MAX_HIGHSCORES + 5) * 10)
        self.assertEqual(scores[MAX_HIGHSCORES - 1]["score"], ( (MAX_HIGHSCORES + 5 - MAX_HIGHSCORES) + 1) * 10)


    def test_add_highscore_update_existing_player(self):
        """Test updating an existing player's score if the new score is higher."""
        add_highscore("PlayerX", 500)
        add_highscore("PlayerX", 600) # Higher score
        scores = load_highscores()
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0]["name"], "PlayerX")
        self.assertEqual(scores[0]["score"], 600)

    def test_add_highscore_update_existing_player_lower_score(self):
        """Test that an existing player's score is not updated if the new score is lower."""
        add_highscore("PlayerY", 700)
        add_highscore("PlayerY", 650) # Lower score
        scores = load_highscores()
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0]["name"], "PlayerY")
        self.assertEqual(scores[0]["score"], 700)

    def test_add_highscore_fill_and_try_add_lower(self):
        """Test adding scores to fill the list, then adding a score that shouldn't make it."""
        for i in range(MAX_HIGHSCORES):
            add_highscore(f"TopPlayer{i}", 1000 - i * 10) # Scores from 1000 down to (1000 - (MAX_HIGHSCORES-1)*10)

        lowest_top_score = 1000 - (MAX_HIGHSCORES - 1) * 10
        add_highscore("LowPlayer", lowest_top_score - 50) # Score that shouldn't make it

        scores = load_highscores()
        self.assertEqual(len(scores), MAX_HIGHSCORES)
        found_low_player = False
        for score_entry in scores:
            if score_entry["name"] == "LowPlayer":
                found_low_player = True
                break
        self.assertFalse(found_low_player, "LowPlayer should not be in the top scores.")
        self.assertEqual(scores[MAX_HIGHSCORES-1]['score'], lowest_top_score)

    def test_add_highscore_invalid_inputs(self):
        """Test adding highscores with invalid inputs (e.g., empty name, non-numeric score)."""
        # These should be handled gracefully by add_highscore, possibly by printing an error and not modifying scores.
        initial_scores = load_highscores() # Should be empty

        add_highscore("", 100) # Empty name
        self.assertEqual(load_highscores(), initial_scores, "Empty name should not add a score.")

        add_highscore("   ", 200) # Whitespace name
        self.assertEqual(load_highscores(), initial_scores, "Whitespace name should not add a score.")

        add_highscore("ValidName", "not_a_score") # Non-numeric score
        self.assertEqual(load_highscores(), initial_scores, "Non-numeric score should not add a score.")


if __name__ == '__main__':
    unittest.main()
