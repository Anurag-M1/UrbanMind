export interface CameraNode {
  id: string;
  name: string;
  cameraId: string;
  sector: string;
  location: string;
  videoId: string;
  status: 'LIVE' | 'PRIORITY' | 'STANDBY';
  latencyMs: number;
}

export const CAMERA_NODES: CameraNode[] = [
  {
    id: 'node-ncr-01',
    name: 'Connaught Place Node',
    cameraId: 'NCR_CAM_0442',
    sector: 'Connaught Place (CP) Outer Circle',
    location: 'New Delhi',
    videoId: 'jJ9QfuZRhIk',
    status: 'LIVE',
    latencyMs: 24,
  },
  {
    id: 'node-ncr-02',
    name: 'ITO Junction Node',
    cameraId: 'NCR_CAM_0518',
    sector: 'ITO Junction (Vikas Marg)',
    location: 'ITO, New Delhi',
    videoId: '2juLrCH5w9U',
    status: 'PRIORITY',
    latencyMs: 27,
  },
  {
    id: 'node-ncr-03',
    name: 'AIIMS Crossing Node',
    cameraId: 'NCR_CAM_0631',
    sector: 'AIIMS Crossing (Ring Road)',
    location: 'Ansari Nagar, New Delhi',
    videoId: 'QIBmMEbLtKw',
    status: 'LIVE',
    latencyMs: 31,
  },
  {
    id: 'node-ncr-04',
    name: 'Hauz Khas Node',
    cameraId: 'NCR_CAM_0714',
    sector: 'Hauz Khas Junction (August Kranti)',
    location: 'Hauz Khas, New Delhi',
    videoId: 'zAQNfzTa_tw',
    status: 'STANDBY',
    latencyMs: 29,
  },
  {
    id: 'node-ncr-05',
    name: 'Lajpat Nagar Node',
    cameraId: 'NCR_CAM_0820',
    sector: 'Lajpat Nagar (Moolchand Crossing)',
    location: 'Lajpat Nagar, New Delhi',
    videoId: 'WYXViSsFvQs',
    status: 'LIVE',
    latencyMs: 25,
  },
  {
    id: 'node-ncr-06',
    name: 'Nehru Place Node',
    cameraId: 'NCR_CAM_0936',
    sector: 'Nehru Place Main Intersection',
    location: 'Nehru Place, New Delhi',
    videoId: '4wAQ-0tFXf0',
    status: 'PRIORITY',
    latencyMs: 28,
  },
  {
    id: 'node-ncr-07',
    name: 'Karol Bagh Node',
    cameraId: 'NCR_CAM_1044',
    sector: 'Karol Bagh (Pusa Road)',
    location: 'Karol Bagh, New Delhi',
    videoId: 'WYXViSsFvQs',
    status: 'LIVE',
    latencyMs: 26,
  },
  {
    id: 'node-ncr-08',
    name: 'Dwarka Sector 10 Node',
    cameraId: 'NCR_CAM_1172',
    sector: 'Dwarka Sector 10 Chowk',
    location: 'Dwarka, New Delhi',
    videoId: 'Nho7nVPWeTA',
    status: 'STANDBY',
    latencyMs: 30,
  },
  {
    id: 'node-ncr-09',
    name: 'Rohini Sector 15 Node',
    cameraId: 'NCR_CAM_1289',
    sector: 'Rohini Sector 15 Crossing',
    location: 'Rohini, New Delhi',
    videoId: '1xl0hX-nF2E',
    status: 'STANDBY',
    latencyMs: 32,
  },
];

export const DEFAULT_CAMERA_NODE_ID = CAMERA_NODES[0]?.id ?? 'node-ncr-01';

export function getCameraNodeById(nodeId?: string | null) {
  return CAMERA_NODES.find((node) => node.id === nodeId) ?? CAMERA_NODES[0];
}

export function buildCameraEmbedUrl(videoId: string, origin: string) {
  return `https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1&playsinline=1&loop=1&playlist=${videoId}&controls=0&modestbranding=1&rel=0&enablejsapi=1&origin=${encodeURIComponent(origin)}&t=${Date.now()}`;
}
