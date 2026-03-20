/* Countdown block for the current signal phase. */

interface SignalTimerProps {
  seconds: number;
  label: string;
}

export function SignalTimer({ seconds, label }: SignalTimerProps) {
  return (
    <div className="rounded-xl border border-um-border bg-black/20 px-3 py-2 text-center">
      <div className="font-mono text-lg text-um-cyan">{seconds.toFixed(0)}s</div>
      <div className="text-[10px] uppercase tracking-[0.22em] text-um-muted">{label}</div>
    </div>
  );
}
