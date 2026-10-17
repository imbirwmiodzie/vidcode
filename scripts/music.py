#!/usr/bin/env python3
"""Synthesize the teaser soundtrack using only the Python standard library.

Writes:
  public/music.wav        stereo 16-bit 44.1 kHz mix (music + sound effects)
  src/audio-data.ts       per-frame loudness and a small spectrum the visuals react to

Timing mirrors src/timing.ts: 120 BPM, 30 fps, one beat = 0.5 s = 15 frames,
one bar = 2 s = 60 frames. Scene cuts land on bar lines (4, 8, 12, 16, 20 s).
"""
import math
import os
import random
import struct
import wave

SR = 44100
FPS = 30
BEAT = 0.5
BAR = 2.0
DUR = 24.0
N = int(SR * DUR)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

random.seed(7)

# Buses: drums/sfx are dry, "duck" is side-chained to the kick, VERB is a mono reverb send.
L = [0.0] * N
R = [0.0] * N
DL = [0.0] * N
DR = [0.0] * N
VERB = [0.0] * N


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def mix(samples, t, gain=1.0, pan=0.0, verb=0.0, duck=False):
    start = int(round(t * SR))
    gl = gain * math.cos((pan + 1) * math.pi / 4)
    gr = gain * math.sin((pan + 1) * math.pi / 4)
    bl, br = (DL, DR) if duck else (L, R)
    for i, s in enumerate(samples):
        j = start + i
        if j >= N:
            break
        if j < 0:
            continue
        bl[j] += s * gl
        br[j] += s * gr
        if verb:
            VERB[j] += s * gain * verb


# ---------------------------------------------------------------- oscillators

TABLE = 2048
SAW = [sum(math.sin(2 * math.pi * k * i / TABLE) / k for k in range(1, 24)) * 0.55 for i in range(TABLE)]
SQUARE = [sum(math.sin(2 * math.pi * k * i / TABLE) / k for k in range(1, 24, 2)) * 0.7 for i in range(TABLE)]


def osc(freq, n, table=SAW):
    out = [0.0] * n
    ph = random.random() * TABLE
    inc = freq * TABLE / SR
    for i in range(n):
        out[i] = table[int(ph)]
        ph += inc
        if ph >= TABLE:
            ph -= TABLE
    return out


def lowpass(x, cutoff):
    """One-pole low-pass; cutoff may be a number or a function of sample index."""
    out = [0.0] * len(x)
    y = 0.0
    fixed = not callable(cutoff)
    a = 1 - math.exp(-2 * math.pi * cutoff / SR) if fixed else 0.0
    for i, s in enumerate(x):
        if not fixed and i % 32 == 0:
            a = 1 - math.exp(-2 * math.pi * cutoff(i) / SR)
        y += a * (s - y)
        out[i] = y
    return out


def highpass(x, cutoff):
    lp = lowpass(x, cutoff)
    return [s - l for s, l in zip(x, lp)]


def noise(n):
    return [random.uniform(-1, 1) for _ in range(n)]


def env(n, attack, decay_tau, hold=0.0):
    a = max(1, int(attack * SR))
    h = int(hold * SR)
    out = [0.0] * n
    for i in range(n):
        if i < a:
            out[i] = i / a
        elif i < a + h:
            out[i] = 1.0
        else:
            out[i] = math.exp(-(i - a - h) / (decay_tau * SR))
    return out


def mul(x, y):
    return [a * b for a, b in zip(x, y)]


# --------------------------------------------------------------------- voices

def kick(length=0.45, f_hi=110, f_lo=45, sweep=0.04, tau=0.28):
    n = int(length * SR)
    out = [0.0] * n
    ph = 0.0
    for i in range(n):
        t = i / SR
        f = f_lo + f_hi * math.exp(-t / sweep)
        ph += 2 * math.pi * f / SR
        out[i] = math.sin(ph) * math.exp(-t / tau)
        if i < 90:  # beater click
            out[i] += random.uniform(-1, 1) * 0.3 * (1 - i / 90)
    fade = int(0.01 * SR)
    for i in range(fade):
        out[n - 1 - i] *= i / fade
    return out


def snare(length=0.3, tone=185, tau=0.09, bright=1800):
    n = int(length * SR)
    body = [math.sin(2 * math.pi * tone * i / SR) * math.exp(-i / (0.05 * SR)) for i in range(n)]
    nz = mul(highpass(noise(n), bright), env(n, 0.001, tau))
    return [0.6 * b + 0.8 * z for b, z in zip(body, nz)]


def hat(length=0.08, tau=0.025):
    n = int(length * SR)
    return mul(highpass(noise(n), 7000), env(n, 0.0005, tau))


def pluck(freq, length=1.4, damping=0.996):
    """Karplus-Strong string."""
    n = int(length * SR)
    period = max(2, int(SR / freq))
    buf = [random.uniform(-1, 1) for _ in range(period)]
    out = [0.0] * n
    for i in range(n):
        s = buf[i % period]
        nxt = buf[(i + 1) % period]
        buf[i % period] = damping * 0.5 * (s + nxt)
        out[i] = s
    return lowpass(out, 5000)


def click():
    n = int(0.03 * SR)
    blip = [math.sin(2 * math.pi * 2400 * i / SR) * math.exp(-i / (0.004 * SR)) for i in range(n)]
    nz = mul(highpass(noise(n), 3000), env(n, 0.0002, 0.003))
    return [0.5 * b + 0.6 * z for b, z in zip(blip, nz)]


def riser(length, f0=200, f1=8000):
    n = int(length * SR)
    nz = noise(n)
    filt = lowpass(nz, lambda i: f0 * (f1 / f0) ** (i / n))
    return [s * (i / n) ** 2 for i, s in enumerate(filt)]


def whoosh(length=0.3):
    n = int(length * SR)
    filt = lowpass(noise(n), lambda i: 400 + 5000 * math.sin(math.pi * i / n))
    return [s * math.sin(math.pi * i / n) ** 2 for i, s in enumerate(filt)]


def pad_chord(notes, length, attack, release, cutoff, detune=0.004):
    n = int(length * SR)
    acc = [0.0] * n
    for m in notes:
        for d in (-detune, detune):
            for i, s in enumerate(osc(midi(m) * (1 + d), n)):
                acc[i] += s
    acc = lowpass(acc, cutoff)
    a, r = int(attack * SR), int(release * SR)
    for i in range(n):
        g = min(1.0, i / a) if a else 1.0
        if i > n - r:
            g *= (n - i) / r
        acc[i] *= g / (2 * len(notes))
    return acc


# ------------------------------------------------------------------- the song
# Bars 0-11. Progression: Am  F  C  G (repeating).
CHORDS = [
    ([57, 60, 64], 45),  # Am, bass A2
    ([57, 60, 65], 41),  # F,  bass F2
    ([55, 60, 64], 48),  # C,  bass C3
    ([55, 59, 62], 43),  # G,  bass G2
]


def chord(bar):
    return CHORDS[bar % 4]


# Scene 1 (0-4 s): pad swells in, filter opening; typing clicks; riser into the drop.
for bar in range(0, 10):
    notes, _ = chord(bar)
    t0 = bar * BAR
    if bar < 2:
        seg = pad_chord(notes, BAR + 0.4, attack=1.2 if bar == 0 else 0.1, release=0.4,
                        cutoff=lambda i, b=bar: 300 + 1300 * min(1.0, (b * BAR + i / SR) / 4.0))
        mix(seg, t0, gain=0.5 + 0.15 * bar, verb=0.3, duck=True)
    else:
        seg = pad_chord(notes, BAR + 0.4, attack=0.05, release=0.4, cutoff=1600)
        mix(seg, t0, gain=0.42 if bar < 9 else 0.3, verb=0.3, duck=True)

for i in range(17):  # one click per typed character: "> make me a video"
    mix(click(), 0.75 + 0.125 * i, gain=0.35, pan=random.uniform(-0.2, 0.2), verb=0.15)

mix(riser(1.25), 2.75, gain=0.25, verb=0.2)

# Kick on every beat from 4 s to 19 s; dropped on the last beat before the impact.
KICKS = [4.0 + BEAT * k for k in range(31)]
for t in KICKS:
    mix(kick(), t, gain=0.95)

# Bass: 8th notes, root/octave pattern plus a sine sub, 4 s - 19.5 s.
for bar in range(2, 10):
    _, root = chord(bar)
    for step in range(8):
        t = bar * BAR + step * BEAT / 2
        if t >= 19.5:
            break
        m = root + (12 if step in (2, 5, 7) else 0)
        n = int(0.24 * SR)
        tone = lowpass(osc(midi(m), n), 900)
        sub = [math.sin(2 * math.pi * midi(root - 12) * i / SR) for i in range(n)]
        e = env(n, 0.004, 0.09, hold=0.06)
        mix(mul([0.7 * a + 0.5 * b for a, b in zip(tone, sub)], e), t, gain=0.55, duck=True)

# Scene 3 (8-12 s): hi-hats on the off-beats, a pluck on each of the 8 keyframe beats.
for k in range(23):
    t = 8.0 + BEAT * k + BEAT / 2
    if t < 19.5:
        mix(hat(), t, gain=0.35, pan=0.3)
PLUCK_NOTES = [69, 72, 76, 81, 65, 69, 72, 77]  # Am arpeggio, then F
for k, m in enumerate(PLUCK_NOTES):
    mix(pluck(midi(m)), 8.0 + BEAT * k, gain=0.5, pan=-0.35 + 0.1 * k, verb=0.35)

# Scene 4 (12-16 s): one snare + whoosh per card at 12, 13, 14 s; a roll into 16 s.
for t in (12.0, 13.0, 14.0):
    mix(whoosh(), t - 0.28, gain=0.35, verb=0.2)
    mix(snare(), t, gain=0.7, verb=0.35)
for k, t in enumerate((15.5, 15.625, 15.75, 15.875)):
    mix(snare(length=0.15), t, gain=0.3 + 0.1 * k, verb=0.2)

# Scene 5 (16-19.5 s): backbeat snare, extra 16th hats, 16th-note arpeggio.
for t in (16.5, 17.5, 18.5):
    mix(snare(), t, gain=0.6, verb=0.3)
for k in range(14):
    t = 16.0 + 0.25 * k
    mix(hat(tau=0.015), t, gain=0.15, pan=-0.3)
ARP = {8: [69, 72, 76, 81, 84, 81, 76, 72], 9: [65, 69, 72, 77, 81, 77, 72, 69]}
for bar in (8, 9):
    for step in range(16):
        t = bar * BAR + step * 0.125
        if t >= 19.5:
            break
        m = ARP[bar][step % 8]
        n = int(0.16 * SR)
        tone = lowpass(osc(midi(m), n, SQUARE), 3200)
        mix(mul(tone, env(n, 0.002, 0.05)), t, gain=0.18, pan=0.4 if step % 2 else -0.4, verb=0.3, duck=True)
mix(riser(1.0, f0=300, f1=10000), 18.5, gain=0.3, verb=0.2)

# Scene 6 (20 s): impact. Sub boom, noise crash, bright Am chord ringing out to silence.
mix(kick(length=2.5, f_hi=90, f_lo=32, sweep=0.12, tau=0.9), 20.0, gain=1.0)
n = int(3.5 * SR)
mix(mul(highpass(noise(n), 2500), env(n, 0.001, 0.7)), 20.0, gain=0.35, verb=0.5)
stab = pad_chord([45, 57, 60, 64, 69, 72, 76], 4.0, attack=0.005, release=1.5,
                 cutoff=lambda i: 600 + 4000 * math.exp(-i / (0.8 * SR)))
mix(stab, 20.0, gain=1.1, verb=0.5)


# ------------------------------------------------------------- reverb + master

def reverb(x):
    """Small Schroeder reverb: 4 damped combs into 2 allpasses."""
    def comb(sig, d, fb=0.8, damp=0.25):
        buf = [0.0] * d
        out = [0.0] * len(sig)
        y = 0.0
        for i, s in enumerate(sig):
            o = buf[i % d]
            y = o * (1 - damp) + y * damp
            buf[i % d] = s + y * fb
            out[i] = o
        return out

    def allpass(sig, d, g=0.5):
        buf = [0.0] * d
        out = [0.0] * len(sig)
        for i, s in enumerate(sig):
            o = buf[i % d]
            buf[i % d] = s + o * g
            out[i] = o - s * g
        return out

    def chain(offset):
        acc = [0.0] * len(x)
        for d in (1557, 1617, 1491, 1422):
            for i, v in enumerate(comb(x, d + offset)):
                acc[i] += v * 0.25
        return allpass(allpass(acc, 225 + offset), 556 + offset)

    return chain(0), chain(23)


def duck_gain():
    g = [1.0] * N
    for t in KICKS:
        s = int(t * SR)
        for i in range(int(0.3 * SR)):
            if s + i < N:
                g[s + i] = min(g[s + i], 1 - 0.55 * math.exp(-i / (0.07 * SR)))
    return g


wl, wr = reverb(VERB)
dg = duck_gain()
out_l = [0.0] * N
out_r = [0.0] * N
fade_n = int(0.5 * SR)
for i in range(N):
    g = 1.0 if i < N - fade_n else (N - i) / fade_n
    out_l[i] = math.tanh((L[i] + DL[i] * dg[i] + 0.3 * wl[i]) * 0.9) * g
    out_r[i] = math.tanh((R[i] + DR[i] * dg[i] + 0.3 * wr[i]) * 0.9) * g

peak = max(max(abs(v) for v in out_l), max(abs(v) for v in out_r))
norm = 0.89 / peak
out_l = [v * norm for v in out_l]
out_r = [v * norm for v in out_r]

wav_path = os.path.join(ROOT, "public", "music.wav")
with wave.open(wav_path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    frames = bytearray()
    for a, b in zip(out_l, out_r):
        frames += struct.pack("<hh", int(a * 32767), int(b * 32767))
    w.writeframes(bytes(frames))


# ---------------------------------------------------- data for the visuals

mono = [(a + b) * 0.5 for a, b in zip(out_l, out_r)]
hop = SR // FPS
total_frames = int(DUR * FPS)

rms = []
for f in range(total_frames):
    seg = mono[f * hop:(f + 1) * hop]
    rms.append(math.sqrt(sum(v * v for v in seg) / len(seg)))
top = max(rms)
rms = [round(v / top, 3) for v in rms]

# Spectrum for the waveform scene (frames 470-610): Goertzel at log-spaced bands.
SPEC_START, SPEC_END, BANDS, WIN = 470, 610, 48, 2048
freqs = [60 * (8000 / 60) ** (b / (BANDS - 1)) for b in range(BANDS)]
window = [0.5 - 0.5 * math.cos(2 * math.pi * i / (WIN - 1)) for i in range(WIN)]
spec_db = []
for f in range(SPEC_START, SPEC_END):
    start = max(0, f * hop - WIN // 2)
    seg = [v * w for v, w in zip(mono[start:start + WIN], window)]
    row = []
    for fr in freqs:
        coeff = 2 * math.cos(2 * math.pi * fr / SR)
        s1 = s2 = 0.0
        for v in seg:
            s0 = v + coeff * s1 - s2
            s2, s1 = s1, s0
        power = s1 * s1 + s2 * s2 - coeff * s1 * s2
        row.append(10 * math.log10(power + 1e-9))
    spec_db.append(row)
# Normalize each band to its own peak so high bands move as much as the bass.
band_hi = [max(r[b] for r in spec_db) for b in range(BANDS)]
RANGE_DB = 36
spectrum = [
    [round(min(1.0, max(0.0, (v - band_hi[b] + RANGE_DB) / RANGE_DB)), 3) for b, v in enumerate(r)]
    for r in spec_db
]
# Single-frequency bands miss notes that fall between them; borrow a little from neighbours.
spectrum = [
    [round(max(r[b], 0.4 * (r[max(0, b - 1)] + r[min(BANDS - 1, b + 1)])), 3) for b in range(BANDS)]
    for r in spectrum
]

ts_path = os.path.join(ROOT, "src", "audio-data.ts")
with open(ts_path, "w") as fh:
    fh.write("// Generated by scripts/music.py. Do not edit by hand.\n")
    fh.write("export const audioData = {\n")
    fh.write(f"  rms: {rms},\n")
    fh.write(f"  spectrumStart: {SPEC_START},\n")
    fh.write("  spectrum: [\n")
    for r in spectrum:
        fh.write(f"    {r},\n")
    fh.write("  ],\n};\n")

print(f"wrote {wav_path} ({DUR:.0f} s) and {ts_path}")
