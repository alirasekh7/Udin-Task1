import pygame
import sys
import json
import os
from datetime import datetime

# Initialize pygame
pygame.init()

# Constants
TILE_SIZE = 30  # Adjusted for editor view
PLAYER_COLOR = (70, 200, 70)
WALL_COLOR = (100, 60, 20)
BOX_COLOR = (200, 120, 50)
TARGET_COLOR = (255, 215, 0)
FLOOR_COLOR = (240, 240, 240)
TEXT_COLOR = (0, 0, 0)
TARGET_BOX_COLOR = (150, 200, 150)  # Box on target color
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER_COLOR = (150, 150, 250)
TEXT_INPUT_COLOR = (255, 255, 255)
TEXT_INPUT_ACTIVE_COLOR = (220, 220, 255)
EDITOR_GRID_COLOR = (200, 200, 200)
MESSAGE_COLOR = (200, 0, 0)  # For error messages

# User roles
ANONYMOUS = 0
PLAYER = 1
ADMIN = 2

# Editor constants
EDITOR_GRID_ROWS = 15
EDITOR_GRID_COLS = 20
EDITOR_OFFSET_X = 50
EDITOR_OFFSET_Y = 150


# Game setup
class SokobanGame:
    def __init__(self):
        self.current_user = None
        self.user_role = ANONYMOUS
        self.users = self.load_users()
        self.levels = self.load_levels()
        self.scores = self.load_scores()

        # Level editor properties
        self.editor_tool = 1  # 1: wall, 2: box, 3: target, 4: player, 0: erase
        self.editor_level_chars = [[' ' for _ in range(EDITOR_GRID_COLS)] for _ in range(EDITOR_GRID_ROWS)]
        self.editor_player_pos_rc = None  # Store as (row, col) for the char grid

        # UI setup
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Multi-User Sokoban")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        self.message_font = pygame.font.SysFont(None, 28)
        self.ui_message = ""  # For displaying messages/errors on screen
        self.ui_message_timer = 0

        # Game state
        self.current_state = "login"  # login, menu, game, level_editor, level_selection, leaderboard
        self.current_level_id_playing = None  # ID of the level being played or viewed in leaderboard
        self.game_instance = None  # Instance of SokobanLevel

        # UI elements
        self.text_inputs = {}
        self.active_input = None
        self.buttons = []

        self.setup_login_ui()

    def set_ui_message(self, msg, duration=180):  # duration in frames (3 seconds at 60fps)
        self.ui_message = msg
        self.ui_message_timer = duration

    def load_users(self):
        try:
            with open('users.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"admin": {"password": "admin123", "role": ADMIN}}

    def save_users(self):
        with open('users.json', 'w') as f:
            json.dump(self.users, f, indent=4)

    def load_levels(self):
        try:
            with open('levels.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "0": {
                    "name": "Default Level",
                    "data": [
                        "#####",
                        "#pbt#",
                        "#####"
                    ],
                    "created_by": "system",
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
            }

    def save_levels(self):
        with open('levels.json', 'w') as f:
            json.dump(self.levels, f, indent=4)

    def load_scores(self):
        try:
            with open('scores.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_scores(self):
        with open('scores.json', 'w') as f:
            json.dump(self.scores, f, indent=4)

    def register_user(self, username, password):
        if not username or not password:
            return False, "Username and password cannot be empty."
        if username in self.users:
            return False, "Username already exists."
        if len(username) < 3:
            return False, "Username too short (min 3 chars)."
        if len(password) < 4:
            return False, "Password too short (min 4 chars)."

        self.users[username] = {"password": password, "role": PLAYER}  # Passwords should be hashed in a real app
        self.save_users()
        return True, "Registration successful. Please login."

    def login_user(self, username, password):
        if username not in self.users:
            return False, "User not found."
        # Passwords should be hashed and verified, not stored plain
        if self.users[username]["password"] != password:
            return False, "Incorrect password."

        self.current_user = username
        self.user_role = self.users[username]["role"]
        return True, f"Login successful. Welcome, {username}!"

    def add_score(self, level_id, moves):
        if self.current_user is None:  # Guests don't save scores
            return

        level_id_str = str(level_id)
        if level_id_str not in self.scores:
            self.scores[level_id_str] = []

        # Check if user already has a score for this level, update if new one is better
        existing_score_idx = -1
        for i, score_entry in enumerate(self.scores[level_id_str]):
            if score_entry["username"] == self.current_user:
                existing_score_idx = i
                break

        if existing_score_idx != -1:
            if moves < self.scores[level_id_str][existing_score_idx]["moves"]:
                self.scores[level_id_str][existing_score_idx]["moves"] = moves
                self.scores[level_id_str][existing_score_idx]["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            else:
                return  # Not a better score
        else:
            self.scores[level_id_str].append({
                "username": self.current_user,
                "moves": moves,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        self.scores[level_id_str].sort(key=lambda x: x["moves"])
        self.save_scores()
        self.set_ui_message(f"Score of {moves} saved for this level!", 120)

    def setup_login_ui(self):
        self.active_input = None
        self.text_inputs = {
            "username": {"rect": pygame.Rect(self.screen_width // 2 - 100, 200, 200, 40), "text": "", "active": False,
                         "label": "Username:"},
            "password": {"rect": pygame.Rect(self.screen_width // 2 - 100, 270, 200, 40), "text": "", "active": False,
                         "password": True, "label": "Password:"}
        }
        self.buttons = [
            {"rect": pygame.Rect(self.screen_width // 2 - 100, 330, 200, 40), "text": "Login", "action": "login"},
            {"rect": pygame.Rect(self.screen_width // 2 - 100, 380, 200, 40), "text": "Register", "action": "register"},
            {"rect": pygame.Rect(self.screen_width // 2 - 100, 430, 200, 40), "text": "Play as Guest",
             "action": "guest"}
        ]

    def setup_menu_ui(self):
        self.active_input = None
        self.text_inputs = {}  # No text inputs on the menu
        self.buttons = [
            {"rect": pygame.Rect(self.screen_width // 2 - 100, 200, 200, 40), "text": "Play Game",
             "action": "level_selection"},
            {"rect": pygame.Rect(self.screen_width // 2 - 100, 260, 200, 40), "text": "Leaderboard",
             "action": "leaderboard_entry"},
            {"rect": pygame.Rect(self.screen_width // 2 - 100, 380, 200, 40), "text": "Logout", "action": "logout"}
        ]
        if self.user_role == ADMIN:
            self.buttons.insert(2, {"rect": pygame.Rect(self.screen_width // 2 - 100, 320, 200, 40),
                                    "text": "Level Editor", "action": "level_editor"})

    def setup_level_selection_ui(self, page=0):  # Added pagination for many levels
        self.active_input = None
        self.text_inputs = {}
        self.buttons = [
            {"rect": pygame.Rect(50, self.screen_height - 70, 150, 40), "text": "Back to Menu", "action": "menu"}]

        y_pos = 100
        levels_per_page = 7
        sorted_level_ids = sorted(self.levels.keys(), key=lambda x: int(x) if x.isdigit() else float('inf'))

        start_index = page * levels_per_page
        end_index = start_index + levels_per_page

        for i, level_id in enumerate(sorted_level_ids[start_index:end_index]):
            level_data = self.levels[level_id]
            self.buttons.append({
                "rect": pygame.Rect(self.screen_width // 2 - 150, y_pos + i * 50, 300, 40),
                "text": f"{level_data['name']} (by {level_data.get('created_by', 'Unknown')})",
                "action": f"play_level_{level_id}"
            })

        # Pagination buttons
        if page > 0:
            self.buttons.append(
                {"rect": pygame.Rect(self.screen_width // 2 - 60, self.screen_height - 70, 50, 40), "text": "<",
                 "action": f"prev_page_{page - 1}"})
        if end_index < len(sorted_level_ids):
            self.buttons.append(
                {"rect": pygame.Rect(self.screen_width // 2 + 10, self.screen_height - 70, 50, 40), "text": ">",
                 "action": f"next_page_{page + 1}"})

    def setup_leaderboard_display_ui(self, level_id_to_show):  # Specific level
        self.active_input = None
        self.text_inputs = {}
        self.current_level_id_playing = level_id_to_show  # Store which leaderboard we are viewing
        self.buttons = [
            {"rect": pygame.Rect(50, self.screen_height - 70, 200, 40), "text": "Back to Level Select",
             "action": "leaderboard_back_to_level_select"}  # Or back to menu
        ]
        if self.current_state != "game_over_leaderboard":  # if not coming from game over screen
            self.buttons[0]["text"] = "Back to Menu"
            self.buttons[0]["action"] = "menu"

    def setup_level_editor_ui(self):
        self.active_input = None
        self.editor_level_chars = [[' ' for _ in range(EDITOR_GRID_COLS)] for _ in
                                   range(EDITOR_GRID_ROWS)]  # Reset grid
        self.editor_player_pos_rc = None
        self.text_inputs = {
            "level_name": {
                "rect": pygame.Rect(EDITOR_OFFSET_X + EDITOR_GRID_COLS * TILE_SIZE + 20, EDITOR_OFFSET_Y, 200, 40),
                "text": "", "active": False, "label": "Level Name:"}
        }
        self.buttons = [
            {"rect": pygame.Rect(EDITOR_OFFSET_X + EDITOR_GRID_COLS * TILE_SIZE + 20, EDITOR_OFFSET_Y + 50, 200, 40),
             "text": "Save Level", "action": "save_level"},
            {"rect": pygame.Rect(EDITOR_OFFSET_X + EDITOR_GRID_COLS * TILE_SIZE + 20, EDITOR_OFFSET_Y + 100, 200, 40),
             "text": "Back to Menu", "action": "menu"},
            # Tool buttons
            {"rect": pygame.Rect(EDITOR_OFFSET_X, EDITOR_OFFSET_Y - 40, 80, 30), "text": "Wall (1)",
             "action": "tool_1"},
            {"rect": pygame.Rect(EDITOR_OFFSET_X + 90, EDITOR_OFFSET_Y - 40, 80, 30), "text": "Box (2)",
             "action": "tool_2"},
            {"rect": pygame.Rect(EDITOR_OFFSET_X + 180, EDITOR_OFFSET_Y - 40, 90, 30), "text": "Target (3)",
             "action": "tool_3"},
            {"rect": pygame.Rect(EDITOR_OFFSET_X + 280, EDITOR_OFFSET_Y - 40, 90, 30), "text": "Player (4)",
             "action": "tool_4"},
            {"rect": pygame.Rect(EDITOR_OFFSET_X + 380, EDITOR_OFFSET_Y - 40, 90, 30), "text": "Erase (0)",
             "action": "tool_0"},
        ]

    def draw_text_inputs(self):
        for name, input_data in self.text_inputs.items():
            # Draw label
            if "label" in input_data:
                label_surface = self.small_font.render(input_data["label"], True, TEXT_COLOR)
                self.screen.blit(label_surface, (input_data["rect"].x, input_data["rect"].y - 20))

            color = TEXT_INPUT_ACTIVE_COLOR if input_data.get("active", False) else TEXT_INPUT_COLOR
            pygame.draw.rect(self.screen, color, input_data["rect"])
            pygame.draw.rect(self.screen, (0, 0, 0), input_data["rect"], 2)

            display_text = input_data["text"]
            if input_data.get("password", False):
                display_text = "*" * len(display_text)

            text_surface = self.font.render(display_text, True, (0, 0, 0))
            # Adjust text blit position for padding
            self.screen.blit(text_surface, (input_data["rect"].x + 5, input_data["rect"].y + (
                        input_data["rect"].height - text_surface.get_height()) // 2))

    def draw_buttons(self):
        for button in self.buttons:
            mouse_pos = pygame.mouse.get_pos()
            color = BUTTON_HOVER_COLOR if button["rect"].collidepoint(mouse_pos) else BUTTON_COLOR

            # Highlight active tool button
            if self.current_state == "level_editor" and "tool_" in button["action"]:
                tool_id = int(button["action"].split("_")[1])
                if tool_id == self.editor_tool:
                    color = BUTTON_HOVER_COLOR  # Keep it highlighted

            pygame.draw.rect(self.screen, color, button["rect"])
            pygame.draw.rect(self.screen, (0, 0, 0), button["rect"], 2)  # Border

            text_surface = self.small_font.render(button["text"], True, (0, 0, 0))  # Use small_font for buttons
            text_rect = text_surface.get_rect(center=button["rect"].center)
            self.screen.blit(text_surface, text_rect)

    def draw_ui_message(self):
        if self.ui_message and self.ui_message_timer > 0:
            message_surface = self.message_font.render(self.ui_message, True, MESSAGE_COLOR,
                                                       FLOOR_COLOR)  # Added background
            message_rect = message_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
            self.screen.blit(message_surface, message_rect)
            self.ui_message_timer -= 1
        elif self.ui_message_timer <= 0:
            self.ui_message = ""

    def draw_login(self):
        self.screen.fill(FLOOR_COLOR)
        title = self.font.render("Sokoban Game", True, TEXT_COLOR)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 100))
        self.draw_text_inputs()
        self.draw_buttons()
        self.draw_ui_message()

    def draw_menu(self):
        self.screen.fill(FLOOR_COLOR)
        welcome_msg = f"Welcome, {self.current_user}!" if self.current_user else "Welcome, Guest!"
        if self.current_user and self.user_role == ADMIN:
            welcome_msg += " (Admin)"

        welcome_text_surface = self.font.render(welcome_msg, True, TEXT_COLOR)
        self.screen.blit(welcome_text_surface, (self.screen_width // 2 - welcome_text_surface.get_width() // 2, 100))
        self.draw_buttons()
        self.draw_ui_message()

    def draw_level_selection(self):
        self.screen.fill(FLOOR_COLOR)
        title = self.font.render("Select a Level", True, TEXT_COLOR)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 50))
        self.draw_buttons()
        self.draw_ui_message()

    def draw_leaderboard_display(self):  # Renamed from draw_leaderboard
        self.screen.fill(FLOOR_COLOR)
        title_text = "Leaderboard"
        if self.current_level_id_playing is not None and str(self.current_level_id_playing) in self.levels:
            level_name = self.levels[str(self.current_level_id_playing)]["name"]
            title_text = f"Leaderboard: {level_name}"

        title_surface = self.font.render(title_text, True, TEXT_COLOR)
        self.screen.blit(title_surface, (self.screen_width // 2 - title_surface.get_width() // 2, 30))

        level_id_str = str(self.current_level_id_playing)
        if level_id_str not in self.scores or not self.scores[level_id_str]:
            no_scores_surface = self.font.render("No scores yet for this level.", True, TEXT_COLOR)
            self.screen.blit(no_scores_surface, (self.screen_width // 2 - no_scores_surface.get_width() // 2, 200))
        else:
            headers = ["Rank", "Username", "Moves", "Date"]
            col_widths = [80, 200, 100, 200]
            start_x = (self.screen_width - sum(col_widths)) // 2

            for i, header in enumerate(headers):
                header_surface = self.small_font.render(header, True, TEXT_COLOR)
                self.screen.blit(header_surface, (start_x + sum(col_widths[:i]) + 10, 80))

            for i, score_entry in enumerate(self.scores[level_id_str][:15]):  # Show top 15
                texts_to_render = [
                    str(i + 1),
                    score_entry["username"],
                    str(score_entry["moves"]),
                    score_entry["date"]
                ]
                for col_idx, text_val in enumerate(texts_to_render):
                    score_surface = self.small_font.render(text_val, True, TEXT_COLOR)
                    self.screen.blit(score_surface, (start_x + sum(col_widths[:col_idx]) + 10, 110 + i * 25))
        self.draw_buttons()
        self.draw_ui_message()

    def draw_level_editor(self):
        self.screen.fill(FLOOR_COLOR)
        title = self.font.render("Level Editor", True, TEXT_COLOR)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 20))

        instructions_y = 50
        instructions = [
            "Click to place, Right-click to erase tile.",
            "Use number keys (0-4) or buttons for tools.",
            "0:Erase, 1:Wall, 2:Box, 3:Target, 4:Player (one only)"
        ]
        for i, inst in enumerate(instructions):
            inst_surface = self.small_font.render(inst, True, TEXT_COLOR)
            self.screen.blit(inst_surface,
                             (self.screen_width // 2 - inst_surface.get_width() // 2, instructions_y + i * 20))

        tool_names = {0: "Erase", 1: "Wall", 2: "Box", 3: "Target", 4: "Player"}
        current_tool_text = self.small_font.render(f"Active Tool: {tool_names[self.editor_tool]}", True, PLAYER_COLOR)
        self.screen.blit(current_tool_text, (EDITOR_OFFSET_X, EDITOR_OFFSET_Y - 70))

        for r in range(EDITOR_GRID_ROWS):
            for c in range(EDITOR_GRID_COLS):
                rect = pygame.Rect(EDITOR_OFFSET_X + c * TILE_SIZE, EDITOR_OFFSET_Y + r * TILE_SIZE, TILE_SIZE,
                                   TILE_SIZE)
                pygame.draw.rect(self.screen, EDITOR_GRID_COLOR, rect, 1)  # Grid line

                char = self.editor_level_chars[r][c]
                char_rect = rect.inflate(-2, -2)  # Slightly smaller rect for drawing char
                if char == '#':
                    pygame.draw.rect(self.screen, WALL_COLOR, char_rect)
                elif char == 'b':
                    pygame.draw.rect(self.screen, BOX_COLOR, char_rect)
                elif char == 't':
                    pygame.draw.rect(self.screen, TARGET_COLOR, char_rect)  # Solid target for editor
                elif char == 'p':
                    pygame.draw.rect(self.screen, PLAYER_COLOR, char_rect)

        self.draw_text_inputs()  # For level name
        self.draw_buttons()  # For save, back, tools
        self.draw_ui_message()

    def handle_editor_click(self, pos, button):
        grid_c = (pos[0] - EDITOR_OFFSET_X) // TILE_SIZE
        grid_r = (pos[1] - EDITOR_OFFSET_Y) // TILE_SIZE

        if 0 <= grid_r < EDITOR_GRID_ROWS and 0 <= grid_c < EDITOR_GRID_COLS:
            tool_char = ' '  # Default for erase or unknown tool
            if button == 1:  # Left click - place tool
                if self.editor_tool == 0:
                    tool_char = ' '  # Erase
                elif self.editor_tool == 1:
                    tool_char = '#'  # Wall
                elif self.editor_tool == 2:
                    tool_char = 'b'  # Box
                elif self.editor_tool == 3:
                    tool_char = 't'  # Target
                elif self.editor_tool == 4:
                    tool_char = 'p'  # Player
            elif button == 3:  # Right click - always erase
                tool_char = ' '

            # If placing player, remove old player first
            if tool_char == 'p':
                if self.editor_player_pos_rc:
                    old_r, old_c = self.editor_player_pos_rc
                    self.editor_level_chars[old_r][old_c] = ' '
                self.editor_player_pos_rc = (grid_r, grid_c)
            # If erasing the current player position
            elif tool_char == ' ' and self.editor_player_pos_rc == (grid_r, grid_c):
                self.editor_player_pos_rc = None

            # If trying to place something where player is (and it's not player tool)
            # or placing player where player is (redundant but ok)
            if self.editor_player_pos_rc == (grid_r, grid_c) and tool_char != 'p':
                self.editor_player_pos_rc = None  # Remove player if overwriting its spot with non-player

            self.editor_level_chars[grid_r][grid_c] = tool_char

    def handle_button_click(self, pos):
        for button_data in self.buttons:
            if button_data["rect"].collidepoint(pos):
                return button_data["action"]
        return None

    def handle_text_input_click(self, pos):
        clicked_input_name = None
        for name, input_data in self.text_inputs.items():
            if input_data["rect"].collidepoint(pos):
                clicked_input_name = name
                input_data["active"] = True
            else:
                input_data["active"] = False
        self.active_input = clicked_input_name  # Update active_input based on click
        return clicked_input_name

    def run(self):
        running = True
        while running:
            mouse_clicked_this_frame = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_clicked_this_frame = True  # Track click for this frame
                    action = self.handle_button_click(event.pos)
                    if action:
                        # Handle tool selection buttons in editor
                        if action.startswith("tool_"):
                            self.editor_tool = int(action.split("_")[1])
                        elif action == "login":
                            if "username" in self.text_inputs and "password" in self.text_inputs:
                                success, message = self.login_user(
                                    self.text_inputs["username"]["text"],
                                    self.text_inputs["password"]["text"]
                                )
                                self.set_ui_message(message)
                                if success:
                                    self.setup_menu_ui()
                                    self.current_state = "menu"
                        elif action == "register":
                            if "username" in self.text_inputs and "password" in self.text_inputs:
                                success, message = self.register_user(
                                    self.text_inputs["username"]["text"],
                                    self.text_inputs["password"]["text"]
                                )
                                self.set_ui_message(message)
                                # Clear fields on success
                                if success:
                                    self.text_inputs["username"]["text"] = ""
                                    self.text_inputs["password"]["text"] = ""
                        elif action == "guest":
                            self.current_user = None
                            self.user_role = ANONYMOUS
                            self.set_ui_message("Playing as Guest.")
                            self.setup_menu_ui()
                            self.current_state = "menu"
                        elif action == "level_selection":
                            self.setup_level_selection_ui()
                            self.current_state = "level_selection"
                        elif action.startswith("play_level_"):
                            level_id = action.split("_")[-1]
                            self.current_level_id_playing = level_id
                            self.game_instance = SokobanLevel(self, level_id)
                            self.current_state = "game"
                        elif action == "leaderboard_entry":  # New action to go to level selection for leaderboard
                            self.set_ui_message("Select a level to view its leaderboard.")
                            self.setup_level_selection_ui()  # Show levels, then they pick one for its leaderboard
                            self.current_state = "leaderboard_level_select"  # New state
                        elif action == "leaderboard_back_to_level_select":
                            self.setup_level_selection_ui()
                            self.current_state = "level_selection"
                        elif action == "logout":
                            self.current_user = None
                            self.user_role = ANONYMOUS
                            self.set_ui_message("Logged out.")
                            self.setup_login_ui()
                            self.current_state = "login"
                        elif action == "menu":
                            self.setup_menu_ui()
                            self.current_state = "menu"
                        elif action == "level_editor":
                            self.setup_level_editor_ui()
                            self.current_state = "level_editor"
                        elif action == "save_level":
                            level_name_text = self.text_inputs.get("level_name", {}).get("text", "").strip()
                            if not level_name_text:
                                self.set_ui_message("Level name cannot be empty.", 120)
                            else:
                                # Trim and validate level
                                min_r, max_r, min_c, max_c = float('inf'), float('-inf'), float('inf'), float('-inf')
                                has_content = False
                                for r_idx, row in enumerate(self.editor_level_chars):
                                    for c_idx, char_val in enumerate(row):
                                        if char_val != ' ':
                                            has_content = True
                                            min_r = min(min_r, r_idx)
                                            max_r = max(max_r, r_idx)
                                            min_c = min(min_c, c_idx)
                                            max_c = max(max_c, c_idx)

                                if not has_content:
                                    self.set_ui_message("Cannot save an empty level design.", 120)
                                else:
                                    final_level_rows = []
                                    for r_idx in range(min_r, max_r + 1):
                                        final_level_rows.append(
                                            "".join(self.editor_level_chars[r_idx][min_c: max_c + 1]))

                                    has_player = any('p' in r_str for r_str in final_level_rows)
                                    has_box = any('b' in r_str for r_str in final_level_rows)
                                    has_target = any('t' in r_str for r_str in final_level_rows)

                                    if not (has_player and has_box and has_target):
                                        self.set_ui_message("Level needs 1 player, >=1 box, >=1 target.", 180)
                                    else:
                                        new_level_id = str(
                                            max([int(k) for k in self.levels.keys() if k.isdigit()] + [-1]) + 1)
                                        self.levels[new_level_id] = {
                                            "name": level_name_text,
                                            "data": final_level_rows,
                                            "created_by": self.current_user or "System",
                                            "date": datetime.now().strftime("%Y-%m-%d")
                                        }
                                        self.save_levels()
                                        self.set_ui_message(f"Level '{level_name_text}' saved!", 120)
                                        self.text_inputs["level_name"]["text"] = ""  # Clear name field
                        elif action.startswith("prev_page_") or action.startswith("next_page_"):
                            page = int(action.split("_")[-1])
                            self.setup_level_selection_ui(page=page)
                    else:  # No button was clicked, check for text input click
                        self.handle_text_input_click(event.pos)

                    # If in level editor and not clicking a button, handle grid click
                    if self.current_state == "level_editor" and not action:
                        # Check if click is within editor grid bounds
                        if EDITOR_OFFSET_X <= event.pos[0] < EDITOR_OFFSET_X + EDITOR_GRID_COLS * TILE_SIZE and \
                                EDITOR_OFFSET_Y <= event.pos[1] < EDITOR_OFFSET_Y + EDITOR_GRID_ROWS * TILE_SIZE:
                            self.handle_editor_click(event.pos, event.button)

                if event.type == pygame.KEYDOWN:
                    if self.active_input is not None and self.active_input in self.text_inputs:
                        if event.key == pygame.K_RETURN:
                            # Potentially trigger login/register or just deactivate
                            if self.current_state == "login" and (
                                    self.active_input == "username" or self.active_input == "password"):
                                # Simulate login button press
                                self.handle_button_click(
                                    self.buttons[0]["rect"].center)  # Assuming login is first button
                            self.text_inputs[self.active_input]["active"] = False
                            self.active_input = None
                        elif event.key == pygame.K_BACKSPACE:
                            current_text = self.text_inputs[self.active_input]["text"]
                            self.text_inputs[self.active_input]["text"] = current_text[:-1]
                        elif len(self.text_inputs[self.active_input]["text"]) < 30:  # Limit input length
                            self.text_inputs[self.active_input]["text"] += event.unicode

                    if self.current_state == "game" and self.game_instance:
                        if event.key == pygame.K_UP:
                            self.game_instance.move_player(0, -1)
                        elif event.key == pygame.K_DOWN:
                            self.game_instance.move_player(0, 1)
                        elif event.key == pygame.K_LEFT:
                            self.game_instance.move_player(-1, 0)
                        elif event.key == pygame.K_RIGHT:
                            self.game_instance.move_player(1, 0)
                        elif event.key == pygame.K_r:
                            self.game_instance = SokobanLevel(self, self.current_level_id_playing)  # Reset
                            self.set_ui_message("Level Reset.", 60)
                        elif event.key == pygame.K_ESCAPE:
                            self.set_ui_message("")  # Clear game messages
                            self.setup_level_selection_ui()  # Go back to level selection
                            self.current_state = "level_selection"
                    elif self.current_state == "level_editor":
                        if pygame.K_0 <= event.key <= pygame.K_4:
                            self.editor_tool = event.key - pygame.K_0
                        elif event.key == pygame.K_ESCAPE:
                            self.setup_menu_ui()
                            self.current_state = "menu"

                # Handle continuous drawing for level editor if mouse is held down
                if self.current_state == "level_editor" and not mouse_clicked_this_frame:  # only if not a new click
                    if pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]:  # Left or Right
                        button_pressed = 1 if pygame.mouse.get_pressed()[0] else 3
                        pos = pygame.mouse.get_pos()
                        # Check if over a button first
                        is_over_button = any(b["rect"].collidepoint(pos) for b in self.buttons)
                        if not is_over_button and \
                                EDITOR_OFFSET_X <= pos[0] < EDITOR_OFFSET_X + EDITOR_GRID_COLS * TILE_SIZE and \
                                EDITOR_OFFSET_Y <= pos[1] < EDITOR_OFFSET_Y + EDITOR_GRID_ROWS * TILE_SIZE:
                            self.handle_editor_click(pos, button_pressed)

            # Draw current state
            if self.current_state == "login":
                self.draw_login()
            elif self.current_state == "menu":
                self.draw_menu()
            elif self.current_state == "level_selection":
                self.draw_level_selection()
            elif self.current_state == "leaderboard_level_select":  # New state drawing
                self.screen.fill(FLOOR_COLOR)
                title = self.font.render("Select Level for Leaderboard", True, TEXT_COLOR)
                self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 50))
                # Re-use level selection buttons, but action will be different
                temp_buttons_for_leaderboard_select = []
                y_pos = 100
                for lvl_id, lvl_data in self.levels.items():
                    btn_rect = pygame.Rect(self.screen_width // 2 - 150, y_pos, 300, 40)
                    temp_buttons_for_leaderboard_select.append({
                        "rect": btn_rect,
                        "text": lvl_data["name"],
                        "action": f"show_leaderboard_{lvl_id}"  # Specific action
                    })
                    # Draw them immediately for this special state
                    color = BUTTON_HOVER_COLOR if btn_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
                    pygame.draw.rect(self.screen, color, btn_rect)
                    pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 2)
                    text_surf = self.small_font.render(lvl_data["name"], True, TEXT_COLOR)
                    self.screen.blit(text_surf, text_surf.get_rect(center=btn_rect.center))
                    y_pos += 50
                    if y_pos > self.screen_height - 100: break  # Limit display

                # Handle clicks for these temporary buttons
                if mouse_clicked_this_frame:
                    for btn_data in temp_buttons_for_leaderboard_select:
                        if btn_data["rect"].collidepoint(pygame.mouse.get_pos()):
                            action = btn_data["action"]
                            if action.startswith("show_leaderboard_"):
                                level_id_to_show = action.split("_")[-1]
                                self.setup_leaderboard_display_ui(level_id_to_show)
                                self.current_state = "leaderboard_display"
                                break
                # Back button for this state
                back_btn_data = {"rect": pygame.Rect(50, self.screen_height - 70, 150, 40), "text": "Back to Menu",
                                 "action": "menu"}
                color = BUTTON_HOVER_COLOR if back_btn_data["rect"].collidepoint(
                    pygame.mouse.get_pos()) else BUTTON_COLOR
                pygame.draw.rect(self.screen, color, back_btn_data["rect"])
                pygame.draw.rect(self.screen, (0, 0, 0), back_btn_data["rect"], 2)
                text_surf = self.small_font.render(back_btn_data["text"], True, TEXT_COLOR)
                self.screen.blit(text_surf, text_surf.get_rect(center=back_btn_data["rect"].center))
                if mouse_clicked_this_frame and back_btn_data["rect"].collidepoint(pygame.mouse.get_pos()):
                    self.setup_menu_ui()
                    self.current_state = "menu"

                self.draw_ui_message()

            elif self.current_state == "leaderboard_display":
                self.draw_leaderboard_display()
            elif self.current_state == "level_editor":
                self.draw_level_editor()
            elif self.current_state == "game" and self.game_instance:
                self.game_instance.draw()
                self.draw_ui_message()  # Show game-related messages like win/reset
            elif self.current_state == "game_over_leaderboard":  # After winning, show leaderboard for that level
                self.draw_leaderboard_display()  # current_level_id_playing is set by game win
                # Add a button to go back to level selection
                done_btn = {"rect": pygame.Rect(self.screen_width // 2 - 100, self.screen_height - 70, 200, 40),
                            "text": "Back to Level Select", "action": "level_selection"}
                color = BUTTON_HOVER_COLOR if done_btn["rect"].collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
                pygame.draw.rect(self.screen, color, done_btn["rect"])
                pygame.draw.rect(self.screen, (0, 0, 0), done_btn["rect"], 2)
                text_surf = self.small_font.render(done_btn["text"], True, TEXT_COLOR)
                self.screen.blit(text_surf, text_surf.get_rect(center=done_btn["rect"].center))
                if mouse_clicked_this_frame and done_btn["rect"].collidepoint(pygame.mouse.get_pos()):
                    self.setup_level_selection_ui()
                    self.current_state = "level_selection"

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


class SokobanLevel:
    def __init__(self, game_manager, level_id_str):
        self.game_manager = game_manager
        self.level_id = level_id_str  # Keep as string to match keys

        if self.level_id not in game_manager.levels:
            print(f"Error: Level ID {self.level_id} not found.")
            # Fallback or error handling
            self.game_manager.set_ui_message(f"Error: Level {self.level_id} not found.", 180)
            self.game_manager.current_state = "menu"  # Go back to menu
            self.game_manager.setup_menu_ui()
            # To prevent further errors, initialize minimally or raise exception
            self.level_data = {"name": "Error Level", "data": ["#p#"]}
            self.level = self.level_data["data"]
            self.valid_level = False
        else:
            self.level_data = game_manager.levels[self.level_id]
            self.level = self.level_data["data"]  # List of strings
            self.valid_level = True

        self.player_pos_rc = None  # (row, col)
        self.boxes_rc = []  # List of (row, col)
        self.targets_rc = []  # List of (row, col)
        self.walls_rc = []  # List of (row, col)

        if self.valid_level:
            self.parse_level()

        self.moves = 0
        self.screen = game_manager.screen
        self.font = game_manager.font
        self.small_font = game_manager.small_font  # For moves text
        self.use_images = False  # Defaulting to no images as per prior requests

        # Calculate level dimensions for drawing
        if self.level and self.level[0]:
            self.grid_rows = len(self.level)
            self.grid_cols = len(self.level[0])
        else:  # Should not happen with valid level
            self.grid_rows = 1
            self.grid_cols = 1

        self.level_pixel_width = self.grid_cols * TILE_SIZE
        self.level_pixel_height = self.grid_rows * TILE_SIZE
        self.offset_x = (self.screen.get_width() - self.level_pixel_width) // 2
        self.offset_y = (self.screen.get_height() - self.level_pixel_height) // 2
        if self.offset_y < 60: self.offset_y = 60  # Ensure space for top text

    def parse_level(self):
        self.boxes_rc = []
        self.targets_rc = []
        self.walls_rc = []
        player_found = False
        for r, row_str in enumerate(self.level):
            for c, char in enumerate(row_str):
                if char == 'p':
                    if player_found:
                        print("Warning: Multiple players in level data, using first one.")
                    else:
                        self.player_pos_rc = (r, c); player_found = True
                elif char == 'b':
                    self.boxes_rc.append((r, c))
                elif char == 't':
                    self.targets_rc.append((r, c))
                elif char == '#':
                    self.walls_rc.append((r, c))
        if not player_found:
            print(f"Error: No player 'p' in level {self.level_id}. Placing at (0,0) as fallback.")
            self.player_pos_rc = (0, 0)  # Fallback
            # Ideally, level validation should prevent this.

    def draw(self):
        if not self.valid_level: return  # Don't draw if level had loading error

        self.screen.fill(FLOOR_COLOR)

        # Draw elements relative to offset
        for r, c in self.targets_rc:
            pygame.draw.rect(self.screen, TARGET_COLOR,
                             (self.offset_x + c * TILE_SIZE, self.offset_y + r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        for r, c in self.walls_rc:
            pygame.draw.rect(self.screen, WALL_COLOR,
                             (self.offset_x + c * TILE_SIZE, self.offset_y + r * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        for r_box, c_box in self.boxes_rc:
            color = TARGET_BOX_COLOR if (r_box, c_box) in self.targets_rc else BOX_COLOR
            pygame.draw.rect(self.screen, color, (
            self.offset_x + c_box * TILE_SIZE, self.offset_y + r_box * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        if self.player_pos_rc:
            r_player, c_player = self.player_pos_rc
            pygame.draw.rect(self.screen, PLAYER_COLOR, (
            self.offset_x + c_player * TILE_SIZE, self.offset_y + r_player * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Draw level info (name, moves) at the top
        level_name_text = self.small_font.render(f"Level: {self.level_data['name']}", True, TEXT_COLOR)
        moves_text_surface = self.small_font.render(f"Moves: {self.moves}", True, TEXT_COLOR)
        self.screen.blit(level_name_text, (10, 10))
        self.screen.blit(moves_text_surface, (10, 35))

        reset_instr = self.small_font.render("R: Reset | ESC: Menu", True, TEXT_COLOR)
        self.screen.blit(reset_instr, (self.screen.get_width() - reset_instr.get_width() - 10, 10))

        if self.check_win():
            self.game_manager.set_ui_message(f"You Win! Moves: {self.moves}", 300)  # Show on game manager screen
            if self.game_manager.current_user:  # Only save if not guest
                self.game_manager.add_score(self.level_id, self.moves)

            # Transition to leaderboard view for this level
            self.game_manager.current_level_id_playing = self.level_id  # Ensure correct leaderboard
            self.game_manager.setup_leaderboard_display_ui(self.level_id)
            self.game_manager.current_state = "game_over_leaderboard"  # Special state after winning
            # The main loop will now draw the leaderboard via game_manager

    def move_player(self, dr, dc):  # delta_row, delta_col
        if not self.valid_level or self.check_win() or not self.player_pos_rc:
            return

        pr, pc = self.player_pos_rc
        next_r, next_c = pr + dr, pc + dc

        if (next_r, next_c) in self.walls_rc:
            return

        box_to_move_idx = -1
        for i, (br, bc) in enumerate(self.boxes_rc):
            if (br, bc) == (next_r, next_c):
                box_to_move_idx = i
                break

        if box_to_move_idx != -1:  # Pushing a box
            box_next_r, box_next_c = next_r + dr, next_c + dc
            if (box_next_r, box_next_c) in self.walls_rc or (box_next_r, box_next_c) in self.boxes_rc:
                return  # Box push blocked
            self.boxes_rc[box_to_move_idx] = (box_next_r, box_next_c)

        self.player_pos_rc = (next_r, next_c)
        self.moves += 1
        # self.draw() # Game manager calls draw in its loop

    def check_win(self):
        if not self.targets_rc: return False  # No targets means no win condition (or auto-win if also no boxes needed)
        if len(self.boxes_rc) < len(self.targets_rc): return False  # Not enough boxes for targets

        for tr, tc in self.targets_rc:
            if (tr, tc) not in self.boxes_rc:
                return False
        return True


# Run the game
if __name__ == "__main__":
    game = SokobanGame()
    game.run()