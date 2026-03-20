/* Reusable three-light traffic signal display. */

import { clsx } from "clsx";

type SignalState = "red" | "yellow" | "green" | "off";

interface SignalLightProps {
  state: SignalState;
  direction: "EW" | "NS";
}

const lightClasses: Record<Exclude<SignalState, "off">, string> = {
  red: "bg-um-red shadow-[0_0_20px_rgba(255,51,85,0.55)]",
  yellow: "bg-um-amber shadow-[0_0_18px_rgba(255,204,0,0.45)]",
  green: "bg-um-green shadow-[0_0_18px_rgba(0,255,136,0.45)]",
};

function bulbClass(active: boolean, color: Exclude<SignalState, "off">): string {
  return clsx(
    "h-6 w-6 rounded-full border border-white/10 transition-all duration-300",
    active ? lightClasses[color] : "opacity-20",
  );
}

export function SignalLight({ state, direction }: SignalLightProps) {
  return (
    <div className="rounded-2xl border border-um-border bg-black/40 px-3 py-4">
      <div className="mb-3 text-center font-mono text-xs tracking-[0.25em] text-um-muted">
        {direction}
      </div>
      <div className="flex flex-col items-center gap-3 rounded-xl bg-black/40 p-3">
        <div className={bulbClass(state === "red", "red")} />
        <div className={bulbClass(state === "yellow", "yellow")} />
        <div className={bulbClass(state === "green", "green")} />
      </div>
    </div>
  );
}
