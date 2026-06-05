import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import { generateMessage, getLatestMessage } from '../api/messages';

export default function MessagePage() {
  const navigate = useNavigate();
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const petName = localStorage.getItem('pet_name') || '소중한 친구';

  function saveMessage(data) {
    setMessage(data);
    localStorage.setItem('message_id', data.id || data._id);
    localStorage.setItem('message_content', data.content);
    localStorage.setItem('message_tone', data.tone || 'warm');
  }

  useEffect(() => {
    const petId = localStorage.getItem('pet_id');
    let cancelled = false;

    async function load() {
      try {
        const existing = await getLatestMessage(petId);
        if (!cancelled) saveMessage(existing);
      } catch {
        try {
          const data = await generateMessage({ pet_id: petId });
          if (!cancelled) saveMessage(data);
        } catch {
          if (!cancelled) setError('메시지 생성에 실패했어요. 다시 시도해주세요.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  async function regenerate() {
    setLoading(true);
    setError('');
    const petId = localStorage.getItem('pet_id');
    try {
      const data = await generateMessage({ pet_id: petId });
      saveMessage(data);
    } catch {
      setError('메시지 생성에 실패했어요. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-purple-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-2">
          {petName}와(과)의 추억
        </h1>
        <p className="text-gray-500 text-center text-sm mb-8">
          소중한 기억을 담아 메시지를 만들었어요.
        </p>

        {loading && (
          <div className="text-center py-12">
            <LoadingSpinner message={`${petName}의 추억을 떠올리고 있어요...`} />
          </div>
        )}

        {!loading && error && (
          <p className="text-red-500 text-sm text-center mb-4">{error}</p>
        )}

        {!loading && message && (
          <>
            <Card className="bg-violet-50 border border-violet-100 mb-6">
              <p className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                {message.content}
              </p>
              {message.tone && (
                <p className="text-violet-400 text-xs mt-4 text-right">
                  톤: {message.tone}
                </p>
              )}
            </Card>

            <p className="text-gray-400 text-xs text-center mb-4">
              이 메시지는 AI가 생성한 추모 글입니다. 반려동물이 직접 한 말이 아닙니다.
            </p>

            <div className="flex flex-col gap-3">
              <Button variant="primary" onClick={() => navigate('/tts')}>
                🔊 음성으로 듣기
              </Button>
              <Button variant="ghost" onClick={regenerate}>
                🔄 다시 생성
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
