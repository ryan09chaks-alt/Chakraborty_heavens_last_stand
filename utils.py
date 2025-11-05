# Utility classes

import pygame as pg

class Cooldown:
    def __init__(self, time_ms):
        self.start_time = 0
        self.time = time_ms

    def start(self):
        self.start_time = pg.time.get_ticks()

    def ready(self):
        return pg.time.get_ticks() - self.start_time >= self.time