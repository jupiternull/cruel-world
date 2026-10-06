"""Authored supply hall with expedition provision selection and route inspection."""
import math
import random
import pygame
from campaign import World, ENVIRONMENTS
from camp import Camp, npc_sprite, inhabitant_sprite
from entities.hero import CLASSES
from zerie_runtime import draw_camp_actor

WIDTH = 1120
POINTS = [('exit', 90, 'Courtyard exit'), ('counter', 350, 'Quartermaster counter'),
          ('ledger', 620, 'Expedition ledger'), ('equipment', 870, 'Preparation rack')]


def storehouse_art():
    rng = random.Random(821)
    s = pygame.Surface((560, 300))
    s.fill((17, 18, 23))
    def rect(c, r): pygame.draw.rect(s, c, r)
    # Cutaway roof and thick masonry enclose a continuous clear walking lane.
    rect((48, 42, 38), (10, 73, 540, 207))
    for y in range(78, 280, 12):
        for x in range(12+(y%24)//2, 548, 24):
            rect((rng.randrange(49, 60), 48, 43), (x, y, 22, 10))
    rect((27, 24, 25), (10, 73, 540, 23))
    for x in (12, 145, 285, 420, 543):
        rect((31, 26, 26), (x+5, 88, 9, 192))
        rect((95, 68, 45), (x, 73, 7, 207))
        rect((126, 92, 58), (x, 73, 2, 207))
        pygame.draw.line(s, (89, 63, 43), (x, 95), (x+30, 125), 5)
    for y in (72, 103): rect((102, 74, 47), (10, y, 540, 7))
    for x in range(20, 550, 36):
        pygame.draw.line(s, (73, 53, 39), (x, 25), (x+38, 72), 6)
        pygame.draw.line(s, (114, 82, 51), (x, 25), (x+38, 72), 2)
    rect((70, 58, 45), (10, 280, 540, 20))
    for y in range(281, 300, 6):
        for x in range(12+(y%12)*3, 550, 36):
            rect((rng.randrange(75, 88), 64, 48), (x, y, 34, 4))
    # Recessed entry with stone jambs, heavy open leaf and lit threshold.
    rect((13, 20, 26), (25, 184, 38, 96))
    rect((98, 93, 79), (20, 180, 5, 100)); rect((98, 93, 79), (63, 180, 5, 100))
    rect((117, 103, 76), (20, 177, 48, 5))
    pygame.draw.polygon(s, (83, 57, 37), [(25,185),(36,192),(36,277),(25,280)])
    rect((156, 137, 95), (23, 277, 44, 3))
    # Shelving bays cast shadows; each row holds differently shaped supplies.
    for left in (77, 210):
        rect((25, 25, 27), (left, 134, 62, 110))
        for y in (156, 190, 229):
            for x in range(left+4, left+56, 17):
                if y == 156:
                    pygame.draw.ellipse(s, (148, 126, 85), (x,y-20,14,20))
                    pygame.draw.line(s,(78,63,43),(x+3,y-19),(x+11,y-19),2)
                else:
                    rect((108, 76, 47), (x,y-22,15,21))
                    pygame.draw.line(s,(49,37,30),(x,y-22),(x+14,y-2),2)
            rect((114, 82, 50), (left,y,62,4))
            rect((46, 34, 29), (left,y+4,62,4))
        for x in (left, left+59): rect((120, 88, 52), (x,130,3,113))
    # Counter has a solid front, ledger, scale and parcels, with space beside it.
    rect((30, 27, 27), (146, 250, 52, 30))
    rect((98, 67, 40), (145, 244, 53, 31))
    for x in range(148,198,8): rect((123, 86, 49), (x,246,2,27))
    rect((153, 109, 63), (140, 240, 63, 5))
    rect((201, 181, 131), (158,235,17,5)); rect((83,70,54),(166,235,1,5))
    pygame.draw.line(s,(153,145,113),(187,226),(187,240),2)
    pygame.draw.line(s,(153,145,113),(181,230),(194,230),1)
    # Route map and ledger desk: visible pins, paths and paper rolls.
    rect((28, 25, 26), (289, 143, 59, 81))
    rect((122, 87, 52), (286,140,61,77)); rect((180, 163, 118), (290,144,53,69))
    for points in ([(294,197),(307,182),(315,163)], [(311,205),(327,188),(338,161)]):
        pygame.draw.lines(s,(94,110,84),False,points,2)
    for x,y in ((305,183),(316,163),(330,186)): pygame.draw.circle(s,(144,56,47),(x,y),2)
    rect((112,79,45),(290,251,61,5)); rect((69,48,33),(296,256,3,24)); rect((69,48,33),(344,256,3,24))
    for x in (297,315,331): rect((204,184,138),(x,245,13,6))
    # Weapons are bundled on pegs above a preparation bench.
    rect((31,28,29),(373,158,83,87))
    for x in range(380,451,12):
        pygame.draw.line(s,(175,177,166),(x,168),(x,228),2)
        rect((131,93,52),(x-4,215,9,2)); rect((119,88,50),(x,229,2,9))
    pygame.draw.arc(s,(147,108,60),(439,171,12,56),-1.5,1.5,2)
    pygame.draw.line(s,(185,164,112),(445,172),(445,225),1)
    rect((123,86,50),(383,253,70,6)); rect((76,53,36),(389,259,4,21)); rect((76,53,36),(445,259,4,21))
    pygame.draw.ellipse(s,(126,135,133),(404,240,21,12)); rect((104,73,43),(431,247,16,6))
    # Locked reserve cage and a dark service passage imply rooms beyond the hall.
    rect((20,23,25),(479,137,58,103))
    for x in (484,508):
        rect((92,66,44),(x,204,23,30)); pygame.draw.line(s,(44,35,29),(x,204),(x+22,231),2)
    for x in range(478,539,8): rect((101,106,102),(x,136,2,106))
    for y in (137,180,240): rect((103,108,103),(477,y,61,3))
    rect((161,134,72),(505,190,6,8)); rect((13,16,20),(499,246,32,34))
    # Barrel staves, rope coils, herbs and lantern brackets establish scale.
    for x,y in ((73,252),(110,255),(461,250),(535,254)):
        pygame.draw.ellipse(s,(111,77,45),(x,y,17,27))
        for a in (4,8,12): pygame.draw.line(s,(77,54,35),(x+a,y+3),(x+a,y+24),1)
        for a in (5,21): rect((68,72,71),(x,y+a,17,3))
    for x in (122,251,467):
        pygame.draw.ellipse(s,(158,130,83),(x,113,14,23),2)
        pygame.draw.ellipse(s,(113,91,62),(x+3,117,8,15),1)
    for x in (94,239,393):
        pygame.draw.line(s,(140,117,77),(x,109),(x,126),1)
        for a in (-3,0,3): pygame.draw.line(s,(73,100,68),(x,123),(x+a,139),2)
    for x in (48,177,317,434):
        rect((36,28,26),(x-2,117,5,28)); rect((142,99,47),(x-4,138,9,14))
        rect((240,173,78),(x-2,140,5,9)); rect((66,46,32),(x-5,152,11,2))
    # Side returns and offset shadows put the furnishings in front of the wall.
    for x,y,w,h in ((77,134,62,110),(210,134,62,110),(286,140,61,77),(373,158,83,87)):
        pygame.draw.polygon(s,(28,25,25),[(x+w,y),(x+w+7,y+4),(x+w+7,y+h+5),(x+w,y+h)])
        pygame.draw.line(s,(137,99,58),(x,y),(x+w,y),1)
    for x in range(150,196,9):
        for y in range(249,272,5):
            pygame.draw.line(s,(88,59,38),(x,y),(x+4,y+1),1)
    for x,y in ((74,269),(112,273),(460,269),(530,273),(148,275),(383,277)):
        pygame.draw.polygon(s,(39,32,29),[(x,y),(x+18,y),(x+36,280),(x+12,280)])
    # Dusty flags near the walls give way to worn boards along the walking lane.
    for x in range(14,546,18):
        pygame.draw.line(s,(120,100,68),(x,282),(x+9,282),1)
        for y in (288,294):
            pygame.draw.line(s,(53,44,35),(x+3,y),(x+11,y),1)
    # A narrow raised back stair is decorative and stays behind the clear lane.
    for i in range(4):
        rect((64+i*7,57+i*5,47+i*4),(499-i*4,269+i*3,31+i*4,3))
    return pygame.transform.scale(s,(WIDTH,600))


class QuartermasterStorehouse(World):
    panel = Camp.panel
    intel = Camp.intel

    def __init__(self):
        super().__init__({'width': WIDTH, 'platforms': [], 'climbs': [], 'hazards': []})
        self.background = storehouse_art()
        self.dialogue = None
        self.ticks = 0
        self.quartermaster = npc_sprite(0)
        self.workers = [inhabitant_sprite(0), inhabitant_sprite(1)]

    def move(self, actor, dx):
        super().move(actor, dx)
        actor.rect.left = max(28, actor.rect.left)
        actor.rect.right = min(self.width-28, actor.rect.right)

    def nearby(self, hero):
        candidates = [p for p in POINTS if abs(hero.rect.centerx-p[1]) < 46 and hero.rect.bottom >= 530]
        return min(candidates,key=lambda p:abs(hero.rect.centerx-p[1])) if candidates else None

    def interact(self, game):
        if self.dialogue:
            self.dialogue = None
            return
        point = self.nearby(game.knight)
        if not point: return
        kind, _, title = point
        if kind == 'exit':
            game.transition_camp(False)
            return
        stats = CLASSES[game.class_id]
        if kind == 'counter':
            game.open_service('supplies')
            return
        elif kind == 'ledger':
            lines = []
            for i in range(len(ENVIRONMENTS)):
                intel = self.intel(game,i)
                lines += [intel[0] + ' | ' + intel[3], intel[1] + ' / ' + intel[2]]
        else:
            primary, defense = {'warrior': ('Three-hit sword combo','Dodge / roll'),
                                'ranger': ('Bow shot','Evade / roll'),
                                'wizard': ('Fireball','Blink / roll')}[game.class_id]
            lines = [stats['name'] + ' equipment', 'Primary: ' + primary,
                     'Secondary: ' + stats['secondary'] + f' ({stats["cooldown"]/60:g}s recovery)',
                     'Defensive movement: ' + defense,
                     f'Damage {stats["damage"]} | Max health {stats["health"]} | Speed {stats["speed"]}',
                     stats['hint'], 'A/D or arrows: move | Space: jump | E: inspect here']
        self.dialogue = {'title': title, 'lines': lines}

    def ambient_positions(self):
        return [(180+abs((self.ticks//3)%100-50),488), (970+abs((self.ticks//4+30)%60-30),488)]

    def draw(self, screen, fonts, game):
        screen.blit(self.background,(-game.camera.x,0))
        for x in (96,354,634,868):
            glow = pygame.Surface((190,270),pygame.SRCALPHA)
            pygame.draw.ellipse(glow,(235,156,68,16),(0,0,190,270))
            screen.blit(glow,(x-95-game.camera.x,280))
        draw_camp_actor(screen, self.quartermaster, 350-game.camera.x, 480, self.ticks)
        for i,(x,y) in enumerate(self.ambient_positions()):
            draw_camp_actor(screen, self.workers[i], x-game.camera.x, 550, self.ticks+i*13, True, i == 0)
            pygame.draw.rect(screen,(122,87,51),(x-6-game.camera.x,y+19,36,24))
            pygame.draw.line(screen,(57,42,31),(x-6-game.camera.x,y+19),(x+29-game.camera.x,y+42),3)
        for kind,x,label in POINTS:
            text = fonts['small'].render({'exit':'COURTYARD','counter':'SUPPLIES','ledger':'ROUTES','equipment':'PREPARE'}[kind],True,(220,203,163))
            screen.blit(text,(x-game.camera.x-text.get_width()//2,360))
        for i in range(24):
            x=(i*47+self.ticks//9)%WIDTH-game.camera.x
            y=290+(i*29+self.ticks//13)%220
            pygame.draw.rect(screen,(126,108,77),(x,y,2,2))

    def draw_foreground(self, screen, game):
        # Foreground lintel stays above the hero and all service labels.
        for x in (10,1090):
            pygame.draw.rect(screen,(34,26,25),(x-game.camera.x,100,16,460))
        pygame.draw.rect(screen,(42,30,26),(0,112,800,18))
        pygame.draw.line(screen,(102,72,44),(0,113),(800,113),3)

    def draw_overlay(self, screen, fonts, game):
        self.panel(screen,fonts,['QUARTERMASTER STOREHOUSE', 'E: inspect / exit   Esc: close panel / pause'],(170,12,460,58))
        target = self.nearby(game.knight)
        if target and not self.dialogue:
            self.panel(screen,fonts,[target[2] + '  [E]'],(155,310,490,36))
        if self.dialogue:
            lines = [self.dialogue['title']] + self.dialogue['lines'] + ['E / Enter / Esc: close']
            self.panel(screen,fonts,lines,(30,150,740,28*len(lines)+18))
