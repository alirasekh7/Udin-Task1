# Udin-Task1
Inclusion of tasks, generated code and prompts


This repository contains Python-based game implementations developed with the assistance of an AI code generation tool. The project demonstrates the process of utilizing AI for software development, addressing specific functional requirements while following defined constraints.

## Methodology: AI Collaboration and Constraint Management

The development of each task involved a collaborative process with an AI assistant [Deepseek and Gemini Pro]. This included:

1.  **Initial Prompting:** Defining the core requirements and game mechanics for the AI.
2.  **Refinement:** Reviewing AI-generated code, identifying discrepancies or bugs, and providing feedback or more specific instructions to guide the AI towards the desired solution.
3.  **Constraint:** Actively steering the AI to produce solutions compatible with a single-file Python/Pygame architecture, avoiding more complex setups involving external databases, networked components, or multiple language integrations that an AI might typically suggest for certain features.
4.  **Problem Solving:** When the AI's output was not immediately correct or optimal, a process of debugging and targeted prompting was employed. This often involved providing error tracebacks or clarifying aspects of the requirements.

A difficult aspect of this methodology was translating complex requirements ("multi-user platform," "geographic fairness") into simpler implementations within the AI constraint. This often meant simulating such features locally.

---

## Task 1: Sokoban Clone

### Objective
Develop a functional clone of the Sokoban puzzle game where the player pushes boxes onto target locations. Key constraints included:
* Player movement in four directions.
* Boxes can only be pushed, not pulled.
* Only one box can be pushed at a time.

### Code Explanation
The Sokoban game is implemented as a single Python class using Pygame.

The game level is defined as a list of strings, where each character represents a game element ('#'` for wall, '`p'` for player, '`b'` for box, '`t'` for target, ' ' for empty floor).
    ```python
    # Example level structure:
    # self.level = [
    #     "##########",
    #     "#p b  t  #", # Player, box, target
    #     "##########"
    # ]
    ```
 On initialization, the `parse_level` method iterates through this string array to fill lists of wall coordinates, initial box positions, target locations, and the player's starting position.
* **Player Movement and Box Pushing Logic:** The `move_player(dx, dy)` method handles player input.
    1.  It calculates the player's potential new position.
    2.  **Wall Collision:** Checks if the new position is a wall; if so, movement is blocked.
    3.  **Box Interaction:** If the new position contains a box:
        * It calculates the position the box would move to (one step further in the same direction).
        * **Box Collision:** Checks if the box's new position is a wall or another box; if so, the push is blocked.
        * If the push is valid, the box's position in the `self.boxes` list is updated.
    4.  If movement is valid (either to an empty space or after a successful box push), the player's position (`self.player_pos`) is updated.
* **Win Condition:** The `check_win` method verifies if all target locations (`self.targets`) are occupied by boxes (`self.boxes`).

### Constraints and AI Interactio
* **Asset Management:** The AI was initially prompted to use images. When this presented a `FileNotFoundError` (due to missing local image files), the AI was guided to implement a fallback mechanism that draws coloured rectangles if images cannot be loaded. This ensured the game was runnable without external dependencies.
* **Logic Adherence:** The AI successfully generated the core logic for movement and box pushing according to the specified constraints (push-only, one box at a time). Iteration was primarily focused on visual presentation and error handling for missing assets.

---

## Task 2: Multi-User Sokoban Enhancement

### Objective
Extend the Sokoban game from Task 1 to include:
* User registration and login.
* Storage of user scores and a leaderboard.
* Three user roles: anonymous, player, and admin.
* Admin capability to create new levels.

### Code Explanation
This task significantly expanded the Sokoban game, introducing UI states and data persistence, all within the single-file constraint.


    * Given the single-file constraint, traditional databases were not used. Instead, user data (`users.json`), level definitions (`levels.json`), and scores (`scores.json`) are stored locally in JSON files.
    * Helper functions (`load_data`, `save_data`) manage reading from and writing to these files.
    * Passwords in `users.json` are stored as plain text in this version for simplicity; in a production scenario, hashing would be essential.
* **UI State Management:**
    * The `SokobanGame` class manages different game states (`self.current_state`): "login", "menu", "game", "level_editor", "level_selection", "leaderboard_display".
    * Each state has a corresponding `setup_..._ui()` method that configures on-screen buttons (`self.buttons`) and text input fields (`self.text_inputs`).
    * Drawing functions (`draw_login()`, `draw_menu()`, etc.) render the UI for the active state.
* **User Authentication & Roles:**
    * `register_user()` and `login_user()` handle user creation and sign-in, interacting with `users.json`.
    * The `self.user_role` attribute determines access to features like the level editor (admin-only).
* **Level Editor (Admin):**
    * The `level_editor` state provides a grid where admins can place game elements (wall, box, target, player) using mouse clicks and keyboard shortcuts to select tools.
    * The `self.editor_level_chars` (a 2D list of characters) stores the design in progress.
    * The "Save Level" functionality (`action == "save_level"`) processes `self.editor_level_chars`:
        1.  It trims empty rows/columns around the designed content to create a compact level.
        2.  Validates that the level contains essential elements (player, at least one box, at least one target).
        3.  Saves the new level (as a list of strings) to `levels.json` with a unique ID, name, creator, and date.
* **Scoring and Leaderboard:**
    * When a logged-in player completes a level, `add_score()` records their username, moves, and timestamp in `scores.json` for that level. Scores are sorted by moves.
    * The leaderboard UI (`draw_leaderboard_display()`) fetches and displays scores for a selected level.

### Constraints and AI Interaction
* **Single File & No Database:** This was the primary constraint. The AI was guided to use JSON files for data storage. This involved prompting for functions to load and save dictionaries to/from JSON.
* **UI Complexity:** Managing multiple UI screens and interactive elements (buttons, text fields) within a single Pygame loop required careful state management. The AI assisted in structuring the different `draw_...()` and `setup_..._ui()` methods.


---

## Task 3: Multi-Player Tap Frenzy Game

### Objective
Create a local multi-player game where players compete by tapping assigned keyboard keys within a 15-second time limit. The game should accurately represent the start time and be fair to all players (within a local context).

### Code Explanation
This game focuses on real-time input handling and synchronized timing for multiple local players.

* **Game States:** The game progresses through "setup", "countdown", "playing", and "results" states.
* **Player Setup (`setup` state):**
    * Allows configuration of the number of players (up to a defined maximum, e.g., 4).
    * Players can input their names.
    * Each active player is automatically assigned a unique key from a predefined list (e.g., `PLAYER_KEYS = [pygame.K_a, pygame.K_l, ...]`).
* **Synchronized Start (`countdown` state):**
    * A visual on-screen countdown ("3...", "2...", "1...", "GO!") is displayed.
    * `pygame.time.get_ticks()` is used to manage the timing of the countdown and the subsequent game duration precisely. The `self.start_ticks` variable is reset at the beginning of each timed phase.
* **Gameplay (`playing` state):**
    * A 15-second timer (`GAME_DURATION_SECONDS`) is displayed and counts down.
    * The game listens for `KEYDOWN` events. If an event's key matches one of the assigned `PLAYER_KEYS`, the corresponding player's score in `self.player_scores` is incremented.
    * Input is only processed during this 15-second window.
* **Results (`results` state):**
    * Displays "Time's Up!".
    * Calculates and shows the final scores for all participating players.
    * Determines and announces the winner(s) (handles ties).
    * Provides options to "Play Again" (retaining current player setup) or start a "New Game" (back to the setup screen).

### Constraints and AI Interaction
* **"Geographic Fairness" Interpretation:** The requirement for fairness across different geographic locations was interpreted in the context of a local game. The AI was guided to implement this by ensuring a perfectly synchronized start time for all players using the local machine's clock and Pygame's timing. The game includes an on-screen note clarifying this local interpretation.
* **AI's Role in Structure:** The AI was effective in generating the initial state machine structure, the Pygame event loop, and basic UI rendering for text and buttons.
* **UI Flow and Player Configuration:** The AI assisted in creating the setup screen where player names could be entered and the number of players adjusted, along with the logic for handling button clicks to navigate between game states.

---

This project demonstrates that while AI can significantly accelerate aspects of game development, human oversight is crucial for managing constraints, refining logic, debugging, and ensuring the final product aligns with nuanced requirements.
