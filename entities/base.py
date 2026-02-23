import pygame
from config import GAME_CONFIG


class Entity:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 0, 0)
        self.vel_y = 0
        self.on_ground = False
        self.alive = True
        self.facing_right = True

        # Collision box offsets within the sprite frame.
        # Subclasses set these to match their sprite layout.
        self._col_x_offset = 0
        self._col_y_offset = 0
        self._col_width = 0    # 0 = use full rect.width
        self._col_height = 0   # 0 = use full rect.height

    def _col_rect(self, dx=0, dy=0):
        """Return the active collision rect, mirroring X offset when facing left."""
        w = self._col_width or self.rect.width
        h = self._col_height or self.rect.height

        if self.facing_right:
            x = self.rect.x + self._col_x_offset + dx
        else:
            x = self.rect.x + (self.rect.width - self._col_x_offset - w) + dx

        y = self.rect.y + self._col_y_offset + dy
        return pygame.Rect(x, y, w, h)

    def check_collision(self, dx, dy, layout):
        test_rect = self._col_rect(dx, dy)
        ts = GAME_CONFIG['TILE_SIZE']
        rows = len(layout)
        cols = len(layout[0]) if rows else 0

        left = test_rect.left // ts
        right = test_rect.right // ts
        top = test_rect.top // ts
        bottom = test_rect.bottom // ts

        for ty in range(max(0, top), min(rows, bottom + 1)):
            for tx in range(max(0, left), min(cols, right + 1)):
                if layout[ty][tx] in GAME_CONFIG['SOLID_TILES']:
                    tile_rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
                    if test_rect.colliderect(tile_rect):
                        return True
        return False

    def apply_gravity(self, layout):
        self.vel_y += GAME_CONFIG['GRAVITY']
        if not self.check_collision(0, self.vel_y, layout):
            self.rect.y += self.vel_y
            self.on_ground = False
            if self.rect.bottom >= GAME_CONFIG['HEIGHT']:
                self.rect.bottom = GAME_CONFIG['HEIGHT']
                self.vel_y = 0
                self.on_ground = True
        else:
            step = 1 if self.vel_y > 0 else -1
            for _ in range(abs(self.vel_y)):
                if self.check_collision(0, step, layout):
                    break
                self.rect.y += step
            self.vel_y = 0
            self.on_ground = True
