import pygame
from config import GAME_CONFIG


def init_fonts():
    try:
        large = pygame.font.Font(None, 48)
        medium = pygame.font.Font(None, 36)
        small = pygame.font.Font(None, 24)
    except Exception:
        large = pygame.font.SysFont('arial', 48)
        medium = pygame.font.SysFont('arial', 36)
        small = pygame.font.SysFont('arial', 24)
    return {'large': large, 'medium': medium, 'small': small}


def draw_ui(screen, fonts, knight, game_state):
    bar_width = 200
    bar_height = 20
    bar_x = 10
    bar_y = 10

    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
    health_width = int((knight.health / knight.max_health) * bar_width)
    health_color = (50, 255, 50) if knight.health > 50 else (255, 50, 50)
    pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

    small = fonts['small']
    screen.blit(small.render(f"HP: {knight.health}/{knight.max_health}", True, (255, 255, 255)), (bar_x + 5, bar_y + 2))
    screen.blit(small.render(f"Score: {game_state.score}", True, (255, 215, 0)), (10, 40))
    screen.blit(small.render(f"Wave: {game_state.wave}", True, (150, 200, 255)), (10, 65))
    screen.blit(small.render("WASD: Move | F: Attack | Shift: Dash | Q: Roll | E: Slide", True, (180, 180, 180)),
                (GAME_CONFIG['WIDTH'] - 530, GAME_CONFIG['HEIGHT'] - 25))


def draw_game_over(screen, fonts, game_state):
    overlay = pygame.Surface((GAME_CONFIG['WIDTH'], GAME_CONFIG['HEIGHT']))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    cx = GAME_CONFIG['WIDTH'] // 2
    cy = GAME_CONFIG['HEIGHT'] // 2

    text = fonts['large'].render("GAME OVER", True, (255, 50, 50))
    screen.blit(text, text.get_rect(center=(cx, cy - 80)))

    text = fonts['medium'].render(f"Final Score: {game_state.score}", True, (255, 215, 0))
    screen.blit(text, text.get_rect(center=(cx, cy - 20)))

    text = fonts['medium'].render(f"Wave Reached: {game_state.wave}", True, (150, 200, 255))
    screen.blit(text, text.get_rect(center=(cx, cy + 30)))

    text = fonts['small'].render("Press R to Restart or ESC to Quit", True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=(cx, cy + 100)))
