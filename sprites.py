# File created by: Ryan Chakraborty (patched)
# The sprites module contains all the sprites
# Sprites include: player, mob - moving object

import pygame as pg
from pygame.sprite import Sprite
from chakraborty_heavens_last_stand.settings import *
from random import randint
vec = pg.math.Vector2

# ------------------ PLAYER ------------------ #
class Player(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface(TILESIZE)
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x*TILESIZE[0], y*TILESIZE[1]))
        # use float pos for smooth movement and robust collisions
        self.pos = vec(self.rect.topleft)
        self.vel = vec(0,0)
        self.speed = 250
        self.coins = 0
        self.health = 100
        # facing direction for projectiles; default to right
        self.dir = vec(1,0)
        self.last_shot = 0
        self.shot_cooldown = 300

    def get_keys(self):
        # compute desired velocity from input (frame-rate independent via dt)
        keys = pg.key.get_pressed()
        self.vel = vec(0,0)
        if keys[pg.K_w]: self.vel.y = -self.speed * self.game.dt
        if keys[pg.K_s]: self.vel.y = self.speed * self.game.dt
        if keys[pg.K_a]: self.vel.x = -self.speed * self.game.dt
        if keys[pg.K_d]: self.vel.x = self.speed * self.game.dt

        # update facing direction only when there's an input direction
        if self.vel.length_squared() > 0:
            # normalize to store only direction (not scaled by dt/speed)
            self.dir = self.vel.normalize()

        # shooting: keep your cooldown behavior but keep it in get_keys (works on key hold & tap)
        if keys[pg.K_SPACE] and pg.time.get_ticks() - self.last_shot > self.shot_cooldown:
            Projectile(self.game, self.rect.centerx, self.rect.centery, self.dir)
            self.last_shot = pg.time.get_ticks()

    def update(self):
        # get input
        self.get_keys()

        # --- axis-separated movement & collision (prevents snapping) ---

        # Horizontal move
        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        hits = pg.sprite.spritecollide(self, self.game.all_walls, False)
        for wall in hits:
            if self.vel.x > 0:  # moving right; hit left side of wall
                self.rect.right = wall.rect.left
            elif self.vel.x < 0:  # moving left; hit right side of wall
                self.rect.left = wall.rect.right
            # apply corrected position and stop horizontal movement
            self.pos.x = self.rect.x
            self.vel.x = 0

        # Vertical move
        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        hits = pg.sprite.spritecollide(self, self.game.all_walls, False)
        for wall in hits:
            if self.vel.y > 0:  # falling; hit top of wall
                self.rect.bottom = wall.rect.top
            elif self.vel.y < 0:  # moving up; hit bottom of wall
                self.rect.top = wall.rect.bottom
            # apply corrected position and stop vertical movement
            self.pos.y = self.rect.y
            self.vel.y = 0

        # --- coin pickup ---
        coin_hits = pg.sprite.spritecollide(self, self.game.all_coins, True)
        if coin_hits:
            self.coins += len(coin_hits)

# ------------------ MOB ------------------ #
class Mob(Sprite):
    def __init__(self, game, x, y, radius=150):
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

    def update(self):
        # created through help of GPT (specifically how to create a radius and a circle showing radius)
        # pursue player if inside radius
        # use player's pos (top-left) for chasing; this matches your other code
        direction = self.game.player.pos - self.pos
        distance = direction.length()
        if distance <= self.radius and distance > 0:
            # compute velocity scaled by dt
            self.vel = direction.normalize() * self.speed * self.game.dt
        else:
            self.vel = vec(0,0)

        # axis-separated movement & collision (same strategy as Player)
        # Horizontal
        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        hits = pg.sprite.spritecollide(self, self.game.all_walls, False)
        for wall in hits:
            if self.vel.x > 0:
                self.rect.right = wall.rect.left
            elif self.vel.x < 0:
                self.rect.left = wall.rect.right
            self.pos.x = self.rect.x
            # stop horizontal movement so the mob doesn't get continuously pushed
            self.vel.x = 0

        # Vertical
        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        hits = pg.sprite.spritecollide(self, self.game.all_walls, False)
        for wall in hits:
            if self.vel.y > 0:
                self.rect.bottom = wall.rect.top
            elif self.vel.y < 0:
                self.rect.top = wall.rect.bottom
            self.pos.y = self.rect.y
            self.vel.y = 0

        # die -> drop a coin
        if self.health <= 0:
            Coin(self.game, int(self.rect.x//TILESIZE[0]), int(self.rect.y//TILESIZE[1]))
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
        self.pos = vec(x,y)
        # ensure direction is normalized (length = 1)
        self.vel = dir.normalize() if dir.length_squared() > 0 else vec(1,0)
        self.speed = 400

    def update(self):
        # move projectile
        self.pos += self.vel * self.speed * self.game.dt
        self.rect.center = self.pos

        # hit mob
        hits = pg.sprite.spritecollide(self, self.game.all_mobs, False)
        for mob in hits:
            mob.health -= 10
            self.kill()
            return

        # hit wall -> destroy projectile
        if pg.sprite.spritecollideany(self, self.game.all_walls):
            self.kill()
            return

        # off-screen -> destroy
        if not self.game.screen.get_rect().collidepoint(self.rect.center):
            self.kill()

        # off-screen -> kill
        if not self.game.screen.get_rect().collidepoint(self.rect.center):
            self.kill()
