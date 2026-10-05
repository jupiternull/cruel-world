import json
import os
import tempfile
import sys
from pathlib import Path


class SaveData:
    def __init__(self, path=None):
        root = Path('/tmp') if sys.platform == 'emscripten' else Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
        self.path = Path(path or os.environ.get('CRUELWORLD_SAVE_PATH', root / 'cruelworld/save.json'))
        self.high_score = 0
        self.last_class = 'warrior'
        self.furthest_environment = 0
        self.settings = {'sound': True, 'volume': 0.7, 'fullscreen': False}
        self.error = ''
        try:
            data = json.loads(self.path.read_text())
            if isinstance(data, dict):
                if data.get('version') == 2 and data.get('last_class') in ('warrior', 'ranger', 'huntress', 'wizard'):
                    self.last_class = 'ranger' if data['last_class'] == 'huntress' else data['last_class']
                furthest = data.get('furthest_environment', 0) if data.get('version') == 2 else 0
                if type(furthest) is int:
                    self.furthest_environment = max(0, min(2, furthest))
                score = data.get('high_score', 0)
                if type(score) is int:
                    self.high_score = max(0, score)
                settings = data.get('settings', {})
                if isinstance(settings, dict):
                    for key in ('sound', 'fullscreen'):
                        if type(settings.get(key)) is bool:
                            self.settings[key] = settings[key]
                    volume = settings.get('volume')
                    if type(volume) in (int, float) and 0 <= volume <= 1:
                        self.settings['volume'] = volume
        except (OSError, ValueError):
            pass

    def save(self):
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             dir=self.path.parent, prefix=self.path.name + '.',
                                             suffix='.tmp', delete=False) as stream:
                temporary = Path(stream.name)
                json.dump({'version': 2, 'high_score': self.high_score, 'settings': self.settings,
                           'last_class': self.last_class, 'furthest_environment': self.furthest_environment}, stream, indent=2)
            temporary.replace(self.path)
            self.error = ''
            return True
        except OSError:
            self.error = 'Could not save progress; check save-folder permissions.'
            return False
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def record(self, score):
        if score > self.high_score:
            self.high_score = score
            self.save()
