"""Deterministic castle refuge, scenery and state-aware camp services."""
import random
import pygame
from campaign import World, ENVIRONMENTS
from entities.hero import CLASSES
from zerie_runtime import (CAMP_SERVICE_ACTORS, CAMP_WORKER_ACTORS,
                           CAMP_ADVENTURER_ACTORS, camp_actor, draw_camp_actor)

ROLES = ['Quartermaster', 'Blacksmith', 'Scout / Cartographer', 'Healer', 'Arcanist', 'Trainer', 'Chronicler']
COLORS = [(155, 126, 76), (173, 79, 48), (77, 139, 123), (190, 184, 145), (127, 97, 165), (120, 139, 158), (159, 112, 112)]
POSITIONS = [160, 430, 680, 1400, 1640, 2040, 1860]
LINES = [
    ['Travel light. Keep your hands ready.', 'Your equipment is enough; your timing matters more.'],
    ['Edges endure when the wielder does.', 'Watch the recovery after every strike.'],
    ['I mark what we can see, nothing more.', 'Clear one route before trusting the next.'],
    ['Rest here. The road can wait a breath.', 'Leave with steady hands and a full heart.'],
    ['Power needs room to breathe.', 'Spend your strongest cast when the lane is clear.'],
    ['Strike the straw, then move out of reach.', 'Practice costs nothing here.'],
    ['I keep the tally when memory grows dim.', 'A return is worth recording.'],
]


WIDTH = 2200
GATES = (850, 970, 1090, 1210)
# Footprints are scenery behind the continuous, unobstructed walking lane.
STATIONS = [
    ('storehouse', (40, 330, 240, 230)),
    ('forge', (310, 280, 240, 280)),
    ('watchpost', (580, 290, 200, 270)),
    ('hospice', (1290, 330, 220, 230)),
    ('arcane annex', (1540, 310, 200, 250)),
    ('training yard', (1990, 390, 200, 170)),
    ('archive', (1770, 270, 180, 290)),
]
SIGN_NAMES = ['SUPPLIES', 'FORGE', 'MAPS', 'HEALER', 'ARCANE', 'TRAINING', 'ARCHIVE']


def courtyard():
    rng = random.Random(317)
    s = pygame.Surface((WIDTH//2, 300))
    s.fill((21, 25, 34))
    def rect(c, r):
        pygame.draw.rect(s, c, r)
    # Midground curtain wall, with irregular windows and buttresses.
    rect((42, 46, 53), (0, 104, 1100, 176))
    for y in range(106, 280, 12):
        for x in range(-12 if y % 24 else 0, 1100, 24):
            rect((rng.randrange(44, 53), 49, 55), (x+1,y+1,22,10))
    for x in range(0,1100,90):
        rect((51,54,60),(x,96,8,184))
        rect((61,62,67),(x-2,91,12,8))
        rect((16,23,30),(x+35,140,8,24))
    for x in range(0,1100,14):
        rect((53,56,62),(x,97,9,12))
    rect((57,54,51),(0,280,1100,20))
    for y in range(280,300,8):
        for x in range(-10 if y%16 else 0,1100,20):
            rect((rng.randrange(64,78),65,61),(x+1,y+1,18,6))
    # Supply store: broad timber warehouse with canvas loading canopy.
    rect((73,57,43),(20,194,120,86))
    pygame.draw.polygon(s,(66,53,48),[(14,196),(48,166),(120,166),(146,196)])
    for x in (24,76,134): rect((112,86,55),(x,196,4,84))
    pygame.draw.polygon(s,(129,111,73),[(20,219),(135,219),(144,237),(14,237)])
    rect((33,31,29),(78,240,27,40))
    for x,y in ((26,253),(42,259),(57,249)):
        rect((116,85,51),(x,y,14,16)); pygame.draw.line(s,(55,40,30),(x,y),(x+13,y+15),2)
    for x in (111,121): pygame.draw.ellipse(s,(146,125,85),(x,256,12,20))
    rect((93,69,43),(67,261,32,4)); rect((205,185,137),(71,257,10,4))
    for x in (30,35,40): pygame.draw.line(s,(169,164,143),(x,240),(x+5,255),1)
    # Forge: heavy stone base, steep slate roof, open furnace and chimney.
    rect((77,74,69),(155,184,120,96))
    pygame.draw.polygon(s,(43,48,55),[(149,185),(184,148),(249,148),(281,185)])
    rect((67,65,62),(247,130,17,67)); rect((100,91,78),(244,128,23,6))
    for x in (158,270): rect((105,79,52),(x,185,4,95))
    pygame.draw.ellipse(s,(29,26,26),(184,211,36,48)); rect((29,26,26),(184,237,36,40))
    rect((148,59,32),(189,237,26,35)); rect((227,125,44),(196,246,12,26))
    rect((113,117,116),(227,257,28,5)); rect((72,76,79),(232,262,16,10))
    for x in range(162,180,5):
        rect((105,76,45),(x,222,2,20)); rect((160,160,147),(x-2,220,6,3))
    # Map pavilion/watch platform: raised lookout and green canvas roof.
    rect((64,61,47),(299,189,84,91))
    pygame.draw.polygon(s,(57,100,87),[(289,201),(337,164),(393,201)])
    for x in (298,378): rect((133,108,69),(x,198,3,82))
    rect((96,77,52),(316,145,5,50)); rect((104,83,53),(314,150,50,4))
    rect((51,65,62),(321,122,39,27)); rect((102,130,111),(321,145,39,3))
    pygame.draw.line(s,(181,155,97),(338,137),(354,129),4)
    rect((184,172,132),(310,218,30,25)); pygame.draw.lines(s,(81,113,98),False,[(312,237),(320,225),(330,235),(337,220)],2)
    rect((111,86,54),(340,258,35,4)); rect((204,188,143),(344,254,27,4))
    # Keep district: four separate full-height stone arches.
    rect((62,63,68),(406,146,230,134))
    for x in (399,628):
        rect((75,76,79),(x,119,18,161))
        for a in range(x,x+18,6): rect((87,86,84),(a,112,4,12))
    for x in range(417,628,12): rect((77,77,79),(x,137,8,12))
    for i,g in enumerate(GATES):
        x=g//2; accent=((78,119,91),(100,88,121),(91,106,139),(184,91,54))[i]
        pygame.draw.ellipse(s,(111,108,97),(x-28,181,56,75)); rect((111,108,97),(x-28,219,56,61))
        pygame.draw.ellipse(s,(18,24,30),(x-21,188,42,65)); rect((18,24,30),(x-21,220,42,60))
        for a in range(x-18,x+20,9): rect((65,60,53),(a,218,3,62))
        for y in range(205,280,18): rect((126,119,102),(x-28,y,6,3)); rect((126,119,102),(x+22,y,6,3))
        rect(accent,(x-8,157,16,24)); pygame.draw.polygon(s,accent,[(x-8,181),(x,188),(x+8,181)])
        rect((143,132,104),(x-30,277,60,3))
        if i==0:
            for a in (-25,25): pygame.draw.lines(s,(68,104,73),False,[(x+a,261),(x+a-3,245),(x+a+2,229)],2)
        if i==1: pygame.draw.polygon(s,(139,117,166),[(x,193),(x-5,203),(x,211),(x+5,203)])
        if i==2: pygame.draw.circle(s,(176,183,203),(x,201),7); pygame.draw.circle(s,(18,24,30),(x+3,198),6)
    # Hospice: pale peaked cloth, open curtains and medicine alcove.
    pygame.draw.polygon(s,(151,149,127),[(640,216),(698,170),(760,216),(752,277),(648,277)])
    pygame.draw.polygon(s,(187,182,154),[(640,216),(698,165),(760,216)])
    rect((44,48,43),(682,222,32,55))
    pygame.draw.polygon(s,(163,162,139),[(680,216),(696,216),(677,267)])
    rect((102,90,64),(728,257,23,4)); rect((169,162,133),(728,251,23,6))
    for x in (655,662,669): rect((95,142,124),(x,255,4,10)); rect((202,190,148),(x,253,4,2))
    for x in (652,746): pygame.draw.lines(s,(74,112,79),False,[(x,243),(x-4,237),(x,231),(x+5,234)],2)
    # Arcane annex: asymmetrical violet roof and luminous crystal spire.
    rect((58,49,70),(775,206,90,74))
    pygame.draw.polygon(s,(87,67,109),[(766,207),(798,164),(820,190),(847,157),(874,207)])
    rect((24,27,40),(804,235,25,45))
    for x,y in ((787,247),(850,232),(832,175)):
        pygame.draw.polygon(s,(133,119,176),[(x,y-13),(x-5,y),(x,y+10),(x+5,y)])
    rect((101,75,56),(838,260,24,4))
    for y in (252,256): rect((151,120,141),(838,y,18,3))
    pygame.draw.circle(s,(130,119,162),(790,220),7,1)
    # Archive: tall narrow gabled hut, recessed shelves and desk.
    rect((79,62,54),(892,172,75,108))
    pygame.draw.polygon(s,(61,48,51),[(885,173),(930,136),(974,173)])
    for x in (893,963): rect((128,99,66),(x,172,4,108))
    rect((33,31,34),(902,190,29,52))
    for y in range(195,242,12):
        rect((117,84,55),(902,y+7,29,3))
        for x in range(905,928,5): rect((rng.randrange(100,160),99,83),(x,y,3,7))
    rect((40,34,32),(938,241,20,39)); rect((124,87,52),(901,259,33,5))
    rect((202,182,133),(904,255,21,4)); rect((231,183,93),(928,249,2,7))
    # Training enclosure is open, with targets and racks, not another shop.
    for x in range(997,1095,12): rect((89,70,48),(x,232,3,45))
    rect((110,86,54),(997,246,98,3))
    for x in (1010,1080):
        pygame.draw.circle(s,(161,139,93),(x,219),14); pygame.draw.circle(s,(101,70,50),(x,219),8,2); pygame.draw.circle(s,(177,106,66),(x,219),3)
        rect((106,79,48),(x-2,232,4,38))
    for x in (1029,1035,1041):
        pygame.draw.line(s,(183,184,174),(x,237),(x,271),2); rect((103,74,45),(x-4,262,8,2))
    # Fine masonry, timber seams, cloth folds and roof courses give surfaces depth.
    for left,right,top in ((155,275,190),(406,636,150)):
        for y in range(top,278,9):
            for x in range(left+2+(y%2)*5,right-4,14):
                if s.get_at((x,y))[:3] in ((77,74,69),(62,63,68)):
                    pygame.draw.line(s,(58,57,57),(x,y),(min(x+12,right-3),y),1)
    for left,right in ((22,138),(300,381),(777,864),(894,966)):
        for x in range(left,right,9):
            for y in range(208,276,12):
                c=s.get_at((x,y))[:3]
                if c in ((73,57,43),(64,61,47),(58,49,70),(79,62,54)):
                    pygame.draw.line(s,tuple(max(0,v-9) for v in c),(x,y),(x,y+10),1)
    for x in range(648,754,12):
        pygame.draw.line(s,(132,131,113),(x,226),(x+2,272),1)
    for left,right,top,color in ((20,140,173,(80,64,54)),(155,275,157,(57,62,69)),(893,965,151,(79,60,60))):
        for y in range(top,195 if left<280 else 172,7):
            for x in range(left,right,12):
                c=s.get_at((x,y))[:3]
                if c in ((66,53,48),(43,48,55),(61,48,51)):
                    pygame.draw.line(s,color,(x,y),(x+8,y),1)
    # Shared well and benches in gaps; low foreground clutter stays off the lane.
    pygame.draw.ellipse(s,(104,103,92),(280,270,16,8)); rect((83,83,76),(280,263,16,10)); pygame.draw.ellipse(s,(27,38,43),(282,261,12,5))
    for x in (145,390,765,880,985):
        rect((99,74,49),(x,274,15,3)); rect((66,50,38),(x+2,277,2,3)); rect((66,50,38),(x+12,277,2,3))
    for x in (12,151,285,390,637,770,878,981,1090):
        rect((87,65,43),(x,284,9,10)); pygame.draw.line(s,(48,39,32),(x,285),(x+8,292),1)
    # Recessed supply threshold, projecting eaves and masonry side returns.
    rect((17,22,26),(78,237,29,43))
    rect((120,96,65),(75,235,4,45)); rect((120,96,65),(107,235,4,45))
    rect((153,124,78),(75,232,36,5)); rect((159,139,98),(74,277,38,3))
    pygame.draw.polygon(s,(87,63,42),[(79,239),(85,242),(85,276),(79,278)])
    rect((187,155,90),(83,258,2,3))
    for left,right,top in ((20,140,196),(155,275,185),(892,967,173),(775,865,207)):
        rect((28,27,30),(left,top,right-left,6))
        pygame.draw.polygon(s,(37,34,34),[(right,top),(right+9,top-6),(right+9,274),(right,280)])
        rect((121,93,59),(left-3,top-3,right-left+8,3))
    for x in (38,117,164,258,788,850,945):
        rect((24,27,32),(x,207,10,20)); rect((114,88,55),(x-2,205,14,3))
        rect((152,122,70),(x+2,210,5,10)); rect((54,43,34),(x,225,12,3))
    # A roofed communal well occupies the gap, leaving the gate approach clear.
    pygame.draw.ellipse(s,(28,30,32),(277,276,30,4))
    rect((100,96,84),(279,258,24,17)); pygame.draw.ellipse(s,(29,39,41),(279,255,24,7))
    for x in (277,303): rect((113,83,48),(x,227,3,49))
    pygame.draw.polygon(s,(82,62,48),[(271,229),(291,214),(311,229)])
    pygame.draw.line(s,(166,136,79),(291,231),(291,256),1)
    rect((117,82,47),(287,248,8,8))
    # Wall walk casts a continuous shadow underneath its parapet.
    rect((27,31,38),(0,113,1100,5))
    rect((74,73,71),(0,110,1100,3))
    for x in range(7,1100,45): rect((52,51,51),(x,113,3,14))
    for x in (145,390,637,770,878,985):
        pygame.draw.polygon(s,(39,37,37),[(x,279),(x+23,279),(x+45,298),(x+17,298)])
    return pygame.transform.scale(s,(WIDTH,600))


def npc_sprite(index):
    return camp_actor(CAMP_SERVICE_ACTORS[index])


def inhabitant_sprite(index):
    return camp_actor(CAMP_WORKER_ACTORS[index])


ADVENTURERS = [
    {'name': 'Mara Reed', 'epithet': 'Orc-road survivor', 'x': 310, 'realm': 0,
     'locked': ['The forest road is barred. Wait for the scouts to open it.',
                'Orc tracks gather where the trees swallow the light.'],
     'available': ['Orcs are gathering along the forest road. I lost my trail there.',
                   'Take the first gate. Break their advance before another patrol vanishes.'],
     'cleared': ['You broke the forest threat. The road has room for footsteps again.',
                 'I will watch the tree line. A quiet wood can still hide an orc blade.']},
    {'name': 'Brann Hollow', 'epithet': 'Depth scout', 'x': 1515, 'realm': 1,
     'locked': ['Something feral scrapes beneath the cave mouth.',
                'Clear the forest route first. We cannot spare a patrol for the depths yet.'],
     'available': ['The cave route is open. Slime coats the stone; heavier things move below.',
                   'Take the second gate. Silence that threat before it reaches the surface.'],
     'cleared': ['The depths have fallen quiet since your return.',
                 'I will test the lower paths. Do not mistake silence for an empty cave.']},
    {'name': 'Vey Ash', 'epithet': 'Grave watcher', 'x': 1750, 'realm': 2,
     'locked': ['The graveyard dead are standing where they should lie.',
                'Settle the cave threat first. The third gate must wait.'],
     'available': ['The graveyard route is open. Undead gather beneath that pale sky.',
                   'Take the third gate. Put their master down before more graves open.'],
     'cleared': ['The dead have lost their master. That is a mercy, however brief.',
                 'I will keep watch by the graves. Rest while the bells are still.']},
]


def adventurer_dialogue(save, index):
    npc = ADVENTURERS[index]
    realm = npc['realm']
    state = 'cleared' if realm in save.cleared_regions else 'available' if save.gate_unlocked(realm) else 'locked'
    return {'title': npc['name'] + ' - ' + npc['epithet'],
            'lines': [ENVIRONMENTS[realm]['name'] + ' | ' + state.upper()] + npc[state]}


class Camp(World):
    def __init__(self):
        super().__init__({'width':WIDTH,'platforms':[],'climbs':[],'hazards':[]})
        self.background = courtyard()
        self.sprites = [npc_sprite(i) for i in range(7)]
        self.inhabitants = [inhabitant_sprite(i) for i in range(4)]
        self.adventurers = [camp_actor(actor) for actor in CAMP_ADVENTURER_ACTORS]
        self.dialogue = None
        self.notice = ''
        self.notice_timer = 0
        self.ticks = 0
        self.dummy = pygame.Rect(2130,500,30,60)
        self.hits = 0

    def nearby(self, hero):
        candidates = [('door',0,182)] + [('npc',i,x) for i,x in enumerate(POSITIONS) if i != 0] + [('gate',i,x) for i,x in enumerate(GATES)]
        candidates += [('adventurer', i, npc['x']) for i, npc in enumerate(ADVENTURERS)]
        candidates = [v for v in candidates if abs(hero.rect.centerx-v[2]) < 38 and hero.rect.bottom >= 530]
        return min(candidates,key=lambda v:abs(hero.rect.centerx-v[2])) if candidates else None

    def intel(self, game, index):
        e = ENVIRONMENTS[index]
        status = 'CLEARED' if index in game.save.cleared_regions else 'READY' if game.save.gate_unlocked(index) else 'LOCKED: clear the previous region'
        return [e['name'], 'Enemies: ' + ', '.join(e['enemies']), 'Boss: ' + e['boss_name'], status]

    def interact(self, game):
        if self.dialogue:
            if self.dialogue.get('gate') is not None:
                index = self.dialogue['gate']
                if game.save.gate_unlocked(index):
                    game.depart(index)
                    return
            self.dialogue = None
            return
        target = self.nearby(game.knight)
        if not target:
            return
        kind,index,_ = target
        if kind == 'adventurer':
            self.dialogue = adventurer_dialogue(game.save, index)
            return
        if kind == 'door':
            game.transition_camp(True)
            return
        if kind == 'gate':
            self.dialogue = {'title':'Expedition Gate', 'lines':self.intel(game,index), 'gate':index}
            return
        if index in (1, 6):
            game.open_service('forge' if index == 1 else 'journal')
            return
        hero = game.knight
        stats = CLASSES[game.class_id]
        detail = []
        if index == 0:
            detail = [stats['name'] + ': ' + stats['description'], f'Health {hero.health}/{hero.max_health} | Run score {game.state.score}', 'Ready for an unlocked Expedition Gate.']
        elif index == 1:
            detail = [f'Primary damage: {stats["damage"]}. Equipment does not wear down.', 'Knight: chain F strikes. Ranged heroes: keep a clear lane.']
        elif index == 2:
            detail = [f'{i+1}: {e["name"]} - ' + ('ready' if game.save.gate_unlocked(i) else 'locked') for i,e in enumerate(ENVIRONMENTS)] + ['Inspect each gate for enemies and boss.']
        elif index == 3:
            detail = ['Already well. Keep that strength.' if hero.health == hero.max_health else 'Your wounds are tended. Health fully restored.']
            hero.heal(hero.max_health)
        elif index == 4:
            detail = [stats['secondary'] + f': {stats["cooldown"]/60:g}s recovery.', 'E uses this ability on expeditions; R tests it here.', 'Flying enemies reward careful aim; attacks aim at nearby foes.']
        elif index == 5:
            detail = [stats['hint'].replace('E:', 'R:'), 'A/D or arrows: move | Space: jump | W/S: climb', f'Straw dummy in the training yard: {self.hits} hits. F/R to test.']
        else:
            detail = [f'Best score: {game.save.high_score}', 'Furthest known expedition: ' + ENVIRONMENTS[game.save.furthest_environment]['name'], f'Regions cleared: {len(game.save.cleared_regions)}/4']
        from progression import reaction
        self.dialogue = {'title':ROLES[index], 'lines':detail + reaction(index, game.save, game.class_id) + LINES[index]}

    def ambient_positions(self):
        return [(base + abs((self.ticks//3 + phase) % 100 - 50), 488)
                for base,phase in ((280,0),(740,32),(1220,61),(1910,17))]

    def draw(self, screen, fonts, game):
        import math
        camera = game.camera
        screen.fill((21,25,34))
        # Distant towers move slower than the buildings, visible above the wall.
        for x,h in ((60,130),(370,95),(740,150),(1110,120),(1510,160),(1900,110),(2310,145)):
            sx = int(x-camera.x*.35)
            pygame.draw.rect(screen,(32,37,47),(sx,205-h,90,h+50))
            for a in range(0,90,18): pygame.draw.rect(screen,(39,44,54),(sx+a,197-h,12,16))
            pygame.draw.rect(screen,(16,23,32),(sx+36,230-h,12,24))
        # The generated art has an opaque sky; expose only its wall/building layers.
        screen.blit(self.background,(-camera.x,192),pygame.Rect(0,192,WIDTH,408))
        for i,(kind,footprint) in enumerate(STATIONS):
            x = POSITIONS[i]-camera.x
            if i != 0:
                draw_camp_actor(screen, self.sprites[i], x, 560, self.ticks+i*11, facing_right=i < 4)
            label = fonts['small'].render(SIGN_NAMES[i],True,(220,203,163))
            pygame.draw.rect(screen,(43,35,31),(x-label.get_width()//2-7,458,label.get_width()+14,24))
            pygame.draw.rect(screen,COLORS[i],(x-label.get_width()//2-7,458,label.get_width()+14,24),1)
            screen.blit(label,(x-label.get_width()//2,460))
        for i,(x,y) in enumerate(self.ambient_positions()):
            sprite = self.inhabitants[i]
            draw_camp_actor(screen, sprite, x-camera.x, 550, self.ticks+i*11, True, (self.ticks//3+i*32)%100 >= 50)
        for i, npc in enumerate(ADVENTURERS):
            x = npc['x']-camera.x
            draw_camp_actor(screen, self.adventurers[i], x, 560, self.ticks+i*17, facing_right=i == 0)
            label = fonts['small'].render(npc['name'], True, (224,211,184))
            screen.blit(label, (x-label.get_width()//2, 418))
        # Crate porter crosses the supply route independently of gameplay RNG.
        porter_x = 215 + abs((self.ticks // 2) % 1420 - 710) - camera.x
        draw_camp_actor(screen, self.inhabitants[1], porter_x, 550, self.ticks, True, (self.ticks//2)%1420 >= 710)
        pygame.draw.rect(screen,(135,94,54),(porter_x-5,514,40,28))
        pygame.draw.line(screen,(63,44,31),(porter_x-5,514),(porter_x+34,541),3)
        # Guard silhouettes stand on the raised wall walk; forge tender works below.
        for x in (650,1235,1790):
            draw_camp_actor(screen, self.inhabitants[3], x-camera.x, 220, self.ticks+x)
        draw_camp_actor(screen, self.inhabitants[1], 490-camera.x, 550, self.ticks)
        hammer_y = 502 + (self.ticks//18)%2*9
        pygame.draw.line(screen,(151,127,89),(480-camera.x,518),(497-camera.x,hammer_y),3)
        pygame.draw.rect(screen,(142,146,140),(492-camera.x,hammer_y-3,12,6))
        # A small cat patrols the well; decorative actors never enter physics.
        cat = 550+abs(self.ticks//5%70-35)-camera.x
        pygame.draw.rect(screen,(151,136,113),(cat,544,18,8))
        pygame.draw.rect(screen,(151,136,113),(cat+13,539,7,8))
        pygame.draw.line(screen,(151,136,113),(cat,546),(cat-7,539),3)
        dummy = camera.rect(self.dummy)
        pygame.draw.line(screen,(116,83,48),(dummy.centerx,510),(dummy.centerx,560),6)
        pygame.draw.rect(screen,(168,141,80),dummy.inflate(-4,-18))
        pygame.draw.line(screen,(106,76,42),(dummy.x-7,522),(dummy.right+7,522),5)
        for i in game.save.cleared_regions:
            x = (610 + i * 82) - camera.x
            pygame.draw.rect(screen, (100, 96, 82), (x-22, 320, 44, 12))
            pygame.draw.rect(screen, (62, 65, 64), (x-14, 332, 28, 52))
            color = ((134, 166, 105), (160, 157, 145), (165, 150, 207), (239, 139, 69))[i]
            if i == 0:
                pygame.draw.rect(screen, color, (x-4, 305, 8, 14))
                pygame.draw.ellipse(screen, color, (x-20, 291, 40, 18))
            elif i == 1:
                pygame.draw.polygon(screen, color, [(x-15, 291), (x+15, 291), (x+12, 309), (x, 319), (x-12, 309)])
            else:
                pygame.draw.circle(screen, color, (x, 304), 15, 4)
            pygame.draw.rect(screen, (125, 108, 73), (x-19, 363, 38, 12))
        for i in game.save.cleared_regions:
            # Repaired courses and stocked supply bins stay behind the walking lane.
            left = 130 + i * 40 - camera.x
            for row in range(3):
                for column in range(3):
                    pygame.draw.rect(screen, (81, 78, 70), (left+column*12, 350+row*8, 10, 6))
            pygame.draw.rect(screen, (111, 80, 48), (220+i*28-camera.x, 520, 24, 28))
            pygame.draw.line(screen, (57, 43, 32), (220+i*28-camera.x, 521), (242+i*28-camera.x, 546), 2)
        if len(game.save.cleared_regions) == 4:
            glow = pygame.Surface((800, 600), pygame.SRCALPHA)
            glow.fill((173, 137, 77, 9))
            screen.blit(glow, (0, 0))
        for i,x in enumerate(GATES):
            status = 'CLEARED' if i in game.save.cleared_regions else 'READY' if game.save.gate_unlocked(i) else 'LOCKED'
            color = (190,173,105) if status=='CLEARED' else (135,190,148) if status=='READY' else (157,100,95)
            label = fonts['small'].render(f'{i+1}  {status}',True,color)
            screen.blit(label,(x-camera.x-label.get_width()//2,419))
            pygame.draw.circle(screen,color,(x-camera.x,401),5)
            if status == 'LOCKED':
                for offset in (-18, 0, 18):
                    pygame.draw.rect(screen, (86, 86, 89), (x-camera.x+offset, 480, 6, 80))
                pygame.draw.line(screen, color, (x-camera.x-28, 510), (x-camera.x+28, 540), 4)
            elif self.dialogue and self.dialogue.get('gate') == i:
                pygame.draw.rect(screen, (229, 207, 133), (x-camera.x-36, 475, 72, 85), 3)
                screen.blit(fonts['small'].render('READIED', True, (229,207,133)), (x-camera.x-38, 440))
        for x in (300,790,1260,1515,1760,1970):
            sx=x-camera.x
            glow=pygame.Surface((64,90),pygame.SRCALPHA)
            pygame.draw.ellipse(glow,(213,137,65,18),(0,0,64,90))
            screen.blit(glow,(sx-32,400))
            pygame.draw.rect(screen,(78,58,40),(sx-3,445,6,32))
            pygame.draw.polygon(screen,(230,147,58),[(sx-6,446),(sx+int(math.sin(self.ticks*.2+x)*3),430),(sx+6,446)])
        # Furnace flicker and a bounded handful of embers.
        flicker = 3 + (self.ticks//5)%3
        pygame.draw.rect(screen,(246,166,62),(392-camera.x,506,24,flicker*5))
        for i in range(5):
            phase=(self.ticks+i*11)%45
            pygame.draw.rect(screen,(211,129,54),(403-camera.x+i*5-phase//5,500-phase,2,2))
        for i in range(9):
            sx=510+(i%3)*8-camera.x+int(math.sin((self.ticks+i*13)*.03)*10)
            y=256-(self.ticks//2+i*17)%100
            pygame.draw.rect(screen,(87,85,82),(sx,y,8+i%3*2,6))
        for x in (90,590,1270,1745):
            sx=x-camera.x; sway=int(math.sin(self.ticks*.045+x)*4)
            pygame.draw.line(screen,(118,100,69),(sx,255),(sx,321),2)
            pygame.draw.polygon(screen,(115,52,60),[(sx+2,256),(sx+26+sway,259),(sx+24+sway,299),(sx+2,294)])
        for i in range(16):
            x=(i*151+self.ticks//8)%WIDTH-camera.x
            y=300+(i*37-self.ticks//4)%240
            pygame.draw.rect(screen,(120,111,91),(x,y,2,2))
        for i in range(4):
            x=1610+(i*23+self.ticks//3)%70-camera.x
            y=430+(i*17-self.ticks//5)%45
            pygame.draw.rect(screen,(149,127,182),(x,y,2,2))
        for i in range(3):
            x=(self.ticks//2+i*190)%WIDTH-camera.x
            y=110+i*19
            pygame.draw.lines(screen,(99,105,114),False,[(x-5,y),(x,y+2+(self.ticks//10)%2),(x+5,y)],2)

    def draw_foreground(self, screen, game):
        x = 28-game.camera.x
        pygame.draw.rect(screen,(58,42,31),(x,550,76,25))
        for wheel in (x+12,x+62):
            pygame.draw.circle(screen,(28,27,29),(wheel,574),12)
            pygame.draw.circle(screen,(113,82,48),(wheel,574),9,2)
        pygame.draw.line(screen,(108,77,44),(x+74,555),(x+108,542),4)
        for a in (4,25,47):
            pygame.draw.rect(screen,(112,80,46),(x+a,527,24,23))
            pygame.draw.line(screen,(55,40,30),(x+a,527),(x+a+23,549),2)

    def draw_overlay(self, screen, fonts, game):
        target = self.nearby(game.knight)
        if target and not self.dialogue:
            label = 'Enter Quartermaster storehouse' if target[0]=='door' else ADVENTURERS[target[1]]['name'] if target[0]=='adventurer' else ROLES[target[1]] if target[0]=='npc' else f'Expedition Gate {target[1]+1}'
            self.panel(screen,fonts,[label + '  [E]'],(155,365,490,36))
        self.panel(screen,fonts,['COURTYARD REFUGE', 'E: interact   F/R: practice   Esc: pause'],(180,12,440,58))
        if self.notice_timer:
            self.panel(screen,fonts,[self.notice],(30,90,740,38))
        if self.dialogue:
            lines = [self.dialogue['title']] + self.dialogue['lines'] + ['E / Enter: ' + ('depart or close' if 'gate' in self.dialogue else 'close') + '   Esc: close']
            self.panel(screen,fonts,lines,(30,135,740,28*len(lines)+18))

    def panel(self, screen, fonts, lines, rect):
        wrapped = []
        for line in lines:
            words = line.split()
            current = ''
            for word in words:
                candidate = (current + ' ' + word).strip()
                if fonts['small'].size(candidate)[0] > rect[2]-24 and current:
                    wrapped.append(current)
                    current = word
                else:
                    current = candidate
            wrapped.append(current)
        height = max(rect[3], 28*len(wrapped)+18)
        rect = (rect[0], min(rect[1], 560-height), rect[2], height)
        pygame.draw.rect(screen,(20,24,31),rect)
        pygame.draw.rect(screen,(116,103,78),rect,2)
        for i,line in enumerate(wrapped):
            screen.blit(fonts['small'].render(line,True,(224,211,184)),(rect[0]+12,rect[1]+9+i*28))
