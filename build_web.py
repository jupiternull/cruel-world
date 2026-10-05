"""Stage runtime files and build a validated itch.io HTML5 archive."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
MODULES = ('main.py', 'config.py', 'assets.py', 'audio.py', 'camera.py', 'campaign.py',
           'game_state.py', 'level.py', 'persistence.py', 'projectile.py', 'scenery.py', 'ui.py')


def runtime_files(root=ROOT):
    from assets import HERO_MANIFEST, MONSTER_MANIFEST, FOREST_ROOT, MOON_ROOT
    files = {root / name for name in MODULES}
    files.update((root / 'entities').glob('*.py'))
    for directory, *_ in HERO_MANIFEST.values():
        files.update((root / 'assets' / directory).rglob('*.png'))
    for species in MONSTER_MANIFEST:
        files.update((root / 'assets/enemies/luizmelo/Monsters_Creatures_Fantasy' / species).glob('*.png'))
    for name in ('Background/Background.png', 'Trees/Dark-Tree.png', 'Assets/Tiles.png',
                 'Assets/Interior-01.png', 'Assets/Buildings.png', 'Assets/Props-Rocks.png'):
        files.add(root / 'assets' / FOREST_ROOT / name)
    for name in ('Background_0.png', 'Background_1.png', 'Tiles.png'):
        files.add(root / 'assets' / MOON_ROOT / name)
    for directory in ('audio', 'fonts', 'licenses', 'ui'):
        files.update(p for p in (root / 'assets' / directory).rglob('*')
                     if p.is_file() and p.suffix.lower() in ('.ogg', '.wav', '.ttf', '.txt', '.png', '.md'))
    return sorted(files)


def validate_archive(path):
    with zipfile.ZipFile(path) as archive:
        files = [entry for entry in archive.infolist() if not entry.is_dir()]
        if 'index.html' not in archive.namelist() or archive.testzip():
            raise ValueError('Missing root index.html or corrupt ZIP')
        if len(files) > 1000 or sum(f.file_size for f in files) > 500_000_000:
            raise ValueError('Archive exceeds itch.io total limits')
        if any(f.file_size > 200_000_000 or len(f.filename) > 240 or
               f.filename.startswith('/') or '..' in Path(f.filename).parts for f in files):
            raise ValueError('Archive exceeds itch.io file limits or has unsafe paths')
        return {'files': len(files), 'bytes': path.stat().st_size,
                'extracted_bytes': sum(f.file_size for f in files)}


def polish_index(html):
    # pygbag's itch ZIP omits the tar used by its localhost branch.
    branch = "if platform.window.location.host.find('.itch.zone')>0:"
    if branch not in html:
        raise ValueError('pygbag loader template changed; review archive loading')
    html = html.replace(branch, 'if True:  # use the packaged ZIP on every host')
    html = html.replace('platform.document.body.style.background = "#7f7f7f"',
                        'platform.document.body.style.background = "#100e14"')
    style = """<style>
body { background: #100e14; color: #e6dbb8; }
#infobox { background: #201a24; color: #e6dbb8; border: 1px solid #a6854c;
 font: 16px Georgia, serif; box-shadow: 0 8px 32px #0008; }
#status { color: #e6dbb8; }
#progress { accent-color: #a6854c; }
canvas { image-rendering: pixelated; }
</style>"""
    return html.replace('<body>', style + '\n<body>')


def main():
    output = ROOT / 'dist/cruel-world-closed-alpha.zip'
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cruelworld-web-') as temporary:
        stage = Path(temporary) / 'cruelworld'
        stage.mkdir()
        for source in runtime_files():
            target = stage / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix == '.wav':
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(source),
                                '-c:a', 'libvorbis', str(target.with_suffix('.ogg'))], check=True)
            else:
                shutil.copy2(source, target)
        subprocess.run([sys.executable, '-m', 'pygbag', '--build', '--archive', '--no_opt',
                        '--title', 'Cruel World | Closed Alpha', '--app_name', 'Cruel World',
                        '--package', 'com.jupiternull.cruelworld', '--ume_block', '1', str(stage)], check=True)
        built = stage / 'build/web.zip'
        with zipfile.ZipFile(built) as source, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as published:
            for name in source.namelist():
                data = source.read(name)
                if name == 'index.html':
                    data = polish_index(data.decode()).encode()
                published.writestr(name, data)
            published.write(ROOT / 'PLAYTEST.md', 'PLAYTEST.md')
        result = validate_archive(output)
    print(json.dumps({'artifact': str(output), **result}, indent=2))


if __name__ == '__main__':
    main()
