import { useState } from 'react';
import Card from '../components/Card';
import Button from '../components/Button';

const KEY_MED = 'health_medications';
const KEY_EXAM = 'health_exams';

function loadJSON(key) {
  try { return JSON.parse(localStorage.getItem(key) || '[]'); }
  catch { return []; }
}

export default function HealthRecordsPage() {
  const [tab, setTab] = useState('med');
  const [medications, setMedications] = useState(() => loadJSON(KEY_MED));
  const [exams, setExams] = useState(() => loadJSON(KEY_EXAM));
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({});
  const [formError, setFormError] = useState('');

  const petName = localStorage.getItem('pet_name') || '소중한 친구';

  function persist(key, data) {
    localStorage.setItem(key, JSON.stringify(data));
  }

  function field(name) {
    return {
      value: form[name] || '',
      onChange: (e) => setForm((f) => ({ ...f, [name]: e.target.value })),
    };
  }

  function resetForm() {
    setForm({});
    setFormError('');
    setShowForm(false);
  }

  function addMed() {
    if (!form.name?.trim()) { setFormError('약 이름을 입력해주세요.'); return; }
    const item = {
      id: Date.now().toString(),
      name: form.name.trim(),
      dose: form.dose || '',
      frequency: form.frequency || '',
      startDate: form.startDate || new Date().toISOString().slice(0, 10),
      note: form.note || '',
    };
    const updated = [item, ...medications];
    setMedications(updated);
    persist(KEY_MED, updated);
    resetForm();
  }

  function addExam() {
    if (!form.item?.trim()) { setFormError('검사 항목을 입력해주세요.'); return; }
    const item = {
      id: Date.now().toString(),
      date: form.date || new Date().toISOString().slice(0, 10),
      item: form.item.trim(),
      result: form.result || '',
      note: form.note || '',
    };
    const updated = [item, ...exams];
    setExams(updated);
    persist(KEY_EXAM, updated);
    resetForm();
  }

  function deleteMed(id) {
    const updated = medications.filter((r) => r.id !== id);
    setMedications(updated);
    persist(KEY_MED, updated);
  }

  function deleteExam(id) {
    const updated = exams.filter((r) => r.id !== id);
    setExams(updated);
    persist(KEY_EXAM, updated);
  }

  const inputCls = 'w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-violet-400';

  return (
    <div className="min-h-screen bg-purple-50 px-4 py-10">
      <div className="w-full max-w-sm mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-1">
          {petName}의 건강 기록
        </h1>
        <p className="text-gray-500 text-center text-sm mb-6">
          투약 일정과 검진 기록을 관리하세요.
        </p>

        {/* 탭 */}
        <div className="flex bg-white rounded-xl p-1 mb-5 shadow-sm">
          {[
            { key: 'med', label: '💊 투약 기록' },
            { key: 'exam', label: '🩺 검진 기록' },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => { setTab(t.key); resetForm(); }}
              className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all
                ${tab === t.key
                  ? 'bg-violet-500 text-white shadow'
                  : 'text-gray-500 hover:text-violet-600'}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* 추가 버튼 */}
        {!showForm && (
          <Button
            variant="primary"
            className="w-full mb-5"
            onClick={() => setShowForm(true)}
          >
            + {tab === 'med' ? '투약 기록 추가' : '검진 기록 추가'}
          </Button>
        )}

        {/* 투약 폼 */}
        {showForm && tab === 'med' && (
          <Card className="mb-5">
            <p className="text-sm font-semibold text-gray-700 mb-3">투약 기록 추가</p>
            <div className="flex flex-col gap-2">
              <input className={inputCls} placeholder="약 이름 *" {...field('name')} />
              <input className={inputCls} placeholder="복용량 (예: 1정, 5ml)" {...field('dose')} />
              <input className={inputCls} placeholder="횟수 (예: 하루 2회)" {...field('frequency')} />
              <label className="text-xs text-gray-400 -mb-1">시작일</label>
              <input type="date" className={inputCls} {...field('startDate')} />
              <input className={inputCls} placeholder="메모" {...field('note')} />
              {formError && <p className="text-red-500 text-xs">{formError}</p>}
              <div className="flex gap-2 mt-1">
                <Button variant="primary" className="flex-1" onClick={addMed}>저장</Button>
                <Button variant="ghost" className="flex-1" onClick={resetForm}>취소</Button>
              </div>
            </div>
          </Card>
        )}

        {/* 검진 폼 */}
        {showForm && tab === 'exam' && (
          <Card className="mb-5">
            <p className="text-sm font-semibold text-gray-700 mb-3">검진 기록 추가</p>
            <div className="flex flex-col gap-2">
              <label className="text-xs text-gray-400 -mb-1">검진 날짜</label>
              <input type="date" className={inputCls} {...field('date')} />
              <input className={inputCls} placeholder="검사 항목 (예: 혈액검사, X-ray) *" {...field('item')} />
              <input className={inputCls} placeholder="결과 (예: 정상, 재진 필요)" {...field('result')} />
              <input className={inputCls} placeholder="메모" {...field('note')} />
              {formError && <p className="text-red-500 text-xs">{formError}</p>}
              <div className="flex gap-2 mt-1">
                <Button variant="primary" className="flex-1" onClick={addExam}>저장</Button>
                <Button variant="ghost" className="flex-1" onClick={resetForm}>취소</Button>
              </div>
            </div>
          </Card>
        )}

        {/* 투약 기록 리스트 */}
        {tab === 'med' && (
          <div className="flex flex-col gap-3">
            {medications.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-10">
                아직 투약 기록이 없어요.<br />
                <span className="text-violet-400">위 버튼으로 추가해보세요.</span>
              </p>
            ) : (
              medications.map((r) => (
                <Card key={r.id}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-800 text-sm">💊 {r.name}</p>
                      {(r.dose || r.frequency) && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          {[r.dose, r.frequency].filter(Boolean).join(' · ')}
                        </p>
                      )}
                      <p className="text-xs text-gray-400 mt-0.5">시작일: {r.startDate}</p>
                      {r.note && <p className="text-xs text-gray-500 mt-1 italic">{r.note}</p>}
                    </div>
                    <button
                      onClick={() => deleteMed(r.id)}
                      className="text-gray-300 hover:text-red-400 text-base shrink-0"
                      aria-label="삭제"
                    >
                      ✕
                    </button>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}

        {/* 검진 기록 리스트 */}
        {tab === 'exam' && (
          <div className="flex flex-col gap-3">
            {exams.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-10">
                아직 검진 기록이 없어요.<br />
                <span className="text-violet-400">위 버튼으로 추가해보세요.</span>
              </p>
            ) : (
              exams.map((r) => (
                <Card key={r.id}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-800 text-sm">🩺 {r.item}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{r.date}</p>
                      {r.result && (
                        <p className="text-xs text-gray-600 mt-1">
                          결과: <span className="text-gray-800">{r.result}</span>
                        </p>
                      )}
                      {r.note && <p className="text-xs text-gray-500 mt-1 italic">{r.note}</p>}
                    </div>
                    <button
                      onClick={() => deleteExam(r.id)}
                      className="text-gray-300 hover:text-red-400 text-base shrink-0"
                      aria-label="삭제"
                    >
                      ✕
                    </button>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
