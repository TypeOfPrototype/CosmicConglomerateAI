import unittest
from unittest.mock import MagicMock, patch
import os

# Add project root to sys.path to allow importing project modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kivy.uix.button import Button
from kivy.uix.slider import Slider

# Since Kivy properties are often initialized in a Kivy-specific way,
# and we are not running a full Kivy app, we might need to mock parts of Kivy's infrastructure
# or ensure that Kivy is initialized minimally if properties rely on that.
# For this test, direct instantiation and attribute setting should work for non-graphical parts.

from game_screen import GameScreen
from start_screen import StartScreen
from custom_widgets import ImageButton # Needed for GameScreen

# Minimal Kivy App Mock to allow widget instantiation if needed
class MinimalKivyAppMock:
    def __init__(self):
        self.root = None

    def run(self):
        pass

@patch('kivy.core.window.Window', MagicMock()) # Mock Window
@patch('kivy.uix.image.Image.source', MagicMock()) # Mock Image source loading
@patch('kivy.uix.label.Label.font_name', MagicMock(return_value='Roboto')) # Mock font loading
@patch('kivy.uix.textinput.TextInput', MagicMock()) # Mock TextInput
@patch('kivy.uix.spinner.Spinner', MagicMock()) # Mock Spinner
@patch('main.SpaceMonopolyApp') # Mock the main app if it's imported by screens
class TestGameSetup(unittest.TestCase):

    def setUp(self):
        # Mock os.path.dirname and os.path.abspath for GameState if it uses them for path resolution
        # This is important if GameState tries to load assets based on __file__
        self.mock_os_path()

        self.game_screen = GameScreen(name='game')
        self.start_screen = StartScreen(name='start')

        # Mock the screen manager for StartScreen
        self.mock_screen_manager = MagicMock()
        self.start_screen.manager = self.mock_screen_manager
        self.mock_screen_manager.get_screen = MagicMock(return_value=self.game_screen)

    def mock_os_path(self):
        # Mock os.path.dirname and abspath to prevent issues with __file__ in GameState
        # This ensures that asset paths are based on a predictable root, not the test file's location.
        # In GameState, script_dir = os.path.dirname(os.path.abspath(__file__))
        # We need to ensure this doesn't break when tests are run from a different directory.
        # For this test, we can mock it to return a dummy path if asset loading isn't critical.
        # If asset loading *is* critical, this mock would need to point to the actual asset directory.
        self.patcher_dirname = patch('os.path.dirname', MagicMock(return_value='/fake/path'))
        self.patcher_abspath = patch('os.path.abspath', MagicMock(return_value='/fake/path/game_logic.py'))
        self.mock_dirname = self.patcher_dirname.start()
        self.mock_abspath = self.patcher_abspath.start()

    def tearDown(self):
        self.patcher_dirname.stop()
        self.patcher_abspath.stop()
        # Clean up any Kivy specific global settings if necessary
        pass

    def test_o_marker_count(self):
        grid_size = (10, 10)
        marker_percentage = 0.20  # 20%
        total_cells = grid_size[0] * grid_size[1]
        expected_o_markers = int(total_cells * marker_percentage)

        # Mock necessary parts of GameScreen that are UI-heavy or rely on Kivy app lifecycle
        # We are primarily testing the logic within initialize_game, not the full UI rendering.
        self.game_screen.game_state = MagicMock() # Mock GameState to avoid its internal logic
        self.game_screen.grid_layout = MagicMock() # Mock GridLayout, we only care about buttons added
        self.game_screen.grid_layout.add_widget = MagicMock() # Mock add_widget

        # Call initialize_game
        self.game_screen.initialize_game(
            player_names=['Player 1', 'Player 2'],
            grid_size=grid_size,
            game_turn_length=80,
            marker_percentage=marker_percentage
        )

        # Count 'O' markers
        o_marker_count = 0
        for row_buttons in self.game_screen.grid_buttons:
            for button in row_buttons:
                if isinstance(button, Button) and button.text == "O":
                    o_marker_count += 1
        
        self.assertEqual(o_marker_count, expected_o_markers,
                         f"Expected {expected_o_markers} 'O' markers, but found {o_marker_count}")

    def test_o_marker_distribution(self):
        grid_size = (20, 20) # Rows, Cols
        marker_percentage = 0.10 # 10%
        
        self.game_screen.game_state = MagicMock()
        self.game_screen.grid_layout = MagicMock()
        self.game_screen.grid_layout.add_widget = MagicMock()

        self.game_screen.initialize_game(
            player_names=['P1', 'P2'],
            grid_size=grid_size,
            game_turn_length=80,
            marker_percentage=marker_percentage
        )

        o_marker_coords = []
        for r_idx, row_buttons in enumerate(self.game_screen.grid_buttons):
            for c_idx, button in enumerate(row_buttons):
                if isinstance(button, Button) and button.text == "O":
                    o_marker_coords.append((r_idx, c_idx))

        self.assertGreater(len(o_marker_coords), 0, "No 'O' markers found on the grid.")

        rows, cols = grid_size
        mid_row = rows // 2
        mid_col = cols // 2

        quadrants = {
            "top_left": False, "top_right": False,
            "bottom_left": False, "bottom_right": False
        }

        for r, c in o_marker_coords:
            if r < mid_row and c < mid_col:
                quadrants["top_left"] = True
            elif r < mid_row and c >= mid_col:
                quadrants["top_right"] = True
            elif r >= mid_row and c < mid_col:
                quadrants["bottom_left"] = True
            elif r >= mid_row and c >= mid_col:
                quadrants["bottom_right"] = True
        
        for quadrant, present in quadrants.items():
            self.assertTrue(present, f"No 'O' markers found in the {quadrant} quadrant.")

    def test_marker_percentage_passing_from_start_screen(self):
        # Mock the initialize_game method on the GameScreen instance
        self.game_screen.initialize_game = MagicMock()

        # Set up StartScreen's UI elements that are accessed in start_game
        self.start_screen.player_inputs = [MagicMock(text='P1'), MagicMock(text='P2')]
        self.start_screen.grid_size_spinner = MagicMock(text='10x10')
        self.start_screen.turn_length_input = MagicMock(text='50')
        
        # Create and set the marker_percentage_slider
        self.start_screen.marker_percentage_slider = Slider(min=0, max=50, value=15)
        # Ensure the label exists if _update_marker_percentage_label is called by slider value change
        self.start_screen.marker_percentage_value_label = MagicMock()


        # Call the start_game method
        self.start_screen.start_game(None) # Argument is instance, can be None for this test

        expected_marker_percentage = 0.15 # 15 / 100.0

        # Assert that initialize_game was called with the correct marker_percentage
        self.game_screen.initialize_game.assert_called_once()
        args, kwargs = self.game_screen.initialize_game.call_args
        
        # The marker_percentage is passed as the 4th positional argument (index 3)
        # or as a keyword argument. Let's check kwargs first, then args.
        if 'marker_percentage' in kwargs:
            passed_marker_percentage = kwargs['marker_percentage']
        elif len(args) > 3: # player_names, grid_size, game_turn_length, marker_percentage
            passed_marker_percentage = args[3]
        else:
            self.fail("marker_percentage not found in call to initialize_game")

        self.assertAlmostEqual(passed_marker_percentage, expected_marker_percentage, places=2,
                               msg="Marker percentage passed from StartScreen to GameScreen is incorrect.")
        
        # Also check other default parameters if necessary
        self.assertEqual(args[0], ['P1', 'P2']) # player_names
        self.assertEqual(args[1], (10,10))      # grid_size
        self.assertEqual(args[2], 50)           # game_turn_length


if __name__ == '__main__':
    # Kivy setup might be needed if widgets directly interact with Window or App during init
    # However, by mocking Window and specific widget properties, we can often avoid full Kivy app init.
    # For these tests, we assume that the logic being tested in initialize_game and start_game
    # doesn't deeply depend on a running Kivy application instance.
    
    # If Kivy complains about "No main window", you might need a minimal App setup:
    # from kivy.app import App
    # class TestApp(App):
    #     def build(self):
    #         return None # No root widget needed for these tests
    # TestApp().run() # This line is problematic as it blocks. Better to mock Kivy internals.

    unittest.main(argv=['first-arg-is-ignored'], exit=False)
