import pygame as pg
from pygame.sprite import Sprite
from settings import *
from random import randint
vec = pg.math.Vector2  # 2D vector class for movement calculations

# ------------------ PLAYER ------------------ #
class Player(Sprite):
    def __init__(self, game, x, y):
        # Assign the player to all_sprites group
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game

        # Images for player facing normal and inverted (optional)
        self.image = game.player_img
        self.image_inv = getattr(game, 'player_img_inv', self.image)

        # Position and rectangle
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))
        self.pos = vec(self.rect.topleft)  # precise floating point position

        # Movement and status
        self.vel = vec(0, 0)
        self.speed = 150
        self.dir = vec(1,0)  # direction facing
        self.coins = 0
        self.health = 100.0
        self.has_key = False

        # Shooting
        self.last_shot = 0
        self.shot_cooldown = 300  # milliseconds

    def get_keys(self):
        # Check keyboard input
        keys = pg.key.get_pressed()
        self.vel = vec(0,0)

        # WASD movement
        if keys[pg.K_w]: self.vel.y = -self.speed
        if keys[pg.K_s]: self.vel.y = self.speed
        if keys[pg.K_a]: self.vel.x = -self.speed
        if keys[pg.K_d]: self.vel.x = self.speed

        # Update facing direction if moving
        if self.vel.length_squared() > 0:
            self.dir = self.vel.normalize()

        # Shooting projectiles
        if keys[pg.K_SPACE] and pg.time.get_ticks() - self.last_shot > self.shot_cooldown:
            Projectile(self.game, self.rect.centerx, self.rect.centery, self.dir)
            self.last_shot = pg.time.get_ticks()

    def update(self):
        self.get_keys()  # handle input

        # --- Horizontal Movement ---
        self.pos.x += self.vel.x * getattr(self.game, 'dt', 1)
        self.rect.x = int(self.pos.x)
        # Collision with walls
        for wall in pg.sprite.spritecollide(self, getattr(self.game, 'all_walls', pg.sprite.Group()), False):
            if self.vel.x > 0: self.rect.right = wall.rect.left
            if self.vel.x < 0: self.rect.left = wall.rect.right
            self.pos.x = self.rect.x
            self.vel.x = 0

        # --- Vertical Movement ---
        self.pos.y += self.vel.y * getattr(self.game, 'dt', 1)
        self.rect.y = int(self.pos.y)
        for wall in pg.sprite.spritecollide(self, getattr(self.game, 'all_walls', pg.sprite.Group()), False):
            if self.vel.y > 0: self.rect.bottom = wall.rect.top
            if self.vel.y < 0: self.rect.top = wall.rect.bottom
            self.pos.y = self.rect.y
            self.vel.y = 0

        # --- Pickup coins ---
        coins = getattr(self.game, 'all_coins', None)
        if coins:
            hits = pg.sprite.spritecollide(self, coins, True)  # remove coin on collision
            if hits: self.coins += len(hits)

        # --- Pickup key ---
        keys = getattr(self.game, 'all_keys', None)
        if keys:
            hits = pg.sprite.spritecollide(self, keys, True)
            if hits: self.has_key = True  # player now has key

        # --- Door interaction ---
        doors = getattr(self.game, 'all_doors', None)
        if doors:
            for door in pg.sprite.spritecollide(self, doors, False):
                if self.has_key:
                    door.kill()  # remove door (open it)

        # Clamp health between 0 and 100
        self.health = max(0, min(self.health, 100))


# ------------------ MOB ------------------ #
class Mob(Sprite):
    def __init__(self, game, x, y, radius=150, drops_key=False):
        # Add mob to all_sprites and all_mobs groups
        self.groups = game.all_sprites, game.all_mobs
        Sprite.__init__(self, self.groups)
        self.game = game

        # Appearance
        self.image = pg.Surface(TILESIZE)
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x*TILESIZE[0], y*TILESIZE[1]))
        self.pos = vec(self.rect.topleft)
        self.vel = vec(0,0)

        # Stats
        self.speed = 100
        self.health = 20
        self.radius = radius  # detection radius for chasing player
        self.drops_key = drops_key

        # Damage cooldown to avoid rapid HP drain
        self.damage_cooldown = 500
        self.last_damage_time = 0

    def update(self):
        # --- Chase Player if within radius ---
        if hasattr(self.game, 'player') and self.game.player:
            direction = self.game.player.pos - self.pos
            distance = direction.length()
            if 0 < distance <= self.radius:
                self.vel = direction.normalize() * self.speed * getattr(self.game, 'dt', 1)
            else:
                self.vel = vec(0,0)
        else:
            self.vel = vec(0,0)

        # --- Horizontal Movement & Collision ---
        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        for wall in pg.sprite.spritecollide(self, getattr(self.game, 'all_walls', pg.sprite.Group()), False):
            if self.vel.x > 0: self.rect.right = wall.rect.left
            if self.vel.x < 0: self.rect.left = wall.rect.right
            self.pos.x = self.rect.x
            self.vel.x = 0

        # --- Vertical Movement & Collision ---
        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        for wall in pg.sprite.spritecollide(self, getattr(self.game, 'all_walls', pg.sprite.Group()), False):
            if self.vel.y > 0: self.rect.bottom = wall.rect.top
            if self.vel.y < 0: self.rect.top = wall.rect.bottom
            self.pos.y = self.rect.y
            self.vel.y = 0

        # --- Damage Player on contact ---
        if hasattr(self.game, 'player') and self.game.player:
            if self.rect.colliderect(self.game.player.rect):
                now = pg.time.get_ticks()
                if now - self.last_damage_time >= self.damage_cooldown:
                    self.last_damage_time = now
                    self.game.player.health -= 10

        # --- Mob death: drop coin or key ---
        if self.health <= 0:
            tile_x = int(self.rect.x // TILESIZE[0])
            tile_y = int(self.rect.y // TILESIZE[1])
            if self.drops_key:
                Key(self.game, tile_x, tile_y)
            else:
                Coin(self.game, tile_x, tile_y)
            self.kill()

    def draw_radius(self, surface):
        # Optional: draw mob detection radius (transparent red circle)
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

        # Appearance
        self.image = pg.Surface((16,16))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=(x,y))

        # Movement
        self.pos = vec(x, y)
        self.vel = dir.normalize() if dir.length_squared() > 0 else vec(1,0)
        self.speed = 400

    def update(self):
        # Move projectile
        self.pos += self.vel * self.speed * getattr(self.game, 'dt', 1)
        self.rect.center = self.pos

        # Hit mobs
        hits = pg.sprite.spritecollide(self, getattr(self.game, 'all_mobs', pg.sprite.Group()), False)
        for mob in hits:
            mob.health -= 10
            self.kill()
            return

        # Hit walls
        if pg.sprite.spritecollideany(self, getattr(self.game, 'all_walls', pg.sprite.Group())):
            self.kill()
            return

        # Off-screen removal
        if not self.game.screen.get_rect().collidepoint(self.rect.center):
            self.kill()