import React from 'react';
import { Shield, Trash2, FileOutput } from 'lucide-react';
import { GovCard } from '@/components/common/gov-card';

const visualizationItems = [
  {
    title: 'Administrative HUD',
    description: 'Toggle official sector labels in 3D City view',
    enabled: true,
  },
  {
    title: 'Security Scanlines',
    description: 'Enable high-security monitor overlay (CRT mode)',
    enabled: false,
  },
  {
    title: 'Auto-Orbit Surveillance',
    description: 'Automatic 360 degree sector rotation during standby',
    enabled: true,
  },
];

const aiProtocolItems = [
  {
    title: 'Priority Pre-emption',
    description: 'Force immediate green corridor for verified emergency units',
    enabled: true,
  },
  {
    title: 'Siren Route Escalation',
    description: 'Promote reroute guidance when live siren verification is active',
    enabled: true,
  },
];

function TogglePill({ enabled }: { enabled: boolean }) {
  return (
    <div className={`relative h-6 w-12 shrink-0 rounded-full shadow-inner ${enabled ? 'bg-navy' : 'bg-gray-200'}`}>
      <div className={`absolute top-1 h-4 w-4 rounded-full bg-white shadow-sm transition-all ${enabled ? 'right-1' : 'left-1'}`} />
    </div>
  );
}

function SettingRow({
  title,
  description,
  enabled,
}: {
  title: string;
  description: string;
  enabled: boolean;
}) {
  return (
    <div className="flex flex-col gap-4 rounded border border-[#d1d9e2] bg-[#f8f9fa] p-4 transition-colors hover:bg-white sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <p className="text-sm font-black uppercase tracking-tight text-navy">{title}</p>
        <p className="mt-1 text-[10px] font-bold uppercase tracking-wide text-navy/40">{description}</p>
      </div>
      <TogglePill enabled={enabled} />
    </div>
  );
}

export default function Settings() {
  return (
    <div className="min-h-full overflow-y-auto bg-[#f5f7fa] p-4 animate-in fade-in duration-700 sm:p-6 lg:p-8">
      <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-8 pb-16">
        <div className="flex flex-col gap-4 border-b-2 border-navy/10 pb-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0">
            <div className="mb-2 flex items-center gap-2">
              <div className="h-6 w-1.5 bg-saffron" />
              <div className="h-6 w-1.5 border border-gray-200 bg-white" />
              <div className="h-6 w-1.5 bg-green" />
              <h3 className="ml-2 text-[10px] font-black uppercase tracking-[0.3em] text-navy/40">Administrative Configuration</h3>
            </div>
            <h2 className="text-3xl font-black uppercase tracking-tight text-navy sm:text-4xl">System Settings</h2>
            <p className="mt-1 font-medium text-navy/50">Official environmental configuration, AI logic, and audit integrity controls.</p>
          </div>
          <div className="self-start rounded border border-[#d1d9e2] bg-white px-4 py-3 shadow-sm lg:self-auto">
            <span className="text-[10px] font-black uppercase tracking-widest text-navy/40">Version Control</span>
            <p className="text-xs font-black text-navy">GOI-UM-1.0.42-STABLE</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 xl:grid-cols-[minmax(0,1.25fr)_minmax(300px,0.75fr)]">
          <div className="space-y-8">
            <GovCard title="INTERFACE & VISUALIZATION AUDIT" accent="navy" className="p-5 sm:p-6">
              <div className="space-y-4">
                {visualizationItems.map((item) => (
                  <SettingRow
                    key={item.title}
                    title={item.title}
                    description={item.description}
                    enabled={item.enabled}
                  />
                ))}
              </div>
            </GovCard>

            <GovCard title="AI LOGIC & PROTOCOL PHASING" accent="saffron" className="p-5 sm:p-6">
              <div className="space-y-4">
                <div className="rounded border border-[#d1d9e2] bg-[#f8f9fa] p-4">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div className="min-w-0">
                      <p className="text-sm font-black uppercase tracking-tight text-navy">Neural Refresh Interval</p>
                      <p className="mt-1 text-[10px] font-bold uppercase tracking-wide text-navy/40">
                        Seconds between adaptive signal recalculation (Webster baseline)
                      </p>
                    </div>
                    <span className="self-start rounded border border-[#d1d9e2] bg-white px-3 py-1 text-xs font-black text-navy shadow-sm lg:self-auto">
                      10s
                    </span>
                  </div>
                  <input
                    type="range"
                    className="mt-4 h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-navy"
                    defaultValue={10}
                  />
                </div>

                {aiProtocolItems.map((item) => (
                  <SettingRow
                    key={item.title}
                    title={item.title}
                    description={item.description}
                    enabled={item.enabled}
                  />
                ))}
              </div>
            </GovCard>
          </div>

          <div className="space-y-8">
            <GovCard title="DATABASE & INTEGRITY" accent="green" className="p-5 sm:p-6">
              <div className="space-y-3">
                <button className="flex w-full items-center justify-between gap-3 rounded border border-[#d1d9e2] bg-[#f8f9fa] p-4 transition-all hover:border-red-200 hover:bg-red-50 group">
                  <span className="text-left text-xs font-black uppercase tracking-widest text-navy/70 transition-colors group-hover:text-red-600">
                    Wipe Incident Logs
                  </span>
                  <Trash2 size={16} className="shrink-0 text-navy/20 transition-colors group-hover:text-red-500" />
                </button>
                <button className="flex w-full items-center justify-between gap-3 rounded border border-[#d1d9e2] bg-[#f8f9fa] p-4 transition-all hover:border-navy/20 hover:bg-navy/5 group">
                  <span className="text-left text-xs font-black uppercase tracking-widest text-navy/70 transition-colors group-hover:text-navy">
                    Export Audit Trail (PDF)
                  </span>
                  <FileOutput size={16} className="shrink-0 text-navy/20 transition-colors group-hover:text-navy" />
                </button>
              </div>
            </GovCard>

            <GovCard title="PROJECT CREDITS" accent="navy" className="p-5 sm:p-6">
              <div className="space-y-3">
                {['Anurag', 'Yash', 'Prakhar'].map((member) => (
                  <div
                    key={member}
                    className="flex flex-col gap-2 rounded border border-[#d1d9e2] bg-[#f8f9fa] px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <span className="text-xs font-black uppercase tracking-[0.18em] text-navy">{member}</span>
                    <span className="text-[9px] font-black uppercase tracking-[0.2em] text-green">Core Project Team</span>
                  </div>
                ))}
              </div>
            </GovCard>

            <div className="flex flex-col items-center rounded-lg border-2 border-dashed border-navy/20 bg-white p-6 text-center sm:p-8">
              <div className="mb-4 rounded-full bg-navy/5 p-3">
                <Shield size={32} className="animate-pulse text-navy" />
              </div>
              <p className="mb-1 text-[10px] font-black uppercase tracking-widest text-navy">Administrative Node</p>
              <p className="text-[9px] font-medium uppercase tracking-tighter leading-relaxed text-navy/40">
                Connected to secure GOI intranet.
                <br />
                All changes logged for fiscal audit.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
