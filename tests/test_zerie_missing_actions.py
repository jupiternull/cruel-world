import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from zerie_missing_actions import (
    ACTION_FRAMES,
    ACTIONS,
    FRAME_SIZE,
    GROUND_Y,
    SCALE,
    action_frames,
    build_missing_actions,
    grounded_frame,
    load_source_frames,
    source_hashes,
)


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / 'assets' / 'vendor' / 'zerie'
EXPECTED_COUNTS = {'Run': 8, 'Jump': 6, 'Fall': 5, 'Land': 5, 'Evade': 8}


class ZerieMissingActionTests(unittest.TestCase):
    def test_frames_are_real_soldier_derivatives_with_expected_dimensions(self):
        actions = action_frames(ASSET_ROOT)

        self.assertEqual(tuple(actions), ACTIONS)
        self.assertEqual({action: len(frames) for action, frames in actions.items()}, EXPECTED_COUNTS)
        for frames in actions.values():
            for frame in frames:
                self.assertEqual(frame.mode, 'RGBA')
                self.assertEqual(frame.size, (FRAME_SIZE, FRAME_SIZE))
                self.assertIsNotNone(frame.getchannel('A').getbbox())

    def test_grounded_source_frame_uses_a_stable_baseline(self):
        source = load_source_frames(ASSET_ROOT)
        for animation, frame_index, _, _ in (entry for frames in ACTION_FRAMES.values() for entry in frames):
            frame = grounded_frame(source[animation][frame_index])
            self.assertEqual(frame.getchannel('A').getbbox()[3], GROUND_Y)

    def test_generation_is_deterministic_and_does_not_change_sources(self):
        before = source_hashes(ASSET_ROOT)
        with tempfile.TemporaryDirectory() as directory:
            first = build_missing_actions(ASSET_ROOT, Path(directory) / 'first')
            second = build_missing_actions(ASSET_ROOT, Path(directory) / 'second')

            self.assertEqual(
                json.loads(first['manifest'].read_text(encoding='utf-8')),
                json.loads(second['manifest'].read_text(encoding='utf-8')),
            )
            for action in ACTIONS:
                self.assertEqual(
                    hashlib.sha256(first['sheets'][action].read_bytes()).hexdigest(),
                    hashlib.sha256(second['sheets'][action].read_bytes()).hexdigest(),
                )
            self.assertEqual(
                hashlib.sha256(first['animated_gif'].read_bytes()).hexdigest(),
                hashlib.sha256(second['animated_gif'].read_bytes()).hexdigest(),
            )
        self.assertEqual(before, source_hashes(ASSET_ROOT))

    def test_outputs_have_valid_sheet_contact_and_gif_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            result = build_missing_actions(ASSET_ROOT, Path(directory))
            for action, path in result['sheets'].items():
                with Image.open(path) as sheet:
                    self.assertEqual(sheet.mode, 'RGBA')
                    self.assertEqual(sheet.size, (FRAME_SIZE * EXPECTED_COUNTS[action], FRAME_SIZE))

            with Image.open(result['contact_sheet']) as contact:
                self.assertEqual(contact.size, (178 + 8 * FRAME_SIZE * SCALE + 32, 70 + (FRAME_SIZE * SCALE + 58) * len(ACTIONS)))

            with Image.open(result['animated_gif']) as gif:
                self.assertEqual(gif.format, 'GIF')
                self.assertEqual(gif.size, (620, 500))
                self.assertEqual(gif.n_frames, sum(EXPECTED_COUNTS.values()))
                self.assertEqual(gif.info['loop'], 0)


if __name__ == '__main__':
    unittest.main()
