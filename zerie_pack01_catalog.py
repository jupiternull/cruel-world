"""Inventory the local Zerie Pack 01 full archive without modifying source assets."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parent
PACK_NAME = 'Tiny RPG Character Asset Pack 01 v2.0 -Full 22 Characters'
CHARACTER_ROOT_NAME = 'Characters(100x100 split)'
DEFAULT_ASSET_ROOT = PROJECT_ROOT / 'assets' / 'vendor' / 'zerie' / 'pack01-full'
DEFAULT_OUTPUT = PROJECT_ROOT / 'artifacts' / 'zerie' / 'pack01-full'
PAGE_COLUMNS = 2
PAGE_ROWS = 4
PREVIEW_SCALE = 2

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def slugify(value):
    return ''.join(character.lower() if character.isalnum() else '-' for character in value).strip('-')


def relative_path(path, root):
    return Path(path).relative_to(root).as_posix()


def find_pack_root(asset_root):
    asset_root = Path(asset_root)
    direct = asset_root / CHARACTER_ROOT_NAME
    if direct.is_dir():
        return asset_root
    candidates = sorted(
        directory for directory in asset_root.iterdir()
        if directory.is_dir() and (directory / CHARACTER_ROOT_NAME).is_dir()
    )
    if len(candidates) != 1:
        raise ValueError(
            f'expected one Pack 01 directory containing {CHARACTER_ROOT_NAME!r} below {asset_root}; '
            f'found {len(candidates)}'
        )
    return candidates[0]


def named_frame_sizes(path):
    filename_match = re.search(r'\((\d+)x(\d+)\)', Path(path).stem, re.IGNORECASE)
    if filename_match:
        yield [int(filename_match.group(1)), int(filename_match.group(2))]
    for component in reversed(Path(path).parts):
        match = re.search(r'\((\d+)x(\d+)\s+split\)', component, re.IGNORECASE)
        if match:
            yield [int(match.group(1)), int(match.group(2))]


def frame_layout(path, image_size):
    width, height = image_size
    for named_size in named_frame_sizes(path):
        if width % named_size[0] == 0 and height % named_size[1] == 0:
            columns = width // named_size[0]
            rows = height // named_size[1]
            return named_size, [columns, rows], columns * rows
    if height and width % height == 0:
        return [height, height], [width // height, 1], width // height
    return [width, height], [1, 1], 1


def alpha_bounds(image):
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    bounds = image.getchannel('A').getbbox()
    return list(bounds) if bounds else None


def action_from_path(path, character_name):
    stem = path.stem
    prefix = f'{character_name}_'
    return stem[len(prefix):] if stem.startswith(prefix) else stem


def inventory_png(path, root, character_name=None):
    with Image.open(path) as source:
        image = source.convert('RGBA')
        frame_size, frame_grid, frame_count = frame_layout(path, image.size)
        metadata = {
            'source': relative_path(path, root),
            'sheet_size': list(image.size),
            'frame_size': frame_size,
            'frame_grid': frame_grid,
            'frame_count': frame_count,
            'alpha_visible_bounds': alpha_bounds(image),
            'sha256': sha256(path),
        }
    if character_name:
        metadata['action'] = action_from_path(path, character_name)
    return metadata


def inventory_variant(directory, root, character_name):
    sheets = [
        inventory_png(path, root, character_name)
        for path in sorted(directory.glob('*.png'), key=lambda path: path.name.casefold())
    ]
    if not sheets:
        raise ValueError(f'{character_name}: no PNG sheets in {directory}')
    return sheets


def is_effect_sheet(sheet):
    return sheet['action'].casefold().endswith('_effect')


def is_actor_action(sheet, character_name):
    return sheet['action'] != character_name and not is_effect_sheet(sheet)


def extra_category(path, container):
    if 'effect' in Path(path).stem.casefold():
        return 'effect'
    return 'projectile' if 'projectile' in container.casefold() else 'effect'


def discover_characters(asset_root):
    asset_root = Path(asset_root)
    pack_root = find_pack_root(asset_root)
    character_root = pack_root / CHARACTER_ROOT_NAME
    characters = []
    for character_directory in sorted(
        (path for path in character_root.iterdir() if path.is_dir()),
        key=lambda path: path.name.casefold(),
    ):
        name = character_directory.name
        base_directory = character_directory / name
        if not base_directory.is_dir():
            raise ValueError(f'{name}: missing unshadowed source directory {base_directory}')
        shadow_directory = character_directory / f'{name} with shadows'
        character_aseprite = character_directory / f'{name}.aseprite'
        pack_aseprite = pack_root / 'Aseprite file' / f'{name}.aseprite'
        extras = []
        for extra_directory in sorted(
            (path for path in character_directory.iterdir() if path.is_dir() and path not in {base_directory, shadow_directory}),
            key=lambda path: path.name.casefold(),
        ):
            for path in sorted(extra_directory.glob('*.png'), key=lambda path: path.name.casefold()):
                item = inventory_png(path, asset_root)
                item['category'] = extra_category(path, extra_directory.name)
                item['container'] = extra_directory.name
                extras.append(item)
        sheets = inventory_variant(base_directory, asset_root, name)
        embedded_effects = []
        for sheet in sheets:
            if is_effect_sheet(sheet):
                effect = dict(sheet)
                effect['category'] = 'effect'
                effect['container'] = name
                embedded_effects.append(effect)
        characters.append({
            'id': slugify(name),
            'name': name,
            'user_role': '',
            'source_directory': relative_path(character_directory, asset_root),
            'actions': [sheet['action'] for sheet in sheets if is_actor_action(sheet, name)],
            'sheets': sheets,
            'shadow_variant': {
                'present': shadow_directory.is_dir(),
                'source_directory': relative_path(shadow_directory, asset_root) if shadow_directory.is_dir() else None,
                'sheets': inventory_variant(shadow_directory, asset_root, name) if shadow_directory.is_dir() else [],
            },
            'aseprite_sources': {
                'character_directory': relative_path(character_aseprite, asset_root) if character_aseprite.is_file() else None,
                'pack_directory': relative_path(pack_aseprite, asset_root) if pack_aseprite.is_file() else None,
            },
            'projectiles_and_effects': embedded_effects + extras,
        })
    if not characters:
        raise ValueError(f'no character directories in {character_root}')
    return characters


def discover_shared_extras(asset_root):
    asset_root = Path(asset_root)
    pack_root = find_pack_root(asset_root)
    extras = []
    for directory in sorted(pack_root.iterdir(), key=lambda path: path.name.casefold()):
        if not directory.is_dir() or directory.name in {CHARACTER_ROOT_NAME, 'Aseprite file'}:
            continue
        for path in sorted(directory.glob('*.png'), key=lambda path: path.name.casefold()):
            item = inventory_png(path, asset_root)
            item['category'] = extra_category(path, directory.name)
            item['container'] = directory.name
            extras.append(item)
    return extras


def manifest_for(asset_root, characters):
    asset_root = Path(asset_root)
    pack_root = find_pack_root(asset_root)
    png_sources = sorted(asset_root.rglob('*.png'))
    aseprite_sources = sorted(asset_root.rglob('*.aseprite'))
    return {
        'catalog': 'zerie-pack01-full',
        'asset_root': str(asset_root),
        'pack_root': relative_path(pack_root, asset_root),
        'source_archive_sha256': '0907f6d9fbb91706cbc28979f2e7d897b5403c7cbf12aa10bbe5157bedfa4940',
        'character_count': len(characters),
        'source_file_counts': {'png': len(png_sources), 'aseprite': len(aseprite_sources)},
        'characters': characters,
        'shared_projectiles_and_effects': discover_shared_extras(asset_root),
    }


def write_manifest(manifest, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)


def wrap_text(draw, text, text_font, maximum_width):
    lines = []
    line = ''
    for word in text.split(', '):
        candidate = word if not line else f'{line}, {word}'
        if line and draw.textlength(candidate, font=text_font) > maximum_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def representative_sheet(character):
    preferred = ('Idle', 'Flying', 'Walk')
    by_action = {sheet['action']: sheet for sheet in character['sheets']}
    for action in preferred:
        if action in by_action:
            return by_action[action]
    return character['sheets'][0]


def render_contact_sheets(characters, asset_root, output_directory):
    asset_root = Path(asset_root)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    tile_width, tile_height = 1040, 380
    page_width = PAGE_COLUMNS * tile_width
    page_height = 54 + PAGE_ROWS * tile_height
    page_size = PAGE_COLUMNS * PAGE_ROWS
    title_font = font(30)
    name_font = font(26)
    detail_font = font(18)
    paths = []
    for page_index, start in enumerate(range(0, len(characters), page_size), 1):
        page = Image.new('RGBA', (page_width, page_height), (10, 14, 26, 255))
        draw = ImageDraw.Draw(page)
        draw.text((18, 14), f'ZERIE PACK 01 FULL — ROSTER {page_index}', font=title_font, fill=(0, 255, 65, 255))
        for tile_index, character in enumerate(characters[start:start + page_size]):
            column = tile_index % PAGE_COLUMNS
            row = tile_index // PAGE_COLUMNS
            x, y = column * tile_width, 54 + row * tile_height
            draw.rectangle((x + 8, y + 8, x + tile_width - 8, y + tile_height - 8), outline=(0, 204, 255, 255), width=2)
            draw.text((x + 24, y + 20), character['name'], font=name_font, fill=(0, 255, 65, 255))
            preview = representative_sheet(character)
            draw.text(
                (x + 24, y + 56),
                f"{preview['action']} · {preview['frame_count']} frames · {preview['sheet_size'][0]}×{preview['sheet_size'][1]}",
                font=detail_font,
                fill=(220, 229, 222, 255),
            )
            action_lines = wrap_text(draw, ', '.join(character['actions']), detail_font, tile_width - 48)
            for line_index, line in enumerate(action_lines):
                draw.text((x + 24, y + 82 + line_index * 20), line, font=detail_font, fill=(145, 171, 185, 255))
            with Image.open(asset_root / preview['source']) as source:
                source = source.convert('RGBA')
                displayed_frames = min(preview['frame_count'], 4)
                for frame_index in range(displayed_frames):
                    frame_width, frame_height = preview['frame_size']
                    frame_column = frame_index % preview['frame_grid'][0]
                    frame_row = frame_index // preview['frame_grid'][0]
                    frame = source.crop((
                        frame_column * frame_width,
                        frame_row * frame_height,
                        (frame_column + 1) * frame_width,
                        (frame_row + 1) * frame_height,
                    ))
                    frame = frame.resize((frame.width * PREVIEW_SCALE, frame.height * PREVIEW_SCALE), Image.Resampling.NEAREST)
                    page.alpha_composite(frame, (x + 26 + frame_index * (frame.width + 8), y + 122 + (len(action_lines) - 1) * 20))
            extra_count = len(character['projectiles_and_effects'])
            metadata = f"shadow {'yes' if character['shadow_variant']['present'] else 'no'} · aseprite {sum(value is not None for value in character['aseprite_sources'].values())}/2 · extras {extra_count}"
            draw.text((x + 24, y + 348), metadata, font=detail_font, fill=(0, 204, 255, 255))
        path = output_directory / f'roster-{page_index:02d}.png'
        page.save(path)
        paths.append(path)
    return paths


def write_capabilities_report(characters, output_path):
    lines = [
        '# Zerie Pack 01 Full — Character Capabilities',
        '',
        'This inventory assigns no gameplay roles. `User-owned role` is deliberately blank for later direction.',
        '',
    ]
    for character in characters:
        extras = character['projectiles_and_effects']
        action_text = ', '.join(character['actions'])
        extra_text = ', '.join(
            f"{item['category']}: {Path(item['source']).name}" for item in extras
        ) or 'none'
        aseprite_count = sum(value is not None for value in character['aseprite_sources'].values())
        lines.extend((
            f"## {character['name']}",
            '',
            '**User-owned role:** ',
            '',
            f'**Actions:** {action_text}',
            '',
            f"**Unshadowed sheets:** {len(character['sheets'])}; **shadow variant:** {'present' if character['shadow_variant']['present'] else 'absent'}; **Aseprite sources:** {aseprite_count}/2.",
            '',
            f'**Projectiles/effects:** {extra_text}.',
            '',
        ))
    output_path = Path(output_path)
    output_path.write_text('\n'.join(lines), encoding='utf-8')


def source_hashes(asset_root):
    asset_root = Path(asset_root)
    return {
        relative_path(path, asset_root): sha256(path)
        for path in sorted(asset_root.rglob('*')) if path.is_file()
    }


def build_catalog(asset_root=DEFAULT_ASSET_ROOT, output_directory=DEFAULT_OUTPUT):
    asset_root = Path(asset_root)
    output_directory = Path(output_directory)
    before = source_hashes(asset_root)
    characters = discover_characters(asset_root)
    manifest = manifest_for(asset_root, characters)
    output_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = output_directory / 'manifest.json'
    report_path = output_directory / 'capabilities.md'
    contact_paths = render_contact_sheets(characters, asset_root, output_directory)
    write_manifest(manifest, manifest_path)
    write_capabilities_report(characters, report_path)
    after = source_hashes(asset_root)
    if before != after:
        raise RuntimeError('source asset hashes changed during catalog generation')
    return {
        'manifest': manifest_path,
        'role_report': report_path,
        'contact_sheets': contact_paths,
        'character_count': len(characters),
        'source_file_count': len(before),
    }


def project_path(path):
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def main():
    parser = argparse.ArgumentParser(description='Catalog the local Zerie Pack 01 full roster.')
    parser.add_argument('--assets-root', default='assets/vendor/zerie/pack01-full')
    parser.add_argument('--output', default='artifacts/zerie/pack01-full')
    args = parser.parse_args()
    result = build_catalog(project_path(args.assets_root), project_path(args.output))
    print(result['manifest'].resolve())
    print(result['role_report'].resolve())
    for path in result['contact_sheets']:
        print(path.resolve())


if __name__ == '__main__':
    main()
