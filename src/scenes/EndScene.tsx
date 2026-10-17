import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { audioData } from "../audio-data";
import { COLORS } from "../theme";
import { SCENE } from "../timing";
import { ramp } from "../util";

// 20-24 s: the dot left by the progress bar bursts on the impact into the end card.
const TITLE = ["Claude", "+", "Remotion"];

export const EndScene: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < SCENE.end) return null;

  const t = frame - SCENE.end;
  const ring = ramp(frame, SCENE.end, SCENE.end + 40);
  const dot = 1 - ramp(frame, SCENE.end, SCENE.end + 8);
  const zoom = interpolate(t, [0, 120], [1, 1.06]);
  const level = audioData.rms[frame] ?? 0;

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 50%, rgba(255, 107, 74, ${0.08 + 0.3 * level}) 0%, transparent 45%)`,
        }}
      />
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <circle cx={960} cy={540} r={14 * dot} fill={COLORS.accent} />
        <circle
          cx={960}
          cy={540}
          r={14 + 1300 * ring}
          fill="none"
          stroke={COLORS.accent}
          strokeWidth={10 * (1 - ring) + 1}
          opacity={1 - ring}
        />
        <circle
          cx={960}
          cy={540}
          r={14 + 800 * ramp(frame, SCENE.end + 3, SCENE.end + 45)}
          fill="none"
          stroke={COLORS.text}
          strokeWidth={2}
          opacity={0.4 * (1 - ramp(frame, SCENE.end + 3, SCENE.end + 45))}
        />
      </svg>

      <div style={{ transform: `scale(${zoom})`, textAlign: "center" }}>
        <div style={{ display: "flex", gap: 40, fontSize: 156, fontWeight: 800, letterSpacing: "-0.04em" }}>
          {TITLE.map((word, i) => {
            const p = ramp(frame, SCENE.end + 2 + i * 4, SCENE.end + 22 + i * 4);
            return (
              <span
                key={word}
                style={{
                  display: "inline-block",
                  color: word === "+" ? COLORS.accent : COLORS.text,
                  opacity: p,
                  transform: `scale(${1.35 - 0.35 * p})`,
                  filter: `blur(${(1 - p) * 16}px)`,
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
        <div
          style={{
            marginTop: 24,
            fontSize: 46,
            fontWeight: 500,
            color: COLORS.muted,
            letterSpacing: "0.02em",
            opacity: ramp(frame, SCENE.end + 30, SCENE.end + 45),
            transform: `translateY(${(1 - ramp(frame, SCENE.end + 30, SCENE.end + 45)) * 20}px)`,
          }}
        >
          prompt <span style={{ color: COLORS.accent }}>→</span> video
        </div>
      </div>
    </AbsoluteFill>
  );
};
