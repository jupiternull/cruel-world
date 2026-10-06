"""Rebuild original gameplay-scale progression captures without touching user saves."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from pathlib import Path
import tempfile
import pygame
from main import Game
from camp import GATES
from progression import PROVISIONS


def main():
    output = Path('artifacts/progression')
    output.mkdir(parents=True, exist_ok=True)
    shots = []
    with tempfile.TemporaryDirectory() as d:
        game = Game(Path(d) / 'save.json')
        def shot(name):
            game.draw()
            pygame.image.save(game.screen, output / (name + '.png'))
            shots.append(game.screen.copy())
        for n in range(4):
            game.save.cleared_regions = list(range(n))
            game.enter_camp('The watch welcomes you home.')
            game.knight.rect.centerx = 720
            game.camera.update(game.knight.rect)
            shot('camp-' + str(n))
        for name in ('forge', 'supplies', 'journal'):
            game.open_service(name)
            shot(name)
            game.service = None
        game.world.dialogue = {'title': 'Expedition Gate', 'lines': game.world.intel(game, 0), 'gate': 0}
        game.knight.rect.centerx = GATES[0]
        game.camera.update(game.knight.rect)
        shot('gate-readied')
        game.depart(0)
        for t in range(100):
            game.tick({})
            if t in (0, 12, 30, 50, 76, 98): shot('departure-' + str(t))
        game.state.score = 8325
        game.features.claimed = {'cache', 'sanctuary'}
        game.expedition.provision = PROVISIONS[2]
        game.expedition.used = True
        game.save.cleared_regions = []
        game.finish_expedition()
        shot('results-first')
        game.return_results()
        game.launch_expedition(0)
        game.finish_expedition()
        shot('results-replay')
        game.return_results()
        game.save.cleared_regions = [0, 1]
        game.launch_expedition(2)
        game.finish_expedition()
        shot('results-final')
        sheet = pygame.Surface((1600, ((len(shots)+1)//2)*600))
        for i, frame in enumerate(shots): sheet.blit(frame, ((i%2)*800, (i//2)*600))
        pygame.image.save(sheet, output / 'contact-sheet.png')
        pygame.quit()


if __name__ == '__main__':
    main()
