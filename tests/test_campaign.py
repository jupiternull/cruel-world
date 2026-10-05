import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pygame
from main import Game
from assets import HERO_MANIFEST, MONSTER_MANIFEST, validated_frames
from campaign import ENVIRONMENTS, World
from camera import Camera
from entities.hero import Hero, CLASSES
from entities.monster import Monster
from projectile import DamageSource
from persistence import SaveData


class CampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = Game(Path(cls.directory.name) / 'campaign.json')

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.directory.cleanup()

    def setUp(self):
        self.game.reset_game('warrior')
        self.keys = {}

    def ticks(self, count):
        for _ in range(count):
            self.game.tick(self.keys)

    def test_exact_hero_and_monster_manifests(self):
        for name, (_, width, height, scale, animations) in HERO_MANIFEST.items():
            for animation, count in animations.items():
                frames = self.game.assets['heroes'][name][animation]
                self.assertEqual(len(frames), count)
                self.assertTrue(all(f.get_size() == (width * scale, height * scale) for f in frames))
                self.assertTrue(all(f.get_bounding_rect().width for f in frames))
        for species, animations in MONSTER_MANIFEST.items():
            for animation, count in animations.items():
                frames = self.game.assets['monsters'][species][animation]
                self.assertEqual(len(frames), count)
                self.assertEqual(frames[0].get_size(), (300, 300))

    def test_bad_manifest_fails_explicitly(self):
        spec = HERO_MANIFEST['warrior']
        with self.assertRaises(ValueError):
            validated_frames(*spec[:4], {'Idle': 7})

    def test_camera_clamps_and_preserves_world_rect(self):
        camera = Camera(2880)
        rect = pygame.Rect(2500, 300, 32, 64)
        original = rect.copy()
        camera.update(rect)
        self.assertEqual(camera.x, 2080)
        self.assertEqual(camera.rect(rect).x, 420)
        self.assertEqual(rect, original)
        camera.update(pygame.Rect(-100, 0, 10, 10))
        self.assertEqual(camera.x, 0)

    def test_world_bounds_use_level_width(self):
        hero = self.game.knight
        for data in ENVIRONMENTS:
            world = World(data)
            world.move(hero, 10000)
            self.assertEqual(hero.rect.right, data['width'])
            self.assertGreater(hero.rect.x, 800)
            world.move(hero, -10000)
            self.assertEqual(hero.rect.x, 0)

    def test_class_selection_before_run_and_persistence(self):
        game = self.game
        game.change_mode('title')
        game.activate()
        self.assertEqual(game.mode, 'class')
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        game.activate()
        self.assertEqual(game.knight.class_id, 'ranger')
        self.assertEqual(game.knight.health, 100)
        self.assertEqual(SaveData(game.save.path).last_class, 'ranger')

    def test_class_stats_and_attack_sources_differ(self):
        results = []
        for name in CLASSES:
            game = self.game
            game.reset_game(name)
            game.knight.attack()
            self.ticks(10)
            source = game.sources[0]
            results.append((game.knight.max_health, game.knight.stats['speed'], source.kind, source.damage))
        self.assertEqual([r[2] for r in results], ['melee', 'arrow', 'fireball'])
        self.assertEqual(len({r[0] for r in results}), 3)
        self.assertEqual(len({r[3] for r in results}), 3)

    def test_secondary_abilities_and_cooldowns(self):
        for name in CLASSES:
            with self.subTest(hero=name):
                game = self.game
                game.reset_game(name)
                hero = game.knight
                before = hero.rect.x
                self.assertTrue(hero.secondary())
                self.assertFalse(hero.secondary())
                self.ticks(10)
                self.assertEqual(hero.secondary_cooldown, hero.stats['cooldown'] - 10)
                if name == 'warrior':
                    self.assertGreater(hero.rect.x, before)
                    self.assertGreater(hero.invulnerable, 0)
                elif name == 'ranger':
                    self.assertEqual(len(game.sources), 3)
                    self.assertTrue(all(s.pierce for s in game.sources))
                else:
                    self.assertEqual(game.sources[0].kind, 'wave')
                    self.assertGreater(game.sources[0].rect.height, 100)

    def test_mobility_and_combo_locks(self):
        for name in CLASSES:
            self.game.reset_game(name)
            hero = self.game.knight
            self.assertTrue(hero.dash())
            self.assertFalse(hero.attack())
            before = hero.health
            hero.take_damage(30)
            self.assertEqual(hero.health, before)
            self.ticks(18)
            self.assertFalse(hero.dash())

    def test_arrows_hit_once_and_stop(self):
        game = self.game
        game.reset_game('ranger')
        enemy = Monster(240, 504, game.assets['monsters']['Mushroom'], 'Mushroom')
        enemy.attack_timer = 1000
        game.enemies = [enemy]
        game.knight.attack()
        self.ticks(25)
        self.assertEqual(enemy.health, enemy.max_health - 18)
        self.assertFalse(any(s.kind == 'arrow' for s in game.sources))

    def test_piercing_wave_hits_two_targets_once(self):
        game = self.game
        game.reset_game('wizard')
        for x in (190, 260):
            enemy = Monster(x, 504, game.assets['monsters']['Mushroom'], 'Mushroom')
            enemy.attack_timer = 1000
            game.enemies.append(enemy)
        enemies = list(game.enemies)
        game.knight.secondary()
        self.ticks(35)
        self.assertEqual([e.health for e in enemies], [10, 10])

    def test_ranged_can_move_and_jump_during_attack(self):
        for name in ('ranger', 'wizard'):
            self.game.reset_game(name)
            hero = self.game.knight
            hero.attack()
            before = hero.rect.x
            hero.handle_input({pygame.K_d: True, pygame.K_SPACE: True}, self.game.world)
            self.assertGreater(hero.rect.x, before)
            self.assertLess(hero.vel_y, 0)
            self.assertTrue(hero.attacking)

    def test_fireball_damage_and_lifetime(self):
        game = self.game
        game.reset_game('wizard')
        enemy = Monster(230, 504, game.assets['monsters']['Goblin'], 'Goblin')
        enemy.attack_timer = 1000
        game.enemies = [enemy]
        game.knight.attack()
        self.ticks(30)
        self.assertEqual(enemy.health, enemy.max_health - 26)
        self.assertFalse(any(s.kind == 'fireball' for s in game.sources))

    def test_combo_releases_three_different_strikes(self):
        hero = self.game.knight
        damages = []
        for _ in range(3):
            hero.attack()
            for _ in range(19):
                hero.update_animation(1000 / 60)
            damages.append(hero.sources[-1].damage)
        self.assertEqual(damages, [22, 30, 42])

    def test_enemy_source_hit_once_even_after_invulnerability_expires(self):
        hero = self.game.knight
        source = DamageSource(hero.rect, 12, 'enemy', 200)
        self.assertTrue(source.hit(hero))
        hero.invulnerable = 0
        self.assertFalse(source.hit(hero))
        self.assertEqual(hero.health, 138)

    def test_ranged_aims_toward_elevated_front_target(self):
        game = self.game
        game.reset_game('ranger')
        enemy = Monster(300, 320, game.assets['monsters']['Flying eye'], 'Flying eye')
        enemy.attack_timer = 1000
        game.enemies = [enemy]
        game.knight.attack()
        self.ticks(10)
        arrow = game.sources[0]
        self.assertLess(arrow.velocity[1], 0)
        self.assertGreater(arrow.velocity[0], 0)
        self.assertAlmostEqual(pygame.Vector2(arrow.velocity).length(), 12)

    def test_projectiles_leave_world_and_hit_ground(self):
        world = self.game.world
        for rect, velocity in [((world.width, 200, 10, 10), (20, 0)), ((20, 555, 10, 10), (0, 8))]:
            source = DamageSource(rect, 10, 'hero', 30, velocity, 'arrow')
            source.update(world)
            self.assertFalse(source.alive)

    def test_pause_freezes_sources_climb_and_audio(self):
        game = self.game
        game.reset_game('wizard')
        game.knight.attack()
        self.ticks(10)
        source = game.sources[0]
        game.change_mode('pause')
        before = (source.rect.copy(), source.lifetime, game.knight.animation_timer, game.campaign.index)
        self.ticks(100)
        self.assertEqual(before, (source.rect, source.lifetime, game.knight.animation_timer, game.campaign.index))
        self.assertTrue(game.audio.paused)

    def test_attach_and_climb(self):
        hero = self.game.knight
        zone = self.game.world.climbables[0]
        hero.rect.centerx = zone.centerx
        hero.rect.bottom = zone.bottom
        hero.handle_input({pygame.K_w: True}, self.game.world)
        self.assertIs(hero.climbing, zone)
        previous = hero.rect.y
        self.game.world.gravity(hero)
        self.assertEqual(hero.rect.y, previous)
        hero.handle_input({pygame.K_w: True}, self.game.world)
        self.assertEqual(hero.rect.y, previous - 3)

    def test_climb_jump_detaches(self):
        hero = self.game.knight
        hero.climbing = self.game.world.climbables[0]
        hero.handle_input({pygame.K_SPACE: True}, self.game.world)
        self.assertIsNone(hero.climbing)
        self.assertLess(hero.vel_y, 0)

    def test_climb_side_detaches(self):
        hero = self.game.knight
        hero.climbing = self.game.world.climbables[0]
        hero.handle_input({pygame.K_d: True}, self.game.world)
        self.assertIsNone(hero.climbing)

    def test_climb_top_lands_on_platform(self):
        hero = self.game.knight
        zone = self.game.world.climbables[0]
        hero.climbing = zone
        hero.rect.centerx = zone.centerx
        hero.rect.bottom = zone.top + 2
        hero.handle_input({pygame.K_w: True}, self.game.world)
        self.assertIsNone(hero.climbing)
        self.game.world.gravity(hero)
        self.assertTrue(hero.on_ground)
        self.assertEqual(hero.rect.bottom, zone.top)

    def test_drop_through_and_land_ground(self):
        game = self.game
        hero = game.knight
        platform = game.world.platforms[0]
        hero.rect.centerx = platform.centerx
        hero.rect.bottom = platform.top
        hero.on_ground = True
        hero.handle_input({pygame.K_s: True, pygame.K_SPACE: True}, game.world)
        self.assertGreater(hero.drop_timer, 0)
        self.ticks(60)
        self.assertEqual(hero.rect.bottom, 560)
        self.assertTrue(hero.on_ground)
        self.assertFalse(hero.drop_through(game.world))

    def test_jump_is_edge_triggered(self):
        hero = self.game.knight
        hero.handle_input({pygame.K_SPACE: True}, self.game.world)
        self.assertLess(hero.vel_y, 0)
        hero.on_ground = True
        hero.vel_y = 0
        hero.handle_input({pygame.K_SPACE: True}, self.game.world)
        self.assertEqual(hero.vel_y, 0)

    def test_hazards_and_checkpoint_retry(self):
        game = self.game
        hazard = game.world.hazards[0]
        game.knight.rect.bottomleft = (hazard.x, 560)
        game.tick({})
        self.assertEqual(game.knight.health, 134)
        game.campaign.update_checkpoint(1300)
        checkpoint = game.campaign.checkpoint
        game.change_mode('over')
        game.activate()
        self.assertEqual(game.knight.rect.x, checkpoint)
        self.assertEqual(game.knight.health, 150)
        self.assertEqual(game.mode, 'play')

    def test_traversal_gates_and_finite_waves(self):
        game = self.game
        game.knight.rect.x = 420
        game.tick({})
        self.assertEqual(game.state.phase, 'ready')
        self.ticks(90)
        self.assertEqual(game.state.phase, 'combat')
        for _ in range(800):
            game.knight.invulnerable = 100
            game.tick({})
        self.assertLessEqual(len(game.enemies), game.state.enemy_limit)
        self.assertLessEqual(game.state.spawned, game.state.wave_size)
        game.knight.rect.x = 2000
        game.tick({})
        self.assertLessEqual(game.knight.rect.right, game.campaign.environment['zones'][0] + 340)

    def test_environment_transition_and_victory(self):
        game = self.game
        for index in range(3):
            self.assertEqual(game.campaign.index, index)
            game.campaign.exit_open = True
            game.state.phase = 'exit'
            game.knight.rect.center = game.world.exit.center
            game.tick({})
        self.assertEqual(game.mode, 'victory')
        self.assertTrue(game.campaign.complete)
        self.assertEqual(SaveData(game.save.path).furthest_environment, 2)

    def test_bosses_are_unique_species_in_each_environment(self):
        for index, data in enumerate(ENVIRONMENTS):
            game = self.game
            game.campaign.index = index
            game.load_environment()
            game.state.wave = 3
            game.spawn(True)
            boss = game.enemies[-1]
            self.assertNotIn(boss.species, data['enemies'])
            self.assertTrue(boss.boss)
            self.assertGreater(boss.health, 200)
            boss.do_attack(game.knight.rect)
            self.assertIsNotNone(boss.telegraph)
            self.assertFalse(boss.sources)
            for _ in range(60):
                boss.update(game.knight, game.world)
            self.assertTrue(boss.sources)
            kinds = {s.kind for s in boss.sources}
            self.assertIn(('spore', 'shock', 'moon')[index], kinds)

    def test_shield_front_reduces_damage_back_and_wave_bypass(self):
        game = self.game
        enemy = Monster(300, 504, game.assets['monsters']['Skeleton'], 'Skeleton')
        enemy.facing_right = True
        front = DamageSource((320, 504, 30, 56), 30, 'hero', 10, kind='arrow')
        enemy.take_damage(30, front)
        self.assertEqual(enemy.health, 60)
        back = DamageSource((280, 504, 30, 56), 30, 'hero', 10, kind='arrow')
        enemy.take_damage(30, back)
        self.assertEqual(enemy.health, 30)
        front.kind = 'wave'
        enemy.take_damage(30, front)
        self.assertFalse(enemy.alive)

    def test_all_classes_and_environments_render_world_and_menus(self):
        game = self.game
        for name in CLASSES:
            for index in range(3):
                with self.subTest(hero=name, region=index):
                    game.reset_game(name)
                    game.campaign.index = index
                    game.load_environment()
                    game.knight.rect.x = 800
                    game.camera.update(game.knight.rect)
                    game.spawn()
                    game.knight.secondary()
                    self.ticks(12)
                    for mode in ('play', 'pause', 'settings', 'over', 'class', 'victory'):
                        game.change_mode(mode)
                        game.draw()
                    self.assertGreater(game.camera.x, 0)

    def test_ranged_mobility_cancels_unreleased_attack(self):
        for name in ('ranger', 'wizard'):
            self.game.reset_game(name)
            hero = self.game.knight
            hero.attack()
            self.ticks(5)
            self.assertTrue(hero.dash(-1))
            self.assertFalse(hero.facing_right)
            self.ticks(15)
            self.assertFalse(self.game.sources)
            self.assertIsNone(hero.pending_attack)
            self.assertFalse(hero.attacking)
        self.game.reset_game('warrior')
        self.game.knight.attack()
        self.assertFalse(self.game.knight.dash())

    def test_wizard_primary_recovers_in_24_ticks_secondary_keeps_commitment(self):
        self.game.reset_game('wizard')
        hero = self.game.knight
        hero.attack()
        self.ticks(9)
        self.assertEqual(len(self.game.sources), 1)
        self.ticks(15)
        self.assertFalse(hero.state_locked)
        self.assertTrue(hero.secondary())
        self.ticks(24)
        self.assertTrue(hero.state_locked)
        self.assertEqual(hero.max_health, 85)
        self.assertEqual(hero.stats['cooldown'], 300)

    def test_transition_stops_old_tick_and_resets_camera(self):
        game = self.game
        game.campaign.exit_open = True
        game.state.phase = 'exit'
        game.knight.rect.center = game.world.exit.center
        game.knight.events.clear()
        with patch.object(game.knight, 'update_animation') as update:
            game.tick({})
        update.assert_not_called()
        self.assertEqual(game.campaign.index, 1)
        self.assertEqual(game.camera.x, 0)
        self.assertEqual(game.knight.rect.topleft, (96, 496))
        self.assertFalse(game.sources)

    def test_projectiles_leave_vertical_world_bounds(self):
        for y, velocity in ((-20, (0, -12)), (610, (0, 12))):
            source = DamageSource((100, y, 10, 10), 12, 'enemy', 100, velocity, 'moon')
            source.update(self.game.world)
            self.assertFalse(source.alive)

    def test_campaign_never_loads_legacy_images(self):
        from assets import load_campaign_assets
        original = pygame.image.load
        paths = []
        def capture(path):
            paths.append(str(path))
            return original(path)
        with patch('pygame.image.load', side_effect=capture):
            load_campaign_assets()
        self.assertTrue(paths)
        self.assertFalse(any('/sprites/' in path or '/tilesets/' in path for path in paths))

    def test_unversioned_save_ignores_campaign_fields(self):
        path = Path(self.directory.name) / 'unversioned.json'
        path.write_text(json.dumps({'high_score': 99, 'last_class': 'wizard', 'furthest_environment': 2}))
        save = SaveData(path)
        self.assertEqual((save.high_score, save.last_class, save.furthest_environment), (99, 'warrior', 0))

    def test_mobility_event_uses_held_retreat_direction(self):
        game = self.game
        game.reset_game('wizard')
        hero = game.knight
        hero.attack()
        with patch('pygame.key.get_pressed', return_value={pygame.K_a: True, pygame.K_d: False,
                                                         pygame.K_LEFT: False, pygame.K_RIGHT: False}):
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LSHIFT))
        self.assertFalse(hero.facing_right)
        self.assertGreater(hero.mobility_timer, 0)
        self.assertIsNone(hero.pending_attack)

    def test_short_world_camera_stays_at_origin(self):
        camera = Camera(400)
        camera.update(pygame.Rect(350, 0, 32, 64))
        self.assertEqual(camera.x, 0)

    def test_menu_audio_transitions_and_settings(self):
        from campaign import ENVIRONMENTS
        audio = self.game.audio
        for data in ENVIRONMENTS:
            self.game.campaign.index = ENVIRONMENTS.index(data)
            self.game.load_environment()
            self.game.change_mode('play')
            for mode in ('pause', 'settings', 'over', 'victory', 'title', 'class'):
                self.game.change_mode(mode)
                self.assertEqual(audio.mode, mode)
                self.assertTrue(audio.ambience_channel.get_busy())
                self.assertIs(audio.ambience_channel.get_sound(), audio.loops[
                    'cave_ambience' if mode in ('settings', 'title', 'class') else data['ambience']])
                self.assertFalse(audio.music_channel.get_busy())
                self.assertEqual(pygame.mixer.music.get_busy(), mode in ('settings', 'title', 'class'))
                with patch('pygame.mixer.music.play') as play:
                    audio.set_mode(mode)
                    play.assert_not_called()
                audio.settings['sound'] = False
                audio.apply_settings()
                self.assertEqual(audio.ambience_channel.get_volume(), 0)
                self.assertEqual(pygame.mixer.music.get_volume(), 0)
                audio.settings['sound'] = True
                audio.settings['volume'] = 0.5
                audio.apply_settings()
                self.assertAlmostEqual(audio.ambience_channel.get_volume(), 0.09, delta=0.01)
                self.game.change_mode('play')
                self.assertFalse(pygame.mixer.music.get_busy())
                self.assertIs(audio.music_channel.get_sound(), audio.loops[data['music']])
                self.assertIs(audio.ambience_channel.get_sound(), audio.loops[data['ambience']])
                self.assertFalse(audio.paused)

    def test_audio_variants_and_independent_environment_channels(self):
        audio = self.game.audio
        for name in ('sword_attack', 'sword_hit', 'bow_attack', 'bow_hit', 'fireball', 'spell_hit', 'dirt_step'):
            self.assertGreaterEqual(len(audio.variants[name]), 2)
        for data in ENVIRONMENTS:
            audio.environment(data)
            self.assertEqual(audio.current_environment, data['id'])
            self.assertIs(audio.music_channel.get_sound(), audio.loops[data['music']])
            self.assertIs(audio.ambience_channel.get_sound(), audio.loops[data['ambience']])
        audio.settings['sound'] = False
        audio.apply_settings()
        self.assertEqual(audio.music_channel.get_volume(), 0)
        self.assertTrue(all(sound.get_volume() == 0 for sounds in audio.variants.values() for sound in sounds))
        audio.settings['sound'] = True
        audio.apply_settings()

    def test_old_saves_migrate_and_invalid_campaign_fields_default(self):
        path = Path(self.directory.name) / 'old.json'
        path.write_text(json.dumps({'high_score': 42, 'settings': {'volume': 0.4}}))
        save = SaveData(path)
        self.assertEqual((save.last_class, save.furthest_environment), ('warrior', 0))
        save.last_class = 'wizard'
        save.furthest_environment = 2
        save.save()
        data = json.loads(path.read_text())
        self.assertEqual(data['version'], 2)
        self.assertEqual(data['high_score'], 42)
        self.assertEqual(SaveData(path).last_class, 'wizard')
        path.write_text(json.dumps({'last_class': 'bad', 'furthest_environment': 'bad'}))
        save = SaveData(path)
        self.assertEqual((save.last_class, save.furthest_environment), ('warrior', 0))


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = Game(Path(cls.directory.name) / 'presentation.json')

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()
        pygame.quit()

    def test_knight_numeric_frame_order_and_runtime(self):
        from assets import KNIGHT_ROOT, KNIGHT_ANIMATIONS
        from config import ASSETS_DIR
        for state, (folder, count) in KNIGHT_ANIMATIONS.items():
            paths = sorted((Path(ASSETS_DIR) / KNIGHT_ROOT / folder).glob('*.png'),
                           key=lambda p: int(p.stem.rsplit('_', 1)[1]))
            self.assertEqual([int(p.stem.rsplit('_', 1)[1]) for p in paths], list(range(count)))
            for i, path in enumerate(paths):
                expected = pygame.transform.scale(pygame.image.load(str(path)), (200, 110))
                actual = self.game.assets['heroes']['warrior'][state][i]
                self.assertEqual(pygame.image.tobytes(actual, 'RGBA'), pygame.image.tobytes(expected, 'RGBA'))
        self.game.reset_game('warrior')
        for stage in (1, 2, 3):
            hero = self.game.knight
            hero.pending_attack = None
            hero.set_state('Idle')
            hero.combo_timer = 28
            hero.combo_stage = stage - 1
            hero.attack()
            self.assertEqual(hero.state, f'Attack{stage}')
            hero.sources.clear()
            for _ in range(8): hero.update_animation(1000/60)
            self.assertFalse(hero.sources)
            hero.update_animation(1000/60)
            self.assertEqual(len(hero.sources), 1)
            self.assertEqual(hero.current_frame_idx, (2, 1, 3)[stage - 1])
            self.game.draw()

    def test_knight_derivatives_are_rebuildable_and_cover_every_pose(self):
        from assets import KNIGHT_ROOT, KNIGHT_SOURCE_ROOT, KNIGHT_ANIMATIONS, load_campaign_assets
        from build_presentation import knight_assets, KNIGHT_HEADS
        from config import ASSETS_DIR
        import hashlib
        source = Path(ASSETS_DIR)/KNIGHT_SOURCE_ROOT
        before = {p: hashlib.sha256(p.read_bytes()).digest() for p in source.rglob('*.png')}
        with tempfile.TemporaryDirectory() as directory:
            knight_assets(directory)
            for state,(folder,count) in KNIGHT_ANIMATIONS.items():
                self.assertEqual(len(KNIGHT_HEADS[state]),count)
                for i in range(count):
                    filename=f"HeroKnight_{({'BlockIdle': 'Block Idle', 'WallSlide': 'Slide', 'LedgeGrab': 'Grab Ledge'}).get(folder, folder)}_{i}.png"
                    generated=Path(directory)/folder/filename
                    runtime=Path(ASSETS_DIR)/KNIGHT_ROOT/folder/filename
                    self.assertEqual(generated.read_bytes(),runtime.read_bytes())
                    derived=pygame.image.load(str(runtime))
                    original=pygame.image.load(str(source/folder/filename))
                    self.assertNotEqual(pygame.image.tobytes(derived,'RGBA'),pygame.image.tobytes(original,'RGBA'))
                    cx,cy=KNIGHT_HEADS[state][i]
                    colors={tuple(derived.get_at((x,y)))[:3] for x in range(max(0,cx-5),min(100,cx+6))
                            for y in range(max(0,cy-5),min(55,cy+6))}
                    self.assertIn((8,9,12),colors)
                    self.assertNotIn((239,206,164),colors)
                    self.assertNotIn((203,136,94),colors)
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).digest() for p in before})
        paths=[]
        load=pygame.image.load
        def record(path):
            paths.append(str(path))
            return load(path)
        with patch('pygame.image.load',side_effect=record): load_campaign_assets()
        self.assertFalse(any('/hero_knight/' in path for path in paths))
        self.assertTrue(any('/heroes/knight/' in path for path in paths))

    def test_missing_knight_derivative_rebuilds_without_bare_head_fallback(self):
        from assets import load_campaign_assets
        from build_presentation import knight_assets
        with patch('pathlib.Path.exists',return_value=False), patch('build_presentation.knight_assets',wraps=knight_assets) as rebuild:
            frames=load_campaign_assets()['heroes']['warrior']
        rebuild.assert_called_once_with()
        self.assertEqual(len(frames['Roll']),9)
        self.assertEqual(CLASSES['warrior']['name'],'Knight')

    def test_ranger_palette_source_and_no_legacy_load(self):
        from assets import load_campaign_assets
        from config import ASSETS_DIR
        original = pygame.image.load(str(Path(ASSETS_DIR) / 'heroes/ranger_source/Martial Hero/Sprites/Idle.png'))
        derived = pygame.image.load(str(Path(ASSETS_DIR) / 'heroes/ranger/Idle.png'))
        self.assertEqual(original.get_size(), derived.get_size())
        self.assertNotEqual(pygame.image.tobytes(original, 'RGBA'), pygame.image.tobytes(derived, 'RGBA'))
        colors = set(tuple(derived.get_at((x,y)))[:3] for x in range(200) for y in range(200) if derived.get_at((x,y)).a)
        self.assertIn((10,19,17), colors)
        self.assertIn((28,57,36), colors)
        self.assertIn((179,130,65), colors)
        self.assertIn((215,209,173), colors)
        self.assertNotIn((206,32,56), colors)
        load = pygame.image.load
        paths = []
        def record(path):
            paths.append(str(path))
            return load(path)
        with patch('pygame.image.load', side_effect=record): load_campaign_assets()
        self.assertFalse(any('/huntress/' in p or '/ranger_source/' in p or '/warrior/' in p for p in paths))
        for state in ('Idle','Run','Jump','Attack1','Hit','Death'):
            self.assertTrue(self.game.assets['heroes']['ranger'][state][0].get_bounding_rect().width)

    def test_ranger_rebuild_shadow_equipment_and_source_removal(self):
        import hashlib
        from build_presentation import ranger_assets, RANGER_POSES, RANGER_COLORS
        from assets import HERO_MANIFEST
        from config import ASSETS_DIR
        root=Path(ASSETS_DIR)/'heroes'
        source=root/'ranger_source'
        before={p:hashlib.sha256(p.read_bytes()).digest() for p in source.rglob('*') if p.is_file()}
        source_colors=set()
        for path in (source/'Martial Hero/Sprites').glob('*.png'):
            im=pygame.image.load(str(path))
            source_colors.update(tuple(im.get_at((x,y)))[:3] for x in range(im.get_width())
                                 for y in range(im.get_height()) if im.get_at((x,y)).a)
        allowed=set(RANGER_COLORS.values())
        self.assertFalse(allowed & source_colors)
        self.assertEqual({k:len(v) for k,v in RANGER_POSES.items()},HERO_MANIFEST['ranger'][-1])
        with tempfile.TemporaryDirectory() as directory:
            for _ in range(2):
                ranger_assets(directory)
                for state,poses in RANGER_POSES.items():
                    generated=Path(directory)/(state+'.png')
                    self.assertEqual(generated.read_bytes(),(root/'ranger'/generated.name).read_bytes())
                    sheet=pygame.image.load(str(generated))
                    self.assertEqual(sheet.get_size(),(200*len(poses),200))
                    for i,(cx,cy,angle) in enumerate(poses):
                        frame=sheet.subsurface((i*200,0,200,200))
                        colors={tuple(frame.get_at((x,y)))[:3] for x in range(200)
                                for y in range(200) if frame.get_at((x,y)).a}
                        self.assertLessEqual(colors,allowed)
                        for key in ('shadow','hood','face','leather','bow','string'):
                            self.assertIn(RANGER_COLORS[key],colors,(state,i,key))
                        self.assertLessEqual(frame.get_bounding_rect().bottom,123)
                        self.assertGreaterEqual(frame.get_bounding_rect().left,45)
                        self.assertLessEqual(frame.get_bounding_rect().right,155)
                        if not angle:
                            # The head is narrow, the upper face dark, and the cowl
                            # connects directly to the jerkin rather than floating.
                            self.assertTrue(frame.get_at((cx,cy+6)).a)
                            self.assertFalse(frame.get_at((cx+13,cy-7)).a)
                        flipped=pygame.transform.flip(frame,True,False)
                        self.assertEqual(pygame.image.tobytes(frame,'RGBA'),
                                         pygame.image.tobytes(pygame.transform.flip(flipped,True,False),'RGBA'))
                        if state.startswith('Attack'):
                            self.assertEqual(bool(frame.get_at((cx+42,cy+15)).a),i<2)
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).digest() for p in before})

    def test_ranger_adult_proportions_across_poses_and_facings(self):
        from build_presentation import RANGER_POSES, RANGER_COLORS
        from config import ASSETS_DIR
        for state, poses in RANGER_POSES.items():
            sheet = pygame.image.load(str(Path(ASSETS_DIR)/'heroes/ranger'/(state+'.png')))
            for index, (cx, cy, angle) in enumerate(poses):
                frame = sheet.subsurface((index*200, 0, 200, 200))
                for facing in (1, -1):
                    image = frame if facing == 1 else pygame.transform.flip(frame, True, False)
                    center = cx if facing == 1 else 199-cx
                    with self.subTest(state=state, frame=index, facing=facing):
                        self.assertLessEqual(image.get_bounding_rect().bottom, 123)
                        if angle:
                            self.assertEqual(image.get_bounding_rect().bottom, 122)
                            continue
                        def width(y, lo, hi, colors=None):
                            pixels = [x for x in range(lo, hi+1)
                                      if image.get_at((center+facing*x, cy+y)).a
                                      and (colors is None or tuple(image.get_at((center+facing*x, cy+y)))[:3] in colors)]
                            self.assertTrue(pixels)
                            return max(pixels)-min(pixels)+1
                        head = max(width(y, -10, 10) for y in range(-8, 3))
                        chest = max(width(y, -9, 8, {RANGER_COLORS['leather']}) for y in range(8, 15))
                        waist = width(20, -8, 7, {RANGER_COLORS['leather']})
                        hips = width(24, -8, 7)
                        self.assertGreaterEqual(chest, head*0.9)
                        self.assertGreaterEqual(chest, 14)
                        self.assertGreaterEqual(waist, 11)
                        self.assertLess(waist, chest)
                        self.assertGreaterEqual(hips, 14)
                        self.assertLessEqual(hips, 18)
                        # Below the hips, trousers retain substantial mass in every gait.
                        legs = sum(tuple(image.get_at((x, y)))[:3] == RANGER_COLORS['legs']
                                   and image.get_at((x, y)).a
                                   for x in range(200) for y in range(cy+26, 122))
                        self.assertGreaterEqual(legs, 35)

    def test_huntress_alias_migrates_to_ranger(self):
        path = Path(self.directory.name) / 'legacy.json'
        path.write_text(json.dumps({'version':2,'last_class':'huntress','high_score':99}))
        save = SaveData(path)
        self.assertEqual(save.last_class, 'ranger')
        save.save()
        self.assertEqual(json.loads(path.read_text())['last_class'], 'ranger')
        self.game.reset_game('huntress')
        self.assertEqual(self.game.knight.class_id, 'ranger')
        self.assertEqual(self.game.knight.stats['name'], 'Ranger')
        self.assertEqual(list(CLASSES), ['warrior','ranger','wizard'])
        self.assertEqual(CLASSES['warrior']['name'], 'Knight')

    def test_logo_transparency_and_font_logo_fallback(self):
        from config import ASSETS_DIR
        from ui import init_fonts, make_logo, logo
        emblem = pygame.image.load(str(Path(ASSETS_DIR) / 'ui/cruel-world-logo.png'))
        self.assertEqual(emblem.get_size(), (680,160))
        self.assertEqual(emblem.get_at((0,0)).a, 0)
        self.assertGreater(pygame.mask.from_surface(emblem).count(), 5000)
        with patch('ui.FONT_ROOT', Path('/missing-fonts')):
            fonts = init_fonts()
            self.assertTrue(fonts['small'].render('Ranger',True,(255,255,255)).get_width())
            self.assertTrue(make_logo(fonts).get_bounding_rect().width)
        with patch('pygame.image.load', side_effect=FileNotFoundError):
            logo(self.game.screen, fonts, (400,140))

    def test_all_menu_modes_and_selected_cards(self):
        for mode in ('title','class','settings','pause','over','victory'):
            self.game.change_mode(mode)
            for index in range(len(self.game.options())):
                self.game.selection = index
                self.game.draw()
                self.assertGreater(pygame.mask.from_surface(self.game.screen).count(), 400000)

    def test_ranger_original_attack_hurt_and_death_timing(self):
        self.game.reset_game('ranger')
        hero = self.game.knight
        self.assertEqual(len(hero.frames['Hit']), 3)
        self.assertEqual(len(hero.frames['Death']), 8)
        for secondary, length in ((False, 21), (True, 30)):
            hero.pending_attack = None
            hero.secondary_cooldown = 0
            hero.set_state('Idle')
            (hero.secondary if secondary else hero.attack)()
            for _ in range(length - 1): hero.update_animation(1000 / 60)
            self.assertIsNotNone(hero.pending_attack)
            hero.update_animation(1000 / 60)
            self.assertIsNone(hero.pending_attack)
