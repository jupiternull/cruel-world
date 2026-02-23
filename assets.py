import os
import pygame
from config import ASSETS_DIR, SPRITES_DIR, TILESETS_DIR


def load_tileset(file_path, tile_width, tile_height):
    full_path = os.path.join(TILESETS_DIR, file_path)
    tileset = pygame.image.load(full_path).convert_alpha()
    tileset_width, tileset_height = tileset.get_size()
    tiles = []
    tiles_x = tileset_width // tile_width
    tiles_y = tileset_height // tile_height
    for y in range(tiles_y):
        for x in range(tiles_x):
            rect = pygame.Rect(x * tile_width, y * tile_height, tile_width, tile_height)
            tile = tileset.subsurface(rect)
            tiles.append(tile)
    return tiles


def load_sprite_sheet(file_path, num_frames, frame_w, frame_h, subfolder):
    full_path = os.path.join(SPRITES_DIR, subfolder, file_path)
    sprite_sheet = pygame.image.load(full_path).convert_alpha()
    frames = []
    for i in range(num_frames):
        rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
        frames.append(sprite_sheet.subsurface(rect))
    return frames


def tint_surface(surface, color):
    tinted = surface.copy()
    tinted.fill(color, special_flags=pygame.BLEND_MULT)
    return tinted


def load_torch_frames():
    full_path = os.path.join(TILESETS_DIR, 'spr_torch.png')
    sheet = pygame.image.load(full_path).convert_alpha()
    frame_width = 21
    frame_height = 27
    frames = []
    for i in range(4):
        rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
        frames.append(sheet.subsurface(rect))
    return frames


def _load_knight_frames():
    """Load all knight_v2 sprite sheets (120x80 per frame)."""
    W, H = 120, 80
    sub = 'knight_v2'
    return {
        'IDLE':              load_sprite_sheet('_Idle.png', 10, W, H, sub),
        'RUN':               load_sprite_sheet('_Run.png', 10, W, H, sub),
        'JUMP':              load_sprite_sheet('_Jump.png', 3, W, H, sub),
        'JUMP_FALL_BETWEEN': load_sprite_sheet('_JumpFallInbetween.png', 2, W, H, sub),
        'FALL':              load_sprite_sheet('_Fall.png', 3, W, H, sub),
        'ATTACK':            load_sprite_sheet('_Attack.png', 4, W, H, sub),
        'ATTACK2':           load_sprite_sheet('_Attack2.png', 6, W, H, sub),
        'ATTACK_COMBO':      load_sprite_sheet('_AttackCombo2hit.png', 10, W, H, sub),
        'CROUCH_FULL':       load_sprite_sheet('_CrouchFull.png', 3, W, H, sub),
        'CROUCH':            load_sprite_sheet('_Crouch.png', 1, W, H, sub),
        'CROUCH_WALK':       load_sprite_sheet('_CrouchWalk.png', 8, W, H, sub),
        'CROUCH_ATTACK':     load_sprite_sheet('_CrouchAttack.png', 4, W, H, sub),
        'DASH':              load_sprite_sheet('_Dash.png', 2, W, H, sub),
        'ROLL':              load_sprite_sheet('_Roll.png', 12, W, H, sub),
        'SLIDE_FULL':        load_sprite_sheet('_SlideFull.png', 4, W, H, sub),
        'SLIDE':             load_sprite_sheet('_Slide.png', 2, W, H, sub),
        'SLIDE_TRANSITION_END': load_sprite_sheet('_SlideTransitionEnd.png', 1, W, H, sub),
        'HIT':               load_sprite_sheet('_Hit.png', 1, W, H, sub),
        'DEATH':             load_sprite_sheet('_Death.png', 10, W, H, sub),
        'TURN_AROUND':       load_sprite_sheet('_TurnAround.png', 3, W, H, sub),
    }


def _load_skeleton_frames(color):
    """Load skeleton sprite sheets (96x64 per frame). color = 'White' or 'Yellow'."""
    W, H = 96, 64
    sub = f'skeleton_{color.lower()}'
    prefix = f'Skeleton_01_{color}_'
    return {
        'IDLE':    load_sprite_sheet(f'{prefix}Idle.png', 8, W, H, sub),
        'WALK':    load_sprite_sheet(f'{prefix}Walk.png', 10, W, H, sub),
        'ATTACK1': load_sprite_sheet(f'{prefix}Attack1.png', 10, W, H, sub),
        'ATTACK2': load_sprite_sheet(f'{prefix}Attack2.png', 9, W, H, sub),
        'HURT':    load_sprite_sheet(f'{prefix}Hurt.png', 5, W, H, sub),
        'DIE':     load_sprite_sheet(f'{prefix}Die.png', 13, W, H, sub),
    }


def load_all_assets():
    knight_frames = _load_knight_frames()
    skeleton_white_frames = _load_skeleton_frames('White')
    skeleton_yellow_frames = _load_skeleton_frames('Yellow')

    dungeon_tiles = load_tileset("tilesetv3.png", 16, 16)
    torch_frames = load_torch_frames()

    return {
        'knight_frames': knight_frames,
        'skeleton_white_frames': skeleton_white_frames,
        'skeleton_yellow_frames': skeleton_yellow_frames,
        'dungeon_tiles': dungeon_tiles,
        'torch_frames': torch_frames,
    }
