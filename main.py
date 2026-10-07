import argparse
import asyncio
import sys
import random
import pygame

from progression import reaction, DISCOVERIES, Expedition, Sayings, UPGRADES, MATERIALS, PROVISIONS, apply_loadout
from config import GAME_CONFIG
from assets import load_campaign_assets
from game_state import CampaignState
from campaign import Campaign, World
from camp import Camp
from camp_interior import QuartermasterStorehouse
from camera import Camera
from scenery import Scenery
from region_features import RegionFeatures
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
        self.transition = None
        self.sayings = Sayings()
        self.service = None
        self.expedition = Expedition(self.save.provision)
        self.running = True
        self.selection = 0
        self.settings_return = 'title'
        self.accumulator = 0
        self.reset_game()
        self.change_mode('title')

    def reset_game(self, class_id=None):
        if not getattr(self, 'transition_action', False):
            self.transition = None
        self.service = None
        self.campaign = Campaign()
        self.class_id = class_id or self.save.last_class
        from zerie_runtime import canonical_class
        self.class_id = canonical_class(self.class_id)
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
        self.enter_camp()

    def enter_camp(self, notice=''):
        health = self.knight.health
        self.knight = Hero(380, 496, self.assets['heroes'][self.class_id], self.class_id)
        if not notice:
            self.knight.health = health
        apply_loadout(self.knight, self.save)
        self.camp_transition = None
        self.exterior_camp = None
        self.audio.camp_morale = len(self.save.cleared_regions) == 4
        self.world = Camp()
        self.world.notice = notice
        self.world.notice_timer = 300 if notice else 0
        self.camera = Camera(self.world.width)
        self.camera.update(self.knight.rect)
        self.enemies = []
        self.sources = []
        self.particles = []
        self.powerups = []
        self.state.game_over = False
        self.state.phase = 'camp'
        self.play_mode = 'camp'
        self.change_mode('camp')

    def transition_camp(self, entering):
        if self.camp_transition:
            return
        self.world.dialogue = None
        self.camp_transition = {'entering': entering, 'tick': 0, 'old': self.screen.copy()}
        hero = self.knight
        hero.pending_attack = None
        hero.attacking = False
        hero.attack_hitbox = None
        hero.mobility_timer = 0
        hero.rushing = False
        hero.combo_buffer = False
        hero.combo_timer = 0
        hero.climbing = None
        hero.vel_y = 0
        hero.sources.clear()
        hero.events.clear()
        hero.set_state('Idle', True)
        self.sources = []
        self.particles = []
        self.powerups = []
        self.enemies = []

    def tick_camp_transition(self):
        transition = self.camp_transition
        transition['tick'] += 1
        if transition['tick'] == 12:
            if transition['entering']:
                self.exterior_camp = self.world
                self.exterior_position = self.knight.rect.topleft
                self.exterior_camera = self.camera.x
                self.world = QuartermasterStorehouse()
                self.knight.rect.midbottom = (90, 560)
                self.camera = Camera(self.world.width)
                self.camera.update(self.knight.rect)
                self.play_mode = 'interior'
            else:
                self.world = self.exterior_camp
                self.knight.rect.topleft = self.exterior_position
                self.knight.rect.bottom = 560
                self.camera = Camera(self.world.width)
                self.camera.x = self.exterior_camera
                self.play_mode = 'camp'
            self.change_mode(self.play_mode)
        if transition['tick'] >= 24:
            self.camp_transition = None

    def depart(self, index):
        if self.save.gate_unlocked(index):
            self.begin_transition(lambda: self.launch_expedition(index), self.campaign_name(index), True)

    def campaign_name(self, index):
        from campaign import ENVIRONMENTS
        return ENVIRONMENTS[index]['name']

    def begin_transition(self, action, title='', interstitial=False):
        if self.transition:
            return
        self.transition = {'tick': 0, 'old': self.screen.copy(), 'action': action,
                           'title': title, 'saying': self.sayings.next() if interstitial else '',
                           'duration': 100 if interstitial else 30}
        self.accumulator = 0

    def tick_transition(self):
        t = self.transition
        t['tick'] += 1
        midpoint = t['duration'] // 2
        if t.get('suspended'):
            t['tick'] -= 1
            return
        if t['tick'] == midpoint:
            self.transition_action = True
            t['action']()
            self.transition_action = False
        if t['tick'] >= t['duration']:
            self.transition = None

    def open_service(self, name):
        self.service = name
        self.service_page = 0
        self.world.dialogue = None

    def service_lines(self):
        if self.service == 'forge':
            lines = ['BLACKSMITH - one equipped fitting; materials are permanent unlocks.']
            for i, (name, _, _, description) in enumerate(UPGRADES[self.class_id]):
                status = 'EQUIPPED' if self.save.equipped.get(self.class_id) == i else 'PURCHASED' if i in self.save.purchased[self.class_id] else 'UNLOCKED' if i in self.save.cleared_regions else 'LOCKED'
                lines += [f'{i+1}: {name} [{status}]', description + ' Needs ' + MATERIALS[i]]
            return lines + reaction(1, self.save, self.class_id)[:1] + ['1/2/3/4: forge & equip (free)   0: remove fitting   Esc: close']
        if self.service == 'supplies':
            return ['QUARTERMASTER - exactly one provision'] + reaction(0, self.save, self.class_id)[:1] + [ '1: Field Dressing - automatic 25 HP heal below 25%, once.', '2: Warding Salt - environmental damage reduced by 25%.', '3: Hunters Charm - optional discovery score +10%.', 'Selected: ' + self.save.provision, 'Retry retains consumed dressing and active provisions.', '1/2/3: select   Esc: close']
        from campaign import ENVIRONMENTS
        i = self.service_page
        row = self.save.records.get(str(i), {})
        lines = reaction(6, self.save, self.class_id)[:1] + ['CHRONICLER - Left/Right: region', ENVIRONMENTS[i]['name'], 'Boss: ' + ('CLEARED / ' + MATERIALS[i] if i in self.save.cleared_regions else 'Unchallenged / material unknown')]
        known = row.get('discoveries', [])
        lines += [f'Discoveries {len(set(known) & set(DISCOVERIES[i]))}/{len(DISCOVERIES[i])}: ' + ', '.join(name if name in known else '???' for name in DISCOVERIES[i])]
        for c in CLASSES:
            lines += [f'{CLASSES[c]["name"]}: best {row.get("best", {}).get(c, 0)} / completions {row.get("completions", {}).get(c, 0)}']
        lines += ['Provision departures: ' + ', '.join(f'{p}: {row.get("provisions", {}).get(p, 0)}' for p in PROVISIONS), 'Esc: close']
        return lines

    def finish_expedition(self):
        if self.mode == 'results':
            return
        index = self.campaign.index
        first = self.save.complete_expedition(index, self.class_id, self.state.score, self.features.claimed & set(DISCOVERIES[index]), self.expedition)
        if first is None:
            self.results = [self.campaign.environment['boss_name'] + ' DEFEATED',
                            'Completion not saved', self.save.error,
                            'No material or unlock granted; records unchanged',
                            f'Score {self.state.score}', self.expedition.result,
                            'Enter: return to camp']
            self.change_mode('results')
            return
        from campaign import ENVIRONMENTS
        self.campaign.complete = index == len(ENVIRONMENTS) - 1
        self.results = [self.campaign.environment['boss_name'] + ' DEFEATED',
                        'THE CAMP ENDURES' if self.campaign.complete else 'EXPEDITION COMPLETE',
                        ('First clear: ' + MATERIALS[index]) if first else 'Replay: unique material already held',
                        f'Score {self.state.score} | Discoveries {len(self.features.claimed & set(DISCOVERIES[index]))}/{len(DISCOVERIES[index])}',
                        self.expedition.result,
                        ('Unlocked: ' + UPGRADES[self.class_id][index][0] + ' + other hero fittings') if first else 'Replay recorded: class best and completed expedition',
                        'Next gate available' if first and index < len(ENVIRONMENTS) - 1 else 'All cleared routes remain replayable',
                        'Enter: return to camp']
        self.change_mode('results')

    def return_results(self):
        from camp import GATES
        self.enter_camp('The watch welcomes you home.')
        self.knight.rect.midbottom = (GATES[self.campaign.index] - 60, 560)
        self.camera.update(self.knight.rect)

    def launch_expedition(self, index, debug=False):
        if not debug and not self.save.gate_unlocked(index):
            return False
        health = self.knight.health
        self.knight = Hero(96, 496, self.assets['heroes'][self.class_id], self.class_id)
        self.knight.health = health
        apply_loadout(self.knight, self.save)
        self.expedition = Expedition(self.save.provision)
        self.state.score = 0
        self.state.completed = 0
        self.campaign.index = index
        self.campaign.checkpoint = 96
        self.campaign.exit_open = False
        self.campaign.complete = False
        self.play_mode = 'play'
        self.change_mode('play')
        self.load_environment()
        return True

    def tick_camp(self, keys):
        if self.camp_transition:
            self.tick_camp_transition()
            return
        camp = self.world
        camp.ticks += 1
        if isinstance(camp, Camp):
            camp.notice_timer = max(0, camp.notice_timer - 1)
        if camp.dialogue:
            return
        hero = self.knight
        hero.handle_input(keys, camp)
        camp.gravity(hero)
        self.camera.update(hero.rect)
        hero.aim = pygame.Vector2(1 if hero.facing_right else -1, 0)
        hero.update_animation(1000 / 60)
        for sound in hero.events:
            self.audio.play(sound)
        hero.events.clear()
        self.sources.extend(hero.sources)
        hero.sources.clear()
        for source in self.sources:
            if source.kind == 'rush':
                source.rect.center = hero.rect.center
                source.position = list(source.rect.topleft)
            source.update(camp)
            if isinstance(camp, Camp) and source.rect.colliderect(camp.dummy) and 'dummy' not in source.hit_targets:
                source.hit_targets.add('dummy')
                camp.hits += 1
                self.audio.play('sword_hit')
        self.sources = [s for s in self.sources if s.alive]

    def load_environment(self):
        self.world = World(self.campaign.environment)
        self.camera = Camera(self.world.width)
        self.scenery = Scenery(self.world, self.assets)
        if self.world.data['id'] == 'underworld':
            from underworld_features import UnderworldFeatures
            self.features = UnderworldFeatures(self.world, self.assets)
            self.features.select_section(96, self.camera)
        else:
            self.features = RegionFeatures(self.world, self.assets)
        self.state.realm_waves = len(self.world.data['zones'])
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
        self.state.paused = mode not in ('play', 'camp', 'interior')
        self.audio.set_mode(mode)

    def enter_class_selection(self):
        self.change_mode('class')
        self.selection = list(CLASSES).index(self.save.last_class)

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
            chosen = self.options()[choice]
            self.begin_transition(lambda: self.reset_game(chosen))
            return
        action = self.options()[choice]
        if action in ('Begin campaign', 'Restart run'):
            self.begin_transition(self.enter_class_selection)
        elif action == 'Retry checkpoint':
            if not getattr(self, 'transition_action', False):
                self.begin_transition(self.activate)
                return
            self.features.retry(self.campaign.checkpoint)
            self.state.score = max(0, self.state.score - 250)
            self.knight = Hero(self.campaign.checkpoint, 496, self.assets['heroes'][self.class_id], self.class_id)
            apply_loadout(self.knight, self.save)
            self.camera.update(self.knight.rect)
            self.enemies = []
            self.sources = []
            self.particles = []
            self.powerups = []
            self.state.spawned = 0
            self.state.spawn_timer = 0
            self.state.game_over = False
            self.state.phase = 'exit' if self.campaign.exit_open else 'travel'
            self.audio.boss_music(False)
            self.change_mode('play')
        elif action == 'Resume':
            self.change_mode(self.play_mode)
        elif action == 'Settings':
            self.settings_return = self.mode
            self.change_mode('settings')
        elif action == 'Title screen':
            self.service = None
            self.begin_transition(lambda: self.change_mode('title'))
        elif action == 'Quit':
            self.running = False

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.WINDOWFOCUSLOST and self.transition:
            self.transition['suspended'] = True
            self.audio.pause(True)
        elif event.type == pygame.WINDOWFOCUSGAINED and self.transition:
            self.transition['suspended'] = False
            self.audio.pause(False)
        elif event.type == pygame.WINDOWFOCUSLOST and self.mode in ('play', 'camp', 'interior'):
            self.change_mode('pause')
        elif event.type == pygame.KEYDOWN:
            key = event.key
            if self.transition:
                return
            if self.mode == 'results':
                if key == pygame.K_RETURN:
                    self.begin_transition(self.return_results)
                return
            if self.service:
                if key == pygame.K_ESCAPE:
                    self.service = None
                elif self.service == 'journal' and key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.service_page = (self.service_page + (1 if key == pygame.K_RIGHT else -1)) % 4
                elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    i = key - pygame.K_1
                    if self.service == 'forge':
                        self.save.purchase(self.class_id, i)
                        apply_loadout(self.knight, self.save)
                    elif self.service == 'supplies':
                        self.save.provision = PROVISIONS[min(i, 2)]
                        self.save.save()
                elif key == pygame.K_0 and self.service == 'forge':
                    self.save.equipped.pop(self.class_id, None)
                    self.save.save()
                    apply_loadout(self.knight, self.save)
                return
            if getattr(self, 'camp_transition', None):
                return
            if self.mode in ('camp', 'interior'):
                if key == pygame.K_ESCAPE and self.world.dialogue:
                    self.world.dialogue = None
                elif key in (pygame.K_ESCAPE, pygame.K_p):
                    self.change_mode('pause')
                elif key in (pygame.K_e, pygame.K_RETURN):
                    self.world.interact(self)
                elif not self.world.dialogue and self.mode == 'camp':
                    actions = {pygame.K_f: self.knight.attack, pygame.K_r: self.knight.secondary,
                               pygame.K_LSHIFT: self.knight.dash, pygame.K_RSHIFT: self.knight.dash, pygame.K_q: self.knight.roll}
                    if key in actions:
                        actions[key]()
            elif self.mode == 'play':
                if key in (pygame.K_ESCAPE, pygame.K_p):
                    self.change_mode('pause')
                elif self.knight.alive:
                    actions = {pygame.K_f: self.knight.attack, pygame.K_LSHIFT: self.knight.dash,
                               pygame.K_RSHIFT: self.knight.dash, pygame.K_q: self.knight.roll, pygame.K_e: self.expedition_interact}
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
                    self.change_mode(self.play_mode)
                elif self.mode in ('over', 'class', 'victory'):
                    self.begin_transition(lambda: self.change_mode('title'))
            elif key == pygame.K_r and self.mode == 'over':
                self.begin_transition(self.reset_game)
            elif key in (pygame.K_UP, pygame.K_w):
                self.selection = (self.selection - 1) % len(self.options())
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.selection = (self.selection + 1) % len(self.options())
            elif self.mode == 'class' and key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.selection = (self.selection + (1 if key == pygame.K_RIGHT else -1)) % 3
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHT, pygame.K_LEFT):
                if key in (pygame.K_RETURN, pygame.K_SPACE) or self.mode == 'settings':
                    self.activate(-1 if key == pygame.K_LEFT else 1)

    def expedition_interact(self):
        if self.transition:
            return True
        if not self.features.interact(self):
            return self.knight.secondary()
        return True

    def spawn(self, boss=False):
        data = self.campaign.environment
        center = data['zones'][self.state.wave - 1]
        if data['id'] == 'underworld':
            from underworld import ENCOUNTERS, CATALOG
            from entities.infernal import Infernal
            actor = ENCOUNTERS[self.state.wave - 1][self.state.spawned - 1]
            frames = self.assets.setdefault('infernal', {})
            if actor not in frames:
                from underworld import load_actor
                frames[actor] = load_actor(actor)
            enemy = Infernal(center + (180 if self.knight.rect.centerx < center else -180), 504, frames[actor], CATALOG[actor]['role'])
            enemy.section = self.state.wave - 1
            enemy.reward_key = (self.state.wave, self.state.spawned)
            self.enemies.append(enemy)
            if enemy.role == 'boss':
                self.audio.boss_music()
            self.audio.play('boss' if enemy.boss else 'wave')
            return
        if boss:
            species = data['boss']
            frames = self.assets['monsters'][species]
        else:
            actor, species = data['enemy_roster'][(self.state.spawned - 1) % len(data['enemy_roster'])]
            frames = self.assets['faction_enemies'][actor]
        x = center + (240 if self.knight.rect.centerx < center else -240)
        x = max(32, min(self.world.width - 100, x))
        y = 320 if species == 'Flying eye' else 476 if boss else 504
        self.enemies.append(Monster(x, y, frames, species, boss, self.campaign.index))
        self.enemies[-1].reward_key = (self.state.wave, self.state.spawned)
        self.audio.play('boss' if boss else 'wave')

    def burst(self, x, y, color):
        for _ in range(10):
            self.particles.append(Particle(x, y, color, random.uniform(-3, 3), random.uniform(-5, -1)))

    def entity_active(self, entity):
        return self.features.kind != "underworld" or self.features.entity_active(entity)

    def tick(self, keys):
        self.audio.update(1 / 60)
        if self.transition:
            self.tick_transition()
            return
        if self.service:
            return
        if self.mode in ('camp', 'interior'):
            self.tick_camp(keys)
            return
        if self.mode != 'play':
            return
        hero = self.knight
        self.expedition.update(hero)
        self.features.update(self)
        if hero.alive:
            if self.state.phase == 'travel' and hero.rect.centerx >= self.campaign.environment['zones'][self.state.wave - 1] - 300:
                self.state.phase = 'ready'
                self.state.transition_timer = 90
            event = self.state.update_wave(sum(e.alive or (e.boss and not e.death_anim_done) for e in self.enemies))
            if event in ('spawn', 'boss'):
                self.spawn(event == 'boss')
            elif event == 'clear':
                if self.state.wave in self.expedition.wave_claims:
                    self.state.score = max(0, self.state.score - 250 * self.state.wave)
                self.expedition.wave_claims.add(self.state.wave)
                hero.heal(30 if self.state.boss_wave else 15)
                self.audio.play('wave')
                if self.state.boss_wave:
                    self.audio.boss_music(False)
                    self.campaign.exit_open = self.features.exit_ready if hasattr(self.features, 'exit_ready') else True
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
                if not hero.invulnerable and hero.rect.colliderect(hazard):
                    hero.take_damage(self.expedition.hazard_damage(16))
            # Retreat is allowed, but combat cannot be skipped by crossing the next zone.
            if self.state.phase in ('ready', 'combat', 'clear'):
                limit = self.campaign.environment['zones'][self.state.wave - 1] + 340
                hero.rect.right = min(hero.rect.right, limit)
            if self.campaign.exit_open and hero.rect.colliderect(self.world.exit):
                self.begin_transition(self.finish_expedition, 'The road falls quiet', True)
                return
        direction = 1 if hero.facing_right else -1
        hero.aim = pygame.Vector2(direction, 0)
        targets = [enemy for enemy in self.enemies if enemy.alive and self.entity_active(enemy)
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
        if self.features.kind == "underworld":
            for source in hero.sources:
                source.section = self.features.active_section
        self.sources.extend(hero.sources)
        hero.sources.clear()
        for enemy in self.enemies:
            if not self.entity_active(enemy):
                continue
            enemy.update(hero, self.world)
            for sound in enemy.events:
                self.audio.play(sound)
            enemy.events.clear()
            self.sources.extend(enemy.sources)
            enemy.sources.clear()
        for source in self.sources:
            if self.features.kind == "underworld" and not self.features.source_active(source):
                continue
            if source.kind == 'rush':
                source.rect.center = hero.rect.center
                source.position = list(source.rect.topleft)
            source.update(self.world)
            if self.features.kind == "underworld" and not self.features.source_active(source):
                continue
            self.features.hit(source)
            targets = [e for e in self.enemies if self.entity_active(e)] if source.team == 'hero' else [hero]
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
                claim = getattr(enemy, 'reward_key', (self.state.wave, enemy.rect.x))
                if claim in self.expedition.kill_claims:
                    continue
                self.expedition.kill_claims.add(claim)
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
                        hero.heal(30, upgrade=True)
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
            self.change_mode('over')
            self.audio.play('game_over')

    def draw(self):
        if isinstance(self.world, (Camp, QuartermasterStorehouse)):
            self.world.draw(self.screen, self.fonts, self)
        else:
            self.scenery.draw(self.screen, self.camera, self.campaign)
            self.features.draw_objects(self.screen, self.camera)
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
                if (self.features.source_active(source) if self.features.kind == "underworld"
                        else True):
                    source.draw(self.screen, self.camera)
            for enemy in self.enemies:
                if self.entity_active(enemy):
                    enemy.draw(self.screen, self.camera)
            self.knight.draw(self.screen, self.camera)
        if isinstance(self.world, (Camp, QuartermasterStorehouse)):
            self.world.draw_foreground(self.screen, self)
        if not isinstance(self.world, (Camp, QuartermasterStorehouse)):
            self.features.draw_foreground(self.screen, self.camera)
        if self.mode == 'play':
            self.features.draw_overlay(self)
            draw_ui(self.screen, self.fonts, self.knight, self.state)
            draw_banner(self.screen, self.fonts, self.campaign.environment['name'], 20, 'small')
            boss = next((e for e in self.enemies if e.boss and e.alive), None)
            if boss:
                bar(self.screen, (280, 62, 300, 14), boss.health / boss.max_health, (151, 44, 49))
                draw_banner(self.screen, self.fonts, 'THE DESCENT WARDEN' if getattr(boss, 'role', '') == 'miniboss' else self.campaign.environment['boss_name'], 46, 'small')
            if self.mode == 'play' and self.state.phase != 'combat':
                text = {'travel': 'Follow the path to the next battle', 'exit': 'Boss defeated - reach the glowing exit',
                        'clear': 'Wave cleared - recover and press onward', 'ready': 'Enemies approach - prepare!'}
                if self.world.data['id'] == 'underworld' and self.state.phase == 'exit' and not self.campaign.exit_open:
                    text['exit'] = 'Regent fallen - return to cool the three seals (E)'
                draw_banner(self.screen, self.fonts, text.get(self.state.phase, ''), 150, 'small')
        if isinstance(self.world, (Camp, QuartermasterStorehouse)) and self.mode in ('camp', 'interior'):
            self.world.draw_overlay(self.screen, self.fonts, self)
        if self.mode in ('camp', 'interior'):
            draw_banner(self.screen, self.fonts, f'HP {self.knight.health}/{self.knight.max_health}  |  Score {self.state.score}', 575, 'small')
        if self.mode == 'class':
            draw_class_selection(self.screen, self.fonts, self.assets['heroes'], self.selection)
        elif self.mode == 'results':
            Camp.panel(self.world, self.screen, self.fonts, self.results, (30, 140, 740, 300))
        elif self.mode not in ('play', 'camp', 'interior'):
            titles = {'title': 'CRUEL WORLD', 'pause': 'PAUSED', 'over': 'YOU HAVE FALLEN', 'settings': 'SETTINGS', 'victory': 'THE WORLD ENDURES'}
            subtitle = f'Best {self.save.high_score}  |  Score {self.state.score}  |  Region {self.campaign.index + 1}/4'
            if self.mode == 'title':
                subtitle = f'Four realms / three heroes  |  Best {self.save.high_score}'
            draw_menu(self.screen, self.fonts, titles[self.mode], subtitle, self.options(), self.selection)
        if self.save.error:
            draw_banner(self.screen, self.fonts, self.save.error, 135, 'small')
        if getattr(self, 'camp_transition', None):
            tick = self.camp_transition['tick']
            old = self.camp_transition['old'].copy()
            old.set_alpha(255 if tick <= 12 else max(0, (24-tick) * 255 // 12))
            self.screen.blit(old, (0, 0))
        if self.mode == 'play':
            draw_banner(self.screen, self.fonts, self.expedition.provision + ' [' + self.expedition.status + ']', 575, 'small')
        if self.service:
            Camp.panel(self.world, self.screen, self.fonts, self.service_lines(), (30, 130, 740, 320))
        if self.transition:
            t = self.transition
            midpoint = t['duration'] // 2
            if t.get('passage'):
                shade = pygame.Surface((800, 600))
                shade.fill((8, 5, 10))
                shade.set_alpha(255 * min(t['tick'], t['duration'] - t['tick']) // midpoint)
                self.screen.blit(shade, (0, 0))
            elif t['saying']:
                panel = pygame.Surface((800, 600))
                panel.fill((20, 24, 31))
                # A native-pixel gate seal and traveling ember give the fixed loading beat motion.
                pygame.draw.rect(panel, (91, 83, 69), (366, 122, 68, 78), 4)
                for x in (380, 398, 416):
                    pygame.draw.rect(panel, (129, 116, 84), (x, 142, 4, 58))
                pygame.draw.rect(panel, (47, 45, 43), (190, 423, 420, 6))
                pygame.draw.rect(panel, (180, 151, 94), (190, 423, 420*t['tick']//t['duration'], 6))
                pygame.draw.rect(panel, (229, 190, 113), (190+420*t['tick']//t['duration'], 421, 4, 10))
                Camp.panel(self.world, panel, self.fonts, [t['title'], '', t['saying']], (45, 235, 710, 150))
                if t['tick'] < midpoint:
                    self.screen.blit(t['old'], (0, 0))
                    panel.set_alpha(min(255, t['tick'] * 255 // 24))
                else:
                    panel.set_alpha(min(255, (t['duration'] - t['tick']) * 255 // 24))
                self.screen.blit(panel, (0, 0))
            else:
                old = t['old'].copy()
                old.set_alpha(max(0, 255 - max(0, t['tick'] - midpoint) * 255 // midpoint))
                self.screen.blit(old, (0, 0))
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
            if self.mode in ('play', 'camp', 'interior') or getattr(self, 'transition', None):
                self.accumulator += elapsed
                while self.accumulator >= 1000 / 60 and (self.mode in ('play', 'camp', 'interior') or getattr(self, 'transition', None)):
                    self.accumulator -= 1000 / 60
                    self.tick(pygame.key.get_pressed())
            if self.mode not in ('play', 'camp', 'interior') and not getattr(self, 'transition', None):
                self.audio.update(elapsed / 1000)
            self.draw()
            count += 1
            await asyncio.sleep(0)
        self.save.save()
        if getattr(self, 'screenshot', None):
            pygame.image.save(self.screen, self.screenshot)
        pygame.quit()


async def async_main():
    parser = argparse.ArgumentParser(description='Cruel World side-scrolling campaign')
    parser.add_argument('--class', dest='class_id', choices=['knight', 'archer', 'wizard', 'warrior', 'ranger', 'huntress'], help='Start a campaign directly with this class')
    parser.add_argument('--environment', type=int, choices=(1, 2, 3), default=1, help='Debug starting region')
    parser.add_argument('--storehouse', action='store_true', help='Start inside the Quartermaster storehouse with --class')
    parser.add_argument('--camp', action='store_true', help='Start directly in camp with --class')
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
        if args.storehouse:
            game.knight.rect.midbottom = (182, 560)
            game.camera.update(game.knight.rect)
            game.transition_camp(True)
            for _ in range(24):
                game.tick({})
        elif not args.camp:
            game.launch_expedition(args.environment - 1, debug=True)
    game.screenshot = args.screenshot
    await game.run_async(args.frames)


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    asyncio.run(async_main())
