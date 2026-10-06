import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from pathlib import Path
import tempfile
import unittest
import pygame
from main import Game
from camp import ADVENTURERS, POSITIONS, GATES, adventurer_dialogue
from camp_interior import QuartermasterStorehouse
from zerie_runtime import (CAMP_SERVICE_ACTORS, CAMP_WORKER_ACTORS,
                           CAMP_ADVENTURER_ACTORS, CAMP_ACTIONS, camp_actor,
                           action_sources, source_path, draw_camp_actor)
from build_web import runtime_files


class ZerieCampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = Game(Path(cls.directory.name)/'save.json')

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.directory.cleanup()

    def setUp(self):
        self.game.reset_game('knight')
        self.game.save.cleared_regions = []

    def test_roles_sources_animation_and_grounding(self):
        self.assertEqual(CAMP_SERVICE_ACTORS, ('Swordsman', 'Armored Axeman', 'Lancer',
                         'Priest', 'Wizard', 'Knight Templar', 'Soldier'))
        for actor in set(CAMP_SERVICE_ACTORS+CAMP_WORKER_ACTORS+CAMP_ADVENTURER_ACTORS):
            frames = camp_actor(actor)
            self.assertEqual(frames.actor, actor)
            for state, action in action_sources(actor, CAMP_ACTIONS).items():
                sheet = pygame.image.load(str(source_path(actor, action)))
                pixels = {pygame.image.tobytes(pygame.transform.scale(
                    sheet.subsurface((x,0,100,100)), (250,250)), 'RGBA')
                    for x in range(0,sheet.get_width(),100)}
                self.assertGreater(len({pygame.image.tobytes(f,'RGBA') for f in frames[state]}), 1)
                for frame in frames[state]:
                    self.assertIn(pygame.image.tobytes(frame,'RGBA'), pixels)
                    bounds = frame.get_bounding_rect()
                    self.assertGreater(bounds.left, 0)
                    self.assertLess(bounds.right, 250)
            canvas = pygame.Surface((400,600), pygame.SRCALPHA)
            draw_camp_actor(canvas, frames, 200, 560, 0)
            self.assertLessEqual(abs(canvas.get_bounding_rect().bottom-560), 5)

    def test_nearest_interactions_and_progression_hooks(self):
        game = self.game
        points = [182]+POSITIONS[1:]+list(GATES)+[n['x'] for n in ADVENTURERS]
        self.assertTrue(all(abs(a-b)>=76 for i,a in enumerate(points) for b in points[i+1:]))
        for i,npc in enumerate(ADVENTURERS):
            for offset in (-37,0,37):
                game.knight.rect.midbottom = (npc['x']+offset,560)
                self.assertEqual(game.world.nearby(game.knight)[:2], ('adventurer',i))
            for clears,state in [([], 'locked' if npc['realm'] else 'available'),
                                 (list(range(npc['realm'])), 'available'),
                                 ([npc['realm']], 'cleared')]:
                game.save.cleared_regions = clears
                before = (game.state.score, game.knight.health, list(clears))
                game.world.dialogue = None
                game.world.interact(game)
                self.assertEqual(game.world.dialogue, adventurer_dialogue(game.save,i))
                self.assertIn(npc['name'],game.world.dialogue['title'])
                self.assertIn(state.upper(),game.world.dialogue['lines'][0])
                self.assertEqual(before,(game.state.score,game.knight.health,game.save.cleared_regions))
                game.world.interact(game)
                self.assertIsNone(game.world.dialogue)
            game.knight.rect.bottom = 400
            self.assertIsNone(game.world.nearby(game.knight))

    def test_interior_and_web_consistency(self):
        interior = QuartermasterStorehouse()
        self.assertIs(interior.quartermaster, self.game.world.sprites[0])
        self.assertEqual([w.actor for w in interior.workers], list(CAMP_WORKER_ACTORS[:2]))
        files = runtime_files()
        for actor in set(CAMP_SERVICE_ACTORS+CAMP_WORKER_ACTORS+CAMP_ADVENTURER_ACTORS):
            for action in action_sources(actor,CAMP_ACTIONS).values():
                self.assertIn(source_path(actor,action),files)
        vendor = [p for p in files if 'vendor/zerie' in str(p)]
        self.assertTrue(all(p.suffix=='.png' and 'with shadows' not in str(p) for p in vendor))
        self.assertNotIn(source_path('Bat','Idle'),files)
