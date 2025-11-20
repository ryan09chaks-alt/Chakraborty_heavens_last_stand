import pygame as pg
from settings import *
from sprites import *
from tilemap import Map
from os import path


# test comment
# second test comment
class Game:
    def __init__(self):
        pg.init()  # Initialize Pygame
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Ryan's Game")
        self.clock = pg.time.Clock()
        self.playing = True  # Game loop flag

    def load_data(self):
        # Set folders and load map
        self.game_folder = path.dirname(__file__)
        self.img_folder = path.join(self.game_folder, 'images')
        self.map = Map(path.join(self.game_folder, "level1.txt"))

        # Load images for player and background
        self.player_img = pg.image.load(path.join(self.img_folder, 'kratos.png')).convert_alpha()
        self.player_img_inv = pg.image.load(path.join(self.img_folder, 'kratos.png')).convert_alpha()
        self.bg_img = pg.image.load(path.join(self.img_folder, 'background.png')).convert_alpha()
        self.bg_img = pg.transform.scale(self.bg_img, (WIDTH, HEIGHT))

    def new(self):
        # Sprite groups
        self.all_sprites = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_projectiles = pg.sprite.Group()
        self.all_keys = pg.sprite.Group()
        self.all_doors = pg.sprite.Group()  # Door group

        self.player = None

        # Build map from file
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == "1": Wall(self, col, row)
                elif tile.upper() == "C": Coin(self, col, row)
                elif tile.upper() == "P": self.player = Player(self, col, row)
                elif tile.upper() == "M": Mob(self, col, row, drops_key=True if len(self.all_mobs) == 0 else False)
                elif tile.upper() == "D": Door(self, col, row)  # Place door

        if self.player is None:
            raise ValueError("Map must have a 'P' tile for the player!")

    def run(self):
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000  # Delta time
            self.events()
            self.all_sprites.update()
            self.draw()
        pg.quit()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.playing = False

    # Draw player health bar
    def draw_health_bar(self, surface, x, y, health):
        width = 200
        height = 20
        health = max(0, min(health, 100))
        fill_width = int((health / 100) * width)

        pg.draw.rect(surface, (0, 255, 0), (x, y, fill_width, height))  # Green bar
        pg.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)  # Outline

    def draw(self):
        self.screen.blit(self.bg_img, (0, 0))  # Background

        # Draw mob detection radius (for debugging)
        for mob in self.all_mobs:
            mob.draw_radius(self.screen)

        self.all_sprites.draw(self.screen)  # Draw all sprites

        if self.player:
            bar_y = self.screen.get_height() - 70
            self.draw_health_bar(self.screen, 20, bar_y, self.player.health)
            self.draw_text(self.screen, f"{int(self.player.health)}", 24, BLACK, 230, bar_y - 2)
            self.draw_text(self.screen, f"Coins: {self.player.coins}", 24, BLACK, 300, 20)
            if self.player.has_key:
                self.draw_text(self.screen, "Key Acquired", 24, YELLOW, 500, 20)

        pg.display.flip()

    # Simple text rendering
    def draw_text(self, surface, text, size, color, x, y):
        font = pg.font.Font(None, size)
        surface.blit(font.render(text, True, color), (x, y))


if __name__ == "__main__":
    g = Game()
    g.load_data()
    g.new()
    g.run()
