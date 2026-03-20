/* Main Leaflet city map with intersection markers and emergency corridor overlay. */

import { useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";

import { CorridorLine } from "./CorridorLine";
import { IntersectionMarker } from "./IntersectionMarker";
import type { IntersectionState } from "../../types";

interface CityMapProps {
  intersections: IntersectionState[];
  corridorIds: string[];
  onSelectIntersection: (intersectionId: string) => void;
}

function FitToBounds({ intersections }: { intersections: IntersectionState[] }) {
  const map = useMap();

  useEffect(() => {
    if (intersections.length === 0) {
      return;
    }
    const bounds = intersections.map((intersection) => [intersection.lat, intersection.lng] as [number, number]);
    map.fitBounds(bounds, { padding: [30, 30] });
  }, [intersections, map]);

  return null;
}

export function CityMap({ intersections, corridorIds, onSelectIntersection }: CityMapProps) {
  const corridorPoints = corridorIds
    .map((corridorId) => intersections.find((intersection) => intersection.id === corridorId))
    .filter((intersection): intersection is IntersectionState => intersection !== undefined)
    .map((intersection) => [intersection.lat, intersection.lng] as [number, number]);

  return (
    <div className="relative h-[620px] overflow-hidden rounded-[32px] border border-um-border">
      <MapContainer
        center={[21.194, 81.378]}
        zoom={12}
        className="h-full w-full"
        zoomControl={false}
      >
        <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
        <FitToBounds intersections={intersections} />
        {intersections.map((intersection) => (
          <IntersectionMarker
            key={intersection.id}
            intersection={intersection}
            onSelect={onSelectIntersection}
          />
        ))}
        <CorridorLine points={corridorPoints} />
      </MapContainer>
      <div className="absolute bottom-4 left-4 rounded-2xl border border-um-border bg-um-surface/90 px-4 py-3 text-xs text-um-text">
        Low wait: green · Medium wait: amber · High wait: red
      </div>
    </div>
  );
}
