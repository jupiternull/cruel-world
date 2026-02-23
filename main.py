import pygame
import sys
import random

from config import GAME_CONFIG, BG_COLOR, SKEL_FRAME_H
from assets import load_all_assets
from level import build_layout, TileMap, place_torches, ground_y
from game_state import GameState
from entities import Knight, Skeleton, YellowSkeleton, Particle, PowerUp
from ui import init_fonts, draw_ui, draw_game_over

pygame.init()
screen = pygame.display.set_mode((GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT']))
pygame.display.set_caption("Cruel World")
clock = pygame.time.Clock()

fonts = init_fonts()
assets = load_all_assets()
layout = build_layout()
tilemap = TileMap(layout, assets['dungeon_tiles'])
torches = place_torches(layout, assets['torch_frames'])


def reset_game():
    spawn_y = ground_y() - 80  # knight frame height
    knight = Knight(100, spawn_y, assets['knight_frames'])
    return knight, [], [], [], 0, GameState()


knight, enemies, particles, powerups, spawn_timer, game_state = reset_game()

running = True
while running:
    dt = clock.tick(GAME_CONFIG['FPS'])

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                knight.attack()
            if event.key == pygame.K_LSHIFT:
                knight.dash()
            if event.key == pygame.K_q:
                knight.roll()
            if event.key == pygame.K_e:
                knight.slide()
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_r and game_state.game_over:
                knight, enemies, particles, powerups, spawn_timer, game_state = reset_game()

    if not game_state.game_over:
        keys = pygame.key.get_pressed()

        game_state.update_wave()

        # Spawn enemies at ground level
        spawn_timer += 1
        if spawn_timer >= game_state.spawn_rate:
            spawn_timer = 0
            for _ in range(game_state.enemies_per_spawn):
                spawn_x = random.choice([0, GAME_CONFIG['WIDTH'] - SKEL_FRAME_H])
                spawn_y = ground_y() - SKEL_FRAME_H
                if random.random() < 0.6:
                    enemies.append(Skeleton(spawn_x, spawn_y, assets['skeleton_white_frames']))
                else:
                    enemies.append(YellowSkeleton(spawn_x, spawn_y, assets['skeleton_yellow_frames']))

        knight.handle_input(keys, layout)
        knight.apply_gravity(layout)
        knight.update_animation(dt)

        for enemy in enemies[:]:
            enemy.move_towards(knight._col_rect(), layout)
            enemy.apply_gravity(layout)
            enemy.update_animation(dt)

            # Enemy attacks player
            if enemy.alive:
                atk_box = enemy.get_attack_hitbox()
                if atk_box and atk_box.colliderect(knight._col_rect()):
                    knight.take_damage(enemy.damage)

            # Player attacks enemy
            if knight.attacking and knight.attack_hitbox and enemy.alive:
                if knight.attack_hitbox.colliderect(enemy._col_rect()):
                    enemy.take_damage(knight.current_damage)

                    # If enemy just died, award score + effects
                    if not enemy.alive:
                        game_state.add_score(100 * game_state.wave)

                        particle_color = (200, 200, 255) if isinstance(enemy, Skeleton) else (255, 220, 100)
                        for _ in range(10):
                            particles.append(Particle(
                                enemy.rect.centerx, enemy.rect.centery,
                                particle_color,
                                random.uniform(-3, 3), random.uniform(-5, -1),
                            ))

                        if random.random() < GAME_CONFIG['POWERUP_SPAWN_CHANCE']:
                            ptype = 'health' if knight.health < knight.max_health * 0.7 else 'score'
                            powerups.append(PowerUp(enemy.rect.centerx, enemy.rect.centery, ptype))

        # Keep enemies alive during death animation, remove when done
        enemies = [e for e in enemies if not e.death_anim_done]

        particles = [p for p in particles if p.update()]

        for powerup in powerups[:]:
            if powerup.update():
                if powerup.get_rect().colliderect(knight._col_rect()):
                    powerup.collected = True
                    if powerup.type == 'health':
                        knight.heal(30)
                    else:
                        game_state.add_score(500)
                    color = (255, 50, 50) if powerup.type == 'health' else (255, 215, 0)
                    for _ in range(5):
                        particles.append(Particle(
                            powerup.x, powerup.y, color,
                            random.uniform(-2, 2), random.uniform(-3, 0),
                        ))
        powerups = [p for p in powerups if p.update()]

        if not knight.alive and knight.state == 'DEATH' and knight.current_frame_idx >= len(knight.current_frames) - 1:
            game_state.game_over = True

    # Update torches
    for torch in torches:
        torch.update(dt)

    # Draw
    screen.fill(BG_COLOR)
    tilemap.draw(screen)

    for torch in torches:
        torch.draw(screen)

    for particle in particles:
        particle.draw(screen)
    for powerup in powerups:
        powerup.draw(screen)

    knight.draw(screen)
    for enemy in enemies:
        enemy.draw(screen)

    draw_ui(screen, fonts, knight, game_state)

    if game_state.game_over:
        draw_game_over(screen, fonts, game_state)

    pygame.display.flip()

pygame.quit()
sys.exit()
