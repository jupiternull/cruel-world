import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from main import Game
from campaign import ENVIRONMENTS
from persistence import SaveData
from zerie_runtime import PLAYER_ACTORS, REALM_ROSTERS, source_path
from build_web import runtime_files


class ZerieIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = Game(Path(cls.directory.name) / 'save.json')

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.directory.cleanup()

    def test_class_names_aliases_and_legacy_progress(self):
        for value, canonical in [('knight', 'warrior'), ('archer', 'ranger'),
                                 ('warrior', 'warrior'), ('ranger', 'ranger'),
                                 ('huntress', 'ranger'), ('wizard', 'wizard')]:
            self.game.reset_game(value)
            self.assertEqual(self.game.knight.class_id, canonical)
            self.assertEqual(self.game.knight.stats['name'], PLAYER_ACTORS[canonical])
            path = Path(self.directory.name) / 'legacy.json'
            path.write_text(json.dumps({'version': 4, 'last_class': value,
                'cleared_regions': [0], 'purchased': {canonical: [0]},
                'equipped': {canonical: 0}, 'records': {'0': {'best': {canonical: 123}}}}))
            save = SaveData(path)
            self.assertEqual(save.last_class, canonical)
            self.assertEqual(save.equipped[canonical], 0)
            self.assertEqual(save.records['0']['best'][canonical], 123)

    def test_real_sources_fallbacks_and_anchors(self):
        for class_id, actor in PLAYER_ACTORS.items():
            frames = self.game.assets['heroes'][class_id]
            self.assertEqual(frames.actor, actor)
            self.assertEqual(frames.action_sources['Jump'], 'Walk')
            self.assertEqual(frames.action_sources['Fall'], 'Walk')
            if actor == 'Knight':
                self.assertEqual(frames.action_sources['Roll'], 'Walk')
                self.assertEqual(frames.action_sources['Block'], 'Block')
            if actor == 'Archer':
                self.assertEqual(frames.action_sources['Attack3'], 'Attack02')
            for state, sequence in frames.items():
                source = pygame.image.load(str(source_path(actor, frames.action_sources[state])))
                source_pixels = {pygame.image.tobytes(pygame.transform.scale(
                    source.subsurface((x, 0, 100, 100)), (250, 250)), 'RGBA')
                    for x in range(0, source.get_width(), 100)}
                for frame in sequence:
                    self.assertIn(pygame.image.tobytes(frame, 'RGBA'), source_pixels)
                    bounds = frame.get_bounding_rect()
                    self.assertGreater(bounds.width, 0)
                    self.assertGreater(bounds.left, 0)
                    self.assertLess(bounds.right, frame.get_width())
            self.assertGreater(frames.anchor.height, 40)

    def test_each_realm_spawns_its_complete_faction_roster(self):
        for index, environment in enumerate(ENVIRONMENTS):
            self.game.reset_game('knight')
            self.game.launch_expedition(index, debug=True)
            roster = REALM_ROSTERS[environment['id']]
            self.assertEqual(environment['faction'], roster['faction'])
            self.game.state.wave = 1
            for spawn, (actor, species) in enumerate(roster['enemies'], 1):
                self.game.state.spawned = spawn
                self.game.spawn()
                enemy = self.game.enemies[-1]
                self.assertEqual((enemy.actor, enemy.species), (actor, species))
                self.assertTrue(enemy.image.get_bounding_rect().width)
                enemy.take_damage(enemy.max_health)
                for _ in range(100):
                    enemy.update_animation(1000 / 60)
                self.assertTrue(enemy.death_anim_done)
            self.game.spawn(boss=True)
            self.assertEqual(self.game.enemies[-1].species, environment['boss'])

    def test_web_stages_only_required_pack_sheets(self):
        files = runtime_files()
        self.assertIn(source_path('Knight', 'Block'), files)
        self.assertIn(source_path('Werebear', 'Walk'), files)
        self.assertFalse(any('with shadows' in str(p) or p.suffix == '.aseprite' for p in files))
        self.assertTrue(any(p.name == 'zerie_runtime.py' for p in files))
