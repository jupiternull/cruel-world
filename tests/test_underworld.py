import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import tempfile
import unittest
from pathlib import Path
import pygame
from campaign import Campaign, ENVIRONMENTS
from main import Game
from underworld import CATALOG, ENCOUNTERS, PACK, load_actor, runtime_sources
from persistence import SaveData
from projectile import DamageSource


class UnderworldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = Game(Path(cls.directory.name) / 'save.json')

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.directory.cleanup()

    def setUp(self):
        self.game.reset_game('warrior')
        self.game.launch_expedition(3, debug=True)

    def test_registration_and_full_local_catalog(self):
        self.assertEqual([e['id'] for e in ENVIRONMENTS], ['forest', 'cave', 'graveyard', 'underworld'])
        self.assertGreater(ENVIRONMENTS[3]['width'], max(e['width'] for e in ENVIRONMENTS[:3]) * 2)
        self.assertEqual(set(CATALOG), {p.name for p in PACK.iterdir() if p.is_dir()})
        self.assertEqual(len(CATALOG), 20)
        self.assertTrue(all(p.is_file() for p in runtime_sources()))
        self.assertEqual({a for wave in ENCOUNTERS for a in wave}, set(CATALOG))

    def test_all_designs_spawn_and_load_actions(self):
        game = self.game
        seen = []
        for wave, actors in enumerate(ENCOUNTERS, 1):
            game.state.wave = wave
            self.assertEqual(game.state.wave_size, len(actors))
            for i, actor in enumerate(actors, 1):
                game.state.spawned = i
                game.spawn(wave == 8)
                enemy = game.enemies[-1]
                self.assertEqual(enemy.actor, actor)
                seen.append(actor)
                for state in ('Idle', 'Walk', 'Flight', 'Attack', 'Take Hit', 'Death'):
                    self.assertTrue(enemy.frames[state])
                    self.assertTrue(any(f.get_bounding_rect().width for f in enemy.frames[state]))
                enemy.take_damage(enemy.max_health * 4)
                for _ in range(150):
                    enemy.update_animation(1000 / 60)
                self.assertTrue(enemy.death_anim_done)
        self.assertEqual(set(seen), set(CATALOG))

    def test_seals_require_guardians_retry_preserves_and_exit_requires_boss(self):
        game = self.game
        for name, wave in (('seal0', 1), ('seal1', 4), ('seal2', 7)):
            game.knight.rect.midbottom = (game.features.objects[name][0], 560)
            game.features.interact(game)
            self.assertNotIn(name, game.features.claimed)
            game.expedition.wave_claims.add(wave)
            game.features.interact(game)
            self.assertIn(name, game.features.claimed)
        game.features.retry(5120)
        self.assertEqual(len(game.features.claimed), 3)
        self.assertFalse(game.features.exit_ready)
        game.expedition.wave_claims.add(8)
        game.features.update(game)
        self.assertTrue(game.features.exit_ready)
        self.assertTrue(game.campaign.exit_open)

    def test_checkpoints_hazards_and_four_realm_save(self):
        game = self.game
        for point in game.world.data['checkpoints'][1:]:
            self.assertTrue(game.campaign.update_checkpoint(point))
            self.assertEqual(game.campaign.checkpoint, point)
        game.knight.rect.midbottom = (960, 560)
        health = game.knight.health
        game.tick({})
        self.assertLess(game.knight.health, health)
        for i in range(4):
            game.save.complete_expedition(i, 'warrior', 200, [], game.expedition)
        loaded = SaveData(game.save.path)
        self.assertEqual(loaded.cleared_regions, [0, 1, 2, 3])
        self.assertEqual(loaded.furthest_environment, 3)
        self.assertEqual(len(loaded.materials), 4)
        self.assertIn('3', loaded.records)
        campaign = Campaign()
        for _ in range(3):
            self.assertTrue(campaign.advance())
        self.assertFalse(campaign.complete)
        self.assertFalse(campaign.advance())
        self.assertTrue(campaign.complete)

    def test_caster_projectile_and_all_classes_can_damage_roles(self):
        game = self.game
        for class_id in ('warrior', 'ranger', 'wizard'):
            game.reset_game(class_id)
            game.launch_expedition(3, debug=True)
            for wave in (4, 5, 8):
                game.state.wave = wave
                game.state.spawned = 1
                game.spawn(wave == 8)
                enemy = game.enemies[-1]
                source = DamageSource(enemy.rect, 20, 'hero', 2)
                before = enemy.health
                self.assertTrue(source.hit(enemy))
                self.assertLess(enemy.health, before)
        boss = game.enemies[-1]
        boss.facing_right = True
        boss.do_attack(game.knight.rect)
        self.assertGreater(boss.windup, 40)
        boss.release_attack(game.world)
        self.assertTrue(boss.sources[0].frames)

    def test_real_primary_attacks_hit_with_every_class(self):
        game = self.game
        for class_id in ('warrior', 'ranger', 'wizard'):
            game.reset_game(class_id)
            game.launch_expedition(3, debug=True)
            game.state.phase = 'combat'
            game.state.spawned = 1
            game.spawn()
            enemy = game.enemies[-1]
            enemy.rect.midbottom = (700, 560)
            enemy.speed = 0
            enemy.attack_timer = 1000
            hero = game.knight
            hero.rect.midbottom = (640, 560)
            hero.facing_right = True
            hero.on_ground = True
            before = enemy.health
            hero.attack()
            for _ in range(45):
                game.tick({})
            self.assertLess(enemy.health, before, class_id)

    def test_optional_actions_fallback_and_boss_grounding(self):
        from unittest.mock import patch
        from underworld import sheets
        paths = sheets('Demon_A')
        paths.pop('Hurt')
        paths.pop('Death')
        paths.pop('Walk')
        paths.pop('Attack01')
        with patch('underworld.sheets', return_value=paths):
            frames = load_actor('Demon_A')
        for state in ('Walk', 'Attack', 'Take Hit', 'Death', 'Shield'):
            self.assertEqual(frames.action_sources[state], 'Idle')
        game = self.game
        for wave in (4, 8):
            game.state.wave = wave
            game.state.spawned = 1
            game.spawn(wave == 8)
            enemy = game.enemies[-1]
            for _ in range(60):
                enemy.update(game.knight, game.world)
            self.assertEqual(enemy.rect.bottom, 560)

    def test_headless_capture_completes_real_objective_flow(self):
        from capture_underworld import capture
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(set(capture(Path(directory))), set(CATALOG))
            self.assertEqual(len(list(Path(directory).glob('*.png'))), 10)
        pygame.init()
        pygame.display.set_mode((800, 600))
