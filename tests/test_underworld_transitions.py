import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import tempfile
import unittest
from pathlib import Path
import pygame
from main import Game


class TransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = Game(Path(cls.directory.name) / 'save.json')

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.directory.cleanup()

    def test_coverage_and_integrated_geometry(self):
        game = self.game
        game.reset_game('warrior')
        game.launch_expedition(3, debug=True)
        transitions = game.features.transitions
        self.assertEqual([t.x for t in transitions], list(range(1280, 8961, 1280)))
        self.assertEqual(len({t.kind for t in transitions}), 7)
        self.assertEqual(sum(t.climb for t in transitions), 2)
        for t in transitions:
            self.assertGreaterEqual(t.opening.height, game.knight.rect.height + 32)
            self.assertGreaterEqual(t.opening.width, 300)
            for y in range(120, 720):
                for x in range(176, 273):
                    self.assertEqual(t.art.get_at((x, y)).a, 255, (t.kind, x, y))
            for r in t.platforms:
                self.assertIn(r, game.world.platforms)
            for r in t.ladders:
                self.assertIn(r, game.world.climbables)
            for r in t.blockers:
                self.assertIn(r, game.features.blockers())
            for zone in game.world.data['zones']:
                self.assertFalse(any(r.collidepoint(zone, 559) for r in t.blockers))
            for x, _ in game.features.objects.values():
                self.assertFalse(t.bounds.collidepoint(x, 523))
            self.assertFalse(any(h.colliderect(t.bounds) for h in game.world.hazards))
            self.assertFalse(any(r.collidepoint(p, 559) for r in t.blockers for p in game.world.data['checkpoints']))

    def test_all_classes_cross_both_directions_and_retry(self):
        game = self.game
        for class_id in ('warrior', 'ranger', 'wizard'):
            game.reset_game(class_id)
            game.launch_expedition(3, debug=True)
            hero = game.knight
            sections = {0}
            for t in game.features.transitions:
                for direction in (1, -1):
                    game.features.retry(t.entries[0 if direction == 1 else 1])
                    hero.rect.midbottom = (t.entries[0 if direction == 1 else 1], 560)
                    hero.vel_y = 0
                    hero.on_ground = True
                    hero.climbing = None
                    key = pygame.K_d if direction == 1 else pygame.K_a
                    for height in (560, 320, -100):
                        hero.rect.midbottom = (t.entries[0 if direction == 1 else 1], height)
                        for _ in range(100):
                            game.world.move(hero, direction * 18)
                        self.assertLess(direction * (hero.rect.centerx - t.x), 0)
                    hero.rect.midbottom = (t.entries[0 if direction == 1 else 1], 560)
                    if t.climb:
                        self.assertIsNone(game.features.nearby_passage(hero))
                        hero.rect.centerx = t.ladders[0 if direction == 1 else 1].centerx
                        for _ in range(90):
                            hero.handle_input({pygame.K_w: True}, game.world)
                            game.world.gravity(hero)
                            if hero.rect.bottom == t.deck_y:
                                break
                        self.assertEqual(hero.rect.bottom, t.deck_y)
                    self.assertEqual(game.features.nearby_passage(hero), (t, direction))
                    hero.attack()
                    hero.mobility_timer = 8
                    from projectile import DamageSource
                    from types import SimpleNamespace
                    source = DamageSource(hero.rect.copy(), 100, 'enemy', 30)
                    game.sources.append(source)
                    enemy = SimpleNamespace(sources=[source])
                    game.enemies = [enemy]
                    original_world = game.world
                    original_claims = game.expedition.wave_claims.copy()
                    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
                    self.assertTrue(game.transition['passage'])
                    self.assertFalse(game.sources)
                    self.assertFalse(enemy.sources)
                    self.assertIsNone(hero.pending_attack)
                    self.assertEqual(hero.mobility_timer, 0)
                    self.assertIsNone(hero.climbing)
                    position = hero.rect.topleft
                    hp = hero.health
                    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f))
                    section = game.features.active_section
                    for _ in range(14):
                        game.tick({key: True, pygame.K_SPACE: True})
                    self.assertEqual(game.features.active_section, section)
                    game.enemies = []
                    game.draw()
                    self.assertEqual(game.features.rendered_sections, (section,))
                    self.assertEqual(hero.rect.topleft, position)
                    self.assertEqual(hero.health, hp)
                    self.assertIsNone(hero.pending_attack)
                    game.tick({key: True})
                    self.assertEqual(hero.rect.midbottom, (t.x + direction * 184, t.deck_y))
                    game.enemies = []
                    game.draw()
                    self.assertEqual(game.features.rendered_sections, (game.features.active_section,))
                    self.assertEqual(hero.facing_right, direction > 0)
                    self.assertEqual(game.features.active_section, t.index + (direction == 1))
                    left = game.features.active_section * 1280
                    self.assertEqual(game.camera.x, max(left, min(left + 480, hero.rect.centerx - 400)))
                    self.assertIs(game.world, original_world)
                    self.assertEqual(game.mode, 'play')
                    self.assertEqual(game.expedition.wave_claims, original_claims)
                    for _ in range(15):
                        game.tick({key: True})
                    self.assertIsNone(game.transition)
                    game.enemies = []
                    game.expedition_interact()
                    self.assertIsNone(game.transition)
                    self.assertGreater(game.features.passage_cooldown, 0)
                    sections.add(hero.rect.centerx // 1280)
            self.assertEqual(sections, set(range(8)))
            game.campaign.update_checkpoint(9300)
            self.assertEqual(game.campaign.checkpoint, 9224)
            game.features.retry(game.campaign.checkpoint)
            self.assertEqual(game.features.passage_cooldown, 0)
            self.assertFalse(game.features.exit_ready)

    def test_section_bounds_scenes_and_retry(self):
        from camera import Camera
        camera = Camera(4000)
        camera.update(pygame.Rect(1800, 0, 40, 40))
        self.assertEqual(camera.x, 1420)
        game = self.game
        game.reset_game('warrior')
        game.launch_expedition(3, debug=True)
        for section in range(8):
            left = section * 1280
            for x, expected in ((left + 1, left), (left + 1279, left + 480)):
                game.features.reposition(game, (x, 560))
                self.assertEqual(game.camera.x, expected)
                game.draw()
                self.assertEqual(game.features.rendered_sections, (section,))
            game.features.retry(left + 96)
            self.assertEqual(game.features.active_section, section)
            self.assertEqual(game.camera.bounds, (left, left + 1280))

    def test_inactive_enemy_and_source_isolation(self):
        from projectile import DamageSource
        from unittest.mock import Mock
        game = self.game
        game.reset_game('warrior')
        game.launch_expedition(3, debug=True)
        game.state.wave = 2
        game.state.spawned = 1
        game.spawn()
        enemy = game.enemies[0]
        enemy.rect.center = game.knight.rect.center
        enemy.update = Mock()
        enemy.draw = Mock()
        source = DamageSource(game.knight.rect, 100, 'enemy', 30, owner=enemy)
        game.sources.append(source)
        source.draw = Mock()
        health = game.knight.health
        game.tick({})
        game.draw()
        self.assertEqual(game.knight.health, health)
        enemy.update.assert_not_called()
        enemy.draw.assert_not_called()
        source.draw.assert_not_called()
        self.assertEqual(source.section, 1)
        wall = DamageSource((1260, 500, 10, 10), 100, 'hero', 30, (30, 0))
        game.sources = [wall]
        game.tick({})
        self.assertFalse(wall.alive)

    def test_seal_and_secondary_priority(self):
        game = self.game
        game.reset_game('ranger')
        game.launch_expedition(3, debug=True)
        game.knight.rect.midbottom = (840, 560)
        game.expedition_interact()
        self.assertIsNone(game.knight.pending_attack)
        self.assertIn('guardians', game.features.notice)
        game.knight.rect.midbottom = (400, 560)
        game.expedition_interact()
        self.assertEqual(game.knight.pending_attack, 'secondary')

    def test_capture_generation(self):
        from capture_underworld_transitions import capture
        with tempfile.TemporaryDirectory() as directory:
            records = capture(Path(directory))
            self.assertEqual(len(records), 28)
            self.assertEqual(len(list(Path(directory).glob('*.png'))), 28)
            for record in records:
                image = pygame.image.load(str(Path(directory) / record['capture']))
                self.assertEqual(image.get_size(), (800, 600))
                left = record['active_section'] * 1280
                self.assertLessEqual(left, record['viewport'][0])
                self.assertLessEqual(record['viewport'][1], left + 1280)
                self.assertEqual(record['rendered_sections'], [record['active_section']])
        type(self).game = Game(Path(self.directory.name) / "save.json")
