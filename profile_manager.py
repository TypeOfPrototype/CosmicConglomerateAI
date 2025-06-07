import json
import os

class UserProfile:
    def __init__(self, username):
        self.username = username
        self.high_score = 0
        self.games_played = 0
        self.total_wins = 0
        self.total_losses = 0
        self.average_score = 0.0
        # Add other relevant stats as needed, e.g., favorite_company, total_shares_traded

    def update_stats(self, score, is_win):
        self.games_played += 1
        if score > self.high_score:
            self.high_score = score
        if is_win:
            self.total_wins += 1
        else:
            self.total_losses += 1

        # Recalculate average_score, avoid division by zero if games_played is 0
        if self.games_played > 0:
            # Assuming 'score' is the sum of all scores, which is not the case here.
            # This should be total score / games_played.
            # For now, let's assume 'score' is the current game's score and we need a running total of scores.
            # This requires an additional attribute, e.g., self.total_score_sum
            # For simplicity, let's placeholder this logic.
            # A more accurate average_score would require storing the sum of all scores.
            # Let's assume for now average_score is just the average of scores seen so far.
            # This will be updated to be more accurate if total_score_sum is added.
            if not hasattr(self, 'total_score_sum'):
                self.total_score_sum = 0
            self.total_score_sum += score
            self.average_score = self.total_score_sum / self.games_played
        else:
            self.average_score = 0.0


    def to_dict(self):
        return {
            'username': self.username,
            'high_score': self.high_score,
            'games_played': self.games_played,
            'total_wins': self.total_wins,
            'total_losses': self.total_losses,
            'average_score': self.average_score,
            # include other stats if added
        }

    @classmethod
    def from_dict(cls, data):
        profile = cls(data['username'])
        profile.high_score = data.get('high_score', 0)
        profile.games_played = data.get('games_played', 0)
        profile.total_wins = data.get('total_wins', 0)
        profile.total_losses = data.get('total_losses', 0)
        profile.average_score = data.get('average_score', 0.0)
        # hydrate other stats if added
        return profile

class ProfileManager:
    def __init__(self, profiles_dir='user_profiles'):
        self.profiles_dir = profiles_dir
        self._ensure_profiles_dir_exists()
        self.profiles = {}  # username: UserProfile object
        self.load_all_profiles()

    def _ensure_profiles_dir_exists(self):
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)

    def create_profile(self, username):
        if username in self.profiles:
            raise ValueError(f"Profile for {username} already exists.")
        profile = UserProfile(username)
        self.profiles[username] = profile
        self.save_profile(username)
        return profile

    def load_profile(self, username):
        filepath = os.path.join(self.profiles_dir, f"{username}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            profile = UserProfile.from_dict(data)
            self.profiles[username] = profile  # Store/update in the manager's cache
            return profile
        except Exception as e:
            # Log error or handle corrupted file
            print(f"Error loading profile {username}: {e}")
            return None

    def save_profile(self, username):
        if username not in self.profiles:
            raise ValueError(f"Profile for {username} not found in memory.")
        profile = self.profiles[username]
        filepath = os.path.join(self.profiles_dir, f"{username}.json")
        with open(filepath, 'w') as f:
            json.dump(profile.to_dict(), f, indent=4)

    def load_all_profiles(self):
        self.profiles.clear()
        if not os.path.exists(self.profiles_dir):
            return
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith(".json"):
                username = filename[:-5]  # Remove .json
                # load_profile already adds to self.profiles
                self.load_profile(username)

    def get_profile(self, username):
        return self.profiles.get(username)

    def list_profile_names(self):
        return list(self.profiles.keys())

    def rename_profile(self, old_username, new_username):
        if not new_username or new_username.isspace():
            raise ValueError("New username cannot be empty.")

        if new_username == old_username:
            # No actual rename needed, but also prevent "profile already exists" if it's the same name
            # Or, could raise a specific error/return False if self-rename is disallowed.
            # For now, let's consider it a no-op success, though "profile already exists" check below would catch it.
            # To be explicit, if new_username is the same as old_username, and old_username exists,
            # it's effectively a successful no-op unless other behavior is desired.
            # The check `if new_username in self.profiles:` handles this correctly if old_username == new_username.
            pass

        if new_username in self.profiles:
            raise ValueError(f"Profile '{new_username}' already exists.")

        if old_username not in self.profiles:
            raise ValueError(f"Profile '{old_username}' not found.")

        profile = self.profiles[old_username]
        profile.username = new_username # Update username attribute on the UserProfile object

        old_filepath = os.path.join(self.profiles_dir, f"{old_username}.json")
        new_filepath = os.path.join(self.profiles_dir, f"{new_username}.json")

        try:
            # Save the profile with the new username (which to_dict() will now use)
            with open(new_filepath, 'w') as f:
                json.dump(profile.to_dict(), f, indent=4)

            # Update internal dictionary
            self.profiles[new_username] = profile
            del self.profiles[old_username]

            # Delete old file
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
            else:
                # Log a warning, as this indicates an inconsistency (profile was in memory but no file)
                print(f"Warning: Old profile file not found at {old_filepath} during rename.")

        except Exception as e:
            # Attempt to rollback changes if any step fails after new file creation
            if os.path.exists(new_filepath):
                try:
                    os.remove(new_filepath)
                except Exception as rollback_e:
                    print(f"Error during rollback (removing new file {new_filepath}): {rollback_e}")

            # Revert profile object username and internal dictionary if rename failed mid-way
            profile.username = old_username
            if new_username in self.profiles: # if it was added
                 del self.profiles[new_username]
            self.profiles[old_username] = profile # ensure old one is back

            raise Exception(f"Failed to rename profile: {e}")

        return True

    def delete_profile(self, username):
        if username not in self.profiles:
            raise ValueError(f"Profile '{username}' not found.")

        filepath = os.path.join(self.profiles_dir, f"{username}.json")

        try:
            # Remove from internal dictionary first
            del self.profiles[username]

            # Delete file
            if os.path.exists(filepath):
                os.remove(filepath)
            else:
                # Log a warning if file was already gone, but profile was in memory
                print(f"Warning: Profile file not found at {filepath} during deletion, but profile was in memory.")
        except Exception as e:
            # If deletion fails, try to add profile back to memory if it was removed
            # This is a best-effort rollback for the in-memory state.
            # The actual file state might be inconsistent if os.remove failed.
            # For simplicity, we won't try to reload it from disk here if it was already gone.
            # This scenario implies more complex error handling might be needed depending on desired atomicity.
            print(f"Error deleting profile {username}: {e}. Profile might be partially deleted.")
            # Re-add to self.profiles if it was removed and we have the object (though it's gone now)
            # This part is tricky as the 'profile' object is not fetched here.
            # Let's assume if del self.profiles[username] succeeded, but os.remove failed,
            # the profile is gone from manager's view, but file might linger.
            # The requirement is to return True on success, so if os.remove fails, it's not a success.
            # Consider re-raising or returning False. Let's re-raise for now.
            raise Exception(f"Failed to delete profile file: {e}")

        return True
