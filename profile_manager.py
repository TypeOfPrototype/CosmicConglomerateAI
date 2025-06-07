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
