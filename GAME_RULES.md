## Original User Request:
Space Monopoly Game Mechanics Blueprint

This document details the core rules and mechanics for the Space Monopoly board game simulation.

**1. Game Setup**

* **Players:**
    * The game supports 2 to 4 players (configurable, requires at least 2).
    * Each player starts with a fixed amount of initial cash (e.g., £6000).
    * Player state includes: Name, Current Cash, Stock Portfolio (shares held per company).
* **Game Board:**
    * A rectangular grid (e.g., 16x12, 22x18, 28x24). Board dimensions are configurable at setup.
    * Each grid square can be in one of the following states:
        * Empty
        * Loose Tile ("Diamond"): A placed tile not yet part of a company.
        * Occupied by Company: Contains the ID of the company occupying it.
* **Companies:**
    * A fixed number of distinct companies exist (e.g., 5: Nerdniss, Beetleguice, StronCannon, DebbiesKnees, Pacifica).
    * Each company has:
        * Unique ID (0 to N-1)
        * Name
        * Size (number of connected tiles on the board)
        * Stock Price (determined by size tiers)
        * Total Shares Available (fixed pool, e.g., 25 per company)
        * Safe Status (becomes `True` when size reaches a threshold, e.g., 11 tiles)
        * Active Status (becomes `True` when founded, `False` when defunct/acquired)
* **Initial Board State:**
    * The board starts empty except for an initial placement of "Loose Tiles" (Diamonds).
    * The number of initial diamonds can be configured as a fixed number or a percentage of the total board squares, subject to a maximum cap.
    * These diamonds are placed randomly on empty squares at the start of the game.
* **Game End Condition:**
    * A maximum game turn length can be configured (e.g., 80 turns).

**2. Player Turn Sequence**

Each player's turn follows a strict sequence:

1.  **Place Tile:** The player *must* place one "Loose Tile" (Diamond) onto an empty square on the board. This action triggers subsequent events (forming, expanding, merging).
2.  **(Optional) Buy Stock:** After the consequences of placing the tile are resolved, the player *may* buy stock in any *active* companies.
3.  **End Turn:** The player concludes their turn.

**3. Tile Placement Mechanics**

Placing a tile on an empty square `(r, c)` triggers different events based on its adjacent squares:

* **Check Legality:** A tile placement is illegal if it would simultaneously connect two or more *safe* companies.
* **Placement Action:** The selected empty square at `(r, c)` temporarily becomes a "Loose Tile".
* **Evaluate Neighbors:** Determine adjacent entities (other Loose Tiles, Active Companies).
    * **Case 1: No Adjacent Active Companies:**
        * **If no adjacent Loose Tiles:** The placed tile remains a Loose Tile. Player proceeds to Buy Stock phase.
        * **If adjacent to Loose Tiles:** A new company is potentially formed.
            * Calculate the connected area of all adjacent Loose Tiles plus the newly placed one.
            * If the total size is 2 or more:
                * Check if any inactive companies are available to be founded.
                * If yes: An inactive company (typically the one with the lowest available ID) is chosen. All connected Loose Tiles in the area are converted to this company's ID. The company becomes active, its size and stock price are updated. The founding player receives a founder bonus (e.g., 1 free share, if available). Player proceeds to Buy Stock phase.
                * If no: The placed tile remains a Loose Tile. Player proceeds to Buy Stock phase.
    * **Case 2: Adjacent to ONE Active Company:**
        * The placed tile, and any Loose Tiles connected to it, are absorbed into the adjacent active company.
        * The company's size and stock price are recalculated.
        * Check for share splits if the price tier triggers it.
        * Check if this expansion triggers secondary mergers (see Mergers).
        * Player proceeds to Buy Stock phase.
    * **Case 3: Adjacent to TWO or MORE Active Companies:**
        * A Merger is triggered. The placed tile and any connected Loose Tiles are temporarily removed/marked.
        * Proceed to Merger Resolution (Section 5). *Note: The player does NOT proceed to Buy Stock until the merger is fully resolved.*

* **Post-Placement Diamond Expansion:** After a tile placement resolves *without* triggering a merger (Cases 1 & 2), check all remaining Loose Tiles on the board. If any Loose Tile is now adjacent to exactly *one* active company, it (and any diamonds connected to it) are automatically absorbed into that company, updating its size/price. If a diamond becomes adjacent to two or more companies due to this expansion, it triggers a *secondary* merger.

**4. Stock Market Mechanics**

* **Buying Stock:**
    * Occurs after the Place Tile phase is fully resolved (including any resulting company formations or single-company expansions).
    * Player can buy stock only in *active* companies.
    * The cost is determined by the company's current stock price.
    * The purchase is limited by:
        * Player's available cash.
        * Shares available in the company's pool (e.g., max 25 initially).
        * (Optional/Not explicit in current logic, but standard): A maximum number of shares (total across all companies) buyable per turn (e.g., 3).
* **Selling Stock:**
    * Occurs via a dedicated "Manage Shares" action (can be invoked anytime during the player's turn, *except* potentially during merger resolution).
    * Player can sell any number of shares they own in any company.
    * The selling price is the company's *current* stock price.
    * Sold shares return to the company's available pool.
* **Share Splits:** If a company's growth causes its stock price to reach a certain threshold (e.g., £3200), a share split occurs *immediately*:
    * The company's stock price is halved.
    * Every player holding shares in that company has their share count doubled.

**5. Merger Resolution**

Triggered when a placed tile connects two or more previously separate active companies.

* **Identify Participants:** Determine all active companies involved in the merge.
* **Determine Acquirer:**
    * The largest company (by tile size) among the participants becomes the acquirer.
    * **Tie-Breaking:** If two or more companies are tied for the largest size, a tie-breaking rule is needed (e.g., the company with the lower ID becomes the acquirer). *User choice could be implemented here.*
* **Identify Acquired/Survivors:**
    * All participating companies *not* chosen as the acquirer are potentially acquired.
    * However, if a non-acquiring company is *safe* (size >= safe threshold), it is *not* acquired and survives the merger independently.
* **Voided Merger:** If all potential targets are safe, the merger is voided. The initially placed tile (and any connected diamonds) are absorbed by the designated (largest) "acquirer", size/price updated. The turn proceeds to Buy Stock phase.
* **Valid Merger - Bonuses:**
    * For each company being acquired (non-safe targets):
        * Calculate Majority and Minority shareholder bonuses based on the stock price *at the moment the merger was triggered*.
        * Majority Bonus: Awarded to the player(s) holding the most shares.
        * Minority Bonus: Awarded to the player(s) holding the second-most shares.
        * **Tie-Breaking (Bonuses):** If multiple players tie for 1st place, the sum of Majority and Minority bonuses is split evenly among them (rounded up). No Minority bonus is paid. If there's a tie for 2nd place, the Minority bonus is split evenly among them (rounded up).
        * Bonuses are paid immediately from the bank to the players' cash.
* **Merger - Share Disposal (Simplified/Current Logic):**
    * *(Current logic auto-finalizes here. A full implementation would involve player choices)*
    * *(Blueprint for player choice phase):*
        * Iterate through each acquired company one by one.
        * For each acquired company, iterate through each player (in turn order, starting from the player *after* the merger triggerer).
        * If a player holds shares in the current acquired company, they choose one action for *all* their shares:
            * **Sell:** Sell all shares at the stock price the company had *at the moment the merger was triggered*. Cash added to player, shares return to company pool.
            * **Trade:** Trade shares for shares in the *acquiring* company at a 2:1 ratio (2 acquired shares for 1 acquirer share). Requires enough shares available in the acquirer's pool. Traded shares return to the acquired company pool.
            * **Keep:** Hold onto the now-defunct shares (potentially worthless unless rules allow defunct companies to reform).
* **Merger - Finalize:**
    * All tiles belonging to the acquired companies, plus the initially placed tile (and any connected diamonds), are converted to the acquirer's company ID.
    * The acquired companies become *inactive*. Their ID becomes available for founding again. Their shares remain in player hands (if kept) or in the pool.
    * The acquiring company's size and stock price are recalculated based on the new total area. Share splits are checked.
    * Check for secondary mergers caused by the acquirer's new footprint.
    * The turn proceeds to the Buy Stock phase for the player who *triggered* the merger.

**6. Game End and Scoring**

* **End Conditions:** The game ends *immediately* if any of the following occur (typically checked after tile placement and potentially after end of turn):
    * A company reaches a maximum size threshold (e.g., 41 tiles).
    * All active companies on the board become safe.
    * The pre-defined game turn limit is reached.
* **Final Scoring:**
    * **Liquidate Stocks:** All shares held by players in *active* companies are valued at the company's final stock price.
    * **Final Bonuses:** Calculate and pay final Majority/Minority bonuses for all *active* companies based on final shareholdings and final stock prices.
    * **Calculate Total Wealth:** Each player's final score is their final cash + total value of their liquidated stock + total final bonuses received.
    * **Determine Winner:** The player with the highest total wealth wins. Ties are possible.

**7. AI Player Integration (Conceptual)**

* If AI players are included, they follow the same turn structure.
* Instead of waiting for UI input, the game triggers the AI's decision logic for each phase (tile placement, stock purchase, merger disposal).
* AI decision logic can vary in complexity (difficulty levels):
    * **Easy:** Random valid moves.
    * **Medium:** Simple heuristics (e.g., expand largest own company, buy stock in growing companies).
    * **Hard:** More complex evaluation (e.g., predicting merger outcomes, strategic blocking, portfolio optimization).
