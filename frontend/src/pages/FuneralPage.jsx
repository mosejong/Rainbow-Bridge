import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';

const MOCK_FUNERAL_HOMES = [
  {
    id: 'f1',
    name: '하늘숲 반려동물 장례식장',
    location: '서울 강동구',
    phone: '02-1234-5678',
    distance: '1.2km',
    hours: '24시간',
    services: ['개별화장', '합동화장', '납골함'],
  },
  {
    id: 'f2',
    name: '무지개 반려동물 장례원',
    location: '서울 송파구',
    phone: '02-8765-4321',
    distance: '2.4km',
    hours: '08:00~22:00',
    services: ['개별화장', '수목장'],
  },
  {
    id: 'f3',
    name: '별이된 친구들 장례원',
    location: '경기 하남시',
    phone: '031-111-2222',
    distance: '5.7km',
    hours: '09:00~21:00',
    services: ['개별화장', '합동화장', '납골당'],
  },
];

const CONSULT_TREE = {
  start: {
    ai: '이별을 준비하면서 어떤 점이 가장 걱정되세요?',
    options: [
      { label: '장례 비용이 얼마나 될지 모르겠어요', next: 'cost' },
      { label: '화장과 매장 중 어떤 게 좋을지 모르겠어요', next: 'method' },
      { label: '언제 연락해야 할지 모르겠어요', next: 'timing' },
      { label: '가족에게 어떻게 알려야 할지 막막해요', next: 'family' },
    ],
  },
  cost: {
    ai: '반려동물 장례 비용은 보통 화장 기준 15~50만원입니다. 크기와 방식(개별/합동 화장)에 따라 달라져요. 개별 화장을 선택하면 유골을 개별 수령할 수 있어요. 미리 여러 곳에 문의해 비교해보는 걸 권장해요.',
    options: [
      { label: '화장 방법에 대해 더 알고 싶어요', next: 'method' },
      { label: '다른 질문이 있어요', next: 'start' },
    ],
  },
  method: {
    ai: '화장은 유골을 납골함·수목장·산골로 간직할 수 있어 가장 많이 선택하는 방법이에요. 매장은 지정된 반려동물 묘지에서 가능합니다. 어떤 방법이든 소중한 기억을 남기는 방식이에요. 마음 편한 선택을 하세요.',
    options: [
      { label: '비용은 얼마나 드나요?', next: 'cost' },
      { label: '연락 시기가 궁금해요', next: 'timing' },
    ],
  },
  timing: {
    ai: '임종 후 가능한 빨리(24시간 내) 장례식장에 연락하는 것이 좋습니다. 급하지 않다면 미리 한두 곳에 연락해 일정을 잡아두면 마음의 준비도 할 수 있어요. 지금 당장 결정하지 않아도 돼요.',
    options: [
      { label: '가족에게 알리는 법이 궁금해요', next: 'family' },
      { label: '다른 질문이 있어요', next: 'start' },
    ],
  },
  family: {
    ai: '아이들에게는 "무지개다리를 건넜어"처럼 자연스러운 표현을 쓰는 게 좋아요. 함께 사진을 보거나 추모하는 시간을 갖는 것이 슬픔을 건강하게 나누는 방법이에요. 어른들끼리도 솔직하게 슬픔을 나눌 수 있도록 대화하는 시간을 만들어보세요.',
    options: [
      { label: '비용·방법이 궁금해요', next: 'cost' },
      { label: '다른 질문이 있어요', next: 'start' },
    ],
  },
};

export default function FuneralPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('search');
  const [chatHistory, setChatHistory] = useState([
    { type: 'ai', text: CONSULT_TREE.start.ai, node: 'start' },
  ]);
  const [currentNode, setCurrentNode] = useState('start');
  const chatBottomRef = useRef(null);

  const petName = localStorage.getItem('pet_name') || '소중한 친구';

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  function handleOption(option) {
    const next = CONSULT_TREE[option.next];
    setChatHistory((prev) => [
      ...prev,
      { type: 'user', text: option.label },
      { type: 'ai', text: next.ai, node: option.next },
    ]);
    setCurrentNode(option.next);
  }

  function openKakaoMap(query) {
    window.open(`https://map.kakao.com/link/search/${encodeURIComponent(query)}`, '_blank');
  }

  const currentOptions = CONSULT_TREE[currentNode]?.options || [];

  return (
    <div className="min-h-screen bg-purple-50 px-4 py-10">
      <div className="w-full max-w-sm mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-1">
          이별을 함께 준비해요
        </h1>
        <p className="text-gray-500 text-center text-sm mb-6">
          {petName}와의 마지막 시간을<br />소중히 보낼 수 있게 도와드릴게요.
        </p>

        {/* 탭 */}
        <div className="flex bg-white rounded-xl p-1 mb-6 shadow-sm">
          {[
            { key: 'search', label: '🗺️ 장례식장 찾기' },
            { key: 'consult', label: '💬 절차 상담' },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all
                ${tab === t.key
                  ? 'bg-violet-500 text-white shadow'
                  : 'text-gray-500 hover:text-violet-600'}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* 장례식장 검색 탭 */}
        {tab === 'search' && (
          <>
            <p className="text-xs text-gray-400 text-center mb-3">주변 반려동물 장례식장 (예시)</p>
            <div className="flex flex-col gap-3 mb-4">
              {MOCK_FUNERAL_HOMES.map((h) => (
                <Card key={h.id}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-800 text-sm">{h.name}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{h.location} · {h.distance} · {h.hours}</p>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {h.services.map((s) => (
                          <span key={s} className="text-xs bg-violet-50 text-violet-600 px-2 py-0.5 rounded-full">
                            {s}
                          </span>
                        ))}
                      </div>
                      <a href={`tel:${h.phone}`} className="text-xs text-violet-600 mt-1.5 block">{h.phone}</a>
                    </div>
                    <button
                      onClick={() => openKakaoMap(h.name)}
                      className="shrink-0 text-xs bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold px-2.5 py-1.5 rounded-lg"
                    >
                      지도
                    </button>
                  </div>
                </Card>
              ))}
            </div>
            <Button
              variant="ghost"
              className="w-full"
              onClick={() => openKakaoMap('반려동물 장례식장')}
            >
              📍 더 많은 장례식장 찾기
            </Button>
          </>
        )}

        {/* 절차 상담 탭 */}
        {tab === 'consult' && (
          <div className="flex flex-col gap-3 mb-4">
            {chatHistory.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.type === 'ai' && (
                  <div className="w-7 h-7 rounded-full bg-violet-100 flex items-center justify-center text-sm shrink-0 mr-2 mt-0.5">
                    🌈
                  </div>
                )}
                <div
                  className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed
                    ${msg.type === 'user'
                      ? 'bg-violet-500 text-white rounded-br-sm'
                      : 'bg-white text-gray-700 shadow-sm rounded-bl-sm'}`}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {/* 현재 선택지 */}
            {currentOptions.length > 0 && (
              <div className="flex flex-col gap-2 mt-1">
                {currentOptions.map((opt, i) => (
                  <button
                    key={i}
                    onClick={() => handleOption(opt)}
                    className="text-left text-sm border border-violet-200 bg-white rounded-xl px-4 py-2.5 hover:border-violet-500 hover:bg-violet-50 text-gray-700 transition-all"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
            <div ref={chatBottomRef} />
          </div>
        )}

        {/* 추모하기 버튼 */}
        <div className="mt-6 border-t border-purple-100 pt-6">
          <p className="text-sm text-gray-500 text-center mb-3">
            마음의 준비가 되셨나요?<br />
            {petName}와의 소중한 기억을 추모해요.
          </p>
          <Button
            variant="primary"
            className="w-full py-3 text-base"
            onClick={() => navigate('/message')}
          >
            추모하기
          </Button>
        </div>
      </div>
    </div>
  );
}
