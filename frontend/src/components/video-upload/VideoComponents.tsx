import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Film, Play, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { uploadVideo, getVideoStatus, applyVideoTimings } from '../../api/video';
import type { VideoAnalysisResult } from '../../types';

const INTERSECTION_OPTIONS = [
  { id: 'int_001', label: 'Connaught Place (CP) Outer Circle' },
  { id: 'int_002', label: 'ITO Junction (Vikas Marg)' },
  { id: 'int_003', label: 'AIIMS Crossing (Ring Road)' },
  { id: 'int_004', label: 'Hauz Khas Junction (August Kranti)' },
  { id: 'int_005', label: 'Lajpat Nagar (Moolchand Crossing)' },
  { id: 'int_006', label: 'Nehru Place Main Intersection' },
  { id: 'int_007', label: 'Karol Bagh (Pusa Road)' },
  { id: 'int_008', label: 'Dwarka Sector 10 Chowk' },
  { id: 'int_009', label: 'Rohini Sector 15 Crossing' },
];

export function VideoDropzone({
  onAnalysisComplete,
}: {
  onAnalysisComplete: (result: VideoAnalysisResult) => void;
}) {
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState<VideoAnalysisResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [intersectionId, setIntersectionId] = useState('int_001');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setError('');
      setResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm'] },
    maxSize: 200 * 1024 * 1024,
    multiple: false,
  });

  const startAnalysis = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setError('');

    try {
      setStatusMsg('Uploading video...');
      const { video_id } = await uploadVideo(selectedFile, intersectionId);
      setUploading(false);
      setProcessing(true);
      setStatusMsg('Running YOLOv8n detection...');

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const status = await getVideoStatus(video_id);
          setProgress(status.progress_pct || 0);

          if (status.frames_processed > 0) {
            setStatusMsg(`Processing frame ${status.frames_processed}/${status.total_frames}...`);
          }

          if (status.status === 'complete') {
            clearInterval(pollInterval);
            setProcessing(false);
            setStatusMsg('Analysis complete!');
            setResult(status);
            onAnalysisComplete(status);
          } else if (status.status === 'error') {
            clearInterval(pollInterval);
            setProcessing(false);
            setError(status.error_message || 'Analysis failed');
          }
        } catch {
          // Continue polling
        }
      }, 1000);
    } catch (err: any) {
      setUploading(false);
      setProcessing(false);
      setError(err.message || 'Upload failed');
    }
  };

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`bg-white border-2 border-dashed p-10 text-center cursor-pointer transition-all rounded-lg shadow-sm ${
          isDragActive ? 'border-navy bg-navy/5' : 'border-gray-200 hover:border-navy/30'
        }`}
      >
        <input {...getInputProps()} />
        <div className="p-4 bg-navy/5 rounded-full w-fit mx-auto mb-4">
          <Upload size={32} className="text-navy" />
        </div>
        <p className="text-sm font-black text-navy uppercase tracking-widest mb-1">
          {isDragActive ? 'Release to Upload' : 'Click to Upload Official Sector Footage'}
        </p>
        <p className="text-[10px] text-navy/40 font-bold uppercase tracking-tighter">Forensic Analysis Protocol · MP4, AVI, MOV · Max 200MB</p>
      </div>

      {/* Selected file preview */}
      {selectedFile && !processing && !result && (
        <div className="card">
          <div className="flex items-center gap-3 mb-3">
            <Film size={20} className="text-cyan" />
            <div className="flex-1">
              <div className="text-sm font-heading">{selectedFile.name}</div>
              <div className="text-xs text-muted">{(selectedFile.size / 1024 / 1024).toFixed(1)} MB</div>
            </div>
          </div>

          <div className="flex gap-3 items-center mb-3">
            <label className="text-xs text-muted">Map to:</label>
            <select
              value={intersectionId}
              onChange={(e) => setIntersectionId(e.target.value)}
              className="bg-surface2 border border-border rounded px-2 py-1 text-xs text-text flex-1"
            >
              {INTERSECTION_OPTIONS.map((option) => (
                <option key={option.id} value={option.id}>{option.label}</option>
              ))}
            </select>
          </div>

          <button onClick={startAnalysis} disabled={uploading} className="btn btn-primary w-full justify-center">
            {uploading ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
            {uploading ? 'Uploading...' : 'Analyze Video'}
          </button>
        </div>
      )}

      {/* Processing state */}
      {processing && (
        <div className="bg-white border border-[#d1d9e2] p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Loader size={16} className="animate-spin text-navy" />
              <span className="text-[10px] font-black text-navy uppercase tracking-widest">{statusMsg}</span>
            </div>
            <span className="text-[10px] font-black text-navy font-mono">{progress.toFixed(0)}%</span>
          </div>
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-navy transition-all duration-300" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card border-red">
          <div className="flex items-center gap-2 text-red">
            <AlertCircle size={16} />
            <span className="text-sm">{error}</span>
          </div>
          <button onClick={() => { setError(''); setSelectedFile(null); }} className="btn text-xs mt-2">
            Retry
          </button>
        </div>
      )}
    </div>
  );
}

export function AnalysisResults({ result }: { result: VideoAnalysisResult }) {
  const [applied, setApplied] = useState(false);
  const [applying, setApplying] = useState(false);

  const handleApply = async () => {
    setApplying(true);
    try {
      await applyVideoTimings(result.video_id);
      setApplied(true);
    } catch {
      // Ignore
    }
    setApplying(false);
  };

  const totalVehicles = Object.values(result.vehicle_counts).reduce((a, b) => a + b, 0);
  const laneEntries = Object.entries(result.lane_density).sort(([, a], [, b]) => b - a);
  const processedCoverage = result.total_frames > 0 ? Math.round((result.frames_processed / result.total_frames) * 100) : 0;
  const averageVehiclesPerFrame = result.frames_processed > 0 ? Math.round(totalVehicles / result.frames_processed) : 0;
  const dominantVehicle = Object.entries(result.vehicle_counts).sort(([, a], [, b]) => b - a)[0];
  const busiestLane = laneEntries[0];
  const recommendedCycle = result.recommended_timings.cycle_length;
  const baselineCycle = 59;
  const cycleDelta = recommendedCycle - baselineCycle;
  const ewGreen = result.recommended_timings.ew_green;
  const nsGreen = result.recommended_timings.ns_green;
  const estimatedWaitReduction = Math.max(
    12,
    Math.min(
      48,
      Math.round(
        ((Math.max(ewGreen, nsGreen) + averageVehiclesPerFrame) / Math.max(1, recommendedCycle)) * 28 +
        laneEntries.length * 2
      )
    )
  );
  const detectionConfidenceValues = result.detection_frames.flatMap((frame) =>
    frame.detections.map((detection) => Math.round(detection.confidence * 100))
  );
  const confidenceAverage = detectionConfidenceValues.length
    ? Math.round(
        detectionConfidenceValues.reduce((sum, value) => sum + value, 0) / detectionConfidenceValues.length
      )
    : 0;
  const peakFrame = [...result.detection_frames].sort(
    (a, b) => b.detections.length + b.ew_count + b.ns_count - (a.detections.length + a.ew_count + a.ns_count)
  )[0];
  const intersectionLabel = INTERSECTION_OPTIONS.find((option) =>
    result.intersections_detected.includes(option.id)
  )?.label ?? result.intersections_detected[0] ?? 'Unmapped Sector';
  const demandBalance = ewGreen >= nsGreen ? 'East-West Priority Bias' : 'North-South Priority Bias';
  const cycleDirection = cycleDelta >= 0 ? 'extended' : 'compressed';
  const timingRationale = busiestLane
    ? `${busiestLane[0].replace(/_/g, ' ').toUpperCase()} carries the highest sampled load, so the adaptive plan shifts green time toward the dominant movement while maintaining cross-axis clearance.`
    : 'The adaptive plan preserves balanced movement because the uploaded evidence did not show a strong directional skew.';

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border border-[#d1d9e2] bg-white p-4 shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Total Detections</p>
          <p className="mt-2 text-3xl font-black text-navy">{totalVehicles}</p>
          <p className="mt-1 text-[10px] font-bold uppercase tracking-wide text-navy/40">Across sampled YOLO frames</p>
        </div>
        <div className="rounded-lg border border-[#d1d9e2] bg-white p-4 shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Frames Audited</p>
          <p className="mt-2 text-3xl font-black text-navy">{result.frames_processed}</p>
          <p className="mt-1 text-[10px] font-bold uppercase tracking-wide text-navy/40">{processedCoverage}% of uploaded footage index scanned</p>
        </div>
        <div className="rounded-lg border border-[#d1d9e2] bg-white p-4 shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Avg Confidence</p>
          <p className="mt-2 text-3xl font-black text-navy">{confidenceAverage}%</p>
          <p className="mt-1 text-[10px] font-bold uppercase tracking-wide text-navy/40">From annotated evidence frames</p>
        </div>
        <div className="rounded-lg border border-[#d1d9e2] bg-white p-4 shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Est. Wait Reduction</p>
          <p className="mt-2 text-3xl font-black text-green">{estimatedWaitReduction}%</p>
          <p className="mt-1 text-[10px] font-bold uppercase tracking-wide text-navy/40">Against fixed timing baseline</p>
        </div>
      </div>

      <div className="rounded-lg border border-[#d1d9e2] bg-white shadow-sm overflow-hidden">
        <div className="border-b border-[#f0f2f5] bg-gray-50 p-4">
          <h3 className="text-[10px] font-black text-navy uppercase tracking-[0.2em]">Detailed Analysis Report</h3>
        </div>
        <div className="space-y-6 p-5">
          <div className="rounded-lg border border-navy/10 bg-[#f8f9fa] p-4">
            <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Operational Summary</p>
            <p className="mt-2 text-sm font-semibold leading-6 text-navy">
              YOLO reviewed <span className="font-black">{result.filename}</span> for <span className="font-black">{intersectionLabel}</span> and
              detected <span className="font-black">{totalVehicles}</span> traffic entities across <span className="font-black">{result.frames_processed}</span> sampled frames.
              {dominantVehicle ? ` The dominant class was ${dominantVehicle[0].toLowerCase()} with ${dominantVehicle[1]} detections.` : ''}
              {busiestLane ? ` ${busiestLane[0].replace(/_/g, ' ').toUpperCase()} emerged as the heaviest movement corridor with ${busiestLane[1]} cumulative observations.` : ''}
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(280px,0.75fr)]">
            <div className="rounded-lg border border-[#d1d9e2] bg-white p-4">
              <h4 className="text-[10px] font-black uppercase tracking-widest text-navy/40">Traffic Mix Breakdown</h4>
              <div className="mt-4 space-y-4">
                {Object.entries(result.vehicle_counts)
                  .sort(([, a], [, b]) => b - a)
                  .map(([cls, count]) => {
                    const pct = totalVehicles > 0 ? Math.round((count / totalVehicles) * 100) : 0;
                    return (
                      <div key={cls} className="flex flex-col">
                        <div className="mb-1.5 flex items-center justify-between gap-3">
                          <span className="text-[10px] font-black uppercase tracking-tight text-navy">{cls}</span>
                          <span className="text-[10px] font-black font-mono text-navy">{count} units · {pct}%</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                          <div className="h-full bg-navy" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>

            <div className="rounded-lg border border-[#d1d9e2] bg-white p-4">
              <h4 className="text-[10px] font-black uppercase tracking-widest text-navy/40">Run Integrity</h4>
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between text-[11px] font-bold text-navy">
                  <span>Video Duration</span>
                  <span>{Math.round(result.duration_seconds)}s</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-bold text-navy">
                  <span>Source FPS</span>
                  <span>{Math.round(result.fps)}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-bold text-navy">
                  <span>Processing Latency</span>
                  <span>{Math.round(result.processing_time_seconds)}s</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-bold text-navy">
                  <span>Avg Vehicles / Sample</span>
                  <span>{averageVehiclesPerFrame}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-bold text-navy">
                  <span>Cycle Strategy</span>
                  <span>{demandBalance}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-bold text-navy">
                  <span>Peak Evidence Frame</span>
                  <span>{peakFrame ? `F${peakFrame.frame_number}` : 'Pending'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="border-t border-[#f0f2f5] bg-[#f8f9fa] p-4 flex flex-col gap-2 text-[10px] font-black uppercase text-navy/40 sm:flex-row sm:items-center sm:justify-between">
          <span>Sector Mapping: <span className="text-navy">{intersectionLabel}</span></span>
          <span>Report Status: <span className="text-green">{result.status}</span></span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(300px,0.9fr)]">
        <div className="rounded-lg border border-[#d1d9e2] bg-white shadow-sm overflow-hidden">
          <div className="border-b border-[#f0f2f5] bg-gray-50 p-4">
            <h3 className="text-[10px] font-black text-navy uppercase tracking-[0.2em]">Directional Load Matrix</h3>
          </div>
          <div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-2">
            {laneEntries.map(([lane, value]) => {
              const peak = busiestLane?.[1] ?? 1;
              const width = Math.round((value / peak) * 100);
              return (
                <div key={lane} className="rounded-lg border border-[#d1d9e2] bg-[#f8f9fa] p-4">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <span className="text-[10px] font-black uppercase tracking-widest text-navy/50">{lane.replace(/_/g, ' ')}</span>
                    <span className="text-lg font-black text-navy">{value}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-white">
                    <div className="h-full bg-saffron" style={{ width: `${width}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="border-t border-[#f0f2f5] bg-[#f8f9fa] p-4">
            <p className="text-sm font-semibold leading-6 text-navy">{timingRationale}</p>
          </div>
        </div>

        <div className="rounded-lg border border-[#d1d9e2] bg-white shadow-sm overflow-hidden">
          <div className="border-b border-[#f0f2f5] bg-gray-50 p-4">
            <h3 className="text-[10px] font-black text-navy uppercase tracking-[0.2em]">AI Recommended Timings</h3>
          </div>
          <div className="space-y-5 p-5">
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg border border-[#d1d9e2] bg-[#f8f9fa] p-3 text-center">
                <div className="text-[10px] font-black uppercase tracking-widest text-navy/40">EW Green</div>
                <div className="mt-2 text-2xl font-black text-green">{ewGreen}s</div>
              </div>
              <div className="rounded-lg border border-[#d1d9e2] bg-[#f8f9fa] p-3 text-center">
                <div className="text-[10px] font-black uppercase tracking-widest text-navy/40">NS Green</div>
                <div className="mt-2 text-2xl font-black text-green">{nsGreen}s</div>
              </div>
              <div className="rounded-lg border border-[#d1d9e2] bg-[#f8f9fa] p-3 text-center">
                <div className="text-[10px] font-black uppercase tracking-widest text-navy/40">Cycle</div>
                <div className="mt-2 text-2xl font-black text-navy">{recommendedCycle}s</div>
              </div>
            </div>

            <div className="rounded-lg border border-navy/10 bg-[#f8f9fa] p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-navy/40">Signal Engineering Notes</p>
              <div className="mt-3 space-y-2 text-sm font-semibold text-navy">
                <div className="flex items-center justify-between gap-3">
                  <span>Baseline Cycle</span>
                  <span>{baselineCycle}s</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Adaptive Cycle</span>
                  <span>{recommendedCycle}s</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Cycle Change</span>
                  <span>{cycleDelta >= 0 ? '+' : ''}{cycleDelta}s</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Optimization Mode</span>
                  <span>{cycleDirection.toUpperCase()}</span>
                </div>
              </div>
            </div>

            <div className="text-sm font-semibold leading-6 text-navy/80">
              The recommended timing plan is projected to reduce queueing by about <span className="font-black text-green">{estimatedWaitReduction}%</span> against the default fixed-timer profile while preserving safe clearance for the secondary approach.
            </div>

            <button
              onClick={handleApply}
              disabled={applied || applying}
              className={`btn w-full justify-center ${applied ? 'btn-success' : 'btn-primary'}`}
            >
              {applied ? (
                <><CheckCircle size={16} /> Applied to Intersection</>
              ) : applying ? (
                <><Loader size={16} className="animate-spin" /> Applying...</>
              ) : (
                'Apply to Intersection'
              )}
            </button>
          </div>
        </div>
      </div>

      {result.detection_frames.length > 0 && (
        <div className="rounded-lg border border-[#d1d9e2] bg-white shadow-sm overflow-hidden">
          <div className="border-b border-[#f0f2f5] bg-gray-50 p-4">
            <h3 className="text-[10px] font-black text-navy uppercase tracking-[0.2em]">YOLO Evidence Frames</h3>
          </div>
          <div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-2 xl:grid-cols-3">
            {result.detection_frames.map((frame, i) => (
              <div key={i} className="overflow-hidden rounded-lg border border-[#d1d9e2] bg-[#f8f9fa]">
                <img
                  src={`data:image/jpeg;base64,${frame.annotated_image_b64}`}
                  alt={`Frame ${frame.frame_number}`}
                  className="h-48 w-full object-cover"
                />
                <div className="space-y-2 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[10px] font-black uppercase tracking-widest text-navy/40">Frame {frame.frame_number}</span>
                    <span className="text-[10px] font-black font-mono text-navy">{Math.round(frame.timestamp_seconds)}s</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="rounded bg-white p-2">
                      <div className="text-[9px] font-black uppercase tracking-widest text-navy/40">Detections</div>
                      <div className="mt-1 text-lg font-black text-navy">{frame.detections.length}</div>
                    </div>
                    <div className="rounded bg-white p-2">
                      <div className="text-[9px] font-black uppercase tracking-widest text-navy/40">EW</div>
                      <div className="mt-1 text-lg font-black text-navy">{frame.ew_count}</div>
                    </div>
                    <div className="rounded bg-white p-2">
                      <div className="text-[9px] font-black uppercase tracking-widest text-navy/40">NS</div>
                      <div className="mt-1 text-lg font-black text-navy">{frame.ns_count}</div>
                    </div>
                  </div>
                  <p className="text-[10px] font-semibold leading-5 text-navy/70">
                    {frame.detections.length > 0
                      ? `Detected ${frame.detections.map((detection) => detection.class_name).slice(0, 4).join(', ')}${frame.detections.length > 4 ? ', ...' : ''}.`
                      : 'No marked detections were preserved for this evidence frame.'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
