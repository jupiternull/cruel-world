"""Pack 01 actors for the pilot; legacy IDs and combat timings remain stable.

The pack has no run, jump, fall, evade, or climbing sheets: Walk supplies
movement/air/evade, Idle supplies ledge holds, and Block supplies shield rush.
Archer's third attack reuses Attack02. No derivative or placeholder art is used.
Source frames are sampled over the existing action duration so damage/recovery
and campaign balance do not change when source sheet lengths differ.
"""
from pathlib import Path

import pygame
from config import ASSETS_DIR


PACK_ROOT = (Path(ASSETS_DIR) / 'vendor/zerie/pack01-full' /
             'Tiny RPG Character Asset Pack 01 v2.0 -Full 22 Characters' /
             'Characters(100x100 split)')
PLAYER_ACTORS = {'warrior': 'Knight', 'ranger': 'Archer', 'wizard': 'Wizard'}
CLASS_ALIASES = {'knight': 'warrior', 'archer': 'ranger', 'huntress': 'ranger'}
PLAYER_ACTIONS = {
    'Idle': 'Idle', 'Run': 'Walk', 'Jump': 'Walk', 'Fall': 'Walk',
    'Attack1': 'Attack01', 'Attack2': 'Attack02', 'Attack3': 'Attack03',
    'Hit': 'Hurt', 'Death': 'Death', 'Roll': 'Walk', 'Block': 'Block',
    'BlockIdle': 'Block', 'WallSlide': 'Walk', 'LedgeGrab': 'Idle',
}
ENEMY_ACTIONS = {'Idle': 'Idle', 'Run': 'Walk', 'Walk': 'Walk',
                 'Attack': 'Attack01', 'Shield': 'Block', 'Take Hit': 'Hurt',
                 'Death': 'Death'}
# Each actor uses an existing combat archetype; boss identities remain unchanged.
REALM_ROSTERS = {
    'forest': {'faction': 'orc', 'enemies': (('Orc', 'Goblin'), ('Armored Orc', 'Goblin'))},
    'graveyard': {'faction': 'undead', 'enemies': (('Skeleton', 'Goblin'),
                  ('Greatsword Skeleton', 'Mushroom'), ('Armored Skeleton', 'Skeleton'))},
    'cave': {'faction': 'feral-depths', 'enemies': (('Slime', 'Mushroom'), ('Werebear', 'Skeleton'))},
}


CAMP_SERVICE_ACTORS = ('Swordsman', 'Armored Axeman', 'Lancer', 'Priest',
                       'Wizard', 'Knight Templar', 'Soldier')
CAMP_WORKER_ACTORS = ('Swordsman', 'Soldier', 'Lancer', 'Soldier')
CAMP_ADVENTURER_ACTORS = ('Archer', 'Knight', 'Priest')
CAMP_ACTIONS = {'Idle': 'Idle', 'Walk': 'Walk'}
_CAMP_FRAMES = {}


def camp_actor(actor):
    if actor not in _CAMP_FRAMES:
        _CAMP_FRAMES[actor] = load_actor(actor, CAMP_ACTIONS, {'Idle': 8, 'Walk': 8})
    return _CAMP_FRAMES[actor]


def draw_camp_actor(screen, frames, x, feet, ticks, walking=False, facing_right=True):
    frame = frames['Walk' if walking else 'Idle'][(ticks // 9) % 8]
    anchor = frames.anchor
    if not facing_right:
        frame = pygame.transform.flip(frame, True, False)
        center = frame.get_width() - anchor.centerx
    else:
        center = anchor.centerx
    screen.blit(frame, (round(x-center), round(feet-anchor.bottom)))


def canonical_class(value):
    return CLASS_ALIASES.get(value, value)


def source_path(actor, action):
    return PACK_ROOT / actor / actor / f'{actor}_{action}.png'


def action_sources(actor, actions):
    result = dict(actions)
    if actor in ('Lancer', 'Knight Templar') and 'Walk' in result:
        result['Walk'] = 'Walk01'
    if actor == 'Archer' and 'Attack3' in result:
        result['Attack3'] = 'Attack02'
    if actor in ('Armored Skeleton', 'Werebear'):
        result['Shield'] = 'Idle'
    return result


class ActorFrames(dict):
    """State sequences carrying the source actor, mappings, and standing pivot."""


def load_actor(actor, actions, counts, scale=2.5):
    sources = action_sources(actor, {state: actions[state] for state in counts})
    loaded = {}
    for action in set(sources.values()):
        path = source_path(actor, action)
        sheet = pygame.image.load(str(path)).convert_alpha()
        width, height = sheet.get_size()
        if height != 100 or width % 100:
            raise ValueError(f'{path}: expected a horizontal 100x100 frame sheet')
        loaded[action] = [pygame.transform.scale(sheet.subsurface((x, 0, 100, 100)),
                          (round(100 * scale), round(100 * scale)))
                          for x in range(0, width, 100)]
        if not loaded[action] or any(not f.get_bounding_rect().width for f in loaded[action]):
            raise ValueError(f'{path}: blank actor frame')
    result = ActorFrames()
    for state, count in counts.items():
        frames = loaded[sources[state]]
        result[state] = [frames[round(i * (len(frames) - 1) / max(1, count - 1))]
                         for i in range(count)]
    # Use the standing body, not weapon sweeps or prone death frames, as the pivot.
    bounds = [f.get_bounding_rect() for f in loaded['Idle']]
    anchor = bounds[0].copy()
    for bound in bounds[1:]:
        anchor.union_ip(bound)
    result.anchor = anchor
    result.actor = actor
    result.action_sources = sources
    return result


def runtime_sources(hero_manifest, monster_manifest):
    files = set()
    for class_id, actor in PLAYER_ACTORS.items():
        actions = action_sources(actor, {s: PLAYER_ACTIONS[s] for s in hero_manifest[class_id][-1]})
        files.update(source_path(actor, action) for action in actions.values())
    for roster in REALM_ROSTERS.values():
        for actor, species in roster['enemies']:
            actions = action_sources(actor, {s: ENEMY_ACTIONS[s] for s in monster_manifest[species]})
            files.update(source_path(actor, action) for action in actions.values())
    for actor in set(CAMP_SERVICE_ACTORS + CAMP_WORKER_ACTORS + CAMP_ADVENTURER_ACTORS):
        files.update(source_path(actor, action) for action in action_sources(actor, CAMP_ACTIONS).values())
    return sorted(files)
