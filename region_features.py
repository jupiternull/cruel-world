"""Authored expedition objects; simulation uses ticks and no global randomness."""
import math
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parent / 'assets/regions'
SUBAREAS = {'forest': ('Ruined approach', 'Flooded grove', 'Overgrown sanctuary'),
            'cave': ('Collapsed entry halls', 'Prison / cistern', 'Sealed armory'),
            'graveyard': ('Outer cemetery', 'Mausoleum row', 'Moonlit crypt')}
DESCRIPTIONS = {
    'cache': 'A soaked survey: shallow pools slow steps; the high ledges stay dry.',
    'ledger': 'An unsigned ledger counts empty cells. The last page is missing.',
    'record': 'The stone speaks of a return. Whose return, the worn lines never say.',
    'sanctuary': 'Roots hold the broken gate together. The silent figure watches the grove.',
    'armory': 'Weapon slots stand empty beneath a seat sealed behind iron.',
    'monument': 'A bell without a rope. Pale light gathers at the closed threshold.'}


class Breakable:
    def __init__(self, kind, x, health=18):
        self.kind = kind
        self.rect = pygame.Rect(x, 500 if kind == 'vine' else 512, 40, 60 if kind == 'vine' else 48)
        self.health = health
        self.alive = True
        self.hit_flash = 0
        self.broken_ticks = 0
        self.rewarded = False

    def _col_rect(self):
        return self.rect

    def take_damage(self, damage, source=None):
        self.health = max(0, self.health - damage)
        self.alive = self.health > 0
        self.hit_flash = 12


class RegionFeatures:
    def __init__(self, world, assets):
        self.world = world
        self.kind = world.data['id']
        self.ticks = 0
        self.notice = ''
        self.notice_timer = 0
        self.claimed = set()
        self.lit = set()
        self.gate_tick = 0
        self.gate_open = False
        self.statue_glow = 0
        self.statue_cooldown = 0
        self.visited = set()
        self.water = [pygame.Rect(1280, 548, 400, 12), pygame.Rect(1920, 548, 360, 12)] if self.kind == 'forest' else []
        self.gate = pygame.Rect(1824, 0, 128, 560) if self.kind == 'cave' else None
        self.objects = ({'cache': (840, 'Search abandoned cache'), 'sanctuary': (2840, 'Observe sanctuary gate')} if self.kind == 'forest' else
                        {'lever': (1776, 'Raise cistern bars'), 'ledger': (1380, 'Read prisoner ledger'), 'armory': (3100, 'Inspect sealed armory')} if self.kind == 'cave' else
                        {'brazier0': (660, 'Light grave lantern'), 'brazier1': (1860, 'Light grave lantern'),
                         'brazier2': (2970, 'Light grave lantern'), 'record': (2370, 'Read crypt record'), 'monument': (3300, 'Observe bell monument')})
        self.breakables = [Breakable(kind, x, hp) for kind,x,hp in
                          ([('vine',1180,18),('vine',2350,18),('urn',640,18)] if self.kind == 'forest' else
                           [('pot',680,18),('pot',1500,18),('cupboard',2440,30)] if self.kind == 'cave' else
                           [('urn',960,18),('urn',2170,18),('urn',3070,18)])]
        self.scenes = [pygame.transform.scale(pygame.image.load(str(ROOT/f'{self.kind}-{i}.png')).convert_alpha(),(1200,440)) for i in range(3)]
        self.frames = {}
        counts = {'water':6,'falls':6} if self.kind == 'forest' else {'cell':8,'statue':6,'pot':4,'window':1,'skeleton':1,'cupboard':1} if self.kind == 'cave' else {}
        for name,count in counts.items():
            sheet=pygame.image.load(str(ROOT/(name+'.png'))).convert_alpha()
            w=sheet.get_width()//count;h=sheet.get_height()
            self.frames[name]=[pygame.transform.scale(sheet.subsurface((i*w,0,w,h)),(w*2,h*2)) for i in range(count)]
        self.moon_fence = None
        if self.kind == 'graveyard':
            self.moon_fence = pygame.transform.scale(assets['moon_tiles'].subsurface((0,240,64,80)),(128,160))
        world.features = self

    def retry(self, checkpoint):
        # Keep claims for this expedition: dying must never farm discoveries or props.
        self.ticks = 0
        self.notice_timer = 0
        self.statue_glow = self.statue_cooldown = 0
        self.gate_open = bool(self.gate and checkpoint >= self.gate.right)
        self.gate_tick = 48 if self.gate_open else 0
        if not self.gate_open:
            self.claimed.discard('lever')
        for prop in self.breakables:
            prop.hit_flash = prop.broken_ticks = 0
            prop.alive = not prop.rewarded
            prop.health = 30 if prop.kind == 'cupboard' else 18

    def movement_factor(self, actor):
        if actor.on_ground and actor.rect.bottom == 560 and any(actor.rect.colliderect(zone) for zone in self.water):
            return 0.75
        return 1

    def blockers(self):
        result = [prop.rect for prop in self.breakables if prop.alive and prop.kind == 'vine']
        if self.gate and not self.gate_open:
            result.append(self.gate)
        return result

    def nearby(self, hero):
        if not hero.alive:
            return None
        candidates = [(abs(hero.rect.centerx-x),name) for name,(x,_) in self.objects.items()
                      if abs(hero.rect.centerx-x)<=70 and hero.rect.bottom>=480 and name not in self.claimed]
        return min(candidates)[1] if candidates else None

    def reward(self, game, name, score, heal):
        if name in self.claimed:
            return False
        self.claimed.add(name)
        game.state.add_score(game.expedition.discovery_score(score) if hasattr(game, 'expedition') else score)
        game.knight.heal(heal)
        return True

    def interact(self, game):
        name = self.nearby(game.knight)
        if name is None:
            return False
        if name == 'lever':
            self.claimed.add(name)
            self.gate_tick = max(1,self.gate_tick)
            self.notice = 'Cistern bars rising. The ground route opens.'
            game.audio.play('door_open')
        elif name.startswith('brazier'):
            self.claimed.add(name)
            self.lit.add(name)
            self.notice = f'Grave lantern lit ({len(self.lit)}/3).'
            if len(self.lit)==3 and self.reward(game,'lanterns',180,18):
                self.notice = 'Three lights answer the bell. The threshold glows. +180 / heal 18'
            game.audio.play('pickup')
        else:
            self.reward(game,name,60 if name in ('sanctuary','armory','monument') else 120,0 if name in ('sanctuary','armory','monument') else 12)
            self.notice = DESCRIPTIONS[name]
            game.audio.play('chest_open')
        self.notice_timer = 270
        return True

    def update(self, game):
        self.ticks += 1
        self.notice_timer = max(0,self.notice_timer-1)
        self.statue_glow = max(0,self.statue_glow-1)
        self.statue_cooldown = max(0,self.statue_cooldown-1)
        if self.gate_tick and not self.gate_open:
            self.gate_tick += 1
            if self.gate_tick >= 48:
                self.gate_open=True
                game.audio.play('door_open')
        if self.kind=='cave' and abs(game.knight.rect.centerx-2630)<120 and not self.statue_cooldown:
            self.statue_glow=90
            self.statue_cooldown=360
        for prop in self.breakables:
            prop.hit_flash=max(0,prop.hit_flash-1)
            if not prop.alive:
                prop.broken_ticks=min(90,prop.broken_ticks+1)
                if not prop.rewarded:
                    prop.rewarded=True
                    game.state.add_score(25)
                    game.knight.heal(3)
                    game.audio.play('sword_hit')
        area = min(2,game.knight.rect.centerx//(self.world.width//3))
        if area not in self.visited:
            self.visited.add(area)
            if not self.notice_timer:
                self.notice=SUBAREAS[self.kind][area]
                self.notice_timer=150

    def hit(self, source):
        if source.team=='hero':
            for prop in self.breakables:
                source.hit(prop)

    def draw_background(self, screen, camera):
        starts = (0, self.world.width//3, self.world.width*2//3)
        for i,x in enumerate(starts):
            screen.blit(self.scenes[i],(x-camera.x,120))
        if self.kind=='forest':
            for x in (1380,2130):
                screen.blit(self.frames['falls'][(self.ticks//8)%6],(x-camera.x,304))
        elif self.kind=='cave':
            for x in (1190,1530,2110):
                screen.blit(self.frames['window'][0],(x-camera.x,292))
            screen.blit(self.frames['skeleton'][0],(1440-camera.x,352))
            screen.blit(self.frames['statue'][(self.ticks//15)%6 if self.statue_glow else 0],(2600-camera.x,368))
            if self.statue_glow:
                pygame.draw.circle(screen,(174,184,175),(2630-camera.x,396),7,2)
            # A full-height pier prevents jumping around the required bars.
            pygame.draw.rect(screen,(49,48,59),(1824-camera.x,0,128,368))
            for y in range(16,360,32):
                pygame.draw.line(screen,(26,28,38),(1824-camera.x,y),(1951-camera.x,y),2)
                for x in range(1824+(16 if y%64 else 0),1952,32):
                    pygame.draw.line(screen,(76,73,82),(x-camera.x,y+2),(x-camera.x,y+30),1)
            pygame.draw.rect(screen,(111,104,97),(1824-camera.x,360,128,8))
            screen.blit(self.frames['cell'][min(7,self.gate_tick//6)],(1824-camera.x,368))
        elif self.kind=='graveyard':
            for x in (180,380,1060,1600,2100,2780,3160,3860):
                screen.blit(self.moon_fence,(x-camera.x,400))
            beams=pygame.Surface((800,600),pygame.SRCALPHA)
            for x in (170,540):
                sx=x-int(camera.x*.12)%240
                pygame.draw.polygon(beams,(149,178,213,12),[(sx,50),(sx+30,50),(sx+195,560),(sx+80,560)])
            screen.blit(beams,(0,0))
            if len(self.lit)==3:
                pygame.draw.rect(screen,(161,218,205),(self.world.width*2//3+518-camera.x,392,164,166),3)

    def draw_objects(self,screen,camera):
        for prop in self.breakables:
            r=camera.rect(prop.rect)
            if not prop.alive and prop.broken_ticks>=90:
                pygame.draw.line(screen,(76,82,72),r.bottomleft,r.bottomright,2)
                continue
            color=(196,214,146) if prop.hit_flash else (82,118,64) if self.kind=='forest' else (128,136,158)
            if prop.kind=='vine':
                for j in range(4):
                    x=r.x+j*10
                    if prop.alive:
                        pygame.draw.lines(screen,color,False,[(x,r.bottom),(x+6,r.top+12),(x-3,r.top)],4)
                        for y in range(r.top+8,r.bottom,14):pygame.draw.polygon(screen,color,[(x,y),(x-8,y-5),(x+2,y+6)])
                    else:
                        pygame.draw.line(screen,color,(x,r.bottom),(x+8,r.bottom-8),3)
            elif prop.kind in self.frames:
                frame=self.frames[prop.kind][0 if prop.alive else min(len(self.frames[prop.kind])-1,1+prop.broken_ticks//6)]
                if prop.hit_flash:frame=frame.copy();frame.fill((50,50,40,0),special_flags=pygame.BLEND_RGBA_ADD)
                screen.blit(frame,(r.centerx-frame.get_width()//2,r.bottom-frame.get_height()))
            else:
                if prop.alive:
                    pygame.draw.ellipse(screen,color,r.inflate(-10,-8));pygame.draw.rect(screen,(46,51,67),(r.x+8,r.y+6,24,6));pygame.draw.line(screen,(65,70,84),(r.centerx,r.y+14),(r.centerx+4,r.bottom-9),2)
                else:
                    for j in range(4):pygame.draw.polygon(screen,color,[(r.x+j*10,r.bottom),(r.x+j*10+6,r.bottom-9),(r.x+j*10+9,r.bottom)])
        for name,(x,_) in self.objects.items():
            sx=x-camera.x
            if name.startswith('brazier'):
                pygame.draw.rect(screen,(96,105,131),(sx-8,532,16,28));pygame.draw.ellipse(screen,(132,150,165),(sx-15,522,30,12))
                if name in self.lit:
                    pygame.draw.circle(screen,(121,217,200),(sx,516),9+self.ticks%3)
                    pygame.draw.circle(screen,(218,242,205),(sx,513),4)
            elif name=='lever':
                pygame.draw.rect(screen,(126,116,91),(sx-10,533,20,27));pygame.draw.line(screen,(220,181,103),(sx,539),(sx+(14 if self.gate_tick else -14),515),4)
            elif name in ('cache','ledger','record'):
                pygame.draw.rect(screen,(105,97,76) if self.kind=='forest' else (105,107,128),(sx-18,531,36,29),border_radius=2)
                pygame.draw.line(screen,(189,181,137),(sx-14,539),(sx+14,539),2)
                if name not in self.claimed:pygame.draw.circle(screen,(194,213,161),(sx,521),3)

    def draw_foreground(self,screen,camera):
        layer=pygame.Surface((800,600),pygame.SRCALPHA)
        if self.kind=='forest':
            frame=self.frames['water'][(self.ticks//8)%6]
            for zone in self.water:
                for x in range(zone.x,zone.right,64):
                    layer.blit(frame,(x-camera.x,548),(0,0,min(64,zone.right-x),12))
                for j in range(8):
                    x=zone.x+(j*47+self.ticks//3)%zone.width-camera.x
                    pygame.draw.line(layer,(153,202,172,120),(x,554),(x+11,554),1)
            for x in (1380,2130):
                for j in range(12):
                    phase=(self.ticks+j*7)%55
                    pygame.draw.circle(layer,(173,210,181,70),(x-camera.x+32+(j%3-1)*12,548-phase//4),2)
        elif self.kind=='cave':
            for x,w in ((1550,130),(1990,220),(2260,90)):
                pygame.draw.ellipse(layer,(77,113,125,75),(x-camera.x,554,w,5))
                for j in range(4):
                    sx=x+(self.ticks//3+j*31)%w-camera.x
                    pygame.draw.line(layer,(140,172,175,65),(sx,556),(sx+12,556),1)
        elif self.kind=='graveyard':
            for j in range(14):
                x=(j*83+self.ticks//3-int(camera.x*.8))%1000-100
                y=549+int(math.sin((self.ticks+j*23)/90)*5)
                pygame.draw.ellipse(layer,(139,159,193,16),(x,y,145,20))
        for j in range(22):
            x=(j*193+self.ticks//(8 if self.kind=='forest' else 12)-camera.x)%self.world.width
            y=230+(j*67)%300+int(math.sin((self.ticks+j*17)/50)*8)
            if self.kind=='forest':
                pygame.draw.circle(layer,(189,216,113,90),(x,y),2)
                if j<3:
                    pygame.draw.lines(layer,(79,106,78,180),False,[(x-5,y),(x,y+int(math.sin(self.ticks/9)*3)),(x+5,y)],1)
            elif self.kind=='cave':
                pygame.draw.line(layer,(108,152,164,100),(x,y),(x,y+4),1)
                if j<4:
                    rx=(j*811+self.ticks*2-camera.x)%self.world.width
                    pygame.draw.ellipse(layer,(88,79,79,230),(rx,553,13,6));pygame.draw.line(layer,(116,99,97,180),(rx,556),(rx-9,554),1)
            else:pygame.draw.circle(layer,(159,179,209,70),(x,y),1)
        screen.blit(layer,(0,0))

    def draw_overlay(self,game):
        from ui import draw_banner
        name=self.nearby(game.knight)
        if name:
            draw_banner(game.screen,game.fonts,'E - '+self.objects[name][1],465,'small')
        if self.notice_timer:
            draw_banner(game.screen,game.fonts,self.notice,185,'small')
