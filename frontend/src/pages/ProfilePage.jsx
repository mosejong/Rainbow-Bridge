import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import Card from '../components/Card';

const SPECIES = ['강아지', '고양이', '기타'];

function ProfilePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    species: '강아지',
    start_date: '',
    end_date: '',
  });
  const [error, setError] = useState('');

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function handleNext(e) {
    e.preventDefault();
    setError('');

    if (!form.name.trim()) {
      setError('반려동물 이름을 입력해주세요.');
      return;
    }
    if (!form.start_date || !form.end_date) {
      setError('함께한 기간을 선택해주세요.');
      return;
    }

    navigate('/memories', { state: { profile: form } });
  }

  return (
    <div className="min-h-screen bg-purple-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-bold text-violet-600 text-center mb-1">🌈 레인보우 브릿지</h1>
        <p className="text-gray-500 text-center text-sm mb-6">소중한 가족을 기억해요</p>

        <Card>
          <h2 className="text-lg font-bold text-gray-800 mb-5">반려동물 프로필 입력</h2>

          <form onSubmit={handleNext} className="flex flex-col gap-5">
            {/* 이름 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                반려동물 이름 <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="예) 콩이"
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-gray-800 focus:outline-none focus:ring-2 focus:ring-violet-300"
              />
            </div>

            {/* 종 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">종</label>
              <div className="flex gap-3">
                {SPECIES.map((s) => (
                  <label key={s} className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="species"
                      value={s}
                      checked={form.species === s}
                      onChange={handleChange}
                      className="accent-violet-500"
                    />
                    <span className="text-gray-700 text-sm">{s}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 함께한 기간 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                함께한 기간 <span className="text-red-400">*</span>
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  name="start_date"
                  value={form.start_date}
                  onChange={handleChange}
                  className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
                />
                <span className="text-gray-400 text-sm">~</span>
                <input
                  type="date"
                  name="end_date"
                  value={form.end_date}
                  onChange={handleChange}
                  className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
                />
              </div>
            </div>

            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}

            <Button type="submit" variant="primary" className="w-full py-3 text-base">
              다음 — 추억 입력
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}

export default ProfilePage;
