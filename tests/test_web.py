import asyncio
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch
import zipfile

from build_web import polish_index, runtime_files, validate_archive
from main import Game
from persistence import SaveData


class WebTests(unittest.TestCase):
    def test_browser_loop_yields_without_blocking_clock(self):
        game = Game.__new__(Game)
        game.running = True
        game.mode = 'title'
        game.state = Mock(score=0)
        game.save = Mock()
        game.draw = Mock()
        game.audio = Mock()
        clock = Mock()
        clock.tick.return_value = 16
        with patch.object(sys, 'platform', 'emscripten'), patch('pygame.time.Clock', return_value=clock), \
                patch('pygame.event.get', return_value=[]), patch('pygame.quit'), \
                patch('main.asyncio.sleep', new_callable=AsyncMock) as sleep:
            asyncio.run(game.run_async(frames=3))
        self.assertEqual(game.draw.call_count, 3)
        self.assertEqual(sleep.await_count, 3)
        self.assertEqual(clock.tick.call_args.args, (0,))

    def test_browser_save_roundtrip_in_session_filesystem(self):
        with patch.object(sys, 'platform', 'emscripten'), tempfile.TemporaryDirectory() as directory:
            save = SaveData(Path(directory) / 'save.json')
            save.record(345)
            self.assertEqual(SaveData(save.path).high_score, 345)
            with patch.dict('os.environ', {}, clear=True):
                self.assertEqual(SaveData().path, Path('/tmp/cruelworld/save.json'))

    def test_runtime_manifest_excludes_development_and_sources(self):
        files = runtime_files()
        self.assertTrue(all(p.is_file() for p in files))
        names = [p.as_posix() for p in files]
        self.assertFalse(any('/tests/' in p or '_source/' in p or '/artifacts/' in p or '/Social/' in p for p in names))
        self.assertTrue(any(p.endswith('cruel-world-logo.png') for p in names))
        self.assertTrue(any(p.endswith('/level.py') for p in names))

    def test_loader_uses_packaged_zip_on_localhost(self):
        html = "if platform.window.location.host.find('.itch.zone')>0:\n<body>"
        result = polish_index(html)
        self.assertIn('if True:', result)
        self.assertIn('#100e14', result)
        with self.assertRaises(ValueError):
            polish_index('<body>changed template')

    def test_archive_requires_root_index_and_safe_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'web.zip'
            for names, valid in ((['index.html', 'game.apk'], True),
                                 (['nested/index.html'], False), (['index.html', '../bad'], False)):
                with zipfile.ZipFile(path, 'w') as archive:
                    for name in names:
                        archive.writestr(name, 'data')
                if valid:
                    self.assertEqual(validate_archive(path)['files'], 2)
                else:
                    with self.assertRaises(ValueError):
                        validate_archive(path)
