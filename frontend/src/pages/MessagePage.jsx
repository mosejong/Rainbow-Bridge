import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import { generateMessage } from '../api/messages';
import { mockMessage } from '../api/mock';

export default function MessagePage() {
  const navigate = useNavigate();
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const petName = localStorage.getItem('pet_name') || '소중한 친구';

  async function fetchMessage() {
    setLoading(true);
    setError('');
    setMessage(null);

    try {
      const petId = localStorage.getItem('pet_id');
      const data = await generateMessage({ pet_id: petId });
      setMessage(data);
      localStorage.setItem('message_id', data._id);
      localStorage.setItem('message_content', data.content);
    } catch {
      // 백엔드 연결 전 mock 처리
      setMessage(mockMessage);
      localStorage.setItem('message_id', mockMessage._id);
      localStorage.setItem('message_content', mockMessage.content);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchMessage();
  }, []);

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

            <div className="flex flex-col gap-3">
              <Button variant="primary" onClick={() => navigate('/tts')}>
                🔊 음성으로 듣기
              </Button>
              <Button variant="ghost" onClick={fetchMessage}>
                🔄 다시 생성
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
