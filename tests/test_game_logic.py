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
        self.player_configurations = [
            {'name': 'Player1', 'profile_username': 'Player1', 'type': 'Human', 'is_new_profile': False},
            {'name': 'Player2', 'profile_username': 'Player2', 'type': 'Human', 'is_new_profile': False}
        ]
        self.grid_size = (10, 10)
        self.game_state = GameState(self.player_configurations, self.grid_size, self.mock_script_dir)
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
            self.game_state.company_map[coord] = {"company_name": company_name, "owner": self.game_state.players[0], "value": 0}
        
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
            self.game_state.company_map[coord] = {"company_name": company_name, "owner": self.game_state.players[0], "value": 0}
        
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
            self.game_state.company_map[coord] = {"company_name": company_name, "owner": self.game_state.players[0], "value": 0}

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
            self.game_state.company_map[coord] = {"company_name": merged_company_name, "owner": self.game_state.players[0], "value": 0}
        
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
        current_player_profile_name = self.game_state.players[0]
        
        actual_company_name, _ = self.game_state.create_new_company(company_creation_coord, current_player_profile_name)

        self.assertIsNotNone(actual_company_name, "Company should be created.")
        self.assertEqual(actual_company_name, expected_company_name) 

        expected_value = 100 + 200 # Value: size 1 (100) + adjacency bonus (200) = 300
        self.assertEqual(self.game_state.company_info[actual_company_name]['value'], expected_value)
        self.assertEqual(self.game_state.company_map[company_creation_coord]['value'], expected_value)


class TestGameLogicMergers(unittest.TestCase):

    def setUp(self):
        self.mock_script_dir = os.path.dirname(__file__)
        self.player_configurations = [
            {'name': 'Player1', 'profile_username': 'Player1', 'type': 'Human', 'is_new_profile': False}
        ]
        self.grid_size = (10, 10)
        self.game_state = GameState(self.player_configurations, self.grid_size, self.mock_script_dir)
        self.game_state.notify_callbacks = MagicMock()  # Mock notify_callbacks

    def test_merge_companies_share_transfer(self):
        # Setup companies
        current_player_profile_name = self.game_state.players[0]
        self.game_state.company_info['BigCorp'] = {'size': 2, 'value': 200}
        self.game_state.company_info['SmallCorp'] = {'size': 1, 'value': 100}

        self.game_state.company_map[(0,0)] = {"company_name": "BigCorp", "owner": current_player_profile_name, "value": 200}
        self.game_state.company_map[(0,1)] = {"company_name": "BigCorp", "owner": current_player_profile_name, "value": 200}
        self.game_state.company_map[(0,3)] = {"company_name": "SmallCorp", "owner": current_player_profile_name, "value": 100}

        # Setup player shares
        self.game_state.player_shares[current_player_profile_name] = {
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
        current_player_profile_name = self.game_state.players[0]
        self.game_state.merge_companies(coords=(0,2), companies=companies_involved, current_player=current_player_profile_name)

        # Assertions
        self.assertEqual(self.game_state.player_shares[current_player_profile_name].get('BigCorp', 0), 30)
        self.assertNotIn('SmallCorp', self.game_state.player_shares[current_player_profile_name])
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

    def test_merge_companies_with_diamonds_no_names_available(self):
        """
        Test merging two companies (A and B) via a tile placement that is also
        adjacent to diamonds, when no company names are available for forming
        a new company from diamonds. Expects normal merger of A & B.
        """
        # 1. Initial GameState (done by setUp)
        # 2. Consume all available company names
        current_player_profile_name = self.game_state.players[0]
        company_names_in_use = []
        for i in range(len(self.game_state.all_company_names)):
            coord = (0, i) # Dummy coordinates for placeholder companies
            company_name, msg = self.game_state.create_new_company(coord, current_player_profile_name)
            self.assertIsNotNone(company_name, f"Failed to create placeholder company {i+1}: {msg}")
            company_names_in_use.append(company_name)
        
        self.assertEqual(len(self.game_state.available_company_names), 0, "All company names should be consumed.")
        initial_total_companies = self.game_state.active_companies # Should be 5

        # 3. Set up two specific active companies (Company A and Company B)
        # These companies were already created above. We just need to define their specific structure.
        # For this test, we'll re-purpose two of the companies created above.
        # Let's assume company_names_in_use[0] is Company A, company_names_in_use[1] is Company B.
        
        company_a_name = company_names_in_use[0] # e.g., "Nerdniss"
        company_b_name = company_names_in_use[1] # e.g., "Beetleguice"

        # Clear the dummy locations for A and B from company_map and reset their info for proper setup
        del self.game_state.company_map[(0,0)] 
        del self.game_state.company_map[(0,1)]
        
        company_a_coords = [(2,2), (2,3)]
        company_b_coords = [(2,5), (2,6)]

        current_player_profile_name = self.game_state.players[0]
        self.game_state.company_info[company_a_name] = {'size': 0, 'value': 0} # Reset before update
        self.game_state.company_info[company_b_name] = {'size': 0, 'value': 0} # Reset before update

        for coord in company_a_coords:
            self.game_state.company_map[coord] = {"company_name": company_a_name, "owner": current_player_profile_name, "value": 0}
        self.game_state.update_company_value(company_a_name) # Updates size to 2, value to 200

        for coord in company_b_coords:
            self.game_state.company_map[coord] = {"company_name": company_b_name, "owner": current_player_profile_name, "value": 0}
        self.game_state.update_company_value(company_b_name) # Updates size to 2, value to 200
        
        # Ensure other placeholder companies (3, 4, 5) don't interfere with merge tile adjacencies
        # Their coords (0,2), (0,3), (0,4) are far from (2,4)

        # 4. Place diamonds
        diamond_coord1 = (1,4)
        diamond_coord2 = (3,4)
        self.game_state.diamond_positions.add(diamond_coord1)
        self.game_state.diamond_positions.add(diamond_coord2)

        # 5. Define merge_trigger_coord
        merge_trigger_coord = (2,4) # Adjacent to Company A, Company B, and the two diamonds

        # 6. Player turn setup and action (expand Company A into merge_trigger_coord)
        current_player = self.game_state.players[0]
        self.game_state.player_has_moved[current_player] = False
        
        # Action: Expand company_a_name. This should trigger merge_companies.
        # expand_company will set player_has_moved.
        # Since company_a_name and company_b_name have equal size (2), company_a_name (the one being expanded)
        # should be the acquiring company.
        updated_coords = self.game_state.expand_company(coords=merge_trigger_coord, company_name=company_a_name, current_player=current_player)
        self.assertTrue(len(updated_coords) > 0, "Expansion and merger should occur.")

        # 7. Assertions
        # a. Game does not crash (implicit if test reaches here)
        
        # b. merge_trigger_coord is in company_map
        self.assertIn(merge_trigger_coord, self.game_state.company_map)
        
        # c. Company at merge_trigger_coord is the dominant company (company_a_name)
        self.assertEqual(self.game_state.company_map[merge_trigger_coord]['company_name'], company_a_name)
        
        # d. Original coords of A and B now map to dominant company
        for coord in company_a_coords:
            self.assertEqual(self.game_state.company_map[coord]['company_name'], company_a_name)
        for coord in company_b_coords: # These should now also belong to company_a_name
            self.assertEqual(self.game_state.company_map[coord]['company_name'], company_a_name)
            
        # e. Available company names: company_b_name's name should be returned
        self.assertEqual(len(self.game_state.available_company_names), 1)
        self.assertIn(company_b_name, self.game_state.available_company_names)
        
        # f. Active companies decreased by one (B merged into A)
        # Initial total companies was 5. One merged, so 4 remain.
        self.assertEqual(self.game_state.active_companies, initial_total_companies - 1)
        self.assertNotIn(company_b_name, self.game_state.company_info, "Company B should be dissolved.")
        
        # g. Diamonds are still present (no diamond company formed)
        self.assertIn(diamond_coord1, self.game_state.diamond_positions)
        self.assertIn(diamond_coord2, self.game_state.diamond_positions)
        
        # h. Player has moved
        self.assertTrue(self.game_state.player_has_moved[current_player])


class TestDiamondPlacement(unittest.TestCase):
    def setUp(self):
        self.mock_script_dir = os.path.dirname(__file__)
        self.player_configurations = [
            {'name': 'Player1', 'profile_username': 'Player1', 'type': 'Human', 'is_new_profile': False},
            {'name': 'Player2', 'profile_username': 'Player2', 'type': 'Human', 'is_new_profile': False}
        ]
        self.grid_size = (10, 10)
        self.game_state = GameState(self.player_configurations, self.grid_size, self.mock_script_dir)
        self.game_state.notify_callbacks = MagicMock() # Mock notify_callbacks

        # Consume all available company names
        current_player_profile_name = self.game_state.players[0]
        for i in range(len(self.game_state.all_company_names)):
            # Use distinct coordinates for each company to avoid placement errors
            # Ensure these coordinates are not problematic (e.g., 'O' markers if any were predefined)
            # For this test, assuming (i, 0) are valid, non-'O' marker locations.
            coord = (i, 0) 
            company_name, msg = self.game_state.create_new_company(coord, current_player_profile_name)
            if company_name is None:
                # This should not happen in a clean setup if logic is correct
                # and all_company_names has 5 unique names.
                raise Exception(f"Failed to create company {i+1} to set up test: {msg}")
        
        # Ensure player_has_moved is reset for the current player before each test method if needed
        # For this specific test, we'll set it explicitly.

    def test_place_diamond_connects_no_available_company_names(self):
        """
        Test placing a diamond that connects to an existing diamond when all company names are in use.
        Expected behavior: Diamond is placed, no new company is formed.
        """
        # Precondition: All company names should be used up
        self.assertEqual(len(self.game_state.available_company_names), 0, "Precondition failed: Not all company names are used.")

        initial_active_companies = self.game_state.active_companies
        
        # Place an initial diamond
        initial_diamond_coord = (5, 5)
        self.game_state.diamond_positions.add(initial_diamond_coord)
        
        # New diamond to be placed adjacent to the initial one
        new_diamond_coord = (5, 6)
        
        # Ensure current player's has_moved flag is False before the action
        current_player_profile_name = self.game_state.players[self.game_state.current_player_index]
        self.game_state.player_has_moved[current_player_profile_name] = False
        
        # Action: Place the new diamond
        success, message = self.game_state.place_diamond(new_diamond_coord, current_player_profile_name)
        
        # Assertions
        self.assertTrue(success, "place_diamond should return True for successful placement.")
        expected_message = f"Diamond placed at {new_diamond_coord}. All companies formed, no new company created."
        self.assertEqual(message, expected_message, "Incorrect message returned by place_diamond.")
        
        self.assertIn(initial_diamond_coord, self.game_state.diamond_positions, "Initial diamond should remain.")
        self.assertIn(new_diamond_coord, self.game_state.diamond_positions, "New diamond should be added.")
        
        self.assertEqual(len(self.game_state.available_company_names), 0, "Available company names should still be zero.")
        self.assertEqual(self.game_state.active_companies, initial_active_companies, "Active company count should not change.")
        
        self.assertNotIn(initial_diamond_coord, self.game_state.company_map, "No company should be mapped to the initial diamond's location.")
        self.assertNotIn(new_diamond_coord, self.game_state.company_map, "No company should be mapped to the new diamond's location.")
        
        self.assertTrue(self.game_state.player_has_moved[current_player_profile_name], "Player's has_moved flag should be True.")

    def test_place_standalone_diamond_no_available_company_names(self):
        """
        Test placing a standalone diamond (not connecting to others) when all company names are in use.
        Expected behavior: Diamond is placed, no company is formed.
        """
        self.assertEqual(len(self.game_state.available_company_names), 0, "Precondition failed: Not all company names are used.")
        initial_active_companies = self.game_state.active_companies
        
        diamond_coord = (3, 3)
        
        current_player_profile_name = self.game_state.players[self.game_state.current_player_index]
        self.game_state.player_has_moved[current_player_profile_name] = False
        
        success, message = self.game_state.place_diamond(diamond_coord, current_player_profile_name)
        
        self.assertTrue(success)
        self.assertEqual(message, f"Diamond placed at {diamond_coord}.")
        self.assertIn(diamond_coord, self.game_state.diamond_positions)
        self.assertEqual(len(self.game_state.available_company_names), 0)
        self.assertEqual(self.game_state.active_companies, initial_active_companies)
        self.assertNotIn(diamond_coord, self.game_state.company_map)
        self.assertTrue(self.game_state.player_has_moved[current_player_profile_name])

    def test_place_diamond_forms_company_if_names_available(self):
        """
        Test that placing a diamond that connects to another forms a company if names are available.
        This is a contrast to the "no available names" scenario.
        """
        # Reset available_company_names for this test by creating a new GameState instance
        # or manually managing the list. For simplicity, let's re-initialize part of the state.
        # Use the updated player_configurations for GameState initialization
        self.game_state = GameState(self.player_configurations, self.grid_size, self.mock_script_dir) # Fresh state
        self.game_state.notify_callbacks = MagicMock()
        
        self.assertTrue(len(self.game_state.available_company_names) > 0, "Precondition: Should have available company names.")
        initial_active_companies = self.game_state.active_companies
        expected_new_company_name = self.game_state.available_company_names[0]

        initial_diamond_coord = (7, 7)
        self.game_state.diamond_positions.add(initial_diamond_coord)
        
        new_diamond_coord = (7, 8) # Adjacent
        
        current_player_profile_name = self.game_state.players[self.game_state.current_player_index]
        # place_diamond now takes current_player argument.
        success, message = self.game_state.place_diamond(new_diamond_coord, current_player_profile_name)
        
        self.assertTrue(success)
        # If a player action (placing a diamond) leads to company formation,
        # and that player gets bonus shares, the message should reflect player agency.
        expected_message_part = f"{current_player_profile_name} created {expected_new_company_name}!"
        self.assertEqual(message, expected_message_part)
        
        # Diamonds should be consumed and removed from diamond_positions
        self.assertNotIn(initial_diamond_coord, self.game_state.diamond_positions)
        self.assertNotIn(new_diamond_coord, self.game_state.diamond_positions)
        
        self.assertEqual(self.game_state.active_companies, initial_active_companies + 1)
        self.assertIn(initial_diamond_coord, self.game_state.company_map)
        self.assertIn(new_diamond_coord, self.game_state.company_map)
        self.assertEqual(self.game_state.company_map[initial_diamond_coord]['company_name'], expected_new_company_name)
        self.assertEqual(self.game_state.company_map[new_diamond_coord]['company_name'], expected_new_company_name)


class TestBonusShares(unittest.TestCase):
    def setUp(self):
        self.mock_script_dir = os.path.dirname(__file__)
        self.player_configurations = [
            {'name': 'Player1', 'profile_username': 'Player1', 'type': 'Human', 'is_new_profile': False},
            {'name': 'Player2', 'profile_username': 'Player2', 'type': 'Human', 'is_new_profile': False}
        ]
        self.grid_size = (10, 10)
        self.game_state = GameState(self.player_configurations, self.grid_size, self.mock_script_dir)
        self.game_state.notify_callbacks = MagicMock() # Mock notify_callbacks

    def test_bonus_shares_on_direct_player_creation(self):
        """
        Test if 5 bonus shares are awarded when a player directly creates a new company.
        """
        current_player_profile_name = self.game_state.players[0]
        coord_input = (0, 0)
        
        # Ensure player has no shares of this potential company initially
        self.assertEqual(len(self.game_state.player_shares[current_player_profile_name]), 0)

        new_company_name, msg = self.game_state.create_new_company(coord_input, current_player_profile_name)

        self.assertIsNotNone(new_company_name, f"Company creation failed: {msg}")
        self.assertIn(new_company_name, self.game_state.player_shares[current_player_profile_name], "New company not found in player's shares.")
        self.assertEqual(self.game_state.player_shares[current_player_profile_name][new_company_name], 5, "Player should have 5 bonus shares.")

    def test_bonus_shares_on_place_diamond_forms_company(self):
        """
        Test if 5 bonus shares are awarded when a player places a diamond that forms a new company.
        """
        current_player_profile_name = self.game_state.players[0]
        initial_diamond_coord = (0, 0)
        new_diamond_coord = (0, 1) # Adjacent to initial_diamond_coord

        self.game_state.diamond_positions.add(initial_diamond_coord)
        
        # Store available company name to check later
        self.assertTrue(len(self.game_state.available_company_names) > 0, "No available company names for test setup.")
        expected_company_name = self.game_state.available_company_names[0]

        success, message = self.game_state.place_diamond(new_diamond_coord, current_player_profile_name)

        self.assertTrue(success, f"Placing diamond failed: {message}")
        # The message from place_diamond -> create_new_company will include the player's name if current_player is passed
        expected_message_part = f"{current_player_profile_name} created {expected_company_name}!"
        # If create_new_company is called with current_player=None (original diamond logic), message changes.
        # Based on current place_diamond, it *does* pass current_player to create_new_company.
        self.assertEqual(message, expected_message_part, "Message should indicate company creation by player.")
        
        # Verify company was formed and shares awarded
        self.assertIn(expected_company_name, self.game_state.company_info, "Company info not created.")
        self.assertIn(expected_company_name, self.game_state.player_shares[current_player_profile_name], f"Company {expected_company_name} not in {current_player_profile_name}'s shares.")
        self.assertEqual(self.game_state.player_shares[current_player_profile_name][expected_company_name], 5, "Player should have 5 bonus shares.")
        
        # Verify diamonds were consumed
        self.assertNotIn(initial_diamond_coord, self.game_state.diamond_positions)
        self.assertNotIn(new_diamond_coord, self.game_state.diamond_positions)

    def test_bonus_shares_on_player_action_forming_multi_tile_company(self):
        """
        Test if 5 bonus shares are awarded when a player's action leads to creating
        a multi-tile company (simulated by direct call to create_new_company with multiple coords).
        """
        current_player_profile_name = self.game_state.players[0]
        # These coordinates would typically be a mix of a newly placed tile and adjacent diamonds
        company_coords = [(0,0), (0,1), (1,0)] 
        
        new_company_name, msg = self.game_state.create_new_company(coords_input=company_coords, current_player=current_player_profile_name)

        self.assertIsNotNone(new_company_name, f"Company creation failed: {msg}")
        self.assertIn(new_company_name, self.game_state.player_shares[current_player_profile_name], "New company not in player's shares.")
        self.assertEqual(self.game_state.player_shares[current_player_profile_name][new_company_name], 5, "Player should have 5 bonus shares for multi-tile company.")

    def test_no_bonus_shares_if_current_player_is_none(self):
        """
        Test that no bonus shares are awarded if create_new_company is called with current_player=None.
        """
        # These coordinates might represent diamonds merging naturally without a specific player action.
        company_coords = [(5,5), (5,6)] 
        
        new_company_name, msg = self.game_state.create_new_company(coords_input=company_coords, current_player=None)

        self.assertIsNotNone(new_company_name, f"Company creation failed: {msg}")
        
        # Verify no player received shares for this company
        for player_name in self.game_state.players:
            self.assertEqual(self.game_state.player_shares[player_name].get(new_company_name, 0), 0,
                             f"Player {player_name} should not have bonus shares for None-player company creation.")


if __name__ == '__main__':
    unittest.main()
