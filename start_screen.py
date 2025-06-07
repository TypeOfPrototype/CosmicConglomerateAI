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
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp


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
            player_default_type = default_configs[i]["type"]
            if player_default_type == "Off":
                name_input.disabled = True
                name_input.text = ""
                profile_spinner.disabled = True
                profile_spinner.text = "<Create New Profile>"
            elif player_default_type == "AI (Easy)":
                profile_spinner.disabled = True
                profile_spinner.text = "<N/A for AI>"
                name_input.disabled = True
                name_input.text = default_configs[i]["name"] # Should be like "AI X (Easy)"
            else: # Human
                name_input.disabled = default_configs[i]["profile_text"] != "<Create New Profile>"
                profile_spinner.disabled = False
                # Ensure name_input text is correct if an existing profile is defaulted
                if default_configs[i]["profile_text"] != "<Create New Profile>":
                    name_input.text = default_configs[i]["profile_text"]
                else:
                    name_input.text = "" # For new profile, start empty

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

        # Manage Profiles Button
        self.manage_profiles_button = Button(
            text='Manage Profiles',
            size_hint=(1, None),
            height=dp(40),
            font_size=20,
            background_normal='',
            background_color=(0.1, 0.5, 0.8, 1), # A distinct color
            font_name=FONT_PATH
        )
        self.manage_profiles_button.bind(on_press=self.show_profile_management_popup)
        layout.add_widget(self.manage_profiles_button)

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

        if text == "AI (Easy)":
            profile_spinner.disabled = True
            profile_spinner.text = "<N/A for AI>" # Placeholder for AI
            name_input.disabled = False # Allow AI name editing
            default_ai_name = f"AI {player_index + 1} (Easy)"
            if not name_input.text.strip(): # If user cleared it or it's initial setup
                name_input.text = default_ai_name
            name_input.hint_text = "Enter AI Name" # Optional: provide a hint
            # else, keep the user's custom AI name if they typed one already
        elif text == "Human":
            profile_spinner.disabled = False
            # name_input.disabled = False # This will be handled by _on_profile_selection_change
            # When switching to Human, profile_spinner might be "<Create New Profile>" or an existing profile.
            # Call _on_profile_selection_change to set name_input state correctly.
            self._on_profile_selection_change(profile_spinner, profile_spinner.text, player_index)
        elif text == "Off":
            profile_spinner.disabled = True
            profile_spinner.text = "<Create New Profile>" # Reset for when it's re-enabled
            name_input.disabled = True
            name_input.text = ""
            name_input.hint_text = "" # Clear hint text


    def _on_profile_selection_change(self, spinner_instance, selected_profile_name, player_index):
        config = self.player_configs[player_index]
        name_input = config['name_input']
        player_type_spinner = config['type_spinner']

        if player_type_spinner.text == "Off" or player_type_spinner.text == "AI (Easy)":
            return # AI profile/name is fixed, "Off" means no input

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

            profile_spinner = config['profile_spinner'] # Human player's profile spinner
            name_input = config['name_input']           # Human player's name input (for new profiles)

            selected_profile_option = profile_spinner.text
            entered_name = name_input.text.strip()

            profile_username_for_game = "" # This will be the actual username string for the profile
            is_new_profile_flag = False
            player_display_name = "" # This is what GameState might use as 'name' if it's different from profile_username

            if player_type == "Human":
                if selected_profile_option == "<Create New Profile>":
                    if not entered_name:
                        self._show_error_popup(f"Player {i+1} (Human): Name cannot be empty when creating a new profile.")
                        return
                    if entered_name == "<Create New Profile>" or entered_name == "<N/A for AI>": # Reserved names
                        self._show_error_popup(f"Player {i+1} (Human): Invalid name '{entered_name}'. Please choose a different name.")
                        return
                    if self.profile_manager.get_profile(entered_name):
                        self._show_error_popup(f"Player {i+1} (Human): Profile '{entered_name}' already exists. Select it from the list or choose a different name.")
                        return
                    if entered_name in active_player_names: # Check against other human player names being configured
                        self._show_error_popup(f"Player {i+1} (Human): Name '{entered_name}' is already taken by another active Human player.")
                        return

                    profile_username_for_game = entered_name
                    player_display_name = entered_name
                    is_new_profile_flag = True
                    active_player_names.add(entered_name)
                else: # Existing profile selected for Human
                    profile_username_for_game = selected_profile_option
                    player_display_name = selected_profile_option
                    is_new_profile_flag = False
                    if profile_username_for_game in active_player_names: # Check against other human player names
                        self._show_error_popup(f"Player {i+1} (Human): Profile '{profile_username_for_game}' is already selected by another active Human player.")
                        return
                    active_player_names.add(profile_username_for_game)

                player_configurations.append({
                    'name': player_display_name,
                    'type': player_type,
                    'profile_username': profile_username_for_game, # Actual profile ID for humans
                    'is_new_profile': is_new_profile_flag
                })

            elif player_type == "AI (Easy)":
                player_game_name = name_input.text.strip()
                if not player_game_name: # If empty after stripping
                    player_game_name = f"AI {i + 1} (Easy)" # Default AI name
                    name_input.text = player_game_name # Update UI if it was empty

                # AI players do not have user profiles in the same way.
                # profile_username can be None or a generic ID.
                # 'name' will be the AI's display name.
                player_configurations.append({
                    'name': player_game_name,
                    'type': player_type,
                    'profile_username': None, # No specific user profile for AI
                    'is_new_profile': False
                })
            # "Off" players are skipped earlier

        if len(player_configurations) < 1:
            self._show_error_popup('At least one player (Human or AI) must be active.')
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

    def _refresh_profile_spinners(self):
        self.existing_profile_names = self.profile_manager.list_profile_names()
        for p_index, config in enumerate(self.player_configs):
            profile_spinner = config['profile_spinner']
            type_spinner = config['type_spinner']
            name_input = config['name_input']

            if type_spinner.text == "Human":
                current_selection = profile_spinner.text
                new_values = ['<Create New Profile>'] + self.existing_profile_names
                profile_spinner.values = new_values

                if current_selection not in new_values or current_selection == "<Create New Profile>" or current_selection == "<N/A for AI>":
                    profile_spinner.text = '<Create New Profile>'
                else:
                    profile_spinner.text = current_selection

                # Ensure _on_profile_selection_change is called to update name_input state
                self._on_profile_selection_change(profile_spinner, profile_spinner.text, p_index)
            elif type_spinner.text == "AI (Easy)":
                profile_spinner.text = "<N/A for AI>" # Keep it as N/A
                profile_spinner.values = ["<N/A for AI>"] # Or ensure this value is in its list if it's dynamic
                name_input.text = f"AI {p_index + 1} (Easy)"
            else: # Off
                profile_spinner.text = "<Create New Profile>"
                name_input.text = ""


    def show_profile_management_popup(self, instance):
        content_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        # Header for the list
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=dp(5))
        header_layout.add_widget(Label(text="Username", size_hint_x=0.3, font_name=FONT_PATH, font_size=dp(16)))
        header_layout.add_widget(Label(text="High Score", size_hint_x=0.2, font_name=FONT_PATH, font_size=dp(16)))
        header_layout.add_widget(Label(text="Games", size_hint_x=0.2, font_name=FONT_PATH, font_size=dp(16)))
        header_layout.add_widget(Label(text="Actions", size_hint_x=0.3, font_name=FONT_PATH, font_size=dp(16)))
        content_layout.add_widget(header_layout)

        scroll_view = ScrollView(size_hint=(1, 0.8))
        self.profile_list_layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
        self.profile_list_layout.bind(minimum_height=self.profile_list_layout.setter('height'))

        scroll_view.add_widget(self.profile_list_layout)
        content_layout.add_widget(scroll_view)

        self._populate_profile_list_layout()

        close_button = Button(text="Close", size_hint=(1, 0.1), height=dp(40), font_name=FONT_PATH, font_size=dp(18))

        self.profile_management_popup = Popup(
            title="Profile Management",
            content=content_layout,
            size_hint=(0.8, 0.9)
        )
        close_button.bind(on_press=self.profile_management_popup.dismiss)
        content_layout.add_widget(close_button)
        self.profile_management_popup.open()

    def _populate_profile_list_layout(self):
        self.profile_list_layout.clear_widgets()
        profiles_names = self.profile_manager.list_profile_names()
        profiles_names.sort() # Sort for consistent order

        for username in profiles_names:
            profile_obj = self.profile_manager.get_profile(username)
            if profile_obj:
                row_layout = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=None, height=dp(44))

                row_layout.add_widget(Label(text=profile_obj.username, size_hint_x=0.3, font_name=FONT_PATH, font_size=dp(14)))
                row_layout.add_widget(Label(text=str(profile_obj.high_score), size_hint_x=0.2, font_name=FONT_PATH, font_size=dp(14)))
                row_layout.add_widget(Label(text=str(profile_obj.games_played), size_hint_x=0.2, font_name=FONT_PATH, font_size=dp(14)))

                actions_layout = BoxLayout(size_hint_x=0.3, spacing=dp(5))
                rename_button = Button(text="Rename", font_size=dp(14), font_name=FONT_PATH)
                rename_button.bind(on_press=partial(self._rename_profile_prompt, profile_obj.username))
                delete_button = Button(text="Delete", font_size=dp(14), font_name=FONT_PATH)
                delete_button.bind(on_press=partial(self._delete_profile_confirm, profile_obj.username))

                actions_layout.add_widget(rename_button)
                actions_layout.add_widget(delete_button)
                row_layout.add_widget(actions_layout)

                self.profile_list_layout.add_widget(row_layout)

    def _rename_profile_prompt(self, username_to_rename, instance_button_UNUSED=None): # Added default for instance
        rename_popup_content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        rename_popup_content.add_widget(Label(text=f"Renaming: {username_to_rename}", font_name=FONT_PATH, font_size=dp(16)))
        rename_popup_content.add_widget(Label(text="Enter new username:", font_name=FONT_PATH, font_size=dp(14)))

        new_name_input = TextInput(multiline=False, font_name=FONT_PATH, font_size=dp(16), size_hint_y=None, height=dp(40))
        rename_popup_content.add_widget(new_name_input)

        buttons_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
        confirm_button = Button(text="Confirm Rename", font_name=FONT_PATH, font_size=dp(16))
        cancel_button = Button(text="Cancel", font_name=FONT_PATH, font_size=dp(16))

        buttons_layout.add_widget(confirm_button)
        buttons_layout.add_widget(cancel_button)
        rename_popup_content.add_widget(buttons_layout)

        rename_popup = Popup(title="Rename Profile", content=rename_popup_content, size_hint=(0.7, 0.5), auto_dismiss=False)

        confirm_button.bind(on_press=partial(self._execute_rename, old_username=username_to_rename, new_name_input_widget=new_name_input, rename_popup_instance=rename_popup))
        cancel_button.bind(on_press=rename_popup.dismiss)

        rename_popup.open()

    def _execute_rename(self, old_username, new_name_input_widget, rename_popup_instance, instance_button_UNUSED=None): # Added default
        new_username = new_name_input_widget.text.strip()
        try:
            self.profile_manager.rename_profile(old_username, new_username)
            rename_popup_instance.dismiss()
            self._refresh_profile_spinners()
            self._populate_profile_list_layout() # Refresh the list in the main management popup
            if hasattr(self, 'profile_management_popup') and self.profile_management_popup.content: # Check if main popup exists
                 self._populate_profile_list_layout()
        except ValueError as e:
            rename_popup_instance.dismiss() # Dismiss current rename prompt first
            self._show_error_popup(str(e), title="Rename Error")


    def _delete_profile_confirm(self, username_to_delete, instance_button_UNUSED=None): # Added default
        confirm_popup_content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        confirm_popup_content.add_widget(Label(text=f"Are you sure you want to delete '{username_to_delete}'?\nThis cannot be undone.", font_name=FONT_PATH, font_size=dp(16)))

        buttons_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
        confirm_delete_button = Button(text="Yes, Delete", font_name=FONT_PATH, font_size=dp(16), background_color=(0.8,0.2,0.2,1))
        cancel_button = Button(text="No, Cancel", font_name=FONT_PATH, font_size=dp(16))

        buttons_layout.add_widget(confirm_delete_button)
        buttons_layout.add_widget(cancel_button)
        confirm_popup_content.add_widget(buttons_layout)

        confirm_popup = Popup(title="Confirm Deletion", content=confirm_popup_content, size_hint=(0.7, 0.4), auto_dismiss=False)

        confirm_delete_button.bind(on_press=partial(self._execute_delete, username_to_delete=username_to_delete, confirm_popup_instance=confirm_popup))
        cancel_button.bind(on_press=confirm_popup.dismiss)

        confirm_popup.open()

    def _execute_delete(self, username_to_delete, confirm_popup_instance, instance_button_UNUSED=None): # Added default
        try:
            self.profile_manager.delete_profile(username_to_delete)
            confirm_popup_instance.dismiss()
            self._refresh_profile_spinners()
            # Refresh the list in the main management popup if it's open
            if hasattr(self, 'profile_management_popup') and self.profile_management_popup.content:
                 self._populate_profile_list_layout()
        except ValueError as e:
            confirm_popup_instance.dismiss()
            self._show_error_popup(str(e), title="Delete Error")
