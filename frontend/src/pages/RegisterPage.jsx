import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Button from '../components/Button';
import { register } from '../api/auth';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '', nickname: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (form.password.length < 6) {
      setError('비밀번호는 6자 이상이어야 해요.');
      return;
    }
    setLoading(true);
    try {
      await register(form);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || '회원가입에 실패했어요. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-purple-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <p className="text-4xl mb-3">🌈</p>
          <h1 className="text-2xl font-bold text-gray-800">회원가입</h1>
          <p className="text-gray-500 text-sm mt-1">함께 기억을 나눠요</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            name="nickname"
            value={form.nickname}
            onChange={handleChange}
            placeholder="닉네임"
            required
            className="w-full p-4 rounded-2xl border border-gray-200 bg-white text-gray-700 text-sm focus:outline-none focus:border-violet-400"
          />
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            placeholder="이메일"
            required
            className="w-full p-4 rounded-2xl border border-gray-200 bg-white text-gray-700 text-sm focus:outline-none focus:border-violet-400"
          />
          <input
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            placeholder="비밀번호 (6자 이상)"
            required
            className="w-full p-4 rounded-2xl border border-gray-200 bg-white text-gray-700 text-sm focus:outline-none focus:border-violet-400"
          />

          {error && <p className="text-red-500 text-sm text-center">{error}</p>}

          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? '가입 중...' : '가입하기'}
          </Button>
        </form>

        <p className="text-center text-gray-500 text-sm mt-6">
          이미 계정이 있으신가요?{' '}
          <Link to="/login" className="text-violet-600 font-medium hover:underline">
            로그인
          </Link>
        </p>
      </div>
    </div>
  );
}
