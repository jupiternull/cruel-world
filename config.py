import os

GAME_CONFIG = {
    'WIDTH': 800,
    'HEIGHT': 600,
    'FPS': 60,
    'TILE_SIZE': 16,
    'PLAYER_SPEED': 5,
    'GRAVITY': 1,
    'JUMP_VELOCITY': -15,
    'SOLID_TILES': [1, 2],
    'INITIAL_SPAWN_RATE': 180,
    'MIN_SPAWN_RATE': 30,
    'PLAYER_MAX_HEALTH': 100,
    'WAVE_DURATION': 1800,
    'POWERUP_SPAWN_CHANCE': 0.1,
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
SPRITES_DIR = os.path.join(ASSETS_DIR, 'sprites')
TILESETS_DIR = os.path.join(ASSETS_DIR, 'tilesets')

BG_COLOR = (20, 14, 28)

# --- Knight collision box (120x80 frame, ~36x56 active area) ---
KNIGHT_FRAME_W = 120
KNIGHT_FRAME_H = 80
KNIGHT_COL_X_OFFSET = 42   # pixels from left edge of frame to collision box
KNIGHT_COL_Y_OFFSET = 20   # pixels from top edge of frame to collision box
KNIGHT_COL_W = 36
KNIGHT_COL_H = 56

# --- Skeleton collision box (96x64 frame, ~30x50 active area) ---
SKEL_FRAME_W = 96
SKEL_FRAME_H = 64
SKEL_COL_X_OFFSET = 33
SKEL_COL_Y_OFFSET = 10
SKEL_COL_W = 30
SKEL_COL_H = 50

# --- Knight ability params ---
DASH_SPEED = 12
DASH_COOLDOWN = 90       # frames
ROLL_SPEED = 7
ROLL_COOLDOWN = 75        # frames
ROLL_INVULN_FRAMES = 36   # i-frames during roll
SLIDE_SPEED = 10
SLIDE_FRICTION = 0.85     # multiplier per frame

# --- Combo system ---
COMBO_WINDOW = 25         # frames after attack ends to chain next hit
ATTACK1_DAMAGE = 10
ATTACK2_DAMAGE = 15
COMBO_DAMAGE = 25

# --- Per-animation frame delays (ms) ---
KNIGHT_FRAME_DELAYS = {
    'IDLE': 100,
    'RUN': 80,
    'JUMP': 80,
    'JUMP_FALL_BETWEEN': 100,
    'FALL': 100,
    'ATTACK': 80,
    'ATTACK2': 70,
    'ATTACK_COMBO': 60,
    'CROUCH_FULL': 80,
    'CROUCH': 100,
    'CROUCH_WALK': 100,
    'CROUCH_ATTACK': 80,
    'DASH': 60,
    'ROLL': 50,
    'SLIDE_FULL': 60,
    'SLIDE': 80,
    'SLIDE_TRANSITION_END': 80,
    'HIT': 200,
    'DEATH': 100,
    'TURN_AROUND': 60,
}

SKEL_FRAME_DELAYS = {
    'IDLE': 120,
    'WALK': 100,
    'ATTACK1': 80,
    'ATTACK2': 80,
    'HURT': 100,
    'DIE': 80,
}

# --- Skeleton stats ---
SKEL_WHITE_HP = 2
SKEL_WHITE_SPEED = 2.0
SKEL_WHITE_DAMAGE = 8
SKEL_WHITE_ATTACK_RANGE = 45
SKEL_WHITE_ATTACK_COOLDOWN = 75

SKEL_YELLOW_HP = 4
SKEL_YELLOW_SPEED = 1.5
SKEL_YELLOW_DAMAGE = 15
SKEL_YELLOW_ATTACK_RANGE = 50
SKEL_YELLOW_ATTACK_COOLDOWN = 90
