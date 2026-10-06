"""Deterministic original regional scenery and curated, embedded runtime derivatives.

Original art needs only Pillow. --sources points to the inspected external extraction;
without it the retained derivative strips are verified and reused, never fetched.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets/regions'
PALETTES = {'forest': [(24, 40, 37), (45, 67, 54), (73, 96, 67), (117, 139, 92), (169, 191, 133)],
            'cave': [(23, 24, 34), (47, 48, 60), (76, 76, 84), (122, 119, 111), (188, 168, 118)],
            'graveyard': [(20, 25, 43), (44, 49, 69), (76, 82, 105), (124, 133, 153), (185, 202, 205)]}


def adapt(image, palette):
    image = image.convert('RGBA')
    result = Image.new('RGBA', image.size)
    result.putdata([(*palette[min(4, (r*3+g*6+b)//512)], a) if a else (0, 0, 0, 0)
                    for r, g, b, a in image.getdata()])
    return result


def derivatives(sources):
    spec = [('water', 'GandalfHardcore Animated Water Tiles.png', [(i*32, 64, i*32+32, 96) for i in range(6)], 'forest'),
            ('falls', 'GandalfHardcore Animated Water Tiles.png', [(i*32, 96, i*32+32, 224) for i in range(6)], 'forest'),
            ('cell', 'cell_door_frames.png', [(i*64, 0, i*64+64, 96) for i in range(8)], 'cave'),
            ('statue', 'statue_frames.png', [(i*32, 0, i*32+32, 96) for i in range(6)], 'cave'),
            ('pot', 'pot_frames.png', [(0,0,32,32),(32,0,64,32),(0,32,32,64),(32,32,64,64)], 'cave'),
            ('window', 'props_tileset_v1.1.png', [(0,0,64,32)], 'cave'),
            ('skeleton', 'props_tileset_v1.1.png', [(64,0,128,64)], 'cave'),
            ('cupboard', 'props_tileset_v1.1.png', [(128,352,192,448)], 'cave')]
    manifest = {}
    for name, filename, crops, realm in spec:
        target = OUT / (name+'.png')
        if sources:
            source = next(sources.rglob(filename))
            sheet = Image.open(source)
            w,h = crops[0][2]-crops[0][0], crops[0][3]-crops[0][1]
            strip = Image.new('RGBA',(w*len(crops),h))
            for i, crop in enumerate(crops):
                frame = adapt(sheet.crop(crop), PALETTES[realm])
                # In-game masonry/ripples permanently integrate each selected fragment.
                d=ImageDraw.Draw(frame)
                if name in ('cell','statue','window','skeleton','cupboard'):
                    d.rectangle((0,h-4,w-1,h-1),fill=PALETTES[realm][1]);d.line((0,h-4,w-1,h-4),fill=PALETTES[realm][3])
                else:
                    d.line((2,h-3,w-4,h-3),fill=PALETTES[realm][2])
                strip.paste(frame,(i*w,0))
            strip.save(target)
        image=Image.open(target)
        manifest[name]={'file': target.name,'size':list(image.size),'frames':len(crops),
                        'source':filename,'crops':crops,'palette':realm,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (OUT/'derivatives.json').write_text(json.dumps(manifest,indent=2)+'\n')


def scene(realm, area):
    p=PALETTES[realm]; im=Image.new('RGBA',(600,220));d=ImageDraw.Draw(im)
    def stone(x,y,w,h):
        d.rectangle((x,y,x+w,y+h),fill=p[1],outline=p[2])
        for yy in range(y+8,y+h,12):
            d.line((x,yy,x+w,yy),fill=p[0])
            for xx in range(x+((yy//12)%2)*12,x+w,24):d.line((xx,yy,xx,yy+12),fill=p[0])
    if realm=='forest':
        if area==0:
            for x,y in [(30,95),(165,125),(370,80),(510,130)]:
                stone(x,y,24,220-y);stone(x-8,y-8,40,8)
                d.polygon([(x+24,y),(x+65,y-30),(x+110,y),(x+104,y+8),(x+65,y-20)],fill=p[2])
            d.polygon([(230,220),(267,160),(309,220)],fill=p[2]);d.polygon([(255,220),(267,178),(285,220)],fill=p[0])
            d.line((231,220,267,160),fill=p[3],width=2)
            for xx in (219,316):d.line((xx,218,xx+4,196),fill=p[3],width=2)
            for xx in (337,348,356):d.line((xx,217,xx+11,207),fill=p[1],width=3)
            d.line((320,202,353,211),fill=p[3],width=3)
        elif area==1:
            for x in (20,260,485):
                d.polygon([(x,220),(x+16,80),(x+30,35),(x+40,80),(x+30,220)],fill=p[0])
                for j in range(5):d.ellipse((x-45+j*7,30+j*18,x+90,85+j*18),fill=p[1])
            stone(135,155,90,18);stone(390,124,70,16)
            for x in (95,120,238,350,465,560):
                for j in range(3):d.line((x,220,x+j*5-6,190-j*3),fill=p[3],width=2)
        else:
            stone(165,67,42,153);stone(393,67,42,153);stone(155,55,290,24)
            d.arc((194,57,406,246),180,360,fill=p[3],width=9)
            stone(270,180,60,40)
            d.polygon([(278,179),(270,118),(282,79),(300,65),(319,82),(330,118),(322,179)],fill=p[2])
            d.ellipse((289,49,310,77),fill=p[3]);d.line((300,100,300,163),fill=p[0],width=3)
            for x in range(160,440,21):
                d.line((x,58,x+7,100+(x%53)),fill=p[2],width=3)
                for y in range(64,110,13):d.ellipse((x-3,y,x+5,y+4),fill=p[3])
    elif realm=='cave':
        for x in (5,140,440,570):stone(x,30 if area else 90,22,190)
        if area==0:
            for x,y in [(50,135),(240,185),(315,158),(480,200)]:stone(x,y,65,220-y)
            d.polygon([(170,5),(230,20),(255,45),(202,64)],fill=p[2])
        elif area==1:
            for x in (50,205,355,505):
                stone(x,93,70,127);d.rectangle((x+8,105,x+62,217),fill=p[0])
                for xx in range(x+12,x+65,12):d.line((xx,107,xx,210),fill=p[2],width=2)
            d.rectangle((145,200,340,219),fill=(39,60,67))
            for x in range(158,330,26):d.line((x,205,x+17,205),fill=p[3])
        else:
            stone(145,25,310,195);d.rectangle((199,55,402,219),fill=p[0],outline=p[3],width=3)
            for x in range(210,400,22):d.line((x,58,x,217),fill=p[2],width=3)
            stone(259,120,83,100);stone(246,175,110,20)
            d.polygon([(270,119),(270,80),(290,90),(300,68),(312,90),(330,80),(330,119)],fill=p[3])
            for x in (60,100,488,528):
                d.line((x,155,x,214),fill=p[3],width=2);d.line((x-8,180,x+8,180),fill=p[2],width=3)
        for x in (120,385):
            for yy in range(0,80,6):d.ellipse((x-1,yy,x+2,yy+5),outline=p[3])
            d.rectangle((x-22,80,x+22,83),fill=p[2])
            for xx in (x-18,x,x+18):d.rectangle((xx,73,xx+2,79),fill=(201,154,85))
    else:
        if area==0:
            for x,h in [(25,35),(80,48),(190,28),(255,39),(410,55),(520,33)]:
                stone(x,220-h,20,h);d.arc((x,210-h,x+20,230-h),180,360,fill=p[3],width=3)
            for x in (130,350,565):
                d.line((x,220,x+8,76),fill=p[1],width=8)
                for dx,y in [(-35,100),(38,120),(-30,150)]:d.line((x+7,y+35,x+dx,y),fill=p[1],width=4)
        elif area==1:
            for x in (30,225,430):
                stone(x,110,140,110);d.polygon([(x-8,110),(x+70,64),(x+148,110)],fill=p[2])
                d.rectangle((x+47,148,x+92,219),fill=p[0],outline=p[3],width=2)
                d.line((x+69,153,x+69,216),fill=p[2],width=2)
                d.rectangle((x+14,191,x+20,208),fill=p[3]);d.point((x+17,188),fill=(218,185,124))
        else:
            stone(145,80,310,140);d.polygon([(125,80),(300,19),(475,80)],fill=p[2])
            stone(255,0,90,80);d.rectangle((272,8,328,64),fill=p[0])
            d.pieslice((281,17,320,59),180,360,fill=p[3]);d.rectangle((282,35,319,48),fill=p[3]);d.line((300,49,300,56),fill=p[2],width=3)
            d.rectangle((259,136,341,219),fill=p[0],outline=p[3],width=3)
            for x in (180,380):
                stone(x,176,40,44);d.polygon([(x+6,175),(x+4,131),(x+20,110),(x+36,131),(x+34,175)],fill=p[2]);d.ellipse((x+12,94,x+27,114),fill=p[3])
        if area==1:
            for x in (182,383):
                d.polygon([(x,220),(x-8,197),(x-4,182),(x+12,178),(x+21,190),(x+19,220)],fill=p[1],outline=p[3])
                d.line((x+6,185,x+8,209),fill=p[2],width=2)
            for x in (193,407):
                d.line((x,215,x+12,211),fill=p[3],width=2)
                for xx in (x,x+12):d.ellipse((xx-2,211,xx+2,215),fill=p[3])
        for x in (20,570):
            d.line((x,220,x,152),fill=p[2],width=2)
            d.line((x,153,x+13,153),fill=p[2],width=2)
            d.rectangle((x+8,155,x+18,170),fill=p[0],outline=p[3])
            d.rectangle((x+11,160,x+15,166),fill=(198,180,132))
        for x in range(5,590,30):
            d.line((x,203,x,219),fill=p[2],width=2);d.polygon([(x-3,204),(x,199),(x+3,204)],fill=p[3])
        d.line((0,209,600,209),fill=p[2],width=2)
    # Coordinate hashing gives worn pixel surfaces without touching random state.
    pixels=im.load()
    original=im.copy().load()
    for y in range(220):
        for x in range(600):
            c=original[x,y]
            if not c[3]:
                continue
            noise=(x*73856093 ^ y*19349663 ^ area*83492791)%101
            index=next((i for i,color in enumerate(p) if c[:3]==color),None)
            if index is not None and noise<3:
                pixels[x,y]=(*p[max(0,index-1)],255)
            elif index is not None and noise>99:
                pixels[x,y]=(*p[min(4,index+1)],255)
    im.save(OUT/f'{realm}-{area}.png')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sources',type=Path);args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    for realm in PALETTES:
        for area in range(3):scene(realm,area)
    derivatives(args.sources)

if __name__=='__main__':main()
