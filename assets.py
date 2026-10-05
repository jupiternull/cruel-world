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


KNIGHT_SOURCE_ROOT = 'heroes/hero_knight/Hero Knight/Sprites/HeroKnight'
KNIGHT_ROOT = 'heroes/knight'
KNIGHT_ANIMATIONS = {'Idle': ('Idle', 8), 'Run': ('Run', 10), 'Attack1': ('Attack1', 6),
                     'Attack2': ('Attack2', 6), 'Attack3': ('Attack3', 8), 'Jump': ('Jump', 3),
                     'Fall': ('Fall', 4), 'Hit': ('Hurt', 3), 'Death': ('DeathNoBlood', 10),
                     'Roll': ('Roll', 9), 'Block': ('Block', 5), 'BlockIdle': ('BlockIdle', 8),
                     'WallSlide': ('WallSlide', 5), 'LedgeGrab': ('LedgeGrab', 5)}
HERO_MANIFEST = {
    'warrior': (KNIGHT_ROOT, 100, 55, 2, {k: v[1] for k, v in KNIGHT_ANIMATIONS.items()}),
    'ranger': ('heroes/ranger', 200, 200, 1.5,
               {'Idle': 8, 'Run': 8, 'Jump': 2, 'Fall': 2, 'Attack1': 5, 'Attack2': 5,
                'Attack3': 7, 'Hit': 3, 'Death': 8}),
    'wizard': ('heroes/wizard/Wizard Pack', 231, 190, 1,
               {'Idle': 6, 'Run': 8, 'Jump': 2, 'Fall': 2, 'Attack1': 8, 'Attack2': 8, 'Hit': 4, 'Death': 7}),
}
MONSTER_MANIFEST = {
    'Goblin': {'Idle': 4, 'Run': 8, 'Attack': 8, 'Take Hit': 4, 'Death': 4},
    'Mushroom': {'Idle': 4, 'Run': 8, 'Attack': 8, 'Take Hit': 4, 'Death': 4},
    'Skeleton': {'Idle': 4, 'Walk': 4, 'Attack': 8, 'Shield': 4, 'Take Hit': 4, 'Death': 4},
    'Flying eye': {'Flight': 8, 'Attack': 8, 'Take Hit': 4, 'Death': 4},
}
FOREST_ROOT = 'environments/legacy_fantasy/Legacy-Fantasy - High Forest 2.3'
MOON_ROOT = 'environments/moon_graveyard/Final'


def image_asset(path):
    return pygame.image.load(os.path.join(ASSETS_DIR, path)).convert_alpha()


def validated_frames(directory, w, h, scale, animations):
    result = {}
    for name, count in animations.items():
        if directory == KNIGHT_ROOT:
            from pathlib import Path
            source, expected = KNIGHT_ANIMATIONS[name]
            files = sorted((Path(ASSETS_DIR) / directory / source).glob('*.png'),
                           key=lambda p: int(p.stem.rsplit('_', 1)[1]))
            if len(files) != count or count != expected:
                raise ValueError(f'{source}: expected {expected} ordered frames')
            frames = [pygame.image.load(str(p)).convert_alpha() for p in files]
            if any(f.get_size() != (w, h) for f in frames):
                raise ValueError(f'{source}: invalid frame dimensions')
            result[name] = [pygame.transform.scale(f, (w * scale, h * scale)) for f in frames]
            continue
        sheet = image_asset(directory + '/' + name + '.png')
        if sheet.get_size() != (w * count, h):
            raise ValueError(f'{directory}/{name}: expected {w * count}x{h}, got {sheet.get_size()}')
        result[name] = [pygame.transform.scale(sheet.subsurface((i * w, 0, w, h)), (w * scale, h * scale)) for i in range(count)]
    return result


def load_campaign_assets():
    from pathlib import Path
    missing = any(not (Path(ASSETS_DIR)/KNIGHT_ROOT/folder/f"HeroKnight_{({'BlockIdle': 'Block Idle', 'WallSlide': 'Slide', 'LedgeGrab': 'Grab Ledge'}).get(folder, folder)}_{i}.png").exists()
                  for folder,count in KNIGHT_ANIMATIONS.values() for i in range(count))
    if missing:
        from build_presentation import knight_assets
        knight_assets()
    heroes = {name: validated_frames(*spec) for name, spec in HERO_MANIFEST.items()}
    monsters = {name: validated_frames('enemies/luizmelo/Monsters_Creatures_Fantasy/' + name,
                                      150, 150, 2, animations) for name, animations in MONSTER_MANIFEST.items()}
    return {'heroes': heroes, 'monsters': monsters,
            'forest_bg': image_asset(FOREST_ROOT + '/Background/Background.png'),
            'forest_trees': image_asset(FOREST_ROOT + '/Trees/Dark-Tree.png').subsurface((0, 0, 112, 384)).copy(),
            'forest_tiles': image_asset(FOREST_ROOT + '/Assets/Tiles.png'),
            'interior': image_asset(FOREST_ROOT + '/Assets/Interior-01.png'),
            'buildings': image_asset(FOREST_ROOT + '/Assets/Buildings.png'),
            'rocks': image_asset(FOREST_ROOT + '/Assets/Props-Rocks.png'),
            'moon_bg': image_asset(MOON_ROOT + '/Background_0.png'),
            'moon_buildings': image_asset(MOON_ROOT + '/Background_1.png'),
            'moon_tiles': image_asset(MOON_ROOT + '/Tiles.png')}
