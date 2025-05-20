# game_logic.py (Parse Diamond Config String)

import os
import random
from collections import defaultdict, deque
import math

# --- Constants ---
INITIAL_MONEY = 6000
FOUNDER_BONUS_STOCK = 1
NUM_COMPANIES = 5
SAFE_COMPANY_SIZE = 11
GAME_END_MAX_SIZE = 41
MAJORITY_BONUS_MULTIPLIER = 10
MINORITY_BONUS_MULTIPLIER = 5
# Removed default diamond constants, logic will parse input
MAX_INITIAL_DIAMONDS_CAP = 50 # Absolute max cap

COMPANY_NAMES_LIST = ["Nerdniss", "Beetleguice", "StronCannon", "DebbiesKnees", "Pacifica"]
COMPANY_IDS = {name: i for i, name in enumerate(COMPANY_NAMES_LIST)}
COMPANY_NAMES_BY_ID = {i: name for i, name in enumerate(COMPANY_NAMES_LIST)}

EMPTY = -1
LOOSE_TILE = -2 # Diamond

# --- Class Definitions (Company, Player, GameBoard remain unchanged) ---
class Company:
    """Represents a company in the game."""
    def __init__(self, company_id, name):
        if not (0 <= company_id < NUM_COMPANIES):
            raise ValueError(f"Invalid company_id: {company_id}")
        self.id = company_id
        self.name = name
        self.size = 0
        self.stock_price = 0
        self.shares_available = 25
        self.is_safe = False
        self.is_active = False # Becomes active when first tile is placed

    def update_status(self, new_size):
        """Updates size, stock price, and safe status."""
        self.size = new_size
        self.stock_price = self._calculate_stock_price()
        self.is_safe = self.size >= SAFE_COMPANY_SIZE
        # Check for share split (moved from GameState for better encapsulation)
        # NOTE: Share split price trigger might need adjustment based on gameplay testing with new price tiers
        if self.stock_price >= 3200: # Example threshold, might need tuning
             self.stock_price //= 2 # Halve price
             print(f"SHARE SPLIT triggered for {self.name}! New price: ${self.stock_price}")
             return True # Indicate split occurred
        return False

    def add_shares(self, count):
        """Adds shares back to the available pool."""
        self.shares_available = min(25, self.shares_available + count)

    def remove_shares(self, count):
        """Removes shares from the available pool. Returns True if successful."""
        if self.shares_available >= count:
            self.shares_available -= count
            return True
        return False

    def deactivate(self):
        """Resets company status when acquired in a merger."""
        self.size = 0
        self.stock_price = 0
        self.is_safe = False
        self.is_active = False
        # shares_available does not reset here, happens when players sell/trade

    def _calculate_stock_price(self):
        """Calculates the stock price based on size (Using snippet's tiers)."""
        s = self.size
        # Tier definitions from snippet
        tier1_limit, tier1_price = 2, 200
        tier2_limit, tier2_price = 3, 300
        tier3_limit, tier3_price = 4, 400
        tier4_limit, tier4_price = 5, 500
        tier5_limit, tier5_price = 10, 600
        tier6_limit, tier6_price = 20, 700
        tier7_limit, tier7_price = 30, 800
        tier8_limit, tier8_price = 40, 900
        tier9_price = 1000 # For 41+

        if s == 0: return 0
        elif s <= tier1_limit: return tier1_price
        elif s <= tier2_limit: return tier2_price
        elif s <= tier3_limit: return tier3_price
        elif s <= tier4_limit: return tier4_price
        elif s <= tier5_limit: return tier5_price
        elif s <= tier6_limit: return tier6_price
        elif s <= tier7_limit: return tier7_price
        elif s <= tier8_limit: return tier8_price
        else: return tier9_price

    def __str__(self):
        status = []
        if self.is_active: status.append("Active")
        if self.is_safe: status.append("Safe")
        status_str = ", ".join(status) if status else "Inactive"
        return (f"{self.name}({self.id}): Size={self.size}, Price=${self.stock_price}, "
                f"Shares Left={self.shares_available} [{status_str}]")

class Player:
    """Represents a player in the game."""
    def __init__(self, name):
        self.name = name
        self.money = INITIAL_MONEY
        self.shares = defaultdict(int) # {company_id: count}
        # Tiles aren't used in this GUI version, players select squares

    def get_shares(self, company_id):
        """Gets the number of shares held for a specific company."""
        return self.shares.get(company_id, 0)

    def add_shares(self, company_id, count):
        """Adds shares of a company to the player's portfolio."""
        if count > 0:
            self.shares[company_id] += count

    def remove_shares(self, company_id, count):
        """Removes shares from the player's portfolio. Returns True if successful."""
        if self.shares.get(company_id, 0) >= count:
            self.shares[company_id] -= count
            if self.shares[company_id] == 0:
                del self.shares[company_id] # Remove entry if count is zero
            return True
        return False

    def add_money(self, amount):
        """Adds money to the player's cash."""
        if amount > 0:
            self.money += amount

    def remove_money(self, amount):
        """Removes money from the player's cash. Returns True if successful."""
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    def __str__(self):
        share_str = ", ".join([f"{COMPANY_NAMES_BY_ID.get(cid, '??')}:{ct}" for cid, ct in sorted(self.shares.items())]) or "None"
        return f"{self.name}: ${self.money}, Shares: {{{share_str}}}"

class GameBoard:
    """Represents the game board grid and manages tiles/diamonds."""
    def __init__(self, grid_size_tuple):
        self.rows, self.cols = grid_size_tuple
        # Grid stores company_id, EMPTY, or LOOSE_TILE (diamond)
        self._grid = [[EMPTY] * self.cols for _ in range(self.rows)]
        self._diamond_positions = set() # Keep track of diamond locations

    def is_valid(self, row, col) -> bool:
        """Checks if the coordinates are within the board boundaries."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get_tile(self, row, col) -> int | None:
        """Gets the value of a tile on the grid. Returns None if invalid coords."""
        return self._grid[row][col] if self.is_valid(row, col) else None

    def set_tile(self, row, col, value):
        """Sets the value of a tile on the grid."""
        if self.is_valid(row, col):
            current_value = self._grid[row][col]
            # If placing a diamond, add to set
            if value == LOOSE_TILE:
                self._diamond_positions.add((row, col))
            # If removing a diamond (e.g., merging), remove from set
            elif current_value == LOOSE_TILE and value != LOOSE_TILE:
                 self._diamond_positions.discard((row, col))
            self._grid[row][col] = value
        else:
            raise IndexError(f"Invalid coordinates: ({row}, {col})")

    def get_neighbors(self, row, col) -> list:
        """Gets valid neighbor coordinates [(r, c), ...] for a given tile."""
        neighbors = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Right, Left, Down, Up
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if self.is_valid(nr, nc):
                neighbors.append((nr, nc))
        return neighbors

    def get_adjacent_entities(self, row, col) -> tuple[set, bool]:
        """
        Finds adjacent companies (by id) and checks for adjacent diamonds (loose tiles).
        Returns: (set_of_company_ids, has_adjacent_loose_tile)
        """
        adjacent_company_ids = set()
        has_adjacent_loose = False
        for nr, nc in self.get_neighbors(row, col):
            neighbor_value = self.get_tile(nr, nc)
            if neighbor_value is not None:
                if neighbor_value >= 0: # It's a company ID
                    adjacent_company_ids.add(neighbor_value)
                elif neighbor_value == LOOSE_TILE:
                    has_adjacent_loose = True
        return adjacent_company_ids, has_adjacent_loose

    def calculate_area_size(self, start_row, start_col, target_value) -> tuple[int, set]:
        """
        Calculates the size and coordinates of a connected area of target_value (BFS).
        Handles company IDs or LOOSE_TILE (diamonds).
        """
        if not self.is_valid(start_row, start_col): return 0, set()
        start_val = self.get_tile(start_row, start_col)
        effective_target = start_val if start_val >= 0 else target_value
        if start_val != effective_target: return 0, set()
        if effective_target == EMPTY: return 0, set()
        queue = deque([(start_row, start_col)])
        visited = set([(start_row, start_col)])
        area_coords = set()
        while queue:
            r, c = queue.popleft()
            area_coords.add((r, c))
            for nr, nc in self.get_neighbors(r, c):
                if (nr, nc) not in visited:
                    neighbor_val = self.get_tile(nr, nc)
                    if neighbor_val == effective_target:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        return len(area_coords), area_coords


    def merge_area(self, coordinates: set, new_company_id: int):
        """Changes the value of all tiles in the coordinates set to the new_company_id."""
        updated_coords = []
        for r, c in coordinates:
            if self.is_valid(r,c):
                self.set_tile(r, c, new_company_id)
                updated_coords.append(((r,c), new_company_id))
        return updated_coords # Return list of ((r,c), new_id) for callback

    def get_company_area(self, company_id: int) -> set:
        """Finds all coordinates belonging to a specific company ID."""
        area = set()
        for r in range(self.rows):
            for c in range(self.cols):
                if self._grid[r][c] == company_id:
                    area.add((r, c))
        return area

    def get_diamond_positions(self) -> set:
        return self._diamond_positions.copy()

    def remove_diamond(self, coords: tuple):
        if coords in self._diamond_positions:
            if self.is_valid(coords[0], coords[1]) and self.get_tile(coords[0], coords[1]) == LOOSE_TILE:
                 self._diamond_positions.discard(coords)
                 self.set_tile(coords[0], coords[1], EMPTY)

# --- Game State Manager ---
class GameState:
    # --- MODIFIED INIT ---
    def __init__(self, player_names, grid_size_tuple, script_dir, initial_diamonds_config="5%"): # Accepts config string
        self.board = GameBoard(grid_size_tuple)
        self.players = [Player(name) for name in player_names]
        self.companies = [Company(i, COMPANY_NAMES_BY_ID[i]) for i in range(NUM_COMPANIES)]
        self.current_player_index = 0
        self.turn_counter = 0
        self.game_state = "STARTING"
        self._available_company_ids = set(range(NUM_COMPANIES))
        self.script_dir = script_dir
        self.company_logos = { # Corrected paths
            "Nerdniss": os.path.join(script_dir, 'nerdniss_logo.png'),
            "Beetleguice": os.path.join(script_dir, 'beetleguice_logo.png'),
            "StronCannon": os.path.join(script_dir, 'stroncannon_logo.png'),
            "DebbiesKnees": os.path.join(script_dir, 'debbiesKnees_logo.png'),
            "Pacifica": os.path.join(script_dir, 'pacifica_logo.png'),
        }
        self.diamond_image_path = os.path.join(script_dir, 'diamond.png')
        self.player_has_moved = {player.name: False for player in self.players}
        self._merger_info: dict | None = None
        self.callbacks = []
        self._initial_diamond_updates = []

        # --- Parse Diamond Config and Place Initial Diamonds ---
        num_initial_diamonds = 0
        rows, cols = grid_size_tuple
        total_cells = rows * cols
        config = initial_diamonds_config.strip()

        try:
            if config.endswith('%'):
                percent = float(config[:-1])
                if 0 <= percent <= 100:
                    num_initial_diamonds = int(total_cells * (percent / 100.0))
                else:
                    print(f"Warning: Invalid percentage '{config}', defaulting to 0 diamonds.")
            elif config.isdigit():
                num_initial_diamonds = int(config)
            else:
                 print(f"Warning: Invalid diamond config '{config}', defaulting to 0 diamonds.")

            # Apply cap and ensure non-negative
            num_initial_diamonds = max(0, min(num_initial_diamonds, MAX_INITIAL_DIAMONDS_CAP, total_cells))

        except ValueError:
             print(f"Warning: Could not parse diamond config '{config}', defaulting to 0 diamonds.")
             num_initial_diamonds = 0

        if num_initial_diamonds > 0:
            possible_coords = [(r, c) for r in range(rows) for c in range(cols)]
            # Ensure we don't try to sample more than available
            num_to_place = min(num_initial_diamonds, len(possible_coords))
            if num_to_place > 0:
                initial_diamond_coords = random.sample(possible_coords, num_to_place)
                print(f"Placing {num_to_place} initial diamonds based on config '{config}'. Coords: {initial_diamond_coords}")
                for r, c in initial_diamond_coords:
                    self.board.set_tile(r, c, LOOSE_TILE)
                    self._initial_diamond_updates.append(((r,c), LOOSE_TILE))
            else:
                 print("No valid coordinates available to place initial diamonds.")
        else:
            print("No initial diamonds placed based on config.")
        # --- End Initial Diamond Placement ---

        self.game_state = "PLAYER_TURN"

    def register_callback(self, callback):
        self.callbacks.append(callback)
        print("Registered a new callback for game state updates.")
        # Send initial updates *now* that the callback is registered
        if self._initial_diamond_updates:
            print(f"Sending {len(self._initial_diamond_updates)} initial diamond updates to newly registered callback.")
            self.notify_callbacks(self._initial_diamond_updates)
            self._initial_diamond_updates = [] # Clear after sending

    # --- Methods `notify_callbacks` and beyond remain the same ---
    # ... (Paste the rest of the methods from the previous game_logic.py response here) ...
    def notify_callbacks(self, updated_entries):
        """Notifies UI of changes."""
        if updated_entries:
             # print(f"Notifying callbacks with: {updated_entries}") # Debug
             for callback in self.callbacks:
                  try:
                      callback(updated_entries)
                  except Exception as e:
                      print(f"Error in callback: {e}")

    def get_initial_board_updates(self):
        """Returns the list of initially placed diamonds for the UI."""
        # This method might not be needed if registration happens before any updates.
        # Kept for potential use, but the logic in register_callback handles it now.
        return self._initial_diamond_updates # Might be empty if already sent

    # --- Rest of GameState methods remain the same as the previous version ---
    # get_current_player, place_tile, _form_company_from_diamonds,
    # _start_merger, _pay_merger_bonuses, _calculate_shareholder_bonuses,
    # _finalize_merger, check_secondary_merges, expand_companies_into_adjacent_diamonds,
    # buy_shares, sell_shares, end_turn, _handle_share_split,
    # _get_connected_diamonds, get_player_info, get_company_info,
    # get_all_active_company_info, get_board_state
    # ... (Paste the rest of the methods from the previous game_logic.py response here) ...
    def get_current_player(self) -> Player:
        return self.players[self.current_player_index]

    # --- Core Game Actions ---

    def place_tile(self, coords):
        """Handles player selecting a square (tile placement in Acquire)."""
        if self.game_state != "PLAYER_TURN":
             print(f"Cannot place tile in state: {self.game_state}")
             return False, "Not the right time to place a tile.", []

        player = self.get_current_player()
        row, col = coords

        if not self.board.is_valid(row, col) or self.board.get_tile(row, col) != EMPTY:
            return False, "Invalid or occupied square.", []

        # Prevent placing next to SAFE companies if it causes a merge of 2+ safe companies
        adj_company_ids_before, _ = self.board.get_adjacent_entities(row, col)
        safe_adj_company_ids_before = {cid for cid in adj_company_ids_before if self.companies[cid].is_safe}
        if len(safe_adj_company_ids_before) >= 2:
            print(f"Illegal Move: Cannot place tile at {coords} as it would merge {len(safe_adj_company_ids_before)} safe companies.")
            return False, "Cannot merge two or more safe companies.", []

        # --- Determine Placement Outcome ---
        # Place temporary marker (like the LOOSE_TILE in snippet) to calculate connected area
        self.board.set_tile(row, col, LOOSE_TILE) # Temporarily use LOOSE_TILE marker
        # Re-fetch adjacent entities *after* placing the temporary marker
        adj_company_ids, adj_loose = self.board.get_adjacent_entities(row, col)
        active_adj_company_ids = {cid for cid in adj_company_ids if self.companies[cid].is_active}
        num_adj_active_companies = len(active_adj_company_ids)

        updated_entries = [] # Track changes for callback
        outcome_message = ""
        placement_result = "UNKNOWN"

        if num_adj_active_companies == 0:
            if not adj_loose: # Adjacent only to empty or boundaries
                # Standalone diamond placement
                placement_result = "PLACED_DIAMOND"
                outcome_message = f"{player.name} placed a diamond."
                # Diamond position is handled by set_tile call above
                updated_entries.append(((row, col), LOOSE_TILE)) # Confirm diamond placement
                print(f"Placed standalone diamond at {coords}")
            else: # Adjacent to other diamonds
                 # Forms a new company with adjacent diamonds
                 placement_result = "FORMING_COMPANY"
                 # Calculate size using the temporary marker
                 size, area_coords = self.board.calculate_area_size(row, col, LOOSE_TILE)
                 print(f"Tile at {coords} connects {len(area_coords)-1} other diamond(s). Area: {area_coords}")
                 if size >= 2: # Need at least 2 tiles (placed + adjacent) to form
                      if self._available_company_ids:
                           # Remove the temporary diamond marker before forming
                           self.board.set_tile(row, col, EMPTY)
                           # Pass area_coords to the formation function
                           form_success, form_message, form_updates = self._form_company_from_diamonds(area_coords, player)
                           if form_success:
                               placement_result = "FORMED_COMPANY_FROM_DIAMOND"
                               outcome_message = form_message
                               updated_entries.extend(form_updates) # Updates handled within helper
                           else: # Should not happen if available_company_ids check passes
                                outcome_message = form_message
                                placement_result = "ERROR"
                                updated_entries.append(((row, col), LOOSE_TILE)) # Revert to diamond?
                      else:
                           outcome_message = "Connected diamonds, but no companies available!"
                           print(outcome_message)
                           # Leave as diamond (temporary marker already placed)
                           updated_entries.append(((row, col), LOOSE_TILE))
                           placement_result = "PLACED_DIAMOND" # Fallback
                 else: # Should not happen if adj_loose is true, but safety check
                      print(f"Warning: adj_loose was true but calculated area size was {size} at {coords}")
                      # Treat as standalone diamond placement
                      placement_result = "PLACED_DIAMOND"
                      outcome_message = f"{player.name} placed a diamond."
                      updated_entries.append(((row, col), LOOSE_TILE))


        elif num_adj_active_companies == 1:
            # Expands an existing company
            placement_result = "EXPANDED_COMPANY"
            company_id = active_adj_company_ids.pop()
            company = self.companies[company_id]
            outcome_message = f"{player.name} expanded {company.name}."
            print(outcome_message)

            # Calculate the full area including the new tile and any connected loose tiles
            size, loose_area = self.board.calculate_area_size(row, col, LOOSE_TILE)
            # Get the existing company area *before* merging
            company_area = self.board.get_company_area(company_id)
            full_new_area = loose_area.union(company_area)

            # Merge the loose area into the company
            merge_updates = self.board.merge_area(loose_area, company_id) # Only merge the loose tiles
            updated_entries.extend(merge_updates)

            # Update company status based on the *new total size*
            new_size = len(full_new_area)
            split_occurred = company.update_status(new_size)
            if split_occurred:
                 self._handle_share_split(company_id)
            updated_entries.append(('company_update', company_id)) # Notify UI about company change

            # Check for further merges caused by expansion AFTER updating size
            self.check_secondary_merges(company_id, player)


        else: # num_adj_active_companies >= 2
            # Causes a merger
            placement_result = "MERGED_COMPANIES"
            print(f"Merger triggered at {coords} by {player.name}. Involving: {[COMPANY_NAMES_BY_ID[cid] for cid in active_adj_company_ids]}")
            # Calculate full area involved in the initial merge trigger (connected diamonds)
            size, initial_loose_area = self.board.calculate_area_size(row, col, LOOSE_TILE)

            # Remove the temporary marker now that we've used it
            self.board.set_tile(row, col, EMPTY) # Set back to empty temporarily

            self._start_merger(active_adj_company_ids, initial_loose_area, player)
            # Further updates handled by merger process
            outcome_message = f"{player.name} triggered a merger!"
            # State changes to MERGER_*

        # If state is still PLAYER_TURN (no merger started)
        if self.game_state == "PLAYER_TURN":
             self.player_has_moved[player.name] = True
             # Auto expand into adjacent diamonds *after* the main placement action resolves
             if placement_result in ["EXPANDED_COMPANY", "PLACED_DIAMOND", "FORMED_COMPANY_FROM_DIAMOND"]:
                  print("Checking for auto-expansion into adjacent diamonds...")
                  expansion_updates = self.expand_companies_into_adjacent_diamonds(player)
                  updated_entries.extend(expansion_updates)

        print(f"place_tile result: {placement_result}, final state: {self.game_state}, message: {outcome_message}")
        # Notify only if state didn't change to merger (merger handles its own notifications)
        if self.game_state == "PLAYER_TURN":
             self.notify_callbacks(updated_entries)
        return True, outcome_message, updated_entries # Return updates for potential immediate use?


    def _form_company_from_diamonds(self, area_coords: set, founder: Player):
        """Internal helper to form a company from connected diamonds."""
        updates = []
        if not self._available_company_ids:
            print("Cannot form company: None available.")
            for r, c in area_coords:
                 self.board.set_tile(r,c, LOOSE_TILE)
                 updates.append(((r,c), LOOSE_TILE))
            # Don't notify here, let caller handle it
            return False, "No companies available to form!", updates

        # --- Player Choice Needed ---
        # TODO: Implement UI prompt for player choice. Auto-choose lowest ID for now.
        chosen_company_id = min(list(self._available_company_ids))
        self._available_company_ids.remove(chosen_company_id)
        company = self.companies[chosen_company_id]
        company.is_active = True
        print(f"{founder.name} is founding {company.name} (ID: {chosen_company_id}) from {area_coords}")

        # Update board
        merge_updates = self.board.merge_area(area_coords, chosen_company_id)
        updates.extend(merge_updates)

        # Update company status
        split_occurred = company.update_status(len(area_coords))
        if split_occurred: self._handle_share_split(chosen_company_id) # Check for split
        updates.append(('company_update', chosen_company_id))

        # Grant founder bonus
        if company.remove_shares(FOUNDER_BONUS_STOCK):
            founder.add_shares(chosen_company_id, FOUNDER_BONUS_STOCK)
            print(f"Granted 1 founder share of {company.name} to {founder.name}.")
            updates.append(('player_update', self.players.index(founder)))
        else:
            print(f"No founder shares available/removable for {company.name}.")

        message = f"{founder.name} founded {company.name}!"
        self.player_has_moved[founder.name] = True # Mark move complete

        # Check for secondary merges immediately after forming
        self.check_secondary_merges(chosen_company_id, founder)

        # Return updates, but don't notify here. Caller (place_tile) will notify
        # if the game state didn't change to MERGER.
        return True, message, updates


    def _start_merger(self, involved_company_ids: set, initial_coords: set, trigger_player: Player):
        """Initiates the merger process."""
        if len(involved_company_ids) < 2:
             print("Merger cancelled: Fewer than 2 active companies involved.")
             return

        print(f"--- Starting Merger involving IDs: {involved_company_ids} ---")
        self.game_state = "MERGER_RESOLUTION" # Change game state

        details = [{'id': cid, 'company': self.companies[cid], 'size': self.companies[cid].size, 'is_safe': self.companies[cid].is_safe}
                   for cid in involved_company_ids if self.companies[cid].is_active]

        if len(details) < 2:
            print("Error: Merger triggered but less than 2 active companies found.")
            self.game_state = "PLAYER_TURN"
            return

        details.sort(key=lambda c: c['size'], reverse=True)
        largest_size = details[0]['size']
        potential_acquirers = [c for c in details if c['size'] == largest_size]
        is_tie = len(potential_acquirers) > 1

        acquirer_detail = None
        if is_tie:
            # TODO: Implement player choice mechanism via UI callback
            print(f"Merger Tie! Sizes: {largest_size}. Candidates: {[c['company'].name for c in potential_acquirers]}")
            potential_acquirers.sort(key=lambda c: c['id'])
            acquirer_detail = potential_acquirers[0] # Auto-choose lowest ID
            print(f"Auto-choosing {acquirer_detail['company'].name} as acquirer.")
        else:
            acquirer_detail = potential_acquirers[0]
            print(f"Acquirer: {acquirer_detail['company'].name} (Size: {largest_size})")

        acquirer_id = acquirer_detail['id']
        acquired_details = []
        survivors = []

        for c_detail in details:
            if c_detail['id'] != acquirer_id:
                if c_detail['is_safe']:
                    survivors.append(c_detail)
                    print(f"{c_detail['company'].name} is safe and survives.")
                else:
                    acquired_details.append(c_detail)
                    print(f"{c_detail['company'].name} will be acquired.")

        if not acquired_details:
            print("Merger voided: All targets are safe.")
            updates = []
            if initial_coords:
                 merge_updates = self.board.merge_area(initial_coords, acquirer_id)
                 updates.extend(merge_updates)
                 final_size = len(self.board.get_company_area(acquirer_id))
                 split_occurred = self.companies[acquirer_id].update_status(final_size)
                 if split_occurred: self._handle_share_split(acquirer_id)
                 updates.append(('company_update', acquirer_id))
                 print(f"Merged initial tiles into {self.companies[acquirer_id].name}. New size: {final_size}")

            self.notify_callbacks(updates)
            self.game_state = "PLAYER_TURN"
            self.player_has_moved[trigger_player.name] = True
            return

        self._merger_info = {
            'acquirer_id': acquirer_id,
            'acquired_details': [{'id': d['id'], 'name': d['company'].name, 'price': d['company'].stock_price} for d in acquired_details],
            'survivor_ids': [d['id'] for d in survivors],
            'trigger_player': trigger_player,
            'initial_coords': initial_coords,
            'current_acquired_idx': 0,
            'current_player_disposal_idx': self.current_player_index
        }

        print(f"Acquirer: {COMPANY_NAMES_BY_ID[acquirer_id]}")
        print(f"Acquired: {[d['name'] for d in self._merger_info['acquired_details']]}")

        self._pay_merger_bonuses()


    def _pay_merger_bonuses(self):
        """Calculates and pays bonuses for companies being acquired."""
        if not self._merger_info or self.game_state != "MERGER_RESOLUTION": return
        print("--- Paying Merger Bonuses ---")
        updates = []
        for acq_detail in self._merger_info['acquired_details']:
            acquired_id = acq_detail['id']
            acquired_name = acq_detail['name']
            merger_price = acq_detail['price']
            print(f"Calculating bonuses for dissolving {acquired_name} (Price at merger: ${merger_price})")

            bonus_list = self._calculate_shareholder_bonuses(acquired_id, merger_price)
            if not bonus_list:
                 print(f"  - No bonuses for {acquired_name}.")
                 continue

            for info in bonus_list:
                try:
                    player_index = info['player_index']
                    player = self.players[player_index]
                    player.add_money(info['amount'])
                    print(f"  - Paid ${info['amount']} bonus to {player.name}")
                    updates.append(('player_update', player_index))
                except IndexError:
                    print(f"  - Error paying bonus to index {player_index}")

        self.notify_callbacks(updates)
        print("--- Bonus Payment Complete ---")

        # TODO: Transition to Share Disposal phase
        print("MERGER STEP: Share Disposal UI/Logic Needed Here.")
        self._finalize_merger()


    def _calculate_shareholder_bonuses(self, company_id: int, stock_price_at_merger: int) -> list:
        """Calculates majority/minority bonuses using price at time of merger."""
        bonuses = []
        if stock_price_at_merger <= 0:
             print(f"  - Warning: Company {company_id} had price ${stock_price_at_merger} at merger. No bonuses.")
             return bonuses
        shareholders = [{'index': i, 'name': p.name, 'shares': p.get_shares(company_id)}
                        for i, p in enumerate(self.players) if p.get_shares(company_id) > 0]
        if not shareholders:
             print(f"  - No shareholders for Company {company_id}. No bonuses.")
             return bonuses
        shareholders.sort(key=lambda x: x['shares'], reverse=True)
        majority_bonus = stock_price_at_merger * MAJORITY_BONUS_MULTIPLIER
        minority_bonus = stock_price_at_merger * MINORITY_BONUS_MULTIPLIER
        first_shares = shareholders[0]['shares']
        first_holders = [sh for sh in shareholders if sh['shares'] == first_shares]
        if len(first_holders) > 1:
            total_bonus = majority_bonus + minority_bonus
            split_amount = math.ceil(total_bonus / len(first_holders))
            print(f"  - Tie for 1st ({first_shares} sh). Splitting ${total_bonus} -> ${split_amount} each.")
            for h in first_holders:
                bonuses.append({'player_index': h['index'], 'player_name': h['name'], 'amount': split_amount})
        else:
            maj_h = first_holders[0]
            bonuses.append({'player_index': maj_h['index'], 'player_name': maj_h['name'], 'amount': majority_bonus})
            print(f"  - Majority Bonus: ${majority_bonus} to {maj_h['name']} ({first_shares} sh).")
            remaining_holders = [sh for sh in shareholders if sh['index'] != maj_h['index']]
            if remaining_holders:
                second_shares = remaining_holders[0]['shares']
                if second_shares > 0:
                    second_holders = [sh for sh in remaining_holders if sh['shares'] == second_shares]
                    split_amount = math.ceil(minority_bonus / len(second_holders))
                    if len(second_holders) > 1:
                         print(f"  - Tie for 2nd ({second_shares} sh). Splitting ${minority_bonus} -> ${split_amount} each.")
                    else:
                         print(f"  - Minority Bonus: ${split_amount} to {second_holders[0]['name']} ({second_shares} sh).")
                    for h in second_holders:
                         bonuses.append({'player_index': h['index'], 'player_name': h['name'], 'amount': split_amount})
                else: print("  - No minority shareholders eligible.")
            else: print("  - No other shareholders for minority bonus.")
        return bonuses


    def _finalize_merger(self):
        """Final step: merges tiles, updates sizes, deactivates companies."""
        if not self._merger_info:
            print("Error: Cannot finalize merger, no info.")
            self.game_state = "PLAYER_TURN"
            return

        print("\n--- Finalizing Merger ---")
        acquirer_id = self._merger_info['acquirer_id']
        acquirer = self.companies[acquirer_id]
        acquired_details = self._merger_info['acquired_details']
        trigger_player = self._merger_info['trigger_player']
        initial_coords = self._merger_info.get('initial_coords', set())

        all_merged_coords = set(initial_coords)
        updates = []

        for acq_detail in acquired_details:
            acq_id = acq_detail['id']
            acq_co = self.companies[acq_id]
            print(f"  - Processing dissolved company: {acq_co.name}")
            acq_area = self.board.get_company_area(acq_id)
            all_merged_coords.update(acq_area)
            acq_co.deactivate()
            updates.append(('company_update', acq_id))
            self._available_company_ids.add(acq_id)

        if all_merged_coords:
             print(f"  - Converting {len(all_merged_coords)} tiles to {acquirer.name}.")
             merge_updates = self.board.merge_area(all_merged_coords, acquirer_id)
             updates.extend(merge_updates)
             final_size = len(self.board.get_company_area(acquirer_id))
             split_occurred = acquirer.update_status(final_size)
             if split_occurred: self._handle_share_split(acquirer_id)
             updates.append(('company_update', acquirer_id))
             print(f"  - {acquirer.name} final size: {acquirer.size}, Price: ${acquirer.stock_price}, Safe: {acquirer.is_safe}")
        else:
            print("  - Warning: No coordinates found to merge.")

        print("--- Merger Complete ---")
        merger_trigger_player_name = self._merger_info['trigger_player'].name
        self._merger_info = None
        self.game_state = "PLAYER_TURN"
        self.player_has_moved[merger_trigger_player_name] = True
        self.notify_callbacks(updates)

        self.check_secondary_merges(acquirer_id, trigger_player) # Use original trigger_player


    def check_secondary_merges(self, recently_changed_company_id: int, player: Player):
        """Checks if the expansion/merger of a company caused it to touch another."""
        if self.game_state != "PLAYER_TURN": return

        print(f"Checking for secondary merges around company {recently_changed_company_id}...")
        company_area = self.board.get_company_area(recently_changed_company_id)
        neighboring_companies = set()
        initial_coords_for_secondary = set()
        checked_neighbors = set()

        for r_tile, c_tile in company_area:
             for nr, nc in self.board.get_neighbors(r_tile, c_tile):
                  coords_neighbor = (nr, nc)
                  if coords_neighbor in checked_neighbors or coords_neighbor in company_area : continue
                  checked_neighbors.add(coords_neighbor)

                  neighbor_val = self.board.get_tile(nr, nc)
                  if neighbor_val is not None:
                       if neighbor_val >= 0:
                           if self.companies[neighbor_val].is_active and neighbor_val != recently_changed_company_id:
                                neighboring_companies.add(neighbor_val)
                       elif neighbor_val == LOOSE_TILE:
                           size, loose_area = self.board.calculate_area_size(nr, nc, LOOSE_TILE)
                           if loose_area:
                                initial_coords_for_secondary.update(loose_area)

        if len(neighboring_companies) >= 1:
             all_involved_ids = neighboring_companies.union({recently_changed_company_id})
             if len(all_involved_ids) >= 2:
                  print(f"Secondary merge detected! Company {recently_changed_company_id} touches {[COMPANY_NAMES_BY_ID[cid] for cid in neighboring_companies]}.")
                  # Remove any loose tiles that triggered this before starting merge
                  updates = []
                  for r_loose, c_loose in initial_coords_for_secondary:
                      self.board.set_tile(r_loose, c_loose, EMPTY)
                      updates.append(((r_loose, c_loose), EMPTY))
                  if updates: self.notify_callbacks(updates)

                  self._start_merger(all_involved_ids, set(), player) # Pass empty set for initial coords
             else: print("Secondary adjacency detected, but only involves one company total.")
        else: print("No secondary merges detected.")


    def expand_companies_into_adjacent_diamonds(self, player: Player) -> list:
        """Checks diamonds, expands adjacent companies, returns UI updates."""
        if self.game_state != "PLAYER_TURN": return []

        updates = []
        diamonds_to_process = list(self.board.get_diamond_positions())
        absorbed_diamonds = set()
        triggered_merger = False

        print(f"Auto-expanding check on {len(diamonds_to_process)} diamonds.")

        for d_coords in diamonds_to_process:
            if triggered_merger: break
            if d_coords in absorbed_diamonds: continue
            if self.board.get_tile(d_coords[0], d_coords[1]) != LOOSE_TILE: continue

            adj_company_ids, _ = self.board.get_adjacent_entities(d_coords[0], d_coords[1])
            active_adj_company_ids = {cid for cid in adj_company_ids if self.companies[cid].is_active}
            num_adj = len(active_adj_company_ids)

            if num_adj == 1:
                 company_id = active_adj_company_ids.pop()
                 company = self.companies[company_id]
                 print(f"Auto-expanding {company.name} into diamond at {d_coords}")
                 size, connected_diamond_area = self.board.calculate_area_size(d_coords[0], d_coords[1], LOOSE_TILE)
                 if not connected_diamond_area: continue

                 merge_updates = self.board.merge_area(connected_diamond_area, company_id)
                 updates.extend(merge_updates)
                 absorbed_diamonds.update(connected_diamond_area)

                 new_size = len(self.board.get_company_area(company_id))
                 split_occurred = company.update_status(new_size)
                 if split_occurred: self._handle_share_split(company_id)
                 updates.append(('company_update', company_id))

                 self.check_secondary_merges(company_id, player)
                 if self.game_state != "PLAYER_TURN": triggered_merger = True

            elif num_adj >= 2:
                 print(f"Diamond at {d_coords} triggers merger between {[COMPANY_NAMES_BY_ID[cid] for cid in active_adj_company_ids]}")
                 size, connected_diamond_area = self.board.calculate_area_size(d_coords[0], d_coords[1], LOOSE_TILE)
                 absorbed_diamonds.update(connected_diamond_area)
                 for r_rem, c_rem in connected_diamond_area:
                      self.board.set_tile(r_rem, c_rem, EMPTY)
                      updates.append(((r_rem, c_rem), EMPTY))

                 self._start_merger(active_adj_company_ids, set(), player)
                 triggered_merger = True

        print(f"Auto-expansion finished. Updates generated: {len(updates)}")
        return updates


    def buy_shares(self, company_id, player_index, amount):
        """Allows a player to buy shares."""
        if not (0 <= company_id < NUM_COMPANIES): return False, "Invalid company ID."
        if not (0 <= player_index < len(self.players)): return False, "Invalid player index."
        if amount <= 0: return False, "Amount must be positive."
        player = self.players[player_index]
        company = self.companies[company_id]
        if not company.is_active: return False, f"{company.name} is not active."
        price = company.stock_price
        if price <= 0: return False, f"{company.name} shares unavailable (price ${price})."
        total_cost = amount * price
        if player.money < total_cost: return False, f"Not enough money (${player.money} < ${total_cost})."
        if company.shares_available < amount: return False, f"Not enough shares in bank ({company.shares_available} < {amount})."
        if player.remove_money(total_cost) and company.remove_shares(amount):
            player.add_shares(company_id, amount)
            print(f"{player.name} bought {amount} shares of {company.name} for ${total_cost}.")
            self.notify_callbacks([('player_update', player_index), ('company_update', company_id)])
            return True, f"Bought {amount}x{company.name} for ${total_cost}."
        else:
            print(f"CRITICAL Error: Share purchase failed for {player.name}, {amount}x{company.name} despite checks!")
            return False, "Purchase failed unexpectedly (Internal Error)."


    def sell_shares(self, company_id, player_index, amount):
        """Allows a player to sell shares."""
        if not (0 <= company_id < NUM_COMPANIES): return False, "Invalid company ID."
        if not (0 <= player_index < len(self.players)): return False, "Invalid player index."
        if amount <= 0: return False, "Amount must be positive."
        player = self.players[player_index]
        company = self.companies[company_id]
        shares_held = player.get_shares(company_id)
        if shares_held < amount: return False, f"Not enough shares held ({shares_held} < {amount})."
        price = 0
        if company.is_active:
            price = company.stock_price
        elif self._merger_info:
             for acq_detail in self._merger_info.get('acquired_details', []):
                  if acq_detail['id'] == company_id:
                       price = acq_detail['price']
                       break
        if price <= 0:
            return False, f"Cannot sell {company.name} shares (price ${price})."
        payout = amount * price
        if player.remove_shares(company_id, amount):
            player.add_money(payout)
            company.add_shares(amount)
            print(f"{player.name} sold {amount} shares of {company.name} for ${payout}.")
            self.notify_callbacks([('player_update', player_index), ('company_update', company_id)])
            return True, f"Sold {amount}x{company.name} for ${payout}."
        else:
            print(f"CRITICAL Error: Share sale failed for {player.name}, {amount}x{company.name} despite checks!")
            return False, "Sale failed unexpectedly (Internal Error)."


    def end_turn(self):
        """Ends the current player's turn."""
        current_player = self.get_current_player()
        if not self.player_has_moved[current_player.name]:
            print(f"{current_player.name} has not made a valid move yet.")
            return False, f"{current_player.name}, please make a move."
        print(f"\n--- Ending Turn for {current_player.name} ---")
        self.player_has_moved[current_player.name] = False
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        next_player = self.get_current_player()
        self.turn_counter += 1
        self.game_state = "PLAYER_TURN"
        print(f"--- Starting Turn {self.turn_counter + 1} for {next_player.name} ---")
        self.notify_callbacks([('turn_update', self.current_player_index)])
        return True, f"It is now {next_player.name}'s turn."


    def _handle_share_split(self, company_id):
         """Doubles player shares for the specified company after a split."""
         updates = []
         print(f"Processing share split for company ID {company_id}")
         for i, player in enumerate(self.players):
              current_shares = player.get_shares(company_id)
              if current_shares > 0:
                   player.add_shares(company_id, current_shares)
                   print(f"  - Doubled {COMPANY_NAMES_BY_ID[company_id]} shares for {player.name} to {player.get_shares(company_id)}")
                   updates.append(('player_update', i))
         self.notify_callbacks(updates)


    def _get_connected_diamonds(self, start_coords):
        """Finds all connected diamonds using BFS."""
        return self.board.calculate_area_size(start_coords[0], start_coords[1], LOOSE_TILE)[1]

    # --- Getters for UI ---
    def get_player_info(self, player_index):
         """Gets formatted player info."""
         if not (0 <= player_index < len(self.players)): return None
         p = self.players[player_index]
         holdings_value = 0
         shares_detail = {}
         for cid, num in sorted(p.shares.items()):
              comp = self.companies[cid]
              price = comp.stock_price if comp.is_active else 0
              value = num * price
              holdings_value += value
              shares_detail[comp.name] = {'count': num, 'price': price, 'value': value}
         return {
              'name': p.name,
              'cash': p.money,
              'holdings_value': holdings_value,
              'total_wealth': p.money + holdings_value,
              'shares_detail': shares_detail
         }

    def get_company_info(self, company_id):
         """Gets formatted company info."""
         if not (0 <= company_id < NUM_COMPANIES): return None
         c = self.companies[company_id]
         return {
              'id': c.id,
              'name': c.name,
              'size': c.size,
              'price': c.stock_price,
              'available': c.shares_available,
              'is_safe': c.is_safe,
              'is_active': c.is_active,
              'logo': self.company_logos.get(c.name)
         }

    def get_all_active_company_info(self):
         """Returns info for active companies, keyed by name."""
         info = {}
         for c in self.companies:
              if c.is_active:
                   info[c.name] = {
                        'id': c.id,
                        'price': c.stock_price,
                        'available': c.shares_available,
                        'logo': self.company_logos.get(c.name)
                   }
         return info

    def get_board_state(self):
        """Returns a copy of the board grid state."""
        return [row[:] for row in self.board._grid]
