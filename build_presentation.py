"""Rebuild curated hero derivatives and the original transparent title emblem."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame
from pathlib import Path


# Pose landmarks use the source's 200px canvas and 122px ground line. Every visible
# pixel is original geometry; source frames provide animation dimensions only.
RANGER_POSES = {
    'Idle': [(96,y,0) for y in (79,80,81,81,82,81,80,79)],
    'Run': [(99,y,0) for y in (83,84,84,83,83,84,83,83)],
    'Jump': [(97,78,0),(98,78,0)],
    'Fall': [(98,79,0),(97,77,0)],
    'Attack1': [(96,79,0),(96,79,0),(95,80,0),(96,80,0),(96,79,0)],
    'Attack2': [(96,80,0),(96,80,0),(95,81,0),(96,81,0),(96,80,0)],
    'Attack3': [(96,79,0),(96,79,0),(95,80,0),(95,80,0),(96,80,0),(96,79,0),(96,79,0)],
    'Hit': [(96,79,0),(89,78,0),(92,79,0)],
    'Death': [(92,79,0),(91,82,0),(92,86,0),(94,92,-15),
              (99,100,-35),(105,109,-75),(105,109,-75),(105,109,-75)],
}
RANGER_COLORS = {
    'outline': (19,25,22), 'hood': (28,57,36), 'fold': (46,78,46),
    'green': (65,88,49), 'shadow': (10,19,17), 'face': (158,137,104),
    'leather': (91,59,34), 'edge': (133,91,48), 'legs': (29,32,30),
    'bow': (179,130,65), 'string': (215,209,173),
}


def ranger_assets(output=None):
    from config import ASSETS_DIR
    source = Path(ASSETS_DIR)/'heroes/ranger_source/Martial Hero/Sprites'
    output = Path(output) if output else Path(ASSETS_DIR)/'heroes/ranger'
    output.mkdir(parents=True, exist_ok=True)
    c = RANGER_COLORS
    for name, poses in RANGER_POSES.items():
        original = 'Idle' if name.startswith('Attack') else 'Take Hit' if name == 'Hit' else name
        sheet = pygame.image.load(str(source/(original+'.png')))
        if sheet.get_height() != 200 or sheet.get_width() % 200:
            raise ValueError(f'{original}: invalid source canvas')
        result = pygame.Surface((200*len(poses),200),pygame.SRCALPHA)
        for i,(cx,cy,angle) in enumerate(poses):
            frame = pygame.Surface((200,200),pygame.SRCALPHA)
            # Draw locally around the neck, then place the complete attached equipment
            # assembly at its frame landmark. Fallen poses rotate the whole upper body.
            upper = pygame.Surface((80,80),pygame.SRCALPHA)
            def poly(color, points):
                pygame.draw.polygon(upper,c[color],[(round(x*0.85)+35,round(y*0.85)+25) if head else (x+35,y+25) for x,y in points])
            def line(color, points, width=1):
                pygame.draw.lines(upper,c[color],False,[(round(x*0.85)+35,round(y*0.85)+25) if head else (x+35,y+25) for x,y in points],width)
            head = False
            # Narrow split tails and a slim quiver behind the far shoulder.
            trail = -3 if name in ('Run','Jump','Fall') else 0
            poly('outline',[(-7,7),(-8+trail,28),(-4,25),(0,27),(3,8)])
            poly('hood',[(-6,8),(-6+trail,25),(-4,23),(0,25),(2,9)])
            poly('outline',[(-17,0),(-13,1),(-15,22),(-19,20)])
            poly('leather',[(-16,2),(-14,3),(-16,20),(-18,19)])
            line('edge',[(-16,4),(-18,18)])
            for dx in (-18,-16,-14):
                line('edge',[(dx,-10),(dx-2,5)])
                line('string',[(dx-1,-10),(dx+1,-8)])
            # Athletic shoulders taper into a fitted waist and full hips.
            poly('outline',[(-11,5),(10,5),(9,12),(6,22),(7,26),(-8,26),(-7,22),(-10,12)])
            poly('green',[(-10,6),(9,6),(8,12),(5,22),(6,25),(-7,25),(-6,22),(-9,12)])
            poly('leather',[(-8,8),(7,8),(6,14),(5,20),(-6,20),(-7,14)])
            line('edge',[(-4,9),(-3,17)])
            line('leather',[(-7,22),(6,22)],2)
            line('edge',[(0,21),(2,21),(2,23),(0,23),(0,21)])
            # Reduce the hood around the neck without moving the pose landmark.
            head = True
            poly('outline',[(-9,-14),(-3,-11),(3,-10),(8,-7),(10,0),(6,5),(-4,5),(-7,0)])
            poly('hood',[(-8,-13),(-2,-9),(2,-8),(6,-6),(8,0),(5,4),(-3,3),(-5,-1)])
            line('fold',[(-6,-10),(-2,-7),(2,-7),(5,-5)])
            poly('shadow',[(2,-7),(6,-5),(8,0),(5,3),(0,2),(0,-3)])
            poly('face',[(7,-1),(9,0),(7,1),(6,3),(3,3),(2,2),(6,2)])
            poly('outline',[(-5,3),(0,5),(5,3),(6,7),(2,9),(-3,7),(-6,7)])
            poly('hood',[(-4,4),(0,6),(4,4),(5,6),(2,7),(-3,6)])
            line('fold',[(-3,5),(0,7),(3,6)])
            head = False
            # Hands and forearms meet the bow grip and drawn string.
            attacking = name.startswith('Attack')
            drawn = attacking and i < 2  # projectile emission tick 9 enters frame 2
            bx, by = 20, 15
            pull = 5 if drawn else bx
            line('outline',[(8,9),(12,13),(bx,by)],5)
            line('green',[(8,9),(12,13),(bx,by)],3)
            line('leather',[(13,13),(19,15)],3)
            line('face',[(20,14),(20,16)],2)
            if attacking:
                line('outline',[(-9,9),(-12,16),(pull,by)],5)
                line('green',[(-9,9),(-12,16),(pull,by)],3)
                line('leather',[(-10,16),(pull,by)],3)
                line('face',[(pull,by),(pull+1,by)],2)
            else:
                line('outline',[(-10,9),(-13,18),(-11,25)],5)
                line('green',[(-10,9),(-13,18)],3)
                line('leather',[(-13,19),(-11,25)],3)
            bow_bottom=min(38,120-cy)
            line('outline',[(bx,-8),(bx+6,0),(bx+9,by),(bx+6,bow_bottom-8),(bx,bow_bottom)],3)
            line('bow',[(bx,-8),(bx+5,0),(bx+8,by),(bx+5,bow_bottom-8),(bx,bow_bottom)],2)
            line('string',[(bx,-8),(pull,by),(bx,bow_bottom)])
            if drawn:
                line('edge',[(pull-3,by),(bx+21,by)])
                line('string',[(pull-3,by-2),(pull,by),(pull-3,by+2)])
                poly('string',[(bx+23,by),(bx+18,by-2),(bx+18,by+2)])
            # Two separate trousered legs replace the source's robe silhouette.
            feet = ((-9,121),(8,121))
            if name == 'Run':
                feet = (((-16,119),(14,121)),((-10,120),(10,121)),
                        ((0,121),(4,115)),((12,121),(-9,116)),
                        ((15,121),(-15,120)),((9,121),(-9,120)),
                        ((0,116),(-4,121)),((-10,116),(10,121)))[i]
            elif name in ('Jump','Fall'):
                feet = ((-11,119),(7,115)) if name=='Jump' else ((-6,121),(9,119))
            if name=='Death' and i>=3:
                feet=((-14,121),(-3,121))
            hip_y = min(116,cy+23)
            for side,(fx,fy) in zip((-5,5),feet):
                foot_x=cx+fx
                pygame.draw.lines(frame,c['outline'],False,[(cx+side,hip_y),(foot_x,fy-6),(foot_x,fy)],7)
                pygame.draw.lines(frame,c['legs'],False,[(cx+side,hip_y),(foot_x,fy-6)],5)
                pygame.draw.line(frame,c['leather'],(foot_x,fy-6),(foot_x,fy),5)
                pygame.draw.line(frame,c['edge'],(foot_x-2,fy),(foot_x+4,fy),2)
            if angle:
                upper=pygame.transform.rotate(upper,angle)
                frame.blit(upper,upper.get_rect(center=(cx+5,cy+15)))
            else:
                frame.blit(upper,(cx-35,cy-25))
            if name == 'Death' and i >= 3:
                # Keep the fallen assembly on the original ground/anchor line.
                bottom=frame.get_bounding_rect().bottom
                grounded=pygame.Surface((200,200),pygame.SRCALPHA)
                grounded.blit(frame,(0,122-bottom))
                frame=grounded
            result.blit(frame,(i*200,0))
        pygame.image.save(result,str(output/(name+'.png')))


# Head centers are curated in source pixels, including tucked, inverted and fallen poses.
KNIGHT_HEADS = {
    'Idle': [(50,17),(49,17),(48,18),(48,18),(49,17),(50,17),(51,18),(51,18)],
    'Run': [(50,y) for y in (18,17,17,16,17,18,17,17,16,17)],
    'Attack1': [(52,17),(55,17),(58,19),(58,17),(59,19),(58,18)],
    'Attack2': [(51,18),(50,25),(50,25),(50,25),(50,23),(49,23)],
    'Attack3': [(52,19),(55,17),(59,23),(59,24),(59,24),(58,24),(52,22),(50,18)],
    'Jump': [(51,19),(51,17),(51,17)],
    'Fall': [(51,16)]*4,
    'Hit': [(50,17),(46,18),(48,18)],
    'Death': [(50,17),(46,18),(48,18),(50,18),(54,27),(55,28),(60,31),(77,50),(77,50),(77,50)],
    'Roll': [(55,24),(62,41),(59,48),(52,47),(46,44),(48,37),(52,31),(54,31),(51,19)],
    'Block': [(51,21),(47,18),(49,19),(49,19),(50,19)],
    'BlockIdle': [(51,y) for y in (19,19,18,18,18,18,19,19)],
    'WallSlide': [(55,18)]*5,
    'LedgeGrab': [(51,15),(52,16),(55,17),(56,18),(56,18)],
}


def knight_assets(output=None):
    from assets import KNIGHT_SOURCE_ROOT, KNIGHT_ANIMATIONS
    from config import ASSETS_DIR
    output = Path(output) if output else Path(ASSETS_DIR)/'heroes/knight'
    output.mkdir(parents=True, exist_ok=True)
    # Original closed iron helm: asymmetric brow, slit, cheek plates and worn ridge.
    pixels = (
        '  ssss   ', ' sggggs  ', 'sggggggs ', 'sggddddss',
        'sddddddds', 'sgdvvvvvs', 'sggddsggs', ' sgdssgs ',
        ' sggdsgs ', '  ssss   ',
    )
    colors = {'s':(108,111,112), 'g':(48,53,59), 'd':(27,30,35), 'v':(8,9,12)}
    helm = pygame.Surface((9,10),pygame.SRCALPHA)
    for y,row in enumerate(pixels):
        for x,c in enumerate(row):
            if c in colors: helm.set_at((x,y),colors[c])
    helm.set_at((7,6),(119,46,35))
    palette = {(43,72,141):(48,53,59), (4,38,86):(27,30,35),
               (179,184,212):(155,156,151), (126,128,143):(92,96,99),
               (156,0,0):(91,25,30), (105,0,26):(51,20,26),
               (97,51,11):(64,62,60), (116,71,26):(94,92,85),
               (50,30,15):(31,29,28)}
    sheet = pygame.Surface((1000,len(KNIGHT_ANIMATIONS)*132),pygame.SRCALPHA)
    sheet.fill((16,18,22))
    font=pygame.font.Font(str(Path(ASSETS_DIR)/'fonts/pixeloperator/PixelOperator.ttf'),18)
    for row,(state,(folder,count)) in enumerate(KNIGHT_ANIMATIONS.items()):
        paths=sorted((Path(ASSETS_DIR)/KNIGHT_SOURCE_ROOT/folder).glob('*.png'),
                     key=lambda p:int(p.stem.rsplit('_',1)[1]))
        if len(paths)!=count or len(KNIGHT_HEADS[state])!=count:
            raise ValueError(f'{state}: invalid source or head manifest')
        destination=output/folder
        destination.mkdir(exist_ok=True)
        for i,path in enumerate(paths):
            frame=pygame.image.load(str(path)).convert_alpha()
            for x in range(100):
                for y in range(55):
                    c=frame.get_at((x,y))
                    if c.a and tuple(c)[:3] in palette:
                        frame.set_at((x,y),(*palette[tuple(c)[:3]],c.a))
            angle = (0,-90,180,180,90,0,0,0,0)[i] if state=='Roll' else -90 if state=='Death' and i>=7 else 0
            helmet=pygame.transform.rotate(helm,angle)
            center=KNIGHT_HEADS[state][i]
            rect=helmet.get_rect(center=center)
            # Remove source face/hair only within the curated head region; retain cape and limbs.
            for x in range(max(0,rect.left-1),min(100,rect.right+1)):
                for y in range(max(0,rect.top-1),min(55,rect.bottom+1)):
                    c=tuple(frame.get_at((x,y)))[:3]
                    if c in ((239,206,164),(203,136,94),(166,103,32),(128,81,37),(31,29,28)):
                        frame.set_at((x,y),(0,0,0,0))
            frame.blit(helmet,rect)
            pygame.image.save(frame,str(destination/path.name))
            sheet.blit(pygame.transform.scale(frame,(100,110)),(i*100,row*132+20))
            sheet.blit(font.render(f'{state} {i}',True,(210,205,190)),(i*100,row*132))
    pygame.image.save(sheet,str(output/'animation-contact-sheet.png'))


def main():
    pygame.init();pygame.display.set_mode((1,1))
    ranger_assets()
    knight_assets()
    from ui import make_logo,init_fonts
    Path('assets/ui').mkdir(exist_ok=True)
    pygame.image.save(make_logo(init_fonts()),'assets/ui/cruel-world-logo.png')
    pygame.quit()

if __name__ == '__main__': main()
