import type { VideoAnalysisResult } from '../types';

const API_BASE = '/api/v1/video';

export async function uploadVideo(file: File, intersectionId: string = 'int_001'): Promise<{ video_id: string; status: string }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('intersection_id', intersectionId);

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function getVideoStatus(videoId: string): Promise<VideoAnalysisResult> {
  const res = await fetch(`${API_BASE}/${videoId}/status`);
  if (!res.ok) throw new Error('Failed to get video status');
  return res.json();
}

export async function getVideoFrames(videoId: string, limit: number = 20): Promise<{ frames: any[] }> {
  const res = await fetch(`${API_BASE}/${videoId}/frames?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to get frames');
  return res.json();
}

export async function applyVideoTimings(videoId: string): Promise<{ applied: boolean; timings: Record<string, number> }> {
  const res = await fetch(`${API_BASE}/${videoId}/apply`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to apply timings');
  return res.json();
}

export async function listVideos(): Promise<{ videos: any[] }> {
  const res = await fetch(`${API_BASE}/list`);
  if (!res.ok) throw new Error('Failed to list videos');
  return res.json();
}
