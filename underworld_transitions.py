"""Authored seam occluders and their matching traversal surfaces."""
import random
import pygame

TYPES = ('fortress tunnel', 'furnace scaffold', 'descending portcullis',
         'root breach', 'chain lift shaft', 'ruined vault', 'Pyre gate')


class Transition:
    def __init__(self, index):
        self.index = index
        self.x = (index + 1) * 1280
        self.kind = TYPES[index]
        self.climb = index in (1, 4)
        self.deck_y = 320 if self.climb else 560
        self.bounds = pygame.Rect(self.x - 224, -120, 448, 840)
        self.opening = pygame.Rect(self.x - 176, self.deck_y - 152, 352, 152)
        self.platforms = [pygame.Rect(self.x - 192, self.deck_y, 384, 16)] if self.climb else []
        self.ladders = [pygame.Rect(self.x + offset, self.deck_y, 24, 560 - self.deck_y)
                        for offset in (-184, 160)] if self.climb else []
        self.blockers = [pygame.Rect(self.x - 128, -10000, 256, 20000)]
        self.entries = (self.x - 168, self.x + 168)
        self.prompt = "E - " + ("Use furnace passage" if index == 1 else
                                "Use chain lift" if index == 4 else "Enter " + self.kind)

    def entry_direction(self, hero):
        if not hero.alive or abs(hero.rect.bottom - self.deck_y) > 12:
            return None
        for side, x in zip((1, -1), self.entries):
            if abs(hero.rect.centerx - x) <= 46 and side * (hero.rect.centerx - self.x) < 0:
                return side
        return None

    def build_art(self, stone):
        # Work on a 2px grid; only nearest-neighbour scaling preserves the source pixels.
        rng = random.Random(871 + self.index)
        art = pygame.Surface((224, 420), pygame.SRCALPHA)
        palette = ((47, 35, 38), (60, 39, 32), (37, 31, 40), (45, 33, 29),
                   (39, 32, 38), (47, 40, 44), (43, 27, 33))[self.index]
        tile = pygame.transform.scale(stone, (32, 12)).copy()
        tile.fill((*palette, 255), special_flags=pygame.BLEND_RGBA_MULT)
        tile.fill(tuple(c // 2 for c in palette), special_flags=pygame.BLEND_RGB_ADD)
        for y in range(0, 420, 12):
            inset = rng.choice((0, 3, 6, 9))
            pygame.draw.rect(art, palette, (inset, y, 224 - inset * 2, 12))
            for x in range(inset - (16 if y // 12 % 2 else 0), 224 - inset, 32):
                art.blit(tile, (x, y))
                shade = rng.randrange(-5, 12)
                face = tuple(max(0, c + shade) for c in palette)
                pygame.draw.polygon(art, face, [(x+2,y+2), (x+26,y+2),
                                               (x+29,y+8), (x+5,y+9)])
                pygame.draw.line(art, tuple(max(0,c-12) for c in face),
                                 (x+5,y+10), (x+29,y+10), 1)
                color = tuple(min(255, c + rng.randrange(8, 24)) for c in palette)
                pygame.draw.line(art, color, (max(inset, x), y), (min(224-inset, x+29), y), 1)
                if rng.random() < .4:
                    pygame.draw.line(art, (23, 18, 24), (x+12, y+3), (x+17, y+10), 2)
        floor = (self.deck_y + 120) // 2
        top = floor - 76
        # A dark, fully opaque interior hides the wallpaper even through the passage.
        contours = (
            [(24,floor), (24,top+24), (48,top), (176,top), (200,top+24), (200,floor)],
            [(24,floor), (24,top+8), (200,top+8), (200,floor)],
            [(24,floor), (24,top+12), (38,top), (186,top), (200,top+12), (200,floor)],
            [(24,floor), (30,top+32), (46,top+18), (65,top+22), (89,top),
             (138,top+6), (169,top+20), (188,top+16), (200,floor)],
            [(24,floor), (24,top), (200,top), (200,floor)],
            [(24,floor), (24,top+31), (57,top+9), (80,top+14), (111,top-5),
             (165,top+6), (200,top+29), (200,floor)],
            [(24,floor), (24,top+28), (69,top+8), (112,top-16),
             (155,top+8), (200,top+28), (200,floor)],
        )
        contour = contours[self.index]
        pygame.draw.polygon(art, (16, 13, 21), contour)
        for depth in range(4):
            c = (35-depth*4, 27-depth*3, 33-depth*3)
            points = [(x + (1 if x < 112 else -1)*depth*4,
                       y + depth*3 if y < floor else y) for x,y in contour]
            pygame.draw.lines(art, c, False, points, 3)
        for x in range(24, 201, 16):
            pygame.draw.rect(art, (76, 52, 43), (x, floor-4, 14, 4))
        # Outer buttresses frame a wide corridor without obstructing the hero.
        for x in (15, 202):
            for y in range(top+22, floor, 10):
                pygame.draw.rect(art, (81, 57, 47), (x, y, 8, 9))
                pygame.draw.line(art, (116, 76, 51), (x, y), (x+7, y), 1)
        if self.index == 0:
            for x in range(18, 210, 24):
                pygame.draw.rect(art, (74, 52, 47), (x, top-38, 14, 20))
            pygame.draw.rect(art, (87, 58, 43), (15, top-18, 195, 7))
        elif self.index == 1:
            for y in range(28, top, 30):
                pygame.draw.line(art, (99, 62, 39), (20, y), (204, y+28), 4)
                pygame.draw.line(art, (42, 31, 29), (20, y+5), (204, y+33), 2)
            for x in (54, 112, 170):
                pygame.draw.rect(art, (100, 44, 31), (x-8, floor+22, 16, 74))
                pygame.draw.rect(art, (241, 109, 36), (x-4, floor+27, 8, 62))
                for y in range(floor+30, floor+90, 12):
                    pygame.draw.line(art, (39, 29, 31), (x-9, y), (x+9, y), 3)
        elif self.index == 2:
            for x in range(40, 190, 15):
                pygame.draw.line(art, (108, 83, 61), (x, top-65), (x, top+18), 3)
                pygame.draw.polygon(art, (143, 95, 56), [(x-3, top+15), (x+3, top+15), (x, top+23)])
            for y in (top-48, top-24):
                pygame.draw.line(art, (67, 48, 42), (30, y), (196, y), 5)
        elif self.index == 3:
            for n in range(13):
                x = rng.randrange(32, 193)
                end = 14 if n % 2 else 210
                points = [(x, 0), (x+12, 66), (x-18, top-32), (end, top+20), (end, floor+15)]
                pygame.draw.lines(art, (24, 19, 23), False, points, 12)
                pygame.draw.lines(art, (86, 57, 42), False, points, 5)
                pygame.draw.lines(art, (118, 73, 46), False, points, 1)
        elif self.index == 4:
            for x in (35, 74, 150, 189):
                for y in range(0, floor-5, 8):
                    pygame.draw.rect(art, (109, 84, 65), (x, y, 4, 6), 1)
            pygame.draw.rect(art, (89, 58, 40), (24, floor-3, 177, 7))
            pygame.draw.circle(art, (119, 80, 48), (112, top-30), 18, 4)
            pygame.draw.line(art, (119, 80, 48), (94, top-30), (130, top-30), 3)
        elif self.index == 5:
            for n in range(9):
                x = 25+n*20
                y = top-15-abs(4-n)*6
                pygame.draw.polygon(art, (100, 77, 64), [(x,y), (x+17,y-7), (x+21,y+12), (x+3,y+18)])
            for x in (8, 204):
                pygame.draw.polygon(art, (77, 61, 54), [(x, floor), (x-8, floor-27), (x+18, floor-17), (x+30, floor)])
        else:
            for x in (18, 200):
                pygame.draw.rect(art, (108, 58, 39), (x-6, top-100, 12, 102))
                pygame.draw.polygon(art, (156, 78, 39), [(x-12, top-99), (x, top-124), (x+12, top-99)])
            pygame.draw.circle(art, (139, 67, 39), (112, top-40), 30, 5)
            pygame.draw.polygon(art, (255, 156, 55), [(112, top-64), (100, top-32), (120, top-32), (112, top-12)], 3)
            # Retracted sealed leaves: the broken central seal opens a broad boss approach.
            for x in (28, 184):
                pygame.draw.rect(art, (78, 42, 35), (x, top+25, 12, 49))
                for y in range(top+30, top+71, 12):
                    pygame.draw.rect(art, (190, 103, 46), (x+3, y, 6, 5), 1)
        for x in (18, 204):
            pygame.draw.rect(art, (61, 40, 32), (x-3, top+38, 6, 12))
            pygame.draw.polygon(art, (221, 89, 30), [(x-5,top+38), (x,top+19), (x+5,top+38)])
            pygame.draw.rect(art, (255, 184, 76), (x-1, top+27, 2, 10))
        # Broken outer contours overlap the wallpapers, while the central seam stays opaque.
        for y in range(420):
            phase = y // 12
            inset = (phase * 7 + self.index * 3) % 13
            if self.index == 3:
                inset += (phase % 4) * 2
            art.fill((0, 0, 0, 0), (0, y, inset, 1))
            art.fill((0, 0, 0, 0), (224-inset, y, inset, 1))
        self.art = pygame.transform.scale(art, self.bounds.size)

    def draw(self, screen, camera):
        if self.bounds.right > camera.x and self.bounds.left < camera.x + 800:
            screen.blit(self.art, (self.bounds.left-camera.x, self.bounds.top))


TRANSITIONS = tuple(Transition(i) for i in range(7))


def near_transition(x, width=0):
    return any(x < t.bounds.right + 24 and x + width > t.bounds.left - 24 for t in TRANSITIONS)
