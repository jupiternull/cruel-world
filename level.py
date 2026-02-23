import pygame
from config import GAME_CONFIG


# Tile indices from the dungeon tileset (tilesetv3.png, 17 cols wide)
# 0 = empty (not drawn), 1/2 = solid floor tiles
EMPTY = 0
FLOOR_A = 1
FLOOR_B = 2


class TileMap:
    def __init__(self, layout, tiles):
        self.layout = layout
        self.tiles = tiles

    def draw(self, screen):
        ts = GAME_CONFIG['TILE_SIZE']
        for row_idx, row in enumerate(self.layout):
            for col_idx, tile_idx in enumerate(row):
                if tile_idx != EMPTY and tile_idx < len(self.tiles):
                    screen.blit(self.tiles[tile_idx], (col_idx * ts, row_idx * ts))


class Torch:
    def __init__(self, x, y, frames):
        self.x = x
        self.y = y
        self.frames = frames
        self.current_frame = 0
        self.animation_timer = 0
        self.frame_delay = 150

    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.frame_delay:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)

    def draw(self, screen):
        screen.blit(self.frames[self.current_frame], (self.x, self.y))


def _add_platform(layout, row, col_start, col_end):
    """Add a 2-tile-thick platform to the layout."""
    for col in range(col_start, col_end + 1):
        layout[row][col] = FLOOR_A
        layout[row + 1][col] = FLOOR_B


GROUND_ROW = 35


def ground_y():
    """Y pixel coordinate of the ground surface (top of ground tiles)."""
    return GROUND_ROW * GAME_CONFIG['TILE_SIZE']


def build_layout():
    """Build a 3-tier platformer level layout."""
    cols = GAME_CONFIG['WIDTH'] // GAME_CONFIG['TILE_SIZE']   # 50
    rows = GAME_CONFIG['HEIGHT'] // GAME_CONFIG['TILE_SIZE']  # 37

    layout = [[EMPTY] * cols for _ in range(rows)]

    # Ground floor (full width) — rows 35-36
    _add_platform(layout, GROUND_ROW, 0, cols - 1)

    # Tier 1 — two platforms, 6 tiles above ground (rows 29-30)
    _add_platform(layout, 29, 3, 16)
    _add_platform(layout, 29, 33, 46)

    # Tier 2 — center bridge (rows 23-24)
    _add_platform(layout, 23, 15, 34)

    # Tier 3 — two high perches (rows 17-18)
    _add_platform(layout, 17, 5, 15)
    _add_platform(layout, 17, 35, 45)

    return layout


def place_torches(layout, torch_frames):
    """Place torches at platform edges for atmosphere."""
    ts = GAME_CONFIG['TILE_SIZE']
    torches = []

    # Find left and right edges of each platform
    for row_idx, row in enumerate(layout):
        for col_idx in range(len(row)):
            if row[col_idx] in GAME_CONFIG['SOLID_TILES']:
                # Left edge: solid tile with empty (or OOB) to its left
                is_left_edge = (col_idx == 0 or row[col_idx - 1] not in GAME_CONFIG['SOLID_TILES'])
                # Right edge: solid tile with empty (or OOB) to its right
                is_right_edge = (col_idx == len(row) - 1 or row[col_idx + 1] not in GAME_CONFIG['SOLID_TILES'])

                if is_left_edge or is_right_edge:
                    # Place torch above the platform edge
                    tx = col_idx * ts - 2  # slight offset to center the 21px torch on 16px tile
                    ty = row_idx * ts - 27  # torch height (27px) above the tile
                    if ty > 0:
                        torches.append(Torch(tx, ty, torch_frames))

    return torches
