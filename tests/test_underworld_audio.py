import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from array import array
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import pygame
from build_web import ROOT, runtime_files
from campaign import ENVIRONMENTS
from main import Game


class ScoreAssetsTests(unittest.TestCase):
    def test_scores_exist_decode_and_ship(self):
        files = runtime_files()
        for name, duration in (('underworld_exploration', 96), ('pyre_regent', 90)):
            path = ROOT / 'assets/audio/tommusic/music' / (name + '.ogg')
            self.assertIn(path, files)
            self.assertGreater(path.stat().st_size, 1000)
            self.assertLess(path.stat().st_size, 3_000_000)
            if shutil.which('ffprobe') and shutil.which('ffmpeg'):
                data = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                    '-show_format', '-of', 'json', str(path)]))
                stream = data['streams'][0]
                self.assertEqual((stream['codec_name'], stream['sample_rate'], stream['channels']),
                                 ('vorbis', '32000', 2))
                self.assertAlmostEqual(float(data['format']['duration']), duration, places=2)
                decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                    '-f', 'f32le', '-c:a', 'pcm_f32le', '-'])
                pcm = array('f')
                pcm.frombytes(decoded)
                self.assertLess(max(abs(v) for v in pcm), .95)
                # Compare seam's adjacent samples to normal local movement.
                for channel in (0, 1):
                    self.assertLess(abs(pcm[channel] - pcm[-2 + channel]), .08)


class ScoreFlowTests(unittest.TestCase):
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
        self.settle()

    def settle(self):
        for _ in range(70):
            self.game.audio.update(1 / 60)

    def spawn(self, wave):
        self.game.state.wave = wave
        self.game.state.spawned = 1
        self.game.spawn(wave == 8)

    def test_mapping_and_boss_only_transition_preserves_ambience(self):
        audio = self.game.audio
        self.assertEqual(ENVIRONMENTS[1]['music'], 'battle_theme')
        self.assertEqual(audio.loop_names, ('underworld_exploration', 'cave_ambience'))
        with patch.object(audio, 'request_loops', wraps=audio.request_loops) as request:
            self.spawn(4)
            request.assert_not_called()
            self.spawn(8)
            request.assert_called_once_with(('pyre_regent', 'cave_ambience'))
        music, ambience = Mock(wraps=audio.music_channel), Mock(wraps=audio.ambience_channel)
        with patch.object(audio, 'music_channel', music), patch.object(audio, 'ambience_channel', ambience):
            self.settle()
            music.play.assert_called_once()
            ambience.play.assert_not_called()
            ambience.stop.assert_not_called()
            for _ in range(100):
                audio.boss_music()
                audio.update(1 / 60)
            music.play.assert_called_once()
        self.assertIs(audio.music_channel.get_sound(), audio.loops['pyre_regent'])

    def test_pause_retry_and_leaving_restore_correct_score(self):
        game = self.game
        self.spawn(8)
        self.settle()
        game.change_mode('pause')
        game.change_mode('play')
        self.settle()
        self.assertEqual(game.audio.loop_names[0], 'pyre_regent')
        game.change_mode('over')
        game.selection = 0
        game.transition_action = True
        game.activate()
        game.transition_action = False
        self.settle()
        self.assertEqual(game.audio.loop_names[0], 'underworld_exploration')
        self.spawn(8)
        self.settle()
        self.assertEqual(game.audio.loop_names[0], 'pyre_regent')
        game.enter_camp()
        self.settle()
        self.assertEqual(game.audio.loop_names, ('camp_music', 'camp_ambience'))
        game.launch_expedition(3, debug=True)
        self.settle()
        self.assertEqual(game.audio.loop_names[0], 'underworld_exploration')
        game.launch_expedition(0, debug=True)
        self.settle()
        self.assertEqual(game.audio.loop_names[0], 'forest_theme')

    def test_retry_during_pending_boss_fade_cancels_boss(self):
        self.spawn(8)
        self.game.change_mode('over')
        self.game.transition_action = True
        self.game.selection = 0
        self.game.activate()
        self.game.transition_action = False
        self.settle()
        self.assertEqual(self.game.audio.loop_names[0], 'underworld_exploration')
        self.assertIsNone(self.game.audio.pending_loops)

    def test_boss_clear_returns_to_exploration(self):
        game = self.game
        self.spawn(8)
        self.settle()
        game.enemies = []
        game.state.phase = 'combat'
        game.tick({})
        self.settle()
        self.assertEqual(game.state.phase, 'exit')
        self.assertEqual(game.audio.loop_names[0], 'underworld_exploration')
