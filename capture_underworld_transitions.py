"""Seven deterministic, section-isolated headless traversal captures."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import json
import random
import tempfile
from pathlib import Path
import pygame
from main import Game


def capture(output=Path('artifacts/underworld-transitions')):
    output.mkdir(parents=True, exist_ok=True)
    random.seed(871)
    records = []
    with tempfile.TemporaryDirectory() as directory:
        game = Game(Path(directory) / 'save.json')
        game.reset_game('warrior')
        game.launch_expedition(3, debug=True)
        game.state.phase = 'travel'
        game.features.notice_timer = 0
        hero = game.knight
        for transition in game.features.transitions:
            for direction, side in ((1, 'forward'), (-1, 'backward')):
                game.features.passage_cooldown = 0
                game.features.reposition(game, (transition.entries[0 if direction == 1 else 1], transition.deck_y))
                hero.vel_y = 0
                hero.on_ground = True
                hero.invulnerable = 0
                hero.hit_flash = 0
                hero.facing_right = direction > 0
                game.camera.update(hero.rect)
                for stage in ('approach', 'emergence'):
                    if stage == 'emergence':
                        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
                        assert game.transition and game.transition.get('passage')
                        for _ in range(30):
                            game.tick({})
                    game.features.ticks = 120
                    game.draw()
                    left = game.features.active_section * 1280
                    assert left <= game.camera.x <= left + 1280 - game.camera.width
                    assert game.features.rendered_sections == (game.features.active_section,)
                    name = f'{transition.index+1:02}-{transition.kind.replace(" ", "-")}-{side}-{stage}.png'
                    pygame.image.save(game.screen, output / name)
                    records.append({'boundary': transition.x, 'type': transition.kind,
                                    'direction': direction, 'stage': stage,
                                    'prompt': transition.prompt if stage == 'approach' else None,
                                    'hero_feet': list(hero.rect.midbottom),
                                    'camera': game.camera.x, 'viewport': [game.camera.x, game.camera.x + game.camera.width],
                                    'active_section': game.features.active_section,
                                    'rendered_sections': list(game.features.rendered_sections), 'capture': name})
        (output / 'verification.json').write_text(json.dumps(records, indent=2) + '\n')
    pygame.quit()
    return records


if __name__ == '__main__':
    capture()
