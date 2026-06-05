import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';

const MOCK_HOSPITALS = [
  { id: 'h1', name: '24시 행복동물병원', distance: '0.3km', phone: '02-1234-5678', hours: '24시간', emergency: true },
  { id: 'h2', name: '푸른숲 동물메디컬센터', distance: '0.7km', phone: '02-9876-5432', hours: '09:00~21:00', emergency: false },
  { id: 'h3', name: '사랑 동물병원', distance: '1.2km', phone: '031-1111-2222', hours: '09:00~19:00', emergency: false },
];

const SYMPTOMS = [
  { id: 'no_eat',    emoji: '🍽️', label: '밥을 잘 안 먹어요' },
  { id: 'too_drink', emoji: '💧', label: '물을 과하게 마셔요' },
  { id: 'vomit',     emoji: '🤢', label: '자주 구토해요' },
  { id: 'lethargy',  emoji: '😴', label: '기운이 없고 잘 움직이지 않아요' },
  { id: 'breath',    emoji: '😮‍💨', label: '숨을 힘들게 쉬어요' },
  { id: 'cough',     emoji: '😷', label: '기침을 자주 해요' },
  { id: 'toilet',    emoji: '🚽', label: '대소변에 이상이 있어요' },
  { id: 'lump',      emoji: '🔴', label: '몸에 혹이나 부종이 생겼어요' },
  { id: 'discharge', emoji: '👁️', label: '눈물·콧물·눈곱이 심해요' },
  { id: 'limp',      emoji: '🦴', label: '절뚝거리거나 걸음이 이상해요' },
];

const MOCK_GUIDE = {
  no_eat:    '식욕 저하는 소화기 질환, 구강 통증, 스트레스 등 다양한 원인이 있습니다. 2일 이상 지속되면 내과 진료를 받으세요.',
  too_drink: '다음다갈(물 과다 섭취)은 당뇨·신장 질환의 신호일 수 있습니다. 신속히 혈액·소변 검사를 받으세요.',
  vomit:     '구토가 하루 3회 이상이거나 혈액이 섞여 있으면 즉시 응급 처치가 필요합니다.',
  lethargy:  '무기력함은 발열, 빈혈, 통증 등의 증상과 함께 나타날 수 있습니다. 체온을 체크하고 수의사 진료를 권장합니다.',
  breath:    '호흡 곤란은 응급 상황일 수 있습니다. 지금 바로 가까운 동물병원 응급실로 가세요.',
  cough:     '기침이 1주일 이상 지속되거나 갑자기 심해지면 심장·기관지 검사가 필요합니다.',
  toilet:    '혈뇨·혈변·변비가 24시간 이상 지속되면 내과·외과 협진이 필요할 수 있습니다.',
  lump:      '새로 생긴 혹은 종양 가능성이 있습니다. 크기·위치를 사진으로 기록 후 정기 검진을 받으세요.',
  discharge: '눈·코 분비물이 짙은 색이거나 냄새가 나면 감염 여부 확인이 필요합니다.',
  limp:      '갑작스러운 파행은 골절, 관절염, 디스크 신호일 수 있습니다. X-ray 검사를 권장합니다.',
};

export default function SymptomsPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(new Set());
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const petName = localStorage.getItem('pet_name') || '소중한 친구';

  function toggleSymptom(id) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
    setGuide(null);
  }

  async function handleSubmit() {
    if (selected.size === 0) {
      setError('증상을 하나 이상 선택해주세요.');
      return;
    }
    setError('');
    setLoading(true);

    // 선택 증상 저장
    localStorage.setItem('symptoms', JSON.stringify([...selected]));

    // TODO: POST /api/v1/health 연동 시 여기서 API 호출
    await new Promise((r) => setTimeout(r, 800));

    // mock AI 진료 안내 조합
    const guides = [...selected]
      .map((id) => MOCK_GUIDE[id])
      .filter(Boolean)
      .join('\n\n');
    setGuide(guides || '수의사 진료를 받아보시기를 권장합니다.');
    setLoading(false);
  }

  function openKakaoMap() {
    const query = encodeURIComponent('동물병원');
    window.open(`https://map.kakao.com/link/search/${query}`, '_blank');
  }

  return (
    <div className="min-h-screen bg-purple-50 px-4 py-10">
      <div className="w-full max-w-sm mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-1">
          {petName}의 증상 확인
        </h1>
        <p className="text-gray-500 text-center text-sm mb-8">
          해당하는 증상을 모두 선택해주세요.
        </p>

        {/* 증상 체크리스트 */}
        <div className="flex flex-col gap-3 mb-6">
          {SYMPTOMS.map(({ id, emoji, label }) => {
            const active = selected.has(id);
            return (
              <button
                key={id}
                onClick={() => toggleSymptom(id)}
                className={`flex items-center gap-4 p-4 rounded-2xl border-2 transition-all text-left
                  ${active
                    ? 'border-violet-500 bg-violet-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-violet-300'}`}
              >
                <span className="text-2xl">{emoji}</span>
                <span className={`font-medium text-sm ${active ? 'text-violet-700' : 'text-gray-700'}`}>
                  {label}
                </span>
                {active && (
                  <span className="ml-auto text-violet-500 text-lg font-bold">✓</span>
                )}
              </button>
            );
          })}
        </div>

        {error && <p className="text-red-500 text-sm text-center mb-3">{error}</p>}

        {!guide && (
          <Button variant="primary" onClick={handleSubmit} disabled={loading}>
            {loading ? <LoadingSpinner message="" /> : 'AI 진료 안내 받기'}
          </Button>
        )}

        {/* AI 진료 안내 결과 */}
        {guide && (
          <Card className="bg-violet-50 border border-violet-100 mb-4">
            <p className="text-sm font-semibold text-violet-700 mb-3">AI 진료 안내</p>
            <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{guide}</p>
            <p className="text-gray-400 text-xs mt-4">
              * AI 안내는 참고용입니다. 정확한 진단은 수의사에게 받으세요.
            </p>
          </Card>
        )}

        {guide && (
          <>
            {/* 주변 병원 목록 */}
            <p className="text-xs text-gray-400 text-center mb-2">주변 동물병원 (예시)</p>
            <div className="flex flex-col gap-3 mb-4">
              {MOCK_HOSPITALS.map((h) => (
                <Card key={h.id} className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <p className="font-semibold text-gray-800 text-sm">{h.name}</p>
                        {h.emergency && (
                          <span className="text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded-full font-semibold">응급</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">{h.distance} · {h.hours}</p>
                      <a href={`tel:${h.phone}`} className="text-xs text-violet-600 mt-0.5 block">{h.phone}</a>
                    </div>
                    <button
                      onClick={() => window.open(`https://map.kakao.com/link/search/${encodeURIComponent(h.name)}`, '_blank')}
                      className="shrink-0 text-xs bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold px-2.5 py-1.5 rounded-lg"
                    >
                      지도
                    </button>
                  </div>
                </Card>
              ))}
            </div>

            <div className="flex flex-col gap-3">
              <Button variant="primary" onClick={openKakaoMap}>
                📍 더 많은 동물병원 찾기
              </Button>
              <Button variant="ghost" onClick={() => navigate('/health-records')}>
                💊 투약·검진 기록 관리
              </Button>
              <Button variant="ghost" onClick={() => { setGuide(null); setSelected(new Set()); }}>
                증상 다시 선택
              </Button>
              <Button variant="ghost" onClick={() => navigate('/emotion')}>
                감정 체크인으로 이동
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
