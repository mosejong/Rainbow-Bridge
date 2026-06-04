import { useState, useRef } from 'react';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import { uploadMedia, getMediaStatus } from '../api/media';

const GUIDE = [
  '정면을 바라보는 사진',
  '입을 다물거나 차분한 표정',
  '얼굴이 또렷하고 밝은 사진',
];

export default function MediaPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | uploading | processing | done | error
  const [videoUrl, setVideoUrl] = useState(null);
  const fileRef = useRef(null);

  const petName = localStorage.getItem('pet_name') || '소중한 친구';

  function handleFileChange(e) {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setStatus('idle');
    setVideoUrl(null);
  }

  async function handleUpload() {
    if (!file) return;
    setStatus('uploading');
    try {
      const petId = localStorage.getItem('pet_id');
      const res = await uploadMedia({ file, pet_id: petId });
      setStatus('processing');
      // 폴링 — 영상 생성은 수십 초 걸림
      await pollStatus(res.asset_id);
    } catch {
      setStatus('error');
    }
  }

  async function pollStatus(assetId) {
    for (let i = 0; i < 30; i++) {
      await new Promise((r) => setTimeout(r, 3000));
      try {
        const res = await getMediaStatus({ asset_id: assetId });
        if (res.status === 'done') {
          setVideoUrl(res.video_url);
          setStatus('done');
          return;
        }
        if (res.status === 'error') {
          setStatus('error');
          return;
        }
      } catch {
        // 계속 폴링
      }
    }
    setStatus('error');
  }

  return (
    <div className="min-h-screen bg-purple-50 px-4 py-10">
      <div className="w-full max-w-sm mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-1">
          추모 영상 만들기
        </h1>
        <p className="text-gray-500 text-center text-sm mb-8">
          {petName}의 사진으로 잔잔한 추모 영상을 만들어요.
        </p>

        {/* 사진 업로드 */}
        <Card className="mb-4">
          <p className="text-gray-700 font-semibold mb-2">사진 선택</p>
          <p className="text-gray-400 text-xs mb-3">
            📸 좋은 영상을 위한 사진 팁:
          </p>
          <ul className="text-gray-400 text-xs mb-4 space-y-1">
            {GUIDE.map((g) => (
              <li key={g} className="flex items-start gap-1">
                <span className="text-violet-400">•</span> {g}
              </li>
            ))}
          </ul>

          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />

          {preview ? (
            <div className="relative">
              <img
                src={preview}
                alt="미리보기"
                className="w-full rounded-xl object-cover max-h-64"
              />
              <button
                onClick={() => { setFile(null); setPreview(null); setStatus('idle'); }}
                className="absolute top-2 right-2 bg-black/50 text-white rounded-full w-6 h-6 text-xs flex items-center justify-center"
              >
                ✕
              </button>
            </div>
          ) : (
            <button
              onClick={() => fileRef.current?.click()}
              className="w-full border-2 border-dashed border-violet-200 rounded-xl py-8 text-center text-gray-400 hover:border-violet-400 transition-colors"
            >
              <p className="text-3xl mb-2">📷</p>
              <p className="text-sm">사진을 선택해주세요</p>
            </button>
          )}
        </Card>

        {/* 생성 버튼 */}
        {status === 'uploading' || status === 'processing' ? (
          <LoadingSpinner
            message={status === 'uploading' ? '사진을 업로드하고 있어요...' : '영상을 생성하고 있어요... (30초~1분)'}
          />
        ) : (
          <Button
            variant="primary"
            onClick={handleUpload}
            disabled={!file || status === 'done'}
          >
            {status === 'done' ? '영상 생성 완료 ✓' : '추모 영상 생성하기'}
          </Button>
        )}

        {status === 'error' && (
          <p className="text-center text-red-400 text-sm mt-3">
            영상 생성에 실패했어요. 다시 시도해주세요.
          </p>
        )}

        {/* 결과 영상 */}
        {videoUrl && (
          <Card className="mt-6">
            <p className="text-gray-700 font-semibold mb-3">생성된 추모 영상</p>
            <video
              src={videoUrl}
              controls
              loop
              className="w-full rounded-xl"
            />
            <a
              href={videoUrl}
              download={`${petName}_추모영상.mp4`}
              className="block mt-3"
            >
              <Button variant="ghost">영상 저장하기</Button>
            </a>
          </Card>
        )}
      </div>
    </div>
  );
}
