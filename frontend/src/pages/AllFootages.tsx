import { Link } from 'react-router-dom';
import { Activity, ArrowUpRight, MonitorPlay } from 'lucide-react';
import { WebcamFeed } from '@/components/dashboard/webcam-feed';
import { CAMERA_NODES } from '@/lib/camera-nodes';
import { useTrafficStore } from '@/lib/store';

export default function AllFootages() {
  const selectedCameraNodeId = useTrafficStore((state) => state.selectedCameraNodeId);
  const setSelectedCameraNodeId = useTrafficStore((state) => state.setSelectedCameraNodeId);
  const liveVisionStatus = useTrafficStore((state) => state.liveVisionStatus);

  return (
    <div className="h-full overflow-y-auto bg-[#f5f7fa] p-4 animate-in fade-in duration-500 sm:p-6">
      <div className="mx-auto flex max-w-[1500px] flex-col gap-6 pb-10">
        <div className="flex flex-col gap-4 rounded-lg border border-[#d1d9e2] bg-white p-5 shadow-sm lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <MonitorPlay size={18} className="text-navy" />
              <span className="text-[10px] font-black uppercase tracking-[0.35em] text-navy/40">Sector Vision Grid</span>
            </div>
            <h1 className="mt-2 text-3xl font-black uppercase tracking-tight text-navy">All Live Footages</h1>
            <p className="mt-2 text-sm font-medium text-navy/55">
              Every available node is mirrored here, and any node you select becomes the active feed on the main sector dashboard.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="rounded border border-[#d1d9e2] bg-[#f8f9fa] px-4 py-3">
              <p className="text-[9px] font-black uppercase tracking-[0.25em] text-navy/35">Current Main Node</p>
              <p className="mt-1 text-sm font-black uppercase tracking-tight text-navy">
                {CAMERA_NODES.find((node) => node.id === selectedCameraNodeId)?.name ?? CAMERA_NODES[0].name}
              </p>
            </div>
            <div className="rounded border border-green/20 bg-green/5 px-4 py-3">
              <p className="text-[9px] font-black uppercase tracking-[0.25em] text-navy/35">Feed Sync</p>
              <div className="mt-1 flex items-center gap-2">
                <Activity size={14} className="text-green" />
                <span className="text-sm font-black uppercase tracking-tight text-green">{liveVisionStatus || 'SYNCING'}</span>
              </div>
            </div>
            <Link
              to="/overview"
              className="inline-flex items-center justify-center gap-2 rounded border border-navy bg-navy px-4 py-3 text-[11px] font-black uppercase tracking-[0.18em] text-white transition-colors hover:bg-navy/90"
            >
              Open Sector Dashboard
              <ArrowUpRight size={14} />
            </Link>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 2xl:grid-cols-3">
          {CAMERA_NODES.map((node) => {
            const isActive = node.id === selectedCameraNodeId;

            return (
              <div
                key={node.id}
                className={`overflow-hidden rounded-lg border bg-white shadow-sm transition-colors ${
                  isActive ? 'border-navy shadow-[0_12px_35px_rgba(15,36,84,0.12)]' : 'border-[#d1d9e2]'
                }`}
              >
                <div className="flex flex-col gap-4 border-b border-[#d1d9e2] bg-[#f8f9fa] px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-black uppercase tracking-[0.25em] text-navy/40">{node.cameraId}</span>
                      <span className={`rounded px-2 py-1 text-[8px] font-black uppercase tracking-[0.18em] ${
                        node.status === 'LIVE'
                          ? 'bg-green/10 text-green'
                          : node.status === 'PRIORITY'
                            ? 'bg-saffron/15 text-saffron'
                            : 'bg-navy/10 text-navy'
                      }`}>
                        {isActive ? 'MAIN DASHBOARD' : node.status}
                      </span>
                    </div>
                    <h2 className="mt-2 text-xl font-black uppercase tracking-tight text-navy">{node.name}</h2>
                    <p className="mt-1 text-[11px] font-bold uppercase tracking-[0.16em] text-navy/45">
                      {node.sector} // {node.location}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setSelectedCameraNodeId(node.id)}
                    className={`rounded border px-4 py-2 text-[10px] font-black uppercase tracking-[0.18em] transition-colors ${
                      isActive
                        ? 'border-green bg-green text-white'
                        : 'border-navy bg-white text-navy hover:bg-navy hover:text-white'
                    }`}
                  >
                    {isActive ? 'Active On Dashboard' : 'Switch To Dashboard'}
                  </button>
                </div>

                <div className="aspect-video bg-black">
                  <WebcamFeed nodeId={node.id} compact />
                </div>

                <div className="grid grid-cols-1 gap-3 px-4 py-4 text-center sm:grid-cols-3">
                  <div className="rounded border border-[#d1d9e2] bg-[#f8f9fa] px-3 py-3">
                    <p className="text-[8px] font-black uppercase tracking-[0.22em] text-navy/35">Node Status</p>
                    <p className="mt-2 text-sm font-black uppercase text-navy">{node.status}</p>
                  </div>
                  <div className="rounded border border-[#d1d9e2] bg-[#f8f9fa] px-3 py-3">
                    <p className="text-[8px] font-black uppercase tracking-[0.22em] text-navy/35">Latency</p>
                    <p className="mt-2 text-sm font-black uppercase text-navy">{node.latencyMs}ms</p>
                  </div>
                  <div className="rounded border border-[#d1d9e2] bg-[#f8f9fa] px-3 py-3">
                    <p className="text-[8px] font-black uppercase tracking-[0.22em] text-navy/35">Coverage</p>
                    <p className="mt-2 text-sm font-black uppercase text-navy">{node.location}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
