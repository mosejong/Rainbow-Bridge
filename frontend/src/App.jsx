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

function ComingSoon({ name }) {
  return (
    <div className="min-h-screen bg-purple-50 flex items-center justify-center">
      <div className="text-center">
        <p className="text-4xl mb-3">🚧</p>
        <p className="text-violet-600 font-bold text-lg">{name}</p>
        <p className="text-gray-400 text-sm mt-1">준비 중이에요</p>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/profile" element={<ProfilePage />} />
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
