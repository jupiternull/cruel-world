import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import json
from copy import deepcopy
import random
import tempfile
import unittest
from unittest.mock import Mock, patch
from audio import AudioManager
from build_web import runtime_files
from pathlib import Path
import pygame
from persistence import SaveData
from progression import Expedition, PROVISIONS, UPGRADES, Sayings, SAYINGS, apply_loadout, effect, reaction
from main import Game


class ProgressionTests(unittest.TestCase):
    def test_retry_reward_claims_and_incomplete_records(self):
        with tempfile.TemporaryDirectory() as d:
            game = Game(Path(d) / 's')
            game.launch_expedition(0)
            game.state.phase = 'combat'
            game.state.spawned = 1
            game.spawn()
            enemy = game.enemies[-1]
            enemy.alive = False
            enemy.health = 0
            game.tick({})
            score = game.state.score
            claims = set(game.expedition.kill_claims)
            game.change_mode('over')
            game.activate()
            for _ in range(30): game.tick({})
            self.assertEqual(game.expedition.kill_claims, claims)
            game.state.phase = 'combat'
            game.state.spawned = 1
            game.spawn()
            enemy = game.enemies[-1]
            enemy.alive = False
            enemy.health = 0
            before = game.state.score
            game.tick({})
            self.assertEqual(game.state.score, before)
            self.assertLessEqual(game.state.score, score)
            self.assertEqual(SaveData(game.save.path).records, {})
            pygame.quit()

    def test_migration_and_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'save.json'
            p.write_text(json.dumps({'version': 3, 'cleared_regions': [0, 1], 'last_class': 'huntress', 'high_score': 42}))
            s = SaveData(p)
            self.assertEqual(len(s.materials), 2)
            self.assertEqual(s.last_class, 'ranger')
            s.save()
            self.assertEqual(SaveData(p).materials, s.materials)
            p.write_text(json.dumps({'version': 4, 'purchased': [], 'equipped': [], 'records': {'0': {'discoveries': 42, 'best': None}}, 'cleared_regions': [True, 9, None]}))
            self.assertEqual(SaveData(p).cleared_regions, [])

    def test_audio_retarget_and_unchanged_loop_phase(self):
        audio = AudioManager.__new__(AudioManager)
        audio.available = True
        audio.paused = False
        audio.loops = {name: object() for name in ('camp', 'outside', 'inside', 'forest')}
        audio.loop_names = (None, None)
        audio.pending_loops = None
        audio.fade = None
        audio.loop_gain = 1
        audio.music_channel = Mock()
        audio.ambience_channel = Mock()
        audio.apply_settings = Mock()
        audio.request_loops(('camp', 'outside'))
        for _ in range(100): audio.update(1/60)
        self.assertEqual(audio.music_channel.play.call_count, 1)
        audio.request_loops(('camp', 'outside'))
        self.assertIsNone(audio.fade)
        audio.request_loops(('forest', 'outside'))
        audio.update(.1)
        audio.request_loops(('camp', 'inside'))
        for _ in range(100): audio.update(1/60)
        self.assertEqual(audio.music_channel.play.call_count, 1)
        self.assertEqual(audio.ambience_channel.play.call_count, 2)
        self.assertEqual(audio.loop_names, ('camp', 'inside'))
        self.assertEqual(audio.loop_gain, 1)
        self.assertIn(Path.cwd() / 'progression.py', runtime_files())

    def test_completion_unique_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            s = SaveData(Path(d) / 's')
            e = Expedition(PROVISIONS[2])
            self.assertTrue(s.complete_expedition(0, 'wizard', 100, ['chest'], e))
            self.assertFalse(s.complete_expedition(0, 'wizard', 90, ['statue'], e))
            self.assertEqual(len(s.materials), 1)
            row = SaveData(s.path).records['0']
            self.assertEqual(row['best']['wizard'], 100)
            self.assertEqual(row['completions']['wizard'], 2)
            self.assertEqual(row['discoveries'], ['chest', 'statue'])

    def test_completion_failure_is_atomic_and_results_report_error(self):
        for failure in ('replace', 'write'):
            for replay in (False, True):
                with self.subTest(failure=failure, replay=replay), tempfile.TemporaryDirectory() as d:
                    game = Game(Path(d) / 'save.json')
                    game.launch_expedition(0)
                    if replay:
                        game.save.complete_expedition(0, 'warrior', 20, ['cache'], game.expedition)
                    else:
                        game.save.save()
                    fields = ('cleared_regions', 'materials', 'records', 'high_score', 'furthest_environment')
                    before = {key: deepcopy(getattr(game.save, key)) for key in fields}
                    original_records = game.save.records
                    disk = game.save.path.read_bytes()
                    game.state.score = 9000
                    game.features.claimed = {'sanctuary'}
                    target = 'pathlib.Path.replace' if failure == 'replace' else 'persistence.json.dump'
                    with patch(target, side_effect=OSError('forced failure')):
                        game.finish_expedition()
                    self.assertIs(game.save.records, original_records)
                    self.assertEqual({key: getattr(game.save, key) for key in fields}, before)
                    self.assertEqual(game.save.path.read_bytes(), disk)
                    self.assertEqual({key: getattr(SaveData(game.save.path), key) for key in fields}, before)
                    self.assertFalse(game.campaign.complete)
                    self.assertIn(game.save.error, game.results)
                    self.assertIn('Completion not saved', game.results)
                    self.assertFalse(any(line.startswith(('First clear:', 'Unlocked:', 'Replay recorded:', 'Next gate')) for line in game.results))
                    self.assertEqual(list(game.save.path.parent.glob('*.tmp')), [])
                    game.draw()
                    pygame.quit()

    def test_boss_exit_waits_for_death_cycle(self):
        for death_frames in ('normal', 'missing', 'empty'):
            with self.subTest(death_frames=death_frames), tempfile.TemporaryDirectory() as d:
                game = Game(Path(d) / 's')
                game.launch_expedition(0)
                game.state.wave = 3
                game.state.phase = 'combat'
                game.state.spawned = 1
                game.spawn(True)
                boss = game.enemies[-1]
                boss.frames = dict(boss.frames)
                if death_frames == 'missing':
                    boss.frames.pop('Death', None)
                elif death_frames == 'empty':
                    boss.frames['Death'] = []
                boss.take_damage(boss.health)
                game.knight.rect.midbottom = (game.world.exit.centerx, 560)
                for _ in range(200):
                    if boss.death_anim_done:
                        break
                    game.tick({})
                    self.assertFalse(game.campaign.exit_open)
                    self.assertIsNone(game.transition)
                    self.assertEqual(game.mode, 'play')
                self.assertTrue(boss.death_anim_done)
                game.knight.rect.midbottom = (game.world.exit.centerx, 560)
                game.tick({})
                self.assertTrue(game.campaign.exit_open)
                self.assertIsNotNone(game.transition)
                for _ in range(100):
                    game.tick({})
                self.assertEqual(game.mode, 'results')
                pygame.quit()

    def test_persistent_provisions_repeat_and_display_active(self):
        with tempfile.TemporaryDirectory() as d:
            game = Game(Path(d) / 's')
            for name in PROVISIONS[1:]:
                game.save.provision = name
                game.launch_expedition(0)
                e = game.expedition
                self.assertEqual(e.status, 'active / not triggered')
                for _ in range(3):
                    self.assertEqual(e.hazard_damage(16), 12 if name == PROVISIONS[1] else 16)
                    self.assertEqual(e.discovery_score(100), 110 if name == PROVISIONS[2] else 100)
                    self.assertFalse(e.consumed)
                    self.assertEqual(e.status, 'active / triggered')
                with patch('main.draw_banner') as banner:
                    game.draw()
                self.assertTrue(any(name + ' [active / triggered]' in call.args for call in banner.call_args_list))
                game.finish_expedition()
                self.assertIn('Selected: ' + name + ' | active / triggered', game.results)
            game.save.provision = PROVISIONS[0]
            game.launch_expedition(0)
            game.knight.health = 1
            game.expedition.update(game.knight)
            self.assertTrue(game.expedition.consumed)
            game.knight.health = 1
            game.expedition.update(game.knight)
            self.assertEqual(game.knight.health, 1)
            game.finish_expedition()
            self.assertIn('Selected: Field Dressing | consumed', game.results)
            pygame.quit()

    def test_quote_rng_boundary_and_rotation(self):
        random.seed(32)
        state = random.getstate()
        quotes = Sayings(5)
        self.assertEqual(set(quotes.next() for _ in SAYINGS), set(SAYINGS))
        self.assertEqual(random.getstate(), state)

    def test_all_upgrades_provisions_transitions_and_render(self):
        with tempfile.TemporaryDirectory() as d:
            game = Game(Path(d) / 's')
            for c in UPGRADES:
                game.reset_game(c)
                game.save.cleared_regions = []
                self.assertFalse(game.save.purchase(c, 2))
                game.save.cleared_regions = [0, 1, 2, 3]
                for i, (_, name, value, _) in enumerate(UPGRADES[c]):
                    self.assertTrue(game.save.purchase(c, i))
                    apply_loadout(game.knight, game.save)
                    self.assertEqual(effect(game.knight, name), value)
                    self.assertEqual(len(game.knight.upgrade_effects), 1)
                    if name == 'healing':
                        game.knight.health = 10
                        game.knight.heal(20, upgrade=True)
                        self.assertEqual(game.knight.health, 30 + value)
                        game.knight.heal(20)
                        self.assertEqual(game.knight.health, 50 + value)
                    elif name == 'mobility':
                        game.knight.pending_attack = None
                        game.knight.mobility_timer = 0
                        game.knight.dash_cooldown = 0
                        game.knight.set_state('Idle', True)
                        game.knight.dash()
                        self.assertEqual(game.knight.dash_cooldown, (150 if c == 'wizard' else 90) - value)
                    elif name == 'reach':
                        game.knight.pending_attack = 'primary'
                        game.knight.emit_attack()
                        self.assertEqual(game.knight.sources[-1].lifetime, 85)

                    self.assertEqual(SaveData(game.save.path).equipped[c], i)
                    game.knight.pending_attack = None
                    game.knight.mobility_timer = 0
                    game.knight.secondary_cooldown = 0
                    game.knight.set_state('Idle', True)
                    game.knight.secondary()
                    self.assertEqual(game.knight.secondary_cooldown, game.knight.stats['cooldown'] - effect(game.knight, 'recovery'))
                self.assertTrue(reaction(6, game.save, c))
            for name in PROVISIONS:
                game.save.provision = name
                game.launch_expedition(0)
                e = game.expedition
                game.knight.health = 10
                e.update(game.knight)
                if name == PROVISIONS[0]:
                    self.assertTrue(e.used)
                    hp = game.knight.health
                    e.update(game.knight)
                    self.assertEqual(hp, game.knight.health)
                self.assertEqual(e.hazard_damage(16), 12 if name == PROVISIONS[1] else 16)
                self.assertEqual(e.discovery_score(100), 110 if name == PROVISIONS[2] else 100)
                game.change_mode('over')
                game.selection = 0
                game.activate()
                for _ in range(30): game.tick({})
                self.assertIs(game.expedition, e)
                game.enter_camp('return')
                game.launch_expedition(0)
                self.assertFalse(game.expedition.used)
            game.enter_camp('return')
            game.draw()
            game.depart(0)
            game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
            game.tick({})
            self.assertEqual(game.transition['tick'], 0)
            game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
            old = game.knight.rect.copy()
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
            self.assertEqual(game.mode, 'camp')
            game.tick({pygame.K_d: True})
            self.assertEqual(old, game.knight.rect)
            for _ in range(100):
                game.tick({})
            self.assertIsNone(game.transition)
            self.assertEqual(game.mode, 'play')
            game.finish_expedition()
            game.draw()
            self.assertEqual(game.mode, 'results')
            for _ in range(50):
                game.tick({})
            self.assertEqual(game.mode, 'results')
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
            for _ in range(30):
                game.tick({})
            self.assertEqual(game.mode, 'camp')
            self.assertEqual(game.knight.health, game.knight.max_health)
            for name in ('forge', 'supplies', 'journal'):
                game.open_service(name)
                game.draw()
                self.assertEqual(game.screen.get_size(), (800, 600))
            game.service = None
            game.audio.set_mode('camp')
            for _ in range(100):
                game.audio.update(1/60)
            names = game.audio.loop_names
            game.audio.set_mode('camp')
            self.assertIsNone(game.audio.fade)
            self.assertEqual(names, game.audio.loop_names)
            game.audio.set_mode('interior')
            gain = game.audio.loop_gain
            game.audio.pause(True)
            game.audio.update(.1)
            self.assertEqual(game.audio.loop_gain, gain)
            game.audio.pause(False)
            for _ in range(100):
                game.audio.update(1/60)
            self.assertEqual(game.audio.loop_gain, 1)
            self.assertIsNone(game.audio.fade)
            pygame.quit()
