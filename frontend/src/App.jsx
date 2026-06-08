import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ProfilePage from './pages/ProfilePage';
import EmotionPage from './pages/EmotionPage';
import MessagePage from './pages/MessagePage';
import ReportPage from './pages/ReportPage';
import MissionPage from './pages/MissionPage';
import TtsPage from './pages/TtsPage';
import TimelinePage from './pages/TimelinePage';
import MediaPage from './pages/MediaPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import SymptomsPage from './pages/SymptomsPage';
import HealthRecordsPage from './pages/HealthRecordsPage';
import FuneralPage from './pages/FuneralPage';
import MemoriesPage from './pages/MemoriesPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/memories" element={<MemoriesPage />} />
        <Route path="/symptoms" element={<SymptomsPage />} />
        <Route path="/health-records" element={<HealthRecordsPage />} />
        <Route path="/funeral" element={<FuneralPage />} />
        <Route path="/emotion" element={<EmotionPage />} />
        <Route path="/message" element={<MessagePage />} />
        <Route path="/tts" element={<TtsPage />} />
        <Route path="/mission" element={<MissionPage />} />
        <Route path="/timeline" element={<TimelinePage />} />
        <Route path="/media" element={<MediaPage />} />
        <Route path="/report" element={<ReportPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
