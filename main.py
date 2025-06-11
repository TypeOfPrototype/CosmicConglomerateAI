# main.py

import os
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from start_screen import StartScreen
from game_screen import GameScreen

# Set the window size for better visibility
Window.size = (1200, 800) # Restored

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
