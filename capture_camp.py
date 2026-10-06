"""Headless courtyard, services, and gate inspection captures."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import tempfile
import pygame
from main import Game
from camp import POSITIONS, GATES


def capture(output=Path('artifacts')):
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        game=Game(Path(directory)/'save.json')
        game.reset_game('warrior')
        views=[('camp-left',180,None,[]),('camp-forge',500,None,[]),
               ('camp-gatehouse',1040,None,[]),('camp-hospice',1450,None,[]),
               ('camp-right',2000,None,[]),('storehouse-door',182,None,[]),
               ('healer',POSITIONS[3],'service',[]),('arcanist',POSITIONS[4],'service',[]),
               ('chronicler',POSITIONS[6],'service',[]),('gate-ready',GATES[0],'service',[]),
               ('gate-locked',GATES[1],'service',[]),('gate-cleared',GATES[2],'service',[0,1,2]),
               ('training',2100,'attack',[]),('trainer',POSITIONS[5],'service',[]),
               ('scout',POSITIONS[2],'service',[])]
        indoor = [('interior-entrance',90,False),('interior-counter',350,False),
                  ('interior-ledger',620,False),('interior-equipment',870,False),
                  ('interior-exit',90,False),('interior-dialogue',350,True),
                  ('interior-ledger-dialogue',620,True),('interior-equipment-dialogue',870,True)]
        sheet=pygame.Surface((2400,600*((len(views)+len(indoor)+2)//3)))
        for i,(name,x,action,cleared) in enumerate(views):
            game.service=None
            game.world.dialogue=None
            game.save.cleared_regions=cleared
            game.sources=[]
            game.knight.pending_attack=None
            game.knight.attacking=False
            game.knight.attack_hitbox=None
            game.knight.set_state('Idle',True)
            game.knight.rect.centerx=x
            game.knight.rect.bottom=560
            game.camera.update(game.knight.rect)
            game.world.ticks=180+i*17
            if action=='service': game.world.interact(game)
            if action=='attack':
                game.knight.facing_right=True
                game.knight.attack()
                for _ in range(6): game.tick({})
            game.draw()
            pygame.image.save(game.screen,output/(name+'.png'))
            sheet.blit(game.screen,((i%3)*800,(i//3)*600))
        # Include rebuildable original art at its native runtime dimensions.
        pygame.image.save(game.world.background,output/'camp-courtyard.png')
        game.service=None
        game.world.dialogue=None
        game.knight.rect.centerx=182
        game.knight.rect.bottom=560
        game.camera.update(game.knight.rect)
        game.world.interact(game)
        for frame in range(25):
            if frame in (0,6,12,18,24):
                game.draw()
                pygame.image.save(game.screen,output/f'storehouse-transition-{frame:02}.png')
            if frame < 24: game.tick({})
        for j,(name,x,dialogue) in enumerate(indoor):
            game.service=None
            game.world.dialogue=None
            game.knight.rect.midbottom=(x,560)
            game.camera.update(game.knight.rect)
            game.world.ticks=240+j*30
            if dialogue: game.world.interact(game)
            game.draw()
            pygame.image.save(game.screen,output/(name+'.png'))
            i=len(views)+j
            sheet.blit(game.screen,((i%3)*800,(i//3)*600))
        pygame.image.save(game.world.background,output/'storehouse-authored.png')
        pygame.image.save(sheet,output/'camp-contact-sheet.png')
    pygame.quit()


if __name__=='__main__':
    capture()
