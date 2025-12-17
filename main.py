# 1. Boss fight as final challenge in level2.
# 2. Final feature: Boss shoots projectiles every 5 seconds, giving strategic combat.
#
# Sources:
# Value Error : https://www.w3schools.com/python/ref_exception_valueerror.asp
# https://stackoverflow.com/questions/37800894/what-is-the-surface-blit-function-in-pygame-what-does-it-do-how-does-it-work
# AI Reference: OpenAI ChatGPT-5 (Code assistance) --> Inventory HUD, Mob Radius
# ==================================================
import pygame as pg
from settings import *
from sprites import *
from tilemap import Map
from os import path

vec = pg.math.Vector2

class Game:
    def __init__(self):
        pg.init()
        # Window & clock setup
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Ryan's Game")
        self.clock = pg.time.Clock()
        self.playing = True
        self.show_full_map = False
        # Current level file
        self.current_level = "level1.txt"

    
    # LOAD DATA
    
    def load_data(self):
        self.game_folder = path.dirname(__file__)
        self.img_folder = path.join(self.game_folder, 'images')
        self.map = Map(path.join(self.game_folder, self.current_level))
        # Player images
        self.player_img = pg.image.load(path.join(self.img_folder, 'kratos.png')).convert_alpha()
        self.player_img_inv = pg.image.load(path.join(self.img_folder, 'kratos.png')).convert_alpha()
        # Background images
        self.bg_img = pg.image.load(path.join(self.img_folder, 'background.png')).convert_alpha()
        self.bg_img = pg.transform.scale(self.bg_img, (WIDTH, HEIGHT))

   
    # START SCREEN
    # Let player select Start, Credits, or Quit
    # Highlight currently selected menu option
    
    def show_start_screen(self):
        waiting = True
        selected = 0
        options = ["Start Game", "Credits", "Quit"]

        while waiting:
            self.screen.fill((0, 0, 0))
            self.draw_text(self.screen, "Heaven's Last Stand", 64, WHITE, WIDTH // 2 - 220, HEIGHT // 4)

            for i, option in enumerate(options):
                color = YELLOW if i == selected else WHITE
                self.draw_text(self.screen, option, 40, color, WIDTH // 2 - 100, HEIGHT // 2 + i * 60)

            pg.display.flip()
            # Handle menu navigation input
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP:
                        selected = (selected - 1) % len(options)
                    if event.key == pg.K_DOWN:
                        selected = (selected + 1) % len(options)
                    if event.key == pg.K_RETURN:
                        if selected == 0:
                            waiting = False
                        elif selected == 1:
                            self.show_credits_screen()
                        elif selected == 2:
                            pg.quit()
                            quit()

    
    # CREDITS SCREEN
  
    def show_credits_screen(self):
        waiting = True
        while waiting:
            self.screen.fill(BLACK)
            self.draw_text(self.screen, "CREDITS", 60, WHITE, WIDTH // 2 - 140, HEIGHT // 4)
            self.draw_text(self.screen, "Thanks to Ryan C", 40, YELLOW, WIDTH // 2 - 180, HEIGHT // 2)
            self.draw_text(self.screen, "Press any key to return", 30, GREY, WIDTH // 2 - 180, HEIGHT - 100)
            pg.display.flip()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN:
                    waiting = False

   
    # WIN SCREEN
    
    def show_win_screen(self):
        waiting = True
        while waiting:
            self.screen.fill((0, 0, 0))
            self.draw_text(self.screen, "YOU WIN!", 80, GREEN, WIDTH // 2 - 180, HEIGHT // 3)
            self.draw_text(self.screen, "Press R to Restart", 40, WHITE, WIDTH // 2 - 150, HEIGHT // 2)
            self.draw_text(self.screen, "Press Q to Quit", 40, WHITE, WIDTH // 2 - 150, HEIGHT // 2 + 60)
            pg.display.flip()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_r:
                        self.change_level("level1.txt")
                        waiting = False
                    if event.key == pg.K_q:
                        pg.quit()
                        quit()


    
    # DEATH SCREEN
    # Gives feedback on player death and allows retry or quit
    def show_death_screen(self):
        while True:
            self.screen.fill(BLACK)
            self.draw_text(self.screen, "YOU DIED", 80, RED, WIDTH // 2 - 180, HEIGHT // 3)
            self.draw_text(self.screen, "Press R to Retry", 40, WHITE, WIDTH // 2 - 150, HEIGHT // 2)
            self.draw_text(self.screen, "Press Q to Quit", 40, WHITE, WIDTH // 2 - 150, HEIGHT // 2 + 60)
            pg.display.flip()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_r:
                        self.change_level(self.current_level)
                        return
                    if event.key == pg.K_q:
                        pg.quit()
                        quit()

   
    # NEW LEVEL
   
    def new(self):
        # Clears groups and spawns all entities based on the map
        self.all_sprites = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_projectiles = pg.sprite.Group()
        self.all_keys = pg.sprite.Group()
        self.all_doors = pg.sprite.Group()

        self.player = None

        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == "1": Wall(self, col, row)
                elif tile.upper() == "C": Coin(self, col, row)
                elif tile.upper() == "P": self.player = Player(self, col, row)
                elif tile.upper() == "M": Mob(self, col, row, drops_key=True if len(self.all_mobs) == 0 else False)
                elif tile.upper() == "B" and self.current_level == "level2.txt": Boss(self, col, row)
                elif tile.upper() == "D": Door(self, col, row)

        if self.player is None:
            raise ValueError("Map must have a 'P' tile for the player!")

   
    # CHANGE LEVEL
 
    def change_level(self, new_level):
        # Preserves player stats, reloads map, respawns entities
        saved_health = self.player.health
        saved_coins = self.player.coins
        saved_key = self.player.has_key

        for sprite in self.all_sprites:
            sprite.kill()

        self.current_level = new_level
        self.map = Map(path.join(self.game_folder, self.current_level))

        self.all_sprites = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_projectiles = pg.sprite.Group()
        self.all_keys = pg.sprite.Group()
        self.all_doors = pg.sprite.Group()

        player_spawned = False
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == "1": Wall(self, col, row)
                elif tile.upper() == "C": Coin(self, col, row)
                elif tile.upper() == "P" and not player_spawned:
                    self.player.rect.topleft = (col * TILESIZE[0], row * TILESIZE[1])
                    self.player.pos = vec(self.player.rect.topleft)
                    player_spawned = True
                elif tile.upper() == "M": Mob(self, col, row, drops_key=True if len(self.all_mobs) == 0 else False)
                elif tile.upper() == "B" and self.current_level == "level2.txt": Boss(self, col, row)
                elif tile.upper() == "D": Door(self, col, row)

        self.player.health = saved_health
        self.player.coins = saved_coins
        self.player.has_key = saved_key
        self.all_sprites.add(self.player)

    
    # MAIN LOOP
  
    def run(self):
        # Handles core game flow, updating and drawing entities
        self.show_start_screen()
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.all_sprites.update()
            if self.player.health <= 0:
                self.show_death_screen()
            self.draw()
        pg.quit()

    
    # EVENTS
    
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.playing = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_m:
                    self.show_full_map = not self.show_full_map

  
    # DRAWING
    def draw(self):
        self.screen.blit(self.bg_img, (0, 0))
        for mob in self.all_mobs:
            mob.draw_radius(self.screen)
        self.all_sprites.draw(self.screen)

        if self.player:
            bar_y = HEIGHT - 70
            self.draw_health_bar(self.screen, 20, bar_y, self.player.health)
            self.draw_stamina_bar(self.screen, 20, bar_y + 25, self.player.stamina)
            self.draw_inventory(self.screen)

        if self.show_full_map:
            self.draw_fullmap()
        else:
            self.draw_minimap(self.screen)

        pg.display.flip()

   
    # HELPER FUNCTIONS
   
    def draw_text(self, surface, text, size, color, x, y):
        font = pg.font.Font(None, size)
        surface.blit(font.render(text, True, color), (x, y))

    def draw_health_bar(self, surface, x, y, health):
        width, height = 200, 20
        fill = int((health / 100) * width)
        pg.draw.rect(surface, (0, 255, 0), (x, y, fill, height))
        pg.draw.rect(surface, WHITE, (x, y, width, height), 2)

    def draw_stamina_bar(self, surface, x, y, stamina):
        width, height = 200, 20
        fill = int((stamina / 100) * width)
        pg.draw.rect(surface, (0, 150, 255), (x, y, fill, height))
        pg.draw.rect(surface, WHITE, (x, y, width, height), 2)

    def draw_inventory(self, surface):
        inv_height = 50
        inv_y = HEIGHT - inv_height
        pg.draw.rect(surface, (50, 50, 50), (0, inv_y, WIDTH, inv_height))
        pg.draw.rect(surface, WHITE, (0, inv_y, WIDTH, inv_height), 2)
        coin_icon = pg.Rect(20, inv_y + 10, 30, 30)
        pg.draw.ellipse(surface, YELLOW, coin_icon)
        self.draw_text(surface, f"x {self.player.coins}", 24, WHITE, coin_icon.right + 10, inv_y + 10)
        key_icon = pg.Rect(150, inv_y + 10, 30, 30)
        pg.draw.rect(surface, (0, 200, 255), key_icon)
        self.draw_text(surface, f"x {1 if self.player.has_key else 0}", 24, WHITE, key_icon.right + 10, inv_y + 10)

    def draw_minimap(self, surface):
        scale = 0.15
        map_w, map_h = int(self.map.width * scale), int(self.map.height * scale)
        x, y = WIDTH - map_w - 20, HEIGHT - 50 - map_h - 10
        pg.draw.rect(surface, (40, 40, 40), (x, y, map_w, map_h))
        pg.draw.rect(surface, WHITE, (x, y, map_w, map_h), 2)
        for row, line in enumerate(self.map.data):
            for col, tile in enumerate(line):
                tile_x = x + col * 32 * scale
                tile_y = y + row * 32 * scale
                if tile == "1": pg.draw.rect(surface, GREY, (tile_x, tile_y, 4, 4))
                if tile.upper() == "C": pg.draw.rect(surface, YELLOW, (tile_x, tile_y, 4, 4))
                if tile.upper() == "M": pg.draw.rect(surface, RED, (tile_x, tile_y, 4, 4))
                if tile.upper() == "B": pg.draw.rect(surface, (128, 0, 128), (tile_x, tile_y, 4, 4))
                if tile.upper() == "D": pg.draw.rect(surface, BLUE, (tile_x, tile_y, 4, 4))
        p_x = x + self.player.rect.centerx * scale
        p_y = y + self.player.rect.centery * scale
        pg.draw.circle(surface, GREEN, (int(p_x), int(p_y)), 4)

    def draw_fullmap(self):
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.fill((10, 10, 10))
        overlay.set_alpha(230)
        self.screen.blit(overlay, (0, 0))
        full_scale = min(WIDTH / self.map.width, HEIGHT / self.map.height)
        for row, line in enumerate(self.map.data):
            for col, tile in enumerate(line):
                draw_x = col * 32 * full_scale
                draw_y = row * 32 * full_scale
                if tile == "1": pg.draw.rect(self.screen, GREY, (draw_x, draw_y, 16, 16))
                if tile.upper() == "C": pg.draw.rect(self.screen, YELLOW, (draw_x, draw_y, 16, 16))
                if tile.upper() == "M": pg.draw.rect(self.screen, RED, (draw_x, draw_y, 16, 16))
                if tile.upper() == "B": pg.draw.rect(self.screen, (128, 0, 128), (draw_x, draw_y, 16, 16))
                if tile.upper() == "D": pg.draw.rect(self.screen, BLUE, (draw_x, draw_y, 16, 16))
        p_x = self.player.rect.centerx * full_scale
        p_y = self.player.rect.centery * full_scale
        pg.draw.circle(self.screen, GREEN, (int(p_x), int(p_y)), 8)
        self.draw_text(self.screen, "FULL MAP — Press M to Close", 36, WHITE, 20, 20)



# PROGRAM START
if __name__ == "__main__":
    g = Game()
    g.load_data()
    g.new()
    g.run()
