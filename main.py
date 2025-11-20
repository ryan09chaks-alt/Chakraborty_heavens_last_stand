import pygame as pg
from settings import *
from sprites import *
from tilemap import Map
from os import path

class Game:
    def __init__(self):
        # Initialize pygame and the game window
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Ryan's Game")
        self.clock = pg.time.Clock()  # for controlling FPS
        self.playing = True  # flag to control the main game loop

    def load_data(self):
        # Load game resources: map, images, background
        self.game_folder = path.dirname(__file__)  # current folder
        self.img_folder = path.join(self.game_folder, 'images')  # images folder
        self.map = Map(path.join(self.game_folder, "level1.txt"))  # load map data

        # Load player images
        self.player_img = pg.image.load(path.join(self.img_folder, 'kratos.png')).convert_alpha()
        self.player_img_inv = pg.image.load(path.join(self.img_folder, 'kratos.png')).convert_alpha()

        # Load and scale background image
        self.bg_img = pg.image.load(path.join(self.img_folder, 'background.png')).convert_alpha()
        self.bg_img = pg.transform.scale(self.bg_img, (WIDTH, HEIGHT))

    def new(self):
        # Create sprite groups for all game objects
        self.all_sprites = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_projectiles = pg.sprite.Group()
        self.all_keys = pg.sprite.Group()
        self.all_doors = pg.sprite.Group()

        self.player = None  # placeholder for player object

        # Read the map and create objects for each tile
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == "1":  # wall tile
                    Wall(self, col, row)
                elif tile.upper() == "C":  # coin
                    Coin(self, col, row)
                elif tile.upper() == "P":  # player start
                    self.player = Player(self, col, row)
                elif tile.upper() == "M":  # mob
                    # first mob drops key, others don't
                    Mob(self, col, row, drops_key=True if len(self.all_mobs) == 0 else False)
                elif tile.upper() == "D":  # door
                    Door(self, col, row)

        # Ensure there is a player in the map
        if self.player is None:
            raise ValueError("Map must have a 'P' tile for the player!")

    def run(self):
        # Main game loop
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000  # time delta for smooth movement
            self.events()  # handle input
            self.all_sprites.update()  # update all sprites
            self.draw()  # draw everything on screen
        pg.quit()  # quit pygame when loop ends

    def events(self):
        # Handle input events
        for event in pg.event.get():
            if event.type == pg.QUIT:  # window close button
                self.playing = False

    def draw_health_bar(self, surface, x, y, health):
        # Draw a green health bar with white border
        width = 200
        height = 20
        health = max(0, min(health, 100))  # clamp health between 0 and 100
        fill_width = int((health / 100) * width)  # scale width based on health
        pg.draw.rect(surface, (0, 255, 0), (x, y, fill_width, height))
        pg.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)

    def draw(self):
        # Draw everything on screen each frame
        self.screen.blit(self.bg_img, (0, 0))  # background first

        # Draw mob detection radius (transparent red circles)
        for mob in self.all_mobs:
            mob.draw_radius(self.screen)

        self.all_sprites.draw(self.screen)  # draw all sprites

        if self.player:
            # Draw health bar
            bar_y = self.screen.get_height() - 70
            self.draw_health_bar(self.screen, 20, bar_y, self.player.health)
            self.draw_text(self.screen, f"{int(self.player.health)}", 24, BLACK, 230, bar_y - 2)
            
            # Draw coin count
            self.draw_text(self.screen, f"Coins: {self.player.coins}", 24, BLACK, 300, 20)
            
            # Indicate if player has collected a key
            if self.player.has_key:
                self.draw_text(self.screen, "Key Acquired", 24, YELLOW, 500, 20)

        pg.display.flip()  # update the full display

    def draw_text(self, surface, text, size, color, x, y):
        # Utility function to draw text on screen
        font = pg.font.Font(None, size)
        surface.blit(font.render(text, True, color), (x, y))


# Run the game
if __name__ == "__main__":
    g = Game()
    g.load_data()  # load images and map
    g.new()        # create sprite instances
    g.run()        # start the game loop
