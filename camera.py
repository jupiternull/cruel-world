import pygame


class Camera:
    def __init__(self, world_width, width=800):
        self.width = width
        self.world_width = world_width
        self.x = 0
        self.bounds = (0, world_width)

    def set_bounds(self, left=0, right=None):
        self.bounds = (left, self.world_width if right is None else right)
        self.x = max(left, min(max(left, self.bounds[1] - self.width), self.x))

    def update(self, target):
        left, right = self.bounds
        self.x = max(left, min(max(left, right - self.width), target.centerx - self.width // 2))

    def rect(self, rect):
        return pygame.Rect(rect).move(-self.x, 0)

    def point(self, x, y):
        return x - self.x, y
