import { useState, useEffect } from 'react';
import Card from '../components/Card';
import LoadingSpinner from '../components/LoadingSpinner';
import { getTimeline } from '../api/timeline';
import { mockTimeline } from '../api/mock';

const TYPE_META = {
  emotion: { emoji: '💭', label: '감정 기록' },
  message: { emoji: '💌', label: '추모 메시지' },
  mission: { emoji: '🌱', label: '미션 완료' },
  media:   { emoji: '🎞️', label: '추모 영상' },
};

function formatDate(str) {
  const d = new Date(str);
  return `${d.getMonth() + 1}월 ${d.getDate()}일`;
}

export default function TimelinePage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const petName = localStorage.getItem('pet_name') || '소중한 친구';

  useEffect(() => {
    async function fetchTimeline() {
      try {
        const petId = localStorage.getItem('pet_id');
        const data = await getTimeline({ pet_id: petId });
        setItems(data);
      } catch {
        setItems(mockTimeline);
      } finally {
        setLoading(false);
      }
    }
    fetchTimeline();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-purple-50 flex items-center justify-center">
        <LoadingSpinner message="추억을 불러오고 있어요..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-purple-50 px-4 py-10">
      <div className="w-full max-w-sm mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-1">
          추모 타임라인
        </h1>
        <p className="text-gray-500 text-center text-sm mb-8">
          {petName}와(과) 함께한 기억들이에요.
        </p>

        {items.length === 0 ? (
          <Card className="text-center py-8">
            <p className="text-4xl mb-3">🌱</p>
            <p className="text-gray-500 text-sm">아직 기록이 없어요.</p>
            <p className="text-gray-400 text-xs mt-1">감정을 기록하면 여기 쌓여요.</p>
          </Card>
        ) : (
          <div className="relative">
            {/* 세로선 */}
            <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-violet-100" />

            <div className="flex flex-col gap-4">
              {[...items].reverse().map((item) => {
                const meta = TYPE_META[item.type] || { emoji: '📝', label: item.type };
                return (
                  <div key={item._id} className="flex items-start gap-4 pl-2">
                    {/* 타임라인 점 */}
                    <div className="w-8 h-8 rounded-full bg-violet-100 border-2 border-violet-300 flex items-center justify-center text-sm shrink-0 z-10">
                      {meta.emoji}
                    </div>
                    <Card className="flex-1 py-3 px-4">
                      <p className="text-gray-700 font-medium text-sm">{meta.label}</p>
                      <p className="text-gray-400 text-xs mt-0.5">
                        {formatDate(item.created_at)}
                      </p>
                    </Card>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
