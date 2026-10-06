import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import random
import tempfile
import unittest
from pathlib import Path
import pygame
from main import Game
from camp import Camp, WIDTH as CAMP_WIDTH
from camp_interior import QuartermasterStorehouse, WIDTH, POINTS, storehouse_art
from build_web import runtime_files


class StorehouseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = Game(Path(cls.directory.name)/'save.json')

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.directory.cleanup()

    def setUp(self):
        self.game.reset_game('warrior')

    def enter(self):
        game = self.game
        game.knight.rect.midbottom = (182,560)
        game.camera.update(game.knight.rect)
        self.assertEqual(game.world.nearby(game.knight)[0], 'door')
        game.camera.x = 17
        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e))
        self.assertIsInstance(game.world, Camp)
        for _ in range(12): game.tick({})
        self.assertIsInstance(game.world, QuartermasterStorehouse)
        for _ in range(12): game.tick({})

    def test_transition_state_and_return_all_classes(self):
        for class_id in ('warrior','ranger','wizard'):
            game = self.game
            game.reset_game(class_id)
            game.knight.health = 23
            game.state.score = 912
            game.save.cleared_regions = [0]
            hero = game.knight
            hero.secondary()
            self.enter()
            exterior = game.exterior_camp
            position, camera = game.exterior_position, game.exterior_camera
            self.assertIs(game.knight,hero)
            self.assertFalse(hero.sources or game.sources or hero.attacking or hero.rushing)
            self.assertEqual((hero.health,game.state.score,game.save.cleared_regions),(23,912,[0]))
            self.assertEqual(game.camera.world_width,WIDTH)
            self.assertEqual(game.world.ground.width,WIDTH)
            game.knight.rect.midbottom=(90,560)
            game.world.interact(game)
            for _ in range(24): game.tick({})
            self.assertIs(game.world,exterior)
            self.assertEqual(game.knight.rect.topleft,position)
            self.assertEqual(game.camera.x,camera)
            self.assertEqual(game.camera.world_width,CAMP_WIDTH)
            self.assertEqual(game.mode,'camp')

    def test_inspection_escape_pause_and_no_launch(self):
        for class_id in ('warrior','ranger','wizard'):
            game=self.game
            game.reset_game(class_id)
            self.enter()
            snapshot=(game.knight.health,game.state.score,game.class_id,list(game.save.cleared_regions),game.campaign.index)
            for kind,x,label in POINTS[1:]:
                game.knight.rect.midbottom=(x,560)
                game.world.interact(game)
                text=' '.join(game.service_lines() if game.service else game.world.dialogue['lines'])
                if kind == 'counter': self.assertIn('Field Dressing', text)
                if kind=='ledger':
                    self.assertIn('LOCKED',text)
                    self.assertIn('SPORE SOVEREIGN',text)
                    self.assertIn('MOON EATER',text)
                if kind=='equipment': self.assertIn('Defensive movement',text)
                game.draw()
                game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
                self.assertIsNone(game.world.dialogue)
                self.assertEqual(game.mode,'interior')
            self.assertEqual(snapshot,(game.knight.health,game.state.score,game.class_id,list(game.save.cleared_regions),game.campaign.index))
            game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
            self.assertEqual(game.mode,'pause')
            game.activate()
            self.assertEqual(game.mode,'interior')

    def test_bounds_determinism_and_decorative_isolation(self):
        rng=random.getstate()
        a=storehouse_art(); b=storehouse_art()
        self.assertEqual(random.getstate(),rng)
        self.assertEqual(pygame.image.tostring(a,'RGB'),pygame.image.tostring(b,'RGB'))
        self.enter()
        game=self.game
        positions=game.world.ambient_positions()
        for _ in range(90): game.tick({pygame.K_d:True})
        self.assertNotEqual(positions,game.world.ambient_positions())
        self.assertEqual(random.getstate(),rng)
        self.assertFalse(game.world.hazards or game.enemies or game.sources)
        for x in (0,560,WIDTH):
            game.knight.rect.centerx=x
            game.tick({})
            self.assertEqual(game.camera.x,max(0,min(WIDTH-800,game.knight.rect.centerx-400)))
        for _ in range(80): game.tick({pygame.K_d:True})
        self.assertEqual(game.knight.rect.right,WIDTH-28)

    def test_audio_handoff_settings_and_manifest(self):
        self.enter()
        game=self.game; audio=game.audio
        for _ in range(100): audio.update(1/60)
        self.assertIs(audio.music_channel.get_sound(),audio.loops['camp_music'])
        self.assertIs(audio.ambience_channel.get_sound(),audio.loops['camp_interior'])
        audio.settings.update(sound=True,volume=0.5)
        audio.apply_settings()
        self.assertAlmostEqual(audio.music_channel.get_volume(),0.07,delta=0.01)
        audio.settings['sound']=False
        audio.apply_settings()
        self.assertEqual(audio.music_channel.get_volume(),0)
        self.assertEqual(audio.ambience_channel.get_volume(),0)
        game.world.interact(game)
        for _ in range(24): game.tick({})
        for _ in range(100): audio.update(1/60)
        self.assertIs(audio.ambience_channel.get_sound(),audio.loops['camp_ambience'])
        self.assertEqual(audio.music_channel.get_volume(),0)
        audio.settings.update(sound=True,volume=0.7)
        audio.apply_settings()
        files=runtime_files()
        self.assertIn(Path.cwd()/'camp_interior.py',files)
        self.assertIn(Path.cwd()/'assets/audio/camp/interior.wav',files)

    def test_only_storehouse_has_door(self):
        for x in (430,680,1400,1640,1860,2040):
            self.game.knight.rect.midbottom=(x,560)
            self.assertEqual(self.game.world.nearby(self.game.knight)[0],'npc')
        self.game.knight.rect.midbottom=(260,560)
        self.assertIsNone(self.game.world.nearby(self.game.knight))
