import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pygame
from game_state import GameState
from persistence import SaveData
from audio import AudioManager
from config import ASSETS_DIR
from main import Game
from entities.monster import Monster
from entities.effects import PowerUp


class LogicTests(unittest.TestCase):
    def test_waves_require_clear_and_are_bounded(self):
        state = GameState()
        for _ in range(150):
            state.update_wave()
        self.assertEqual(state.phase, 'combat')
        for _ in range(state.wave_size):
            state.spawn_timer = state.spawn_rate
            self.assertEqual(state.update_wave(0), 'spawn')
        self.assertIsNone(state.update_wave(1))
        self.assertEqual(state.update_wave(0), 'clear')
        self.assertEqual(state.score, 250)
        for _ in range(180):
            state.update_wave()
        self.assertEqual(state.wave, 2)
        state.wave = 1000
        self.assertLessEqual(state.wave_size, 18)
        self.assertLessEqual(state.enemy_limit, 6)
        self.assertGreaterEqual(state.spawn_rate, 75)
        self.assertTrue(state.boss_wave)
        state.wave = 999
        self.assertEqual(state.wave_size, 18)

    def test_pause_freezes_wave(self):
        state = GameState()
        state.paused = True
        for _ in range(500):
            state.update_wave()
        self.assertEqual(state.transition_timer, 150)

    def test_save_validation_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'save.json'
            path.write_text('{bad json')
            save = SaveData(path)
            self.assertEqual(save.high_score, 0)
            save.record(500)
            save.record(100)
            save.settings['sound'] = False
            self.assertTrue(save.save())
            loaded = SaveData(path)
            self.assertEqual(loaded.high_score, 500)
            self.assertFalse(loaded.settings['sound'])
            path.write_text(json.dumps({'high_score': -1, 'settings': {'volume': 10, 'sound': 'yes'}}))
            loaded = SaveData(path)
            self.assertEqual(loaded.high_score, 0)
            self.assertEqual(loaded.settings['volume'], 0.7)
            self.assertTrue(loaded.settings['sound'])
            save.path = Path(root)
            self.assertFalse(save.save())
            self.assertTrue(save.error)

    def test_atomic_save_with_tmp_suffix_and_failed_replace(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'save.tmp'
            save = SaveData(path)
            save.record(100)
            original = path.read_bytes()
            save.high_score = 200
            with patch.object(Path, 'replace', side_effect=OSError('cannot replace')):
                self.assertFalse(save.save())
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(root).iterdir()), [path])
            self.assertTrue(save.save())
            self.assertEqual(SaveData(path).high_score, 200)
            self.assertFalse(save.error)

    def test_supplied_audio_decodes(self):
        pygame.init()
        audio = AudioManager({'sound': True, 'volume': 0.7})
        self.assertEqual(set(audio.sounds), {'attack', 'hit', 'kill', 'pickup', 'score',
                                            'jump', 'wave', 'boss', 'game_over', 'menu'})
        self.assertTrue(audio.music_loaded)
        for path in (Path(ASSETS_DIR) / 'audio').rglob('*'):
            if path.suffix in ('.wav', '.ogg'):
                with self.subTest(asset=path.name):
                    self.assertGreater(pygame.mixer.Sound(str(path)).get_length(), 0)
        audio.play('menu')
        audio.settings['sound'] = False
        audio.apply_settings()
        for sound in audio.sounds.values():
            self.assertEqual(sound.get_volume(), 0)

    def test_audio_absent_and_unavailable(self):
        pygame.init()
        with tempfile.TemporaryDirectory() as root:
            audio = AudioManager({'sound': True, 'volume': 0.7}, root)
            self.assertEqual(audio.sounds, {})
            audio.play('attack')
            for mode in ('title', 'pause', 'over', 'victory', 'class', 'settings', 'play'):
                audio.set_mode(mode)
            audio.pause(True)
            audio.pause(False)
        pygame.mixer.quit()
        with patch('pygame.mixer.init', side_effect=pygame.error('no device')):
            audio = AudioManager({'sound': True, 'volume': 0.7})
            self.assertFalse(audio.available)
            audio.play('hit')
            audio.set_mode('title')
            audio.set_mode('play')
            audio.apply_settings()

    def test_invalid_custom_audio_falls_back_to_wav(self):
        pygame.init()
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            (directory / 'attack.ogg').write_bytes(b'invalid audio')
            source = Path(ASSETS_DIR) / 'audio/sfx/tap.wav'
            (directory / 'attack.wav').write_bytes(source.read_bytes())
            audio = AudioManager({'sound': True, 'volume': 0.7}, directory)
            self.assertIn('attack', audio.sounds)
            self.assertFalse(audio.music_loaded)

    def test_imported_combat_audio_falls_back_when_bundle_missing(self):
        pygame.init()
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            (directory / 'attack.wav').write_bytes((Path(ASSETS_DIR) / 'audio/sfx/tap.wav').read_bytes())
            audio = AudioManager({'sound': True, 'volume': 0.7}, directory)
            with patch('pygame.mixer.find_channel') as channel:
                for name in ('sword_attack', 'bow_attack', 'fireball', 'arcane_wave'):
                    audio.play(name)
                    channel.return_value.play.assert_called_with(audio.sounds['attack'])

    def test_environment_keeps_fallback_music_when_bundle_missing(self):
        from campaign import ENVIRONMENTS
        pygame.init()
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            (directory / 'music.ogg').write_bytes((Path(ASSETS_DIR) / 'audio/music/Ironchest_dungeon001.ogg').read_bytes())
            audio = AudioManager({'sound': True, 'volume': 0.7}, directory)
            audio.environment(ENVIRONMENTS[0])
            self.assertTrue(pygame.mixer.music.get_busy())
            audio.pause(True)
            audio.environment(ENVIRONMENTS[1])
            self.assertFalse(pygame.mixer.music.get_busy())
            audio.pause(False)
            self.assertTrue(pygame.mixer.music.get_busy())

    def test_realm_audio_without_fallback_can_change_to_missing_realm(self):
        from campaign import ENVIRONMENTS
        pygame.init()
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / 'tommusic/music'
            directory.mkdir(parents=True)
            (directory / 'forest_theme.ogg').write_bytes((Path(ASSETS_DIR) / 'audio/tommusic/music/forest_theme.ogg').read_bytes())
            audio = AudioManager({'sound': True, 'volume': 0.7}, root)
            audio.environment(ENVIRONMENTS[0])
            audio.environment(ENVIRONMENTS[1])
            self.assertFalse(audio.music_channel.get_busy())

    def test_audio_variants_do_not_change_gameplay_random_state(self):
        import random
        pygame.init()
        audio = AudioManager({'sound': True, 'volume': 0.7})
        before = random.getstate()
        audio.play('sword_attack')
        self.assertEqual(random.getstate(), before)

    def test_missing_required_asset_exits_cleanly(self):
        from main import main
        with patch('sys.argv', ['main.py']), patch('main.Game', side_effect=FileNotFoundError('missing hero')), \
                patch('pygame.quit') as quit_game, patch('sys.stderr') as error:
            with self.assertRaises(SystemExit) as result:
                main()
        self.assertEqual(result.exception.code, 1)
        quit_game.assert_called_once()
        self.assertIn('Could not start Cruel World', ''.join(call.args[0] for call in error.write.call_args_list))


class GameplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = Game(Path(cls.directory.name) / 'save.json')

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.directory.cleanup()

    def setUp(self):
        self.game.save = SaveData(Path(self.directory.name) / (self._testMethodName + '.json'))
        self.game.audio.settings = self.game.save.settings
        self.game.audio.apply_settings()
        self.game.reset_game()
        self.keys = {key: False for key in (pygame.K_a, pygame.K_d, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_s, pygame.K_DOWN, pygame.K_SPACE, pygame.K_w)}

    def test_buffered_combo_and_damage_interrupt(self):
        knight = self.game.knight
        knight.attack()
        knight.attack()
        for _ in range(20):
            knight.update_animation(1000 / 60)
        self.assertEqual(knight.state, 'Attack2')
        self.assertTrue(knight.attacking)
        knight.take_damage(8)
        self.assertFalse(knight.attacking)
        self.assertIsNone(knight.attack_hitbox)
        self.assertFalse(knight.combo_buffer)

    def test_combo_window_respects_ability_locks(self):
        knight = self.game.knight
        for ability in ('dash', 'roll', 'slide'):
            with self.subTest(ability=ability):
                knight.set_state('Run')
                knight.dash_cooldown = knight.roll_cooldown = 0
                knight.combo_stage = 1
                knight.combo_timer = 25
                getattr(knight, ability)()
                state = knight.state
                self.assertTrue(knight.state_locked)
                knight.attack()
                self.assertEqual(knight.state, state)
                self.assertFalse(knight.attacking)

    def test_one_hit_per_swing_and_single_pickup_update(self):
        game = self.game
        game.state.phase = 'combat'
        game.state.spawn_timer = -10000
        game.spawn()
        enemy = game.enemies[0]
        enemy.rect.x = game.knight.rect.x + 45
        enemy.rect.y = game.knight.rect.y + 16
        enemy.health = enemy.max_health = 100
        enemy.attack_timer = 1000
        game.knight.attack()
        for _ in range(15):
            game.tick(self.keys)
        self.assertEqual(enemy.health, 78)
        pickup = PowerUp(400, 200)
        game.powerups = [pickup]
        game.tick(self.keys)
        self.assertEqual(pickup.lifetime, 299)

    def test_pause_restart_and_game_over(self):
        game = self.game
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        before = game.knight.rect.copy()
        for _ in range(20):
            game.tick(self.keys)
        self.assertEqual(game.knight.rect, before)
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.state.score = 700
        game.knight.take_damage(game.knight.max_health)
        for _ in range(100):
            game.tick(self.keys)
        self.assertEqual(game.mode, 'over')
        self.assertGreaterEqual(game.save.high_score, 700)
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        self.assertEqual(game.mode, 'play')
        self.assertEqual(game.state.score, 0)
        self.assertEqual(game.knight.health, 150)

    def test_pause_freezes_all_gameplay_timers(self):
        game = self.game
        game.spawn()
        game.powerups = [PowerUp(400, 200)]
        game.knight.roll()
        game.change_mode('pause')
        before = (game.knight.roll_cooldown, game.knight.invulnerable,
                  game.enemies[0].animation_timer, game.powerups[0].lifetime,
                  game.state.transition_timer)
        for _ in range(120):
            game.tick(self.keys)
        self.assertEqual(before, (game.knight.roll_cooldown, game.knight.invulnerable,
                                 game.enemies[0].animation_timer, game.powerups[0].lifetime,
                                 game.state.transition_timer))

    def test_initial_title_has_menu_audio_and_pauses_gameplay(self):
        with patch('main.AudioManager.set_mode') as mode:
            game = Game(Path(self.directory.name) / 'initial-title.json')
        self.assertEqual(game.mode, 'title')
        self.assertTrue(game.state.paused)
        mode.assert_called_with('title')

    def test_quit_event_exits_before_tick_or_draw(self):
        game = self.game
        with patch('pygame.event.get', return_value=[pygame.event.Event(pygame.QUIT)]), \
                patch.object(game, 'tick') as tick, patch.object(game, 'draw') as draw, \
                patch('pygame.quit'):
            game.run(frames=1)
        tick.assert_not_called()
        draw.assert_not_called()
        game.running = True

    def test_pickup_rewards_and_collection_once(self):
        game = self.game
        game.knight.health = 40
        col = game.knight._col_rect()
        game.powerups = [PowerUp(*col.center, 'health'), PowerUp(*col.center, 'score')]
        game.tick(self.keys)
        self.assertEqual(game.knight.health, 70)
        self.assertEqual(game.state.score, 500)
        self.assertFalse(game.powerups)
        game.tick(self.keys)
        self.assertEqual(game.state.score, 500)

    def test_boss_armor_windup_and_clear_rewards(self):
        game = self.game
        game.state.wave = 3
        game.state.phase = 'combat'
        game.state.spawn_timer = game.state.spawn_rate
        game.tick(self.keys)
        boss = game.enemies[0]
        boss.do_attack()
        state = boss.state
        self.assertFalse(boss.sources)
        boss.take_damage(10)
        self.assertEqual(boss.state, state)
        self.assertTrue(boss.attacking)
        self.assertIsNotNone(boss.telegraph)
        for _ in range(60):
            boss.update(game.knight, game.world)
        self.assertTrue(boss.sources)
        boss.take_damage(boss.health)
        game.knight.health = 40
        game.tick(self.keys)
        self.assertEqual(game.knight.health, 70)
        self.assertEqual(game.state.score, 3750)
        game.tick(self.keys)
        self.assertEqual(game.state.score, 3750)

    def test_one_way_platform_and_fast_fall(self):
        knight = self.game.knight
        knight.rect.topleft = (200, 464 - knight.rect.height)
        knight.vel_y = -5
        self.game.world.gravity(knight)
        self.assertLess(knight.rect.bottom, 464)
        knight.rect.bottom = 456
        knight.vel_y = 100
        self.game.world.gravity(knight)
        self.assertEqual(knight.rect.bottom, 464)
        self.assertTrue(knight.on_ground)

    def test_boss_clear_and_render_all_menus(self):
        game = self.game
        game.state.wave = 3
        game.knight.rect.x = game.campaign.environment['zones'][2]
        game.state.phase = 'combat'
        game.tick(self.keys)
        game.state.spawn_timer = game.state.spawn_rate
        game.tick(self.keys)
        boss = game.enemies[0]
        self.assertIsInstance(boss, Monster)
        self.assertTrue(boss.boss)
        self.assertEqual(boss.species, 'Mushroom')
        boss.do_attack()
        self.assertEqual(boss.windup, 60)
        game.draw()
        boss.take_damage(boss.health)
        game.tick(self.keys)
        self.assertEqual(game.state.phase, 'exit')
        for mode in ('title', 'pause', 'settings', 'over'):
            game.change_mode(mode)
            game.draw()

    def test_focus_pause_and_settings_persist(self):
        game = self.game
        game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(game.mode, 'pause')
        game.selection = 1
        game.activate()
        self.assertEqual(game.mode, 'settings')
        previous = game.save.settings['sound']
        game.selection = 0
        game.activate()
        self.assertEqual(game.save.settings['sound'], not previous)
        game.selection = 1
        game.activate(-1)
        self.assertEqual(game.save.settings['volume'], 0.6)
        self.assertEqual(SaveData(game.save.path).settings, game.save.settings)
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(game.mode, 'pause')

    def test_enemy_reaches_high_platform_and_gravity_lands(self):
        game = self.game
        game.knight.rect.topleft = (560, 304)
        game.spawn()
        enemy = game.enemies[0]
        enemy.rect.topleft = (560, 504)
        minimum = enemy.rect.y
        for _ in range(500):
            enemy.update(game.knight, game.world)
            minimum = min(minimum, enemy.rect.y)
        self.assertLess(minimum, 350)
        for _ in range(100):
            game.world.gravity(game.knight)
        self.assertEqual(game.knight.rect.bottom, 368)
        self.assertTrue(game.knight.on_ground)


if __name__ == '__main__':
    unittest.main()
