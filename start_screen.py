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
from functools import partial # For binding with arguments

# Path to your custom font
FONT_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'Orbitron-Regular.ttf')

# Import profile manager
from profile_manager import ProfileManager, UserProfile


class StartScreen(Screen):
    title_label = ObjectProperty(None)
    start_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(StartScreen, self).__init__(**kwargs)
        # Initialize ProfileManager
        self.profile_manager = ProfileManager()
        self.existing_profile_names = self.profile_manager.list_profile_names()
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
        self.player_configs = []
        players_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.3), spacing=10)
        player_types = ["Off", "Human", "AI (Easy)"]
        default_configs = [
            {"type": "Human", "name": "Player 1", "profile_text": "<Create New Profile>"},
            {"type": "Human", "name": "Player 2", "profile_text": "<Create New Profile>"},
            {"type": "Off", "name": "", "profile_text": "<Create New Profile>"},
            {"type": "Off", "name": "", "profile_text": "<Create New Profile>"}
        ]

        # Try to assign existing profiles to first few players if available
        available_profiles = self.existing_profile_names[:]
        if available_profiles:
            if len(available_profiles) > 0 and default_configs[0]["type"] != "Off":
                default_configs[0]["profile_text"] = available_profiles.pop(0)
                default_configs[0]["name"] = default_configs[0]["profile_text"]
            if len(available_profiles) > 0 and default_configs[1]["type"] != "Off":
                default_configs[1]["profile_text"] = available_profiles.pop(0)
                default_configs[1]["name"] = default_configs[1]["profile_text"]


        for i in range(4):
            player_row_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)

            profile_spinner_values = ['<Create New Profile>'] + self.existing_profile_names
            profile_spinner = Spinner(
                text=default_configs[i]["profile_text"],
                values=profile_spinner_values,
                size_hint_x=0.3, # Adjusted size
                font_size=18,
                background_normal='',
                background_color=(0.2, 0.2, 0.2, 1),
                color=(1, 1, 1, 1),
                font_name=FONT_PATH
            )

            type_spinner = Spinner(
                text=default_configs[i]["type"],
                values=player_types,
                size_hint_x=0.3, # Adjusted size
                font_size=18,
                background_normal='',
                background_color=(0.2, 0.2, 0.2, 1),
                color=(1, 1, 1, 1),
                font_name=FONT_PATH
            )

            name_input = TextInput(
                hint_text='Enter New Profile Name' if default_configs[i]["profile_text"] == "<Create New Profile>" else default_configs[i]["name"],
                text=default_configs[i]["name"] if default_configs[i]["profile_text"] != "<Create New Profile>" else "",
                size_hint_x=0.4, # Adjusted size
                multiline=False,
                font_size=18,
                padding=(10, 10),
                background_normal='',
                background_color=(0.2, 0.2, 0.2, 1),
                foreground_color=(1, 1, 1, 1)
            )

            # Set initial state of TextInput and Profile Spinner based on Spinner
            if default_configs[i]["type"] == "Off":
                name_input.disabled = True
                name_input.text = ""
                profile_spinner.disabled = True
                profile_spinner.text = "<Create New Profile>" # Reset when off
            else:
                name_input.disabled = default_configs[i]["profile_text"] != "<Create New Profile>"
                profile_spinner.disabled = False


            # Bind spinners change to callbacks
            type_spinner.bind(text=partial(self._on_player_type_change, player_index=i))
            profile_spinner.bind(text=partial(self._on_profile_selection_change, player_index=i))

            player_row_layout.add_widget(profile_spinner) # Added profile spinner
            player_row_layout.add_widget(type_spinner)
            player_row_layout.add_widget(name_input)
            players_layout.add_widget(player_row_layout)
            self.player_configs.append({
                'profile_spinner': profile_spinner, # Stored profile spinner
                'type_spinner': type_spinner,
                'name_input': name_input
            })

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

    def _on_player_type_change(self, spinner_instance, text, player_index):
        config = self.player_configs[player_index]
        name_input = config['name_input']
        profile_spinner = config['profile_spinner']

        if text == "Off":
            name_input.disabled = True
            name_input.text = ""
            profile_spinner.disabled = True
            # Optionally reset profile spinner:
            # profile_spinner.text = "<Create New Profile>"
        else:
            profile_spinner.disabled = False
            # Trigger profile selection logic to correctly set name_input state
            self._on_profile_selection_change(profile_spinner, profile_spinner.text, player_index)
            # If profile is "<Create New Profile>", set default name based on type, otherwise name is set by profile
            if profile_spinner.text == "<Create New Profile>":
                if text == "Human" and not name_input.text: # Don't overwrite if user started typing
                    name_input.hint_text = f"Player {player_index + 1} Name"
                elif text == "AI (Easy)" and not name_input.text:
                    name_input.hint_text = f"AI {player_index + 1} Name"


    def _on_profile_selection_change(self, spinner_instance, selected_profile_name, player_index):
        config = self.player_configs[player_index]
        name_input = config['name_input']
        player_type_spinner = config['type_spinner']

        if player_type_spinner.text == "Off": # Should not happen if type_spinner disables profile_spinner
            return

        if selected_profile_name == "<Create New Profile>":
            name_input.disabled = False
            name_input.text = ""
            name_input.hint_text = "Enter New Profile Name"
            if player_type_spinner.text == "Human": # Set a default hint based on player type
                 name_input.hint_text = f"P{player_index+1} New Profile"
            elif player_type_spinner.text == "AI (Easy)":
                 name_input.hint_text = f"AI {player_index+1} New Profile"
        else:
            name_input.disabled = True
            name_input.text = selected_profile_name
            name_input.hint_text = ""


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
        player_configurations = []
        active_player_names = set() # To check for duplicate names among active players

        for i, config in enumerate(self.player_configs):
            player_type = config['type_spinner'].text
            if player_type == "Off":
                continue

            profile_spinner = config['profile_spinner']
            name_input = config['name_input']

            selected_profile_option = profile_spinner.text
            entered_name = name_input.text.strip()

            profile_username = ""
            is_new_profile = False

            if selected_profile_option == "<Create New Profile>":
                if not entered_name:
                    self._show_error_popup(f"Player {i+1}: Name cannot be empty when creating a new profile.")
                    return
                if entered_name == "<Create New Profile>": # Reserved name
                    self._show_error_popup(f"Player {i+1}: Invalid name '{entered_name}'. Please choose a different name.")
                    return
                if self.profile_manager.get_profile(entered_name):
                    self._show_error_popup(f"Player {i+1}: Profile '{entered_name}' already exists. Select it from the list or choose a different name.")
                    return
                if entered_name in active_player_names:
                    self._show_error_popup(f"Player {i+1}: Name '{entered_name}' is already taken by another active player in this game.")
                    return
                
                profile_username = entered_name
                is_new_profile = True
            else:
                # Existing profile selected
                profile_username = selected_profile_option
                if profile_username in active_player_names:
                    self._show_error_popup(f"Player {i+1}: Profile '{profile_username}' is already selected by another player.")
                    return

            active_player_names.add(profile_username)
            player_configurations.append({
                'name': profile_username, # 'name' key is used by game logic, should be the profile username
                'type': player_type,
                'profile_username': profile_username,
                'is_new_profile': is_new_profile
            })

        if len(player_configurations) < 1:
            self._show_error_popup('At least one player (Human or AI) must be active.')
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
            # Display an error popup if grid size is not selected
            self._show_error_popup('Please select a valid grid size.')
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
            player_configurations, (cols, rows), game_turn_length, marker_percentage
        )

    def _show_error_popup(self, message):
        error_popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        error_popup.open()
