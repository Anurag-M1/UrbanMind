/* Compact alert badge for faults, warnings, and emergency events. */

import { clsx } from "clsx";

import type { Alert } from "../../types";

interface AlertBadgeProps {
  alert: Alert;
}

const badgeClasses: Record<Alert["kind"], string> = {
  emergency: "border-um-red/60 bg-um-red/10 text-um-red",
  fault: "border-um-amber/60 bg-um-amber/10 text-um-amber",
  warning: "border-um-purple/60 bg-um-purple/10 text-um-purple",
  info: "border-um-cyan/60 bg-um-cyan/10 text-um-cyan",
};

export function AlertBadge({ alert }: AlertBadgeProps) {
  return (
    <div
      className={clsx(
        "rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.16em]",
        badgeClasses[alert.kind],
      )}
    >
      {alert.title}
    </div>
  );
}
