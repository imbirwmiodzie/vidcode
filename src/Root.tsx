import { Composition } from "remotion";
import { Teaser } from "./Teaser";
import { DURATION, FPS } from "./timing";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Teaser"
      component={Teaser}
      durationInFrames={DURATION}
      fps={FPS}
      width={1920}
      height={1080}
    />
  );
};
