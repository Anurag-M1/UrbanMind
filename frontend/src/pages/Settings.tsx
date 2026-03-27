import React from 'react';
import { Settings as SettingsIcon, Database, Layout, Shield, Trash2, FileOutput } from 'lucide-react';
import { GovCard } from '@/components/common/gov-card';

export default function Settings() {

  return (
    <div className="p-8 space-y-8 bg-[#f5f7fa] animate-in fade-in duration-700">
      <div className="flex justify-between items-end border-b-2 border-navy/10 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-1.5 h-6 bg-saffron" />
            <div className="w-White h-6 bg-white border border-gray-200" />
            <div className="w-1.5 h-6 bg-green" />
            <h3 className="text-[10px] font-black text-navy/40 uppercase tracking-[0.3em] ml-2">Administrative Configuration</h3>
          </div>
          <h2 className="text-4xl font-black text-navy tracking-tight uppercase">System Settings</h2>
          <p className="text-navy/50 font-medium mt-1">Official Environmental Configuration, AI Logic, and Audit Integrity</p>
        </div>
        <div className="bg-white px-4 py-2 rounded border border-[#d1d9e2] shadow-sm">
          <span className="text-[10px] font-black text-navy/40 uppercase tracking-widest">Version Control</span>
          <p className="text-xs font-black text-navy">GOI-UM-1.0.42-STABLE</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: General Configuration */}
        <div className="lg:col-span-2 space-y-8">
          <GovCard title="INTERFACE & VISUALIZATION AUDIT" accent="navy" className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-[#f8f9fa] rounded border border-[#d1d9e2] hover:bg-white transition-colors">
                <div>
                  <p className="text-sm font-black text-navy uppercase tracking-tight">Administrative HUD</p>
                  <p className="text-[10px] text-navy/40 font-bold uppercase tracking-wide">Toggle Official Sector Labels in 3D City view</p>
                </div>
                <div className="w-12 h-6 bg-navy rounded-full relative cursor-pointer shadow-inner">
                  <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm" />
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-[#f8f9fa] rounded border border-[#d1d9e2] hover:bg-white transition-colors">
                <div>
                  <p className="text-sm font-black text-navy uppercase tracking-tight">Security Scanlines</p>
                  <p className="text-[10px] text-navy/40 font-bold uppercase tracking-wide">Enable High-Security Monitor Overlay (CRT Mode)</p>
                </div>
                <div className="w-12 h-6 bg-gray-200 rounded-full relative cursor-pointer shadow-inner">
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm" />
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-[#f8f9fa] rounded border border-[#d1d9e2] hover:bg-white transition-colors">
                <div>
                  <p className="text-sm font-black text-navy uppercase tracking-tight">Auto-Orbit Surveillance</p>
                  <p className="text-[10px] text-navy/40 font-bold uppercase tracking-wide">Automatic 360° Sector Rotation during Standby</p>
                </div>
                <div className="w-12 h-6 bg-navy rounded-full relative cursor-pointer shadow-inner">
                  <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm" />
                </div>
              </div>
            </div>
          </GovCard>

          <GovCard title="AI LOGIC & PROTOCOL PHASING" accent="saffron" className="p-6">
            <div className="space-y-4">
               <div className="p-4 bg-[#f8f9fa] rounded border border-[#d1d9e2] flex flex-col gap-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm font-black text-navy uppercase tracking-tight">Neural Refresh Interval</p>
                      <p className="text-[10px] text-navy/40 font-bold uppercase tracking-wide">Seconds between adaptive signal recalculation (Webster's Baseline)</p>
                    </div>
                    <span className="text-xs font-black text-navy px-3 py-1 bg-white rounded border border-[#d1d9e2] shadow-sm">10s</span>
                  </div>
                  <input type="range" className="w-full h-1.5 bg-gray-200 appearance-none rounded-lg accent-navy cursor-pointer" />
               </div>

               <div className="flex items-center justify-between p-4 bg-[#f8f9fa] rounded border border-[#d1d9e2] hover:bg-white transition-colors">
                <div>
                  <p className="text-sm font-black text-navy uppercase tracking-tight">Priority Pre-emption</p>
                  <p className="text-[10px] text-navy/40 font-bold uppercase tracking-wide">Force immediate green corridor for verified Emergency Units</p>
                </div>
                <div className="w-12 h-6 bg-navy rounded-full relative cursor-pointer shadow-inner">
                  <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm" />
                </div>
              </div>
            </div>
          </GovCard>
        </div>

        {/* Right Column: Audit & Data Integrity */}
        <div className="space-y-8">
          <GovCard title="DATABASE & INTEGRITY" accent="green" className="p-6">
            <div className="space-y-3">
              <button className="w-full flex items-center justify-between p-4 bg-[#f8f9fa] rounded border border-[#d1d9e2] group hover:bg-red-50 hover:border-red-200 transition-all">
                <span className="text-xs font-black text-navy/70 uppercase tracking-widest group-hover:text-red-600 transition-colors">Wipe Incident Logs</span>
                <Trash2 size={16} className="text-navy/20 group-hover:text-red-500 transition-colors" />
              </button>
              <button className="w-full flex items-center justify-between p-4 bg-[#f8f9fa] rounded border border-[#d1d9e2] group hover:bg-navy/5 hover:border-navy/20 transition-all">
                <span className="text-xs font-black text-navy/70 uppercase tracking-widest group-hover:text-navy transition-colors">Export Audit Trail (PDF)</span>
                <FileOutput size={16} className="text-navy/20 group-hover:text-navy transition-colors" />
              </button>
            </div>
          </GovCard>

          <GovCard title="PROJECT CREDITS" accent="navy" className="p-6">
            <div className="space-y-3">
              {['Anurag', 'Yash', 'Prakhar'].map((member) => (
                <div key={member} className="flex items-center justify-between rounded border border-[#d1d9e2] bg-[#f8f9fa] px-4 py-3">
                  <span className="text-xs font-black uppercase tracking-[0.18em] text-navy">{member}</span>
                  <span className="text-[9px] font-black uppercase tracking-[0.2em] text-green">Core Project Team</span>
                </div>
              ))}
            </div>
          </GovCard>

          <div className="p-6 bg-white border-2 border-dashed border-navy/20 rounded-lg flex flex-col items-center text-center">
             <div className="p-3 bg-navy/5 rounded-full mb-4">
                <Shield size={32} className="text-navy animate-pulse" />
             </div>
             <p className="text-[10px] font-black text-navy uppercase tracking-widest mb-1">Administrative Node</p>
             <p className="text-[9px] text-navy/40 font-medium leading-relaxed uppercase tracking-tighter">
                Connected to secure GOI intranet.<br />
                All changes logged for fiscal audit.
             </p>
          </div>
        </div>
      </div>
    </div>
  );
}
