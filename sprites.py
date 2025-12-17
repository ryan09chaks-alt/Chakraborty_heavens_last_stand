import pygame as pg
from pygame.sprite import Sprite
from settings import *
from random import randint

vec = pg.math.Vector2

# Player character controlled by the user, handles movement, shooting, and stamina
class Player(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game

        self.image = game.player_img
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))
        self.pos = vec(self.rect.topleft)
        self.vel = vec(0, 0)
        self.dir = vec(1, 0)

        self.base_speed = 150
        self.health = 100
        self.coins = 0
        self.has_key = False

        self.last_shot = 0
        self.shot_cooldown = 300

        self.max_stamina = 100
        self.stamina = 100
        self.sprint_multiplier = 1.7
        self.stamina_drain = 40
        self.stamina_regen = 20

    # Handles input for movement, sprinting, and shooting
    def get_keys(self):
        keys = pg.key.get_pressed()
        move = vec(0, 0)

        if keys[pg.K_w]: move.y = -1
        if keys[pg.K_s]: move.y = 1
        if keys[pg.K_a]: move.x = -1
        if keys[pg.K_d]: move.x = 1

        if move.length_squared() > 0:
            move = move.normalize()

        sprinting = keys[pg.K_LSHIFT] and self.stamina > 0
        speed = self.base_speed * (self.sprint_multiplier if sprinting else 1)
        self.vel = move * speed

        if self.vel.length_squared() > 0:
            self.dir = self.vel.normalize()

        if keys[pg.K_SPACE] and pg.time.get_ticks() - self.last_shot > self.shot_cooldown:
            Projectile(self.game, self.rect.centerx, self.rect.centery, self.dir)
            self.last_shot = pg.time.get_ticks()

        if sprinting:
            self.stamina -= self.stamina_drain * self.game.dt
        else:
            self.stamina += self.stamina_regen * self.game.dt

        self.stamina = max(0, min(self.stamina, self.max_stamina))

    # Updates player position, handles collisions, pickups, and stats
    def update(self):
        self.get_keys()
        self.pos.x += self.vel.x * self.game.dt
        self.rect.x = int(self.pos.x)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.x > 0: self.rect.right = wall.rect.left
            if self.vel.x < 0: self.rect.left = wall.rect.right
            self.pos.x = self.rect.x

        self.pos.y += self.vel.y * self.game.dt
        self.rect.y = int(self.pos.y)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.y > 0: self.rect.bottom = wall.rect.top
            if self.vel.y < 0: self.rect.top = wall.rect.bottom
            self.pos.y = self.rect.y

        # Collect coins
        hits = pg.sprite.spritecollide(self, self.game.all_coins, True)
        self.coins += len(hits)

        # Collect keys
        if pg.sprite.spritecollide(self, self.game.all_keys, True):
            self.has_key = True

        self.health = max(0, min(self.health, 100))

# Standard enemy that follows player within radius and deals damage
class Mob(Sprite):
    def __init__(self, game, x, y, radius=150, drops_key=False):
        self.groups = game.all_sprites, game.all_mobs
        Sprite.__init__(self, self.groups)
        self.game = game

        self.image = pg.Surface(TILESIZE)
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))
        self.pos = vec(self.rect.topleft)
        self.vel = vec(0, 0)

        self.speed = 100
        self.health = 20
        self.radius = radius
        self.drops_key = drops_key

        self.last_damage = 0
        self.damage_cd = 500

    # Updates movement, collision, player damage, and death logic
    def update(self):
        direction = self.game.player.pos - self.pos
        dist = direction.length()
        if 0 < dist <= self.radius:
            self.vel = direction.normalize() * self.speed * self.game.dt
        else:
            self.vel = vec(0, 0)

        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.x > 0: self.rect.right = wall.rect.left
            if self.vel.x < 0: self.rect.left = wall.rect.right
            self.pos.x = self.rect.x

        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.y > 0: self.rect.bottom = wall.rect.top
            if self.vel.y < 0: self.rect.top = wall.rect.bottom
            self.pos.y = self.rect.y

        # Damage player if colliding and cooldown passed
        if self.rect.colliderect(self.game.player.rect):
            now = pg.time.get_ticks()
            if now - self.last_damage > self.damage_cd:
                self.last_damage = now
                self.game.player.health -= 10

        # Drop coin or key and remove mob on death
        if self.health <= 0:
            tx = int(self.rect.x // TILESIZE[0])
            ty = int(self.rect.y // TILESIZE[1])
            if self.drops_key:
                Key(self.game, tx, ty)
            else:
                Coin(self.game, tx, ty)
            self.kill()

    # Draws detection radius for player awareness
    def draw_radius(self, surface):
        s = pg.Surface((self.radius * 2, self.radius * 2), pg.SRCALPHA)
        pg.draw.circle(s, (255, 0, 0, 50), (self.radius, self.radius), self.radius)
        surface.blit(s, (self.rect.centerx - self.radius, self.rect.centery - self.radius))

# Simple coin pickup
class Coin(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_coins
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface(TILESIZE)
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))

# Key pickup used for doors
class Key(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_keys
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface(TILESIZE)
        self.image.fill((0, 200, 255))
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))

# Door to trigger level change
class Door(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_doors
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface(TILESIZE)
        self.image.fill((139, 69, 19))
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))

    # Switches levels when player collides
    def update(self):
        if self.rect.colliderect(self.game.player.rect):
            self.game.player.vel *= 0
            if self.game.current_level == "level1.txt":
                self.game.change_level("level2.txt")
            elif self.game.current_level == "level2.txt":
                self.game.change_level("level1.txt")

# Solid wall for collision
class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface(TILESIZE)
        self.image.fill(GREY)
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))

# Projectiles shot by player or boss
class Projectile(Sprite):
    def __init__(self, game, x, y, dir):
        self.groups = game.all_sprites, game.all_projectiles
        Sprite.__init__(self, self.groups)
        self.game = game

        self.image = pg.Surface((16, 16))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=(x, y))

        self.pos = vec(x, y)
        self.vel = dir.normalize() if dir.length_squared() > 0 else vec(1, 0)
        self.speed = 400

    # Moves projectile and handles collisions with walls or mobs
    def update(self):
        self.pos += self.vel * self.speed * self.game.dt
        self.rect.center = self.pos

        if pg.sprite.spritecollideany(self, self.game.all_walls):
            self.kill()
            return

        hits = pg.sprite.spritecollide(self, self.game.all_mobs, False)
        for mob in hits:
            mob.health -= 10
            self.kill()
            return

        if not self.game.screen.get_rect().collidepoint(self.rect.center):
            self.kill()

# Boss enemy with extra health and shooting attack every 5 seconds
class Boss(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_mobs
        Sprite.__init__(self, self.groups)
        self.game = game

        self.image = pg.Surface(TILESIZE)
        self.image.fill((128, 0, 128))
        self.rect = self.image.get_rect(topleft=(x * TILESIZE[0], y * TILESIZE[1]))
        self.pos = vec(self.rect.topleft)
        self.vel = vec(0, 0)

        self.speed = 80
        self.health = 200
        self.radius = 300  # Longer detection radius
        self.last_damage = 0
        self.damage_cd = 500
        self.last_shot_time = 0
        self.shot_interval = 5000  # Shoot every 5 seconds

    # Moves toward player and shoots projectiles periodically
    def update(self):
        direction = self.game.player.pos - self.pos
        dist = direction.length()
        if 0 < dist <= self.radius:
            self.vel = direction.normalize() * self.speed * self.game.dt
        else:
            self.vel = vec(0, 0)

        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.x > 0: self.rect.right = wall.rect.left
            if self.vel.x < 0: self.rect.left = wall.rect.right
            self.pos.x = self.rect.x

        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        for wall in pg.sprite.spritecollide(self, self.game.all_walls, False):
            if self.vel.y > 0: self.rect.bottom = wall.rect.top
            if self.vel.y < 0: self.rect.top = wall.rect.bottom
            self.pos.y = self.rect.y

        # Damage player if colliding
        if self.rect.colliderect(self.game.player.rect):
            now = pg.time.get_ticks()
            if now - self.last_damage > self.damage_cd:
                self.last_damage = now
                self.game.player.health -= 15

        # Shoot projectiles at intervals
        now = pg.time.get_ticks()
        if now - self.last_shot_time > self.shot_interval:
            Projectile(self.game, self.rect.centerx, self.rect.centery,
                       (self.game.player.pos - self.pos).normalize())
            self.last_shot_time = now

        # Kill boss and trigger win screen
        if self.health <= 0:
            self.kill()
            self.game.show_win_screen()

    # Draw detection radius for awareness
    def draw_radius(self, surface):
        s = pg.Surface((self.radius * 2, self.radius * 2), pg.SRCALPHA)
        pg.draw.circle(s, (128, 0, 128, 50), (self.radius, self.radius), self.radius)
        surface.blit(s, (self.rect.centerx - self.radius, self.rect.centery - self.radius))
