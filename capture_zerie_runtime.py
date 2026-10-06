"""Render Zerie Soldier and Orc samples through the live Cruel World expedition renderer."""
import argparse
import os
from pathlib import Path
import tempfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame

from main import Game
from zerie_asset_proof import FRAME_SIZE, SAMPLES, character_directory


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_ROOT / 'artifacts' / 'zerie'
CANDIDATE_SCALES = (2.0, 2.5, 3.0)
PLAYER_STATES = {
    'Idle': 'Idle', 'Run': 'Walk', 'Attack1': 'Attack01', 'Attack2': 'Attack02',
    'Attack3': 'Attack03', 'Jump': 'Walk', 'Fall': 'Walk', 'Hit': 'Hurt',
    'Death': 'Death', 'Roll': 'Walk', 'Block': 'Idle', 'BlockIdle': 'Idle',
    'WallSlide': 'Walk', 'LedgeGrab': 'Idle',
}
ENEMY_STATES = {
    'Idle': 'Idle', 'Walk': 'Walk', 'Attack': 'Attack01', 'Take Hit': 'Hurt',
    'Death': 'Death',
}


def sample(sample_id):
    return next(item for item in SAMPLES if item['id'] == sample_id)


def source_path(asset_root, sample_id, animation):
    actor = sample(sample_id)
    return character_directory(asset_root, actor) / f"{actor['name']}_{animation}.png"


def load_sheet_frames(asset_root, sample_id, animation, scale):
    sheet = pygame.image.load(str(source_path(asset_root, sample_id, animation))).convert_alpha()
    count = sheet.get_width() // FRAME_SIZE
    size = round(FRAME_SIZE * scale)
    return [pygame.transform.scale_by(
        sheet.subsurface((index * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE)), scale
    ) if size == FRAME_SIZE else pygame.transform.scale(
        sheet.subsurface((index * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE)), (size, size)
    ) for index in range(count)]


def frames_and_anchor(asset_root, sample_id, states, scale):
    loaded = {}
    for source_animation in set(states.values()):
        loaded[source_animation] = load_sheet_frames(asset_root, sample_id, source_animation, scale)
    frames = {state: loaded[source_animation] for state, source_animation in states.items()}
    bounds = [frame.get_bounding_rect() for group in frames.values() for frame in group]
    visible = bounds[0].copy()
    for bound in bounds[1:]:
        visible.union_ip(bound)
    return frames, visible


def apply_zerie_standins(game, asset_root, scale):
    player_frames, player_anchor = frames_and_anchor(asset_root, 'soldier', PLAYER_STATES, scale)
    enemy_frames, enemy_anchor = frames_and_anchor(asset_root, 'orc', ENEMY_STATES, scale)

    hero = game.knight
    hero.frames = hero.states = player_frames
    hero.anchor = player_anchor
    hero.set_state('Attack2', True)
    hero.current_frame_idx = min(3, len(hero.current_frames) - 1)
    hero.image = hero.current_frames[hero.current_frame_idx]

    game.spawn()
    enemy = game.enemies[-1]
    enemy.frames = enemy_frames
    enemy.current_frames = enemy_frames['Take Hit']
    enemy.state = 'Take Hit'
    enemy.current_frame_idx = min(1, len(enemy.current_frames) - 1)
    enemy.image = enemy.current_frames[enemy.current_frame_idx]
    enemy.anchor = enemy_anchor
    enemy.hit_stun = 20
    enemy.rect.midbottom = (700, 560)
    return {'player': player_anchor, 'enemy': enemy_anchor}


def setup_combat(game, asset_root, scale):
    game.reset_game('warrior')
    game.launch_expedition(0, debug=True)
    game.knight.rect.midbottom = (500, 560)
    game.camera.update(game.knight.rect)
    game.state.phase = 'combat'
    game.state.wave = 1
    anchors = apply_zerie_standins(game, asset_root, scale)
    game.draw()
    return game.screen.copy(), anchors


def label(surface, text, position):
    font = pygame.font.Font(None, 26)
    rendered = font.render(text, True, (220, 229, 222))
    panel = pygame.Rect(position[0] - 7, position[1] - 4, rendered.get_width() + 14, rendered.get_height() + 8)
    pygame.draw.rect(surface, (10, 14, 26), panel)
    pygame.draw.rect(surface, (0, 204, 255), panel, 1)
    surface.blit(rendered, position)


def capture(output=DEFAULT_OUTPUT, assets_root=PROJECT_ROOT / 'assets' / 'vendor' / 'zerie'):
    output = Path(output)
    assets_root = Path(assets_root)
    output.mkdir(parents=True, exist_ok=True)
    gameplay_path = output / 'soldier-orc-gameplay.png'
    comparison_path = output / 'soldier-orc-scale-comparison.png'
    pygame.init()
    try:
        with tempfile.TemporaryDirectory() as directory:
            game = Game(Path(directory) / 'save.json')
            captures = []
            anchors = {}
            for scale in CANDIDATE_SCALES:
                screen, anchors[scale] = setup_combat(game, assets_root, scale)
                captures.append((scale, screen))
            pygame.image.save(captures[1][1], str(gameplay_path))

            panel_size = (400, 300)
            sheet = pygame.Surface((len(captures) * panel_size[0], panel_size[1] + 42))
            sheet.fill((10, 14, 26))
            for index, (scale, screen) in enumerate(captures):
                x = index * panel_size[0]
                sheet.blit(pygame.transform.scale(screen, panel_size), (x, 42))
                player = anchors[scale]['player']
                enemy = anchors[scale]['enemy']
                label(sheet, f'{scale:.2f}x  Soldier {player.height}px / Orc {enemy.height}px', (x + 10, 11))
            pygame.image.save(sheet, str(comparison_path))
    finally:
        pygame.quit()
    return gameplay_path, comparison_path


def capture_playable(output):
    """Capture production frames through Game.draw and Hero.draw, without stand-ins."""
    from entities.hero import CLASSES
    from campaign import ENVIRONMENTS
    from camera import Camera
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    pygame.init()
    try:
        with tempfile.TemporaryDirectory() as directory:
            game = Game(Path(directory) / 'save.json')
            for selected in range(3):
                game.change_mode('class')
                game.selection = selected
                game.draw()
                path = output / f'class-selection-{selected + 1}.png'
                pygame.image.save(game.screen, str(path))
                paths.append(path)
            realm_shots = []
            for index, environment in enumerate(ENVIRONMENTS):
                game.reset_game(list(CLASSES)[index])
                game.launch_expedition(index, debug=True)
                game.knight.rect.midbottom = (500, 560)
                game.knight.set_state('Attack1', True)
                game.knight.current_frame_idx = 2
                game.knight.image = game.knight.current_frames[2]
                game.state.phase = 'combat'
                game.state.wave = 1
                for number, _ in enumerate(environment['enemy_roster'], 1):
                    game.state.spawned = number
                    game.spawn()
                    enemy = game.enemies[-1]
                    enemy.rect.midbottom = (600 + number * 65, 560)
                    enemy.facing_right = False
                    enemy.set_state('Attack')
                    enemy.current_frame_idx = 2
                    enemy.image = enemy.current_frames[2]
                game.camera.update(game.knight.rect)
                game.draw()
                path = output / f"{environment['id']}-faction.png"
                pygame.image.save(game.screen, str(path))
                paths.append(path)
                realm_shots.append(game.screen.copy())
            sheet = pygame.Surface((1200, 900))
            sheet.fill((10, 14, 26))
            for index, shot in enumerate(realm_shots):
                sheet.blit(pygame.transform.scale(shot, (400, 300)), (index * 400, 600))
            game.change_mode('class')
            game.draw()
            sheet.blit(game.screen, (200, 0))
            path = output / 'playable-contact-sheet.png'
            pygame.image.save(sheet, str(path))
            paths.append(path)
            states = ('Idle', 'Run', 'Jump', 'Fall', 'Attack1', 'Attack2', 'Attack3', 'Hit', 'Death', 'Roll', 'Block', 'WallSlide')
            sheet = pygame.Surface((len(states) * 220, 3 * 230))
            sheet.fill((10, 14, 26))
            for row, class_id in enumerate(CLASSES):
                game.reset_game(class_id)
                hero = game.knight
                for column, state in enumerate(states):
                    if state not in hero.frames:
                        continue
                    hero.set_state(state, True)
                    hero.current_frame_idx = len(hero.current_frames) // 2
                    hero.image = hero.current_frames[hero.current_frame_idx]
                    tile = pygame.Surface((220, 230))
                    tile.fill((10, 14, 26))
                    pygame.draw.line(tile, (76, 91, 104), (0, 196), (220, 196))
                    hero.rect.midbottom = (110, 196)
                    hero.draw(tile, Camera(800))
                    label(tile, f'{hero.stats["name"]}: {state}', (8, 12))
                    sheet.blit(tile, (column * 220, row * 230))
            path = output / 'player-actions.png'
            pygame.image.save(sheet, str(path))
            paths.append(path)
    finally:
        pygame.quit()
    return paths


def main():
    parser = argparse.ArgumentParser(description='Capture Zerie Soldier and Orc samples in the Cruel World renderer.')
    parser.add_argument('--output', default=str(DEFAULT_OUTPUT))
    parser.add_argument('--assets-root', default=str(PROJECT_ROOT / 'assets' / 'vendor' / 'zerie'))
    parser.add_argument('--playable', action='store_true', help='Capture the integrated Pack 01 playable slice')
    args = parser.parse_args()
    if args.playable:
        for path in capture_playable(args.output):
            print(path.resolve())
        return
    gameplay, comparison = capture(args.output, args.assets_root)
    print(gameplay.resolve())
    print(comparison.resolve())


if __name__ == '__main__':
    main()
