/* UrbanMind root application shell and route layout. */

import { ActivitySquare, AlertOctagon, BarChart3, Cog, LayoutDashboard } from "lucide-react";
import { NavLink, Route, Routes } from "react-router-dom";

import { AlertBadge } from "./components/shared/AlertBadge";
import { useWebSocket } from "./hooks/useWebSocket";
import { AnalyticsPage } from "./pages/Analytics";
import { DashboardPage } from "./pages/Dashboard";
import { EmergencyPage } from "./pages/Emergency";
import { SettingsPage } from "./pages/Settings";
import { useIntersectionStore } from "./store/intersectionStore";

const navigation = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/emergency", label: "Emergency", icon: AlertOctagon },
  { to: "/settings", label: "Settings", icon: Cog },
];

export default function App() {
  const { isConnected, connectionStatus } = useWebSocket();
  const alerts = useIntersectionStore((state) => state.alerts);

  return (
    <div className="min-h-screen min-w-[1280px] bg-um-bg text-um-text">
      <div className="grid min-h-screen grid-cols-[240px_minmax(0,1fr)]">
        <aside className="border-r border-um-border bg-gradient-to-b from-[#041225] to-[#020c18] p-6">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-um-border bg-black/20 p-3">
              <ActivitySquare className="h-6 w-6 text-um-cyan" />
            </div>
            <div>
              <div className="font-display text-2xl text-white">UrbanMind</div>
              <div className="text-xs uppercase tracking-[0.22em] text-um-muted">
                AI Traffic Control
              </div>
            </div>
          </div>

          <nav className="mt-10 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    [
                      "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition",
                      isActive
                        ? "border border-um-cyan/40 bg-um-cyan/10 text-um-cyan"
                        : "border border-transparent text-um-text hover:border-um-border hover:bg-black/20",
                    ].join(" ")
                  }
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>

          <div className="mt-10 space-y-2">
            {alerts.slice(0, 3).map((alert) => (
              <AlertBadge key={alert.id} alert={alert} />
            ))}
          </div>
        </aside>

        <main className="p-6">
          <header className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="font-display text-3xl text-white">City Authority Command Console</h1>
              <p className="mt-1 text-sm text-um-muted">
                Live adaptive signaling, emergency corridors, and analytics for Bhilai-Durg.
              </p>
            </div>
            <div className="rounded-full border border-um-border bg-um-surface/90 px-4 py-2 text-sm">
              <span
                className={`mr-2 inline-block h-2.5 w-2.5 rounded-full ${
                  isConnected ? "bg-um-green animate-glow" : "bg-um-red"
                }`}
              />
              {connectionStatus}
            </div>
          </header>

          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/emergency" element={<EmergencyPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
