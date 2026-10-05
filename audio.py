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
        self.environment_data = None
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
                    pygame.mixer.music.load(str(music))
                    pygame.mixer.music.play(-1)
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
        self.music_channel.set_volume(volume * (0.25 if self.mode != 'play' else 0.55))
        self.ambience_channel.set_volume(volume * (0.18 if self.mode != 'play' else 0.3))

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

    def environment(self, data):
        self.environment_data = data
        if self.mode != 'play':
            self.set_mode(self.mode, refresh=True)
            return
        if not self.available:
            return
        self.current_environment = data['id']
        if data['music'] in self.loops:
            pygame.mixer.music.stop()
        elif self.fallback_music_loaded:
            pygame.mixer.music.play(-1)
            if self.paused:
                pygame.mixer.music.pause()
        for channel, name in ((self.music_channel, data['music']), (self.ambience_channel, data['ambience'])):
            channel.stop()
            if name in self.loops:
                channel.play(self.loops[name], loops=-1)
                self.music_loaded = True
                if self.paused:
                    channel.pause()
        self.apply_settings()

    def set_mode(self, mode, refresh=False):
        if mode == self.mode and not refresh:
            return
        self.mode = mode
        self.paused = mode != 'play'
        if not self.available:
            return
        # Stop transient gameplay cues and replace the two reserved loops atomically.
        pygame.mixer.stop()
        pygame.mixer.music.stop()
        if mode == 'play':
            if self.environment_data:
                self.environment(self.environment_data)
            return
        front_end = mode in ('title', 'class', 'settings')
        if front_end and self.fallback_music_loaded:
            pygame.mixer.music.play(-1)
        elif front_end and 'graveyard_theme' in self.loops:
            self.music_channel.play(self.loops['graveyard_theme'], loops=-1)
        ambience = 'cave_ambience' if front_end else (
            self.environment_data['ambience'] if self.environment_data else 'cave_ambience')
        sound = self.loops.get(ambience) or self.loops.get('cave_ambience')
        if sound:
            self.ambience_channel.play(sound, loops=-1)
        self.apply_settings()

    def pause(self, paused):
        self.paused = paused
        if self.available:
            if paused:
                pygame.mixer.pause()
                pygame.mixer.music.pause()
            else:
                pygame.mixer.unpause()
                pygame.mixer.music.unpause()
