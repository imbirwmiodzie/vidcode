import { continueRender, delayRender, cancelRender, staticFile } from "remotion";

export const COLORS = {
  bg: "#0B0D12",
  panel: "#141821",
  accent: "#FF6B4A",
  accentSoft: "#FFB4A3",
  text: "#F2F2F2",
  muted: "rgba(242, 242, 242, 0.45)",
  faint: "rgba(242, 242, 242, 0.1)",
};

export const FONT = "Inter Video";

// Bundle Inter from public/fonts so renders look the same on any machine.
const WEIGHTS: [string, number][] = [
  ["Inter-Medium.otf", 500],
  ["Inter-SemiBold.otf", 600],
  ["Inter-Bold.otf", 700],
  ["Inter-ExtraBold.otf", 800],
];

const handle = delayRender("Loading Inter");
Promise.all(
  WEIGHTS.map(([file, weight]) =>
    new FontFace(FONT, `url(${staticFile(`fonts/${file}`)})`, {
      weight: String(weight),
    })
      .load()
      .then((face) => document.fonts.add(face)),
  ),
)
  .then(() => continueRender(handle))
  .catch((err) => cancelRender(err));
