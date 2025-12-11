# Game Settings + Engine Setup
import pygame as pg
from settings import *
from sprites import *
from tilemap import Map
from os import path

class Game:
    def __init__(self):
        pg.init()

        # --- Create the game window and clock ---
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Ryan's Game")
        self.clock = pg.time.Clock()

        # Tracks if the game loop is running
        self.playing = True


    def load_data(self):
        # --- Loads images, map, and sets file paths ---
        self.game_folder = path.dirname(__file__)
        self.img_folder = path.join(self.game_folder, 'images')
        self.map = Map(path.join(self.game_folder, "level1.txt"))

        # Player graphics
        self.player_img = pg.image.load(path.join(self.img_folder, 'kratos.png')).convert_alpha()
        self.player_img_inv = pg.image.load(path.join(self.img_folder, 'kratos.png')).convert_alpha()

        # Background image
        self.bg_img = pg.image.load(path.join(self.img_folder, 'background.png')).convert_alpha()
        self.bg_img = pg.transform.scale(self.bg_img, (WIDTH, HEIGHT))


    # ------------------ START MENU ------------------ #
    def show_start_screen(self):
        """Displays a simple start menu before the game begins."""
        waiting = True

        title_font = pg.font.Font(None, 80)
        text_font = pg.font.Font(None, 40)

        while waiting:
            self.clock.tick(FPS)

            # Check for user input
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.playing = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        waiting = False

            # Draw background
            self.screen.fill((20, 20, 20))

            # Draw title
            title = title_font.render("Heaven's Last Stand", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))

            # Draw instruction
            press_enter = text_font.render("Press ENTER to Start", True, (200, 200, 200))
            self.screen.blit(press_enter, (WIDTH//2 - press_enter.get_width()//2, HEIGHT//2))

            pg.display.flip()


    def new(self):
        # --- Create all sprite groups for the level ---
        self.all_sprites = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_projectiles = pg.sprite.Group()
        self.all_keys = pg.sprite.Group()
        self.all_doors = pg.sprite.Group()

        self.player = None

        # --- Build the world from map.txt ---
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):

                # Create objects based on character in map file
                if tile == "1": 
                    Wall(self, col, row)

                elif tile.upper() == "C":
                    Coin(self, col, row)

                elif tile.upper() == "P":
                    self.player = Player(self, col, row)

                # First mob drops the key
                elif tile.upper() == "M":
                    Mob(self, col, row, drops_key=True if len(self.all_mobs) == 0 else False)

                elif tile.upper() == "D":
                    Door(self, col, row)

        # Prevent running the game without placing player
        if self.player is None:
            raise ValueError("Map must have a 'P' tile for the player!")


    # ------------------ MAIN GAME LOOP ------------------ #
    def run(self):
        while self.playing:
            # dt = frame time → smooth movement
            self.dt = self.clock.tick(FPS) / 1000

            self.events()
            self.all_sprites.update()
            self.draw()

        pg.quit()


    def events(self):
        # Handles only quitting for now
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.playing = False


    # ------------------ HEALTH BAR ------------------ #
    def draw_health_bar(self, surface, x, y, health):
        """Draws a simple green health bar with white outline."""
        width = 200
        height = 20
        health = max(0, min(health, 100))
        fill = int((health / 100) * width)

        pg.draw.rect(surface, (0, 255, 0), (x, y, fill, height))  # green fill
        pg.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)  # outline


    # ------------------ STAMINA BAR ------------------ #
    def draw_stamina_bar(self, surface, x, y, stamina):
        """Draws stamina bar next to health."""
        width = 200
        height = 20
        stamina = max(0, min(stamina, 100))
        fill = int((stamina / 100) * width)

        pg.draw.rect(surface, (0, 150, 255), (x, y, fill, height))  # blue fill
        pg.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)


    # ------------------ INVENTORY BAR ------------------ #
    def draw_inventory(self, surface):
        """Draws coin and key icons at bottom of screen."""
        inv_height = 50
        inv_y = self.screen.get_height() - inv_height

        # Background
        pg.draw.rect(surface, (50, 50, 50), (0, inv_y, WIDTH, inv_height))
        pg.draw.rect(surface, WHITE, (0, inv_y, WIDTH, inv_height), 2)

        # Coin icon + count
        coin_icon = pg.Rect(20, inv_y + 10, 30, 30)
        pg.draw.ellipse(surface, YELLOW, coin_icon)
        self.draw_text(surface, f"x {self.player.coins}", 24, WHITE, coin_icon.right + 10, inv_y + 10)

        # Key icon + count
        key_icon = pg.Rect(150, inv_y + 10, 30, 30)
        pg.draw.rect(surface, (0, 200, 255), key_icon)
        self.draw_text(surface, f"x {1 if self.player.has_key else 0}", 24, WHITE, key_icon.right + 10, inv_y + 10)


    # ------------------ DRAW EVERYTHING ------------------ #
    def draw(self):
        # Background
        self.screen.blit(self.bg_img, (0, 0))

        # Show mob detection radius (for debugging)
        for mob in self.all_mobs:
            mob.draw_radius(self.screen)

        # Draw all objects
        self.all_sprites.draw(self.screen)

        # UI (health, stamina, coins, key)
        if self.player:
            bar_y = self.screen.get_height() - 70

            # Health
            self.draw_health_bar(self.screen, 20, bar_y, self.player.health)

            # Stamina (next to health)
            self.draw_stamina_bar(self.screen, 20, bar_y + 25, self.player.stamina)

            # Additional info
            self.draw_text(self.screen, f"Coins: {self.player.coins}", 24, BLACK, 300, 20)

            # "Key acquired" message
            if self.player.has_key:
                self.draw_text(self.screen, "Key Acquired", 24, YELLOW, 500, 20)

            # Bottom HUD
            self.draw_inventory(self.screen)

        pg.display.flip()


    # ------------------ TEXT HELPER ------------------ #
    def draw_text(self, surface, text, size, color, x, y):
        font = pg.font.Font(None, size)
        surface.blit(font.render(text, True, color), (x, y))


# ------------------ PROGRAM START ------------------ #
if __name__ == "__main__":
    g = Game()
    g.load_data()
    g.show_start_screen()   # Show menu before game begins
    g.new()
    g.run()
