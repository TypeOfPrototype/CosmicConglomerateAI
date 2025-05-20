# start_screen.py (Configurable Diamonds + Fonts + AI Player Selection)

import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner # Import Spinner
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.metrics import dp, sp # Import sp and dp

# FONT_PATH = None # Use Kivy default

class StartScreen(Screen):
    title_label = ObjectProperty(None)
    start_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(StartScreen, self).__init__(**kwargs)
        self.player_slots = [] # Store (name_input, type_spinner) tuples
        self.build_ui()

    def build_ui(self):
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(20))

        # Background
        with layout.canvas.before:
            Color(0.05, 0.05, 0.2, 1)
            self.bg_gradient = Rectangle(pos=self.pos, size=Window.size)
            layout.bind(size=self._update_bg, pos=self._update_bg)

        # Title Label
        self.title_label = Label(
            text="Space Monopoly", font_size='50sp', size_hint=(1, 0.2),
            color=(1, 0.9, 0.3, 0) # Start transparent
        )
        layout.add_widget(self.title_label)

        # Player inputs & AI Selection
        self.player_slots = [] # Reset if build_ui is called again
        players_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.3), spacing=dp(10))
        for i in range(4):
            player_slot_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(40), spacing=dp(5))

            name_input = TextInput(
                hint_text=f'Player {i + 1} Name', size_hint=(0.7, 1),
                multiline=False, font_size='18sp', padding=(dp(10), dp(10)),
                background_normal='', background_color=(0.2, 0.2, 0.2, 1),
                foreground_color=(1, 1, 1, 1)
            )

            type_spinner = Spinner(
                text='Human', # Default to Human
                values=['Human', 'AI Easy', 'AI Medium', 'AI Hard'],
                size_hint=(0.3, 1),
                font_size='16sp', background_normal='', background_color=(0.2, 0.2, 0.2, 1),
                color=(1, 1, 1, 1)
            )
            player_slot_layout.add_widget(name_input)
            player_slot_layout.add_widget(type_spinner)
            self.player_slots.append((name_input, type_spinner)) # Store tuple
            players_layout.add_widget(player_slot_layout)

        layout.add_widget(players_layout)

        # Options Layout (Grid Size & Diamonds) - Adjusted Spacing/Hints
        options_layout = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(10))

        # Grid size
        grid_size_label = Label(text='Grid:', size_hint=(0.15, 1), font_size='16sp')
        self.grid_size_spinner = Spinner(
            text='22x18', values=['16x12', '22x18', '28x24'], size_hint=(0.3, 1), # Adjusted hint
            font_size='16sp', background_normal='', background_color=(0.2, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        options_layout.add_widget(grid_size_label)
        options_layout.add_widget(self.grid_size_spinner)

        # --- Configurable Initial Diamonds ---
        diamonds_label = Label(text='Start Diamonds:', size_hint=(0.3, 1), font_size='16sp')
        # Use TextInput instead of CheckBox
        self.diamonds_input = TextInput(
            text='5%', # Default to 5%
            hint_text='Number or %',
            size_hint=(0.25, 1), # Adjusted hint
            multiline=False,
            font_size='16sp',
            padding=(dp(8), dp(8)),
            background_normal='', background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1)
        )
        options_layout.add_widget(diamonds_label)
        options_layout.add_widget(self.diamonds_input)
        # --- End Diamond Option ---

        layout.add_widget(options_layout)

        # Game turn length input
        self.turn_length_input = TextInput(
            hint_text='Game Turn Length (Default: 80)', size_hint=(1, None), height=dp(40),
            input_filter='int', multiline=False, font_size='18sp', padding=(dp(10), dp(10)),
            background_normal='', background_color=(0.2, 0.2, 0.2, 1), foreground_color=(1, 1, 1, 1)
        )
        layout.add_widget(self.turn_length_input)

        # Start button
        self.start_button = Button(
            text='Start Game', size_hint=(1, 0.2), font_size='24sp',
            color=(1, 1, 1, 1), background_normal='', background_color=(0.1, 0.6, 0.9, 1)
        )
        self.start_button.bind(on_press=self.start_game)
        with self.start_button.canvas.before:
            Color(0.1, 0.6, 0.9, 1)
            self.start_button_round = RoundedRectangle(pos=self.start_button.pos, size=self.start_button.size, radius=[dp(10)])
        self.start_button.bind(pos=self._update_button_round, size=self._update_button_round)
        layout.add_widget(self.start_button)

        self.add_widget(layout)
        self.animate_widgets()

    def _update_bg(self, instance, value):
        self.bg_gradient.pos = instance.pos
        self.bg_gradient.size = instance.size

    def _update_button_round(self, instance, value):
        self.start_button_round.pos = instance.pos
        self.start_button_round.size = instance.size

    def animate_widgets(self):
        # (Animation logic remains the same)
        title_animation = Animation(color=(1, 0.9, 0.3, 1), duration=2)
        title_animation.start(self.title_label)
        self.start_button.opacity = 0
        def start_button_fade_in(dt): Animation(opacity=1, duration=2).start(self.start_button)
        Clock.schedule_once(start_button_fade_in, 1)


    def start_game(self, instance):
        # --- Updated Player Config Collection ---
        player_configs = []
        default_ai_names = iter(["Bot Alice", "Bot Bob", "Bot Charlie", "Bot Delta"])
        human_count = 0
        for name_input, type_spinner in self.player_slots:
            name = name_input.text.strip()
            player_type = type_spinner.text
            if name:
                player_configs.append((name, player_type))
                if player_type == 'Human':
                     human_count += 1
            elif player_type != 'Human': # Add default AI if type is selected but no name
                 ai_name = next(default_ai_names, f"Bot_{len(player_configs)+1}")
                 player_configs.append((ai_name, player_type))

        # Default players if none entered
        if not player_configs:
            player_configs = [("Player 1", "Human"), ("Player 2", "AI Easy")]
        elif len(player_configs) == 1:
             # Add a default AI if only one player was configured
             ai_name = next(default_ai_names, "Bot_2")
             player_configs.append((ai_name, "AI Easy"))

        if len(player_configs) < 2:
            self._show_error_popup('At least 2 players (Human or AI) are required.')
            return
        if len(player_configs) > 4:
            self._show_error_popup('Maximum of 4 players allowed.')
            return

        # --- End Player Config Collection ---

        grid_size_text = self.grid_size_spinner.text
        try:
            cols_str, rows_str = grid_size_text.split('x')
            cols = int(cols_str)
            rows = int(rows_str)
            grid_size_tuple = (rows, cols) # Logic uses (rows, cols)
        except ValueError:
            self._show_error_popup('Invalid grid size selected.')
            return

        try:
            game_turn_length = int(self.turn_length_input.text) if self.turn_length_input.text else 80
            if game_turn_length <= 0: raise ValueError
        except ValueError: game_turn_length = 80

        initial_diamonds_config = self.diamonds_input.text.strip()

        # Switch screen and pass config
        self.manager.current = 'game'
        game_screen = self.manager.get_screen('game')
        game_screen.initialize_game(
            player_configs, # Pass the list of (name, type) tuples
            grid_size_tuple,
            game_turn_length,
            initial_diamonds_config
        )

    def _show_error_popup(self, message):
        popup = Popup(title='Input Error', content=Label(text=message, font_size=sp(14)), size_hint=(0.6, 0.3))
        popup.open()
