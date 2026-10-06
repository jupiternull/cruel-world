import json
from copy import deepcopy
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
        self.cleared_regions = []
        self.settings = {'sound': True, 'volume': 0.7, 'fullscreen': False}
        self.error = ''
        self.purchased = {c: [] for c in ('warrior', 'ranger', 'wizard')}
        self.equipped = {}
        self.records = {}
        self.provision = 'Field Dressing'
        try:
            data = json.loads(self.path.read_text())
            if isinstance(data, dict):
                if data.get('version') in (2, 3, 4) and data.get('last_class') in ('warrior', 'ranger', 'huntress', 'wizard', 'knight', 'archer'):
                    from zerie_runtime import canonical_class
                    self.last_class = canonical_class(data['last_class'])
                furthest = data.get('furthest_environment', 0) if data.get('version') in (2, 3, 4) else 0
                if type(furthest) is int:
                    self.furthest_environment = max(0, min(2, furthest))
                cleared = data.get('cleared_regions', []) if data.get('version') in (3, 4) else list(range(self.furthest_environment))
                if isinstance(cleared, list):
                    self.cleared_regions = sorted({i for i in cleared if type(i) is int and 0 <= i < 3})
                from progression import PROVISIONS
                if data.get('provision') in PROVISIONS:
                    self.provision = data['provision']
                purchased = data.get('purchased', {})
                equipped = data.get('equipped', {})
                for c in self.purchased:
                    values = purchased.get(c, []) if isinstance(purchased, dict) else []
                    self.purchased[c] = sorted({i for i in values if type(i) is int and i in self.cleared_regions}) if isinstance(values, list) else []
                    selected = equipped.get(c) if isinstance(equipped, dict) else None
                    if type(selected) is int and selected in self.purchased[c]:
                        self.equipped[c] = selected
                records = data.get('records', {})
                if isinstance(records, dict):
                    for key, value in records.items():
                        if key in ('0', '1', '2') and isinstance(value, dict):
                            row = {'discoveries': sorted({v for v in value.get('discoveries', []) if isinstance(v, str) and len(v) < 80}) if isinstance(value.get('discoveries'), list) else []}
                            for field in ('best', 'completions', 'provisions'):
                                source = value.get(field, {})
                                allowed = PROVISIONS if field == 'provisions' else self.purchased
                                row[field] = {k: min(v, 1000000000) for k, v in source.items() if k in allowed and type(v) is int and v >= 0} if isinstance(source, dict) else {}
                            self.records[key] = row
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
                json.dump({'version': 4, 'purchased': self.purchased, 'equipped': self.equipped, 'records': self.records, 'provision': self.provision, 'cleared_regions': self.cleared_regions, 'high_score': self.high_score, 'settings': self.settings,
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

    def gate_unlocked(self, index):
        return index == 0 or index - 1 in self.cleared_regions

    def clear_region(self, index):
        self.cleared_regions = sorted(set(self.cleared_regions + [index]))
        self.furthest_environment = max(self.furthest_environment, min(2, index + 1))
        self.save()

    @property
    def materials(self):
        from progression import MATERIALS
        return [MATERIALS[i] for i in self.cleared_regions]

    def purchase(self, class_id, index):
        if class_id not in self.purchased or type(index) is not int or index not in self.cleared_regions:
            return False
        self.purchased[class_id] = sorted(set(self.purchased[class_id] + [index]))
        self.equipped[class_id] = index
        self.save()
        return True

    def complete_expedition(self, index, class_id, score, discoveries, expedition):
        snapshot = (self.cleared_regions, self.furthest_environment, self.records, self.high_score)
        self.records = deepcopy(self.records)
        first = index not in self.cleared_regions
        self.cleared_regions = sorted(set(self.cleared_regions + [index]))
        self.furthest_environment = max(self.furthest_environment, min(2, index + 1))
        row = self.records.setdefault(str(index), {'discoveries': [], 'best': {}, 'completions': {}, 'provisions': {}})
        row['discoveries'] = sorted(set(row['discoveries']) | set(discoveries))
        row['best'][class_id] = max(row['best'].get(class_id, 0), score)
        row['completions'][class_id] = row['completions'].get(class_id, 0) + 1
        row['provisions'][expedition.provision] = row['provisions'].get(expedition.provision, 0) + 1
        self.high_score = max(self.high_score, score)
        if not self.save():
            self.cleared_regions, self.furthest_environment, self.records, self.high_score = snapshot
            return None
        return first
