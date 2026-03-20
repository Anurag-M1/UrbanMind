/* Leaflet marker representing a live signalized intersection. */

import L from "leaflet";
import { Marker, Popup } from "react-leaflet";

import type { IntersectionState } from "../../types";

interface IntersectionMarkerProps {
  intersection: IntersectionState;
  onSelect: (intersectionId: string) => void;
}

function buildIcon(intersection: IntersectionState) {
  const color = intersection.fault
    ? "var(--um-muted)"
    : intersection.override
      ? "var(--um-red)"
      : intersection.ew_green
        ? "var(--um-green)"
        : "var(--um-red)";

  return L.divIcon({
    className: "urbanmind-marker",
    html: `<div style="width:18px;height:18px;border-radius:999px;background:${color};box-shadow:0 0 18px ${color};border:2px solid rgba(255,255,255,0.35)"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

export function IntersectionMarker({ intersection, onSelect }: IntersectionMarkerProps) {
  return (
    <Marker
      position={[intersection.lat, intersection.lng]}
      icon={buildIcon(intersection)}
      eventHandlers={{ click: () => onSelect(intersection.id) }}
    >
      <Popup>{intersection.name}</Popup>
    </Marker>
  );
}
