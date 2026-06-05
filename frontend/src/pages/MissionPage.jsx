import { useState, useEffect } from 'react';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import { getMissions, completeMission } from '../api/missions';
import { mockMissions } from '../api/mock';

export default function MissionPage() {
  const [missions, setMissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(null);

  const petName = localStorage.getItem('pet_name') || '소중한 친구';

  useEffect(() => {
    async function fetchMissions() {
      try {
        const petId = localStorage.getItem('pet_id');
        const data = await getMissions({ pet_id: petId });
        setMissions(data);
      } catch {
        setMissions(mockMissions);
      } finally {
        setLoading(false);
      }
    }
    fetchMissions();
  }, []);

  async function handleComplete(missionId) {
    setCompleting(missionId);
    try {
      const updated = await completeMission({ mission_id: missionId });
      setMissions((prev) =>
        prev.map((m) => (m.id === missionId ? updated : m))
      );
    } catch {
      // 백엔드 미연결 시 로컬 상태만 업데이트
      setMissions((prev) =>
        prev.map((m) => (m.id === missionId ? { ...m, completed: true } : m))
      );
    } finally {
      setCompleting(null);
    }
  }

  const doneCount = missions.filter((m) => m.completed).length;

  if (loading) {
    return (
      <div className="min-h-screen bg-purple-50 flex items-center justify-center">
        <LoadingSpinner message="미션을 불러오고 있어요..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-purple-50 px-4 py-10">
      <div className="w-full max-w-sm mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-1">
          오늘의 미션
        </h1>
        <p className="text-gray-500 text-center text-sm mb-2">
          {petName}와(과) 함께했던 일상으로 천천히 돌아가요.
        </p>

        {/* 완료율 바 */}
        <div className="flex items-center gap-3 mb-8">
          <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
            <div
              className="bg-violet-500 h-2 rounded-full transition-all duration-500"
              style={{ width: missions.length ? `${(doneCount / missions.length) * 100}%` : '0%' }}
            />
          </div>
          <span className="text-violet-600 text-sm font-medium whitespace-nowrap">
            {doneCount}/{missions.length} 완료
          </span>
        </div>

        {/* 미션 카드 목록 */}
        <div className="flex flex-col gap-4">
          {missions.map((mission) => (
            <Card
              key={mission.id}
              className={`transition-all ${mission.completed ? 'opacity-60' : ''}`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl mt-0.5">
                  {mission.completed ? '✅' : '🌱'}
                </span>
                <div className="flex-1">
                  <p className={`font-semibold ${mission.completed ? 'line-through text-gray-400' : 'text-gray-800'}`}>
                    {mission.title}
                  </p>
                  {mission.description && (
                    <p className="text-gray-500 text-sm mt-1">{mission.description}</p>
                  )}
                </div>
              </div>

              {!mission.completed && (
                <div className="mt-4">
                  <Button
                    variant="primary"
                    className="w-full"
                    onClick={() => handleComplete(mission.id)}
                    disabled={completing === mission.id}
                  >
                    {completing === mission.id ? '처리 중...' : '완료했어요'}
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>

        {doneCount === missions.length && missions.length > 0 && (
          <p className="text-center text-violet-600 font-semibold mt-8">
            🎉 오늘 미션을 모두 완료했어요!
          </p>
        )}
      </div>
    </div>
  );
}
