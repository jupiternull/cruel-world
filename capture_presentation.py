"""Capture all UI modes and nine runtime class/realm views without touching player saves."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import tempfile
import pygame
from main import Game
from entities.hero import CLASSES


def capture(output=Path('artifacts')):
    output.mkdir(exist_ok=True)
    shots=[]
    with tempfile.TemporaryDirectory() as root:
        game=Game(Path(root)/'save.json')
        def shot(name):
            game.draw()
            pygame.image.save(game.screen,str(output/(name+'.png')))
            shots.append(name)
        for mode in ('title','settings','pause','over','victory'):
            game.reset_game('warrior')
            game.launch_expedition(0, debug=True)
            if mode == 'over':
                game.knight.take_damage(game.knight.max_health)
                for _ in range(90): game.knight.update_animation(1000 / 60)
            game.change_mode(mode)
            shot('death' if mode=='over' else mode)
        game.change_mode('class')
        for i,name in enumerate(CLASSES):
            game.selection=i
            shot('class-'+name)
        for name in CLASSES:
            for realm in range(3):
                game.reset_game(name)
                game.campaign.index=realm
                game.launch_expedition(game.campaign.index, debug=True)
                game.knight.rect.x=game.campaign.environment['zones'][0]-80
                game.camera.update(game.knight.rect)
                game.state.phase='combat'
                game.spawn()
                game.enemies[0].rect.x=game.knight.rect.x+90
                game.knight.attack()
                for _ in range(9):game.tick({})
                shot('combat-'+name+'-'+str(realm+1))
        sheet=pygame.Surface((1200,((len(shots)+2)//3)*300))
        for i,name in enumerate(shots):
            im=pygame.image.load(str(output/(name+'.png')))
            sheet.blit(pygame.transform.scale(im,(400,300)),(i%3*400,i//3*300))
        pygame.image.save(sheet,str(output/'ui-contact-sheet.png'))
        detail=pygame.Surface((800,440))
        detail.fill((24,25,29))
        for column,(state,index) in enumerate((('Idle',0),('Attack1',3),('Roll',2),('Death',9))):
            frame=game.assets['heroes']['warrior'][state][index]
            for row,facing in enumerate((True,False)):
                image=frame if facing else pygame.transform.flip(frame,True,False)
                detail.blit(pygame.transform.scale(image,(200,220)),(column*200,row*220))
        pygame.image.save(detail,str(output/'knight-facing-contact-sheet.png'))
    ranger_contact(output)
    pygame.quit()

def ranger_contact(output):
    from build_presentation import RANGER_POSES
    font=pygame.font.Font(None,20)
    sheet=pygame.Surface((1280,len(RANGER_POSES)*340))
    sheet.fill((35,39,43))
    for row,(state,poses) in enumerate(RANGER_POSES.items()):
        source=pygame.image.load('assets/heroes/ranger/'+state+'.png')
        for index in range(len(poses)):
            frame=source.subsurface((index*200,0,200,200))
            # Both facings use the same complete-canvas flip as the runtime renderer.
            for facing in range(2):
                image=frame if facing==0 else pygame.transform.flip(frame,True,False)
                image=image.subsurface((45,55,110,100))
                sheet.blit(pygame.transform.scale(image,(160,145)),(index*160,row*340+facing*170+20))
                sheet.blit(font.render(f'{state} {index} '+('R' if facing==0 else 'L'),True,(220,214,194)),(index*160,row*340+facing*170))
    pygame.image.save(sheet,str(output/'ranger-facing-contact-sheet.png'))


if __name__=='__main__':capture()
