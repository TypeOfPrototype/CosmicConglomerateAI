# highscore_screen.py

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.app import App

from highscore_manager import load_highscores

class HighscoreScreen(Screen):
    def __init__(self, **kwargs):
        super(HighscoreScreen, self).__init__(**kwargs)

        # Main layout with a dark background
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        with self.main_layout.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # Dark background color
            self.rect = Rectangle(size=self.main_layout.size, pos=self.main_layout.pos)
        self.main_layout.bind(size=self._update_rect, pos=self._update_rect)

        self.add_widget(self.main_layout)

        # Title
        title_label = Label(
            text="[b]Top 10 Highscores[/b]",
            font_size=Window.height * 0.04, # Responsive font size
            markup=True,
            size_hint_y=None,
            height=Window.height * 0.1,
            color=(0.8, 0.8, 0.8, 1) # Light grey color for title
        )
        self.main_layout.add_widget(title_label)

        # Scrollable area for scores (though not strictly scrollable yet without ScrollView)
        # For simplicity, we'll just use a BoxLayout. If more than 10 scores were shown, ScrollView would be needed.
        self.scores_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.8)
        self.main_layout.add_widget(self.scores_layout)

        # Back button
        back_button = Button(
            text="Back to Main Menu",
            size_hint_y=None,
            height=Window.height * 0.08, # Responsive height
            font_size=Window.height * 0.025 # Responsive font size
        )
        back_button.bind(on_press=self.go_back)
        self.main_layout.add_widget(back_button)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_enter(self):
        """
        Called when the screen is entered. Loads and displays highscores.
        """
        self.populate_highscores()

    def populate_highscores(self):
        """
        Loads highscores and updates the display.
        """
        self.scores_layout.clear_widgets()
        highscores = load_highscores()

        if not highscores:
            no_scores_label = Label(
                text="No highscores yet!",
                font_size=Window.height * 0.025,
                color=(0.7, 0.7, 0.7, 1)
            )
            self.scores_layout.add_widget(no_scores_label)
            return

        for i, entry in enumerate(highscores):
            player_name = entry.get("name", "N/A")
            score = entry.get("score", 0)

            score_label_text = f"[b]{i+1}.[/b] {player_name} - {score}"
            score_label = Label(
                text=score_label_text,
                font_size=Window.height * 0.022, # Responsive font size
                markup=True,
                size_hint_y=None,
                height=Window.height * 0.05,
                color=(0.9, 0.9, 0.9, 1) # Off-white for good contrast
            )
            self.scores_layout.add_widget(score_label)

    def go_back(self, instance):
        """
        Navigates back to the start screen.
        """
        self.manager.current = 'start'

if __name__ == '__main__':
    # This is a simple test to run the HighscoreScreen standalone
    # For this to work, you'd need a highscores.json or it will show "No highscores yet!"
    # And you'd need to create a dummy highscore_manager.py if it's not in the same path
    # or ensure it's discoverable by Python.

    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager

    # Create a dummy highscores.json for testing if it doesn't exist
    import os
    import json
    if not os.path.exists("highscores.json"):
        dummy_scores = [
            {"name": "Alice", "score": 1000},
            {"name": "Bob", "score": 900},
            {"name": "Charlie", "score": 800},
        ]
        with open("highscores.json", "w") as f:
            json.dump(dummy_scores, f)

    # Dummy highscore_manager if not available (simplified)
    if not os.path.exists("highscore_manager.py"):
        with open("highscore_manager.py", "w") as f:
            f.write("""
import json
import os
HIGHSCORE_FILE = "highscores.json"
def load_highscores():
    if not os.path.exists(HIGHSCORE_FILE): return []
    try:
        with open(HIGHSCORE_FILE, 'r') as f: scores = json.load(f)
        return scores if isinstance(scores, list) else []
    except: return []
""")


    class TestApp(App):
        def build(self):
            sm = ScreenManager()
            # Ensure highscore_manager is available for import by HighscoreScreen
            # If highscore_manager.py was created by a previous step, it should be fine.
            # If running this test totally standalone, the dummy created above helps.
            sm.add_widget(HighscoreScreen(name='highscores'))
            sm.current = 'highscores'
            return sm

    TestApp().run()
