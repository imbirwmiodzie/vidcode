import { Easing, interpolate } from "remotion";
import { COLORS } from "./theme";

export const outQuint = Easing.bezier(0.22, 1, 0.36, 1);
export const inOut = Easing.bezier(0.65, 0, 0.35, 1);

// 0 -> 1 between two frames, clamped.
export const ramp = (frame: number, from: number, to: number, easing = outQuint) =>
  interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing,
  });

// Opacity for a scene that fades in over [inStart, inEnd] and out over [outStart, outEnd].
export const sceneOpacity = (
  frame: number,
  inStart: number,
  inEnd: number,
  outStart: number,
  outEnd: number,
) => Math.min(ramp(frame, inStart, inEnd, inOut), 1 - ramp(frame, outStart, outEnd, inOut));

// Headline whose words slide up out of a mask one after another.
export const Words: React.FC<{
  text: string;
  frame: number;
  start: number;
  step: number;
  size: number;
  accent?: string[];
}> = ({ text, frame, start, step, size, accent = [] }) => (
  <div
    style={{
      display: "flex",
      justifyContent: "center",
      gap: size * 0.28,
      fontSize: size,
      fontWeight: 800,
      letterSpacing: "-0.03em",
      lineHeight: 1.15,
    }}
  >
    {text.split(" ").map((word, i) => {
      const p = ramp(frame, start + i * step, start + i * step + 12);
      return (
        <span key={i} style={{ display: "inline-block", overflow: "hidden", paddingBottom: size * 0.08 }}>
          <span
            style={{
              display: "inline-block",
              transform: `translateY(${(1 - p) * 110}%)`,
              color: accent.includes(word) ? COLORS.accent : COLORS.text,
            }}
          >
            {word}
          </span>
        </span>
      );
    })}
  </div>
);
