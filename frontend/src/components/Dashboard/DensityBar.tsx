/* Horizontal density bar for directional traffic counts. */

interface DensityBarProps {
  label: string;
  count: number;
  maxCount?: number;
}

export function DensityBar({ label, count, maxCount = 40 }: DensityBarProps) {
  const width = Math.min(100, (count / maxCount) * 100);
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-um-text">{label}</span>
        <span className="font-mono text-um-cyan">{count.toFixed(0)} vehicles</span>
      </div>
      <div className="h-3 rounded-full bg-black/30">
        <div
          className="h-3 rounded-full bg-gradient-to-r from-um-green via-um-amber to-um-red transition-all duration-500"
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}
