import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import { generateTts } from '../api/tts';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const TONES = [
  { value: 'warm', label: '따뜻하게', emoji: '🌸' },
  { value: 'calm', label: '차분하게', emoji: '🌿' },
  { value: 'soft', label: '부드럽게', emoji: '☁️' },
];

export default function TtsPage() {
  const navigate = useNavigate();
  const [selectedTone, setSelectedTone] = useState('warm');
  const [audioUrl, setAudioUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);

  const petId = localStorage.getItem('pet_id');
  const petName = localStorage.getItem('pet_name') || '소중한 친구';
  const messageText = localStorage.getItem('message_content'); // MessagePage에서 저장 필요

  async function handleGenerate() {
    if (!messageText) return;
    setLoading(true);
    setAudioUrl(null);
    setError(null);
    try {
      const res = await generateTts({ pet_id: petId, text: messageText, tone: selectedTone });
      const url = res.audio_url.startsWith('http')
        ? res.audio_url
        : `${API_BASE}${res.audio_url}`;
      setAudioUrl(url);
      localStorage.setItem('tts_done', '1');
    } catch {
      setError('음성 생성에 실패했어요. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  }

  function handlePlayPause() {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setPlaying(!playing);
  }

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onEnd = () => setPlaying(false);
    audio.addEventListener('ended', onEnd);
    return () => audio.removeEventListener('ended', onEnd);
  }, [audioUrl]);

  return (
    <div className="min-h-screen bg-purple-50 px-4 py-10">
      <div className="w-full max-w-sm mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-1">
          음성으로 듣기
        </h1>
        <p className="text-gray-500 text-center text-sm mb-8">
          {petName}를 위한 추모 메시지를 음성으로 들어보세요.
        </p>

        {/* 톤 선택 */}
        <Card className="mb-6">
          <p className="text-gray-700 font-semibold mb-3">음성 톤 선택</p>
          <div className="flex gap-2">
            {TONES.map((tone) => (
              <button
                key={tone.value}
                onClick={() => { setSelectedTone(tone.value); setAudioUrl(null); }}
                className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-all
                  ${selectedTone === tone.value
                    ? 'bg-violet-500 text-white border-violet-500'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-violet-300'}`}
              >
                {tone.emoji} {tone.label}
              </button>
            ))}
          </div>
        </Card>

        {/* 오디오 플레이어 */}
        {audioUrl && (
          <Card className="mb-6">
            <audio ref={audioRef} src={audioUrl} className="hidden" />
            <div className="flex items-center gap-4">
              <button
                onClick={handlePlayPause}
                className="w-12 h-12 rounded-full bg-violet-500 text-white flex items-center justify-center text-xl hover:bg-violet-600 transition-colors"
              >
                {playing ? '⏸' : '▶️'}
              </button>
              <div className="flex-1">
                <p className="text-gray-700 font-medium text-sm">추모 메시지 낭독</p>
                <p className="text-gray-400 text-xs mt-0.5">
                  {TONES.find(t => t.value === selectedTone)?.label} 톤
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* 버튼 */}
        {loading ? (
          <LoadingSpinner message="음성을 생성하고 있어요..." />
        ) : (
          <Button variant="primary" onClick={handleGenerate} disabled={!messageText} className="w-full">
            {audioUrl ? '다시 생성하기' : '낭독 시작'}
          </Button>
        )}

        {!messageText && (
          <p className="text-center text-gray-400 text-sm mt-3">
            먼저 추모 메시지를 생성해주세요.
          </p>
        )}

        {error && (
          <p className="text-center text-red-400 text-sm mt-3">{error}</p>
        )}

        <div className="mt-4">
          <Button
            variant={audioUrl ? 'primary' : 'ghost'}
            onClick={() => navigate('/media')}
            disabled={!audioUrl}
            className="w-full"
          >
            {audioUrl ? '다음 — 추모 영상 만들기' : '음성 생성 후 다음으로'}
          </Button>
        </div>
      </div>
    </div>
  );
}
