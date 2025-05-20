import unittest
from unittest.mock import MagicMock, patch
import os # Add this if script_dir usage in GameState needs it for tests

# Assuming game_logic.py is in the parent directory relative to the 'tests' directory
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from game_logic import GameState

class TestGameLogicOMarkerBonus(unittest.TestCase):

    def setUp(self):
        # A minimal GameState setup for testing these specific features.
        # script_dir might be needed if GameState's __init__ relies on it for asset paths,
        # even if assets themselves aren't loaded in these specific tests.
        # Providing a dummy path for script_dir.
        self.mock_script_dir = os.path.dirname(__file__) 
        self.players = ["Player1", "Player2"]
        self.grid_size = (10, 10)
        self.game_state = GameState(self.players, self.grid_size, self.mock_script_dir)
        # Mock the callbacks as they are not relevant for these tests
        self.game_state.register_callback(MagicMock())


    def test_update_company_value_no_o_markers(self):
        # Test value calculation without any O markers
        company_name = "TestCorp"
        self.game_state.company_info[company_name] = {'size': 0, 'value': 0} # Initial setup
        coords = [(0,0), (0,1)] # Company of size 2
        for coord in coords:
            self.game_state.company_map[coord] = {"company_name": company_name, "owner": "Player1", "value": 0}
        
        self.game_state.update_company_value(company_name)
        self.assertEqual(self.game_state.company_info[company_name]['value'], 2 * 100) # 200

    def test_update_company_value_with_one_o_marker(self):
        # Test value with one O marker
        company_name = "TestCorp"
        self.game_state.company_info[company_name] = {'size': 0, 'value': 0}
        coords = [(1,0), (1,1)] # Size 2
        o_marker_loc = (1,0)
        self.game_state.initial_o_marker_locations = {o_marker_loc}
        for coord in coords:
            self.game_state.company_map[coord] = {"company_name": company_name, "owner": "Player1", "value": 0}

        self.game_state.update_company_value(company_name)
        expected_value = (2 * 100) + 200 # 200 base + 200 bonus
        self.assertEqual(self.game_state.company_info[company_name]['value'], expected_value)
        self.assertEqual(self.game_state.company_map[(1,1)]['value'], expected_value)

    def test_update_company_value_with_multiple_o_markers(self):
        # Test value with multiple O markers
        company_name = "TestCorp"
        self.game_state.company_info[company_name] = {'size': 0, 'value': 0}
        coords = [(2,0), (2,1), (2,2)] # Size 3
        o_marker_locs = {(2,0), (2,2)}
        self.game_state.initial_o_marker_locations = o_marker_locs
        for coord in coords:
            self.game_state.company_map[coord] = {"company_name": company_name, "owner": "Player1", "value": 0}

        self.game_state.update_company_value(company_name)
        expected_value = (3 * 100) + (2 * 200) # 300 base + 400 bonus
        self.assertEqual(self.game_state.company_info[company_name]['value'], expected_value)

    def test_create_new_company_on_o_marker(self):
        # Test company creation covering an O marker
        o_marker_loc = (3,3)
        self.game_state.initial_o_marker_locations = {o_marker_loc}
        self.game_state.available_company_names = ["NewCorp"] # Ensure a name is available
        
        # Mock notify_callbacks to prevent issues if it expects UI components
        self.game_state.notify_callbacks = MagicMock()

        company_name, _ = self.game_state.create_new_company((3,3), "Player1")
        
        self.assertIsNotNone(company_name)
        expected_value = (1 * 100) + 200 # 100 base + 200 bonus
        self.assertEqual(self.game_state.company_info[company_name]['value'], expected_value)
        self.assertEqual(self.game_state.company_map[(3,3)]['value'], expected_value)

    def test_expand_company_onto_o_marker(self):
        # Setup initial company
        self.game_state.available_company_names = ["ExpandCorp"]
        self.game_state.notify_callbacks = MagicMock() # Mock callbacks
        
        # Create a company NOT on an O marker first
        # The create_new_company calls update_company_value internally.
        # If initial_o_marker_locations is empty at this point, value will be base.
        self.game_state.initial_o_marker_locations = set() # Ensure no O-markers for initial creation
        company_name, _ = self.game_state.create_new_company((4,0), "Player1") 
        self.assertEqual(self.game_state.company_info[company_name]['value'], 100, "Initial company value without O-marker bonus should be 100.")

        # Now set an O marker and expand onto it
        o_marker_loc = (4,1)
        self.game_state.initial_o_marker_locations = {o_marker_loc} # Set O-marker for expansion
        
        self.game_state.expand_company((4,1), company_name, "Player1")
        
        # Company size is now 2. One O marker covered.
        expected_value = (2 * 100) + 200 # 200 base + 200 bonus
        self.assertEqual(self.game_state.company_info[company_name]['value'], expected_value)
        self.assertEqual(self.game_state.company_map[(4,1)]['value'], expected_value)
        self.assertEqual(self.game_state.company_map[(4,0)]['value'], expected_value) # Original cell value also updates

    def test_merge_companies_with_o_markers_simplified(self):
        # Simplified approach: Manually set up a merged company state and call update_company_value
        # This tests the value calculation post-merge rather than the merge logic itself.
        merged_company_name = "MergedCorp"
        self.game_state.company_info[merged_company_name] = {'size': 0, 'value': 0} # Initial setup for the new test
        # Ensure company_map is clean for this specific company or use unique coords
        merged_coords = [(7,0), (7,1), (7,2), (7,3)] # Size 4
        o_markers_for_merged = {(7,0), (7,3)} # Two O markers
        self.game_state.initial_o_marker_locations = o_markers_for_merged # Set O-markers for this test
        
        # Clear previous company_map entries or use distinct coords to avoid interference
        # For simplicity, let's assume these coords are fresh for MergedCorp
        for coord in merged_coords:
            self.game_state.company_map[coord] = {"company_name": merged_company_name, "owner": "Player1", "value": 0}
        
        # Simulate that a merge happened (size is implicitly set by update_company_value based on company_map entries)
        # and now we update the value
        self.game_state.update_company_value(merged_company_name)
        expected_value = (4 * 100) + (2 * 200) # 400 base + 400 bonus
        self.assertEqual(self.game_state.company_info[merged_company_name]['value'], expected_value)
        # Verify a couple of map entries as well
        self.assertEqual(self.game_state.company_map[(7,0)]['value'], expected_value)
        self.assertEqual(self.game_state.company_map[(7,1)]['value'], expected_value)


if __name__ == '__main__':
    unittest.main()
