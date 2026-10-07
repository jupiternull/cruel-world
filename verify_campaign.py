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


def transition_keys(game, keys):
    hero = game.knight
    direction = int(keys.get(pygame.K_d, False)) - int(keys.get(pygame.K_a, False))
    if not direction:
        return keys
    for transition in getattr(game.features, 'transitions', ()):
        if direction * (transition.x - hero.rect.centerx) <= 0:
            continue
        entry = transition.entries[0 if direction > 0 else 1]
        if abs(hero.rect.centerx - entry) > 260:
            continue
        if transition.climb and hero.rect.bottom > transition.deck_y + 12:
            ladder = transition.ladders[0 if direction > 0 else 1]
            if hero.climbing is not None or abs(hero.rect.centerx - ladder.centerx) <= 8:
                return {pygame.K_w: True}
            return {pygame.K_d if hero.rect.centerx < ladder.centerx else pygame.K_a: True}
        if transition.entry_direction(hero) == direction:
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
            return {}
        return {pygame.K_d if hero.rect.centerx < entry else pygame.K_a: True}
    return keys


def combat_keys(game, tick):
    if game.transition:
        return {}
    hero = game.knight
    enemies = [enemy for enemy in game.enemies if enemy.alive and game.entity_active(enemy)]
    inactive = [enemy for enemy in game.enemies if enemy.alive and not game.entity_active(enemy)]
    if not enemies and inactive:
        target = inactive[0]
        return transition_keys(game, {pygame.K_d if target.rect.centerx > hero.rect.centerx else pygame.K_a: True})
    keys = {}
    features = game.features
    gate = getattr(features, 'gate', None)
    if gate and not features.gate_open and 1680 < hero.rect.centerx < 1904:
        if abs(hero.rect.centerx-1776) > 60:
            return {pygame.K_d if hero.rect.centerx < 1776 else pygame.K_a: True}
        if not features.gate_tick:
            game.expedition_interact()
        return {}
    barrier = next((p for p in getattr(features, 'breakables', ()) if p.kind == 'vine' and p.alive
                    and 0 < p.rect.centerx-hero.rect.centerx < 140), None)
    if barrier:
        hero.facing_right = True
        hero.aim = pygame.Vector2(1,0)
        if barrier.rect.left-hero.rect.right < 40 and tick % 12 == 0:
            hero.attack()
        approach = {pygame.K_d: True}
        if hero.on_ground and any(hero.rect.move(40,0).colliderect(rect) for rect in game.world.hazards):
            approach[pygame.K_SPACE] = tick % 2 == 0
        return approach

    if getattr(game.world, 'data', {}).get('id') == 'underworld':
        for name, required in (('seal0', 1), ('seal1', 4), ('seal2', 7)):
            if required in game.expedition.wave_claims and name not in features.claimed:
                x = features.objects[name][0]
                if abs(hero.rect.centerx - x) > 60:
                    direction = pygame.K_d if hero.rect.centerx < x else pygame.K_a
                    keys = {direction: True}
                    dx = 1 if direction == pygame.K_d else -1
                    if hero.on_ground and any(hero.rect.move(dx * 40, 0).colliderect(rect) for rect in game.world.hazards):
                        keys[pygame.K_SPACE] = tick % 2 == 0
                        if hero.class_id != 'warrior' and not hero.mobility_timer:
                            hero.dash(dx)
                    return transition_keys(game, keys)
                game.expedition_interact()
                return {}
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
    return transition_keys(game, keys)


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
            game.launch_expedition(0)
            screenshots = set()
            deaths = 0
            retry_locations = []
            for tick in range(limit):
                game.tick(combat_keys(game, tick))
                key = (game.campaign.index, game.state.wave)
                if (game.state.boss_wave and game.enemies and key not in screenshots
                        and game.knight.alive
                        and any(enemy.boss and enemy.windup for enemy in game.enemies)):
                    game.draw()
                    pygame.image.save(game.screen, output / f'{name}-region-{game.campaign.index + 1}.png')
                    screenshots.add(key)
                if game.mode == 'over' and not game.transition:
                    deaths += 1
                    retry_locations.append({'region': game.campaign.index + 1, 'wave': game.state.wave})
                    if deaths > 10:
                        break
                    game.selection = 0
                    game.activate()
                if game.mode == 'results' and not game.transition:
                    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
                if game.mode == 'camp' and not game.transition:
                    if not game.campaign.complete:
                        game.launch_expedition(game.campaign.index + 1)
                        continue
                    game.draw()
                    pygame.image.save(game.screen, output / f'{name}-victory.png')
                    break
            report.append({'class': name, 'ticks': tick + 1, 'deaths': deaths, 'region': game.campaign.index + 1,
                           'wave': game.state.wave, 'mode': game.mode, 'score': game.state.score,
                           'campaign_complete': game.campaign.complete, 'cleared_regions': list(game.save.cleared_regions),
                           'retry_locations': retry_locations, 'boss_screenshots': len(screenshots)})
            print(f'{name}: {game.mode}, region {game.campaign.index + 1}, wave {game.state.wave}, {deaths} retries', flush=True)
        game.change_mode('class')
        game.draw()
        pygame.image.save(game.screen, output / 'class-selection.png')
    if all(row['boss_screenshots'] == 4 for row in report):
        sheet = pygame.Surface((1600, 900))
        for row, name in enumerate(CLASSES):
            for column in range(4):
                shot = pygame.image.load(output / f'{name}-region-{column + 1}.png')
                sheet.blit(pygame.transform.scale(shot, (400, 300)), (column * 400, row * 300))
        pygame.image.save(sheet, output / 'campaign-contact-sheet.png')
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    pygame.quit()
    return all(row['mode'] == 'camp' and row['campaign_complete'] and row['cleared_regions'] == [0, 1, 2, 3] and row['deaths'] <= 10 and row['boss_screenshots'] == 4 for row in report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bounded campaign bot using ordinary combat and checkpoint retries')
    parser.add_argument('--output', type=Path, default=Path('artifacts'))
    parser.add_argument('--ticks', type=int, default=60000)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.output, args.ticks) else 1)
