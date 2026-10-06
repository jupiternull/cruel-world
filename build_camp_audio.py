"""Rebuild original periodic lute-like music and quiet courtyard texture (stdlib)."""
import math
import random
import struct
import wave
from pathlib import Path

RATE = 22050
DURATION = 16


def samples(kind):
    count = RATE * DURATION
    output = [0.0] * count
    rng = random.Random(419)
    if kind == 'music':
        notes = [146.832, 174.614, 220, 196, 146.832, 130.813, 174.614, 164.814]
        for beat in range(32):
            frequency = notes[beat // 4] * (2 if beat % 4 in (1,3) else 1)
            for n in range(RATE * 2):
                t = n / RATE
                envelope = min(1,t*100) * math.exp(-t*3.8)
                tone = sum(math.sin(2*math.pi*frequency*h*t)/(h*h) for h in (1,2,3,4))
                output[(beat*RATE//2+n)%count] += tone*envelope*0.12
        for n in range(count):
            t = n/RATE
            # Integer cycle counts guarantee the quiet drone wraps continuously.
            output[n] += 0.025*math.sin(2*math.pi*1176*t/DURATION) + 0.015*math.sin(2*math.pi*1760*t/DURATION)
    elif kind == 'interior':
        # Periodic wood resonances and restrained lantern hiss, no exterior voices.
        for n in range(count):
            t = n / RATE
            output[n] = rng.uniform(-1,1)*0.009 + 0.009*math.sin(2*math.pi*624*t/DURATION)
        for beat in (1,5,10,14):
            for n in range(RATE):
                t = n / RATE
                output[(beat*RATE+n)%count] += 0.024*math.sin(2*math.pi*83*t)*math.sin(math.pi*t)**2*math.exp(-t*3)
        span = RATE//4
        for n in range(span):
            a = n/span
            output[n] = output[count-span+n]*(1-a)+output[n]*a
    else:
        filtered = 0
        noise = [rng.uniform(-1,1) for _ in range(count)]
        for n in range(count*2):
            filtered = filtered*0.96 + noise[n%count]*0.04
            if n >= count:
                t = (n-count)/RATE
                output[n-count] = filtered*0.16 + 0.005*math.sin(2*math.pi*48*t/DURATION)
        for beat in (2,7,11,14):
            for n in range(RATE//3):
                t=n/RATE
                output[(beat*RATE+n)%count] += 0.013*math.exp(-t*22)*(math.sin(2*math.pi*660*t)+0.4*math.sin(2*math.pi*1030*t))
        # Crossfade the cyclic noise seam without a silence dip.
        span=RATE//4
        for n in range(span):
            a=n/span
            output[n] = output[count-span+n]*(1-a)+output[n]*a
    return b''.join(struct.pack('<h',max(-32767,min(32767,round(v*32767)))) for v in output)


def build(directory=Path('assets/audio/camp')):
    directory.mkdir(parents=True,exist_ok=True)
    for kind in ('music','ambience','interior'):
        with wave.open(str(directory / (kind+'.wav')),'wb') as stream:
            stream.setparams((1,2,RATE,0,'NONE','not compressed'))
            stream.writeframes(samples(kind))


if __name__ == '__main__':
    build()
