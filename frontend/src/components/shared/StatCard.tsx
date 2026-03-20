/* Shared stat card component used throughout the UrbanMind dashboard. */

import { clsx } from "clsx";
import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string;
  tone?: "cyan" | "green" | "red" | "amber" | "purple";
  helper?: string;
  icon?: ReactNode;
}

const toneClasses: Record<NonNullable<StatCardProps["tone"]>, string> = {
  cyan: "border-b-um-cyan text-um-cyan",
  green: "border-b-um-green text-um-green",
  red: "border-b-um-red text-um-red",
  amber: "border-b-um-amber text-um-amber",
  purple: "border-b-um-purple text-um-purple",
};

export function StatCard({ label, value, helper, icon, tone = "cyan" }: StatCardProps) {
  return (
    <article className="rounded-2xl border border-um-border bg-um-surface/90 p-4 shadow-cyan">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className={clsx("border-b pb-3 font-mono text-[28px] leading-none", toneClasses[tone])}>
            {value}
          </div>
          <div className="mt-3 text-[11px] uppercase tracking-[0.22em] text-um-muted">{label}</div>
          {helper ? <div className="mt-1 text-xs text-um-text/80">{helper}</div> : null}
        </div>
        {icon ? <div className="rounded-xl border border-um-border bg-black/20 p-2">{icon}</div> : null}
      </div>
    </article>
  );
}
