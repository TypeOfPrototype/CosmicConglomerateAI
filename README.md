# Cosmic Conglomerate

Cosmic Conglomerate is a digital board game for 2-4 players, built with Python and Kivy. It is inspired by the classic board game Acquire, where players strategically invest in companies, expand them, and trigger mergers to increase their wealth. This project is based on an original 'Space Monopoly Game Mechanics Blueprint'.

## Core Features

*   **Game Setup & Configuration:**
    *   Supports 2 to 4 players, configurable as Human (with profiles) or AI (Easy difficulty).
    *   Selectable grid sizes (e.g., 16x12, 22x18, 28x24).
    *   Configurable game turn limit (defaults to 80 turns).
    *   Initial board setup includes special "O" marker tiles, placed based on a configurable percentage. These markers can provide bonuses when companies are formed or expanded near them.
*   **Gameplay Mechanics:**
    *   **Tile Placement:** Players place tiles on the board. Depending on adjacent tiles, this can:
        *   Form a new company if adjacent to other unowned tiles or "O" markers.
        *   Expand an existing company if adjacent to it. The player who places the tile becomes the owner of the new/expanded company tile.
        *   Trigger a merger if the placed tile connects two or more existing companies.
        *   Place a "Diamond" if no company is formed or expanded. Diamonds are neutral tiles that can be absorbed by companies later.
    *   **Stock Market:** Players can buy and sell shares of active companies during their turn. Share prices are influenced by company size and "O" marker proximity. Share splits can occur if a company's value reaches a certain threshold.
    *   **Company Mergers:** When companies merge, the larger company acquires the smaller one(s). Shares in acquired companies are typically converted to shares in the acquiring company or paid out (specifics are detailed in the `GAME_RULES.md`).
*   **AI Players:** AI opponents are available ("Easy" difficulty), making random valid moves.
*   **User Interface:**
    *   Interactive game board display showing companies, tiles, and player assets.
    *   Sidebar for player information (cash, stock holdings, current player).
    *   Controls for placing tiles and managing shares.

## Getting Started

### Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd cosmic-conglomerate # Or your project directory name
   ```
2. Install Kivy and other dependencies manually. (A `requirements.txt` file is not yet available.)
   (Ensure you have Python installed. See [Kivy installation guide](https://kivy.org/doc/stable/gettingstarted/installation.html) for Kivy setup.)

### How to Run

```bash
python main.py
```

### How to Run Tests

The project includes a `tests/` directory. To run the tests:

```bash
python -m unittest discover tests
```

## Project Structure

*   `main.py`: Entry point for the Kivy application.
*   `start_screen.py`: UI and logic for the game setup screen.
*   `game_screen.py`: UI and logic for the main game board and interactions.
*   `game_logic.py`: Core game state management, rules enforcement, and AI logic.
*   `profile_manager.py`: Handles creation, loading, and saving of player profiles.
*   `custom_widgets.py`: Contains custom Kivy widgets used in the UI.
*   `assets/`: Contains images and fonts.
    *   `assets/images/`: Game logos, tile images, etc.
    *   `assets/fonts/`: Custom fonts used in the game.
*   `tests/`: Unit tests for the game logic and other components.
*   `GAME_RULES.md`: Detailed rules and mechanics of the game.
*   `README.md`: This file.
*   `LICENSE`: Project license information.

## Basic Controls

Gameplay primarily involves:
*   **Clicking on highlighted squares** on the game board to place tiles. This can lead to forming new companies, expanding existing ones, or placing diamonds.
*   Using the **Share Management** popup to buy and sell shares in active companies.
*   Clicking **End Turn** to pass play to the next player.
*   Navigating menus on the **Start Screen** to configure players, grid size, and other game settings.

## Visual Theme

The game aims for a futuristic, space-themed aesthetic with a clean and modern user interface. Key elements include:
*   A dark blue primary color palette evoking deep space, with light gray and teal for accents and readability.
*   Use of sans-serif typography (Orbitron) to enhance the futuristic feel.
*   Space-themed icons and a grid-based layout consistent with the board game inspiration.

## Contributing

Contributions are welcome! If you would like to contribute to Cosmic Conglomerate, please consider the following:

*   **Reporting Bugs:** If you find a bug, please open an issue on the project's issue tracker, providing as much detail as possible.
*   **Suggesting Enhancements:** Feel free to open an issue to suggest new features or improvements.
*   **Pull Requests:** For direct code contributions:
    1.  Fork the repository.
    2.  Create a new branch for your feature or bug fix.
    3.  Make your changes, adhering to the existing code style.
    4.  Add tests for your changes if applicable.
    5.  Ensure all tests pass.
    6.  Submit a pull request with a clear description of your changes.

Please note that this project is maintained by a small team, so response times may vary.

For detailed game mechanics, please see [GAME_RULES.md](GAME_RULES.md).
