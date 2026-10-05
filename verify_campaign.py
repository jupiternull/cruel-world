import argparse
import json
import os
import random
import tempfile
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from main import Game
from entities.hero import CLASSES


def combat_keys(game, tick):
    hero = game.knight
    enemies = [enemy for enemy in game.enemies if enemy.alive]
    keys = {}
    if enemies:
        target = min(enemies, key=lambda enemy: abs(enemy.rect.centerx - hero.rect.centerx))
        distance = target.rect.centerx - hero.rect.centerx
        if not hero.mobility_timer:
            hero.facing_right = distance >= 0
        high_target = target.rect.bottom < hero.rect.centery
        if not target.flying and target.rect.bottom < hero.rect.bottom - 110:
            climbs = [zone for zone in game.world.climbables if zone.top <= target.rect.bottom]
            if climbs:
                zone = min(climbs, key=lambda zone: abs(zone.centerx - hero.rect.centerx) + abs(zone.centerx - target.rect.centerx))
                if abs(hero.rect.centerx - zone.centerx) > 12 and hero.climbing is None:
                    keys[pygame.K_d if zone.centerx > hero.rect.centerx else pygame.K_a] = True
                else:
                    keys[pygame.K_w] = True
                return keys
        desired_range = 48 if hero.class_id == 'warrior' or target.flying or high_target else 180
        if abs(distance) > desired_range:
            keys[pygame.K_d if distance > 0 else pygame.K_a] = True
        elif hero.class_id != 'warrior' and not target.flying and abs(distance) < 140:
            keys[pygame.K_a if distance > 0 else pygame.K_d] = True
        needs_jump = target.rect.bottom < hero.rect.centery + 15 and hero.on_ground
        if needs_jump:
            keys[pygame.K_SPACE] = tick % 2 == 0
        if 0 < target.windup <= 20 and target.telegraph and hero.rect.colliderect(target.telegraph):
            if hero.class_id == 'warrior':
                hero.secondary()
            else:
                hero.dash(-1 if distance > 0 else 1)
            keys[pygame.K_SPACE] = tick % 2 == 0
        if hero.class_id != 'warrior' or not keys.get(pygame.K_SPACE):
            if tick % 12 == 0:
                hero.attack()
            if tick % 30 == 0 and abs(distance) < 350:
                hero.secondary()
    else:
        keys[pygame.K_d] = True
        if any(hero.rect.move(36, 0).colliderect(rect) for rect in game.world.hazards):
            keys[pygame.K_SPACE] = True
    dx = int(keys.get(pygame.K_d, False)) - int(keys.get(pygame.K_a, False))
    if hero.on_ground and any(hero.rect.move(dx * 40, 0).colliderect(rect) for rect in game.world.hazards):
        keys[pygame.K_SPACE] = tick % 2 == 0
    return keys


def verify(output, limit):
    output.mkdir(parents=True, exist_ok=True)
    report = []
    with tempfile.TemporaryDirectory() as directory:
        game = Game(Path(directory) / 'save.json')
        game.save.settings['sound'] = False
        game.audio.apply_settings()
        for name in CLASSES:
            random.seed(0)
            game.reset_game(name)
            screenshots = set()
            deaths = 0
            retry_locations = []
            for tick in range(limit):
                game.tick(combat_keys(game, tick))
                key = (game.campaign.index, game.state.wave)
                if (game.state.wave == 3 and game.enemies and key not in screenshots
                        and game.knight.alive and game.knight.health >= game.knight.max_health * 0.4
                        and any(enemy.boss and enemy.windup for enemy in game.enemies)):
                    game.draw()
                    pygame.image.save(game.screen, output / f'{name}-region-{game.campaign.index + 1}.png')
                    screenshots.add(key)
                if game.mode == 'over':
                    deaths += 1
                    retry_locations.append({'region': game.campaign.index + 1, 'wave': game.state.wave})
                    if deaths > 5:
                        break
                    game.selection = 0
                    game.activate()
                if game.mode == 'victory':
                    game.draw()
                    pygame.image.save(game.screen, output / f'{name}-victory.png')
                    break
            report.append({'class': name, 'ticks': tick + 1, 'deaths': deaths, 'region': game.campaign.index + 1,
                           'wave': game.state.wave, 'mode': game.mode, 'score': game.state.score,
                           'retry_locations': retry_locations, 'boss_screenshots': len(screenshots)})
            print(f'{name}: {game.mode}, region {game.campaign.index + 1}, wave {game.state.wave}, {deaths} retries', flush=True)
        game.change_mode('class')
        game.draw()
        pygame.image.save(game.screen, output / 'class-selection.png')
    if all(row['boss_screenshots'] == 3 for row in report):
        sheet = pygame.Surface((1200, 900))
        for row, name in enumerate(CLASSES):
            for column in range(3):
                shot = pygame.image.load(output / f'{name}-region-{column + 1}.png')
                sheet.blit(pygame.transform.scale(shot, (400, 300)), (column * 400, row * 300))
        pygame.image.save(sheet, output / 'campaign-contact-sheet.png')
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    pygame.quit()
    return all(row['mode'] == 'victory' and row['deaths'] <= 5 and row['boss_screenshots'] == 3 for row in report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bounded campaign bot using ordinary combat and checkpoint retries')
    parser.add_argument('--output', type=Path, default=Path('artifacts'))
    parser.add_argument('--ticks', type=int, default=60000)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.output, args.ticks) else 1)
