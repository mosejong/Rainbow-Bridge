import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import Card from '../components/Card';
import LoadingSpinner from '../components/LoadingSpinner';
import { getReport } from '../api/report';
import { mockReport } from '../api/mock';

export default function ReportPage() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  const petName = localStorage.getItem('pet_name') || '소중한 친구';

  useEffect(() => {
    async function fetchReport() {
      try {
        const petId = localStorage.getItem('pet_id');
        const data = await getReport({ pet_id: petId });
        setReport(data);
      } catch {
        setReport(mockReport);
      } finally {
        setLoading(false);
      }
    }
    fetchReport();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-purple-50 flex items-center justify-center">
        <LoadingSpinner message="리포트를 불러오고 있어요..." />
      </div>
    );
  }

  const completionPct = report.mission_completion_rate != null
    ? Math.round(report.mission_completion_rate * 100)
    : null;

  return (
    <div className="min-h-screen bg-purple-50 px-4 py-10">
      <div className="w-full max-w-sm mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-1">
          {petName}와(과)의 회복 기록
        </h1>
        {report.period && (
          <p className="text-gray-400 text-center text-sm mb-8">{report.period}</p>
        )}

        {/* 감정 추이 그래프 */}
        <Card className="mb-5">
          <p className="text-sm font-semibold text-gray-600 mb-4">감정 점수 추이</p>
          {report.emotion_trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={report.emotion_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ede9fe" />
                <XAxis dataKey="created_at" tick={{ fontSize: 11 }} />
                <YAxis domain={[1, 10]} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(value) => [`${value}점`, '감정']}
                  contentStyle={{ borderRadius: '12px', fontSize: '12px' }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#7c3aed"
                  strokeWidth={2}
                  dot={{ fill: '#7c3aed', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-sm text-center py-8">아직 기록이 없어요</p>
          )}
          <p className="text-xs text-gray-400 mt-2 text-right">1=매우 힘듦 · 10=괜찮음</p>
        </Card>

        {/* 미션 완료율 */}
        {completionPct != null && (
          <Card className="mb-5">
            <p className="text-sm font-semibold text-gray-600 mb-3">미션 완료율</p>
            <div className="flex items-center gap-4">
              <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-violet-500 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${completionPct}%` }}
                />
              </div>
              <span className="text-violet-700 font-bold text-lg w-12 text-right">
                {completionPct}%
              </span>
            </div>
          </Card>
        )}

        {/* 이용 요약 */}
        <Card>
          <p className="text-sm font-semibold text-gray-600 mb-3">이용 요약</p>
          <div className="grid grid-cols-3 gap-2 text-center">
            {[
              { label: '감정 기록', key: 'emotions' },
              { label: '추모 메시지', key: 'messages' },
              { label: '미션', key: 'missions' },
            ].map(({ label, key }) => (
              <div key={key} className="bg-violet-50 rounded-xl py-3">
                <p className="text-violet-700 font-bold text-xl">
                  {report.usage?.[key] ?? 0}
                </p>
                <p className="text-gray-500 text-xs mt-1">{label}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
