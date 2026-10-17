#!/usr/bin/env python3
"""Synthesize the teaser soundtrack (grand piano, acoustic guitar and flute) using only the
Python standard library.

Writes:
  public/music.wav        stereo 16-bit 44.1 kHz mix (music + sound effects)
  src/audio-data.ts       smoothed per-frame loudness and spectrum the visuals react to

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

L = [0.0] * N
R = [0.0] * N
VERB = [0.0] * N  # mono reverb send


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def mix(samples, t, gain=1.0, pan=0.0, verb=0.0):
    start = int(round(t * SR))
    gl = gain * math.cos((pan + 1) * math.pi / 4)
    gr = gain * math.sin((pan + 1) * math.pi / 4)
    for i, s in enumerate(samples):
        j = start + i
        if j >= N:
            break
        if j < 0:
            continue
        L[j] += s * gl
        R[j] += s * gr
        if verb:
            VERB[j] += s * gain * verb


# -------------------------------------------------------------------- helpers

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


def resonator(x, freq, q):
    """Two-pole resonant band-pass, used for the guitar body."""
    w = 2 * math.pi * freq / SR
    r = math.exp(-w / (2 * q))
    a1, a2 = 2 * r * math.cos(w), -r * r
    out = [0.0] * len(x)
    y1 = y2 = 0.0
    for i, s in enumerate(x):
        y = (1 - r) * s + a1 * y1 + a2 * y2
        y2, y1 = y1, y
        out[i] = y
    return out


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


# ------------------------------------------------------------------ instruments

_piano_cache = {}


def piano(m, length=3.0, vel=0.7):
    """Additive grand piano: stretched (inharmonic) partials, two-stage decay,
    a detuned second string on the low partials, a felt-hammer thump and a damper release."""
    key = (m, round(length, 2), round(vel, 2))
    if key in _piano_cache:
        return _piano_cache[key]
    f = midi(m)
    n = int(length * SR)
    out = [0.0] * n
    sustain = min(7.0, 3.2 * (261.6 / f) ** 0.6)  # low notes ring longer
    inharm = 0.0004 * (f / 261.6) ** 0.5
    brightness = 0.35 + 0.5 * vel
    for k in range(1, 15):
        fk = f * k * math.sqrt(1 + inharm * k * k)
        if fk > 11000:
            break
        ak = (1 / k) * brightness ** (k - 1) * (1.6 if k == 1 else 1.0)
        tau = sustain / (1 + 0.45 * (k - 1))
        for detune, share in ((1.0, 0.6), (1.0007, 0.4)) if k <= 4 else ((1.0, 1.0),):
            w = 2 * math.pi * fk * detune / SR
            c = 2 * math.cos(w)
            ph = random.random() * 2 * math.pi
            y1, y2 = math.sin(ph), math.sin(ph - w)
            fast, slow = 0.65 * ak * share, 0.35 * ak * share
            df, ds = math.exp(-1 / (0.22 * tau * SR)), math.exp(-1 / (tau * SR))
            for i in range(n):
                y = c * y1 - y2
                y2, y1 = y1, y
                out[i] += y * (fast + slow)
                fast *= df
                slow *= ds
                if slow < 1e-5:
                    break
    hammer_n = int(0.02 * SR)
    hammer = lowpass(noise(hammer_n), 600 + 2500 * vel)
    for i in range(hammer_n):
        out[i] += hammer[i] * 0.25 * (1 - i / hammer_n) ** 2
    attack = int(0.002 * SR)
    release = int(0.18 * SR)
    for i in range(attack):
        out[i] *= i / attack
    for i in range(release):
        out[n - 1 - i] *= i / release
    peak = 0.32 * vel
    out = [s * peak for s in out]
    _piano_cache[key] = out
    return out


_guitar_cache = {}


def guitar_string(m, length, vel=0.7):
    """Karplus-Strong steel string with a soft pick, pluck-position comb and a small body."""
    key = (m, round(length, 3), round(vel, 2))
    if key in _guitar_cache:
        return _guitar_cache[key]
    f = midi(m)
    n = int(length * SR)
    period = max(2, int(round(SR / f - 0.5)))  # the averaging filter adds half a sample
    excite = lowpass(noise(period), 1500 + 3500 * vel)
    pos = max(1, int(period * 0.18))
    buf = [excite[i] - 0.8 * excite[i - pos] for i in range(period)]
    rho = 0.9975 - 0.0015 * (f / 440)
    out = [0.0] * n
    prev = 0.0
    for i in range(n):
        j = i % period
        s = buf[j]
        buf[j] = rho * 0.5 * (s + prev)
        prev = s
        out[i] = s
    body = resonator(out, 110, 3)
    body2 = resonator(out, 230, 4)
    out = [0.75 * s + 0.6 * b + 0.4 * c for s, b, c in zip(out, body, body2)]
    mute = int(0.04 * SR)
    for i in range(min(mute, n)):
        out[n - 1 - i] *= i / mute
    out = [s * 0.35 * vel for s in out]
    _guitar_cache[key] = out
    return out


# Open-chord voicings (low string first).
GUITAR = {
    "Am": [45, 52, 57, 60, 64],
    "F": [41, 48, 53, 57, 60, 65],
    "C": [48, 52, 55, 60, 64],
    "G": [43, 47, 50, 55, 59, 67],
}


def strum(name, t, length, vel=0.6, up=False, spread=0.014):
    notes = GUITAR[name][::-1][:4] if up else GUITAR[name]
    for k, m in enumerate(notes):
        mix(guitar_string(m, length, vel * (0.75 if up else 1.0)), t + k * spread, gain=1.0,
            pan=0.35, verb=0.25)


def pick(m, t, length=0.9, vel=0.6, pan=0.35):
    mix(guitar_string(m, length, vel), t, pan=pan, verb=0.3)


def flute(m, length, vel=0.6):
    """Flute: a near-sine tone with a few soft harmonics, breath noise tuned to the note,
    a breathy "chiff" on the attack, a slight pitch scoop and delayed vibrato."""
    f = midi(m)
    n = int(length * SR)
    harmonics = [(1, 1.0), (2, 0.22 + 0.25 * vel), (3, 0.08 + 0.15 * vel), (4, 0.04), (5, 0.015)]
    attack, release = 0.07, min(0.15, length * 0.3)
    vib_rate, vib_depth = 5.1, 0.005
    out = [0.0] * n
    ph = 0.0
    for i in range(n):
        t = i / SR
        vib = min(1.0, max(0.0, (t - 0.22) / 0.35)) * vib_depth
        scoop = -0.006 * math.exp(-t / 0.04)
        ph += 2 * math.pi * f * (1 + scoop + vib * math.sin(2 * math.pi * vib_rate * t)) / SR
        out[i] = sum(a * math.sin(k * ph) for k, a in harmonics)
    breath_tone = resonator(noise(n), f, 8)
    breath_air = highpass(noise(n), 4000)
    gain = 0.22 * vel
    rel_n = int(release * SR)
    for i in range(n):
        t = i / SR
        e = 1 - math.exp(-t / (attack / 3))
        if i > n - rel_n:
            e *= (n - i) / rel_n
        swell = 1 + 0.08 * math.sin(math.pi * min(1.0, t / length))
        chiff = 1.6 * math.exp(-t / 0.05)
        trem = 1 + 0.04 * math.sin(2 * math.pi * vib_rate * t) * min(1.0, max(0.0, (t - 0.22) / 0.35))
        out[i] = (out[i] * swell * trem + 0.8 * breath_tone[i] * (0.3 + chiff) + 0.02 * breath_air[i] * (0.3 + chiff)) * e * gain
    return out


def play_flute(phrase, vel=0.6, pan=-0.05):
    """phrase: (start time, midi note, length) tuples; notes overlap slightly for a legato feel."""
    for t, m, length in phrase:
        mix(flute(m, length + 0.04, vel), t, pan=pan, verb=0.45)


def kick(length=0.4, gain=1.0):
    n = int(length * SR)
    out = [0.0] * n
    ph = 0.0
    for i in range(n):
        t = i / SR
        ph += 2 * math.pi * (48 + 70 * math.exp(-t / 0.035)) / SR
        out[i] = math.sin(ph) * math.exp(-t / 0.22) * gain
    fade = int(0.01 * SR)
    for i in range(fade):
        out[n - 1 - i] *= i / fade
    return out


def click():
    n = int(0.03 * SR)
    blip = [math.sin(2 * math.pi * 2400 * i / SR) * math.exp(-i / (0.004 * SR)) for i in range(n)]
    nz = mul(highpass(noise(n), 3000), env(n, 0.0002, 0.003))
    return [0.5 * b + 0.6 * z for b, z in zip(blip, nz)]


def whoosh(length=0.35):
    n = int(length * SR)
    filt = lowpass(noise(n), lambda i: 300 + 3000 * math.sin(math.pi * i / n))
    return [s * math.sin(math.pi * i / n) ** 2 for i, s in enumerate(filt)]


# -------------------------------------------------------------------- the song
# Bars 0-11. Progression: Am  F  C  G (repeating).
PROG = ["Am", "F", "C", "G"]
PIANO_CHORD = {"Am": [57, 60, 64], "F": [57, 60, 65], "C": [55, 60, 64], "G": [55, 59, 62]}
PIANO_BASS = {"Am": 33, "F": 29, "C": 36, "G": 31}


def name(bar):
    return PROG[bar % 4]


def piano_chord(ch, t, length, vel, roll=0.0, bass=True):
    notes = ([PIANO_BASS[ch], PIANO_BASS[ch] + 12] if bass else []) + PIANO_CHORD[ch]
    for k, m in enumerate(notes):
        mix(piano(m, length, vel), t + k * roll, pan=-0.25 + 0.08 * k, verb=0.35)


# Scene 1 (0-4 s): solo piano, rolled chords; one typing click per character;
# a rising arpeggio leads into the downbeat at 4 s.
piano_chord("Am", 0.0, 2.4, 0.45, roll=0.06)
piano_chord("F", 2.0, 2.2, 0.5, roll=0.05)
for k, m in enumerate([57, 60, 64, 65, 69, 72, 76, 77]):
    mix(piano(m, 1.2, 0.35 + 0.05 * k), 3.0 + k * 0.125, pan=-0.2 + 0.05 * k, verb=0.35)
for i in range(17):  # "> make me a video"
    mix(click(), 0.75 + 0.125 * i, gain=0.25, pan=random.uniform(-0.2, 0.2), verb=0.1)

# Soft kick on every beat from 4 s to 19 s; dropped on the last beat before the impact.
KICKS = [4.0 + BEAT * k for k in range(31)]
for t in KICKS:
    mix(kick(gain=0.55 if t % 1 == 0 else 0.4), t)

# Guitar strumming 4 s - 16 s: pattern D . D U . U D U on 8th notes.
PATTERN = [(0, False), (2, False), (3, True), (5, True), (6, False), (7, True)]
for bar in range(2, 8):
    ch = name(bar)
    quiet = 0.75 if bar in (6, 7) else 1.0  # leave room for the card accents
    for idx, (slot, up) in enumerate(PATTERN):
        t = bar * BAR + slot * BEAT / 2
        nxt = PATTERN[idx + 1][0] if idx + 1 < len(PATTERN) else 8
        length = (nxt - slot) * BEAT / 2 + 0.05
        strum(ch, t, length, vel=(0.55 if slot % 4 == 0 else 0.42) * quiet, up=up)

# Piano: chord on each bar 4-8 s, melody on each of the 8 keyframe beats 8-12 s.
for bar in (2, 3):
    piano_chord(name(bar), bar * BAR, 2.2, 0.5, roll=0.02)
MELODY_A = [69, 72, 76, 81, 72, 77, 81, 79]
for k, m in enumerate(MELODY_A):
    mix(piano(m, 1.6, 0.7), 8.0 + BEAT * k, pan=-0.15, verb=0.4)
for bar in (4, 5):
    piano_chord(name(bar), bar * BAR, 2.2, 0.35, roll=0.02)

# Scene 4 (12-16 s): one forte piano accent per card at 12, 13 and 14 s; a strum fill into 16 s.
for t, ch in ((12.0, "C"), (13.0, "C"), (14.0, "G")):
    mix(whoosh(), t - 0.3, gain=0.25, verb=0.2)
    piano_chord(ch, t, 1.4 if t < 14 else 1.9, 0.85, roll=0.01)
for k, t in enumerate((15.5, 15.625, 15.75, 15.875)):
    strum("G", t, 0.14, vel=0.45 + 0.08 * k, up=k % 2 == 1, spread=0.008)

# Scene 5 (16-19.5 s): fingerpicked 16ths on guitar, piano chords and melody.
PICK_ORDER = [0, 2, 3, 4, 3, 2, 4, 3]
for bar in (8, 9):
    voicing = GUITAR[name(bar)]
    for step in range(16):
        t = bar * BAR + step * 0.125
        if t >= 19.5:
            break
        pick(voicing[PICK_ORDER[step % 8] % len(voicing)], t, length=0.7, vel=0.5 + 0.1 * (step % 4 == 0),
             pan=0.4 if step % 2 else 0.25)
    piano_chord(name(bar), bar * BAR, 1.9 if bar == 8 else 1.45, 0.55, roll=0.015)
MELODY_B = [(16.0, 76), (16.5, 74), (17.0, 72), (17.5, 76), (18.0, 77), (18.5, 76), (19.0, 72)]
for t, m in MELODY_B:
    mix(piano(m, 1.0 if t == 19.0 else 0.9, 0.75), t, pan=-0.15, verb=0.4)

# Flute: a phrase over the code scene, long notes under the keyframe melody, a run into
# 16 s, a counter-melody to the end of the groove and a held note over the final chord.
play_flute([(4.0, 79, 1.0), (5.0, 76, 0.5), (5.5, 74, 0.5), (6.0, 74, 1.25), (7.25, 71, 0.25), (7.5, 72, 0.5)])
play_flute([(8.0, 76, 1.95), (10.0, 77, 1.95)], vel=0.4)
play_flute([(15.0 + 0.125 * k, m, 0.125) for k, m in enumerate([69, 71, 72, 74, 76, 77, 79, 81])], vel=0.5)
play_flute([(16.0, 81, 1.0), (17.0, 79, 1.0), (18.0, 81, 0.5), (18.5, 79, 0.5), (19.0, 76, 0.42)], vel=0.65)
play_flute([(20.15, 81, 3.6)], vel=0.55)

# Scene 6 (20 s): impact. Low piano octaves fortissimo, full A minor chord and a big strum,
# all ringing out to silence.
mix(kick(length=1.8, gain=0.9), 20.0)
for m in (21, 33, 45):
    mix(piano(m, 4.0, 1.0), 20.0, gain=1.1, pan=-0.2, verb=0.5)
for k, m in enumerate([57, 60, 64, 69, 72, 76]):
    mix(piano(m, 4.0, 0.9), 20.0 + k * 0.012, pan=-0.1 + 0.05 * k, verb=0.5)
strum("Am", 20.0, 4.0, vel=0.8, spread=0.02)


# ------------------------------------------------------------ reverb + master

def reverb(x):
    """Small Schroeder reverb: 4 damped combs into 2 allpasses."""
    def comb(sig, d, fb=0.84, damp=0.3):
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


wl, wr = reverb(VERB)
out_l = [0.0] * N
out_r = [0.0] * N
fade_n = int(0.5 * SR)
for i in range(N):
    g = 1.0 if i < N - fade_n else (N - i) / fade_n
    out_l[i] = math.tanh((L[i] + 0.35 * wl[i]) * 1.2) * g
    out_r[i] = math.tanh((R[i] + 0.35 * wr[i]) * 1.2) * g

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

def follow(values, attack, release):
    """Envelope follower so visuals rise and fall smoothly instead of flickering per frame."""
    out = []
    level = values[0]
    for v in values:
        level += (v - level) * (attack if v > level else release)
        out.append(level)
    return out


mono = [(a + b) * 0.5 for a, b in zip(out_l, out_r)]
hop = SR // FPS
total_frames = int(DUR * FPS)

rms = []
for f in range(total_frames):
    seg = mono[f * hop:(f + 1) * hop]
    rms.append(math.sqrt(sum(v * v for v in seg) / len(seg)))
rms = follow(rms, attack=0.35, release=0.08)
top = max(rms)
rms = [round(v / top, 3) for v in rms]

# Spectrum for the waveform scene (frames 470-610): Goertzel at log-spaced bands.
SPEC_START, SPEC_END, BANDS, WIN = 470, 610, 48, 2048
freqs = [80 * (6000 / 80) ** (b / (BANDS - 1)) for b in range(BANDS)]
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
    [min(1.0, max(0.0, (v - band_hi[b] + RANGE_DB) / RANGE_DB)) for b, v in enumerate(r)]
    for r in spec_db
]
# Single-frequency bands miss notes that fall between them; borrow a little from neighbours.
spectrum = [
    [max(r[b], 0.4 * (r[max(0, b - 1)] + r[min(BANDS - 1, b + 1)])) for b in range(BANDS)]
    for r in spectrum
]
# Smooth each band over time.
columns = [follow([r[b] for r in spectrum], attack=0.22, release=0.1) for b in range(BANDS)]
spectrum = [[round(columns[b][f], 3) for b in range(BANDS)] for f in range(len(spectrum))]

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
