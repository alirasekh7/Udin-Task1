import pygame
import sys

# Initialize pygame
pygame.init()

# Constants
TILE_SIZE = 50
PLAYER_COLOR = (70, 200, 70)
WALL_COLOR = (100, 60, 20)
BOX_COLOR = (200, 120, 50)
TARGET_COLOR = (255, 215, 0)
FLOOR_COLOR = (240, 240, 240)
TEXT_COLOR = (0, 0, 0)
TARGET_BOX_COLOR = (150, 200, 150)  # Box on target color


# Game setup
class Sokoban:
    def __init__(self):
        # Larger level with multiple boxes and targets
        self.level = [
            "##########",
            "#   t    #",
            "#        #",
            "#  b  b  #",
            "#        #",
            "#   p    #",
            "#  b  t  #",
            "#        #",
            "#   t    #",
            "##########"
        ]
        self.player_pos = [4, 5]
        self.boxes = []
        self.targets = []
        self.walls = []
        self.parse_level()

        # Pygame setup
        self.screen_width = len(self.level[0]) * TILE_SIZE
        self.screen_height = len(self.level) * TILE_SIZE
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Sokoban Clone - Expanded")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)

        # Load images (or use colored rectangles if images not found)
        try:
            self.player_img = pygame.transform.scale(pygame.image.load("player.png"), (TILE_SIZE, TILE_SIZE))
            self.box_img = pygame.transform.scale(pygame.image.load("box.png"), (TILE_SIZE, TILE_SIZE))
            self.wall_img = pygame.transform.scale(pygame.image.load("wall.png"), (TILE_SIZE, TILE_SIZE))
            self.target_img = pygame.transform.scale(pygame.image.load("target.png"), (TILE_SIZE, TILE_SIZE))
            self.use_images = True
        except:
            self.use_images = False

    def parse_level(self):
        for y, row in enumerate(self.level):
            for x, char in enumerate(row):
                if char == 'p':
                    self.player_pos = [x, y]
                elif char == 'b':
                    self.boxes.append([x, y])
                elif char == 't':
                    self.targets.append([x, y])
                elif char == '#':
                    self.walls.append([x, y])

    def draw(self):
        self.screen.fill(FLOOR_COLOR)

        # Draw targets first (under boxes)
        for target in self.targets:
            if self.use_images:
                self.screen.blit(self.target_img, (target[0] * TILE_SIZE, target[1] * TILE_SIZE))
            else:
                pygame.draw.rect(self.screen, TARGET_COLOR,
                                 (target[0] * TILE_SIZE, target[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)

        # Draw walls
        for wall in self.walls:
            if self.use_images:
                self.screen.blit(self.wall_img, (wall[0] * TILE_SIZE, wall[1] * TILE_SIZE))
            else:
                pygame.draw.rect(self.screen, WALL_COLOR,
                                 (wall[0] * TILE_SIZE, wall[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Draw boxes (check if on target)
        for box in self.boxes:
            if box in self.targets:
                if self.use_images:
                    # Draw special image for box on target if available
                    self.screen.blit(self.box_img, (box[0] * TILE_SIZE, box[1] * TILE_SIZE))
                    pygame.draw.rect(self.screen, TARGET_BOX_COLOR,
                                     (box[0] * TILE_SIZE, box[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)
                else:
                    pygame.draw.rect(self.screen, TARGET_BOX_COLOR,
                                     (box[0] * TILE_SIZE, box[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            else:
                if self.use_images:
                    self.screen.blit(self.box_img, (box[0] * TILE_SIZE, box[1] * TILE_SIZE))
                else:
                    pygame.draw.rect(self.screen, BOX_COLOR,
                                     (box[0] * TILE_SIZE, box[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Draw player
        if self.use_images:
            self.screen.blit(self.player_img, (self.player_pos[0] * TILE_SIZE, self.player_pos[1] * TILE_SIZE))
        else:
            pygame.draw.rect(self.screen, PLAYER_COLOR,
                             (self.player_pos[0] * TILE_SIZE, self.player_pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Check win condition
        if self.check_win():
            win_text = self.font.render("You Win! Press R to restart", True, TEXT_COLOR)
            self.screen.blit(win_text, (self.screen_width // 2 - 150, 10))

        pygame.display.flip()

    def move_player(self, dx, dy):
        if self.check_win():  # Don't move after winning
            return

        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        # Check if new position is a wall
        if [new_x, new_y] in self.walls:
            return

        # Check if new position has a box
        if [new_x, new_y] in self.boxes:
            box_new_x = new_x + dx
            box_new_y = new_y + dy

            # Check if box can be pushed
            if [box_new_x, box_new_y] not in self.walls and [box_new_x, box_new_y] not in self.boxes:
                box_index = self.boxes.index([new_x, new_y])
                self.boxes[box_index] = [box_new_x, box_new_y]
            else:
                return

        # Update player position
        self.player_pos = [new_x, new_y]

    def check_win(self):
        # All targets must have a box on them
        for target in self.targets:
            if target not in self.boxes:
                return False
        return True

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.move_player(0, -1)
                    elif event.key == pygame.K_DOWN:
                        self.move_player(0, 1)
                    elif event.key == pygame.K_LEFT:
                        self.move_player(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.move_player(1, 0)
                    elif event.key == pygame.K_r:  # Reset level
                        self.__init__()
                    elif event.key == pygame.K_ESCAPE:  # Quit game
                        running = False

            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


# Run the game
if __name__ == "__main__":
    game = Sokoban()
    game.run()