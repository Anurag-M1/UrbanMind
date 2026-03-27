interface PulseRingProps {
  color?: 'cyan' | 'green' | 'red' | 'amber';
  size?: number;
}

export function PulseRing({ color = 'cyan', size = 12 }: PulseRingProps) {
  const colorMap = {
    cyan: 'bg-cyan',
    green: 'bg-green',
    red: 'bg-red',
    amber: 'bg-amber',
  };

  return (
    <span className="relative inline-flex" style={{ width: size, height: size }}>
      <span
        className={`absolute inline-flex h-full w-full rounded-full ${colorMap[color]} opacity-75 pulse-ring`}
      />
      <span
        className={`relative inline-flex rounded-full ${colorMap[color]}`}
        style={{ width: size, height: size }}
      />
    </span>
  );
}
