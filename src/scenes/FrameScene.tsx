import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../theme";
import { BEAT, SCENE } from "../timing";
import { inOut, ramp, sceneOpacity, Words } from "../util";

// 8-12 s: a video frame draws itself; a ball bounces on every beat while a playhead
// sweeps the timeline and drops a keyframe on each pluck.
const FX = 520;
const FY = 300;
const FW = 880;
const FH = 495;
const TRACK_Y = 880;
const BALL = 30;
const FLOOR = FY + FH - 40;

const progress = (frame: number) => Math.min(1, Math.max(0, (frame - SCENE.frame) / (8 * BEAT)));

const ballAt = (frame: number) => {
  const local = Math.max(0, frame - SCENE.frame);
  const phase = (local % BEAT) / BEAT;
  return {
    x: FX + 80 + progress(frame) * (FW - 160),
    y: FLOOR - BALL - 230 * Math.sin(Math.PI * phase),
    squash: phase < 0.12 || phase > 0.94 ? 0.82 : 1,
  };
};

export const FrameScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < SCENE.frame - 6 || frame > SCENE.cards + 16) return null;

  const opacity = sceneOpacity(frame, SCENE.frame - 6, SCENE.frame + 4, SCENE.cards - 10, SCENE.cards + 12);
  const exit = ramp(frame, SCENE.cards - 10, SCENE.cards + 12, inOut);
  const draw = ramp(frame, SCENE.frame - 2, SCENE.frame + 22);
  const fill = ramp(frame, SCENE.frame + 10, SCENE.frame + 24);
  const content = ramp(frame, SCENE.frame + 4, SCENE.frame + 14);
  const head = progress(frame);
  const ball = ballAt(frame);

  return (
    <AbsoluteFill style={{ opacity, transform: `scale(${1 - 0.06 * exit})` }}>
      <div style={{ position: "absolute", top: 110, left: 0, right: 0 }}>
        <Words text="Every frame is code." frame={frame} start={SCENE.frame + 6} step={7} size={104} accent={["code."]} />
      </div>

      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <defs>
          <clipPath id="frameClip">
            <rect x={FX} y={FY} width={FW} height={FH} rx={24} />
          </clipPath>
        </defs>
        <rect x={FX} y={FY} width={FW} height={FH} rx={24} fill={COLORS.panel} opacity={fill * 0.9} />
        <rect
          x={FX}
          y={FY}
          width={FW}
          height={FH}
          rx={24}
          fill="none"
          stroke={COLORS.accent}
          strokeWidth={3}
          strokeDasharray={2800}
          strokeDashoffset={2800 * (1 - draw)}
        />
        <g clipPath="url(#frameClip)" opacity={content}>
          <line x1={FX + 40} x2={FX + FW - 40} y1={FLOOR} y2={FLOOR} stroke={COLORS.faint} strokeWidth={3} />
          {[6, 4, 2].map((lag, i) => {
            const ghost = ballAt(frame - lag);
            return <circle key={lag} cx={ghost.x} cy={ghost.y} r={BALL} fill={COLORS.accent} opacity={0.08 + 0.08 * i} />;
          })}
          <ellipse
            cx={ball.x}
            cy={ball.y + BALL * (1 - ball.squash)}
            rx={BALL / ball.squash}
            ry={BALL * ball.squash}
            fill={COLORS.accent}
          />
        </g>
      </svg>

      <div
        style={{
          position: "absolute",
          left: FX + 28,
          top: FY + 22,
          fontSize: 24,
          color: COLORS.muted,
          opacity: content,
        }}
      >
        Teaser · 1920×1080 · 30 fps
      </div>
      <div
        style={{
          position: "absolute",
          right: 1920 - FX - FW + 28,
          top: FY + 22,
          fontSize: 24,
          color: COLORS.text,
          opacity: content,
          fontFeatureSettings: '"tnum"',
        }}
      >
        frame {String(frame).padStart(4, "0")}
      </div>

      {/* Timeline */}
      <div style={{ opacity: content }}>
        <div
          style={{
            position: "absolute",
            left: FX,
            top: TRACK_Y - 2,
            width: FW,
            height: 4,
            borderRadius: 2,
            backgroundColor: COLORS.faint,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: FX,
            top: TRACK_Y - 2,
            width: FW * head,
            height: 4,
            borderRadius: 2,
            backgroundColor: "rgba(255, 107, 74, 0.45)",
          }}
        />
        {Array.from({ length: 8 }, (_, k) => {
          const hit = SCENE.frame + k * BEAT;
          const s = spring({ frame: frame - hit, fps, config: { damping: 10, stiffness: 200 } });
          return (
            <div
              key={k}
              style={{
                position: "absolute",
                left: FX + (FW * k) / 8 - 13,
                top: TRACK_Y - 13,
                width: 26,
                height: 26,
                borderRadius: 4,
                backgroundColor: k % 2 ? COLORS.text : COLORS.accent,
                transform: `rotate(45deg) scale(${frame >= hit ? s : 0})`,
              }}
            />
          );
        })}
        <div
          style={{
            position: "absolute",
            left: FX + FW * head - 2,
            top: TRACK_Y - 34,
            width: 4,
            height: 68,
            borderRadius: 2,
            backgroundColor: COLORS.accent,
            boxShadow: "0 0 18px rgba(255, 107, 74, 0.8)",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
