import { useState } from 'react';
import SafetyModal from './components/SafetyModal';

function App() {
  const [safetyOpen, setSafetyOpen] = useState(false);

  return (
    <div className="min-h-screen bg-purple-50 flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold text-violet-600 mb-2">🌈 레인보우 브릿지</h1>
      <p className="text-gray-500 mb-8">반려동물 펫로스 회복 서비스</p>

      <button
        onClick={() => setSafetyOpen(true)}
        className="bg-red-500 text-white px-6 py-3 rounded-xl font-bold hover:bg-red-600"
      >
        1393 모달 테스트
      </button>

      <SafetyModal isOpen={safetyOpen} onClose={() => setSafetyOpen(false)} />
    </div>
  );
}

export default App;
