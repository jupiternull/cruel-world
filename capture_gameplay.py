"""Reproducible renderer captures: sequential gameplay, curated stills and evidence."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import hashlib
import json
import random
import tempfile
from pathlib import Path

import pygame
from PIL import Image, ImageDraw
from main import Game
from verify_campaign import combat_keys
from underworld import AREA_NAMES, ENCOUNTERS

# Each hard cut begins a new encounter; every frame inside it advances the game.
SEGMENTS = (
    ('warrior', 3, 1, 'cinder-dominion'),
    ('ranger', 0, 1, 'verdant-ruins'),
    ('wizard', 2, 1, 'moon-graveyard'),
    ('warrior', 3, 8, 'pyre-regent'),
)


def encounter(game, class_id, realm, wave):
    game.reset_game(class_id)
    game.launch_expedition(realm, debug=True)
    game.features.notice_timer = 0
    game.state.wave = wave
    game.state.phase = 'combat'
    game.state.spawned = 0
    center = game.world.data['zones'][wave - 1]
    position = (center - 160, 560)
    if realm == 3:
        game.features.reposition(game, position)
    else:
        game.knight.rect.midbottom = position
    game.camera.update(game.knight.rect)
    count = len(ENCOUNTERS[wave - 1]) if realm == 3 else 3
    for number in range(count):
        game.state.spawned += 1
        game.spawn(wave == 8)
        game.enemies[-1].rect.midbottom = (center + 90 + number * 75, 560)
    game.knight.on_ground = True


def capture(output=Path('docs/media/gameplay.gif')):
    random.seed(902)
    output.parent.mkdir(parents=True, exist_ok=True)
    evidence = Path('artifacts/gameplay')
    evidence.mkdir(parents=True, exist_ok=True)
    frames, metadata, samples = [], [], []
    with tempfile.TemporaryDirectory() as temporary:
        game = Game(Path(temporary) / 'save.json')
        for mode, filename in (('title', 'title'), ('class', 'class-selection'), ('victory', 'victory')):
            if mode == 'victory':
                game.campaign.index = 3
                game.state.score = 28650
                game.save.high_score = 28650
            game.change_mode(mode)
            game.draw()
            pygame.image.save(game.screen, output.parent / (filename + '.png'))
        for class_id, realm, wave, filename in SEGMENTS:
            encounter(game, class_id, realm, wave)
            positions, states, actions, hashes = set(), set(), set(), set()
            start = len(frames)
            for tick in range(240):
                hero = game.knight
                # Choreograph ordinary abilities while the same combat simulation runs.
                if tick in (0, 210) and hero.secondary():
                    actions.add('secondary')
                if 80 <= tick <= 110 and 'mobility' not in actions and hero.dash(-1):
                    actions.add('mobility')
                keys = combat_keys(game, tick)
                if tick < 12:
                    keys = {pygame.K_d: True}
                if tick % 24 == 0 and hero.attack():
                    actions.add('primary')
                game.tick(keys)
                assert game.mode == 'play' and hero.alive, (filename, tick)
                positions.add(hero.rect.x)
                states.add(hero.state)
                if tick % 5 == 0:
                    game.draw()
                    frame = Image.frombytes('RGB', (800, 600), pygame.image.tostring(game.screen, 'RGB'))
                    if tick == (20 if filename == 'cinder-dominion' else 60):
                        frame.save(output.parent / (filename + '.png'))
                    frame = frame.resize((640, 480), Image.Resampling.NEAREST)
                    frames.append(frame)
                    hashes.add(hashlib.sha256(frame.tobytes()).hexdigest())
                    if tick in (0, 60, 120, 180):
                        samples.append((filename, frame.copy()))
            assert len(positions) > 10 and len(hashes) > 40 and len(states) > 1
            assert 'secondary' in actions and 'Attack1' in states, (filename, actions, states)
            if class_id != 'warrior':
                assert 'mobility' in actions, (filename, actions)
            metadata.append({'class': class_id, 'realm': game.world.data['id'],
                             'area': AREA_NAMES[wave - 1] if realm == 3 else filename,
                             'frames': [start, len(frames) - 1], 'distinct_frames': len(hashes),
                             'positions': len(positions), 'states': sorted(states), 'actions': sorted(actions)})
        encounter(game, 'ranger', 1, 1)
        for tick in range(60):
            game.tick(combat_keys(game, tick))
        game.draw()
        pygame.image.save(game.screen, output.parent / 'sunken-keep.png')
    # A palette sampled across every scene retains both infernal reds and cool realms.
    palette_source = Image.new('RGB', (640, 480 * len(SEGMENTS)))
    for index in range(len(SEGMENTS)):
        palette_source.paste(frames[index * 48 + 24], (0, index * 480))
    palette = palette_source.quantize(colors=192)
    sequence = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    sequence[0].save(output, save_all=True, append_images=sequence[1:], duration=80,
                     loop=0, optimize=True, disposal=1)
    with Image.open(output) as gif:
        duration, distinct = 0, set()
        for index in range(gif.n_frames):
            gif.seek(index)
            duration += gif.info['duration']
            distinct.add(hashlib.sha256(gif.convert('RGB').tobytes()).hexdigest())
        metrics = {'frames': gif.n_frames, 'duration_ms': duration, 'size': list(gif.size),
                   'distinct_frames': len(distinct), 'bytes': output.stat().st_size, 'loop': gif.info['loop']}
    assert metrics['frames'] == 192 and len(distinct) > 180
    assert metrics['size'] == [640, 480] and 10000 <= duration <= 18000
    assert metrics['bytes'] < 10_000_000
    sheet = Image.new('RGB', (1280, 4 * 252), '#100e14')
    draw = ImageDraw.Draw(sheet)
    for index, (name, frame) in enumerate(samples):
        x, y = index % 4 * 320, index // 4 * 252
        sheet.paste(frame.resize((320, 240)), (x, y + 12))
        draw.text((x + 4, y), name, fill='white')
    sheet.save(evidence / 'contact-sheet.png')
    (evidence / 'metadata.json').write_text(json.dumps({'metrics': metrics, 'segments': metadata}, indent=2) + '\n')
    print(json.dumps(metrics, indent=2))
    pygame.quit()


if __name__ == '__main__':
    capture()
