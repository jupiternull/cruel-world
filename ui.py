import math
from pathlib import Path
import pygame
from config import ASSETS_DIR

IVORY = (230, 219, 184)
GOLD = (166, 133, 76)
CRIMSON = (113, 30, 39)
INK = (16, 18, 20)
FONT_ROOT = Path(ASSETS_DIR) / 'fonts'


def safe_font(path, size):
    try:
        return pygame.font.Font(str(path), size)
    except (OSError, pygame.error):
        return pygame.font.Font(None, size)


def init_fonts():
    heading = FONT_ROOT / 'medievalsharp/MedievalSharp-Regular.ttf'
    body = FONT_ROOT / 'pixeloperator/PixelOperator.ttf'
    return {'large': safe_font(heading, 40), 'medium': safe_font(heading, 28),
            'small': safe_font(body, 22), 'body': safe_font(body, 26),
            'tiny': safe_font(body, 18), 'logo': safe_font(heading, 76)}


def text(screen, font, words, center, color=IVORY):
    image = font.render(words, True, color)
    screen.blit(image, image.get_rect(center=center))


def rune(screen, x, y, color=GOLD, size=9):
    pygame.draw.lines(screen, color, False, [(x,y-size),(x-size//2,y),(x,y+size),(x+size//2,y),(x,y-size)], 1)
    pygame.draw.line(screen,color,(x-size,y),(x+size,y))


def panel(screen, rect, selected=False, wood=False):
    rect = pygame.Rect(rect)
    pygame.draw.rect(screen, (5,6,8), rect.move(3,5), border_radius=3)
    pygame.draw.rect(screen, (46,32,28) if wood else (30,32,33), rect, border_radius=3)
    # Fine horizontal grain and stone scoring stay behind opaque, high-contrast text.
    for y in range(rect.top+7,rect.bottom-5,9):
        pygame.draw.line(screen,(53,38,30) if wood else (35,37,37),(rect.left+5,y),(rect.right-5,y))
    pygame.draw.rect(screen,CRIMSON if selected else (71,66,53),rect,3)
    pygame.draw.rect(screen,GOLD if selected else (102,89,65),rect.inflate(-8,-8),1)
    for x in (rect.left+9,rect.right-10):
        for y in (rect.top+9,rect.bottom-10):
            pygame.draw.circle(screen,(10,12,13),(x,y),4)
            pygame.draw.circle(screen,GOLD,(x-1,y-1),2)
    length=18
    for x,d in ((rect.left,1),(rect.right-1,-1)):
        for y,e in ((rect.top,1),(rect.bottom-1,-1)):
            pygame.draw.lines(screen,GOLD,False,[(x,y+e*length),(x,y),(x+d*length,y)],2)


def separator(screen, y, left=190, right=610):
    pygame.draw.line(screen,(75,66,49),(left,y),(right,y))
    pygame.draw.line(screen,GOLD,(left+25,y+2),(right-25,y+2))
    rune(screen,(left+right)//2,y,IVORY,6)


def atmosphere(screen):
    shade = pygame.Surface((800,600),pygame.SRCALPHA)
    shade.fill((7,10,14,190))
    screen.blit(shade,(0,0))
    # Layered perimeter shading leaves the content brighter than the edges.
    vignette = pygame.Surface((800,600),pygame.SRCALPHA)
    for inset in range(0,110,5):
        pygame.draw.rect(vignette,(0,0,0,max(0,52-inset//3)),(inset,inset,800-inset*2,600-inset*2),5)
    screen.blit(vignette,(0,0))
    seconds=pygame.time.get_ticks()/1000
    for i in range(38):
        x=(i*137+math.sin(seconds*.3+i)*19)%800
        y=(i*79-seconds*(8+i%7))%600
        color=(149+i%60,75+i%35,43) if i%3 else (112,109,94)
        pygame.draw.circle(screen,color,(int(x),int(y)),1 if i%4 else 2)
    for x in (45,755):
        pygame.draw.line(screen,(65,57,44),(x,88),(x,510))
        for y in (105,495): rune(screen,x,y,size=12)


def make_logo(fonts):
    surface=pygame.Surface((680,160),pygame.SRCALPHA)
    font=fonts['logo']; words='CRUEL WORLD'
    face=font.render(words,True,IVORY)
    if face.get_width()>620:
        face=pygame.transform.smoothscale(face,(620,face.get_height()))
    rect=face.get_rect(center=(340,78))
    mask=pygame.mask.from_surface(face)
    solid=mask.to_surface(setcolor=(0,0,0,255),unsetcolor=(0,0,0,0))
    for dx,dy in ((-3,0),(3,0),(0,-3),(0,3)):
        surface.blit(solid,rect.move(dx,dy+5))
    back=mask.to_surface(setcolor=(94,28,35,255),unsetcolor=(0,0,0,0))
    for depth in range(8,0,-1): surface.blit(back,rect.move(0,depth))
    colored=pygame.Surface(face.get_size(),pygame.SRCALPHA)
    for y in range(face.get_height()):
        t=y/max(1,face.get_height()-1)
        c=(int(245-105*t),int(231-115*t),int(186-115*t))
        pygame.draw.line(colored,c,(0,y),(face.get_width(),y))
    alpha=mask.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0))
    colored.blit(alpha,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    cracks=pygame.Surface(face.get_size(),pygame.SRCALPHA)
    for x in range(23,face.get_width(),71):
        pygame.draw.lines(cracks,(41,35,30,210),False,[(x,12),(x-4,22),(x+2,29),(x-1,39)],1)
    cracks.blit(alpha,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(colored,rect);surface.blit(cracks,rect)
    # Original split crown and crossed blade ornament, kept subordinate to the name.
    pygame.draw.polygon(surface,GOLD,[(317,19),(312,5),(329,13),(340,0),(351,13),(368,5),(363,19)],2)
    pygame.draw.line(surface,CRIMSON,(110,133),(570,133),3)
    pygame.draw.line(surface,GOLD,(145,136),(655-145,136))
    for x in (304,376):
        pygame.draw.line(surface,IVORY,(x,145),(340,119),2)
        pygame.draw.line(surface,GOLD,(x-5,137),(x+5,149),3)
    rune(surface,340,133,IVORY,9)
    return surface


def logo(screen,fonts,center):
    try:
        emblem=pygame.image.load(str(Path(ASSETS_DIR)/'ui/cruel-world-logo.png')).convert_alpha()
    except (OSError,pygame.error):
        emblem=make_logo(fonts)
    screen.blit(emblem,emblem.get_rect(center=center))


def draw_banner(screen, fonts, words, y, size='medium'):
    if not words: return
    image=fonts[size].render(words,True,IVORY)
    rect=image.get_rect(center=(400,y))
    panel(screen,rect.inflate(40,14))
    screen.blit(image,rect)


def draw_menu(screen, fonts, title, subtitle, options, selected):
    atmosphere(screen)
    is_title=title=='CRUEL WORLD'
    if is_title:
        logo(screen,fonts,(400,145))
        text(screen,fonts['small'],'A CHRONICLE OF ASH & IRON',(400,242),GOLD)
    else:
        panel(screen,(128,78,544,430))
        text(screen,fonts['tiny'],'C R U E L   W O R L D',(400,108),GOLD)
        text(screen,fonts['large'],title,(400,160))
        separator(screen,192)
    text(screen,fonts['small'],subtitle,(400,277 if is_title else 222))
    for i,option in enumerate(options):
        y=(320 if is_title else 260)+i*52
        active=i==selected
        panel(screen,(205,y,390,44),active,wood=True)
        if active:
            pygame.draw.polygon(screen,IVORY,[(224,y+15),(232,y+22),(224,y+29)])
            rune(screen,574,y+22,IVORY,6)
        text(screen,fonts['body'],option,(400,y+22),IVORY if active else (180,172,148))
    separator(screen,520)
    text(screen,fonts['small'],'Up / Down: select    Enter: choose    Esc: back',(400,548))
    text(screen,fonts['tiny'],'Left / Right: adjust settings   |   F: attack   E: ability   Shift / Q: evade',(400,577),GOLD)


def draw_class_selection(screen, fonts, heroes, selected):
    from entities.hero import CLASSES
    atmosphere(screen)
    text(screen,fonts['tiny'],'C R U E L   W O R L D',(400,27),GOLD)
    text(screen,fonts['large'],'Choose your oath',(400,66))
    text(screen,fonts['small'],'Three realms await. Carry steel, bow, or flame into the dark.',(400,108))
    for index,(name,stats) in enumerate(CLASSES.items()):
        rect=pygame.Rect(25+index*253,140,244,365)
        active=index==selected
        panel(screen,rect,active)
        text(screen,fonts['tiny'],f'0{index+1}   /   '+('THE VANGUARD' if index==0 else 'THE WAYFARER' if index==1 else 'THE ARCANIST'),(rect.centerx,163),GOLD)
        # Every portrait is a runtime manifest frame, uniformly fitted to its own stage.
        frame=heroes[name]['Idle'][(pygame.time.get_ticks()//180)%len(heroes[name]['Idle'])]
        bounds=frame.get_bounding_rect();portrait=frame.subsurface(bounds)
        scale=min(150/portrait.get_width(),134/portrait.get_height())
        portrait=pygame.transform.scale(portrait,(int(portrait.get_width()*scale),int(portrait.get_height()*scale)))
        pygame.draw.ellipse(screen,(13,14,15),(rect.centerx-65,313,130,16))
        screen.blit(portrait,portrait.get_rect(midbottom=(rect.centerx,324)))
        text(screen,fonts['medium'],stats['name'],(rect.centerx,349),IVORY if active else GOLD)
        roles={'warrior':('Hold the line.','Chain three crushing strikes.'),
               'ranger':('Strike from the treeline.','Loose arrows & piercing volleys.'),
               'wizard':('Command the forbidden.','Burn foes with arcane flame.')}
        for i,line in enumerate(roles[name]): text(screen,fonts['tiny'],line,(rect.centerx,379+i*20))
        for j,(label,value) in enumerate((('VITALITY',stats['health']/150),('MOBILITY',stats['speed']/6),('POWER',stats['damage']/26))):
            y=423+j*22
            screen.blit(fonts['tiny'].render(label,True,GOLD),(rect.left+17,y-3))
            for k in range(8):
                pygame.draw.rect(screen,stats['color'] if k<round(value*8) else (56,55,48),(rect.left+111+k*13,y,10,8))
        if active: text(screen,fonts['tiny'],'[ ENTER TO SWEAR THE OATH ]',(rect.centerx,487),IVORY)
    text(screen,fonts['small'],'Arrow keys: choose    Enter: begin    Esc: back',(400,540))
    text(screen,fonts['tiny'],'F: primary   E: secondary   Shift / Q: defensive mobility',(400,571),GOLD)


def bar(screen,rect,fraction,color):
    rect=pygame.Rect(rect)
    pygame.draw.rect(screen,(8,9,10),rect)
    fill=rect.inflate(-4,-4);fill.width=int(fill.width*max(0,min(1,fraction)))
    pygame.draw.rect(screen,color,fill)
    pygame.draw.line(screen,IVORY,fill.topleft,fill.topright)
    pygame.draw.rect(screen,GOLD,rect,1)


def draw_ui(screen, fonts, knight, game_state):
    panel(screen,(8,8,254,112))
    screen.blit(fonts['small'].render(f"{knight.stats['name']}  {knight.health}/{knight.max_health}",True,IVORY),(20,15))
    bar(screen,(20,40,229,13),knight.health/knight.max_health,(151,44,49))
    screen.blit(fonts['tiny'].render(f'Score {game_state.score}   Wave {game_state.wave}/3',True,GOLD),(20,58))
    for y,label,timer,total in ((79,knight.stats['secondary'],knight.secondary_cooldown,knight.stats['cooldown']),
                               (98,'Blink' if knight.class_id=='wizard' else 'Evade' if knight.class_id=='ranger' else 'Dodge',knight.dash_cooldown,150 if knight.class_id=='wizard' else 90)):
        screen.blit(fonts['tiny'].render(label+': '+('READY' if not timer else f'{timer/60:.1f}s'),True,IVORY),(20,y-3))
        bar(screen,(195,y,54,8),1-timer/total,knight.stats['color'])
    pygame.draw.rect(screen,INK,(0,574,800,26))
    pygame.draw.line(screen,GOLD,(0,574),(800,574))
    text(screen,fonts['tiny'],knight.stats['hint']+'   |   Esc: pause',(400,587))
    if game_state.phase=='travel':
        draw_banner(screen,fonts,'A/D: move   Space: jump   W/S: climb   S+Space: drop',552,'tiny')
