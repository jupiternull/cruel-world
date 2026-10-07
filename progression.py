"""Bounded loadouts and completed-expedition records; no gameplay randomness."""
import random

DISCOVERIES = (('cache', 'sanctuary'), ('ledger', 'armory'), ('brazier0', 'brazier1', 'brazier2', 'record', 'monument'), ('seal0', 'seal1', 'seal2', 'testament'))

MATERIALS = ('Sovereign Mycelium', 'Marauder Iron', 'Lunar Remnant', 'Pyre Crown')
PROVISIONS = ('Field Dressing', 'Warding Salt', 'Hunters Charm')
UPGRADES = {
    'warrior': [('Living lining', 'healing', 5, 'Healing pickups restore 5 extra HP.'),
                ('Tempered guard', 'recovery', 18, 'Shield rush recovers 18 ticks sooner.'),
                ('Moonstep greaves', 'mobility', 12, 'Dodge recovers 12 ticks sooner.')],
    'ranger': [('Forager binding', 'healing', 5, 'Healing pickups restore 5 extra HP.'),
               ('Iron bow fittings', 'recovery', 21, 'Volley recovers 21 ticks sooner.'),
               ('Lunar fletching', 'reach', 10, 'Arrows fly for 10 extra ticks.')],
    'wizard': [('Mycelial focus', 'healing', 5, 'Healing pickups restore 5 extra HP.'),
               ('Iron sigil', 'recovery', 30, 'Arcane wave recovers 30 ticks sooner.'),
               ('Moonward clasp', 'mobility', 20, 'Blink recovers 20 ticks sooner.')],
}
for upgrades in UPGRADES.values():
    upgrades.append(('Cinder ward', 'healing', 8, 'Healing pickups restore 8 extra HP.'))

SAYINGS = (
    'Death keeps no ledger. The Chronicler insists on one.',
    'Darkness charges no toll, but takes its due.',
    'A sharp blade still needs a steady hand.',
    'Drink after the watch; the wall has no patience for swaying.',
    'Court her with clean boots. Even courage tracks mud.',
    'A warm bed wins more hearts than a cold boast.',
    'The living mend their socks. The dead have other troubles.',
    'Keep one coal for morning and one friend for winter.',
    'A full cup is poor armour, but excellent company.',
    'The bravest campfire is the one that lasts till dawn.',
    'Bring your shield home. We are short of serving trays.',
    'No banner ever stitched its own holes.',
)


class Sayings:
    def __init__(self, seed=None):
        self.random = random.Random(seed)
        self.pool = []

    def next(self):
        if not self.pool:
            self.pool = list(SAYINGS)
            self.random.shuffle(self.pool)
        return self.pool.pop()


def apply_loadout(hero, save):
    hero.upgrade_effects = {}
    selected = save.equipped.get(hero.class_id)
    if selected in save.purchased.get(hero.class_id, []) and selected in save.cleared_regions:
        _, effect, amount, _ = UPGRADES[hero.class_id][selected]
        hero.upgrade_effects[effect] = amount


def effect(hero, name):
    return getattr(hero, 'upgrade_effects', {}).get(name, 0)


class Expedition:
    def __init__(self, provision):
        self.provision = provision if provision in PROVISIONS else PROVISIONS[0]
        self.used = False
        self.kill_claims = set()
        self.wave_claims = set()

    @property
    def consumed(self):
        return self.provision == PROVISIONS[0] and self.used

    @property
    def status(self):
        if self.provision == PROVISIONS[0]:
            return 'consumed' if self.consumed else 'ready'
        return 'active / triggered' if self.used else 'active / not triggered'

    @property
    def result(self):
        return 'Selected: ' + self.provision + ' | ' + self.status

    def update(self, hero):
        if self.provision == PROVISIONS[0] and not self.used and hero.alive and hero.health <= hero.max_health * .25:
            self.used = True
            hero.heal(25)

    def hazard_damage(self, damage):
        if self.provision == PROVISIONS[1]:
            self.used = True
            return max(1, damage * 3 // 4)
        return damage

    def discovery_score(self, score):
        if self.provision == PROVISIONS[2]:
            self.used = True
            return score + score // 10
        return score


def reaction(index, save, class_id):
    before = ('Count your supplies before your boasts.', 'One fitting at a time. Bring back something worth forging.',
              'The first road is open. The others await proof.', 'Come back breathing; I can handle the scratches.',
              'Practice your timing before trusting a spell.', 'Your feet are part of your weapon.', 'An empty page is a reason to travel.')
    after = ('New supplies are stacked by the door.', 'Your trophy bought us time at the forge.',
             'Another route stands ready.', 'The beds are quieter tonight.', 'The air feels less burdened.',
             'Now practice what kept you alive.', 'I have ink enough for your return.')
    final = ('Four roads, and still mouths to feed.', 'Peace is no excuse for a dull edge.',
             'The roads remain open for another watch.', 'Keep the bandages. Quiet is rarely permanent.',
             'The lamps burn steadier now.', 'Victory still needs practice.', 'Four names crossed out. Yours remains in the living column.')
    line = (final if len(save.cleared_regions) == 4 else after if save.cleared_regions else before)[index]
    guidance = {'warrior': 'Keep the combo deliberate.', 'ranger': 'Leave room to evade.', 'wizard': 'Save a blink for danger.'}
    discoveries = sum(len(r.get('discoveries', [])) for r in save.records.values())
    return [line, guidance[class_id]] + ([f'{discoveries} landmarks entered in the ledger.'] if index in (2, 6) and discoveries else [])
