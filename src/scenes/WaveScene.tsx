import { AbsoluteFill, Easing, interpolate, interpolateColors, useCurrentFrame } from "remotion";
import { audioData } from "../audio-data";
import { COLORS } from "../theme";
import { SCENE } from "../timing";
import { inOut, ramp, Words } from "../util";

// 16-20 s: the real spectrum of the soundtrack, which then flattens into a render
// progress bar, fills by 19.5 s and collapses into a dot on the silent beat before 20 s.
const BANDS = 48;
const STRIDE = 30;
const LEFT = (1920 - BANDS * STRIDE) / 2;
const CY = 540;
const MORPH = SCENE.wave + 60;
const DONE = 585;

const spectrumAt = (frame: number, band: number) => {
  const row = audioData.spectrum[frame - audioData.spectrumStart];
  return row ? row[band] : 0;
};

export const WaveScene: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < SCENE.wave - 8 || frame >= SCENE.end) return null;

  const opacity = ramp(frame, SCENE.wave - 8, SCENE.wave + 4, inOut);
  const textOut = 1 - ramp(frame, MORPH, MORPH + 12, inOut);
  const flat = ramp(frame, MORPH, MORPH + 16, inOut);
  const progress = ramp(frame, MORPH + 12, DONE, Easing.inOut(Easing.quad));
  const collapse = ramp(frame, DONE + 3, SCENE.end, Easing.in(Easing.cubic));
  const barWidth = interpolate(collapse, [0, 1], [BANDS * STRIDE, 28]);
  const barHeight = interpolate(collapse, [0, 1], [14, 28]);

  return (
    <AbsoluteFill style={{ opacity }}>
      <div style={{ position: "absolute", top: 110, left: 0, right: 0, opacity: textOut }}>
        <Words text="Music? Also code." frame={frame} start={SCENE.wave + 8} step={7} size={104} accent={["code."]} />
      </div>

      {flat < 1
        ? Array.from({ length: BANDS }, (_, b) => {
            const grow = ramp(frame, SCENE.wave - 4 + Math.abs(b - (BANDS - 1) / 2) * 0.5, SCENE.wave + 6 + Math.abs(b - (BANDS - 1) / 2) * 0.5);
            const v = spectrumAt(frame, b);
            const h = interpolate(flat, [0, 1], [(12 + v * 470) * grow, 14]);
            const w = interpolate(flat, [0, 1], [18, STRIDE]);
            return (
              <div
                key={b}
                style={{
                  position: "absolute",
                  left: LEFT + b * STRIDE,
                  top: CY - h / 2,
                  width: w,
                  height: h,
                  borderRadius: 9 * (1 - flat),
                  backgroundColor: interpolateColors(flat, [0, 1], [
                    interpolateColors(v, [0, 1], ["rgba(242, 242, 242, 0.35)", COLORS.accent]),
                    COLORS.faint,
                  ]),
                }}
              />
            );
          })
        : null}

      {flat > 0 ? (
        <>
          <div
            style={{
              position: "absolute",
              left: 960 - barWidth / 2,
              top: CY - barHeight / 2,
              width: barWidth,
              height: barHeight,
              borderRadius: barHeight / 2,
              overflow: "hidden",
              backgroundColor: COLORS.faint,
              opacity: flat,
            }}
          >
            <div
              style={{
                width: `${progress * 100}%`,
                height: "100%",
                backgroundColor: COLORS.accent,
                boxShadow: "0 0 24px rgba(255, 107, 74, 0.8)",
              }}
            />
          </div>
          <div
            style={{
              position: "absolute",
              left: LEFT,
              width: BANDS * STRIDE,
              top: CY - 92,
              display: "flex",
              justifyContent: "space-between",
              fontSize: 44,
              opacity: flat * (1 - ramp(frame, DONE, DONE + 8)),
              fontFeatureSettings: '"tnum"',
            }}
          >
            <span>
              <span style={{ color: COLORS.muted }}>rendering </span>out/final.mp4
            </span>
            <span style={{ color: progress >= 1 ? COLORS.accent : COLORS.text }}>{Math.round(progress * 100)}%</span>
          </div>
        </>
      ) : null}

      <div
        style={{
          position: "absolute",
          top: 880,
          left: 0,
          right: 0,
          textAlign: "center",
          fontSize: 32,
          fontWeight: 500,
          color: COLORS.muted,
          opacity: ramp(frame, SCENE.wave + 20, SCENE.wave + 32) * textOut,
        }}
      >
        scripts/music.py <span style={{ color: COLORS.accent }}>→</span> public/music.wav
      </div>
    </AbsoluteFill>
  );
};
