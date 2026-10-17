# vidcode

A 24-second, 1920×1080 teaser made entirely from code with [Remotion](https://remotion.dev).

- `src/Teaser.tsx` – the composition; scenes live in `src/scenes/`
- `src/timing.ts` – shared timing (120 BPM, 30 fps, cuts on bar lines)
- `scripts/music.py` – synthesizes `public/music.wav` and `src/audio-data.ts` (Python standard library only)
- `public/fonts/` – Inter (SIL OFL, see `INTER-LICENSE.txt`)

```console
npm install
python3 scripts/music.py   # regenerate the soundtrack and audio data
npm run dev                # preview in Remotion Studio
npx remotion render src/index.ts Teaser out/final.mp4
```
