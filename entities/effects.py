import math
import random
import pygame


class Particle:
    def __init__(self, x, y, color, velocity_x, velocity_y, lifetime=30):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = velocity_x
        self.vel_y = velocity_y
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += 0.3
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen):
        size = int(self.size * (self.lifetime / self.max_lifetime))
        if size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)


class PowerUp:
    def __init__(self, x, y, type='health'):
        self.type = type
        self.x = x
        self.y = y
        self.size = 16
        self.lifetime = 300
        self.collected = False
        self.bob_offset = 0
        self.bob_speed = 0.1

    def update(self):
        self.lifetime -= 1
        self.bob_offset = math.sin(pygame.time.get_ticks() * self.bob_speed * 0.01) * 5
        return self.lifetime > 0 and not self.collected

    def draw(self, screen):
        y_pos = self.y + self.bob_offset
        if self.type == 'health':
            color = (255, 50, 50)
            pygame.draw.rect(screen, color, (self.x - 6, y_pos - 2, 12, 4))
            pygame.draw.rect(screen, color, (self.x - 2, y_pos - 6, 4, 12))
        else:
            color = (255, 215, 0)
            points = []
            for i in range(5):
                angle = math.radians(i * 72 - 90)
                points.append((self.x + math.cos(angle) * 8, y_pos + math.sin(angle) * 8))
            pygame.draw.polygon(screen, color, points)

    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
