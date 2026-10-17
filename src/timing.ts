// Shared timing. Mirrors scripts/music.py: 120 BPM at 30 fps.
export const FPS = 30;
export const BEAT = 15; // frames per beat
export const BAR = 60; // frames per bar (2 s)
export const DURATION = 720; // 24 s

// Scene start frames. Every cut lands on a bar line.
export const SCENE = {
  prompt: 0,
  code: 120,
  frame: 240,
  cards: 360,
  wave: 480,
  end: 600,
} as const;

export const PROMPT = "> make me a video";

// Frame at which character i of PROMPT is typed (one click per 16th note).
export const typedAt = (i: number) => (0.75 + 0.125 * i) * FPS;

// Kick drum plays on every beat from 4 s up to (not including) 19.5 s.
export const KICK_START = 120;
export const KICK_END = 585;

// Smooth 0..1 bump: rises to its peak `rise` frames after a hit, then eases back out.
export const bump = (sinceHit: number, rise = 3) =>
  sinceHit <= 0 ? 0 : (sinceHit / rise) * Math.exp(1 - sinceHit / rise);

// Gentle pulse on each kick.
export const kickPulse = (frame: number) => {
  if (frame < KICK_START || frame >= KICK_END + BEAT) return 0;
  return bump(((frame - KICK_START) % BEAT) + 1, 2.5);
};
