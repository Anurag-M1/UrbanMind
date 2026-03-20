/* Animated corridor polyline between pre-empted intersections. */

import { Polyline } from "react-leaflet";

interface CorridorLineProps {
  points: Array<[number, number]>;
}

export function CorridorLine({ points }: CorridorLineProps) {
  if (points.length < 2) {
    return null;
  }

  return (
    <Polyline
      positions={points}
      pathOptions={{
        color: "var(--um-red)",
        opacity: 0.8,
        dashArray: "10 12",
        weight: 5,
      }}
    />
  );
}
