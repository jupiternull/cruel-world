"""Deterministic headless capstone verification with real movement and attacks."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import json
import random
import tempfile
from pathlib import Path
import pygame
from main import Game
from underworld import ENCOUNTERS, AREA_NAMES


def capture(output=Path('artifacts/underworld')):
    output.mkdir(parents=True, exist_ok=True)
    random.seed(902)
    seen = []
    with tempfile.TemporaryDirectory() as directory:
        game = Game(Path(directory) / 'save.json')
        game.reset_game('warrior')
        game.launch_expedition(3, debug=True)
        for wave, actors in enumerate(ENCOUNTERS, 1):
            game.state.wave = wave
            game.state.phase = 'combat'
            game.state.spawned = 0
            game.enemies = []
            game.sources = []
            hero = game.knight
            game.features.reposition(game, (game.world.data['zones'][wave - 1] - 80, 560))
            hero.health = hero.max_health
            hero.on_ground = True
            for actor in actors:
                game.state.spawned += 1
                game.spawn(wave == 8)
                seen.append(game.enemies[-1].actor)
                game.enemies[-1].rect.x += (game.state.spawned - 1) * 90
            for _ in range(12):
                game.tick({pygame.K_d: True})
            hero.attack()
            for _ in range(24):
                game.tick({})
            game.camera.update(hero.rect)
            game.draw()
            pygame.image.save(game.screen, output / f'{wave:02}-{AREA_NAMES[wave - 1].lower().replace(" ", "-")}.png')
            # Finish authored encounters deterministically through real hero damage sources.
            from projectile import DamageSource
            for enemy in game.enemies:
                source = DamageSource(enemy.rect, enemy.max_health * 4, 'hero', 1, kind='wave')
                assert source.hit(enemy)
            for _ in range(130):
                game.tick({})
            assert wave in game.expedition.wave_claims, wave
            for name, required in (('seal0', 1), ('seal1', 4), ('seal2', 7)):
                if wave == required:
                    game.features.reposition(game, (game.features.objects[name][0], 560))
                    assert game.features.interact(game)
        game.features.update(game)
        assert game.features.exit_ready and game.campaign.exit_open
        game.features.reposition(game, (game.features.objects['testament'][0], 560))
        assert game.features.interact(game)
        game.features.reposition(game, game.world.exit.midbottom)
        game.camera.update(game.knight.rect)
        game.draw()
        pygame.image.save(game.screen, output / '09-open-exit.png')
        game.tick({})
        for _ in range(100):
            game.tick({})
        assert game.mode == 'results' and game.campaign.complete
        game.draw()
        pygame.image.save(game.screen, output / '10-capstone-results.png')
        (output / 'verification.json').write_text(json.dumps({'actors': seen, 'seals': sorted(game.features.claimed),
            'complete': game.campaign.complete, 'score': game.state.score}, indent=2) + '\n')
    pygame.quit()
    return seen


if __name__ == '__main__':
    capture()
