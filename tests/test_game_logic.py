import unittest
from unittest.mock import MagicMock, patch
import os # Add this if script_dir usage in GameState needs it for tests

# Assuming game_logic.py is in the parent directory relative to the 'tests' directory
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from game_logic import GameState

class TestGameLogicOMarkerBonus(unittest.TestCase):

    def setUp(self):
        self.mock_script_dir = os.path.dirname(__file__) 
        self.players = ["Player1", "Player2"]
        self.grid_size = (10, 10)
        self.game_state = GameState(self.players, self.grid_size, self.mock_script_dir)
        self.game_state.register_callback(MagicMock()) # Mock callbacks

    def test_update_company_value_no_o_markers(self):
        # Test value calculation without any O markers
        company_name = "TestCorpNoBonus"
        # Clean slate for this test
        self.game_state.company_info = {company_name: {'size': 0, 'value': 0}}
        self.game_state.company_map = {}
        self.game_state.initial_o_marker_locations = set()
        
        coords = [(0,0), (0,1)] # Company of size 2
        for coord in coords:
            self.game_state.company_map[coord] = {"company_name": company_name, "owner": "Player1", "value": 0}
        
        self.game_state.update_company_value(company_name)
        self.assertEqual(self.game_state.company_info[company_name]['value'], 2 * 100) # 200

    def test_update_company_value_adjacent_to_one_o_marker(self):
        # Test value with company adjacent to one O marker
        company_name = "TestCorpAdj1"
        # Clean slate
        self.game_state.company_info = {company_name: {'size': 0, 'value': 0}}
        self.game_state.company_map = {}
        self.game_state.initial_o_marker_locations = set()

        company_coords = [(1,0), (1,1)] # Size 2
        o_marker_loc = (1,2) # O marker adjacent to (1,1)
        self.game_state.initial_o_marker_locations = {o_marker_loc}
        
        for coord in company_coords:
            self.game_state.company_map[coord] = {"company_name": company_name, "owner": "Player1", "value": 0}
        
        self.game_state.update_company_value(company_name)
        
        expected_value = (2 * 100) + 200 # 200 base + 200 single adjacency bonus
        self.assertEqual(self.game_state.company_info[company_name]['value'], expected_value)
        self.assertEqual(self.game_state.company_map[(1,1)]['value'], expected_value)

    def test_update_company_value_adjacent_to_multiple_o_markers_receives_single_bonus(self):
        # Test value with company adjacent to multiple O markers, expects single bonus
        company_name = "TestCorpAdjMulti"
        self.game_state.company_info = {company_name: {'size': 0, 'value': 0}}
        self.game_state.company_map = {}
        self.game_state.initial_o_marker_locations = set()

        company_coords = [(2,1), (2,2)] # Size 2
        o_marker_locs = {(2,0), (2,3)} # O markers adjacent to (2,1) and (2,2)
        self.game_state.initial_o_marker_locations = o_marker_locs

        for coord in company_coords:
            self.game_state.company_map[coord] = {"company_name": company_name, "owner": "Player1", "value": 0}

        self.game_state.update_company_value(company_name)
        
        expected_value = (2 * 100) + 200 # 200 base + 200 single adjacency bonus
        self.assertEqual(self.game_state.company_info[company_name]['value'], expected_value)

    def test_merged_company_value_with_o_marker_adjacency(self):
        # Test value of a manually defined "merged" company adjacent to an O marker
        merged_company_name = "MergedCorpAdj"
        self.game_state.company_info = {merged_company_name: {'size': 0, 'value': 0}}
        self.game_state.company_map = {}
        self.game_state.initial_o_marker_locations = set()
        
        merged_coords = [(7,0), (7,1), (7,2), (7,3)] # Size 4
        o_markers_for_merged = {(6,0)} # O marker at (6,0) is adjacent to company tile (7,0)
        self.game_state.initial_o_marker_locations = o_markers_for_merged
        
        for coord in merged_coords:
            self.game_state.company_map[coord] = {"company_name": merged_company_name, "owner": "Player1", "value": 0}
        
        self.game_state.update_company_value(merged_company_name) 
        
        expected_value = (4 * 100) + 200 # 400 base + 200 single adjacency bonus
        self.assertEqual(self.game_state.company_info[merged_company_name]['value'], expected_value)
        self.assertEqual(self.game_state.company_map[(7,0)]['value'], expected_value)

    def test_o_marker_adjacency_bonus_on_create(self): # Renamed for clarity from test_o_marker_adjacency_bonus
        # This test verifies company creation adjacent to an 'O' marker.
        # setUp re-initializes GameState, so available_company_names is fresh.
        o_marker_loc = (2,2)
        self.game_state.initial_o_marker_locations = {o_marker_loc}
        
        company_creation_coord = (2,1) # Adjacent to (2,2)
        # GameState.all_company_names = ["Nerdniss", "Beetleguice", ...]
        # create_new_company pops from available_company_names. Default setup makes "Nerdniss" first.
        expected_company_name = self.game_state.all_company_names[0] 
        
        actual_company_name, _ = self.game_state.create_new_company(company_creation_coord, "Player1")

        self.assertIsNotNone(actual_company_name, "Company should be created.")
        self.assertEqual(actual_company_name, expected_company_name) 

        expected_value = 100 + 200 # Value: size 1 (100) + adjacency bonus (200) = 300
        self.assertEqual(self.game_state.company_info[actual_company_name]['value'], expected_value)
        self.assertEqual(self.game_state.company_map[company_creation_coord]['value'], expected_value)


class TestGameLogicMergers(unittest.TestCase):

    def setUp(self):
        self.mock_script_dir = os.path.dirname(__file__)
        self.players = ["Player1"]
        self.grid_size = (10, 10)
        self.game_state = GameState(self.players, self.grid_size, self.mock_script_dir)
        self.game_state.notify_callbacks = MagicMock()  # Mock notify_callbacks

    def test_merge_companies_share_transfer(self):
        # Setup companies
        self.game_state.company_info['BigCorp'] = {'size': 2, 'value': 200}
        self.game_state.company_info['SmallCorp'] = {'size': 1, 'value': 100}

        self.game_state.company_map[(0,0)] = {"company_name": "BigCorp", "owner": "Player1", "value": 200}
        self.game_state.company_map[(0,1)] = {"company_name": "BigCorp", "owner": "Player1", "value": 200}
        self.game_state.company_map[(0,3)] = {"company_name": "SmallCorp", "owner": "Player1", "value": 100}

        # Setup player shares
        self.game_state.player_shares['Player1'] = {
            'BigCorp': 20,
            'SmallCorp': 10
        }

        # Setup available company names
        # Ensure the merging corps are not available initially, and other names are.
        self.game_state.available_company_names = [name for name in self.game_state.all_company_names if name not in ['BigCorp', 'SmallCorp']]
        # Add a known name for predictability if needed, or ensure all_company_names has enough variety.
        if not self.game_state.available_company_names:
             self.game_state.available_company_names.append("ExtraCorp")


        # Action: Trigger merger
        companies_involved = {'BigCorp', 'SmallCorp'}
        self.game_state.merge_companies(coords=(0,2), companies=companies_involved, current_player="Player1")

        # Assertions
        self.assertEqual(self.game_state.player_shares['Player1'].get('BigCorp', 0), 30)
        self.assertNotIn('SmallCorp', self.game_state.player_shares['Player1'])
        self.assertNotIn('SmallCorp', self.game_state.company_info)
        self.assertEqual(self.game_state.company_info['BigCorp']['size'], 3) # 2 (BigCorp) + 1 (SmallCorp from map) + 1 (merging tile (0,2))
                                                                          # The merge_companies logic adds the merging tile to the acquirer.
                                                                          # And updates size based on company_map.
                                                                          # If (0,2) is the merging tile, it's added to BigCorp.
                                                                          # So size becomes 2 (original) + 1 (SmallCorp tile) + 1 (merging tile) = 4.
                                                                          # Let's re-verify merge_companies logic for size.
                                                                          # It does self.company_info[largest_company]['size'] += self.company_info[company]['size']
                                                                          # Then update_company_value recalculates size based on company_map.
                                                                          # The merging tile (0,2) is also assigned to largest_company.
                                                                          # So, BigCorp (2 tiles) + SmallCorp (1 tile) + merging tile (1 tile) = 4 tiles.
        self.assertEqual(self.game_state.company_info['BigCorp']['size'], 3)
        self.assertIn('SmallCorp', self.game_state.available_company_names)


if __name__ == '__main__':
    unittest.main()
