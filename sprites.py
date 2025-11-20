import pygame as pg
from pygame.sprite import Sprite
from settings import *
from random import randint
vec = pg.math.Vector2

# ------------------ PLAYER ------------------ #
class Player(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = game.player_img
        self.image_inv = getattr(game, 'player_img_inv', self.image)
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))
        self.pos = vec(self.rect.topleft)
        self.vel = vec(0,0)
        self.speed = 150
        self.coins = 0
        self.health = 100.0
        self.has_key = False
        self.dir = vec(1,0)
        self.last_shot = 0
        self.shot_cooldown = 300

    def get_keys(self):
        keys = pg.key.get_pressed()
        self.vel = vec(0,0)
        if keys[pg.K_w]: self.vel.y = -self.speed 
        if keys[pg.K_s]: self.vel.y = self.speed 
        if keys[pg.K_a]: self.vel.x = -self.speed
        if keys[pg.K_d]: self.vel.x = self.speed
        if self.vel.length_squared() > 0:
            self.dir = self.vel.normalize()
        if keys[pg.K_SPACE] and pg.time.get_ticks() - self.last_shot > self.shot_cooldown:
            Projectile(self.game, self.rect.centerx, self.rect.centery, self.dir)
            self.last_shot = pg.time.get_ticks()

    def update(self):
        self.get_keys()

        # --- Horizontal movement ---
        self.pos.x += self.vel.x * getattr(self.game, 'dt', 1)
        self.rect.x = int(self.pos.x)

        # Walls + closed doors collision (act as walls if no key)
        for wall in list(self.game.all_walls) + [d for d in self.game.all_doors if not self.has_key]:
            if self.rect.colliderect(wall.rect):
                if self.vel.x > 0: self.rect.right = wall.rect.left
                if self.vel.x < 0: self.rect.left = wall.rect.right
                self.pos.x = self.rect.x
                self.vel.x = 0

        # --- Vertical movement ---
        self.pos.y += self.vel.y * getattr(self.game, 'dt', 1)
        self.rect.y = int(self.pos.y)

        for wall in list(self.game.all_walls) + [d for d in self.game.all_doors if not self.has_key]:
            if self.rect.colliderect(wall.rect):
                if self.vel.y > 0: self.rect.bottom = wall.rect.top
                if self.vel.y < 0: self.rect.top = wall.rect.bottom
                self.pos.y = self.rect.y
                self.vel.y = 0

        # --- Coin pickup ---
        hits = pg.sprite.spritecollide(self, self.game.all_coins, True)
        if hits: self.coins += len(hits)

        # --- Key pickup ---
        hits = pg.sprite.spritecollide(self, self.game.all_keys, True)
        if hits: self.has_key = True

        # --- Open doors if player has key ---
        for door in pg.sprite.spritecollide(self, self.game.all_doors, False):
            if self.has_key:
                door.kill()  # remove door

        # Clamp health
        self.health = max(0, min(self.health, 100))

# ------------------ MOB ------------------ #
class Mob(Sprite):
    def __init__(self, game, x, y, radius=150, drops_key=False):
        self.groups = game.all_sprites, game.all_mobs
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface(TILESIZE)
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x*TILESIZE[0], y*TILESIZE[1]))
        self.pos = vec(self.rect.topleft)
        self.vel = vec(0,0)
        self.speed = 100
        self.health = 20
        self.radius = radius
        self.drops_key = drops_key
        self.damage_cooldown = 500
        self.last_damage_time = 0

    def update(self):
        # chase player
        if self.game.player:
            direction = self.game.player.pos - self.pos
            distance = direction.length()
            if 0 < distance <= self.radius:
                self.vel = direction.normalize() * self.speed * getattr(self.game, 'dt', 1)
            else:
                self.vel = vec(0,0)
        else:
            self.vel = vec(0,0)

        # Horizontal
        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        for wall in list(self.game.all_walls):
            if self.rect.colliderect(wall.rect):
                if self.vel.x > 0: self.rect.right = wall.rect.left
                if self.vel.x < 0: self.rect.left = wall.rect.right
                self.pos.x = self.rect.x
                self.vel.x = 0

        # Vertical
        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        for wall in list(self.game.all_walls):
            if self.rect.colliderect(wall.rect):
                if self.vel.y > 0: self.rect.bottom = wall.rect.top
                if self.vel.y < 0: self.rect.top = wall.rect.bottom
                self.pos.y = self.rect.y
                self.vel.y = 0

        # Damage player
        if self.game.player and self.rect.colliderect(self.game.player.rect):
            now = pg.time.get_ticks()
            if now - self.last_damage_time >= self.damage_cooldown:
                self.last_damage_time = now
                self.game.player.health -= 10

        # Die -> drop coin or key
        if self.health <= 0:
            tile_x = int(self.rect.x // TILESIZE[0])
            tile_y = int(self.rect.y // TILESIZE[1])
            if self.drops_key:
                Key(self.game, tile_x, tile_y)
            else:
                Coin(self.game, tile_x, tile_y)
            self.kill()

    def draw_radius(self, surface):
        s = pg.Surface((self.radius*2, self.radius*2), pg.SRCALPHA)
        pg.draw.circle(s, (255,0,0,50), (self.radius,self.radius), self.radius)
        surface.blit(s, (self.rect.centerx - self.radius, self.rect.centery - self.radius))

# ------------------ COIN ------------------ #
class Coin(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_coins
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface(TILESIZE)
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(topleft=(x*TILESIZE[0], y*TILESIZE[1]))

# ------------------ KEY ------------------ #
class Key(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_keys
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface(TILESIZE)
        self.image.fill((0, 200, 255))
        self.rect = self.image.get_rect(topleft=(x*TILESIZE[0], y*TILESIZE[1]))

# ------------------ DOOR ------------------ #
class Door(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_doors
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface(TILESIZE)
        self.image.fill((139,69,19))  # brown
        self.rect = self.image.get_rect(topleft=(x*TILESIZE[0], y*TILESIZE[1]))

# ------------------ WALL ------------------ #
class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface(TILESIZE)
        self.image.fill(GREY)
        self.rect = self.image.get_rect(topleft=(x*TILESIZE[0], y*TILESIZE[1]))

# ------------------ PROJECTILE ------------------ #
class Projectile(Sprite):
    def __init__(self, game, x, y, dir):
        self.groups = game.all_sprites, game.all_projectiles
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((16,16))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=(x,y))
        self.pos = vec(x, y)
        self.vel = dir.normalize() if dir.length_squared() > 0 else vec(1,0)
        self.speed = 400

    def update(self):
        self.pos += self.vel * self.speed * getattr(self.game, 'dt', 1)
        self.rect.center = self.pos

        # hit mob
        hits = pg.sprite.spritecollide(self, getattr(self.game, 'all_mobs', pg.sprite.Group()), False)
        for mob in hits:
            mob.health -= 10
            self.kill()
            return

        # wall
        if pg.sprite.spritecollideany(self, getattr(self.game, 'all_walls', pg.sprite.Group())):
            self.kill()
            return

        # off-screen
        if not self.game.screen.get_rect().collidepoint(self.rect.center):
            self.kill()