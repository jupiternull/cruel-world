"""Local licensed catalog and authored Cinder Dominion encounters."""
from pathlib import Path
import pygame
from zerie_runtime import ActorFrames

ROOT = Path(__file__).resolve().parent / 'assets/vendor'
PACK = ROOT / 'zerie/pack02-full/Tiny RPG Character Asset Pack 02 -Full 20 Characters/Characters(100x100 split)'
ENCOUNTERS = (
    ('Demon_A', 'Demon_B', 'Hellhound'),
    ('Black Knight_A', 'Black Knight_B', 'Demoness_B'),
    ('Demon_C', 'Demon_D', 'Warlock'),
    ('Minotaur',),
    ('Hellbat', 'Blood Monster_B', 'Ghostfire'),
    ('Blood Monster_A', 'Lava Slime', 'Eyeball Monster'),
    ('Demon_E', 'Demoness_A', 'Flame Golem'),
    ('Black Knight_C',),
)
CATALOG = {name: {'role': 'boss' if name == 'Black Knight_C' else
            'miniboss' if name == 'Minotaur' else
            'caster' if name in ('Warlock', 'Eyeball Monster', 'Ghostfire') else
            'flying' if name in ('Hellbat', 'Blood Monster_B') else
            'elite' if name in ('Black Knight_A', 'Black Knight_B', 'Flame Golem', 'Demon_E') else 'melee',
            'projectile': {'Warlock': 'Attack02_Effect', 'Eyeball Monster': 'Beam',
                           'Ghostfire': 'Beam', 'Black Knight_C': 'Beam'}.get(name)}
           for wave in ENCOUNTERS for name in wave}
SCENES = tuple((pack, filename) for pack, filenames in (
    ('underfire', ('01_the_altar', '02_the_chamber', '04_the_hall', '03_the_deep')),
    ('hellwake', ('01_hollowfall', '02_emberflow', '03_cindervault', '04_pyreheart')))
    for filename in filenames)
AREA_NAMES = ('Ashen Altar', 'Iron Chamber', 'Warlock Hall', 'Minotaur Descent',
              'Hollowfall', 'Emberflow', 'Cindervault', 'Pyreheart')


def sheets(actor):
    directory = PACK / actor / actor
    return {p.stem[len(actor)+1:]: p for p in directory.glob(actor + '_*.png')}


def load_actor(actor):
    paths = sheets(actor)
    idle = 'Idle' if 'Idle' in paths else 'Flying'
    movement = 'Flying' if 'Flying' in paths else 'Walk' if 'Walk' in paths else idle
    mappings = {'Idle': idle, 'Walk': movement, 'Run': movement, 'Flight': movement,
                'Attack': 'Attack01', 'Take Hit': 'Hurt', 'Death': 'Death', 'Shield': 'Block'}
    result = ActorFrames()
    cache = {}
    for state, action in mappings.items():
        action = action if action in paths else idle
        if action not in cache:
            sheet = pygame.image.load(str(paths[action])).convert_alpha()
            w, h = sheet.get_size()
            if h != 100 or w % 100:
                raise ValueError(f'{paths[action]}: expected horizontal 100px frames')
            cache[action] = [pygame.transform.scale(sheet.subsurface((x, 0, 100, 100)), (250, 250)) for x in range(0, w, 100)]
        result[state] = cache[action]
    for action in ('Attack02', 'Attack03'):
        if action in paths:
            sheet = pygame.image.load(str(paths[action])).convert_alpha()
            result[action] = [pygame.transform.scale(sheet.subsurface((x, 0, 100, 100)), (250, 250)) for x in range(0, sheet.get_width(), 100)]
    result.anchor = result['Idle'][0].get_bounding_rect()
    result.actor = actor
    result.action_sources = {s: a if a in paths else idle for s, a in mappings.items()}
    projectile = CATALOG[actor]['projectile']
    result.projectile = []
    if projectile in paths:
        sheet = pygame.image.load(str(paths[projectile])).convert_alpha()
        result.projectile = [pygame.transform.scale(sheet.subsurface((x, 0, 100, 100)), (150, 150)) for x in range(0, sheet.get_width(), 100)]
    return result


def scene_path(pack, filename):
    return ROOT / f'firepious/world-bundle/{pack}/{pack}/1x/{filename}.png'


def runtime_sources():
    return [p for actor in CATALOG for p in sheets(actor).values()] + [scene_path(*scene) for scene in SCENES]
