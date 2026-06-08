import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { createPet } from '../api/pets';
import Button from '../components/Button';
import Card from '../components/Card';
import LoadingSpinner from '../components/LoadingSpinner';

const EMPTY_SLOT = { keyword: '', detail: '' };

function MemoriesPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const profile = location.state?.profile;

  const [slots, setSlots] = useState([
    { ...EMPTY_SLOT },
    { ...EMPTY_SLOT },
    { ...EMPTY_SLOT },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!profile) {
    navigate('/profile', { replace: true });
    return null;
  }

  function handleSlotChange(idx, field, value) {
    setSlots((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s))
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    const memories = slots
      .filter((s) => s.keyword.trim() !== '')
      .map((s) => ({ keyword: s.keyword.trim(), detail: s.detail.trim() }));

    if (memories.length === 0) {
      setError('추억 키워드를 최소 1개 입력해주세요.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        name: profile.name.trim(),
        species: profile.species,
        period: `${profile.start_date} ~ ${profile.end_date}`,
        memories,
      };
      const pet = await createPet(payload);
      localStorage.setItem('pet_id', pet.id || pet._id);
      localStorage.setItem('pet_name', pet.name);
      navigate('/emotion');
    } catch (err) {
      setError('저장 중 오류가 발생했어요. 다시 시도해주세요.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-purple-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-bold text-violet-600 text-center mb-1">🌈 레인보우 브릿지</h1>
        <p className="text-gray-500 text-center text-sm mb-6">소중한 가족을 기억해요</p>

        <Card>
          <button
            type="button"
            onClick={() => navigate('/profile', { state: { profile } })}
            className="flex items-center gap-1 text-gray-400 text-sm mb-4 hover:text-gray-600"
          >
            ← 이전
          </button>

          <h2 className="text-lg font-bold text-gray-800 mb-1">추억 키워드 입력</h2>
          <p className="text-sm text-gray-500 mb-5">
            {profile.name}와(과) 나눈 소중한 기억을 알려주세요.{' '}
            <span className="text-gray-400">(최대 3개)</span>
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {slots.map((slot, idx) => (
              <div key={idx} className="flex flex-col gap-1.5">
                <input
                  type="text"
                  value={slot.keyword}
                  onChange={(e) => handleSlotChange(idx, 'keyword', e.target.value)}
                  placeholder={`추억 키워드 ${idx + 1} (예: 공원 산책)`}
                  className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-gray-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-violet-300"
                />
                <input
                  type="text"
                  value={slot.detail}
                  onChange={(e) => handleSlotChange(idx, 'detail', e.target.value)}
                  placeholder="상세 내용 (예: 저녁마다 한강공원 같이 걸었어요)"
                  disabled={!slot.keyword.trim()}
                  className="w-full border border-gray-100 rounded-xl px-4 py-2.5 text-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-violet-200 disabled:bg-gray-50 disabled:text-gray-300 disabled:cursor-not-allowed"
                />
              </div>
            ))}

            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}

            {loading ? (
              <LoadingSpinner message="저장 중이에요..." />
            ) : (
              <Button type="submit" variant="primary" className="w-full py-3 text-base">
                다음 — 감정 체크인
              </Button>
            )}
          </form>
        </Card>
      </div>
    </div>
  );
}

export default MemoriesPage;
