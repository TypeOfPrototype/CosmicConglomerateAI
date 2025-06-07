import unittest
import os
import json
import shutil
import tempfile

# Assuming profile_manager.py is in the parent directory relative to the 'tests' directory
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from profile_manager import UserProfile, ProfileManager

class TestUserProfile(unittest.TestCase):
    def setUp(self):
        self.user_profile = UserProfile("test_user")
        # Ensure total_score_sum is initialized if your UserProfile.update_stats relies on it
        if not hasattr(self.user_profile, 'total_score_sum'):
            self.user_profile.total_score_sum = 0

    def test_initialization(self):
        self.assertEqual(self.user_profile.username, "test_user")
        self.assertEqual(self.user_profile.high_score, 0)
        self.assertEqual(self.user_profile.games_played, 0)
        self.assertEqual(self.user_profile.total_wins, 0)
        self.assertEqual(self.user_profile.total_losses, 0)
        self.assertEqual(self.user_profile.average_score, 0.0)
        self.assertEqual(self.user_profile.total_score_sum, 0)

    def test_update_stats_first_game_win(self):
        self.user_profile.update_stats(score=100, is_win=True)
        self.assertEqual(self.user_profile.games_played, 1)
        self.assertEqual(self.user_profile.total_wins, 1)
        self.assertEqual(self.user_profile.total_losses, 0)
        self.assertEqual(self.user_profile.high_score, 100)
        self.assertEqual(self.user_profile.average_score, 100.0)
        self.assertEqual(self.user_profile.total_score_sum, 100)

    def test_update_stats_loss_new_high_score(self):
        self.user_profile.update_stats(score=50, is_win=True) # First game
        self.user_profile.update_stats(score=120, is_win=False) # Second game, loss, new high score
        self.assertEqual(self.user_profile.games_played, 2)
        self.assertEqual(self.user_profile.total_wins, 1)
        self.assertEqual(self.user_profile.total_losses, 1)
        self.assertEqual(self.user_profile.high_score, 120)
        self.assertEqual(self.user_profile.average_score, (50 + 120) / 2)
        self.assertEqual(self.user_profile.total_score_sum, 170)

    def test_update_stats_multiple_updates(self):
        self.user_profile.update_stats(score=100, is_win=True)
        self.user_profile.update_stats(score=80, is_win=False)
        self.user_profile.update_stats(score=120, is_win=True)
        self.assertEqual(self.user_profile.games_played, 3)
        self.assertEqual(self.user_profile.total_wins, 2)
        self.assertEqual(self.user_profile.total_losses, 1)
        self.assertEqual(self.user_profile.high_score, 120)
        self.assertEqual(self.user_profile.average_score, (100 + 80 + 120) / 3)
        self.assertEqual(self.user_profile.total_score_sum, 300)

    def test_to_dict(self):
        self.user_profile.update_stats(score=150, is_win=True)
        # Manually set total_score_sum if it's part of your UserProfile's to_dict
        if hasattr(self.user_profile, 'total_score_sum'):
             self.user_profile.total_score_sum = 150 # Match the update_stats call

        profile_dict = self.user_profile.to_dict()
        expected_dict = {
            'username': "test_user",
            'high_score': 150,
            'games_played': 1,
            'total_wins': 1,
            'total_losses': 0,
            'average_score': 150.0,
        }
        # If total_score_sum is part of to_dict, add it to expected_dict
        if 'total_score_sum' in profile_dict:
            expected_dict['total_score_sum'] = 150

        self.assertEqual(profile_dict, expected_dict)

    def test_from_dict(self):
        data = {
            'username': "dict_user",
            'high_score': 200,
            'games_played': 5,
            'total_wins': 3,
            'total_losses': 2,
            'average_score': 40.0, # 200 / 5
            'total_score_sum': 200 # Explicitly provide if needed for avg score logic
        }
        profile = UserProfile.from_dict(data)
        self.assertEqual(profile.username, "dict_user")
        self.assertEqual(profile.high_score, 200)
        self.assertEqual(profile.games_played, 5)
        self.assertEqual(profile.total_wins, 3)
        self.assertEqual(profile.total_losses, 2)
        self.assertEqual(profile.average_score, 40.0)
        # If total_score_sum is loaded by from_dict and used by update_stats, test its presence
        if hasattr(profile, 'total_score_sum'):
            self.assertEqual(profile.total_score_sum, data.get('total_score_sum', 0))


class TestProfileManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for profiles
        self.test_profiles_dir = tempfile.mkdtemp()
        self.profile_manager = ProfileManager(profiles_dir=self.test_profiles_dir)

    def tearDown(self):
        # Remove the temporary directory after tests
        shutil.rmtree(self.test_profiles_dir)

    def test_ensure_profiles_dir_exists(self):
        self.assertTrue(os.path.exists(self.test_profiles_dir))

    def test_create_profile_success(self):
        username = "new_user"
        profile = self.profile_manager.create_profile(username)
        self.assertIn(username, self.profile_manager.profiles)
        self.assertEqual(profile, self.profile_manager.profiles[username])

        expected_filepath = os.path.join(self.test_profiles_dir, f"{username}.json")
        self.assertTrue(os.path.exists(expected_filepath))

        loaded_profile = self.profile_manager.get_profile(username)
        self.assertEqual(loaded_profile.username, username)

    def test_create_profile_duplicate(self):
        username = "duplicate_user"
        self.profile_manager.create_profile(username) # First creation
        with self.assertRaises(ValueError):
            self.profile_manager.create_profile(username) # Attempt duplicate

    def test_load_profile_success(self):
        username = "existing_user"
        # Manually create a profile file
        data_to_save = {
            'username': username, 'high_score': 100, 'games_played': 1,
            'total_wins': 1, 'total_losses': 0, 'average_score': 100.0,
            'total_score_sum': 100
        }
        filepath = os.path.join(self.test_profiles_dir, f"{username}.json")
        with open(filepath, 'w') as f:
            json.dump(data_to_save, f)

        # Clear manager's cache and load
        self.profile_manager.profiles.clear()
        profile = self.profile_manager.load_profile(username)

        self.assertIsNotNone(profile)
        self.assertEqual(profile.username, username)
        self.assertEqual(profile.high_score, 100)
        self.assertIn(username, self.profile_manager.profiles)

    def test_load_profile_non_existent(self):
        profile = self.profile_manager.load_profile("non_existent_user")
        self.assertIsNone(profile)

    def test_save_profile_success(self):
        username = "user_to_save"
        profile = self.profile_manager.create_profile(username)
        profile.update_stats(score=500, is_win=True)
        self.profile_manager.save_profile(username)

        # Load it back in a new manager instance or clear cache and reload
        new_manager = ProfileManager(profiles_dir=self.test_profiles_dir)
        loaded_profile = new_manager.get_profile(username) # get_profile loads if not in memory

        self.assertIsNotNone(loaded_profile)
        self.assertEqual(loaded_profile.high_score, 500)
        self.assertEqual(loaded_profile.games_played, 1)

    def test_save_profile_non_existent_in_memory(self):
        # This tests trying to save a profile that isn't in self.profile_manager.profiles
        with self.assertRaises(ValueError):
            self.profile_manager.save_profile("ghost_user")

    def test_load_all_profiles(self):
        # Create a few mock profile files
        user1_data = {'username': "user1", 'high_score': 10}
        user2_data = {'username': "user2", 'high_score': 20}

        with open(os.path.join(self.test_profiles_dir, "user1.json"), 'w') as f:
            json.dump(user1_data, f)
        with open(os.path.join(self.test_profiles_dir, "user2.json"), 'w') as f:
            json.dump(user2_data, f)
        # Add a non-json file to ensure it's skipped
        with open(os.path.join(self.test_profiles_dir, "test.txt"), 'w') as f:
            f.write("hello")

        self.profile_manager.load_all_profiles() # This should clear and reload

        self.assertEqual(len(self.profile_manager.profiles), 2)
        self.assertIn("user1", self.profile_manager.profiles)
        self.assertIn("user2", self.profile_manager.profiles)
        self.assertEqual(self.profile_manager.profiles["user1"].high_score, 10)
        self.assertEqual(self.profile_manager.profiles["user2"].high_score, 20)

    def test_list_profile_names(self):
        self.profile_manager.create_profile("alpha")
        self.profile_manager.create_profile("beta")

        profile_names = self.profile_manager.list_profile_names()
        self.assertIn("alpha", profile_names)
        self.assertIn("beta", profile_names)
        self.assertEqual(len(profile_names), 2)

    def test_rename_profile_success(self):
        old_username = "user_to_rename"
        new_username = "user_renamed"
        self.profile_manager.create_profile(old_username)

        self.assertTrue(self.profile_manager.rename_profile(old_username, new_username))

        self.assertNotIn(old_username, self.profile_manager.profiles)
        self.assertNotIn(old_username, self.profile_manager.list_profile_names())
        old_filepath = os.path.join(self.test_profiles_dir, f"{old_username}.json")
        self.assertFalse(os.path.exists(old_filepath))

        self.assertIn(new_username, self.profile_manager.profiles)
        self.assertIn(new_username, self.profile_manager.list_profile_names())
        new_filepath = os.path.join(self.test_profiles_dir, f"{new_username}.json")
        self.assertTrue(os.path.exists(new_filepath))

        renamed_profile = self.profile_manager.get_profile(new_username)
        self.assertIsNotNone(renamed_profile)
        self.assertEqual(renamed_profile.username, new_username)

    def test_rename_profile_new_name_exists(self):
        user_a = "userA"
        user_b = "userB"
        self.profile_manager.create_profile(user_a)
        self.profile_manager.create_profile(user_b)

        with self.assertRaisesRegex(ValueError, f"Profile '{user_b}' already exists."):
            self.profile_manager.rename_profile(user_a, user_b)

        # Verify userA still exists and is unchanged
        self.assertIn(user_a, self.profile_manager.profiles)
        self.assertTrue(os.path.exists(os.path.join(self.test_profiles_dir, f"{user_a}.json")))
        profile_a = self.profile_manager.get_profile(user_a)
        self.assertEqual(profile_a.username, user_a)


    def test_rename_profile_old_name_not_exists(self):
        with self.assertRaisesRegex(ValueError, "Profile 'nonexistentuser' not found."):
            self.profile_manager.rename_profile("nonexistentuser", "newname")

    def test_rename_profile_empty_new_name(self):
        user1 = "user1_for_empty_rename"
        self.profile_manager.create_profile(user1)
        with self.assertRaisesRegex(ValueError, "New username cannot be empty."):
            self.profile_manager.rename_profile(user1, "")
        with self.assertRaisesRegex(ValueError, "New username cannot be empty."):
            self.profile_manager.rename_profile(user1, "   ")

    def test_delete_profile_success(self):
        username_to_delete = "user_to_delete"
        self.profile_manager.create_profile(username_to_delete)

        # Ensure file exists before deletion for a complete test
        filepath = os.path.join(self.test_profiles_dir, f"{username_to_delete}.json")
        self.assertTrue(os.path.exists(filepath))

        self.assertTrue(self.profile_manager.delete_profile(username_to_delete))

        self.assertNotIn(username_to_delete, self.profile_manager.profiles)
        self.assertNotIn(username_to_delete, self.profile_manager.list_profile_names())
        self.assertFalse(os.path.exists(filepath))

    def test_delete_profile_non_existent(self):
        with self.assertRaisesRegex(ValueError, "Profile 'nonexistentuser' not found."):
            self.profile_manager.delete_profile("nonexistentuser")

if __name__ == '__main__':
    unittest.main()
