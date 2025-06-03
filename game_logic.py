# game_logic.py

import os
import random # Added random import
from collections import deque

class GameState:
    def __init__(self, player_configurations, grid_size, script_dir): # Changed players to player_configurations
        self.players = [p['name'] for p in player_configurations] # Extract player names
        self.player_types = {p['name']: p['type'] for p in player_configurations} # Store player types
        self.grid_size = grid_size  # (rows, cols)
        self.current_player_index = 0
        self.company_count = 0
        self.active_companies = 0
        self.turn_counter = 0

        # Managing available company names
        self.all_company_names = [
            "Nerdniss", "Beetleguice", "StronCannon", "DebbiesKnees", "Pacifica"
        ]
        self.available_company_names = self.all_company_names.copy()

        # Company logos with absolute paths
        self.script_dir = script_dir
        self.company_logos = {
            "Nerdniss": os.path.join(script_dir, 'assets', 'images', 'nerdniss_logo.png'),
            "Beetleguice": os.path.join(script_dir, 'assets', 'images', 'beetleguice_logo.png'),
            "StronCannon": os.path.join(script_dir, 'assets', 'images', 'stroncannon_logo.png'),
            "DebbiesKnees": os.path.join(script_dir, 'assets', 'images', 'debbiesKnees_logo.png'),
            "Pacifica": os.path.join(script_dir, 'assets', 'images', 'pacifica_logo.png'),
        }
        self.diamond_image_path = os.path.join(script_dir, 'assets', 'images', 'diamond.png')

        # Game data
        self.company_map = {}  # Maps coordinates to company info
        self.company_info = {}  # Maps company names to their details
        self.player_wealth = {player: 6000 for player in self.players}
        self.player_shares = {player: {} for player in self.players}
        self.diamond_positions = set()  # Set of coordinates with diamonds

        # Track if players have made a move during their turn
        self.player_has_moved = {player: False for player in self.players}  # New flag

        # Callbacks for UI updates
        self.callbacks = []
        self.initial_o_marker_locations = set()

    def set_initial_o_marker_locations(self, locations_set):
        self.initial_o_marker_locations = locations_set
        print(f"Initial O marker locations set: {self.initial_o_marker_locations}") # Optional: for debugging

    def register_callback(self, callback):
        """
        Registers a callback function to be called when the company_map is updated.
        The callback should accept a list of tuples: (coords, company_name)
        """
        self.callbacks.append(callback)
        print("Registered a new callback for game state updates.")

    def notify_callbacks(self, updated_entries):
        """
        Notifies all registered callbacks with the list of updated entries.
        Each entry is a tuple: (coords, company_name)
        """
        for callback in self.callbacks:
            callback(updated_entries)
        print(f"Notified {len(self.callbacks)} callbacks with {len(updated_entries)} updates.")

    def create_new_company(self, coords_input, current_player):
        """
        Creates a new company at the specified coordinates.
        Handles ownership appropriately, especially when created from diamonds.

        Parameters:
            coords_input (tuple or list of tuples): The coordinates to assign to the new company.
            current_player (str or None): The player creating the company or None if created from diamonds.

        Returns:
            tuple: (company_name, message)
        """
        # Determine if coords_input is a single tuple or a list of tuples
        if isinstance(coords_input, tuple):
            coords_list = [coords_input]
        elif isinstance(coords_input, list):
            coords_list = coords_input
        else:
            raise TypeError("coords_input must be a tuple or a list of tuples representing coordinates.")

        # Validate each coordinate in the list and check for 'O' markers
        for coord in coords_list:
            if not (isinstance(coord, tuple) and len(coord) == 2):
                raise TypeError(f"Each coordinate must be a tuple of (row, col). Invalid coord: {coord}")
            if coord in self.initial_o_marker_locations:
                print(f"Error: Cannot create company at {coord}. Position is an 'O' marker tile.")
                return None, "Cannot create company on an 'O' marker tile."

        if not self.available_company_names:
            print("No more available company names to create a new company.")
            return None, "No more available company names!"

        company_name = self.available_company_names.pop(0)
        self.active_companies += 1
        self.company_count += 1  # Increment total company count

        # Initialize company info
        initial_value = 100  # Companies start at £100 per share
        self.company_info[company_name] = {
            'size': len(coords_list),
            'value': initial_value,
        }

        updated_entries = []

        for coord in coords_list:
            self.company_map[coord] = {
                "company_name": company_name,
                "owner": current_player if current_player else "Diamond",
                "value": initial_value
            }
            updated_entries.append((coord, company_name))
            print(f"Assigned '{company_name}' to {coord} owned by '{current_player if current_player else 'Diamond'}'.")

        # Update the new company's value to include any "O" marker bonuses
        self.update_company_value(company_name)

        print(f"Created new company '{company_name}' at {coords_list} owned by '{current_player if current_player else 'Diamond'}'.")

        # Notify callbacks about the new company
        self.notify_callbacks(updated_entries)

        if current_player:
            # Award 5 bonus shares to the player who created the company
            self.player_shares[current_player][company_name] = self.player_shares[current_player].get(company_name, 0) + 5
            print(f"Awarded 5 bonus shares of '{company_name}' to player '{current_player}'.")
            
            self.player_has_moved[current_player] = True  # Player has made a move
            return company_name, f"{current_player} created {company_name}!"
        else:
            return company_name, f"A new company '{company_name}' was created from diamonds!"

    def expand_company(self, coords, company_name, current_player):
        """
        Expands an existing company into the specified coordinates.

        Parameters:
            coords (tuple): The coordinate to expand into.
            company_name (str): The name of the company to expand.
            current_player (str): The player performing the expansion.

        Returns:
            list: List of coordinates that have been updated.
        """
        if coords in self.initial_o_marker_locations:
            print(f"Error: Cannot expand company into {coords}. Position is an 'O' marker tile.")
            return []

        if company_name not in self.company_info:
            print(f"Error: Company '{company_name}' does not exist.")
            return []

        # Assign the company to the new coordinates
        self.company_map[coords] = {
            "company_name": company_name,
            "owner": current_player,
            "value": 0  # Will be updated below
        }
        print(f"Expanded company '{company_name}' into {coords} by '{current_player}'.")

        # Update company size and value
        self.update_company_value(company_name)

        # Check if the company's value triggers a share split
        self.check_share_split(company_name)

        # Notify callbacks about the expansion
        self.notify_callbacks([(coords, company_name)])

        # After expansion, check if the expanded position is adjacent to other companies and merge if necessary
        adjacent_companies = self.get_adjacent_companies(coords)
        if len(adjacent_companies) > 1:
            merged_entries = self.merge_companies(coords, adjacent_companies, current_player)
            if merged_entries:
                self.player_has_moved[current_player] = True  # Player has made a move
            return merged_entries
        else:
            self.player_has_moved[current_player] = True  # Player has made a move
            return [coords]

    def merge_companies(self, coords, companies, current_player):
        """
        Merges multiple companies into the largest one or creates a new company if multiple diamonds are involved.

        Parameters:
            coords (tuple): The coordinate initiating the merge.
            companies (set): Set of company names adjacent to the coordinate.
            current_player (str): The player performing the merge.

        Returns:
            list: List of all coordinates updated during the merge.
        """
        if not companies or len(companies) < 2:
            print("No need to merge; insufficient companies.")
            return []

        # Determine if multiple diamonds are adjacent
        row, col = coords
        adjacent_cells = [
            (row - 1, col), (row + 1, col),
            (row, col - 1), (row, col + 1)
        ]
        adjacent_diamonds = [cell for cell in adjacent_cells if cell in self.diamond_positions]

        # **Handle Diamond Mergers into New Companies**
        if len(adjacent_diamonds) >= 2:
            print(f"Multiple diamonds adjacent to {coords}. Creating a new company.")
            # Include the current coords in the new company
            diamonds_to_merge = set(adjacent_diamonds)
            # Add the triggering coordinate to the set of tiles that would form the new company
            # If coords is already a diamond, set properties handle it.
            # If coords is not a diamond, it's included for the attempt.
            potential_new_company_tiles = set(adjacent_diamonds)
            potential_new_company_tiles.add(coords)

            print(f"Attempting to create a new company from diamonds and triggering tile: {potential_new_company_tiles}")
            new_company_name, message = self.create_new_company(list(potential_new_company_tiles), current_player)

            if new_company_name:
                # Successfully created a new company from diamonds and the triggering tile
                # Remove all constituent tiles of the new company from diamond_positions
                # (if they were diamonds to begin with)
                for cell in potential_new_company_tiles:
                    self.diamond_positions.discard(cell) # discard is safe if cell wasn't a diamond
                
                print(f"Successfully merged diamonds and tile {coords} into new company '{new_company_name}'.")
                # Notify callbacks is handled by create_new_company
                # The player_has_moved flag is also handled by create_new_company
                return [(tile, new_company_name) for tile in potential_new_company_tiles]
            else:
                # Failed to create a new company from diamonds (e.g., no names available)
                # Do not return. Instead, proceed to normal merger logic for the 'coords' tile.
                # The adjacent_diamonds remain on the board.
                print(f"Failed to create a new company from diamonds and tile {coords} (e.g., '{message}'). Proceeding with normal merger for the tile.")
                # No return here; execution will fall through.

        # **Proceed with Normal Merge into the Largest Existing Company**
        companies = list(companies)
        companies.sort(key=lambda x: self.company_info[x]['size'], reverse=True)
        largest_company = companies[0]
        merged_companies = companies[1:]

        print(f"Merging companies into '{largest_company}'. Companies to merge: {merged_companies}")

        updated_entries = []
        # Initialize share transfer dictionary
        player_shares_to_transfer = {player: 0 for player in self.players}

        for company in merged_companies:
            if company == largest_company:
                continue  # Skip the largest company

            # Update grid and company map
            for coord_key, info in list(self.company_map.items()):
                if info["company_name"] == company:
                    self.company_map[coord_key]["company_name"] = largest_company
                    updated_entries.append((coord_key, largest_company))
                    print(f"Updated company_map at {coord_key} to '{largest_company}'.")

            # Update company info
            self.company_info[largest_company]['size'] += self.company_info[company]['size']
            print(f"Increased size of '{largest_company}' to {self.company_info[largest_company]['size']}.")

            # Collect shares to transfer
            for player, shares in self.player_shares.items():
                if company in shares:
                    num_shares = shares.pop(company)
                    player_shares_to_transfer[player] += num_shares
                    print(f"Player '{player}' has {num_shares} shares in '{company}' to transfer.")

            del self.company_info[company]
            print(f"Deleted company '{company}' from company_info.")

            # Reduce active companies count
            self.active_companies -= 1
            print(f"Decremented active_companies to {self.active_companies}.")

            # Add the dissolved company's name back to the available list if not already present
            if company not in self.available_company_names:
                self.available_company_names.append(company)
                print(f"Added '{company}' back to available_company_names.")

        # Transfer the collected shares to the largest company
        for player, total_shares in player_shares_to_transfer.items():
            if total_shares > 0:
                self.player_shares[player][largest_company] = self.player_shares[player].get(
                    largest_company, 0
                ) + total_shares
                print(f"Player '{player}' now has {self.player_shares[player][largest_company]} shares in '{largest_company}'.")

        # After merging, update the largest company's value
        self.update_company_value(largest_company)

        # **Bug Fix:** Ensure coords exists in company_map before accessing
        if coords not in self.company_map:
            print(f"Error: coords {coords} not in company_map. Assigning to '{largest_company}'.")
            self.company_map[coords] = {
                "company_name": largest_company,
                "owner": current_player,
                "value": self.company_info[largest_company]['value']
            }
            updated_entries.append((coords, largest_company))
        else:
            self.company_map[coords]["value"] = self.company_info[largest_company]['value']
            updated_entries.append((coords, largest_company))
            print(f"Set value at {coords} to {self.company_info[largest_company]['value']}.")

        # Notify callbacks about the merged companies
        self.notify_callbacks(updated_entries)

        # Indicate that the player has made a move
        self.player_has_moved[current_player] = True

        return updated_entries

    def update_company_value(self, company_name):
        """
        Updates the value of the specified company based on its size.

        Parameters:
            company_name (str): The name of the company to update.
        """
        if company_name not in self.company_info:
            print(f"Error: Company '{company_name}' does not exist.")
            return

        size = 0
        company_positions = []
        for c_coords, c_info in self.company_map.items():
            if c_info["company_name"] == company_name:
                size += 1
                company_positions.append(c_coords)
        
        extra_value = 0
        for company_coord in company_positions:
            r, c = company_coord
            potential_adjacent_o_markers = [
                (r - 1, c), (r + 1, c),  # North, South
                (r, c - 1), (r, c + 1)   # West, East
            ]
            for adj_coord in potential_adjacent_o_markers:
                if adj_coord in self.initial_o_marker_locations:
                    extra_value += 200  # Accumulate bonus for each adjacency
        
        base_value = size * 100
        total_value = base_value + extra_value

        self.company_info[company_name]['size'] = size
        self.company_info[company_name]['value'] = total_value
        
        # The log message for `o_marker_bonus` should correctly reflect this accumulated `extra_value`.
        print(f"Updated company '{company_name}': size={size}, base_value={base_value}, o_marker_bonus={extra_value}, total_value={total_value}.")

        # Update the value in company_map entries
        for c_coords in company_positions:
            self.company_map[c_coords]['value'] = total_value
            # The existing print statement for company_map update can remain or be adjusted if needed.
            # For now, let's keep it as is, or we can make it more detailed.
            # print(f"Set value at {c_coords} for company '{company_name}' to {total_value}.")
            # Keeping the old one for consistency with previous logs unless a change is specifically requested for this line.
            print(f"Set value at {c_coords} to {total_value}.")

    def check_share_split(self, company_name):
        """
        Splits shares if the company's value exceeds a threshold.

        Parameters:
            company_name (str): The name of the company to check.
        """
        if company_name not in self.company_info:
            print(f"Error: Company '{company_name}' does not exist.")
            return

        if self.company_info[company_name]["value"] >= 3200:
            print(f"Share split triggered for '{company_name}'.")
            for player in self.players:
                if company_name in self.player_shares[player]:
                    original_shares = self.player_shares[player][company_name]
                    self.player_shares[player][company_name] *= 2
                    print(f"Doubled shares for player '{player}' in '{company_name}' from {original_shares} to {self.player_shares[player][company_name]}.")
            self.company_info[company_name]["value"] //= 2
            print(f"Halved value of '{company_name}' to {self.company_info[company_name]['value']}.")

    def get_adjacent_companies(self, coords):
        """
        Returns a set of adjacent company names to the given coordinates.

        Parameters:
            coords (tuple): The coordinate to check around.

        Returns:
            set: Set of adjacent company names.
        """
        row, col = coords
        adjacent_cells = [
            (row - 1, col), (row + 1, col),
            (row, col - 1), (row, col + 1)
        ]
        companies = set()
        for r, c in adjacent_cells:
            if 0 <= r < self.grid_size[0] and 0 <= c < self.grid_size[1]:
                if (r, c) in self.company_map:
                    company_name = self.company_map[(r, c)]["company_name"]
                    companies.add(company_name)
        print(f"Adjacent companies to {coords}: {companies}")
        return companies

    def buy_shares(self, company_name, player, amount):
        """
        Allows a player to buy shares in a company.

        Parameters:
            company_name (str): The company to buy shares in.
            player (str): The player buying the shares.
            amount (int): The number of shares to buy.

        Returns:
            tuple: (success (bool), message (str))
        """
        if company_name in self.company_info:
            company_value = self.company_info[company_name]["value"]
            total_cost = amount * company_value
            if self.player_wealth[player] >= total_cost:
                self.player_wealth[player] -= total_cost
                self.player_shares[player][company_name] = self.player_shares[player].get(
                    company_name, 0
                ) + amount
                print(f"{player} bought {amount} shares in '{company_name}' for £{total_cost}.")
                return True, f"{player} bought {amount} shares in {company_name} for £{total_cost}!"
            else:
                print(f"{player} does not have enough money to buy shares in '{company_name}'.")
                return False, f"{player} doesn't have enough money!"
        else:
            print(f"Company '{company_name}' does not exist.")
            return False, f"{company_name} does not exist."

    def sell_shares(self, company_name, player, amount):
        """
        Allows a player to sell shares in a company.

        Parameters:
            company_name (str): The company to sell shares in.
            player (str): The player selling the shares.
            amount (int): The number of shares to sell.

        Returns:
            tuple: (success (bool), message (str))
        """
        if company_name in self.player_shares[player]:
            if self.player_shares[player][company_name] >= amount:
                company_value = self.company_info[company_name]["value"]
                total_earnings = amount * company_value
                self.player_wealth[player] += total_earnings
                self.player_shares[player][company_name] -= amount
                if self.player_shares[player][company_name] == 0:
                    del self.player_shares[player][company_name]
                print(f"{player} sold {amount} shares in '{company_name}' for £{total_earnings}.")
                return True, f"{player} sold {amount} shares in {company_name} for £{total_earnings}!"
            else:
                print(f"{player} does not own {amount} shares in '{company_name}'.")
                return False, f"{player} does not own {amount} shares in {company_name}!"
        else:
            print(f"{player} does not own any shares in '{company_name}'.")
            return False, f"{player} does not own any shares in {company_name}!"

    def _get_connected_diamonds(self, start_coords):
        """
        Returns a set of all diamonds connected to the start_coords using BFS.

        Parameters:
            start_coords (tuple): The starting coordinate.

        Returns:
            set: Set of connected diamond coordinates.
        """
        connected = set()
        queue = deque()
        queue.append(start_coords)
        connected.add(start_coords)

        while queue:
            current = queue.popleft()
            row, col = current
            adjacent = [
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1)
            ]
            for cell in adjacent:
                if cell in self.diamond_positions and cell not in connected:
                    connected.add(cell)
                    queue.append(cell)
        return connected

    def place_diamond(self, coords, current_player):
        """
        Places a diamond at the specified coordinates and handles potential mergers.

        Parameters:
            coords (tuple): The coordinate to place the diamond at.
            current_player (str): The player performing this action.

        Returns:
            tuple: (success (bool), message (str))
        """
        if coords in self.initial_o_marker_locations:
            print(f"Error: Cannot place diamond at {coords}. Position is an 'O' marker tile.")
            return False, "Cannot place diamond on an 'O' marker tile."

        if not (isinstance(coords, tuple) and len(coords) == 2):
            print(f"Error: coords must be a tuple of (row, col). Received: {coords}")
            return False, "Invalid coordinates format."

        if coords in self.company_map or coords in self.diamond_positions:
            print(f"Error: Cannot place diamond at {coords}. Position already occupied.")
            return False, f"Position {coords} is already occupied."

        self.diamond_positions.add(coords)
        print(f"Placed diamond at {coords}.")

        # Find all connected diamonds including the newly placed one
        connected_diamonds = self._get_connected_diamonds(coords)
        print(f"Connected diamonds after placing at {coords}: {connected_diamonds}")

        if len(connected_diamonds) >= 2:
            # Scenario 1: Diamond connects to 2 or more existing diamonds
            if self.available_company_names:
                # Scenario 1.a: Company names are available - form a new company
                print(f"Attempting to form a new company with diamonds: {connected_diamonds} by player {current_player}")
                new_company_name, message = self.create_new_company(list(connected_diamonds), current_player=current_player)
                if new_company_name:
                    # Remove the merged diamonds from diamond_positions as they are now part of a company
                    self.diamond_positions.difference_update(connected_diamonds)
                    print(f"Merged diamonds at {connected_diamonds} into new company '{new_company_name}'.")
                    # player_has_moved is handled by create_new_company when current_player is provided and company is formed.
                    return True, message
                else:
                    # Failed to create company (e.g. an 'O' marker tile was part of connected_diamonds)
                    # The diamond was added to diamond_positions, but if creation fails, it should ideally be removed
                    # or the placement itself should be invalid.
                    # However, create_new_company can fail if a coord in coords_list is an 'O' marker.
                    # If one of the connected_diamonds is an 'O' marker, this path is taken.
                    # The initial diamond placement at 'coords' might be valid, but the broader group isn't.
                    # For now, let's assume if new_company_name is None, the overall action related to
                    # forming a company from this set of diamonds failed.
                    # The problem description implies create_new_company might fail due to other reasons too.
                    # If the failure was due to an 'O' marker, then the diamond at 'coords' might need to be reverted too if strict.
                    # Current logic: if new_company_name is None, it's a failure to form company.
                    # The initial diamond at 'coords' remains in diamond_positions.
                    print(f"Failed to create a new company from diamonds: {message}")
                    # This path indicates a complex failure. The player did attempt a move.
                    # It's debatable if player_has_moved should be True if the *intended* company formation failed.
                    # However, a diamond *was* placed.
                    self.player_has_moved[current_player] = True # A diamond was placed.
                    return False, message # Return the message from create_new_company
            else:
                # Scenario 1.b: All company names are in use - place diamond, no new company
                print(f"Diamond placed at {coords}, connects to {len(connected_diamonds)-1} other diamonds. All company names in use. No new company formed.")
                # The diamond was already added to self.diamond_positions at the start of the function.
                # No company is formed, so diamonds remain in self.diamond_positions.
                self.player_has_moved[current_player] = True
                return True, f"Diamond placed at {coords}. All companies formed, no new company created."
        else:
            # Scenario 2: Standalone diamond or connects to only one other diamond (not enough to form company)
            print(f"Diamond at {coords} does not form a new company. Connected diamonds: {len(connected_diamonds)}")
            # The diamond was already added to self.diamond_positions at the start of the function.
            self.player_has_moved[current_player] = True  # Player has made a move
            return True, f"Diamond placed at {coords}."

    def end_turn(self):
        """
        Ends the current player's turn and resets necessary flags.

        Returns:
            tuple: (success (bool), message (str))
        """
        current_player = self.players[self.current_player_index]
        if not self.player_has_moved[current_player]:
            print(f"{current_player} has not made a move yet!")
            return False, f"{current_player}, please make a move before ending your turn."
        else:
            self.player_has_moved[current_player] = False  # Reset move flag
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            self.turn_counter += 1
            print(f"Turn ended. It's now {self.players[self.current_player_index]}'s turn.")
            return True, f"Turn ended. It's now {self.players[self.current_player_index]}'s turn."

    def get_player_type(self, player_name):
        """
        Returns the type of the given player.
        """
        return self.player_types.get(player_name)

    def ai_take_turn(self, player_name):
        """
        Allows an AI player to take a turn.
        """
        current_player = player_name
        available_cells = []
        # Iterate c from 0 to self.grid_size[1]-1 (cols) and r from 0 to self.grid_size[0]-1 (rows)
        for r in range(self.grid_size[0]): # rows
            for c in range(self.grid_size[1]): # cols
                cell = (r, c)
                if cell not in self.company_map and \
                   cell not in self.diamond_positions and \
                   cell not in self.initial_o_marker_locations:
                    available_cells.append(cell)

        if not available_cells:
            print(f"AI Warning: No available cells for {player_name} to make a move.") # Changed print message
            self.player_has_moved[player_name] = True # Allow turn to pass
            return None, f"{player_name} (AI) has no available moves." # Changed returned message

        selected_cell = random.choice(available_cells)
        print(f"AI {current_player} selected cell: {selected_cell}")

        adj_companies = self.get_adjacent_companies(selected_cell)
        action_taken_message = ""

        if adj_companies:
            # ... existing logic for expanding or merging ...
            if len(adj_companies) == 1:
                company_to_expand = list(adj_companies)[0]
                self.expand_company(selected_cell, company_to_expand, current_player)
                action_taken_message = f"{current_player} (AI) expanded {company_to_expand} at {selected_cell}."
            else: # Multiple adjacent companies
                self.merge_companies(selected_cell, adj_companies, current_player)
                if selected_cell in self.company_map:
                    merged_company_name = self.company_map[selected_cell]["company_name"]
                    action_taken_message = f"{current_player} (AI) merged companies into {merged_company_name} at {selected_cell}."
                else:
                    action_taken_message = f"{current_player} (AI) initiated a merge at {selected_cell}."
        else: # No adjacent companies to selected_cell
            if self.available_company_names and self._can_found_company_at(selected_cell): # Condition A
                new_company_name, message = self.create_new_company(selected_cell, current_player)
                # THE FOLLOWING 'if/else' BLOCK (Condition B) MUST BE NESTED INSIDE THE 'THEN' OF Condition A
                if new_company_name: # Condition B (Correctly Nested)
                    action_taken_message = f"{current_player} (AI) created {new_company_name} at {selected_cell}."
                    # self.player_has_moved is set by create_new_company if successful
                else: # Else for Condition B (Correctly Nested)
                    # create_new_company failed (e.g., cell was an 'O' marker, or other reason from message)
                    # Fallback to placing a diamond
                    if not self.player_has_moved[current_player]: 
                        self.player_has_moved[current_player] = True 
                    success, diamond_message = self.place_diamond(selected_cell, current_player)
                    if success:
                        action_taken_message = f"{current_player} (AI) placed a diamond at {selected_cell} after failing to create company. ({diamond_message})"
                    else:
                        action_taken_message = f"{current_player} (AI) failed to make a move at {selected_cell} after failing to create company and diamond. ({diamond_message})"
            else: # Else for Condition A (around line 661). This should now be syntactically valid.
                # Cannot found a company (no names or no valid adjacency), so place a diamond
                if not self.player_has_moved[current_player]:
                     self.player_has_moved[current_player] = True 
                success, diamond_message = self.place_diamond(selected_cell, current_player)
                if success:
                    action_taken_message = f"{current_player} (AI) placed a diamond at {selected_cell}. ({diamond_message})"
                else:
                    action_taken_message = f"{current_player} (AI) failed to place diamond at {selected_cell}. ({diamond_message})"
        
        # Ensure player_has_moved is True if any action was attempted or if AI decided to pass.
        # The individual calls (create_new_company, place_diamond, expand_company, merge_companies)
        # are responsible for setting self.player_has_moved[current_player] = True upon successful action.
        # If ai_take_turn reaches this point and no action successfully set it,
        # it implies a possible path where an action was attempted but failed in a way that didn't set the flag,
        # or the AI decided to do nothing (which it currently doesn't).
        # The robust check for empty available_cells already handles setting this flag if no move is possible at all.
        # If, after all logic, player_has_moved is STILL false, it's a bug.
        # However, the above logic tries to ensure it's set if any operation is attempted.
        # Let's rely on the action methods themselves or the initial "no available cells" check.

        print(action_taken_message) # Keep for debugging
        return selected_cell, action_taken_message

    def _can_found_company_at(self, coords):
        row, col = coords
        # Define orthogonal neighbors
        potential_neighbors = [
            (row - 1, col), (row + 1, col), # North, South
            (row, col - 1), (row, col + 1)   # West, East
        ]

        for r_neighbor, c_neighbor in potential_neighbors:
            # Check grid boundaries for the neighbor
            # Assuming self.grid_size = (cols, rows) as per subtask note for this method
            if 0 <= r_neighbor < self.grid_size[1] and 0 <= c_neighbor < self.grid_size[0]:
                neighbor_coords = (r_neighbor, c_neighbor)
                if neighbor_coords in self.company_map:
                    return True # Adjacent to an existing company
                if neighbor_coords in self.diamond_positions:
                    return True # Adjacent to a diamond
                if neighbor_coords in self.initial_o_marker_locations:
                    return True # Adjacent to an 'O' marker
        return False # No qualifying adjacencies found

    # Additional methods can be added below as needed
