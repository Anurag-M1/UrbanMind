import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { MainLayout } from './components/layout/main-layout';
import { SimulatorInit } from './components/simulator-init';
import { useTrafficStore, type CurrentPage } from './lib/store';
import Overview from './pages/Overview';
import VideoAnalysis from './pages/VideoAnalysis';
import Emergency from './pages/Emergency';
import Analytics from './pages/Analytics';
import ROIPage from './pages/ROIPage';
import Settings from './pages/Settings';
import DigitalTwin from './pages/DigitalTwin';
import AllFootages from './pages/AllFootages';

function AppContent() {
  const location = useLocation();
  const setCurrentPage = useTrafficStore((state) => state.setCurrentPage);

  useEffect(() => {
    const pageMap: Record<string, CurrentPage> = {
      '/overview': 'dashboard',
      '/footages': 'footages',
      '/video': 'video',
      '/analytics': 'analytics',
      '/emergency': 'emergency',
      '/roi': 'roi',
      '/digital-twin': 'digital-twin',
      '/settings': 'settings',
    };

    setCurrentPage(pageMap[location.pathname] ?? 'dashboard');
  }, [location.pathname, setCurrentPage]);

  return (
    <MainLayout>
      <SimulatorInit />
      <Routes>
        <Route path="/overview" element={<Overview />} />
        <Route path="/footages" element={<AllFootages />} />
        <Route path="/video" element={<VideoAnalysis />} />
        <Route path="/emergency" element={<Emergency />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/roi" element={<ROIPage />} />
        <Route path="/digital-twin" element={<DigitalTwin />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="*" element={<Navigate to="/overview" replace />} />
      </Routes>
    </MainLayout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
