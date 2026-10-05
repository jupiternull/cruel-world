"""Capture a continuous deterministic gameplay loop; Pillow is a tooling dependency."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import random
import tempfile
from pathlib import Path

import pygame
from PIL import Image
from main import Game
from verify_campaign import combat_keys


def capture(output=Path('docs/media/gameplay.gif')):
    random.seed(0)
    frames = []
    with tempfile.TemporaryDirectory() as temporary:
        game = Game(Path(temporary) / 'save.json')
        game.reset_game('ranger')
        for tick in range(480):
            game.tick(combat_keys(game, tick))
            if tick % 4 == 0:
                game.draw()
                data = pygame.image.tostring(game.screen, 'RGB')
                frames.append(Image.frombytes('RGB', (800, 600), data).resize(
                    (640, 480), Image.Resampling.NEAREST))
        # Reverse the same continuous sequence for a seamless preview loop.
        sequence = frames + frames[-2:0:-1]
        palette = frames[0].quantize(colors=128)
        sequence = [frame.quantize(palette=palette, dither=Image.Dither.NONE)
                    for frame in sequence]
        output.parent.mkdir(parents=True, exist_ok=True)
        sequence[0].save(output, save_all=True, append_images=sequence[1:],
                         duration=70, loop=0, optimize=True, disposal=1)
    pygame.quit()


if __name__ == '__main__':
    capture()
