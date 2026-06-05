import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Button from '../components/Button';
import { login } from '../api/auth';

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { access_token } = await login(form);
      localStorage.setItem('access_token', access_token);
      navigate('/profile');
    } catch {
      setError('이메일 또는 비밀번호를 확인해주세요.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-purple-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <p className="text-4xl mb-3">🌈</p>
          <h1 className="text-2xl font-bold text-gray-800">레인보우 브릿지</h1>
          <p className="text-gray-500 text-sm mt-1">소중한 기억을 간직해요</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
            placeholder="비밀번호"
            required
            className="w-full p-4 rounded-2xl border border-gray-200 bg-white text-gray-700 text-sm focus:outline-none focus:border-violet-400"
          />

          {error && <p className="text-red-500 text-sm text-center">{error}</p>}

          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? '로그인 중...' : '로그인'}
          </Button>
        </form>

        <p className="text-center text-gray-500 text-sm mt-6">
          아직 계정이 없으신가요?{' '}
          <Link to="/register" className="text-violet-600 font-medium hover:underline">
            회원가입
          </Link>
        </p>
      </div>
    </div>
  );
}
