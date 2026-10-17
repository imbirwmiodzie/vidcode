import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../theme";
import { SCENE } from "../timing";
import { inOut, ramp } from "../util";

// 12-16 s: three cards land on the snare hits at 12, 13 and 14 s, then merge into the wave.
const W = 440;
const H = 520;
const GAP = 64;
const LEFT = (1920 - (3 * W + 2 * GAP)) / 2;
const TOP = (1080 - H) / 2;

const iconStroke = { stroke: COLORS.text, strokeWidth: 8, fill: "none", strokeLinecap: "round", strokeLinejoin: "round" } as const;

const EditorIcon = () => (
  <g {...iconStroke}>
    <rect x={20} y={52} width={88} height={36} rx={8} />
    <rect x={118} y={52} width={62} height={36} rx={8} />
    <rect x={20} y={112} width={54} height={36} rx={8} />
    <rect x={84} y={112} width={96} height={36} rx={8} />
    <line x1={100} y1={28} x2={100} y2={172} />
  </g>
);

const CameraIcon = () => (
  <g {...iconStroke}>
    <rect x={18} y={60} width={122} height={84} rx={14} />
    <polygon points="140,88 182,64 182,140 140,116" />
  </g>
);

const WaveIcon = () => (
  <g {...iconStroke}>
    {[30, 70, 110, 50, 140, 90, 120, 60, 36].map((h, i) => (
      <line key={i} x1={28 + i * 18} x2={28 + i * 18} y1={100 - h / 2} y2={100 + h / 2} />
    ))}
  </g>
);

const CARDS = [
  { word: "editor", sub: "just React components", Icon: EditorIcon, tilt: 10 },
  { word: "stock", sub: "just SVG and CSS", Icon: CameraIcon, tilt: 0 },
  { word: "samples", sub: "just Python sine waves", Icon: WaveIcon, tilt: -10 },
];

export const CardsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < SCENE.cards - 10 || frame > SCENE.wave + 12) return null;

  const merge = ramp(frame, SCENE.wave - 14, SCENE.wave + 8, inOut);

  return (
    <AbsoluteFill style={{ perspective: 1800 }}>
      {CARDS.map(({ word, sub, Icon, tilt }, i) => {
        const land = SCENE.cards + 30 * i;
        const s = spring({ frame: frame - (land - 8), fps, config: { damping: 14, stiffness: 140 } });
        const strike = ramp(frame, land + 3, land + 13);
        const flash = Math.max(0, 1 - (frame - land) / 12) * (frame >= land ? 1 : 0);
        const cx = LEFT + i * (W + GAP) + W / 2;
        const float = Math.sin((frame - land) / 18 + i) * 6 * s;
        return (
          <div
            key={word}
            style={{
              position: "absolute",
              left: cx - W / 2,
              top: TOP,
              width: W,
              height: H,
              borderRadius: 32,
              background: `linear-gradient(160deg, #1A1F2A 0%, ${COLORS.panel} 60%, #0F1218 100%)`,
              border: `2px solid rgba(255, 107, 74, ${0.12 + 0.75 * flash})`,
              boxShadow: `0 40px 80px rgba(0, 0, 0, 0.5), 0 0 ${60 * flash}px rgba(255, 107, 74, ${0.5 * flash})`,
              opacity: Math.min(1, s * 2) * (1 - merge),
              transform: [
                `translateX(${(960 - cx) * merge}px)`,
                `translateY(${(1 - s) * 520 + float}px)`,
                `rotateX(${(1 - s) * 35}deg)`,
                `rotateY(${(1 - s) * -40 + tilt * (1 - merge)}deg)`,
                `scale(${1 - 0.8 * merge})`,
              ].join(" "),
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              paddingTop: 64,
            }}
          >
            <svg width={200} height={200} viewBox="0 0 200 200">
              <Icon />
              <line
                x1={22}
                y1={178}
                x2={178}
                y2={22}
                stroke={COLORS.panel}
                strokeWidth={26}
                strokeLinecap="round"
                strokeDasharray={221}
                strokeDashoffset={221 * (1 - strike)}
              />
              <line
                x1={22}
                y1={178}
                x2={178}
                y2={22}
                stroke={COLORS.accent}
                strokeWidth={10}
                strokeLinecap="round"
                strokeDasharray={221}
                strokeDashoffset={221 * (1 - strike)}
              />
            </svg>
            <div style={{ marginTop: 52, fontSize: 66, fontWeight: 800, letterSpacing: "-0.03em" }}>
              No {word}
              <span style={{ color: COLORS.accent }}>.</span>
            </div>
            <div style={{ marginTop: 14, fontSize: 28, fontWeight: 500, color: COLORS.muted }}>{sub}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
