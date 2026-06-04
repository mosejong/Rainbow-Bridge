import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPet } from '../api/pets';
import Button from '../components/Button';
import Card from '../components/Card';
import LoadingSpinner from '../components/LoadingSpinner';

const SPECIES = ['강아지', '고양이', '기타'];

function ProfilePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    species: '강아지',
    start_date: '',
    end_date: '',
    memories: [],
    photo: null,
  });
  const [memoryInput, setMemoryInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function handleMemoryKeyDown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      const keyword = memoryInput.trim();
      if (!keyword || form.memories.length >= 3) return;
      setForm((prev) => ({ ...prev, memories: [...prev.memories, keyword] }));
      setMemoryInput('');
    }
  }

  function removeMemory(idx) {
    setForm((prev) => ({
      ...prev,
      memories: prev.memories.filter((_, i) => i !== idx),
    }));
  }

  function handlePhoto(e) {
    setForm((prev) => ({ ...prev, photo: e.target.files[0] || null }));
  }

  async function handleSubmit(e) {
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

    setLoading(true);
    try {
      const payload = {
        name: form.name.trim(),
        species: form.species,
        period: `${form.start_date} ~ ${form.end_date}`,
        memories: form.memories,
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
          <h2 className="text-lg font-bold text-gray-800 mb-5">반려동물 프로필 입력</h2>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
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

            {/* 추억 키워드 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                추억 키워드{' '}
                <span className="text-gray-400 font-normal">(최대 3개, 엔터로 추가)</span>
              </label>
              <input
                type="text"
                value={memoryInput}
                onChange={(e) => setMemoryInput(e.target.value)}
                onKeyDown={handleMemoryKeyDown}
                placeholder="예) 공원 산책"
                disabled={form.memories.length >= 3}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-gray-800 focus:outline-none focus:ring-2 focus:ring-violet-300 disabled:bg-gray-50 disabled:text-gray-400"
              />
              {form.memories.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {form.memories.map((m, i) => (
                    <span
                      key={i}
                      className="flex items-center gap-1 bg-violet-100 text-violet-700 text-sm px-3 py-1 rounded-full"
                    >
                      {m}
                      <button
                        type="button"
                        onClick={() => removeMemory(i)}
                        className="text-violet-400 hover:text-violet-700 ml-1 leading-none"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* 사진 업로드 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                사진 <span className="text-gray-400 font-normal">(선택)</span>
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handlePhoto}
                className="w-full text-sm text-gray-500 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:bg-violet-100 file:text-violet-700 file:font-medium hover:file:bg-violet-200 cursor-pointer"
              />
              {form.photo && (
                <p className="text-xs text-gray-400 mt-1">{form.photo.name}</p>
              )}
            </div>

            {/* 에러 */}
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}

            {/* 제출 */}
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

export default ProfilePage;
