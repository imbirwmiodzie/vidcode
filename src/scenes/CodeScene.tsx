import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { COLORS } from "../theme";
import { kickPulse, SCENE } from "../timing";
import { inOut, ramp, sceneOpacity } from "../util";

// 4-8 s: the prompt turns into the code that renders this video, one line per 8th note.
const LINES = [
  "export const Teaser = () => {",
  "  const frame = useCurrentFrame();",
  "  const { fps } = useVideoConfig();",
  "",
  "  const pop = spring({ frame, fps });",
  "  const glow = interpolate(frame, [0, 120], [0, 1]);",
  "",
  "  return (",
  "    <AbsoluteFill style={{ scale: pop }}>",
  '      <Prompt text="make me a video" />',
  '      <Audio src={staticFile("music.wav")} />',
  "    </AbsoluteFill>",
  "  );",
  "};",
];

const FRAGMENTS = [
  "interpolate(frame, [0, 30], [0, 1])",
  "spring({ frame, fps })",
  "<Sequence from={240}>",
  "useCurrentFrame()",
  'staticFile("music.wav")',
  "<AbsoluteFill />",
  "Easing.bezier(.2, 1, .3, 1)",
  'random("seed")',
  "durationInFrames={720}",
  "fps={30}",
  "width={1920}",
  "height={1080}",
];

const TOKEN = /("[^"]*")|(\b(?:export|const|return)\b)|(\b\d+\b)|([A-Z]\w*)|(\w+)|([^\w\s"]+)|(\s+)/g;

const tokenize = (line: string) => {
  const out: RegExpExecArray[] = [];
  TOKEN.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = TOKEN.exec(line))) out.push(m);
  return out;
};

const Highlighted: React.FC<{ line: string }> = ({ line }) => (
  <>
    {tokenize(line).map((m, i) => {
      const [tok, str, kw, num, comp, , punct] = m;
      const style: React.CSSProperties =
        str || num
          ? { color: COLORS.accentSoft }
          : kw
            ? { color: COLORS.accent, textShadow: "0 0 24px rgba(255, 107, 74, 0.6)" }
            : comp
              ? { color: COLORS.text, fontWeight: 700 }
              : punct
                ? { color: COLORS.muted }
                : { color: COLORS.text };
      return (
        <span key={i} style={style}>
          {tok}
        </span>
      );
    })}
  </>
);

const lineAt = (i: number) => SCENE.code + 4 + i * 7.5;

export const CodeScene: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < SCENE.code - 4 || frame > SCENE.frame + 14) return null;

  const opacity = sceneOpacity(frame, SCENE.code - 4, SCENE.code + 8, SCENE.frame - 12, SCENE.frame + 8);
  const fold = ramp(frame, SCENE.frame - 14, SCENE.frame + 10, inOut);
  const enter = ramp(frame, SCENE.code - 4, SCENE.code + 20);
  // Scroll so the line being written stays near the middle of the screen.
  const written = interpolate(frame, [lineAt(0), lineAt(LINES.length - 1)], [0, LINES.length - 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scroll = interpolate(written, [0, LINES.length - 1], [300, -60]);
  const pulse = kickPulse(frame);
  const current = LINES.reduce((acc, _, i) => (frame >= lineAt(i) ? i : acc), -1);

  return (
    <AbsoluteFill style={{ opacity }}>
      {[0, 1].map((layer) =>
        FRAGMENTS.map((text, i) => {
          const speed = layer === 0 ? 2.6 : 1.5;
          const y = 1240 - ((random(`fy${layer}${i}`) * 1400 + (frame - SCENE.code) * speed) % 1400);
          return (
            <div
              key={`${layer}-${i}`}
              style={{
                position: "absolute",
                // Keep the fragments in the side margins, clear of the main code.
                left: random(`fs${layer}${i}`) < 0.5 ? random(`fx${layer}${i}`) * 160 - 120 : 1560 + random(`fx${layer}${i}`) * 260,
                top: y,
                fontSize: layer === 0 ? 28 : 20,
                color: COLORS.text,
                opacity: layer === 0 ? 0.08 : 0.05,
                filter: `blur(${layer === 0 ? 2.5 : 5}px)`,
                whiteSpace: "pre",
              }}
            >
              {text}
            </div>
          );
        }),
      )}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            position: "relative",
            width: 1180,
            fontSize: 38,
            lineHeight: "58px",
            fontWeight: 500,
            whiteSpace: "pre",
            fontFeatureSettings: '"tnum", "zero"',
            transform: `translateY(${scroll}px) scale(${(1.08 - 0.08 * enter) * (1 - 0.45 * fold) * (1 + 0.003 * pulse)})`,
            filter: `blur(${fold * 8}px)`,
          }}
        >
          {LINES.map((line, i) => {
            const p = ramp(frame, lineAt(i), lineAt(i) + 7);
            return (
              <div key={i} style={{ position: "relative", height: 58 }}>
                {i === current ? (
                  <div
                    style={{
                      position: "absolute",
                      left: -96,
                      right: -24,
                      top: 0,
                      bottom: 0,
                      borderRadius: 10,
                      backgroundColor: `rgba(255, 107, 74, ${0.07 + 0.03 * pulse})`,
                    }}
                  />
                ) : null}
                <span
                  style={{
                    position: "absolute",
                    left: -84,
                    width: 48,
                    textAlign: "right",
                    color: COLORS.faint,
                    fontSize: 28,
                    opacity: p,
                  }}
                >
                  {i + 1}
                </span>
                <div
                  style={{
                    position: "relative",
                    clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`,
                    transform: `translateX(${(1 - p) * 24}px)`,
                  }}
                >
                  <Highlighted line={line} />
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
