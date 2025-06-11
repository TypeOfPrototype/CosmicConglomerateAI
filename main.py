# main.py

import os
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from start_screen import StartScreen
from game_screen import GameScreen

# Set the window size for better visibility
Window.size = (1600, 900) # Restored

# Calculate center position
screen_width = Window.system_size[0]
screen_height = Window.system_size[1]
window_width = Window.width
window_height = Window.height

Window.left = ((screen_width - window_width) / 2) - 75
Window.top = (screen_height - window_height) / 2

# Define the main application class
class SpaceMonopolyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartScreen(name='start'))
        sm.add_widget(GameScreen(name='game'))
        return sm

# Set to fullscreen before running the app
# Window.fullscreen = 'auto' # Commented out for windowed mode

# Run the application
if __name__ == "__main__":
    SpaceMonopolyApp().run()
