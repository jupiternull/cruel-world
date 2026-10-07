import pygame


ENVIRONMENTS = [
    {'id': 'forest', 'name': 'THE VERDANT RUINS', 'width': 3840,
     'color': (32, 61, 49), 'music': 'forest_theme', 'ambience': 'forest_night_ambience',
     'enemies': ('Goblin', 'Flying eye'), 'boss': 'Mushroom', 'boss_name': 'SPORE SOVEREIGN',
     'platforms': [(160, 464, 224), (448, 368, 224), (768, 448, 256),
                   (1120, 400, 224), (1456, 304, 224), (1744, 448, 256), (2672, 448, 224), (3008, 400, 224), (3472, 464, 192)],
     'climbs': [(272, 464, 96), (560, 368, 192), (1568, 304, 256), (3120, 400, 160)],
     'hazards': [(1024, 544, 64, 16), (2048, 544, 64, 16)],
     'zones': (640, 1840, 3340), 'checkpoints': (96, 1280, 3024)},
    {'id': 'cave', 'name': 'THE SUNKEN KEEP', 'width': 4032,
     'color': (28, 23, 36), 'music': 'battle_theme', 'ambience': 'cave_ambience',
     'enemies': ('Mushroom', 'Skeleton'), 'boss': 'Goblin', 'boss_name': 'THE IRON MARAUDER',
     'platforms': [(192, 432, 256), (512, 336, 192), (832, 464, 192),
                   (1152, 368, 256), (1472, 272, 224), (1792, 368, 224),
                   (2112, 464, 192), (2704, 400, 256), (3104, 432, 192), (3584, 448, 224)],
     'climbs': [(304, 432, 128), (608, 336, 224), (1584, 272, 288), (2816, 400, 160)],
     'hazards': [(736, 544, 64, 16), (1696, 544, 64, 16), (2336, 544, 64, 16)],
     'zones': (640, 2200, 3500), 'checkpoints': (96, 1984, 3200)},
    {'id': 'graveyard', 'name': 'THE MOON GRAVEYARD', 'width': 4224,
     'color': (15, 21, 43), 'music': 'graveyard_theme', 'ambience': 'interior_night_ambience',
     'enemies': ('Goblin', 'Mushroom', 'Skeleton'), 'boss': 'Flying eye', 'boss_name': 'MOON EATER',
     'platforms': [(160, 448, 192), (416, 352, 224), (768, 432, 192),
                   (1088, 336, 224), (1408, 448, 192), (1728, 352, 256),
                   (2080, 432, 224), (2464, 336, 256), (2928, 448, 192), (3360, 416, 224), (3808, 448, 192)],
     'climbs': [(256, 448, 112), (528, 352, 208), (1200, 336, 224), (2592, 336, 224), (3472, 416, 144)],
     'hazards': [(960, 544, 64, 16), (2016, 544, 64, 16), (2720, 544, 64, 16)],
     'zones': (640, 2050, 3680), 'checkpoints': (96, 1536, 3360)},
]


from underworld import ENCOUNTERS
from underworld_transitions import TRANSITIONS, near_transition
ENVIRONMENTS.append({
    'id': 'underworld', 'name': 'THE CINDER DOMINION', 'width': 10240,
    'color': (35, 12, 20), 'music': 'underworld_exploration',
    'boss_music': 'pyre_regent', 'ambience': 'cave_ambience',
    'enemies': ('Goblin', 'Flying eye', 'Skeleton'), 'boss': 'Goblin',
    'boss_name': 'THE PYRE REGENT', 'faction': 'infernal',
    'enemy_roster': tuple((a, 'Goblin') for wave in ENCOUNTERS for a in wave),
    'platforms': [(x, 432 if i % 2 else 464, 224) for i, x in enumerate(range(400, 9700, 640))],
    'climbs': [(x + 96, 432 if i % 2 else 464, 128 if i % 2 else 96) for i, x in enumerate(range(400, 9700, 640))],
    'hazards': [(x, 544, 80, 16) for x in (920, 2200, 3480, 4760, 6040, 7320, 8600)],
    'zones': (640, 1920, 3200, 4480, 5760, 7040, 8320, 9600),
    'checkpoints': (96,) + tuple(t.x + 264 for t in TRANSITIONS),
})


_underworld = ENVIRONMENTS[-1]
_underworld['platforms'] = [p for p in _underworld['platforms'] if not near_transition(p[0], p[2])] + [
    (r.x, r.y, r.width) for t in TRANSITIONS for r in t.platforms]
_underworld['climbs'] = [c for c in _underworld['climbs'] if not near_transition(c[0], 24)] + [
    (r.x, r.y, r.height) for t in TRANSITIONS for r in t.ladders]
_underworld['hazards'] = [h for h in _underworld['hazards'] if not near_transition(h[0], h[2])]

from zerie_runtime import REALM_ROSTERS

for environment in ENVIRONMENTS:
    if environment['id'] == 'underworld':
        continue
    roster = REALM_ROSTERS[environment['id']]
    environment['faction'] = roster['faction']
    environment['enemy_roster'] = roster['enemies']
    environment['enemies'] = tuple(species for actor, species in roster['enemies'])


class Campaign:
    def __init__(self):
        self.index = 0
        self.checkpoint = 96
        self.exit_open = False
        self.complete = False

    @property
    def environment(self):
        return ENVIRONMENTS[self.index]

    def advance(self):
        if self.index == len(ENVIRONMENTS) - 1:
            self.complete = True
            return False
        self.index += 1
        self.checkpoint = 96
        self.exit_open = False
        return True

    def update_checkpoint(self, x):
        old = self.checkpoint
        for point in self.environment['checkpoints']:
            if x >= point:
                self.checkpoint = max(self.checkpoint, point)
        return self.checkpoint != old


class World:
    def __init__(self, environment):
        self.data = environment
        self.width = environment['width']
        self.ground = pygame.Rect(0, 560, self.width, 40)
        self.platforms = [pygame.Rect(x, y, w, 16) for x, y, w in environment['platforms']]
        self.climbables = [pygame.Rect(x, y, 24, h) for x, y, h in environment['climbs']]
        self.hazards = [pygame.Rect(rect) for rect in environment['hazards']]
        self.exit = pygame.Rect(self.width - 112, 464, 48, 96)

    def move(self, actor, dx):
        features = getattr(self, 'features', None)
        if features and getattr(actor, 'class_id', None):
            dx *= features.movement_factor(actor)
        old = actor.rect.copy()
        actor.rect.x = max(0, min(self.width - actor.rect.width, actor.rect.x + int(dx)))
        if features and getattr(actor, 'class_id', None):
            for rect in features.blockers():
                if actor.rect.colliderect(rect):
                    if dx > 0 and old.right <= rect.left:
                        actor.rect.right = rect.left
                    elif dx < 0 and old.left >= rect.right:
                        actor.rect.left = rect.right

    def gravity(self, actor):
        if getattr(actor, 'climbing', None) is not None:
            actor.vel_y = 0
            return
        actor.vel_y = min(16, actor.vel_y + 1)
        previous = actor.rect.bottom
        actor.rect.y += int(actor.vel_y)
        actor.on_ground = False
        surfaces = [self.ground] + ([] if getattr(actor, 'drop_timer', 0) else self.platforms)
        if actor.vel_y >= 0:
            for surface in sorted(surfaces, key=lambda rect: rect.top):
                if actor.rect.right > surface.left and actor.rect.left < surface.right and previous <= surface.top <= actor.rect.bottom:
                    actor.rect.bottom = surface.top
                    actor.vel_y = 0
                    actor.on_ground = True
                    break
