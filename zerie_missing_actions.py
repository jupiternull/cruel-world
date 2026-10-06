"""Build deterministic missing-action proof sheets from the local Zerie Soldier source."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from zerie_asset_proof import FRAME_SIZE, SAMPLES, character_directory


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_ROOT / 'artifacts' / 'zerie' / 'missing-actions'
SCALE = 4
GROUND_Y = 82
ACTIONS = ('Run', 'Jump', 'Fall', 'Land', 'Evade')
ACTION_FRAMES = {
    'Run': (
        ('Walk', 0, 0, 0), ('Walk', 1, 0, 0), ('Walk', 2, 0, 0), ('Walk', 3, 0, 0),
        ('Walk', 4, 0, 0), ('Walk', 5, 0, 0), ('Walk', 6, 0, 0), ('Walk', 7, 0, 0),
    ),
    'Jump': (
        ('Walk', 1, 0, 0), ('Walk', 2, 0, -3), ('Walk', 3, 1, -10),
        ('Walk', 4, 2, -18), ('Walk', 5, 2, -24), ('Walk', 6, 2, -20),
    ),
    'Fall': (
        ('Walk', 6, 1, -24), ('Walk', 7, 1, -20), ('Walk', 0, 0, -15),
        ('Walk', 1, 0, -9), ('Walk', 2, 0, -3),
    ),
    'Land': (
        ('Walk', 3, 1, -2), ('Walk', 4, 1, 2), ('Walk', 5, 0, 3),
        ('Walk', 6, 0, 1), ('Idle', 0, 0, 0),
    ),
    'Evade': (
        ('Idle', 1, 0, 0), ('Walk', 6, -2, 1), ('Walk', 5, -6, 0),
        ('Walk', 4, -10, -1), ('Hurt', 0, -12, 0), ('Walk', 7, -8, 0),
        ('Idle', 2, -3, 0), ('Idle', 0, 0, 0),
    ),
}


def soldier_sample():
    return next(sample for sample in SAMPLES if sample['id'] == 'soldier')


def source_directory(asset_root):
    return character_directory(asset_root, soldier_sample())


def source_path(asset_root, animation):
    return source_directory(asset_root) / f'Soldier_{animation}.png'


def load_source_frames(asset_root):
    frames = {}
    needed = {animation for sequence in ACTION_FRAMES.values() for animation, *_ in sequence}
    for animation in needed:
        sheet = Image.open(source_path(asset_root, animation)).convert('RGBA')
        frames[animation] = [
            sheet.crop((index * FRAME_SIZE, 0, (index + 1) * FRAME_SIZE, FRAME_SIZE))
            for index in range(sheet.width // FRAME_SIZE)
        ]
    return frames


def alpha_bounds(image):
    return image.getchannel('A').getbbox()


def grounded_frame(source, offset_x=0, offset_y=0):
    """Re-anchor source pixels at one ground line before applying authored motion."""
    bounds = alpha_bounds(source)
    if bounds is None:
        return Image.new('RGBA', (FRAME_SIZE, FRAME_SIZE))
    frame = Image.new('RGBA', (FRAME_SIZE, FRAME_SIZE))
    x = (FRAME_SIZE - (bounds[2] - bounds[0])) // 2 - bounds[0] + offset_x
    y = GROUND_Y - bounds[3] + offset_y
    frame.alpha_composite(source, (x, y))
    return frame


def edit_landing_compression(frame, amount):
    """Reuse the lower source-pixel clusters to give contact frames a compressed weight."""
    if not amount:
        return frame
    result = frame.copy()
    lower = frame.crop((0, 62, FRAME_SIZE, FRAME_SIZE))
    result.paste((0, 0, 0, 0), (0, 62, FRAME_SIZE, FRAME_SIZE))
    result.alpha_composite(lower, (0, amount + 62))
    return result


def action_frames(asset_root):
    source_frames = load_source_frames(asset_root)
    actions = {}
    for action, sequence in ACTION_FRAMES.items():
        rendered = []
        for index, (animation, frame_index, x, y) in enumerate(sequence):
            frame = grounded_frame(source_frames[animation][frame_index], x, y)
            if action == 'Land' and index in (1, 2):
                frame = edit_landing_compression(frame, 1)
            rendered.append(frame)
        actions[action] = rendered
    return actions


def save_action_sheets(actions, output_directory):
    paths = {}
    for action, frames in actions.items():
        sheet = Image.new('RGBA', (FRAME_SIZE * len(frames), FRAME_SIZE))
        for index, frame in enumerate(frames):
            sheet.alpha_composite(frame, (index * FRAME_SIZE, 0))
        path = output_directory / f'soldier-{action.lower()}.png'
        sheet.save(path)
        paths[action] = path
    return paths


def text_font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)


def render_contact_sheet(actions, output_path):
    label_width = 178
    row_height = FRAME_SIZE * SCALE + 58
    width = label_width + max(len(frames) for frames in actions.values()) * FRAME_SIZE * SCALE + 32
    height = 70 + row_height * len(actions)
    sheet = Image.new('RGBA', (width, height), (10, 14, 26, 255))
    draw = ImageDraw.Draw(sheet)
    title_font = text_font(30)
    label_font = text_font(24)
    draw.text((18, 18), 'ZERIE SOLDIER — MISSING ACTION PROOF', font=title_font, fill=(0, 255, 65, 255))
    for row, (action, frames) in enumerate(actions.items()):
        y = 70 + row * row_height
        draw.rectangle((12, y, width - 12, y + row_height - 10), outline=(0, 204, 255, 255), width=2)
        draw.text((28, y + 18), action, font=label_font, fill=(220, 229, 222, 255))
        ground = y + 24 + GROUND_Y * SCALE
        draw.line((label_width, ground, width - 28, ground), fill=(76, 91, 104, 255), width=2)
        for index, frame in enumerate(frames):
            scaled = frame.resize((FRAME_SIZE * SCALE, FRAME_SIZE * SCALE), Image.Resampling.NEAREST)
            sheet.alpha_composite(scaled, (label_width + index * FRAME_SIZE * SCALE, y + 20))
            draw.text((label_width + index * FRAME_SIZE * SCALE + 8, y + 4), str(index + 1), font=label_font, fill=(0, 204, 255, 255))
    sheet.save(output_path)


def render_gif(actions, output_path):
    width, height = 620, 500
    title_font = text_font(36)
    label_font = text_font(24)
    frames = []
    durations = []
    for action, action_sequence in actions.items():
        for index, frame in enumerate(action_sequence):
            canvas = Image.new('RGBA', (width, height), (10, 14, 26, 255))
            draw = ImageDraw.Draw(canvas)
            draw.rectangle((18, 16, width - 18, height - 16), outline=(0, 204, 255, 255), width=2)
            draw.text((36, 34), 'ZERIE SOLDIER', font=title_font, fill=(0, 255, 65, 255))
            draw.text((36, 82), f'{action.upper()}  {index + 1}/{len(action_sequence)}', font=label_font, fill=(220, 229, 222, 255))
            ground = 425
            draw.line((52, ground, width - 52, ground), fill=(76, 91, 104, 255), width=3)
            scaled = frame.resize((FRAME_SIZE * SCALE, FRAME_SIZE * SCALE), Image.Resampling.NEAREST)
            canvas.alpha_composite(scaled, ((width - scaled.width) // 2, ground - GROUND_Y * SCALE))
            frames.append(canvas.convert('P', palette=Image.Palette.ADAPTIVE, colors=255))
            durations.append(92)
        durations[-1] = 260
    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=durations, loop=0, disposal=2)


def source_hashes(asset_root):
    needed = sorted({animation for sequence in ACTION_FRAMES.values() for animation, *_ in sequence})
    return {
        source_path(asset_root, animation).relative_to(asset_root).as_posix():
        hashlib.sha256(source_path(asset_root, animation).read_bytes()).hexdigest()
        for animation in needed
    }


def write_manifest(output_path, asset_root, actions):
    payload = {
        'frame_size': [FRAME_SIZE, FRAME_SIZE],
        'ground_y': GROUND_Y,
        'actions': {
            action: {
                'frame_count': len(frames),
                'sources': [
                    {'animation': animation, 'frame': index, 'offset': [x, y]}
                    for animation, index, x, y in ACTION_FRAMES[action]
                ],
            }
            for action, frames in actions.items()
        },
        'source_hashes': source_hashes(asset_root),
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def build_missing_actions(asset_root, output_directory):
    asset_root = Path(asset_root)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    actions = action_frames(asset_root)
    sheets = save_action_sheets(actions, output_directory)
    contact_sheet = output_directory / 'contact-sheet.png'
    animated_gif = output_directory / 'soldier-missing-actions.gif'
    manifest = output_directory / 'manifest.json'
    render_contact_sheet(actions, contact_sheet)
    render_gif(actions, animated_gif)
    write_manifest(manifest, asset_root, actions)
    return {'sheets': sheets, 'contact_sheet': contact_sheet, 'animated_gif': animated_gif, 'manifest': manifest}


def project_path(path):
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def main():
    parser = argparse.ArgumentParser(description='Render Zerie Soldier missing-action derivative proof.')
    parser.add_argument('--assets-root', default='assets/vendor/zerie')
    parser.add_argument('--output', default='artifacts/zerie/missing-actions')
    args = parser.parse_args()
    result = build_missing_actions(project_path(args.assets_root), project_path(args.output))
    for path in (*result['sheets'].values(), result['contact_sheet'], result['animated_gif'], result['manifest']):
        print(path.resolve())


if __name__ == '__main__':
    main()
