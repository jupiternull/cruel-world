import math
import pygame
from region_features import RegionFeatures
from underworld import SCENES, AREA_NAMES, scene_path
from underworld_transitions import Transition


class UnderworldFeatures(RegionFeatures):
    def __init__(self, world, assets):
        self.world = world
        self.kind = 'underworld'
        self.active_section = 0
        self.camera = None
        self.rendered_sections = ()
        self.passage_cooldown = 0
        self.ticks = 0
        self.notice = 'Defeat guardians, cool three seals with E, then slay the Pyre Regent.'
        self.notice_timer = 300
        self.claimed = set()
        self.visited = set()
        self.breakables = []
        self.water = []
        self.objects = {'seal0': (840, 'Cool altar seal'), 'seal1': (4680, 'Cool descent seal'),
                        'seal2': (8520, 'Cool vault seal'), 'testament': (7240, 'Read the burned testament')}
        self.scenes = [pygame.transform.scale(pygame.image.load(str(scene_path(*s))).convert(), (1280, 720)) for s in SCENES]
        # Real scene masonry supplies collision surfaces; source scenes are static backdrops.
        source = pygame.image.load(str(scene_path(*SCENES[1]))).convert()
        self.stone = pygame.transform.scale(source.subsurface((0, 132, 32, 12)), (64, 24))
        self.transitions = [Transition(i) for i in range(7)]
        for transition in self.transitions:
            transition.build_art(self.stone)
        world.features = self
        self.boss_defeated = False

    @property
    def exit_ready(self):
        return self.boss_defeated and all(f'seal{i}' in self.claimed for i in range(3))

    @staticmethod
    def section_at(x):
        return max(0, min(len(SCENES) - 1, int(x) // 1280))

    def select_section(self, x, camera=None):
        self.active_section = self.section_at(x)
        if camera is not None:
            self.camera = camera
        if self.camera is not None:
            left = self.active_section * 1280
            self.camera.set_bounds(left, left + 1280)

    def reposition(self, game, midbottom):
        game.knight.rect.midbottom = midbottom
        self.select_section(game.knight.rect.centerx, game.camera)
        game.camera.update(game.knight.rect)

    def entity_active(self, entity):
        if not hasattr(entity, "section"):
            owner = getattr(entity, "owner", None)
            entity.section = getattr(owner, "section", self.section_at(entity.rect.centerx))
        return entity.section == self.active_section

    def source_active(self, source):
        if not self.entity_active(source):
            return False
        left = source.section * 1280
        if source.rect.left < left or source.rect.right > left + 1280:
            source.alive = False
        return source.alive

    def retry(self, checkpoint):
        self.select_section(checkpoint)
        self.passage_cooldown = 0
        self.ticks = 0
        self.notice_timer = 0

    def blockers(self):
        return [r for t in self.transitions for r in t.blockers]

    def nearby_passage(self, hero):
        return next(((t, direction) for t in self.transitions
                     if (direction := t.entry_direction(hero)) is not None
                     and self.active_section == t.index + (direction < 0)), None)

    def use_passage(self, game, transition, direction):
        def clear():
            hero = game.knight
            hero.pending_attack = None
            hero.attacking = False
            hero.attack_hitbox = None
            hero.attack_elapsed = 0
            hero.mobility_timer = 0
            hero.rushing = False
            hero.combo_buffer = False
            hero.combo_timer = 0
            hero.combo_stage = 0
            hero.climbing = None
            hero.vel_y = 0
            hero.drop_timer = 0
            hero.jump_held = False
            hero.sources.clear()
            hero.events.clear()
            hero.hit_targets.clear()
            hero.set_state('Idle', True)
            game.sources.clear()
            for enemy in game.enemies:
                enemy.sources.clear()
        def emerge():
            clear()
            hero = game.knight
            self.reposition(game, (transition.x + direction * 184, transition.deck_y))
            hero.on_ground = True
            hero.facing_right = direction > 0
            hero.aim = pygame.Vector2(direction, 0)
            hero.invulnerable = max(hero.invulnerable, 45)
            game.camera.update(hero.rect)
            self.passage_cooldown = 45
        clear()
        game.begin_transition(emerge)
        game.transition['passage'] = True

    def interact(self, game):
        if game.transition:
            return True
        passage = self.nearby_passage(game.knight)
        if passage:
            if not self.passage_cooldown:
                self.use_passage(game, *passage)
            return True
        name = self.nearby(game.knight)
        if name is None:
            return False
        if name.startswith('seal'):
            wave = {'seal0': 1, 'seal1': 4, 'seal2': 7}[name]
            if wave not in game.expedition.wave_claims:
                self.notice = 'Defeat the seal guardians before cooling this seal.'
                self.notice_timer = 180
                return True
            self.reward(game, name, 150, 25)
            self.notice = f'Seal cooled ({sum(s.startswith("seal") for s in self.claimed)}/3). +150 / heal 25'
        else:
            self.reward(game, name, 120, 12)
            self.notice = 'The Regent feeds the core through three seals. Cool them, then break his reign.'
        self.notice_timer = 240
        game.audio.play('chest_open')
        return True

    def update(self, game):
        self.passage_cooldown = max(0, self.passage_cooldown - 1)
        self.ticks += 1
        self.notice_timer = max(0, self.notice_timer - 1)
        if 8 in game.expedition.wave_claims:
            self.boss_defeated = True
        if self.exit_ready:
            game.campaign.exit_open = True
        area = self.active_section
        if area not in self.visited:
            self.visited.add(area)
            if not self.notice_timer:
                self.notice = AREA_NAMES[area]
                self.notice_timer = 180

    def draw_background(self, screen, camera):
        i = self.active_section
        screen.blit(self.scenes[i], (i * 1280 - camera.x, -120))
        self.rendered_sections = (i,)
        shade = pygame.Surface((800, 600), pygame.SRCALPHA)
        shade.fill((25, 8, 17, 45))
        screen.blit(shade, (0, 0))
        for transition in self.transitions:
            transition.draw(screen, camera)

    def draw_objects(self, screen, camera):
        for name, (x, _) in self.objects.items():
            sx = x - camera.x
            if -60 < sx < 860:
                screen.blit(self.stone, (sx - 32, 536))
                color = (118, 230, 207) if name in self.claimed else (255, 153, 65)
                pygame.draw.circle(screen, color, (sx, 523), 10, 3)
                pygame.draw.line(screen, color, (sx, 510), (sx, 534), 2)

    def draw_foreground(self, screen, camera):
        layer = pygame.Surface((800, 600), pygame.SRCALPHA)
        for hazard in self.world.hazards:
            r = camera.rect(hazard)
            pygame.draw.rect(layer, (236, 76, 25), r)
            for x in range(r.left, r.right, 8):
                y = r.top + 3 + int(math.sin((x + self.ticks * 3) / 15) * 2)
                pygame.draw.line(layer, (255, 204, 88), (x, y), (x + 6, y), 3)
            pygame.draw.ellipse(layer, (255, 86, 24, 45), r.inflate(50, 30))
        for j in range(45):
            x = (j * 197 + self.ticks // 3 - camera.x) % 850
            y = 580 - (j * 53 + self.ticks * (1 + j % 2)) % 550
            pygame.draw.circle(layer, (255, 148 + j % 70, 60, 130), (x, y), 1 + j % 2)
        for x in range(int(camera.x) // 256 * 256, int(camera.x) + 850, 256):
            screen.blit(self.stone, (x - camera.x, 582))
        screen.blit(layer, (0, 0))

    def draw_overlay(self, game):
        passage = self.nearby_passage(game.knight)
        if passage and not game.transition and not self.passage_cooldown:
            from ui import draw_banner
            draw_banner(game.screen, game.fonts, passage[0].prompt, 465, 'small')
        else:
            super().draw_overlay(game)
        text = game.fonts['small'].render(f'SEALS {sum(s.startswith("seal") for s in self.claimed)}/3  |  PYRE REGENT ' + ('FALLEN' if self.boss_defeated else 'ALIVE'), True, (245, 191, 124))
        game.screen.blit(text, (20, 132))
