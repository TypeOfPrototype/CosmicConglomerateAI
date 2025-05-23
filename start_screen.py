# start_screen.py

import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.properties import ObjectProperty
from kivy.clock import Clock  # Import Clock for scheduling animations

# Path to your custom font
FONT_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'Orbitron-Regular.ttf')


class StartScreen(Screen):
    title_label = ObjectProperty(None)
    start_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(StartScreen, self).__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)

        # Background with gradient
        with layout.canvas.before:
            Color(0.05, 0.05, 0.2, 1)  # Dark space-like background
            self.bg_gradient = Rectangle(pos=self.pos, size=Window.size)
            layout.bind(size=self._update_bg, pos=self._update_bg)

        # Title Label with custom font and initial opacity for animation
        self.title_label = Label(
            text="Space Monopoly",
            font_size=64,
            size_hint=(1, 0.2),
            color=(1, 0.9, 0.3, 0),  # Start transparent for fade-in
            font_name=FONT_PATH
        )
        layout.add_widget(self.title_label)

        # Player configuration inputs
        self.player_inputs = []
        self.player_checkboxes = [] # Initialize player_checkboxes list
        players_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.3), spacing=10)
        for i in range(4):
            player_row_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40) # Create player_row_layout
            checkbox = CheckBox(size_hint_x=None, width=40) # Create checkbox

            if i == 0: # Player 1
                checkbox.active = True
                checkbox.disabled = True
            elif i == 1: # Player 2
                checkbox.active = True
            
            self.player_checkboxes.append(checkbox) # Add checkbox to list
            player_row_layout.add_widget(checkbox) # Add checkbox to player_row_layout

            player_input = TextInput(
                hint_text=f'Player {i + 1} Name',
                size_hint=(1, 1), # Modified size_hint
                # height=40, # Removed height
                multiline=False,
                font_size=20,
                padding=(10, 10),
                background_normal='',
                background_color=(0.2, 0.2, 0.2, 1),
                foreground_color=(1, 1, 1, 1)  # Updated property name
            )
            player_row_layout.add_widget(player_input) # Add player_input to player_row_layout
            self.player_inputs.append(player_input)
            players_layout.add_widget(player_row_layout) # Add player_row_layout to players_layout
        layout.add_widget(players_layout)

        # Grid size selection
        grid_size_layout = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        grid_size_label = Label(
            text='Grid Size:',
            size_hint=(0.3, 1),
            font_size=24,
            color=(1, 1, 1, 1),
            font_name=FONT_PATH
        )
        self.grid_size_spinner = Spinner(
            text='22x18',
            values=['16x12', '22x18', '28x24'],
            size_hint=(0.7, 1),
            font_size=24,
            background_normal='',
            background_color=(0.2, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_PATH
        )
        grid_size_layout.add_widget(grid_size_label)
        grid_size_layout.add_widget(self.grid_size_spinner)
        layout.add_widget(grid_size_layout)

        # Marker percentage selection
        marker_percentage_layout = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        marker_percentage_label = Label(
            text='Marker Percentage:',
            size_hint=(0.3, 1),
            font_size=24,
            color=(1, 1, 1, 1),
            font_name=FONT_PATH
        )
        self.marker_percentage_slider = Slider(
            min=0,
            max=50,
            value=10,
            step=1,
            size_hint=(0.5, 1)
        )
        self.marker_percentage_value_label = Label(
            text=f"{int(self.marker_percentage_slider.value)}%",
            size_hint=(0.2, 1),
            font_size=24,
            color=(1, 1, 1, 1),
            font_name=FONT_PATH
        )
        self.marker_percentage_slider.bind(value=self._update_marker_percentage_label)
        marker_percentage_layout.add_widget(marker_percentage_label)
        marker_percentage_layout.add_widget(self.marker_percentage_slider)
        marker_percentage_layout.add_widget(self.marker_percentage_value_label)
        layout.add_widget(marker_percentage_layout)

        # Game turn length input
        self.turn_length_input = TextInput(
            hint_text='Enter Game Turn Length (Default: 80)',
            size_hint=(1, None),
            height=40,
            input_filter='int',
            multiline=False,
            font_size=20,
            padding=(10, 10),
            background_normal='',
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1)  # Updated property name
        )
        layout.add_widget(self.turn_length_input)

        # Start button with rounded corners and custom font
        self.start_button = Button(
            text='Start Game',
            size_hint=(1, 0.2),
            font_size=32,
            color=(1, 1, 1, 1),
            background_normal='',
            background_color=(0.1, 0.6, 0.9, 1),
            font_name=FONT_PATH
        )
        self.start_button.bind(on_press=self.start_game)
        # Add rounded rectangle
        with self.start_button.canvas.before:
            Color(0.1, 0.6, 0.9, 1)
            self.start_button_round = RoundedRectangle(pos=self.start_button.pos,
                                                       size=self.start_button.size,
                                                       radius=[20])
            self.start_button.bind(pos=self._update_button_round,
                                   size=self._update_button_round)
        layout.add_widget(self.start_button)

        self.add_widget(layout)

        # Animate the title and start button
        self.animate_widgets()

    def _update_bg(self, instance, value):
        self.bg_gradient.pos = instance.pos
        self.bg_gradient.size = instance.size

    def _update_button_round(self, instance, value):
        self.start_button_round.pos = instance.pos
        self.start_button_round.size = instance.size

    def _update_marker_percentage_label(self, instance, value):
        self.marker_percentage_value_label.text = f"{int(value)}%"

    def animate_widgets(self):
        # Fade in the title
        title_animation = Animation(color=(1, 0.9, 0.3, 1), duration=2)
        title_animation.start(self.title_label)

        # Fade in the start button after a 1-second delay
        self.start_button.opacity = 0  # Initially transparent

        def start_button_fade_in(dt):
            Animation(opacity=1, duration=2).start(self.start_button)

        Clock.schedule_once(start_button_fade_in, 1)  # 1-second delay

    def start_game(self, instance):
        # Retrieve player names
        player_names = []
        for i in range(4): # Or use enumerate if you prefer
            if self.player_checkboxes[i].active:
                name = self.player_inputs[i].text.strip()
                if not name:
                    name = f"Player {i + 1}"
                player_names.append(name)

        if len(player_names) < 1:
            # Display an error popup if fewer than 1 player is selected
            error_popup = Popup(
                title='Error',
                content=Label(text='At least 1 player must be selected.'),
                size_hint=(0.6, 0.4)
            )
            error_popup.open()
            return

        # Retrieve grid size
        grid_size_text = self.grid_size_spinner.text
        if 'x' in grid_size_text:
            cols, rows = map(int, grid_size_text.split('x'))
        else:
            # Display an error popup if grid size is not selected
            error_popup = Popup(
                title='Error',
                content=Label(text='Please select a valid grid size.'),
                size_hint=(0.6, 0.4)
            )
            error_popup.open()
            return

        # Retrieve game turn length
        try:
            game_turn_length = int(self.turn_length_input.text)
            if game_turn_length <= 0:
                raise ValueError
        except (ValueError, TypeError):
            game_turn_length = 80  # Default turn length

        # Pass configuration to the game screen
        self.manager.current = 'game'
        marker_percentage = self.marker_percentage_slider.value / 100.0
        self.manager.get_screen('game').initialize_game(
            player_names, (cols, rows), game_turn_length, marker_percentage
        )
