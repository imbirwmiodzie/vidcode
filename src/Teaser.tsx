import { AbsoluteFill, Html5Audio, interpolate, random, staticFile, useCurrentFrame } from "remotion";
import { Background } from "./Background";
import { CardsScene } from "./scenes/CardsScene";
import { CodeScene } from "./scenes/CodeScene";
import { EndScene } from "./scenes/EndScene";
import { FrameScene } from "./scenes/FrameScene";
import { PromptScene } from "./scenes/PromptScene";
import { WaveScene } from "./scenes/WaveScene";
import { COLORS, FONT } from "./theme";
import { SCENE } from "./timing";

export const Teaser: React.FC = () => {
  const frame = useCurrentFrame();

  // Short camera shake on the impact at 20 s.
  const shake = Math.max(0, 1 - (frame - SCENE.end) / 12) * (frame >= SCENE.end ? 1 : 0);
  const sx = (random(`sx${frame}`) - 0.5) * 18 * shake;
  const sy = (random(`sy${frame}`) - 0.5) * 18 * shake;

  return (
    <AbsoluteFill style={{ fontFamily: FONT, color: COLORS.text, fontWeight: 600 }}>
      <Background />
      <AbsoluteFill style={{ transform: `translate(${sx}px, ${sy}px)` }}>
        <PromptScene />
        <CodeScene />
        <FrameScene />
        <CardsScene />
        <WaveScene />
        <EndScene />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          backgroundColor: "black",
          opacity: interpolate(frame, [696, 719], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      />
      <Html5Audio src={staticFile("music.wav")} />
    </AbsoluteFill>
  );
};
