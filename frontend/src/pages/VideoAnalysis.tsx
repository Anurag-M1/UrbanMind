import { useState } from 'react';
import { VideoDropzone, AnalysisResults } from '../components/video-upload/VideoComponents';
import type { VideoAnalysisResult } from '../types';
import { Activity, FileVideo } from 'lucide-react';
import { GovCard } from '../components/common/gov-card';

const INTERSECTION_LABELS: Record<string, string> = {
  int_001: 'Connaught Place (CP) Outer Circle',
  int_002: 'ITO Junction (Vikas Marg)',
  int_003: 'AIIMS Crossing (Ring Road)',
  int_004: 'Hauz Khas Junction (August Kranti)',
  int_005: 'Lajpat Nagar (Moolchand Crossing)',
  int_006: 'Nehru Place Main Intersection',
  int_007: 'Karol Bagh (Pusa Road)',
  int_008: 'Dwarka Sector 10 Chowk',
  int_009: 'Rohini Sector 15 Crossing',
};

export default function VideoAnalysis() {
  const [result, setResult] = useState<VideoAnalysisResult | null>(null);
  const mappedSector = result?.intersections_detected?.[0]
    ? INTERSECTION_LABELS[result.intersections_detected[0]] ?? result.intersections_detected[0]
    : 'Awaiting sector assignment';

  return (
    <div className="h-full overflow-y-auto bg-[#f5f7fa] p-4 animate-in fade-in duration-700 sm:p-6 lg:p-8">
      <div className="mx-auto max-w-[1500px] space-y-8 pb-20">
        {/* Official Module Header */}
        <div className="flex flex-col gap-5 border-b-2 border-navy/10 pb-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-5">
            <div className="p-4 rounded bg-white border border-[#d1d9e2] shadow-sm">
              <FileVideo size={32} className="text-navy" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-black text-navy/40 uppercase tracking-[0.4em]">Vision Logic Bureau</span>
                <div className="px-1.5 py-0.5 bg-green/10 text-green text-[8px] font-black uppercase rounded border border-green/20">Active</div>
              </div>
              <h1 className="text-3xl font-black text-navy uppercase tracking-tight">Manual Vision</h1>
            </div>
          </div>
          <div className="flex items-center gap-4 self-start rounded border border-[#d1d9e2] bg-white px-5 py-3 shadow-sm">
            <Activity size={16} className="text-green animate-pulse" />
            <div className="flex flex-col">
              <span className="text-[9px] font-black text-navy/40 uppercase tracking-widest">Neural Status</span>
              <span className="text-xs font-black text-navy">CALIBRATED</span>
            </div>
          </div>
        </div>

        <div className={`grid gap-8 ${result ? 'xl:grid-cols-[minmax(0,1fr)_320px]' : 'grid-cols-1'}`}>
          {/* Main Analysis Workspace */}
          <div className="space-y-6">
            <div className="rounded-lg border-2 border-navy/10 bg-white shadow-xl overflow-hidden relative p-8">
              <VideoDropzone onAnalysisComplete={setResult} />
              
              {!result && (
                <div className="mt-8 border-t border-[#f0f2f5] pt-8 text-center">
                  <div className="max-w-md mx-auto space-y-4">
                    <p className="text-xs font-black text-navy uppercase tracking-[0.2em] leading-relaxed">
                      Initialize Manual Vision Review by Uploading Sector Footage
                    </p>
                    <p className="text-[10px] text-navy/40 font-medium leading-relaxed uppercase tracking-tighter">
                      AI processing will analyze vehicular classification, municipal density mapping, and optimal split-second timing calibration. Supported formats: .mp4, .avi, .mov (Max 50MB)
                    </p>
                  </div>
                </div>
              )}
            </div>

            {result && (
              <GovCard title="YOLO ANALYSIS DOSSIER" className="overflow-hidden p-0">
                <div className="border-b border-[#f0f2f5] bg-gray-50 px-6 py-4">
                  <p className="text-sm font-black uppercase tracking-wider text-navy">
                    Uploaded sector footage has been audited and converted into an operator-ready report.
                  </p>
                </div>
                <div className="p-4 sm:p-6">
                  <AnalysisResults result={result} />
                </div>
              </GovCard>
            )}
          </div>

          {/* Forensic Detection Results */}
          {result && (
            <div className="space-y-6 animate-in slide-in-from-right-4 duration-500 xl:sticky xl:top-6 xl:self-start">
               <div className="flex items-center gap-3 border-l-4 border-navy pl-4">
                  <h3 className="text-sm font-black text-navy uppercase tracking-widest">Forensic Matrix</h3>
               </div>
               <GovCard accent="navy" className="overflow-hidden">
                 <div className="flex items-center justify-between border-b border-[#f0f2f5] bg-gray-50 p-4">
                    <span className="text-[9px] font-black text-navy/40 uppercase">Audit Result_ID</span>
                    <span className="text-[9px] font-mono text-navy font-bold">#{result.video_id.toUpperCase()}</span>
                 </div>
                 <div className="space-y-4 p-4">
                   <div className="rounded border border-[#d1d9e2] bg-[#f8f9fa] p-3">
                     <p className="text-[9px] font-black uppercase tracking-widest text-navy/40">Mapped Sector</p>
                     <p className="mt-2 text-sm font-black text-navy">{mappedSector}</p>
                   </div>
                   <div className="rounded border border-[#d1d9e2] bg-[#f8f9fa] p-3">
                     <p className="text-[9px] font-black uppercase tracking-widest text-navy/40">Source File</p>
                     <p className="mt-2 break-all text-sm font-semibold text-navy">{result.filename}</p>
                   </div>
                   <div className="grid grid-cols-2 gap-3">
                     <div className="rounded border border-[#d1d9e2] bg-white p-3 text-center">
                       <p className="text-[9px] font-black uppercase tracking-widest text-navy/40">Frames</p>
                       <p className="mt-2 text-2xl font-black text-navy">{result.frames_processed}</p>
                     </div>
                     <div className="rounded border border-[#d1d9e2] bg-white p-3 text-center">
                       <p className="text-[9px] font-black uppercase tracking-widest text-navy/40">Latency</p>
                       <p className="mt-2 text-2xl font-black text-navy">{Math.round(result.processing_time_seconds)}s</p>
                     </div>
                   </div>
                   <div className="rounded border border-green/20 bg-green/5 p-3">
                     <p className="text-[9px] font-black uppercase tracking-widest text-green">Assessment</p>
                     <p className="mt-2 text-sm font-semibold leading-6 text-navy">
                       The detailed YOLO report is available in the main workspace with evidence frames, lane pressure, and adaptive timing recommendations.
                     </p>
                   </div>
                 </div>
                 <div className="p-3 bg-navy text-center">
                    <span className="text-[9px] font-black text-white uppercase tracking-[0.2em]">
                      Manual Vision Report Linked To Sector Workflow
                    </span>
                 </div>
               </GovCard>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
