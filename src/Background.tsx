import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { audioData } from "./audio-data";
import { COLORS } from "./theme";

export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const level = audioData.rms[frame] ?? 0;
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      <AbsoluteFill
        style={{
          backgroundImage: "radial-gradient(rgba(242, 242, 242, 0.07) 1.5px, transparent 1.5px)",
          backgroundSize: "48px 48px",
          backgroundPosition: `0px ${-frame * 0.4}px`,
          opacity: interpolate(frame, [0, 40], [0, 1], { extrapolateRight: "clamp" }),
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 50%, rgba(255, 107, 74, ${0.04 + 0.12 * level}) 0%, transparent 60%)`,
        }}
      />
      <AbsoluteFill
        style={{ background: "radial-gradient(ellipse at center, transparent 45%, rgba(0, 0, 0, 0.65) 100%)" }}
      />
    </AbsoluteFill>
  );
};
