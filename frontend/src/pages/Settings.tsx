/* Settings page for deployment and RTSP configuration guidance. */

export function SettingsPage() {
  return (
    <div className="space-y-6 rounded-3xl border border-um-border bg-um-surface/90 p-6">
      <div>
        <h2 className="font-display text-3xl text-white">Settings</h2>
        <p className="mt-2 text-sm text-um-text">
          Configure deployment variables, RTSP camera URLs, and fixed-timer fallback policies.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-3xl border border-um-border bg-black/20 p-5">
          <div className="text-xs uppercase tracking-[0.22em] text-um-muted">RTSP Integration</div>
          <pre className="mt-4 whitespace-pre-wrap font-mono text-sm text-um-text">
            {`Add camera URLs in the backend intersection seed or API bootstrap.
Example: rtsp://camera.example.com/live/int_001`}
          </pre>
        </div>
        <div className="rounded-3xl border border-um-border bg-black/20 p-5">
          <div className="text-xs uppercase tracking-[0.22em] text-um-muted">Edge Deployment</div>
          <pre className="mt-4 whitespace-pre-wrap font-mono text-sm text-um-text">
            {`Jetson Nano benchmark target: 15 FPS
Use scripts/benchmark_edge.sh after loading tuned YOLO weights.`}
          </pre>
        </div>
      </div>
    </div>
  );
}
