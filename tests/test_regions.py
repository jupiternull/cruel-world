import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import hashlib
import json
import random
import tempfile
import unittest
from pathlib import Path
import pygame
from main import Game
from camera import Camera
from projectile import DamageSource
from build_region_assets import PALETTES, scene
from build_web import runtime_files

ROOT=Path(__file__).resolve().parents[1]


class RegionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=tempfile.TemporaryDirectory()
        cls.game=Game(Path(cls.directory.name)/'save.json')

    @classmethod
    def tearDownClass(cls):
        pygame.quit();cls.directory.cleanup()

    def setUp(self):
        self.game.reset_game('warrior');self.game.launch_expedition(0,debug=True)

    def region(self,index,class_id='warrior'):
        self.game.reset_game(class_id);self.game.launch_expedition(index,debug=True)
        return self.game.features,self.game.knight

    def test_derivative_dimensions_palette_transparency_hash(self):
        from PIL import Image
        manifest=json.loads((ROOT/'assets/regions/derivatives.json').read_text())
        expected={'water':(192,32),'falls':(192,128),'cell':(512,96),'statue':(192,96),
                  'pot':(128,32),'window':(64,32),'skeleton':(64,64),'cupboard':(64,96)}
        self.assertEqual(set(manifest),set(expected))
        for name,size in expected.items():
            record=manifest[name];path=ROOT/'assets/regions'/record['file']
            with Image.open(path) as image:
                self.assertEqual(image.size,size)
                self.assertEqual(list(size),record['size'])
                pixels=list(image.getdata())
                self.assertTrue(any(p[3]==0 for p in pixels))
                self.assertTrue(any(p[3]>0 for p in pixels))
                self.assertTrue(all(p[:3] in PALETTES[record['palette']] for p in pixels if p[3]))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),record['sha256'])

    def test_licenses_exact_supplied_bytes_and_provenance(self):
        expected={'GANDALFHARDCORE_REGION_TERMS.txt':('GandalfHardcore','https://gandalfhardcore.itch.io/free-pixel-art-sidescroller-asset-pack-32x32-overworld','3da5a215426198aef01c2dce3d5bd6cda0d59974b37f77607887562b1b11dbaf'),
                  'HYPNOBIUS_REGION_TERMS.txt':('Hypnobius','https://hypnobius.itch.io/grungy-dungeon-props','1646c7ad88274c6b225b16286acd034ca020a59aa651e28807c0edf09f363b41')}
        for filename,(creator,url,digest) in expected.items():
            data=(ROOT/'assets/licenses'/filename).read_bytes()
            header,terms=data.split(b'Original supplied terms (verbatim bytes follow):\n',1)
            self.assertIn(('Creator: '+creator).encode(),header)
            self.assertIn(url.encode(),header)
            self.assertIn(b'Retrieval date: October 6, 2026',header)
            self.assertIn(b'Selected files used:',header)
            self.assertEqual(hashlib.sha256(terms).hexdigest(),digest)

    def test_water_slowdown_only_ground_and_reset_without_jump_change(self):
        f,h=self.game.features,self.game.knight
        for x,expected in [(1300,3),(100,4),(2320,4)]:
            h.rect.midbottom=(x,560);h.on_ground=True
            old=h.rect.x;vy=h.vel_y;self.game.world.move(h,4)
            self.assertEqual(h.rect.x-old,expected);self.assertEqual(h.vel_y,vy)
        h.rect.midbottom=(1400,500);h.on_ground=False;old=h.rect.x
        self.game.world.move(h,4);self.assertEqual(h.rect.x-old,4)
        self.region(1);self.assertEqual(self.game.features.water,[])

    def test_real_primary_attacks_break_vines_for_every_class(self):
        for class_id in ('warrior','ranger','wizard'):
            f,h=self.region(0,class_id);p=f.breakables[0]
            self.game.state.wave=2
            h.rect.midbottom=(p.rect.left-30,560);h.facing_right=True
            h.attack()
            for _ in range(45):self.game.tick({})
            self.assertFalse(p.alive,class_id);self.assertTrue(p.rewarded)
            score=self.game.state.score
            for _ in range(20):self.game.tick({})
            self.assertEqual(self.game.state.score,score)

    def test_reward_once_and_enemy_sources_cannot_break_props(self):
        f,h=self.region(1);p=f.breakables[0];h.health-=20
        enemy=DamageSource(p.rect,100,'enemy',3)
        f.hit(enemy);self.assertTrue(p.alive)
        source=DamageSource(p.rect,100,'hero',3)
        f.hit(source);f.update(self.game)
        self.assertEqual(self.game.state.score,25);self.assertEqual(h.health,h.max_health-17)
        for _ in range(20):f.hit(source);f.update(self.game)
        self.assertEqual(self.game.state.score,25)
        f.retry(96);self.assertFalse(p.alive)

    def test_cache_once_across_retry_and_relaunch_resets(self):
        f,h=self.game.features,self.game.knight;h.rect.midbottom=(840,560);h.health-=30
        self.assertTrue(f.interact(self.game));self.assertEqual(self.game.state.score,120)
        self.assertEqual(h.health,h.max_health-18)
        self.assertFalse(f.interact(self.game));f.retry(96)
        self.assertFalse(f.interact(self.game));self.assertEqual(self.game.state.score,120)
        self.game.launch_expedition(0,debug=True)
        self.assertNotIn('cache',self.game.features.claimed)

    def test_interaction_priority_falls_back_to_secondary(self):
        f,h=self.game.features,self.game.knight;h.rect.midbottom=(840,560)
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e))
        self.assertIn('cache',f.claimed);self.assertEqual(h.secondary_cooldown,0)
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e))
        self.assertGreater(h.secondary_cooldown,0)

    def test_lever_animation_collision_retry_both_sides(self):
        f,h=self.region(1);h.rect.midbottom=(1776,560)
        for _ in range(20):self.game.world.move(h,4)
        self.assertEqual(h.rect.right,f.gate.left)
        h.rect.midbottom=(1776,560);self.assertTrue(f.interact(self.game))
        for _ in range(24):f.update(self.game)
        self.assertFalse(f.gate_open);self.assertGreater(f.gate_tick,1)
        for _ in range(24):f.update(self.game)
        self.assertTrue(f.gate_open)
        h.rect.midbottom=(1800,560)
        for _ in range(45):self.game.world.move(h,4)
        self.assertGreater(h.rect.left,f.gate.right)
        f.retry(96);self.assertFalse(f.gate_open);self.assertNotIn('lever',f.claimed)
        h.rect.midbottom=(1776,560);self.assertTrue(f.interact(self.game))
        f.retry(1984);self.assertTrue(f.gate_open)
        self.game.launch_expedition(1,debug=True);self.assertFalse(self.game.features.gate_open)

    def test_actual_checkpoint_retry_restores_gate_coherently(self):
        f,h=self.region(1);self.game.campaign.checkpoint=1984
        self.game.change_mode('over');self.game.selection=0;self.game.activate()
        for _ in range(30): self.game.tick({})
        self.assertEqual(self.game.knight.rect.x,1984)
        self.assertTrue(f.gate_open);self.assertEqual(self.game.mode,'play')
        self.game.campaign.checkpoint=96;self.game.change_mode('over');self.game.selection=0;self.game.activate()
        for _ in range(30): self.game.tick({})
        self.assertFalse(f.gate_open);self.assertIsNotNone(f.objects.get('lever'))

    def test_statue_reaction_is_nonlethal_and_deterministic(self):
        f,h=self.region(1);h.rect.midbottom=(2630,560)
        health=h.health;score=self.game.state.score;state=random.getstate()
        for _ in range(400):f.update(self.game)
        self.assertEqual(h.health,health);self.assertEqual(self.game.state.score,score)
        self.assertEqual(random.getstate(),state);self.assertGreater(f.statue_glow,0)
        f.retry(1984);self.assertEqual(f.statue_glow,0)

    def test_three_optional_braziers_reward_once_and_remain_on_retry(self):
        f,h=self.region(2);h.health-=30
        for i,x in enumerate((660,1860,2970)):
            h.rect.midbottom=(x,560);self.assertTrue(f.interact(self.game))
            self.assertEqual(self.game.state.score,180 if i==2 else 0)
        self.assertEqual(h.health,h.max_health-12);self.assertEqual(len(f.lit),3)
        score=self.game.state.score
        f.retry(1536);self.assertEqual(len(f.lit),3)
        self.assertFalse(f.interact(self.game));self.assertEqual(self.game.state.score,score)
        self.assertFalse(self.game.campaign.exit_open)
        self.game.launch_expedition(2,debug=True);self.assertEqual(self.game.features.lit,set())

    def test_pause_freezes_every_region_animation_and_mechanism(self):
        for index in range(3):
            f,h=self.region(index);f.gate_tick=1;f.notice_timer=20;f.statue_glow=90
            self.game.change_mode('pause')
            before=(f.ticks,f.gate_tick,f.notice_timer,f.statue_glow)
            for _ in range(10):self.game.tick({});self.game.draw()
            self.assertEqual(before,(f.ticks,f.gate_tick,f.notice_timer,f.statue_glow))

    def test_world_camera_and_render_all_subareas_for_every_class(self):
        for index in range(3):
            for class_id in ('warrior','ranger','wizard'):
                f,h=self.region(index,class_id);world=self.game.world
                self.assertTrue(3600<=world.width<=4400)
                for x in (0,world.width//3,world.width*2//3,world.width-32):
                    h.rect.x=x;self.game.camera.update(h.rect);self.game.draw()
                    self.assertTrue(0<=self.game.camera.x<=world.width-800)
                h.rect.y=100;self.game.world.move(h,99999)
                self.assertEqual(h.rect.right,world.width)
                self.game.world.move(h,-99999);self.assertEqual(h.rect.left,0)

    def test_original_assets_rebuild_deterministically_and_web_inclusion(self):
        for realm in PALETTES:
            for area in range(3):
                p=ROOT/'assets/regions'/f'{realm}-{area}.png';before=p.read_bytes()
                scene(realm,area);self.assertEqual(p.read_bytes(),before)
        files=runtime_files()
        self.assertIn(ROOT/'region_features.py',files)
        self.assertTrue(all(p in files for p in (ROOT/'assets/regions').glob('*.png')))
        self.assertFalse(any('Downloads' in str(p) or 'scratch' in str(p) for p in files))
