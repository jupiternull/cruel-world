import pygame


class Camera:
    def __init__(self, world_width, width=800):
        self.width = width
        self.world_width = world_width
        self.x = 0

    def update(self, target):
        self.x = max(0, min(max(0, self.world_width - self.width), target.centerx - self.width // 2))

    def rect(self, rect):
        return pygame.Rect(rect).move(-self.x, 0)

    def point(self, x, y):
        return x - self.x, y
