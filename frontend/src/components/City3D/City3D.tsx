import { useState, useCallback } from 'react';
import { Maximize, Minimize } from 'lucide-react';

interface City3DProps {
  intersections: any[];
  onIntersectionSelect?: (id: string) => void;
}

export default function City3D({ intersections, onIntersectionSelect }: City3DProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = useCallback(() => {
    const el = document.getElementById('sketchfab-container');
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  return (
    <div id="sketchfab-container" className="relative w-full h-full bg-[#f8f9fa] overflow-hidden group">
      {/* Sketchfab Live Preview */}
      <iframe
        title="UrbanMind Low Poly City Preview"
        frameBorder="0"
        allowFullScreen
        allow="autoplay; fullscreen; xr-spatial-tracking"
        xr-spatial-tracking="true"
        execution-while-out-of-viewport="true"
        execution-while-not-rendered="true"
        web-share="true"
        src="https://sketchfab.com/models/c5f3bb50fed947e8891b236bc85b4f7d/embed?autostart=1&internal=1&tracking=0&ui_ar=0&ui_infos=0&ui_snapshots=1&ui_stop=0&ui_theatre=1&ui_watermark=0"
        className="w-full h-full border-0 grayscale-[0.1] contrast-[1.05]"
      />

      {/* Control Overlay */}
      <div className="absolute top-4 right-4 flex gap-2 z-50 pointer-events-auto opacity-0 group-hover:opacity-100 transition-opacity">
        <button 
          onClick={toggleFullscreen} 
          className="bg-navy/90 text-white text-[10px] font-black uppercase tracking-widest py-2 px-4 rounded shadow-2xl border border-white/20 backdrop-blur-md flex items-center gap-2 hover:bg-navy transition-all" 
          title="Toggle Fullscreen"
        >
          {isFullscreen ? <Minimize size={12} /> : <Maximize size={12} />}
          {isFullscreen ? 'Exit Terminal' : 'Full Screen Entry'}
        </button>
      </div>

      {/* Formal HUD Frame */}
      <div className="absolute inset-0 pointer-events-none border border-navy/10">
        <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-navy/20" />
        <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-navy/20" />
        <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-navy/20" />
        <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-navy/20" />
      </div>
      
      {/* Flag Accent Line at map bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-1 flex z-10 pointer-events-none opacity-50">
        <div className="flex-1 bg-saffron" />
        <div className="flex-1 bg-white" />
        <div className="flex-1 bg-green" />
      </div>
    </div>
  );
}
