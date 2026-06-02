import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ProfilePage from './pages/ProfilePage';

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
        <Route path="/" element={<Navigate to="/profile" replace />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/emotion" element={<ComingSoon name="감정 체크인" />} />
        <Route path="/message" element={<ComingSoon name="AI 추모 메시지" />} />
        <Route path="/tts" element={<ComingSoon name="TTS 음성 낭독" />} />
        <Route path="/mission" element={<ComingSoon name="미션 카드" />} />
        <Route path="/timeline" element={<ComingSoon name="추모 타임라인" />} />
        <Route path="/report" element={<ComingSoon name="평가 리포트" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
