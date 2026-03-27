import { AnalyticsView } from '../components/analytics/AnalyticsView';
import { BarChart3, Activity } from 'lucide-react';

export default function Analytics() {
  return (
    <div className="flex h-full flex-col space-y-6 bg-[#f5f7fa] p-4 animate-in fade-in duration-700 sm:p-6 lg:p-8">
      {/* Official Module Header */}
      <div className="flex flex-col gap-4 border-b-2 border-navy/10 pb-6 shrink-0 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-5">
          <div className="p-4 rounded bg-white border border-[#d1d9e2] shadow-sm">
            <BarChart3 size={32} className="text-navy" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-black text-navy/40 uppercase tracking-[0.4em]">Integrated Data Bureau</span>
              <div className="px-1.5 py-0.5 bg-navy/5 text-navy text-[8px] font-black uppercase rounded border border-navy/20">Certified</div>
            </div>
            <h1 className="text-3xl font-black text-navy uppercase tracking-tight">System Performance Matrix</h1>
          </div>
        </div>
        <div className="hidden md:flex items-center gap-4 bg-white px-5 py-3 rounded border border-[#d1d9e2] shadow-sm">
          <Activity size={16} className="text-green animate-pulse" />
          <div className="flex flex-col">
            <span className="text-[9px] font-black text-navy/40 uppercase tracking-widest">Network Status</span>
            <span className="text-xs font-black text-navy uppercase">Synchronized</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-lg border-2 border-navy/10 bg-white p-2 shadow-xl">
        <AnalyticsView />
      </div>
    </div>
  );
}
