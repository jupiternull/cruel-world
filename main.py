import argparse
import asyncio
import sys
import random
import pygame

from config import GAME_CONFIG
from assets import load_campaign_assets
from game_state import CampaignState
from campaign import Campaign, World
from camera import Camera
from scenery import Scenery
from entities.hero import Hero, CLASSES
from entities.monster import Monster
from persistence import SaveData
from audio import AudioManager
from entities import Particle, PowerUp
from ui import init_fonts, draw_ui, draw_menu, draw_banner, draw_class_selection, bar


class Game:
    def __init__(self, save_path=None):
        pygame.init()
        self.save = SaveData(save_path)
        self.screen = pygame.display.set_mode((800, 600), pygame.FULLSCREEN if self.save.settings['fullscreen'] and sys.platform != 'emscripten' else 0)
        pygame.display.set_caption('Cruel World')
        self.fonts = init_fonts()
        self.assets = load_campaign_assets()
        self.audio = AudioManager(self.save.settings)
        self.running = True
        self.selection = 0
        self.settings_return = 'title'
        self.accumulator = 0
        self.reset_game()
        self.change_mode('title')

    def reset_game(self, class_id=None):
        self.campaign = Campaign()
        self.class_id = class_id or self.save.last_class
        if self.class_id == 'huntress':
            self.class_id = 'ranger'
        self.save.last_class = self.class_id
        self.save.save()
        self.knight = Hero(96, 496, self.assets['heroes'][self.class_id], self.class_id)
        self.particles = []
        self.powerups = []
        self.state = CampaignState()
        self.mode = 'play'
        self.selection = 0
        self.accumulator = 0
        self.load_environment()
        self.audio.set_mode('play')

    def load_environment(self):
        self.world = World(self.campaign.environment)
        self.camera = Camera(self.world.width)
        self.scenery = Scenery(self.world, self.assets)
        self.enemies = []
        self.sources = []
        self.particles = []
        self.powerups = []
        self.knight.rect.topleft = (96, 496)
        self.knight.vel_y = 0
        self.knight.climbing = None
        self.knight.pending_attack = None
        self.knight.attacking = False
        self.knight.attack_hitbox = None
        self.knight.mobility_timer = 0
        self.knight.rushing = False
        self.knight.sources = []
        self.knight.set_state('Idle')
        self.state.wave = 1
        self.state.phase = 'travel'
        self.state.spawned = 0
        self.state.spawn_timer = 0
        self.save.furthest_environment = max(self.save.furthest_environment, self.campaign.index)
        self.save.save()
        self.audio.environment(self.campaign.environment)

    def options(self):
        if self.mode == 'title':
            return ['Begin campaign', 'Settings', 'Quit']
        if self.mode == 'class':
            return list(CLASSES)
        if self.mode == 'victory':
            return ['Restart run', 'Title screen', 'Quit']
        if self.mode == 'pause':
            return ['Resume', 'Settings', 'Restart run', 'Title screen']
        if self.mode == 'over':
            return ['Retry checkpoint', 'Restart run', 'Title screen', 'Quit']
        settings = self.save.settings
        return [f"Sound: {'On' if settings['sound'] else 'Off'}", f"Volume: {round(settings['volume'] * 100)}%", 'Fullscreen: use host button' if sys.platform == 'emscripten' else f"Fullscreen: {'On' if settings['fullscreen'] else 'Off'}", 'Back']

    def change_mode(self, mode):
        self.mode = mode
        self.selection = 0
        self.accumulator = 0
        self.state.paused = mode != 'play'
        self.audio.set_mode(mode)

    def activate(self, direction=1):
        choice = self.selection
        self.audio.play('menu')
        if self.mode == 'settings':
            settings = self.save.settings
            if choice == 0:
                settings['sound'] = not settings['sound']
            elif choice == 1:
                settings['volume'] = round(max(0, min(1, settings['volume'] + direction * 0.1)), 1)
            elif choice == 2 and sys.platform != 'emscripten':
                settings['fullscreen'] = not settings['fullscreen']
                self.screen = pygame.display.set_mode((800, 600), pygame.FULLSCREEN if settings['fullscreen'] else 0)
            else:
                self.change_mode(self.settings_return)
            self.audio.apply_settings()
            self.save.save()
            return
        if self.mode == 'class':
            self.reset_game(self.options()[choice])
            return
        action = self.options()[choice]
        if action in ('Begin campaign', 'Restart run'):
            self.save.record(self.state.score)
            self.change_mode('class')
            self.selection = list(CLASSES).index(self.save.last_class)
        elif action == 'Retry checkpoint':
            self.save.record(self.state.score)
            self.state.score = max(0, self.state.score - 250)
            self.knight = Hero(self.campaign.checkpoint, 496, self.assets['heroes'][self.class_id], self.class_id)
            self.enemies = []
            self.sources = []
            self.particles = []
            self.powerups = []
            self.state.spawned = 0
            self.state.spawn_timer = 0
            self.state.game_over = False
            self.state.phase = 'exit' if self.campaign.exit_open else 'travel'
            self.change_mode('play')
        elif action == 'Resume':
            self.change_mode('play')
        elif action == 'Settings':
            self.settings_return = self.mode
            self.change_mode('settings')
        elif action == 'Title screen':
            self.save.record(self.state.score)
            self.change_mode('title')
        elif action == 'Quit':
            self.running = False

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.WINDOWFOCUSLOST and self.mode == 'play':
            self.change_mode('pause')
        elif event.type == pygame.KEYDOWN:
            key = event.key
            if self.mode == 'play':
                if key in (pygame.K_ESCAPE, pygame.K_p):
                    self.change_mode('pause')
                elif self.knight.alive:
                    actions = {pygame.K_f: self.knight.attack, pygame.K_LSHIFT: self.knight.dash,
                               pygame.K_RSHIFT: self.knight.dash, pygame.K_q: self.knight.roll, pygame.K_e: self.knight.secondary}
                    if key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_q):
                        keys = pygame.key.get_pressed()
                        direction = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
                        actions[key](direction)
                    elif key in actions:
                        actions[key]()

            elif key == pygame.K_ESCAPE:
                if self.mode == 'settings':
                    self.change_mode(self.settings_return)
                elif self.mode == 'pause':
                    self.change_mode('play')
                elif self.mode in ('over', 'class', 'victory'):
                    self.change_mode('title')
            elif key == pygame.K_r and self.mode == 'over':
                self.reset_game()
            elif key in (pygame.K_UP, pygame.K_w):
                self.selection = (self.selection - 1) % len(self.options())
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.selection = (self.selection + 1) % len(self.options())
            elif self.mode == 'class' and key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.selection = (self.selection + (1 if key == pygame.K_RIGHT else -1)) % 3
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHT, pygame.K_LEFT):
                if key in (pygame.K_RETURN, pygame.K_SPACE) or self.mode == 'settings':
                    self.activate(-1 if key == pygame.K_LEFT else 1)

    def spawn(self, boss=False):
        data = self.campaign.environment
        center = data['zones'][self.state.wave - 1]
        species = data['boss'] if boss else data['enemies'][(self.state.spawned - 1) % len(data['enemies'])]
        x = center + (240 if self.knight.rect.centerx < center else -240)
        x = max(32, min(self.world.width - 100, x))
        y = 320 if species == 'Flying eye' else 476 if boss else 504
        self.enemies.append(Monster(x, y, self.assets['monsters'][species], species, boss, self.campaign.index))
        self.audio.play('boss' if boss else 'wave')

    def burst(self, x, y, color):
        for _ in range(10):
            self.particles.append(Particle(x, y, color, random.uniform(-3, 3), random.uniform(-5, -1)))

    def tick(self, keys):
        if self.mode != 'play':
            return
        hero = self.knight
        if hero.alive:
            if self.state.phase == 'travel' and hero.rect.centerx >= self.campaign.environment['zones'][self.state.wave - 1] - 300:
                self.state.phase = 'ready'
                self.state.transition_timer = 90
            event = self.state.update_wave(sum(e.alive for e in self.enemies))
            if event in ('spawn', 'boss'):
                self.spawn(event == 'boss')
            elif event == 'clear':
                hero.heal(30 if self.state.boss_wave else 15)
                self.audio.play('wave')
                if self.state.boss_wave:
                    self.campaign.exit_open = True
                    self.state.phase = 'exit'
                    self.audio.play('door_open')
            # A wave's clear timer leads back into traversal before the next zone.
            if self.state.phase == 'combat' and self.state.spawned == 0 and self.state.wave > 1:
                zone = self.campaign.environment['zones'][self.state.wave - 1]
                if hero.rect.centerx < zone - 300:
                    self.state.phase = 'travel'
            grounded = hero.on_ground
            old_x = hero.rect.x
            hero.handle_input(keys, self.world)
            self.world.gravity(hero)
            if not grounded and hero.on_ground:
                self.audio.play('land_stone')
            if hero.on_ground and old_x != hero.rect.x:
                hero.footstep_timer += 1
                if hero.footstep_timer % 18 == 0:
                    self.audio.play('dirt_step' if self.campaign.index == 0 else 'stone_step')
            if self.campaign.update_checkpoint(hero.rect.centerx):
                self.audio.play('chest_open')
            for hazard in self.world.hazards:
                if hero.rect.colliderect(hazard):
                    hero.take_damage(16)
            # Retreat is allowed, but combat cannot be skipped by crossing the next zone.
            if self.state.phase in ('ready', 'combat', 'clear'):
                limit = self.campaign.environment['zones'][self.state.wave - 1] + 340
                hero.rect.right = min(hero.rect.right, limit)
            if self.campaign.exit_open and hero.rect.colliderect(self.world.exit):
                self.audio.play('door_open')
                hero.heal(40)
                if self.campaign.advance():
                    self.load_environment()
                else:
                    self.state.phase = 'victory'
                    self.save.record(self.state.score)
                    self.change_mode('victory')
                return
        direction = 1 if hero.facing_right else -1
        hero.aim = pygame.Vector2(direction, 0)
        targets = [enemy for enemy in self.enemies if enemy.alive
                   and 0 < (enemy.rect.centerx - hero.rect.centerx) * direction < 560
                   and abs(enemy.rect.centery - hero.rect.centery) < 280]
        if targets:
            target = min(targets, key=lambda enemy: pygame.Vector2(enemy.rect.center).distance_squared_to(hero.rect.center))
            offset = pygame.Vector2(target.rect.center) - pygame.Vector2(hero.rect.center)
            hero.aim = offset.normalize()
        hero.update_animation(1000 / 60)
        for sound in hero.events:
            self.audio.play(sound)
        hero.events.clear()
        self.sources.extend(hero.sources)
        hero.sources.clear()
        for enemy in self.enemies:
            enemy.update(hero, self.world)
            for sound in enemy.events:
                self.audio.play(sound)
            enemy.events.clear()
            self.sources.extend(enemy.sources)
            enemy.sources.clear()
        for source in self.sources:
            if source.kind == 'rush':
                source.rect.center = hero.rect.center
                source.position = list(source.rect.topleft)
            source.update(self.world)
            targets = self.enemies if source.team == 'hero' else [hero]
            for target in targets:
                before = target.health
                if source.hit(target) and target.health != before:
                    sound = 'sword_hit' if source.kind in ('melee', 'rush') else 'bow_hit' if source.kind in ('arrow', 'volley') else 'spell_hit'
                    self.audio.play(sound)
                    self.burst(*target.rect.center, (235, 192, 115))
        self.sources = [source for source in self.sources if source.alive]
        for enemy in self.enemies:
            if not enemy.alive and not enemy.rewarded:
                enemy.rewarded = True
                self.state.add_score((1000 if enemy.boss else 100) * self.state.wave)
                self.audio.play('kill')
                if enemy.boss or random.random() < GAME_CONFIG['POWERUP_SPAWN_CHANCE']:
                    self.powerups.append(PowerUp(*enemy.rect.center, 'health' if enemy.boss or hero.health < hero.max_health * 0.7 else 'score'))
        self.enemies = [e for e in self.enemies if not e.death_anim_done]
        self.particles = [p for p in self.particles if p.update()]
        surviving = []
        for pickup in self.powerups:
            if pickup.update():
                if hero.alive and pickup.get_rect().colliderect(hero.rect):
                    if pickup.type == 'health':
                        hero.heal(30)
                    else:
                        self.state.add_score(500)
                    self.audio.play('pickup' if pickup.type == 'health' else 'score')
                    self.burst(pickup.x, pickup.y, (255, 100, 100))
                else:
                    surviving.append(pickup)
        self.powerups = surviving
        self.camera.update(hero.rect)
        if not hero.alive and hero.current_frame_idx == len(hero.current_frames) - 1:
            self.state.game_over = True
            self.save.record(self.state.score)
            self.change_mode('over')
            self.audio.play('game_over')

    def draw(self):
        self.scenery.draw(self.screen, self.camera, self.campaign)
        if self.state.phase in ('ready', 'combat', 'clear'):
            gate_x = self.campaign.environment['zones'][self.state.wave - 1] + 340 - self.camera.x
            if 0 <= gate_x < 800:
                pygame.draw.line(self.screen, (145, 113, 211), (gate_x, 240), (gate_x, 560), 3)
                for y in range(250, 560, 32):
                    pygame.draw.line(self.screen, (224, 194, 250), (gate_x - 5, y), (gate_x + 5, y + 12), 2)
        for thing in self.particles + self.powerups:
            original = thing.x
            thing.x -= self.camera.x
            thing.draw(self.screen)
            thing.x = original
        if self.mode not in ('title', 'class', 'settings'):
            for source in self.sources:
                source.draw(self.screen, self.camera)
            for enemy in self.enemies:
                enemy.draw(self.screen, self.camera)
            self.knight.draw(self.screen, self.camera)
        if self.mode == 'play':
            draw_ui(self.screen, self.fonts, self.knight, self.state)
            draw_banner(self.screen, self.fonts, self.campaign.environment['name'], 20, 'small')
            boss = next((e for e in self.enemies if e.boss and e.alive), None)
            if boss:
                bar(self.screen, (280, 62, 300, 14), boss.health / boss.max_health, (151, 44, 49))
                draw_banner(self.screen, self.fonts, self.campaign.environment['boss_name'], 46, 'small')
            if self.mode == 'play' and self.state.phase != 'combat':
                text = {'travel': 'Follow the path to the next battle', 'exit': 'Boss defeated - reach the glowing exit',
                        'clear': 'Wave cleared - recover and press onward', 'ready': 'Enemies approach - prepare!'}
                draw_banner(self.screen, self.fonts, text.get(self.state.phase, ''), 150, 'small')
        if self.mode == 'class':
            draw_class_selection(self.screen, self.fonts, self.assets['heroes'], self.selection)
        elif self.mode != 'play':
            titles = {'title': 'CRUEL WORLD', 'pause': 'PAUSED', 'over': 'YOU HAVE FALLEN', 'settings': 'SETTINGS', 'victory': 'THE WORLD ENDURES'}
            subtitle = f'Best {self.save.high_score}  |  Score {self.state.score}  |  Region {self.campaign.index + 1}/3'
            if self.mode == 'title':
                subtitle = f'Three realms / three heroes  |  Best {self.save.high_score}'
            draw_menu(self.screen, self.fonts, titles[self.mode], subtitle, self.options(), self.selection)
        if self.save.error:
            draw_banner(self.screen, self.fonts, self.save.error, 135, 'small')
        pygame.display.flip()

    def run(self, frames=None):
        asyncio.run(self.run_async(frames))

    async def run_async(self, frames=None):
        clock = pygame.time.Clock()
        count = 0
        while self.running and (frames is None or count < frames):
            elapsed = min(clock.tick(0 if sys.platform == 'emscripten' else 60), 100)
            for event in pygame.event.get():
                self.handle_event(event)
            if not self.running:
                break
            if self.mode == 'play':
                self.accumulator += elapsed
                while self.accumulator >= 1000 / 60 and self.mode == 'play':
                    self.accumulator -= 1000 / 60
                    self.tick(pygame.key.get_pressed())
            self.draw()
            count += 1
            await asyncio.sleep(0)
        self.save.record(self.state.score)
        self.save.save()
        if getattr(self, 'screenshot', None):
            pygame.image.save(self.screen, self.screenshot)
        pygame.quit()


async def async_main():
    parser = argparse.ArgumentParser(description='Cruel World side-scrolling campaign')
    parser.add_argument('--class', dest='class_id', choices=list(CLASSES) + ['huntress'], help='Start a campaign directly with this class')
    parser.add_argument('--environment', type=int, choices=(1, 2, 3), default=1, help='Debug starting region')
    parser.add_argument('--screenshot', help='Save the final frame as a PNG')
    parser.add_argument('--frames', type=int, help='Exit after this many frames for smoke testing')
    args = parser.parse_args([] if sys.platform == 'emscripten' else None)
    try:
        game = Game()
    except (OSError, pygame.error, ValueError) as error:
        pygame.quit()
        parser.exit(1, f'Could not start Cruel World: {error}\n')
    if args.class_id:
        game.reset_game(args.class_id)
        game.campaign.index = args.environment - 1
        game.load_environment()
    game.screenshot = args.screenshot
    await game.run_async(args.frames)


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    asyncio.run(async_main())
