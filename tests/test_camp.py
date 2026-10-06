import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import json
import tempfile
import unittest
from pathlib import Path
import pygame
from main import Game
from camp import Camp, POSITIONS, GATES, STATIONS, WIDTH, courtyard, npc_sprite
from persistence import SaveData
from build_camp_audio import build
from build_web import runtime_files


class CampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = Game(Path(cls.directory.name) / 'camp.json')

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.directory.cleanup()

    def setUp(self):
        self.game.save.cleared_regions = []
        self.game.reset_game('warrior')

    def interact(self, x):
        self.game.service = None
        self.game.world.dialogue = None
        self.game.knight.rect.centerx = x
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e))

    def test_title_class_camp_all_heroes(self):
        for index,name in enumerate(('warrior','ranger','wizard')):
            self.game.change_mode('title')
            self.game.activate()
            for _ in range(30): self.game.tick({})
            self.assertEqual(self.game.mode,'class')
            self.game.selection=index
            self.game.activate()
            for _ in range(30): self.game.tick({})
            self.assertEqual(self.game.mode,'camp')
            self.assertEqual(self.game.knight.class_id,name)
            self.assertIsInstance(self.game.world,Camp)
            self.game.tick({pygame.K_d:True})
            self.assertGreater(self.game.knight.rect.x,380)

    def test_services_dialogue_escape_and_health(self):
        game=self.game
        game.knight.health=12
        self.interact(POSITIONS[3])
        self.assertEqual(game.knight.health,game.knight.max_health)
        self.assertIn('fully restored',' '.join(game.world.dialogue['lines']))
        self.interact(POSITIONS[3])
        self.assertIn('Already well',' '.join(game.world.dialogue['lines']))
        for x in POSITIONS[1:]:
            self.interact(x)
            self.assertGreaterEqual(len(game.service_lines() if game.service else game.world.dialogue['lines']),3)
            game.draw()
        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertIsNone(game.world.dialogue)
        self.assertEqual(game.mode,'camp')
        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertEqual(game.mode,'pause')
        game.activate()
        self.assertEqual(game.mode,'camp')

    def test_gates_intel_lock_and_launch(self):
        game=self.game
        self.interact(GATES[1])
        self.assertIn('LOCKED',' '.join(game.world.dialogue['lines']))
        game.world.interact(game)
        self.assertEqual(game.mode,'camp')
        self.interact(GATES[0])
        self.assertIn('SPORE SOVEREIGN',' '.join(game.world.dialogue['lines']))
        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
        for _ in range(100): game.tick({})
        self.assertEqual(game.mode,'play')
        self.assertEqual(game.campaign.index,0)
        self.assertFalse(game.launch_expedition(2))
        self.assertTrue(game.launch_expedition(2,debug=True))

    def test_return_score_health_cleanup_and_completion(self):
        game=self.game
        for index in range(3):
            self.assertTrue(game.launch_expedition(index))
            game.state.score=1234
            game.knight.health=10
            game.knight.secondary()
            game.campaign.exit_open=True
            game.state.phase='exit'
            game.knight.rect.center=game.world.exit.center
            game.tick({})
            for _ in range(100): game.tick({})
            self.assertEqual(game.mode,'results')
            game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
            for _ in range(30): game.tick({})
            self.assertEqual(game.mode,'camp')
            self.assertEqual(game.state.score,1234)
            self.assertEqual(game.knight.health,game.knight.max_health)
            self.assertEqual(game.knight.rect.bottom,560)
            self.assertFalse(game.sources or game.enemies or game.knight.sources)
            self.assertEqual(game.knight.secondary_cooldown,0)
            self.assertIn(index,SaveData(game.save.path).cleared_regions)
        self.assertTrue(game.campaign.complete)
        self.assertIn('welcomes',game.world.notice)

    def test_attacks_only_touch_dummy(self):
        game=self.game
        for name in ('warrior','ranger','wizard'):
            game.reset_game(name)
            game.knight.rect.centerx=game.world.dummy.x-48
            game.knight.facing_right=True
            game.knight.attack()
            for _ in range(25):
                game.tick({})
            self.assertGreater(game.world.hits,0)
            self.assertEqual(game.knight.health,game.knight.max_health)
            self.assertEqual(game.state.score,0)

    def test_deterministic_original_art_and_audio(self):
        self.assertEqual(courtyard().get_size(),(WIDTH,600))
        self.assertEqual(pygame.image.tostring(courtyard(),'RGB'),pygame.image.tostring(courtyard(),'RGB'))
        sprites=[pygame.image.tostring(npc_sprite(i)['Idle'][0],'RGBA') for i in range(7)]
        self.assertEqual(len(set(sprites)),7)
        self.assertTrue(all(npc_sprite(i)['Idle'][0].get_size()==(250,250) for i in range(7)))
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)
            build(target)
            first={p.name:p.read_bytes() for p in target.iterdir()}
            build(target)
            self.assertEqual(first,{p.name:p.read_bytes() for p in target.iterdir()})
            for name,data in first.items():
                self.assertEqual(data,(Path('assets/audio/camp')/name).read_bytes())

    def test_audio_reserved_channels_and_mute(self):
        audio=self.game.audio
        for _ in range(100): audio.update(1/60)
        self.assertIs(audio.music_channel.get_sound(),audio.loops['camp_music'])
        self.assertIs(audio.ambience_channel.get_sound(),audio.loops['camp_ambience'])
        self.game.launch_expedition(0)
        for _ in range(100): audio.update(1/60)
        self.assertIs(audio.music_channel.get_sound(),audio.loops['forest_theme'])
        self.game.enter_camp()
        for _ in range(100): audio.update(1/60)
        self.assertIs(audio.music_channel.get_sound(),audio.loops['camp_music'])
        audio.settings['sound']=False
        audio.apply_settings()
        self.assertEqual(audio.music_channel.get_volume(),0)
        self.assertEqual(audio.ambience_channel.get_volume(),0)
        audio.settings['sound']=True
        audio.apply_settings()
        self.assertIn(Path.cwd()/'camp.py',runtime_files())

    def test_save_migration_and_invalid_clears(self):
        path=Path(self.directory.name)/'migration.json'
        for furthest in range(3):
            path.write_text(json.dumps({'version':2,'furthest_environment':furthest,'last_class':'huntress','high_score':99}))
            save=SaveData(path)
            self.assertEqual(save.cleared_regions,list(range(furthest)))
            self.assertEqual(save.last_class,'ranger')
            self.assertTrue(save.gate_unlocked(furthest))
            save.save()
            self.assertEqual(SaveData(path).cleared_regions,list(range(furthest)))
        path.write_text(json.dumps({'version':3,'cleared_regions':[True,-1,0,0,5,'2']}))
        self.assertEqual(SaveData(path).cleared_regions,[0])

    def test_wide_hub_stations_camera_and_ambient_isolation(self):
        game = self.game
        self.assertGreater(game.world.width, 2 * game.screen.get_width())
        self.assertEqual(len(set(kind for kind,rect in STATIONS)), 7)
        self.assertEqual(len(set(rect for kind,rect in STATIONS)), 7)
        ordered = sorted(POSITIONS)
        self.assertTrue(all(b-a >= 180 for a,b in zip(ordered,ordered[1:])))
        self.assertLess(GATES[0]-game.knight.rect.centerx, 550)
        before = game.world.ambient_positions()
        physics = (game.world.ground.copy(), list(game.world.platforms), game.state.score, game.knight.health)
        for _ in range(90): game.tick({})
        self.assertNotEqual(before, game.world.ambient_positions())
        self.assertEqual(physics, (game.world.ground, game.world.platforms, game.state.score, game.knight.health))
        for x in (100,1100,2150):
            game.knight.rect.centerx = x
            game.tick({})
            self.assertEqual(game.camera.x,max(0,min(WIDTH-800,x-400)))
            game.draw()
        self.assertEqual(game.camera.x, WIDTH-800)
        for i,x in enumerate(GATES):
            self.interact(x)
            self.assertEqual(game.world.dialogue['gate'],i)
        game.world.dialogue = None
        game.knight.rect.x = WIDTH-40
        for _ in range(20): game.tick({pygame.K_d:True})
        self.assertLessEqual(game.knight.rect.right, WIDTH)
