"""Compose original Cinder Dominion scores with deterministic stdlib synthesis.

32 bars at 80 BPM and 48 bars at 128 BPM. All voices, percussion and
arrangements are authored here; no external samples. Reverb wraps around the
score so the final beat's decay continues under the first beat on replay.
"""
from array import array
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parent
RATE = 32000
TRACKS = ('underworld_exploration', 'pyre_regent')
TAU = 2 * math.pi


def frequency(note):
    return 440 * 2 ** ((note - 69) / 12)


def voice(kind, note, duration, seed):
    rng = random.Random(seed)
    result = array('f')
    phase = 0
    filtered = 0
    for i in range(round(duration * RATE)):
        t = i / RATE
        end = min(1, (duration - t) / .08)
        if kind in ('kick', 'tom'):
            f = (44 if kind == 'kick' else frequency(note)) + 95 * math.exp(-t * 32)
            phase += TAU * f / RATE
            value = math.sin(phase) * math.exp(-t * (9 if kind == 'kick' else 5))
            value += rng.uniform(-1, 1) * .18 * math.exp(-t * 90)
        elif kind in ('snare', 'metal'):
            noise = rng.uniform(-1, 1)
            filtered = .65 * filtered + .35 * noise
            value = (noise - filtered) * math.exp(-t * (17 if kind == 'snare' else 30))
            value += .3 * math.sin(TAU * (185 if kind == 'snare' else 1723) * t) * math.exp(-t * 20)
        else:
            f = frequency(note)
            attack = min(1, t / (.06 if kind == 'pad' else .012))
            envelope = attack * end * math.exp(-t * (1.1 if kind == 'pad' else 3.2 if kind == 'bell' else 4))
            if kind == 'stab':
                # Saturated harmonic brass, bounded before mixing; no noise bed.
                tone = sum(math.sin(TAU * f * h * t) / h for h in (1, 2, 3, 4, 5, 7))
                value = math.tanh(tone * 1.8) * envelope
            elif kind == 'bell':
                value = (math.sin(TAU * f * t) + .3 * math.sin(TAU * f * 2.01 * t) + .12 * math.sin(TAU * f * 3.98 * t)) * envelope
            else:
                value = (math.sin(TAU * f * t) + .22 * math.sin(TAU * f * 2 * t) + .08 * math.sin(TAU * f * 3 * t)) * envelope
        # A short attack avoids a discontinuity even for drums on loop beat one.
        result.append(value * end * min(1, t / .003))
    return result


def compose(boss):
    beat = 60 / (128 if boss else 80)
    bars = 48 if boss else 32
    count = round(bars * 4 * beat * RATE)
    left, right = array('f', [0]) * count, array('f', [0]) * count
    cache = {}
    rng = random.Random(90713 if boss else 41982)

    def add(kind, note, at, length, gain, pan=0):
        key = (kind, note, length)
        if key not in cache:
            cache[key] = voice(kind, note, length, rng.randrange(2 ** 32))
        start = round(at * beat * RATE)
        lg, rg = gain * math.sqrt((1 - pan) / 2), gain * math.sqrt((1 + pan) / 2)
        for i, value in enumerate(cache[key]):
            j = (start + i) % count
            left[j] += value * lg
            right[j] += value * rg

    roots = (26, 26, 27, 26, 29, 26, 25, 26)
    for bar in range(bars):
        at = bar * 4
        root = roots[(bar // 2) % len(roots)]
        section = (bar // 8) % (6 if boss else 4)
        add('pad', root, at, beat * 6, .25 if boss else .19, -.25)
        add('pad', root + 7, at + 2, beat * 5, .08, .4)
        for offset in ((0, 1.5, 2, 3.5) if boss else (0, 2.5)):
            add('kick', 0, at + offset, .65, .52 if boss else .3)
        for offset in ((1, 3) if boss else (3,)):
            add('snare' if boss else 'tom', 43, at + offset, .8, .32 if boss else .18, .15)
        for step in range(8 if boss else 4):
            if not boss and (step + bar) % 3:
                continue
            add('metal', 0, at + step * (.5 if boss else 1), .2, .065 if boss else .035, -.55 if step % 2 else .55)
        if boss:
            for offset, interval in ((0, 0), (.75, 0), (1.5, 1), (2.5, 0), (3.25, 6)):
                add('stab', root + interval, at + offset, .42, .3)
            if section in (1, 2, 3, 4):
                for offset, interval in ((.5, 12), (2, 13), (3, 18)):
                    add('stab', root + interval, at + offset, .55, .13, -.3)
            if section in (2, 3, 4) and bar % 2 == 0:
                for offset, note in enumerate((62, 63, 68, 65)):
                    add('bell', note, at + offset * .75, 1.1, .12, .35)
            if section == 4:
                add('tom', 45, at + 2.75, .6, .23, -.4)
                add('tom', 40, at + 3.75, .6, .23, .4)
        else:
            add('pad', root + 12, at + 1.5, beat * 2, .065, .2)
            if bar % 2 == 0 and section != 3:
                motif = ((62, 63, 69), (65, 63, 62), (62, 68, 63), (60, 63, 62))[(bar // 2) % 4]
                for offset, note in zip((.5, 2, 3.25), motif):
                    add('bell', note, at + offset, 2.7, .105, -.35 if bar % 4 else .35)
            if section == 2:
                add('tom', 38, at + 1.75, .9, .13, -.4)
    # Cycle-quantized low drones preserve oscillator phase at the loop boundary.
    duration = count / RATE
    for i in range(count):
        drone = .035 * math.sin(TAU * round(frequency(26) * duration) * i / count)
        left[i] += drone
        right[i] += drone
    dry_l, dry_r = left[:], right[:]
    for delay, gain in ((.281, .16), (.563, .09), (.937, .055)):
        shift = round(delay * RATE)
        for i in range(count):
            left[i] += dry_r[(i - shift) % count] * gain
            right[i] += dry_l[(i - shift) % count] * gain
    # Remove DC and normalize with ample Vorbis reconstruction headroom.
    means = (sum(left) / count, sum(right) / count)
    peak = max(max(abs(v - mean) for v in channel) for channel, mean in zip((left, right), means))
    scale = .72 / peak
    pcm = array('h')
    for l, r in zip(left, right):
        pcm.append(round((l - means[0]) * scale * 32767))
        pcm.append(round((r - means[1]) * scale * 32767))
    if sys.byteorder != 'little':
        pcm.byteswap()
    return pcm, duration


def build():
    temporary = ROOT / 'artifacts/tmp/underworld_audio'
    destination = ROOT / 'assets/audio/tommusic/music'
    temporary.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    for boss, name in enumerate(TRACKS):
        pcm, duration = compose(bool(boss))
        wav = temporary / (name + '.wav')
        with wave.open(str(wav), 'wb') as stream:
            stream.setparams((2, 2, RATE, 0, 'NONE', 'not compressed'))
            stream.writeframes(pcm.tobytes())
        output = destination / (name + '.ogg')
        subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-i', str(wav),
                        '-fflags', '+bitexact', '-flags:a', '+bitexact',
                        '-c:a', 'libvorbis', '-q:a', '4', '-map_metadata', '-1',
                        '-metadata', 'title=' + name, '-metadata', 'artist=Cruel World procedural score',
                        str(output)], check=True)
        print(json.dumps({'track': name, 'duration': duration, 'rate': RATE,
                          'channels': 2, 'pcm_peak': .72, 'bytes': output.stat().st_size}), flush=True)


if __name__ == '__main__':
    build()
