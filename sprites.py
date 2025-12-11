# sprites.py
import pygame as pg
from pygame.sprite import Sprite
from settings import *
from random import randint
vec = pg.math.Vector2  # convenient alias

# ------------------ PLAYER ------------------ #
class Player(Sprite):
    def __init__(self, game, x, y):
        # register groups
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game

        # images
        self.image = game.player_img
        self.image_inv = getattr(game, 'player_img_inv', self.image)

        # position / rect
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))
        self.pos = vec(self.rect.topleft)   # float position
        self.vel = vec(0, 0)

        # movement base speed (pixels / second)
        self.base_speed = 150

        # direction for shooting
        self.dir = vec(1, 0)

        # stats
        self.health = 100.0
        self.coins = 0
        self.has_key = False

        # shooting
        self.last_shot = 0
        self.shot_cooldown = 300  # ms

        # -------- Sprint / Stamina --------
        self.max_stamina = 100.0
        self.stamina = self.max_stamina
        self.sprint_multiplier = 1.7   # times base speed
        self.stamina_drain = 40.0      # per second while sprinting
        self.stamina_regen = 20.0      # per second when not sprinting

    def get_keys(self):
        """Compute self.vel (pixels/sec), update direction and handle shooting + sprint consumption/regeneration."""
        keys = pg.key.get_pressed()
        move = vec(0, 0)

        # WASD movement input -> movement vector (not scaled by speed yet)
        if keys[pg.K_w]:
            move.y = -1
        if keys[pg.K_s]:
            move.y = 1
        if keys[pg.K_a]:
            move.x = -1
        if keys[pg.K_d]:
            move.x = 1

        # normalize movement vector for diagonal speed consistency
        if move.length_squared() > 0:
            move = move.normalize()

        # is sprint requested?
        sprinting = keys[pg.K_LSHIFT] and self.stamina > 0 and move.length_squared() > 0

        # choose speed
        speed = self.base_speed * (self.sprint_multiplier if sprinting else 1.0)

        # set velocity in pixels/sec
        self.vel = move * speed

        # update facing direction if moving (used for projectiles)
        if self.vel.length_squared() > 0:
            self.dir = self.vel.normalize()

        # shooting (space)
        if keys[pg.K_SPACE] and pg.time.get_ticks() - self.last_shot > self.shot_cooldown:
            Projectile(self.game, self.rect.centerx, self.rect.centery, self.dir)
            self.last_shot = pg.time.get_ticks()

        # stamina drain or regen (use game.dt seconds)
        if sprinting:
            self.stamina -= self.stamina_drain * self.game.dt
        else:
            # regen only when not sprinting
            self.stamina += self.stamina_regen * self.game.dt

        # clamp stamina
        self.stamina = max(0.0, min(self.stamina, self.max_stamina))

    def update(self):
        # read input and update velocity / stamina
        self.get_keys()

        # apply movement with dt
        self.pos.x += self.vel.x * self.game.dt
        self.rect.x = int(self.pos.x)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.x > 0:
                self.rect.right = wall.rect.left
            if self.vel.x < 0:
                self.rect.left = wall.rect.right
            self.pos.x = self.rect.x

        self.pos.y += self.vel.y * self.game.dt
        self.rect.y = int(self.pos.y)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.y > 0:
                self.rect.bottom = wall.rect.top
            if self.vel.y < 0:
                self.rect.top = wall.rect.bottom
            self.pos.y = self.rect.y

        # pickup coins
        hits = pg.sprite.spritecollide(self, self.game.all_coins, True)
        if hits:
            self.coins += len(hits)

        # pickup key
        key_hits = pg.sprite.spritecollide(self, self.game.all_keys, True)
        if key_hits:
            self.has_key = True

        # open door if has key
        for door in pg.sprite.spritecollide(self, self.game.all_doors, False):
            if self.has_key:
                door.kill()

        # clamp health
        self.health = max(0.0, min(self.health, 100.0))

# ------------------ MOB ------------------ #
class Mob(Sprite):
    def __init__(self, game, x, y, radius=150, drops_key=False):
        self.groups = game.all_sprites, game.all_mobs
        Sprite.__init__(self, self.groups)
        self.game = game

        self.image = pg.Surface(TILESIZE)
        # self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x*TILESIZE[0], y*TILESIZE[1]))
        self.pos = vec(self.rect.topleft)
        self.vel = vec(0, 0)

        self.speed = 100
        self.health = 20
        self.radius = radius
        self.drops_key = drops_key

        self.damage_cooldown = 500
        self.last_damage_time = 0

    def update(self):
        # chase player if inside radius
        if hasattr(self.game, 'player') and self.game.player:
            direction = self.game.player.pos - self.pos
            distance = direction.length()
            if 0 < distance <= self.radius:
                self.vel = direction.normalize() * self.speed * self.game.dt
            else:
                self.vel = vec(0, 0)
        else:
            self.vel = vec(0, 0)

        # horizontal movement & collision
        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.x > 0:
                self.rect.right = wall.rect.left
            if self.vel.x < 0:
                self.rect.left = wall.rect.right
            self.pos.x = self.rect.x
            self.vel.x = 0

        # vertical movement & collision
        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.y > 0:
                self.rect.bottom = wall.rect.top
            if self.vel.y < 0:
                self.rect.top = wall.rect.bottom
            self.pos.y = self.rect.y
            self.vel.y = 0

        # damage player on contact
        if hasattr(self.game, 'player') and self.game.player:
            if self.rect.colliderect(self.game.player.rect):
                now = pg.time.get_ticks()
                if now - self.last_damage_time >= self.damage_cooldown:
                    self.last_damage_time = now
                    self.game.player.health -= 10

        # death -> drop coin/key
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
        self.image.fill((0,200,255))
        self.rect = self.image.get_rect(topleft=(x*TILESIZE[0], y*TILESIZE[1]))

# ------------------ DOOR ------------------ #
class Door(Sprite):
    def __init__(self, game, x, y, target_level="level2.txt"):  # Add target_level parameter
        self.groups = game.all_sprites, game.all_doors
        Sprite.__init__(self, self.groups)
        self.rect = pg.Rect(x*TILESIZE[0], y*TILESIZE[1], TILESIZE[0], TILESIZE[1])
        self.target_level = target_level  # The map this door will load
        self.image = pg.Surface(TILESIZE)
        self.image.fill((139,69,19))
        
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
        self.pos += self.vel * self.speed * self.game.dt
        self.rect.center = self.pos

        # hit mobs
        hits = pg.sprite.spritecollide(self, self.game.all_mobs, False)
        for mob in hits:
            mob.health -= 10
            self.kill()
            return

        # hit walls
        if pg.sprite.spritecollideany(self, self.game.all_walls):
            self.kill()
            return

        # off-screen
        if not self.game.screen.get_rect().collidepoint(self.rect.center):
            self.kill()
