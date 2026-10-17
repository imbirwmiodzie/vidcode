import { AbsoluteFill, Easing, interpolate, random, useCurrentFrame } from "remotion";
import { COLORS } from "../theme";
import { BEAT, PROMPT, SCENE, typedAt } from "../timing";
import { ramp } from "../util";

// 0-4 s: a prompt is typed in time with the clicks, then bursts apart on the downbeat.
export const PromptScene: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame > SCENE.code + 22) return null;

  const burst = ramp(frame, SCENE.code - 2, SCENE.code + 20);
  const fadeOut = 1 - ramp(frame, SCENE.code, SCENE.code + 18, Easing.linear);
  const lastTyped = typedAt(PROMPT.length - 1);
  const typing = frame >= typedAt(0) && frame < lastTyped + 4;
  const cursorOn = typing || frame % BEAT < 8;
  const typedCount = PROMPT.split("").filter((_, i) => frame >= typedAt(i)).length;
  const cursor = (
    <span key="cursor" style={{ position: "relative", display: "inline-block", width: 0 }}>
      <span
        style={{
          position: "absolute",
          left: 10,
          top: -96,
          width: 60,
          height: 120,
          borderRadius: 6,
          backgroundColor: COLORS.accent,
          opacity: (cursorOn ? 1 : 0) * (1 - burst),
        }}
      />
    </span>
  );
  const push = interpolate(frame, [0, SCENE.code], [0.94, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          fontSize: 128,
          fontWeight: 700,
          letterSpacing: "-0.02em",
          whiteSpace: "pre",
          transform: `scale(${push})`,
          textShadow: "0 0 48px rgba(255, 107, 74, 0.25)",
        }}
      >
        {PROMPT.split("").map((ch, i) => {
          const pop = ramp(frame, typedAt(i), typedAt(i) + 5);
          const dx = (i - PROMPT.length / 2) * 50 + (random(`dx${i}`) - 0.5) * 700;
          const dy = (random(`dy${i}`) - 0.5) * 900;
          const rot = (random(`r${i}`) - 0.5) * 220;
          return [
            i === typedCount ? cursor : null,
            <span
              key={i}
              style={{
                display: "inline-block",
                color: i === 0 ? COLORS.accent : COLORS.text,
                opacity: (frame >= typedAt(i) ? pop : 0) * fadeOut,
                transform: `translate(${dx * burst}px, ${dy * burst + (1 - pop) * 16}px) rotate(${rot * burst}deg) scale(${1 - 0.4 * burst})`,
                filter: `blur(${burst * 10}px)`,
              }}
            >
              {ch}
            </span>,
          ];
        })}
        {typedCount === PROMPT.length ? cursor : null}
      </div>
    </AbsoluteFill>
  );
};
