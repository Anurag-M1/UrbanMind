/* Heatmap legend explaining wait-time severity colors. */

export function HeatmapLegend() {
  return (
    <div className="rounded-2xl border border-um-border bg-black/30 p-4 text-sm text-um-text">
      <div className="mb-3 text-xs uppercase tracking-[0.22em] text-um-muted">Heatmap Legend</div>
      <div className="flex items-center gap-3">
        <span className="h-3 w-3 rounded-full bg-um-green" />
        <span>Low wait</span>
        <span className="h-3 w-3 rounded-full bg-um-amber" />
        <span>Medium wait</span>
        <span className="h-3 w-3 rounded-full bg-um-red" />
        <span>High wait</span>
      </div>
    </div>
  );
}
