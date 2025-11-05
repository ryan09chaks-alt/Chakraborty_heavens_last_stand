# Created by Ryan Chakraborty with the help of ChatGPT
# import necessary modules
# core game loop
# input
# update
# draw

# why? what? how?

import pygame as pg
from chakraborty_heavens_last_stand.settings import *
from chakraborty_heavens_last_stand.sprites import *
from chakraborty_heavens_last_stand.tilemap import Map
from os import path

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Ryan's Game")
        self.clock = pg.time.Clock()
        self.playing = True
        self.map = Map(path.join(path.dirname(__file__), "level1.txt"))

    def new(self):
        self.all_sprites = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_projectiles = pg.sprite.Group()

        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == "1":
                    Wall(self, col, row)
                elif tile.upper() == "C":
                    Coin(self, col, row)
                elif tile.upper() == "P":
                    self.player = Player(self, col, row)
                elif tile.upper() == "M":
                    Mob(self, col, row)

    def run(self):
        while self.playing:
            self.dt = self.clock.tick(FPS)/1000
            self.events()
            self.all_sprites.update()
            self.draw()
        pg.quit()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.playing = False

    def draw(self):
        self.screen.fill(WHITE)
        # draw mobs' detection radius
        for mob in self.all_mobs:
            mob.draw_radius(self.screen)
        self.all_sprites.draw(self.screen)
        # draw player stats
        self.draw_text(self.screen, f"Health: {self.player.health}", 24, BLACK, 80, 20)
        self.draw_text(self.screen, f"Coins: {self.player.coins}", 24, BLACK, 250, 20)
        pg.display.flip()

    def draw_text(self, surface, text, size, color, x, y):
        font = pg.font.Font(None, size)
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, (x,y))

if __name__ == "__main__":
    g = Game()
    g.new()
    g.run()
     