import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SafetyModal from '../components/SafetyModal';
import Button from '../components/Button';
import { postEmotion } from '../api/emotions';

const MOODS = [
  { emoji: '😊', label: '괜찮아요',     score: 9 },
  { emoji: '😔', label: '슬퍼요',       score: 6 },
  { emoji: '😢', label: '많이 힘들어요', score: 3 },
  { emoji: '😰', label: '너무 힘들어요', score: 1 },
  { emoji: '😶', label: '잘 모르겠어요', score: 5 },
];

const RISK_MOODS = ['너무 힘들어요'];

export default function EmotionPage() {
  const navigate = useNavigate();
  const [selectedMood, setSelectedMood] = useState(null);
  const [note, setNote] = useState('');
  const [safetyOpen, setSafetyOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!selectedMood) {
      setError('오늘 기분을 선택해주세요.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const petId = localStorage.getItem('pet_id');
      const moodScore = MOODS.find((m) => m.label === selectedMood)?.score ?? 5;
      const response = await postEmotion({ pet_id: petId, score: moodScore, note });

      if (response.risk_level >= 2 || RISK_MOODS.includes(selectedMood)) {
        setSafetyOpen(true);
        return;
      }
      navigate('/message');
    } catch {
      // 백엔드 연결 전 mock 처리
      if (RISK_MOODS.includes(selectedMood)) {
        setSafetyOpen(true);
        return;
      }
      navigate('/message');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-purple-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-2">오늘 기분이 어떠세요?</h1>
        <p className="text-gray-500 text-center text-sm mb-8">솔직하게 선택해주세요.</p>

        <div className="flex flex-col gap-3 mb-8">
          {MOODS.map(({ emoji, label }) => (
            <button
              key={label}
              onClick={() => setSelectedMood(label)}
              className={`flex items-center gap-4 p-4 rounded-2xl border-2 transition-all text-left
                ${selectedMood === label
                  ? 'border-violet-500 bg-violet-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-violet-300'}`}
            >
              <span className="text-3xl">{emoji}</span>
              <span className={`font-medium ${selectedMood === label ? 'text-violet-700' : 'text-gray-700'}`}>
                {label}
              </span>
            </button>
          ))}
        </div>

        <div className="mb-6">
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="오늘 있었던 일을 적어도 좋아요. (선택)"
            className="w-full p-4 rounded-2xl border border-gray-200 bg-white resize-none text-gray-700 text-sm focus:outline-none focus:border-violet-400"
            rows={3}
          />
        </div>

        {error && <p className="text-red-500 text-sm text-center mb-3">{error}</p>}

        <Button onClick={handleSubmit} disabled={loading} variant="primary">
          {loading ? '기록 중...' : '기록하기'}
        </Button>
      </div>

      <SafetyModal isOpen={safetyOpen} onClose={() => { setSafetyOpen(false); navigate('/message'); }} />
    </div>
  );
}
