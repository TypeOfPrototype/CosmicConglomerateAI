# game_logic.py (Corrected Full Version + AI Implementation v3)

import os
import random # Import random for AI
from collections import defaultdict, deque
import math

# --- Constants ---
INITIAL_MONEY = 6000
FOUNDER_BONUS_STOCK = 1
NUM_COMPANIES = 5
SAFE_COMPANY_SIZE = 11
GAME_END_MAX_SIZE = 41 # Example value from snippet
MAJORITY_BONUS_MULTIPLIER = 10 # Example value from snippet
MINORITY_BONUS_MULTIPLIER = 5 # Example value from snippet
MAX_INITIAL_DIAMONDS_CAP = 50 # Absolute max cap

COMPANY_NAMES_LIST = ["Nerdniss", "Beetleguice", "StronCannon", "DebbiesKnees", "Pacifica"]
COMPANY_IDS = {name: i for i, name in enumerate(COMPANY_NAMES_LIST)}
COMPANY_NAMES_BY_ID = {i: name for i, name in enumerate(COMPANY_NAMES_LIST)}

EMPTY = -1
LOOSE_TILE = -2 # Diamond

# --- Class Definitions ---
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
        # Check for share split
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
    """Represents a player (Human or AI) in the game."""
    # --- MODIFIED INIT ---
    def __init__(self, name, is_human=True, ai_difficulty=None): # Added AI flags
        self.name = name
        self.money = INITIAL_MONEY
        self.shares = defaultdict(int) # {company_id: count}
        self.is_human = is_human            # True for human, False for AI
        self.ai_difficulty = ai_difficulty  # None for human, 1=Easy, 2=Medium, 3=Hard
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
        # Include AI difficulty in string representation
        player_type = "Human" if self.is_human else f"AI-{self.ai_difficulty}"
        share_str = ", ".join([f"{COMPANY_NAMES_BY_ID.get(cid, '??')}:{ct}" for cid, ct in sorted(self.shares.items())]) or "None"
        return f"{self.name} ({player_type}): ${self.money}, Shares: {{{share_str}}}"

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
    def __init__(self, player_configs, grid_size_tuple, script_dir, initial_diamonds_config="5%"):
        self.board = GameBoard(grid_size_tuple)
        # --- Create players based on config ---
        self.players = []
        for config in player_configs:
            name, player_type = config
            is_human = (player_type == 'Human')
            ai_difficulty = None
            if player_type == 'AI Easy': ai_difficulty = 1
            elif player_type == 'AI Medium': ai_difficulty = 2
            elif player_type == 'AI Hard': ai_difficulty = 3
            # Pass the new flags to the Player constructor
            self.players.append(Player(name=name, is_human=is_human, ai_difficulty=ai_difficulty))
        # --- End player creation ---

        self.companies = [Company(i, COMPANY_NAMES_BY_ID[i]) for i in range(NUM_COMPANIES)]
        self.current_player_index = 0
        self.turn_counter = 0
        self.game_state = "STARTING" # Will be set to PLAYER_TURN after init
        self._available_company_ids = set(range(NUM_COMPANIES))
        self.script_dir = script_dir
        # Correct logo paths assumed to be in the same directory
        self.company_logos = {
            "Nerdniss": os.path.join(script_dir, 'nerdniss_logo.png'),
            "Beetleguice": os.path.join(script_dir, 'beetleguice_logo.png'),
            "StronCannon": os.path.join(script_dir, 'stroncannon_logo.png'),
            "DebbiesKnees": os.path.join(script_dir, 'debbiesKnees_logo.png'), # Use correct file name case
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
                else: print(f"Warning: Invalid percentage '{config}', defaulting to 0 diamonds.")
            elif config.isdigit(): num_initial_diamonds = int(config)
            else: print(f"Warning: Invalid diamond config '{config}', defaulting to 0 diamonds.")
            num_initial_diamonds = max(0, min(num_initial_diamonds, MAX_INITIAL_DIAMONDS_CAP, total_cells))
        except ValueError: print(f"Warning: Could not parse diamond config '{config}', defaulting to 0 diamonds.") ; num_initial_diamonds = 0
        if num_initial_diamonds > 0:
            possible_coords = [(r, c) for r in range(rows) for c in range(cols)]
            num_to_place = min(num_initial_diamonds, len(possible_coords))
            if num_to_place > 0:
                initial_diamond_coords = random.sample(possible_coords, num_to_place)
                print(f"Placing {num_to_place} initial diamonds. Coords: {initial_diamond_coords}")
                for r, c in initial_diamond_coords:
                    self.board.set_tile(r, c, LOOSE_TILE) ; self._initial_diamond_updates.append(((r,c), LOOSE_TILE))
            else: print("No valid coordinates available.")
        else: print("No initial diamonds placed.")
        # --- End Initial Diamond Placement ---

        self.game_state = "PLAYER_TURN" # Ready for first turn

    def register_callback(self, callback):
        self.callbacks.append(callback)
        print("Registered a new callback for game state updates.")
        if self._initial_diamond_updates:
            print(f"Sending {len(self._initial_diamond_updates)} initial diamond updates to newly registered callback.")
            self.notify_callbacks(self._initial_diamond_updates)
            self._initial_diamond_updates = [] # Clear after sending

    def notify_callbacks(self, updated_entries):
        """Notifies UI of changes."""
        if updated_entries:
             for callback in self.callbacks:
                  try: callback(updated_entries)
                  except Exception as e: print(f"Error in callback: {e}")

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

        # Rule Check: Cannot merge 2+ safe companies
        adj_ids_before, _ = self.board.get_adjacent_entities(row, col)
        safe_adj_before = {cid for cid in adj_ids_before if self.companies[cid].is_safe}
        if len(safe_adj_before) >= 2:
            return False, "Cannot merge two or more safe companies.", []

        # --- Determine Placement Outcome ---
        self.board.set_tile(row, col, LOOSE_TILE) # Use LOOSE_TILE marker temporarily
        adj_company_ids, adj_loose = self.board.get_adjacent_entities(row, col)
        active_adj_company_ids = {cid for cid in adj_company_ids if self.companies[cid].is_active}
        num_adj_active_companies = len(active_adj_company_ids)

        updated_entries = [] ; outcome_message = "" ; placement_result = "UNKNOWN"

        if num_adj_active_companies == 0:
            if not adj_loose: # Standalone diamond
                placement_result = "PLACED_DIAMOND"
                outcome_message = f"{player.name} placed a diamond."
                updated_entries.append(((row, col), LOOSE_TILE))
            else: # Forms new company
                 placement_result = "FORMING_COMPANY"
                 size, area_coords = self.board.calculate_area_size(row, col, LOOSE_TILE)
                 if size >= 2:
                      if self._available_company_ids:
                           self.board.set_tile(row, col, EMPTY) # Remove temporary marker
                           form_success, form_message, form_updates = self._form_company_from_diamonds(area_coords, player)
                           if form_success:
                               placement_result = "FORMED_COMPANY_FROM_DIAMOND"
                               outcome_message = form_message ; updated_entries.extend(form_updates)
                           else: # Should not happen if check passes
                               outcome_message = form_message; placement_result = "ERROR"
                               updated_entries.append(((row, col), LOOSE_TILE)) # Revert?
                      else:
                           outcome_message = "Connected diamonds, but no companies available!"
                           updated_entries.append(((row, col), LOOSE_TILE)); placement_result = "PLACED_DIAMOND"
                 else: # Should not happen if adj_loose is true
                      placement_result = "PLACED_DIAMOND"
                      outcome_message = f"{player.name} placed a diamond."
                      updated_entries.append(((row, col), LOOSE_TILE))

        elif num_adj_active_companies == 1: # Expands company
            placement_result = "EXPANDED_COMPANY"
            company_id = active_adj_company_ids.pop(); company = self.companies[company_id]
            outcome_message = f"{player.name} expanded {company.name}."
            size, loose_area = self.board.calculate_area_size(row, col, LOOSE_TILE)
            company_area = self.board.get_company_area(company_id); full_new_area = loose_area.union(company_area)
            merge_updates = self.board.merge_area(loose_area, company_id); updated_entries.extend(merge_updates)
            split_occurred = company.update_status(len(full_new_area))
            if split_occurred: self._handle_share_split(company_id)
            updated_entries.append(('company_update', company_id))
            self.check_secondary_merges(company_id, player)

        else: # Merger
            placement_result = "MERGED_COMPANIES"
            print(f"Merger triggered at {coords} by {player.name}. Involving: {[COMPANY_NAMES_BY_ID[cid] for cid in active_adj_company_ids]}")
            size, initial_loose_area = self.board.calculate_area_size(row, col, LOOSE_TILE)
            self.board.set_tile(row, col, EMPTY) # Remove temporary marker
            self._start_merger(active_adj_company_ids, initial_loose_area, player)
            outcome_message = f"{player.name} triggered a merger!"

        # Post-action logic (only if not in merger state)
        if self.game_state == "PLAYER_TURN":
             self.player_has_moved[player.name] = True
             if placement_result in ["EXPANDED_COMPANY", "PLACED_DIAMOND", "FORMED_COMPANY_FROM_DIAMOND"]:
                  expansion_updates = self.expand_companies_into_adjacent_diamonds(player)
                  updated_entries.extend(expansion_updates)
             self.notify_callbacks(updated_entries) # Notify only if state didn't change

        return True, outcome_message, updated_entries

    def _form_company_from_diamonds(self, area_coords: set, founder: Player):
        """Internal helper to form a company from connected diamonds."""
        updates = []
        if not self._available_company_ids:
            print("Cannot form company: None available.")
            for r, c in area_coords: self.board.set_tile(r,c, LOOSE_TILE); updates.append(((r,c), LOOSE_TILE))
            return False, "No companies available to form!", updates

        # TODO: Implement UI prompt for player choice. Auto-choose lowest ID for now.
        chosen_id = min(list(self._available_company_ids)); self._available_company_ids.remove(chosen_id)
        company = self.companies[chosen_id]; company.is_active = True
        print(f"{founder.name} is founding {company.name} (ID: {chosen_id}) from {area_coords}")
        merge_upd = self.board.merge_area(area_coords, chosen_id); updates.extend(merge_upd)
        split = company.update_status(len(area_coords)); updates.append(('company_update', chosen_id))
        if split: self._handle_share_split(chosen_id)
        if company.remove_shares(FOUNDER_BONUS_STOCK):
            founder.add_shares(chosen_id, FOUNDER_BONUS_STOCK); updates.append(('player_update', self.players.index(founder)))
        else: print(f"No founder shares available/removable for {company.name}.")
        msg = f"{founder.name} founded {company.name}!"
        self.player_has_moved[founder.name] = True
        self.check_secondary_merges(chosen_id, founder)
        return True, msg, updates

    def _start_merger(self, involved_ids: set, initial_coords: set, trigger_player: Player):
        """Initiates the merger process."""
        if len(involved_ids) < 2: return
        print(f"--- Starting Merger involving IDs: {involved_ids} ---")
        self.game_state = "MERGER_RESOLUTION" # Change game state
        details = [{'id': cid, 'company': self.companies[cid], 'size': self.companies[cid].size, 'is_safe': self.companies[cid].is_safe}
                   for cid in involved_ids if self.companies[cid].is_active]
        if len(details) < 2: self.game_state = "PLAYER_TURN"; return
        details.sort(key=lambda c: c['size'], reverse=True)
        largest = details[0]['size']; pots = [c for c in details if c['size'] == largest]; is_tie = len(pots) > 1
        acq_det = None
        if is_tie:
            print(f"Merger Tie! Sizes: {largest}. Candidates: {[c['company'].name for c in pots]}")
            pots.sort(key=lambda c: c['id']); acq_det = pots[0]; print(f"Auto-choosing {acq_det['company'].name} as acquirer.")
        else: acq_det = pots[0]; print(f"Acquirer: {acq_det['company'].name} (Size: {largest})")
        acq_id = acq_det['id']; acquired = []; survivors = []
        for d in details:
            if d['id'] != acq_id:
                if d['is_safe']: survivors.append(d); print(f"{d['company'].name} is safe and survives.")
                else: acquired.append(d); print(f"{d['company'].name} will be acquired.")
        if not acquired:
            print("Merger voided: All targets are safe."); updates = []
            if initial_coords:
                 merge_upd = self.board.merge_area(initial_coords, acq_id); updates.extend(merge_upd)
                 final_s = len(self.board.get_company_area(acq_id)); split = self.companies[acq_id].update_status(final_s)
                 if split: self._handle_share_split(acq_id)
                 updates.append(('company_update', acq_id)); print(f"Merged initial tiles. New size: {final_s}")
            self.notify_callbacks(updates); self.game_state = "PLAYER_TURN"; self.player_has_moved[trigger_player.name] = True
            return
        self._merger_info = {'acquirer_id': acq_id, 'acquired_details': [{'id': d['id'], 'name': d['company'].name, 'price': d['company'].stock_price} for d in acquired], 'survivor_ids': [d['id'] for d in survivors], 'trigger_player': trigger_player, 'initial_coords': initial_coords}
        print(f"Acquirer: {COMPANY_NAMES_BY_ID[acq_id]}"); print(f"Acquired: {[d['name'] for d in self._merger_info['acquired_details']]}")
        self._pay_merger_bonuses() # Pay bonuses, then finalize (no disposal yet)

    def _pay_merger_bonuses(self):
        """Calculates and pays bonuses for companies being acquired."""
        if not self._merger_info or self.game_state != "MERGER_RESOLUTION": return
        print("--- Paying Merger Bonuses ---"); updates = []
        for acq_det in self._merger_info['acquired_details']:
            acquired_id = acq_det['id']; acquired_name = acq_det['name']; merger_price = acq_det['price']
            print(f"Calculating bonuses for dissolving {acquired_name} (Price @ merger: ${merger_price})")
            bon_list = self._calculate_shareholder_bonuses(acquired_id, merger_price)
            if not bon_list: print(f"  - No bonuses for {acquired_name}."); continue
            for info in bon_list:
                try:
                    p_idx = info['player_index']; p = self.players[p_idx]; p.add_money(info['amount'])
                    print(f"  - Paid ${info['amount']} bonus to {p.name}"); updates.append(('player_update', p_idx))
                except IndexError: print(f"  - Error paying bonus to index {p_idx}")
        self.notify_callbacks(updates); print("--- Bonus Payment Complete ---")
        print("MERGER STEP: Auto-finalizing after bonuses (Share Disposal TODO).")
        self._finalize_merger()

    def _calculate_shareholder_bonuses(self, company_id: int, stock_price_at_merger: int) -> list:
        """Calculates majority/minority bonuses using price at time of merger."""
        bonuses = []; if stock_price_at_merger <= 0: print(f"Warn: Co {company_id} price ${stock_price_at_merger}. No bonuses."); return bonuses
        holders = [{'index': i, 'name': p.name, 'shares': p.get_shares(company_id)} for i, p in enumerate(self.players) if p.get_shares(company_id) > 0]
        if not holders: print(f"  - No shareholders for Co {company_id}."); return bonuses
        holders.sort(key=lambda x: x['shares'], reverse=True)
        maj_b = stock_price_at_merger * MAJORITY_BONUS_MULTIPLIER; min_b = stock_price_at_merger * MINORITY_BONUS_MULTIPLIER
        first_s = holders[0]['shares']; first_h = [sh for sh in holders if sh['shares'] == first_s]
        if len(first_h) > 1:
            total = maj_b + min_b; split = math.ceil(total / len(first_h)); print(f"  - Tie 1st ({first_s} sh). Split ${total} -> ${split} each.")
            for h in first_h: bonuses.append({'player_index': h['index'], 'player_name': h['name'], 'amount': split})
        else:
            maj_h = first_h[0]; bonuses.append({'player_index': maj_h['index'], 'player_name': maj_h['name'], 'amount': maj_b}); print(f"  - Maj Bonus: ${maj_b} to {maj_h['name']} ({first_s} sh).")
            rem = [sh for sh in holders if sh['index'] != maj_h['index']]
            if rem:
                sec_s = rem[0]['shares']
                if sec_s > 0:
                    sec_h = [sh for sh in rem if sh['shares'] == sec_s]; split = math.ceil(min_b / len(sec_h))
                    if len(sec_h) > 1: print(f"  - Tie 2nd ({sec_s} sh). Split ${min_b} -> ${split} each.")
                    else: print(f"  - Min Bonus: ${split} to {sec_h[0]['name']} ({sec_s} sh).")
                    for h in sec_h: bonuses.append({'player_index': h['index'], 'player_name': h['name'], 'amount': split})
                else: print("  - No minority eligible.")
            else: print("  - No others for minority bonus.")
        return bonuses

    def _finalize_merger(self):
        """Final step: merges tiles, updates sizes, deactivates companies."""
        if not self._merger_info: self.game_state = "PLAYER_TURN"; return
        print("\n--- Finalizing Merger ---")
        acq_id = self._merger_info['acquirer_id']; acq_er = self.companies[acq_id]
        acq_ed = self._merger_info['acquired_details']; trig_p = self._merger_info['trigger_player']
        init_c = self._merger_info.get('initial_coords', set()); all_c = set(init_c); updates = []
        for det in acq_ed:
            acq_id_d = det['id']; acq_co = self.companies[acq_id_d]
            print(f"  - Processing dissolved: {acq_co.name}"); all_c.update(self.board.get_company_area(acq_id_d))
            acq_co.deactivate(); updates.append(('company_update', acq_id_d)); self._available_company_ids.add(acq_id_d)
        if all_c:
             print(f"  - Converting {len(all_c)} tiles to {acq_er.name}."); merge_upd = self.board.merge_area(all_c, acq_id); updates.extend(merge_upd)
             final_s = len(self.board.get_company_area(acq_id)); split = acq_er.update_status(final_s); updates.append(('company_update', acq_id))
             if split: self._handle_share_split(acq_id); print(f"  - {acq_er.name} final size: {final_s}")
        else: print("  - Warning: No coords found to merge.")
        print("--- Merger Complete ---")
        trig_p_name = self._merger_info['trigger_player'].name; self._merger_info = None
        self.game_state = "PLAYER_TURN"; self.player_has_moved[trig_p_name] = True
        self.notify_callbacks(updates); self.check_secondary_merges(acq_id, trig_p)

    def check_secondary_merges(self, cid: int, player: Player):
        """Checks if the expansion/merger of a company caused it to touch another."""
        if self.game_state != "PLAYER_TURN": return
        print(f"Checking secondary merges around Co {cid}..."); comp_area = self.board.get_company_area(cid); neigh_comps = set(); init_c = set(); checked = set()
        for r, c in comp_area:
             for nr, nc in self.board.get_neighbors(r, c):
                  coord_n = (nr, nc)
                  if coord_n in checked or coord_n in comp_area : continue
                  checked.add(coord_n); val = self.board.get_tile(nr, nc)
                  if val is not None:
                       if val >= 0:
                           if self.companies[val].is_active and val != cid: neigh_comps.add(val)
                       elif val == LOOSE_TILE:
                           size, loose_a = self.board.calculate_area_size(nr, nc, LOOSE_TILE)
                           if loose_a: init_c.update(loose_a)
        if len(neigh_comps) >= 1:
             all_involved = neigh_comps.union({cid})
             if len(all_involved) >= 2:
                  print(f"Secondary merge! Co {cid} touches {[COMPANY_NAMES_BY_ID[c] for c in neigh_comps]}.") ; updates = []
                  for r_l, c_l in init_c: self.board.set_tile(r_l, c_l, EMPTY); updates.append(((r_l, c_l), EMPTY))
                  if updates: self.notify_callbacks(updates)
                  self._start_merger(all_involved, set(), player) # Pass empty set for initial coords
             else: print("Secondary adjacency detected, but only involves one company total.")
        else: print("No secondary merges detected.")

    def expand_companies_into_adjacent_diamonds(self, player: Player) -> list:
        """Checks diamonds, expands adjacent companies, returns UI updates."""
        if self.game_state != "PLAYER_TURN": return []
        updates = []; diamonds = list(self.board.get_diamond_positions()); absorbed = set(); merger = False
        print(f"Auto-expanding check on {len(diamonds)} diamonds.")
        for d_c in diamonds:
            if merger: break
            if d_c in absorbed or self.board.get_tile(d_c[0], d_c[1]) != LOOSE_TILE: continue
            adj_ids, _ = self.board.get_adjacent_entities(d_c[0], d_c[1])
            active_adj = {cid for cid in adj_ids if self.companies[cid].is_active}; num = len(active_adj)
            if num == 1:
                 cid = active_adj.pop(); company = self.companies[cid]; print(f"Auto-expanding {company.name} into diamond @ {d_c}")
                 size, loose_a = self.board.calculate_area_size(d_c[0], d_c[1], LOOSE_TILE); if not loose_a: continue
                 merge_upd = self.board.merge_area(loose_a, cid); updates.extend(merge_upd); absorbed.update(loose_a)
                 new_s = len(self.board.get_company_area(cid)); split = company.update_status(new_s); updates.append(('company_update', cid))
                 if split: self._handle_share_split(cid)
                 self.check_secondary_merges(cid, player); if self.game_state != "PLAYER_TURN": merger = True
            elif num >= 2:
                 print(f"Diamond @ {d_c} triggers merger between {[COMPANY_NAMES_BY_ID[cid] for cid in active_adj]}")
                 size, loose_a = self.board.calculate_area_size(d_c[0], d_c[1], LOOSE_TILE); absorbed.update(loose_a)
                 for r_r, c_r in loose_a: self.board.set_tile(r_r, c_r, EMPTY); updates.append(((r_r, c_r), EMPTY))
                 self._start_merger(active_adj, set(), player); merger = True
        print(f"Auto-expansion finished. Updates generated: {len(updates)}")
        return updates

    def buy_shares(self, company_id, player_index, amount):
        """Allows a player to buy shares."""
        if not (0 <= company_id < NUM_COMPANIES): return False, "Invalid company ID."
        if not (0 <= player_index < len(self.players)): return False, "Invalid player index."
        if amount <= 0: return False, "Amount must be positive."
        player = self.players[player_index]; company = self.companies[company_id]
        if not company.is_active: return False, f"{company.name} is not active."
        price = company.stock_price; if price <= 0: return False, f"{company.name} shares unavailable (price ${price})."
        total_cost = amount * price; if player.money < total_cost: return False, f"Not enough money (${player.money} < ${total_cost})."
        if company.shares_available < amount: return False, f"Not enough shares in bank ({company.shares_available} < {amount})."
        if player.remove_money(total_cost) and company.remove_shares(amount):
            player.add_shares(company_id, amount); print(f"{player.name} bought {amount}x{company.name} for ${total_cost}.")
            self.notify_callbacks([('player_update', player_index), ('company_update', company_id)])
            return True, f"Bought {amount}x{company.name} for ${total_cost}."
        else: print(f"CRITICAL Error: Share purchase fail {player.name}, {amount}x{company.name}"); return False, "Purchase fail (Internal Error)."

    def sell_shares(self, company_id, player_index, amount):
        """Allows a player to sell shares."""
        if not (0 <= company_id < NUM_COMPANIES): return False, "Invalid company ID."
        if not (0 <= player_index < len(self.players)): return False, "Invalid player index."
        if amount <= 0: return False, "Amount must be positive."
        player = self.players[player_index]; company = self.companies[company_id]
        shares_held = player.get_shares(company_id); if shares_held < amount: return False, f"Not enough shares held ({shares_held} < {amount})."
        price = 0
        if company.is_active: price = company.stock_price
        elif self._merger_info:
             for acq_detail in self._merger_info.get('acquired_details', []):
                  if acq_detail['id'] == company_id: price = acq_detail['price']; break
        if price <= 0: return False, f"Cannot sell {company.name} shares (price ${price})."
        payout = amount * price
        if player.remove_shares(company_id, amount):
            player.add_money(payout); company.add_shares(amount); print(f"{player.name} sold {amount}x{company.name} for ${payout}.")
            self.notify_callbacks([('player_update', player_index), ('company_update', company_id)])
            return True, f"Sold {amount}x{company.name} for ${payout}."
        else: print(f"CRITICAL Error: Share sale fail {player.name}, {amount}x{company.name}"); return False, "Sale fail (Internal Error)."

    def end_turn(self):
        """Ends the current player's turn."""
        current_player = self.get_current_player()
        if not self.player_has_moved[current_player.name]:
            print(f"{current_player.name} has not made a valid move yet.")
            return False, f"{current_player.name}, please make a move."
        print(f"\n--- Ending Turn for {current_player.name} ---")
        self.player_has_moved[current_player.name] = False
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        next_player = self.get_current_player(); self.turn_counter += 1; self.game_state = "PLAYER_TURN"
        print(f"--- Starting Turn {self.turn_counter + 1} for {next_player.name} ---")
        self.notify_callbacks([('turn_update', self.current_player_index)])
        return True, f"It is now {next_player.name}'s turn."

    def _handle_share_split(self, company_id):
         """Doubles player shares for the specified company after a split."""
         updates = [] ; print(f"Processing share split for company ID {company_id}")
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
         p = self.players[player_index]; holdings_value = 0; shares_detail = {}
         for cid, num in sorted(p.shares.items()):
              comp = self.companies[cid]; price = comp.stock_price if comp.is_active else 0
              value = num * price; holdings_value += value; shares_detail[comp.name] = {'count': num, 'price': price, 'value': value}
         return {'name': p.name, 'cash': p.money, 'holdings_value': holdings_value, 'total_wealth': p.money + holdings_value, 'shares_detail': shares_detail}

    def get_company_info(self, company_id):
         """Gets formatted company info."""
         if not (0 <= company_id < NUM_COMPANIES): return None
         c = self.companies[company_id]
         return {'id': c.id, 'name': c.name, 'size': c.size, 'price': c.stock_price, 'available': c.shares_available, 'is_safe': c.is_safe, 'is_active': c.is_active, 'logo': self.company_logos.get(c.name)}

    def get_all_active_company_info(self):
         """Returns info for active companies, keyed by name."""
         info = {}
         for c in self.companies:
              if c.is_active: info[c.name] = {'id': c.id, 'price': c.stock_price, 'available': c.shares_available, 'logo': self.company_logos.get(c.name)}
         return info

    def get_board_state(self):
        """Returns a copy of the board grid state."""
        return [row[:] for row in self.board._grid]

# --- AI Decision Logic ---

def get_ai_tile_placement(player: Player, game_state: GameState) -> tuple | None:
    """Decides where the AI player should place a tile."""
    if player.ai_difficulty == 1:
        return _ai_easy_choose_tile(player, game_state)
    elif player.ai_difficulty == 2:
        # TODO: Implement Medium AI tile logic
        print("AI Medium tile logic not implemented, using Easy.")
        return _ai_easy_choose_tile(player, game_state)
    elif player.ai_difficulty == 3:
        # TODO: Implement Hard AI tile logic
        print("AI Hard tile logic not implemented, using Easy.")
        return _ai_easy_choose_tile(player, game_state)
    return None

def get_ai_stock_purchase(player: Player, game_state: GameState) -> dict | None:
    """Decides which stocks the AI player should buy. Returns dict {cid: amount} or None."""
    if player.ai_difficulty == 1:
         return _ai_easy_buy_stock(player, game_state)
    elif player.ai_difficulty == 2:
         # TODO: Implement Medium AI stock logic
         print("AI Medium stock logic not implemented, using Easy.")
         return _ai_easy_buy_stock(player, game_state)
    elif player.ai_difficulty == 3:
         # TODO: Implement Hard AI stock logic
         print("AI Hard stock logic not implemented, using Easy.")
         return _ai_easy_buy_stock(player, game_state)
    return None

def get_ai_merger_disposal(player: Player, game_state: GameState, acquired_company_id: int) -> tuple[str, int] | None:
     """Decides how the AI player disposes shares during a merger. Returns (action, quantity) or None."""
     # NOTE: This function is currently NOT CALLED because the merger logic auto-finalizes.
     # If you implement player choices during merger disposal, this function will be needed.
     shares_held = player.get_shares(acquired_company_id)
     if shares_held == 0: return None

     merger_price = 0
     if game_state._merger_info:
         for acq_detail in game_state._merger_info.get('acquired_details', []):
             if acq_detail['id'] == acquired_company_id:
                 merger_price = acq_detail.get('price', 0); break
     else: print(f"Warn: AI Merger disposal called without merger info for Co {acquired_company_id}"); return ('keep', shares_held)

     # --- Difficulty Based Logic ---
     if player.ai_difficulty == 1: # Easy AI
          if merger_price > 0:
               print(f"AI Easy ({player.name}): Selling {shares_held}x{acquired_company_id} @ ${merger_price}")
               return ('sell', shares_held)
          else:
               print(f"AI Easy ({player.name}): Keeping {shares_held}x{acquired_company_id} (cannot sell)")
               return ('keep', shares_held)
     elif player.ai_difficulty >= 2: # Medium/Hard AI (Needs more logic)
          # TODO: Implement Medium/Hard disposal logic (e.g., check trade possibility)
          print(f"AI Med/Hard ({player.name}): Disposal logic TODO. Defaulting to Easy.")
          if merger_price > 0: return ('sell', shares_held)
          else: return ('keep', shares_held)

     return ('keep', shares_held) # Default fallback

# --- Helper functions for each difficulty ---
def _ai_easy_choose_tile(player: Player, game_state: GameState) -> tuple | None:
    """Easy AI: Choose a random valid empty square that doesn't merge 2+ safe companies."""
    board_state = game_state.get_board_state()
    empty_squares = []
    rows, cols = game_state.board.rows, game_state.board.cols
    for r in range(rows):
        for c in range(cols):
             if board_state[r][c] == EMPTY:
                  adj_ids, _ = game_state.board.get_adjacent_entities(r, c)
                  safe_adj = {cid for cid in adj_ids if game_state.companies[cid].is_safe}
                  if len(safe_adj) < 2: empty_squares.append((r, c))
    if not empty_squares: return None
    return random.choice(empty_squares)

def _ai_easy_buy_stock(player: Player, game_state: GameState) -> dict | None:
    """Easy AI: Buy 1 random affordable share."""
    purchasable = game_state.get_all_active_company_info()
    affordable = []
    for name, data in purchasable.items():
         price = data.get('price', 0); available = data.get('available', 0); cid = data.get('id')
         if price > 0 and available > 0 and player.money >= price and cid is not None: affordable.append(cid)
    if affordable: return {random.choice(affordable): 1} # Buy exactly 1
    return None

# --- TODO: Implement Medium and Hard AI Logic Helpers ---
# def _ai_medium_choose_tile(player, game_state): pass
# def _ai_medium_buy_stock(player, game_state): pass
# def _ai_hard_choose_tile(player, game_state): pass
# def _ai_hard_buy_stock(player, game_state): pass
