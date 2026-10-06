"""Gameplay-scale authored views, including before/after expedition mechanisms."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import tempfile
import pygame
from main import Game


def capture(output=Path('artifacts/regions')):
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        game=Game(Path(directory)/'save.json')
        for realm,index in [('forest',0),('cave',1),('graveyard',2)]:
            for class_id in ('warrior','ranger','wizard'):
                game.reset_game(class_id);game.launch_expedition(index,debug=True)
                views=[('approach',400),('discovery',840 if index==0 else 1380 if index==1 else 2370),
                       ('mechanism',1550 if index==0 else 1780 if index==1 else 1860),
                       ('third-area',2800 if index==0 else 2860 if index==1 else 3000),
                       ('landmark',3050 if index==0 else 3300 if index==1 else 3450),
                       ('boss-arena',game.world.data['zones'][2])]
                shots=[]
                for label,x in views:
                    game.knight.rect.midbottom=(x,560);game.camera.update(game.knight.rect)
                    game.features.ticks=180
                    game.state.phase='travel'
                    if label=='boss-arena':
                        game.state.wave=3;game.state.phase='combat';game.spawn(True)
                    game.draw();shot=game.screen.copy();shots.append((label,shot))
                    pygame.image.save(shot,output/f'{realm}-{class_id}-{label}.png')
                game.enemies=[];game.state.phase='travel'
                if index==1:
                    game.knight.rect.midbottom=(1776,560);game.features.interact(game)
                    for _ in range(60):game.features.update(game)
                    game.camera.update(game.knight.rect)
                elif index==2:
                    for x in (660,1860,2970):
                        game.knight.rect.midbottom=(x,560);game.features.interact(game)
                    game.knight.rect.midbottom=(3450,560);game.camera.update(game.knight.rect)
                else:
                    game.knight.rect.midbottom=(1180,560);game.camera.update(game.knight.rect)
                    prop=game.features.breakables[0];prop.take_damage(30)
                    for _ in range(15):game.features.update(game)
                game.draw();shots.append(('mechanism-completed',game.screen.copy()))
                pygame.image.save(game.screen,output/f'{realm}-{class_id}-mechanism-completed.png')
                discovery = 'cache' if index==0 else 'ledger' if index==1 else 'record'
                game.knight.rect.midbottom=(game.features.objects[discovery][0],560)
                game.camera.update(game.knight.rect)
                game.features.interact(game)
                game.draw();shots.append(('discovery-read',game.screen.copy()))
                pygame.image.save(game.screen,output/f'{realm}-{class_id}-discovery-read.png')
                sheet=pygame.Surface((1600,4*624));sheet.fill((17,18,25))
                for i,(label,shot) in enumerate(shots):
                    x=(i%2)*800;y=(i//2)*624
                    sheet.blit(game.fonts['small'].render(label,True,(211,220,204)),(x+12,y+3))
                    sheet.blit(shot,(x,y+24))
                pygame.image.save(sheet,output/f'{realm}-{class_id}-contact-sheet.png')
    pygame.quit()

if __name__=='__main__':capture()
