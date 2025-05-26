# game_screen.py

import os
import random
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty, NumericProperty
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.app import App # Added import

from custom_widgets import ImageButton
from game_logic import GameState


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.main_layout = BoxLayout(orientation='horizontal')
        self.add_widget(self.main_layout)

        # Initialize sidebar visibility and original width
        self.sidebar_visible = False
        self.sidebar_original_width_hint = 0.3

        # Initialize properties for blinking
        self.blink_event = None
        self.blinking_buttons = []
        self.blinking_animations = []

    def initialize_game(self, player_configurations, grid_size, game_turn_length, marker_percentage=0.1): # player_names -> player_configurations
        self.main_layout.clear_widgets()

        # Initialize GameState
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Pass player_configurations directly to GameState
        self.game_state = GameState(player_configurations, grid_size, script_dir)
        self.game_turn_length = game_turn_length  # Game turn length set by player

        # **Register the callback to handle GameState updates**
        self.game_state.register_callback(self.handle_game_state_update)

        # Sidebar for player information
        self.sidebar_layout = BoxLayout(
            orientation='vertical',
            size_hint=(0, 1),
            padding=[Window.width * 0.01, Window.height * 0.01],
            spacing=Window.height * 0.01
        )
        self.sidebar_layout.opacity = 0
        with self.sidebar_layout.canvas.before:
            Color(0, 0, 0, 1)  # Black background
            self.sidebar_rect = Rectangle(pos=self.sidebar_layout.pos, size=self.sidebar_layout.size)
        self.sidebar_layout.bind(
            pos=lambda instance, value: setattr(self.sidebar_rect, 'pos', value),
            size=lambda instance, value: setattr(self.sidebar_rect, 'size', value)
        )

        self.current_player_label = Label(
            text=f"[b]Current Player:[/b] {self.game_state.players[0]}", # Use game_state.players
            size_hint=(1, 0.1),
            markup=True,
            font_size=Window.height * 0.02,
            color=(1, 1, 1, 1)
        )
        self.player_money_label = Label(
            text=f"Cash: £6000",
            size_hint=(1, 0.1),
            font_size=Window.height * 0.018,
            color=(1, 1, 1, 1)
        )

        # New Holdings Display Structure
        self.holdings_title_label = Label(
            text="[b]Holdings:[/b]",
            markup=True,
            size_hint=(1, 0.05),
            font_size=Window.height * 0.018,
            color=(1,1,1,1)
        )
        self.holdings_display_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.3), # Takes full width of sidebar_layout
            spacing=5 # spacing between each holding row
        )
        self.total_wealth_label = Label( # Repurposed from old player_holdings_label concept
            text="Total Wealth: £0",
            size_hint=(1, 0.05),
            font_size=Window.height * 0.018,
            color=(1,1,1,1)
        )
        # self.company_info_label is removed as per instructions
        self.sidebar_spacer = Label(size_hint=(1, 0.4)) # Corrected size_hint_y to make sum 1.0
        
        self.settings_button = Button(
            text="Settings",
            size_hint=(1, 0.1),
            font_size=Window.height * 0.018 # Match other sidebar elements
        )
        self.settings_button.bind(on_press=self.open_settings_popup)

        # Clear existing widgets from sidebar_layout before adding new ones in correct order
        self.sidebar_layout.clear_widgets() 
        
        # Add widgets in the specified order
        self.sidebar_layout.add_widget(self.current_player_label)       # size_hint_y: 0.1
        self.sidebar_layout.add_widget(self.player_money_label)        # size_hint_y: 0.1
        self.sidebar_layout.add_widget(self.holdings_title_label)      # size_hint_y: 0.05
        self.sidebar_layout.add_widget(self.holdings_display_container) # size_hint_y: 0.3
        self.sidebar_layout.add_widget(self.total_wealth_label)        # size_hint_y: 0.05
        # self.company_info_label is removed from layout
        self.sidebar_layout.add_widget(self.sidebar_spacer)            # size_hint_y: 0.4 (corrected)
        self.sidebar_layout.add_widget(self.settings_button)           # size_hint_y: 0.1
                                                                        # New Total: 0.1+0.1+0.05+0.3+0.05+0.4+0.1 = 1.0

        self.main_layout.add_widget(self.sidebar_layout)

        # Game board layout
        self.game_layout = BoxLayout(
            orientation='vertical', size_hint=(1.0, 1), padding=10, spacing=10
        )

        # Info label to display player actions
        self.info_label = Label(
            text=f"Welcome to Space Monopoly! {self.game_state.players[0]}'s Turn", # Use game_state.players
            size_hint=(1, 0.05),
            font_size=16,
            color=(1, 1, 1, 1)
        )
        self.game_layout.add_widget(self.info_label)

        # Grid layout for the game board
        self.grid_size = grid_size
        self.grid_layout = GridLayout(
            cols=self.grid_size[0], rows=self.grid_size[1], spacing=1, size_hint=(1, 0.85)
        )
        with self.grid_layout.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Darker grey background
            self.grid_rect = Rectangle(pos=self.grid_layout.pos, size=self.grid_layout.size)
        self.grid_layout.bind(
            pos=lambda instance, value: setattr(self.grid_rect, 'pos', value),
            size=lambda instance, value: setattr(self.grid_rect, 'size', value)
        )

        # Initialize grid buttons
        self.grid_buttons = []
        total_cells = self.grid_size[0] * self.grid_size[1]
        # Use the marker_percentage from StartScreen, default to 0.1 if not provided
        max_circles = int(total_cells * marker_percentage)

        # Create a list of all possible (row, col) coordinates
        all_coordinates = []
        for r in range(self.grid_size[1]):
            for c in range(self.grid_size[0]):
                all_coordinates.append((r, c))

        # Randomly shuffle the list of all possible coordinates
        random.shuffle(all_coordinates)

        # Select the first `max_circles` coordinates for "O" markers
        o_marker_locations_list = all_coordinates[:max_circles]
        o_marker_locations_set = set(o_marker_locations_list)

        for row in range(self.grid_size[1]):
            button_row = []
            for col in range(self.grid_size[0]):
                if (row, col) in o_marker_locations_set:
                    btn = Button(
                        text="O",
                        font_size=24,
                        background_normal='',
                        background_color=[0.2, 0.2, 0.2, 1],  # Match grid background
                        color=(1, 1, 1, 1)  # White text for contrast
                    )
                else:
                    btn = ImageButton(
                        source='',  # Initially no image
                        allow_stretch=True,
                        keep_ratio=True,
                        size_hint=(1, 1),
                        coords=(row, col),
                        text=''
                    )
                    btn.bind(on_press=self.on_grid_button_press)
                    # btn.bind(on_release=self.show_company_info) # Removed as per instruction
                    btn.disabled = True  # Initially, all non-circle buttons are disabled

                button_row.append(btn)
                self.grid_layout.add_widget(btn)
            self.grid_buttons.append(button_row)

        # Pass the collected 'O' marker locations to GameState
        self.game_state.set_initial_o_marker_locations(o_marker_locations_set)

        self.game_layout.add_widget(self.grid_layout)

        # Button layout for additional actions
        button_layout = BoxLayout(
            orientation='horizontal', size_hint=(1, 0.1), spacing=10
        )
        self.end_turn_button = Button(
            text="End Turn", on_press=self.process_human_end_turn, font_size=18, # Changed on_press
            disabled=True  # Initially disabled
        )
        self.share_management_button = Button(
            text="Share Management", on_press=self.show_share_management_popup, font_size=18
        )
        self.toggle_sidebar_button = Button(
            text="Toggle Sidebar", on_press=self.toggle_sidebar, font_size=18
        )
        button_layout.add_widget(self.end_turn_button)
        button_layout.add_widget(self.share_management_button)
        button_layout.add_widget(self.toggle_sidebar_button)
        self.game_layout.add_widget(button_layout)

        self.main_layout.add_widget(self.game_layout)
        self.update_player_info()

        # Start the first turn
        self.next_turn()

    def handle_game_state_update(self, updated_entries):
        """
        Callback function to handle updates from GameState.
        It receives a list of tuples: (coords, company_name)
        """
        print(f"Handling game state update with {len(updated_entries)} entries.")
        for coords, company_name in updated_entries:
            row, col = coords
            if 0 <= row < self.grid_size[1] and 0 <= col < self.grid_size[0]:
                button = self.grid_buttons[row][col]
                self.update_grid_button(button, company_name)
                print(f"Updated button at ({row}, {col}) to company '{company_name}'.")
            else:
                print(f"Warning: Coordinates {coords} are out of bounds.")

    def verify_images(self):
        for name, path in self.game_state.company_logos.items():
            if not os.path.exists(path):
                print(f"Error: {path} does not exist.")
            else:
                print(f"Loaded {name} logo from {path}.")
        if not os.path.exists(self.game_state.diamond_image_path):
            print(f"Warning: Diamond image not found at {self.game_state.diamond_image_path}. Falling back to text.")

    def on_grid_button_press(self, instance):
        """
        Handle button press logic when a grid square is clicked.
        """
        # Enable the end turn button after a valid selection
        self.end_turn_button.disabled = False
        if instance.disabled:
            return  # Ignore clicks on disabled buttons

        current_coords = instance.coords
        current_player = self.game_state.players[self.game_state.current_player_index]

        # Check for adjacent companies using company_map
        adjacent_companies = self.game_state.get_adjacent_companies(current_coords)
        if adjacent_companies:
            if len(adjacent_companies) == 1:
                # Expand the existing company
                company_name = adjacent_companies.pop()
                self.game_state.expand_company(current_coords, company_name, current_player)
                # The UI will be updated via the callback
                self.info_label.text = f"{current_player} expanded {company_name}!"
                # Perform flip animation upon expansion
                self.perform_flip_animation(instance)
            else:
                # Merge companies
                self.game_state.merge_companies(current_coords, adjacent_companies, current_player)
                merged_company_name = self.game_state.company_map[current_coords]["company_name"]
                # The UI will be updated via the callback
                self.info_label.text = f"{current_player} merged companies into {merged_company_name}!"
                # Perform flip animation upon merging
                self.perform_flip_animation(instance)
        else: # No adjacent companies
            # current_player is already defined in this scope
            if self.game_state.available_company_names and self.game_state._can_found_company_at(current_coords):
                # Create a new company
                company_name, message = self.game_state.create_new_company(current_coords, current_player)
                if company_name:
                    # The UI will be updated via the callback from create_new_company
                    self.info_label.text = message
                    self.perform_flip_animation(instance) # instance is the button
                else:
                    # create_new_company failed (e.g. trying to create on 'O' marker itself)
                    self.info_label.text = message
                    # Potentially place diamond if creation failed?
                    # For now, let's assume if _can_found_company_at was true, but create_new_company failed,
                    # it's a specific rule interaction (like on 'O' marker) and not a diamond placement.
                    # The original human logic didn't have a fallback to diamond here if is_adjacent_to was true.
                    # However, the AI logic *does* fallback. For consistency, maybe human should too.
                    # Let's make it consistent: if create_new_company fails, human also tries diamond.
                    if "Cannot create company on an 'O' marker tile" in message: # Or similar check
                        self.info_label.text = message + " Try placing a diamond." # Guide user
                        # No automatic diamond placement here, user must click again if they want diamond.
                        # Button will be disabled after this interaction by disable_grid_buttons().
                        # This makes it less like AI, but gives human more control after failure.
                        pass
                    # If create_new_company failed for other reasons (e.g. no names), message is already set.
            else: # No available company names or cannot found company at current_coords
                # Place a diamond
                self.place_diamond(instance) # instance is the button
                # self.info_label.text is set by place_diamond or its callers if needed.
                # For direct call here, we might need:
                # self.info_label.text = f"{current_player} placed a diamond."
                # However, self.place_diamond itself calls game_state.place_diamond which returns a message.
                # The current self.place_diamond(self, instance) in GameScreen:
                #   success, message = self.game_state.place_diamond(current_coords, current_player_name)
                #   if success: # updates visuals
                #   else: self.info_label.text = message
                # This seems fine. If place_diamond fails, it sets info_label. If it succeeds, a message is not explicitly set here,
                # but game_state.place_diamond does return one. Let's ensure a generic success message if place_diamond itself doesn't set one.
                # Checking place_diamond: it *does not* set info_label on success.
                # So we should set it here.
                if instance.source == self.game_state.diamond_image_path or instance.text == "◆": # Check if diamond was actually placed
                     self.info_label.text = f"{current_player} placed a diamond at {current_coords}."
                # If place_diamond failed, it will have set its own error message.

        # After the move, expand companies into adjacent diamonds
        self.expand_companies_into_adjacent_diamonds()
        self.disable_grid_buttons()
        self.update_player_info()
        self.end_turn_button.disabled = False # Enable end turn button after human move

    def perform_flip_animation(self, instance):
        """
        Performs a single flip animation on the given instance.
        This is used when a diamond is created or converted into a company.
        """
        instance.scale_x = 1  # Reset scale
        flip_animation = Animation(scale_x=-1, duration=0.25) + Animation(scale_x=1, duration=0.25)
        flip_animation.start(instance)

    def place_diamond(self, instance):
        """
        Place a diamond on the selected square and handle potential mergers.
        """
        current_coords = instance.coords
        current_player_name = self.game_state.players[self.game_state.current_player_index]
        success, message = self.game_state.place_diamond(current_coords, current_player_name)
        if success:
            if os.path.exists(self.game_state.diamond_image_path):
                # Set the image source to diamond.png
                instance.source = self.game_state.diamond_image_path
                instance.reload()
                instance.color = [1, 1, 1, 1]
                # Start single flip animation
                instance.scale_x = 1
                animation = Animation(scale_x=-1, duration=0.5) + Animation(scale_x=1, duration=0.5)
                # Removed animation.repeat = True to prevent continuous flipping
                animation.start(instance)
            else:
                # Fallback to using Unicode diamond character
                instance.text = u"◆"
                instance.color = (1, 1, 1, 1)
                instance.font_size = 24  # Increased font size for visibility
        else:
            self.info_label.text = message

    def expand_companies_into_adjacent_diamonds(self):
        """
        Check all diamonds on the board to see if they are adjacent to any companies.
        If so, handle expansions or mergers accordingly.
        """
        diamonds_to_remove = set()
        for diamond_coords in list(self.game_state.diamond_positions):
            adjacent_companies = self.game_state.get_adjacent_companies(diamond_coords)
            if adjacent_companies:
                button = self.grid_buttons[diamond_coords[0]][diamond_coords[1]]
                if len(adjacent_companies) == 1:
                    # Expand the company into the diamond
                    company_name = adjacent_companies.pop()
                    self.game_state.expand_company(diamond_coords, company_name, self.game_state.players[self.game_state.current_player_index])
                    # The UI will be updated via the callback
                    self.info_label.text += f" {company_name} expanded into a diamond!"
                    # Perform flip animation upon expansion
                    self.perform_flip_animation(button)
                else:
                    # Merge companies via the diamond
                    self.game_state.merge_companies(diamond_coords, adjacent_companies, self.game_state.players[self.game_state.current_player_index])
                    merged_company_name = self.game_state.company_map[diamond_coords]["company_name"]
                    # The UI will be updated via the callback
                    self.info_label.text += f" Companies merged into {merged_company_name} via a diamond!"
                    # Perform flip animation upon merging
                    self.perform_flip_animation(button)
                # Mark the diamond for removal
                diamonds_to_remove.add(diamond_coords)
        # Remove the diamonds that have been absorbed
        self.game_state.diamond_positions -= diamonds_to_remove

    def update_grid_button(self, button, company_name):
        """
        Update the grid button to reflect the company.
        This includes setting the correct logo and color.
        """
        logo_path = self.game_state.company_logos.get(company_name, '')

        if os.path.exists(logo_path):
            button.source = ''  # Clear current image
            button.reload()     # Process clearing

            def _set_final_logo(dt): # Inner callback
                button.source = logo_path
                button.reload()
                button.color = [1, 1, 1, 1] # Reset color with logo
                print(f"Set button source (scheduled) to '{logo_path}' for company '{company_name}'.")
            
            Clock.schedule_once(_set_final_logo, 0) # Schedule for next frame
        
        else: # Fallback if logo doesn't exist
            button.source = '' # Ensure no image is set
            button.reload()    # Process clearing
            # Fallback color logic from previous implementation (tinting the non-existent image)
            default_color = [0.5, 0.5, 0.5, 1] # A neutral default color
            if hasattr(self.game_state, 'company_colors'):
                button.color = self.game_state.company_colors.get(company_name, default_color)
                # This print might be confusing as it says "Set button color" but it's tinting an empty source.
                # For consistency with previous code, it's kept. A better approach might be button.background_color.
                print(f"Logo for '{company_name}' not found. Set button color (tint) to '{button.color}'.")
            else:
                button.color = default_color
                print(f"Logo for '{company_name}' not found and no company_colors. Set button color (tint) to default '{button.color}'.")

        # These should apply immediately:
        button.text = ""
        button.angle = 0
        button.scale_x = 1
        if hasattr(button, 'anim') and button.anim:
            button.anim.cancel(button)
            # Using delattr as suggested in the problem description for safety
            if hasattr(button, 'anim'): # Check again in case cancel somehow removed it
                 delattr(button, 'anim')
        button.disabled = True
        print(f"Button at ({button.coords[0]}, {button.coords[1]}) properties reset and disabled.")

    def next_turn(self, instance=None):
        """
        Proceed to the next player's turn.
        """
        # Disable the end turn button until a new action is taken
        self.end_turn_button.disabled = True 
        # Removed logic for incrementing player index and turn counter (handled by GameState.end_turn())
        
        self.update_player_info()

        current_player_name = self.game_state.players[self.game_state.current_player_index]
        player_type = self.game_state.get_player_type(current_player_name)
        self.info_label.text = f"{current_player_name}'s Turn ({player_type})"

        if player_type == "AI (Easy)":
            self.info_label.text += " - Thinking..."
            self.disable_grid_buttons() # Stops blinking, disables all grid buttons
            self.end_turn_button.disabled = True
            Clock.schedule_once(self.run_ai_turn, 1.0) # 1 second delay
        else: # Human player
            self.enable_grid_buttons()
            self.end_turn_button.disabled = True # Will be enabled once human makes a move

        # End game check after turn length reached
        if self.game_state.turn_counter >= self.game_turn_length:
            self.end_game()

    def run_ai_turn(self, dt):
        """
        Executes an AI player's turn.
        """
        current_player_name = self.game_state.players[self.game_state.current_player_index]
        selected_cell, action_message = self.game_state.ai_take_turn(current_player_name)

        self.info_label.text = action_message # Display AI action

        # Visual Update for AI's move (specifically for diamonds, as company updates are handled by callback)
        if selected_cell is not None and \
           0 <= selected_cell[0] < self.grid_size[1] and \
           0 <= selected_cell[1] < self.grid_size[0]:
            
            # If it's not a company tile after AI's move, then it might be a diamond
            # Company tiles are updated by the callback handle_game_state_update.
            if selected_cell not in self.game_state.company_map: 
                button = self.grid_buttons[selected_cell[0]][selected_cell[1]]
                if os.path.exists(self.game_state.diamond_image_path):
                    button.source = self.game_state.diamond_image_path
                    button.reload()
                else:
                    button.text = "◆"
                    button.font_size = 24
                button.color = [1, 1, 1, 1]
                print(f"AI Debug: Updated button {selected_cell} for diamond after AI turn.")
            # If it IS in company_map, the callback will handle it.

        elif selected_cell is not None: # selected_cell was not None, but was out of bounds
            print(f"AI Error: selected_cell {selected_cell} is out of bounds for the grid. Rows: {self.grid_size[1]}, Cols: {self.grid_size[0]}")
            # info_label is already set by action_message.
            
        # If selected_cell is None, info_label already has a message like "no available moves".
        # Nothing specific to do for visuals if selected_cell is None.

        self.update_player_info()
        self.expand_companies_into_adjacent_diamonds() # Important after AI move
        self.disable_grid_buttons() # Ensure grid is disabled after AI move

        success, end_turn_message = self.game_state.end_turn()

        if not success:
            self.info_label.text = f"AI Error: {end_turn_message}" # Update info label with error
            # Potentially show a popup or handle error more gracefully
            # For now, allowing human to see the issue and maybe End Turn button becomes active
            self.end_turn_button.disabled = False 
            return # Do not proceed to next turn if AI failed its turn obligation

        # self.game_state.end_turn() has updated player_index and turn_counter
        self.next_turn() # Sets up UI for the new current player (Human or AI)

    def process_human_end_turn(self, instance):
        """
        Processes a human player's attempt to end their turn.
        """
        current_player_name = self.game_state.players[self.game_state.current_player_index]
        success, message = self.game_state.end_turn()

        if success:
            self.info_label.text = message
            self.next_turn()
        else: # Player hasn't made a move or other end_turn condition not met
            self.info_label.text = message
            Popup(title='Move Required', 
                  content=Label(text=message), 
                  size_hint=(0.5, 0.3)).open()

    def buy_shares(self, company_name, player, amount):
        """
        Allow players to buy shares in a company.
        """
        success, message = self.game_state.buy_shares(company_name, player, amount)
        self.info_label.text = message
        self.update_player_info()

    def sell_shares(self, company_name, player, amount):
        """
        Allow players to sell shares in a company.
        """
        success, message = self.game_state.sell_shares(company_name, player, amount)
        self.info_label.text = message
        self.update_player_info()

    def show_share_management_popup(self, instance):
        """
        Show a popup to manage shares (buy or sell).
        """
        current_player = self.game_state.players[self.game_state.current_player_index]
        cash = self.game_state.player_wealth[current_player]
        holdings_value = 0
        for company, num_shares in self.game_state.player_shares[current_player].items():
            if company in self.game_state.company_info:
                share_value = self.game_state.company_info[company]["value"]
                total_share_value = share_value * num_shares
                holdings_value += total_share_value
        total_wealth = cash + holdings_value

        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Player's cash and holdings at the top
        player_info_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        player_cash_label = Label(text=f"Cash: £{cash}", size_hint=(0.5, 1))
        player_holdings_label = Label(text=f"Holdings Value: £{holdings_value}", size_hint=(0.5, 1))
        player_info_layout.add_widget(player_cash_label)
        player_info_layout.add_widget(player_holdings_label)
        content.add_widget(player_info_layout)

        # Company information header
        header_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        header_layout.add_widget(Label(text="[b]Logo[/b]", size_hint=(0.2, 1), markup=True))
        header_layout.add_widget(Label(text="[b]Company[/b]", size_hint=(0.2, 1), markup=True))
        header_layout.add_widget(Label(text="[b]Price[/b]", size_hint=(0.2, 1), markup=True))
        header_layout.add_widget(Label(text="[b]Your Shares[/b]", size_hint=(0.2, 1), markup=True))
        header_layout.add_widget(Label(text="[b]Total Value[/b]", size_hint=(0.2, 1), markup=True))
        content.add_widget(header_layout)

        # List of companies with their prices and player's holdings
        companies_layout = GridLayout(cols=1, size_hint=(1, 0.4))
        for company in self.game_state.company_info.keys():
            company_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=60)

            # Add Company Logo
            logo_path = self.game_state.company_logos.get(company, '')
            if os.path.exists(logo_path):
                logo = Image(source=logo_path, size_hint=(0.2, 1), allow_stretch=True, keep_ratio=True)
            else:
                # Placeholder if logo not found
                logo = Label(text="No Logo", size_hint=(0.2, 1))
            company_layout.add_widget(logo)

            # Add Company Name
            company_label = Label(text=company, size_hint=(0.2, 1), halign='left', valign='middle')
            company_label.bind(size=company_label.setter('text_size'))
            company_layout.add_widget(company_label)

            # Add Company Price
            price = self.game_state.company_info[company]["value"]
            price_label = Label(text=f"£{price}", size_hint=(0.2, 1))
            company_layout.add_widget(price_label)

            # Add Player's Shares
            num_shares = self.game_state.player_shares[current_player].get(company, 0)
            shares_label = Label(text=str(num_shares), size_hint=(0.2, 1))
            company_layout.add_widget(shares_label)

            # Add Total Value
            total_value = num_shares * price
            total_value_label = Label(text=f"£{total_value}", size_hint=(0.2, 1))
            company_layout.add_widget(total_value_label)

            companies_layout.add_widget(company_layout)
        content.add_widget(companies_layout)

        # Spinner for selecting a company
        available_companies = [
            name for name in self.game_state.company_info.keys()
        ]
        company_spinner = Spinner(
            text='Select Company', values=available_companies, size_hint=(1, 0.1)
        )
        content.add_widget(company_spinner)

        # Slider for selecting the number of shares
        amount_slider = Slider(
            min=0, max=10, value=0, step=1, size_hint=(1, 0.1)
        )
        amount_label = Label(
            text=f'Quantity: {int(amount_slider.value)}', size_hint=(1, 0.05)
        )
        cost_label = Label(
            text='Total Cost: £0', size_hint=(1, 0.05)
        )

        # Buy Max and Sell Max buttons
        max_buttons_layout = BoxLayout(size_hint=(1, 0.1))
        buy_max_button = Button(text='Buy Max')
        sell_max_button = Button(text='Sell Max')
        max_buttons_layout.add_widget(buy_max_button)
        max_buttons_layout.add_widget(sell_max_button)
        content.add_widget(max_buttons_layout)

        # Add the labels and slider to the content
        content.add_widget(amount_label)
        content.add_widget(cost_label)
        content.add_widget(amount_slider)

        # Toggle buttons for Buy/Sell
        toggle_layout = BoxLayout(size_hint=(1, 0.1))
        buy_toggle = ToggleButton(text='Buy', group='action', state='down')
        sell_toggle = ToggleButton(text='Sell', group='action')
        toggle_layout.add_widget(buy_toggle)
        toggle_layout.add_widget(sell_toggle)
        content.add_widget(toggle_layout)

        # Action button
        action_button = Button(text='Confirm', size_hint=(1, 0.1))
        content.add_widget(action_button)

        popup = Popup(
            title='Share Management', content=content, size_hint=(0.8, 0.9)
        )

        # Function to update the slider and cost/proceeds label based on company selection and action
        def update_slider_and_cost(instance, value):
            action = 'buy' if buy_toggle.state == 'down' else 'sell'
            selected_company = company_spinner.text
            if selected_company != 'Select Company':
                share_price = self.game_state.company_info[selected_company]['value']
                if action == 'buy':
                    max_shares = self.game_state.player_wealth[current_player] // share_price
                else:
                    max_shares = self.game_state.player_shares[current_player].get(selected_company, 0)
                max_shares = int(max_shares)
                amount_slider.max = max_shares if max_shares > 0 else 10
                if amount_slider.value > max_shares:
                    amount_slider.value = max_shares
                amount_slider.min = 0
                amount_label.text = f'Quantity: {int(amount_slider.value)}'
                total_amount = int(amount_slider.value) * share_price
                cost_label.text = f'{"Total Cost" if action == "buy" else "Total Proceeds"}: £{total_amount}'
            else:
                amount_slider.value = 0
                amount_slider.max = 0
                amount_label.text = 'Quantity: 0'
                cost_label.text = 'Total Cost: £0'

        # Update slider and cost when company or action changes
        company_spinner.bind(text=update_slider_and_cost)
        buy_toggle.bind(state=update_slider_and_cost)
        sell_toggle.bind(state=update_slider_and_cost)

        # Update cost when slider value changes
        def update_amount_labels(instance, value):
            action = 'buy' if buy_toggle.state == 'down' else 'sell'
            selected_company = company_spinner.text
            if selected_company != 'Select Company':
                share_price = self.game_state.company_info[selected_company]['value']
                amount_label.text = f'Quantity: {int(value)}'
                total_amount = int(value) * share_price
                cost_label.text = f'{"Total Cost" if action == "buy" else "Total Proceeds"}: £{total_amount}'
            else:
                amount_label.text = 'Quantity: 0'
                cost_label.text = 'Total Cost: £0'

        amount_slider.bind(value=update_amount_labels)

        # Buy Max and Sell Max button functionality
        def buy_max(instance):
            buy_toggle.state = 'down'
            sell_toggle.state = 'normal'
            update_slider_and_cost(None, None)
            amount_slider.value = amount_slider.max

        def sell_max(instance):
            sell_toggle.state = 'down'
            buy_toggle.state = 'normal'
            update_slider_and_cost(None, None)
            amount_slider.value = amount_slider.max

        buy_max_button.bind(on_press=buy_max)
        sell_max_button.bind(on_press=sell_max)

        # Close the popup after performing the action
        def perform_action_and_close(instance):
            action = 'buy' if buy_toggle.state == 'down' else 'sell'
            self.perform_share_management(
                company_spinner.text, int(amount_slider.value), action
            )
            popup.dismiss()

        action_button.bind(on_press=perform_action_and_close)
        popup.open()

    def perform_share_management(self, company_name, amount, action):
        """
        Perform the share management action (buy or sell) based on user input.
        """
        if company_name != 'Select Company' and amount > 0:
            player = self.game_state.players[self.game_state.current_player_index]
            if action == 'buy':
                self.buy_shares(company_name, player, amount)
            else:
                self.sell_shares(company_name, player, amount)
        else:
            self.info_label.text = "Please select a valid company and amount."

    def disable_grid_buttons(self):
        """
        Reset unchosen highlighted squares and disable all buttons.
        """
        for row in self.grid_buttons:
            for button in row:
                if isinstance(button, ImageButton):
                    # Reset color to default regardless of source
                    button.color = [1, 1, 1, 1]
                    button.disabled = True  # Disable all buttons
                else:
                    if button.background_color == [0.3, 0.3, 0.8, 1]:  # Light blue
                        button.background_color = [0.2, 0.2, 0.2, 1]  # Reset to dark grey
                    button.disabled = True  # Disable all buttons

        # Stop blinking animations
        for animation, button in zip(self.blinking_animations, self.blinking_buttons):
            animation.cancel(button)
        self.blinking_animations = []
        self.blinking_buttons = []

    def enable_grid_buttons(self):
        """
        Enable a random selection of empty squares for the next turn.
        """
        empty_squares = [
            (r, c)
            for r in range(self.grid_size[1])
            for c in range(self.grid_size[0])
            if isinstance(self.grid_buttons[r][c], ImageButton) and self.grid_buttons[r][c].source == ''
        ]
        if not empty_squares:
            self.info_label.text = "No available squares to enable."
            return

        num_to_enable = max(1, int(0.05 * len(empty_squares)))  # Enable 5% of empty squares
        if num_to_enable > len(empty_squares):
            num_to_enable = len(empty_squares)  # Avoid sampling more squares than available
        enabled_squares = random.sample(empty_squares, num_to_enable)
        self.blinking_buttons = []  # Reset the blinking buttons list
        self.blinking_animations = []  # Reset the animations list

        for r, c in enabled_squares:
            button = self.grid_buttons[r][c]
            button.disabled = False
            # Initialize button color to light blue
            button.color = [0.3, 0.3, 0.8, 1]
            self.blinking_buttons.append(button)  # Add to blinking buttons
            print(f"Enabled square at ({r}, {c}) for player '{self.game_state.players[self.game_state.current_player_index]}'.")
            # Create the animation for this button
            animation = Animation(color=[1, 1, 1, 1], duration=0.5) + Animation(color=[0.3, 0.3, 0.8, 1], duration=0.5)
            animation.repeat = True
            animation.start(button)
            self.blinking_animations.append(animation)

    def end_game(self):
        """
        Calculate final wealth and determine the winner.
        """
        player_wealth_summary = {
            player: self.game_state.player_wealth[player] for player in self.game_state.players
        }
        for player, shares in self.game_state.player_shares.items():
            for company, num_shares in shares.items():
                if company in self.game_state.company_info:
                    company_value = self.game_state.company_info[company]["value"]
                    player_wealth_summary[player] += num_shares * company_value

        # Find the player with the highest wealth
        winner = max(player_wealth_summary, key=player_wealth_summary.get)
        self.info_label.text = (
            f"Game over! {winner} wins with £{player_wealth_summary[winner]}!"
        )
        print(f"Game Over! Winner: {winner} with £{player_wealth_summary[winner]}.")
        self.disable_grid_buttons()

    def update_player_info(self):
        """
        Update the sidebar with the current player's information.
        """
        current_player = self.game_state.players[self.game_state.current_player_index]
        cash = self.game_state.player_wealth[current_player]
        holdings_value = 0

        self.holdings_display_container.clear_widgets() # Clear previous holdings

        # Populate new holdings display
        for company, num_shares in self.game_state.player_shares[current_player].items():
            if company in self.game_state.company_info: # Should always be true if data is consistent
                share_value = self.game_state.company_info[company]['value']
                total_share_value = share_value * num_shares
                holdings_value += total_share_value

                holding_row_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=int(Window.height * 0.04))
                
                logo_path = self.game_state.company_logos.get(company, '')
                if os.path.exists(logo_path):
                    logo_widget = Image(source=logo_path, size_hint_x=0.2, allow_stretch=True, keep_ratio=True)
                else:
                    logo_widget = Label(text=" ", size_hint_x=0.2) # Placeholder
                holding_row_layout.add_widget(logo_widget)

                holding_detail_text = f"{company}: {num_shares} @ £{share_value} (£{total_share_value})"
                detail_label = Label(
                    text=holding_detail_text,
                    size_hint_x=0.8,
                    font_size=int(Window.height * 0.015),
                    color=(1,1,1,1),
                    halign='left',
                    valign='middle'
                )
                detail_label.bind(size=detail_label.setter('text_size')) # For text wrapping
                holding_row_layout.add_widget(detail_label)
                
                self.holdings_display_container.add_widget(holding_row_layout)

        total_wealth = cash + holdings_value

        self.current_player_label.text = f"[b]Current Player:[/b] {current_player}"
        self.player_money_label.text = f"Cash: £{cash}"
        self.total_wealth_label.text = f"Total Wealth: £{total_wealth}"
        # The old self.player_holdings_label is no longer used for this combined text.

    def open_settings_popup(self, instance):
        """
        Opens a settings popup with options to restart or go to main menu.
        """
        content_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Font size adjustment
        font_label = Label(text="Adjust Font Size:", size_hint_y=None, height=44)
        content_layout.add_widget(font_label)

        # Assuming default Kivy font size is around 15-16sp. Slider range 10-30sp.
        # Default value can be set to the current global font size if accessible, or a sensible default.
        font_slider = Slider(min=10, max=30, value=16, step=1, size_hint_y=None, height=44)
        self.font_value_label = Label(text=f"Current Size: {int(font_slider.value)}", size_hint_y=None, height=44)
        
        font_slider.bind(value=self.on_font_slider_change)
        
        content_layout.add_widget(self.font_value_label)
        content_layout.add_widget(font_slider)

        # Spacer or separator can be added here if needed for visual separation
        # content_layout.add_widget(Label(size_hint_y=None, height=20)) # Example spacer

        restart_button = Button(text="Restart Game", size_hint_y=None, height=44)
        restart_button.bind(on_press=self.restart_game_action)
        content_layout.add_widget(restart_button)

        main_menu_button = Button(text="Go to Main Menu", size_hint_y=None, height=44)
        main_menu_button.bind(on_press=self.go_to_main_menu_action)
        content_layout.add_widget(main_menu_button)

        # Store the popup instance to be able to dismiss it from actions
        self.settings_popup = Popup(
            title="Settings",
            content=content_layout,
            size_hint=(0.6, 0.4) # 60% width, 40% height
        )
        self.settings_popup.open()

    def restart_game_action(self, instance):
        """
        Action for restarting the game. Navigates to the 'start' screen.
        """
        if hasattr(self, 'settings_popup') and self.settings_popup.parent:
            self.settings_popup.dismiss()
        
        App.get_running_app().root.current = 'start'
        print("Restart Game button pressed - navigating to start screen.")

    def go_to_main_menu_action(self, instance):
        """
        Action for going to the main menu. Navigates to the 'start' screen.
        """
        if hasattr(self, 'settings_popup') and self.settings_popup.parent:
            self.settings_popup.dismiss()

        App.get_running_app().root.current = 'start'
        print("Go to Main Menu button pressed - navigating to start screen.")

    def on_font_slider_change(self, instance, value):
        """
        Called when the font size slider value changes.
        Updates the label displaying the current font size.
        """
        new_font_size = int(value)
        self.font_value_label.text = f"Current Size: {new_font_size}"
        print(f"Font size changed to: {new_font_size}")

        # Apply the new font size to relevant labels
        if hasattr(self, 'info_label'):
            self.info_label.font_size = new_font_size
        
        if hasattr(self, 'current_player_label'):
            self.current_player_label.font_size = new_font_size
            
        if hasattr(self, 'player_money_label'):
            self.player_money_label.font_size = new_font_size
            
        if hasattr(self, 'player_holdings_label'):
            # self.player_holdings_label is now self.total_wealth_label
            # If there's a specific label for holdings text that needs font adjustment,
            # it would be within holdings_display_container, and those are created dynamically.
            # The title self.holdings_title_label could be adjusted here if needed.
            # For now, the prompt doesn't specify changing font of dynamically created labels.
            pass # No direct self.player_holdings_label to update font size for.
            
        if hasattr(self, 'total_wealth_label'): # Check for the new total wealth label
            self.total_wealth_label.font_size = new_font_size

        # self.company_info_label is removed.
        # if hasattr(self, 'company_info_label'):
        #    self.company_info_label.font_size = new_font_size
        
        # Consider also updating font sizes of buttons or other elements if desired
        # For example, the settings popup buttons themselves, or sidebar buttons.
        # For now, sticking to the primary informational labels.
        
        # Note: If labels within show_company_info popup need dynamic font updates,
        # that method would also need to be aware of the current global font size setting.
        # This current implementation changes font_size for labels directly managed by GameScreen.

    def _trigger_grid_layout_update(self, animation, widget):
        # It's good practice to check if the layouts exist, though they should.
        if hasattr(self, 'game_layout') and self.game_layout:
            self.game_layout.do_layout()
        if hasattr(self, 'grid_layout') and self.grid_layout:
            self.grid_layout.do_layout()
        print("Triggered grid layout update via on_complete") # Optional: for debugging

    def toggle_sidebar(self, instance):
        """
        Toggles the visibility of the sidebar with an animation.
        The 'instance' argument is passed by Kivy when a button calls this method.
        """
        if self.sidebar_visible:
            self.animate_sidebar_close()
        else:
            self.animate_sidebar_open()

    def animate_sidebar_open(self):
        """
        Animates the sidebar to open (slide in from the left).
        """
        self.sidebar_visible = True
        self.game_layout.size_hint_x = 1 - self.sidebar_original_width_hint
        anim = Animation(size_hint_x=self.sidebar_original_width_hint, opacity=1, duration=0.3)
        anim.bind(on_complete=self._trigger_grid_layout_update) # New line
        anim.start(self.sidebar_layout)

    def animate_sidebar_close(self):
        """
        Animates the sidebar to close (slide out to the left).
        """
        self.sidebar_visible = False
        self.game_layout.size_hint_x = 1.0
        anim = Animation(size_hint_x=0, opacity=0, duration=0.3)
        anim.bind(on_complete=self._trigger_grid_layout_update) # New line
        anim.start(self.sidebar_layout)
