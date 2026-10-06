import argparse
import json
import os
from pathlib import Path

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame


PROJECT_ROOT = Path(__file__).resolve().parent
FRAME_SIZE = 100
PREVIEW_SCALE = 2
SAMPLES = (
    {
        'id': 'soldier',
        'name': 'Soldier',
        'pack': 'pack01-free',
        'pack_directory': 'Tiny RPG Character Asset Pack 01 v2.0 -Free Soldier&Orc',
        'animations': (
            ('Idle', 6), ('Walk', 8), ('Attack01', 6), ('Attack02', 6),
            ('Attack03', 9), ('Hurt', 4), ('Death', 4),
        ),
    },
    {
        'id': 'orc',
        'name': 'Orc',
        'pack': 'pack01-free',
        'pack_directory': 'Tiny RPG Character Asset Pack 01 v2.0 -Free Soldier&Orc',
        'animations': (
            ('Idle', 6), ('Walk', 8), ('Attack01', 6), ('Attack02', 6),
            ('Hurt', 4), ('Death', 4),
        ),
    },
    {
        'id': 'demon_a',
        'name': 'Demon_A',
        'pack': 'pack02-free',
        'pack_directory': 'Tiny RPG Character Asset Pack 02 -Free Demon_A&Blood Monster_A',
        'animations': (
            ('Idle', 6), ('Walk', 8), ('Attack01', 7), ('Attack02', 7),
            ('Hurt', 4), ('Death', 4),
        ),
    },
    {
        'id': 'blood_monster_a',
        'name': 'Blood Monster_A',
        'pack': 'pack02-free',
        'pack_directory': 'Tiny RPG Character Asset Pack 02 -Free Demon_A&Blood Monster_A',
        'animations': (
            ('Idle', 6), ('Walk', 8), ('Attack01', 8), ('Attack02', 8),
            ('Hurt', 4), ('Death', 4),
        ),
    },
)


def character_directory(asset_root, sample):
    return (Path(asset_root) / sample['pack'] / sample['pack_directory'] /
            'Characters(100x100 split)' / sample['name'] / sample['name'])


def discover_characters(asset_root):
    asset_root = Path(asset_root)
    characters = []
    for sample in SAMPLES:
        directory = character_directory(asset_root, sample)
        sheets = []
        for animation, expected_frames in sample['animations']:
            path = directory / f"{sample['name']}_{animation}.png"
            if not path.is_file():
                raise ValueError(f"{sample['id']}/{animation}: missing {path}")
            image = pygame.image.load(str(path))
            width, height = image.get_size()
            expected_size = (FRAME_SIZE * expected_frames, FRAME_SIZE)
            if (width, height) != expected_size:
                raise ValueError(
                    f"{sample['id']}/{animation}: expected {expected_size[0]}x{expected_size[1]}, "
                    f"got {width}x{height}"
                )
            sheets.append({
                'animation': animation,
                'frame_count': expected_frames,
                'frame_size': [FRAME_SIZE, FRAME_SIZE],
                'sheet_size': [width, height],
                'source': path.relative_to(asset_root).as_posix(),
            })
        characters.append({
            'id': sample['id'],
            'name': sample['name'],
            'pack': sample['pack'],
            'source_directory': directory.relative_to(asset_root).as_posix(),
            'sheets': sheets,
        })
    return characters


def manifest_for(characters):
    return {
        'asset_root': 'assets/vendor/zerie',
        'frame_size': [FRAME_SIZE, FRAME_SIZE],
        'preview_scale': PREVIEW_SCALE,
        'characters': characters,
    }


def write_manifest(characters, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest_for(characters), indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )


def draw_text(surface, font, text, position, color=(220, 229, 222)):
    surface.blit(font.render(text, False, color), position)


def render_contact_sheet(characters, asset_root, output_path):
    asset_root = Path(asset_root)
    output_path = Path(output_path)
    font = pygame.font.Font(None, 26)
    title_font = pygame.font.Font(None, 36)
    frame_pixels = FRAME_SIZE * PREVIEW_SCALE
    label_width = 156
    row_height = frame_pixels + 30
    panel_width = label_width + (9 * frame_pixels) + 24
    panel_height = 52 + max(len(character['sheets']) for character in characters) * row_height + 16
    gap = 16
    sheet = pygame.Surface((panel_width * 2 + gap * 3, panel_height * 2 + gap * 3))
    sheet.fill((10, 14, 26))

    for index, character in enumerate(characters):
        panel_x = gap + (index % 2) * (panel_width + gap)
        panel_y = gap + (index // 2) * (panel_height + gap)
        panel = pygame.Surface((panel_width, panel_height))
        panel.fill((19, 26, 43))
        pygame.draw.rect(panel, (0, 204, 255), panel.get_rect(), 2)
        draw_text(panel, title_font, character['name'], (12, 10), (0, 255, 65))
        for row, metadata in enumerate(character['sheets']):
            y = 52 + row * row_height
            draw_text(panel, font, f"{metadata['animation']} ({metadata['frame_count']})", (10, y + 6))
            source = asset_root / metadata['source']
            image = pygame.image.load(str(source))
            for frame_index in range(metadata['frame_count']):
                frame = image.subsurface((frame_index * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE))
                frame = pygame.transform.scale(frame, (frame_pixels, frame_pixels))
                panel.blit(frame, (label_width + frame_index * frame_pixels, y))
        sheet.blit(panel, (panel_x, panel_y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(sheet, str(output_path))


def build_proof(asset_root, output_directory):
    pygame.init()
    try:
        characters = discover_characters(asset_root)
        output_directory = Path(output_directory)
        manifest_path = output_directory / 'manifest.json'
        contact_sheet_path = output_directory / 'contact-sheet.png'
        write_manifest(characters, manifest_path)
        render_contact_sheet(characters, asset_root, contact_sheet_path)
        return manifest_path, contact_sheet_path
    finally:
        pygame.quit()


def project_path(path):
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def main():
    parser = argparse.ArgumentParser(
        description='Validate local Zerie free samples and render a gameplay-scale proof.'
    )
    parser.add_argument('--assets-root', default='assets/vendor/zerie')
    parser.add_argument('--output', default='artifacts/zerie')
    args = parser.parse_args()
    manifest_path, contact_sheet_path = build_proof(
        project_path(args.assets_root), project_path(args.output)
    )
    print(manifest_path.resolve())
    print(contact_sheet_path.resolve())


if __name__ == '__main__':
    main()
