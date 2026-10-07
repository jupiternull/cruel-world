from pathlib import Path
import random
import pygame
from config import ASSETS_DIR


class AudioManager:
    def __init__(self, settings, directory=None):
        self.settings = settings
        self.sounds = {}
        self.available = False
        self.music_loaded = False
        self.fallback_music_loaded = False
        self.random = random.Random()
        self.variants = {}
        self.loops = {}
        self.current_environment = None
        self.paused = False
        self.mode = 'play'
        self.camp_morale = False
        self.environment_data = None
        self.boss_music_active = False
        self.fade = None
        self.loop_names = (None, None)
        self.loop_gain = 1.0
        self.pending_loops = None
        self.fallback_path = None
        directory = Path(directory or Path(ASSETS_DIR) / 'audio')
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.available = True
        except pygame.error:
            return
        supplied = {
            'attack': 'tap', 'hit': 'hurt', 'kill': 'explosion',
            'pickup': 'power_up', 'score': 'coin', 'jump': 'jump',
            'wave': 'power_up', 'boss': 'explosion',
            'game_over': 'explosion', 'menu': 'tap',
        }
        for name, filename in supplied.items():
            candidates = [directory / (name + extension) for extension in ('.ogg', '.wav')]
            candidates.extend(directory / 'sfx' / (filename + extension) for extension in ('.ogg', '.wav'))
            for path in candidates:
                if path.is_file():
                    try:
                        self.sounds[name] = pygame.mixer.Sound(str(path))
                        break
                    except (pygame.error, OSError):
                        continue
        for music in (directory / 'music.ogg', directory / 'music' / 'Ironchest_dungeon001.ogg'):
            if music.is_file():
                try:
                    self.loops['fallback'] = pygame.mixer.Sound(str(music))
                    self.fallback_path = music
                    self.music_loaded = True
                    self.fallback_music_loaded = True
                    break
                except (pygame.error, OSError):
                    continue
        pygame.mixer.set_num_channels(24)
        pygame.mixer.set_reserved(2)
        self.music_channel = pygame.mixer.Channel(0)
        self.ambience_channel = pygame.mixer.Channel(1)
        bundle = directory / 'tommusic'
        for path in sorted((bundle / 'sfx').glob('*.ogg')):
            name = path.stem.rstrip('0123456789').rstrip('_')
            try:
                sound = pygame.mixer.Sound(str(path))
                self.variants.setdefault(name, []).append(sound)
            except (pygame.error, OSError):
                pass
        for folder in ('music', 'ambience'):
            for path in sorted((bundle / folder).glob('*.ogg')):
                try:
                    self.loops[path.stem] = pygame.mixer.Sound(str(path))
                except (pygame.error, OSError):
                    pass
        for name in ('music', 'ambience', 'interior'):
            for extension in ('.ogg', '.wav'):
                path = directory / 'camp' / (name + extension)
                if path.is_file():
                    try:
                        self.loops['camp_' + name] = pygame.mixer.Sound(str(path))
                        break
                    except (pygame.error, OSError):
                        continue
        self.apply_settings()

    def apply_settings(self):
        if not self.available:
            return
        volume = self.settings['volume'] if self.settings['sound'] else 0
        for sound in self.sounds.values():
            sound.set_volume(volume)
        for variants in self.variants.values():
            for sound in variants:
                sound.set_volume(volume)
        pygame.mixer.music.set_volume(volume * (0.35 if self.mode != 'play' else 0.6))
        self.music_channel.set_volume(self.loop_gain * volume * (0.14 if self.mode == 'interior' else 0.25 if self.mode != 'play' else 0.55))
        self.ambience_channel.set_volume((0.9 if self.camp_morale and self.mode == 'camp' else 1) * self.loop_gain * volume * (0.18 if self.mode != 'play' else 0.3))

    def play(self, name):
        original_name = name
        name = {'jump': 'jump_stone', 'boss': 'arcane_wave', 'wave': 'chest_open'}.get(name, name)
        if name not in self.variants:
            name = {'sword_attack': 'attack', 'bow_attack': 'attack', 'fireball': 'attack',
                    'arcane_wave': 'attack', 'sword_block': 'attack', 'sword_hit': 'hit',
                    'bow_hit': 'hit', 'spell_hit': 'hit'}.get(original_name, original_name)
        if not self.available or not self.settings['sound']:
            return
        if name in self.variants:
            channel = pygame.mixer.find_channel()
            if channel:
                channel.play(self.random.choice(self.variants[name]))
        elif name in self.sounds:
            channel = pygame.mixer.find_channel()
            if channel:
                channel.play(self.sounds[name])

    def request_loops(self, names):
        if names[0] not in self.loops and 'fallback' in self.loops:
            names = ('fallback', names[1])
        if names == self.loop_names and self.pending_loops is None:
            return
        if names == self.pending_loops:
            return
        self.pending_loops = names
        self.fade = 'out'

    def update(self, dt):
        if not self.fade or self.paused:
            return
        dt = max(0, min(dt, .1))
        if self.fade == 'out':
            self.loop_gain = max(0, self.loop_gain - dt / .35)
            if self.loop_gain == 0:
                names = self.pending_loops
                self.pending_loops = None
                if self.available:
                    # Replace only changed loops at silence; the shared camp score keeps its phase.
                    for i, (channel, name) in enumerate(zip((self.music_channel, self.ambience_channel), names)):
                        if name != self.loop_names[i]:
                            channel.stop()
                            if name in self.loops:
                                channel.play(self.loops[name], loops=-1)
                self.loop_names = names
                self.fade = 'in'
        else:
            self.loop_gain = min(1, self.loop_gain + dt / .55)
            if self.loop_gain == 1:
                self.fade = None
        self.apply_settings()

    def environment(self, data):
        self.environment_data = data
        self.boss_music_active = False
        self.current_environment = data['id']
        if self.mode == 'play':
            self.request_loops((data['music'], data['ambience']))

    def boss_music(self, active=True):
        self.boss_music_active = active
        if self.mode == 'play' and self.environment_data:
            self.request_loops(self.environment_loops())

    def environment_loops(self):
        data = self.environment_data
        music = data.get('boss_music', data['music']) if self.boss_music_active else data['music']
        return music, data['ambience']

    def set_mode(self, mode, refresh=False):
        if mode == self.mode and not refresh:
            return
        self.mode = mode
        if mode in ('pause', 'settings', 'over'):
            self.pause(True)
            return
        self.pause(False)
        if mode in ('camp', 'interior'):
            self.current_environment = mode
            names = ('camp_music', 'camp_interior' if mode == 'interior' else 'camp_ambience')
        elif mode == 'play' and self.environment_data:
            names = self.environment_loops()
        elif mode == 'results':
            names = ('camp_music', 'camp_interior')
        else:
            names = ('graveyard_theme', 'cave_ambience')
        self.request_loops(names)
        self.apply_settings()

    def pause(self, paused):
        self.paused = paused
        if self.available:
            if paused:
                pygame.mixer.pause()
            else:
                pygame.mixer.unpause()
