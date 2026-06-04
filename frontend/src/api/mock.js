export const mockPet = {
  _id: 'pet_001',
  name: '콩이',
  species: '강아지',
  period: '2018-2026',
  memories: ['공원 산책', '간식 좋아함', '낮잠 자는 거 좋아함'],
  photo_url: null,
};

export const mockEmotion = {
  id: 'emo_001',
  pet_id: 'pet_001',
  score: 6,
  note: '오늘 콩이 생각이 많이 났어',
  risk_level: 0,
  created_at: '2026-06-04T00:00:00Z',
  crisis_message: null,
};

export const mockMessage = {
  _id: 'msg_001',
  pet_id: 'pet_001',
  content:
    '콩이는 당신과 함께한 모든 순간을 소중히 간직하고 있을 거예요. 공원 산책도, 함께한 낮잠도 모두 아름다운 기억입니다.',
  tone: '따뜻함',
};

export const mockMissions = [
  { id: 'mis_001', pet_id: 'pet_001', title: '오늘 5분 산책하기', description: '잠깐이라도 밖에 나가 바람을 맞아보세요.', completed: false, created_at: '2026-06-04T00:00:00Z', completed_at: null },
  { id: 'mis_002', pet_id: 'pet_001', title: '콩이 사진 1장 꺼내보기', description: '소중한 추억을 떠올려보세요.', completed: false, created_at: '2026-06-04T00:00:00Z', completed_at: null },
  { id: 'mis_003', pet_id: 'pet_001', title: '좋아하는 음악 듣기', description: '마음을 달래는 음악 한 곡을 골라보세요.', completed: true, created_at: '2026-06-04T00:00:00Z', completed_at: '2026-06-04T09:00:00Z' },
];

export const mockTimeline = [
  { _id: 'tl_001', type: 'emotion', ref_id: 'emo_001', created_at: '2026-06-01' },
  { _id: 'tl_002', type: 'message', ref_id: 'msg_001', created_at: '2026-06-02' },
];

export const mockReport = {
  pet_id: 'pet_001',
  period: '2026-06',
  usage: { messages: 3, emotions: 5, missions: 2 },
  emotion_trend: [
    { created_at: '06-01', score: 6 },
    { created_at: '06-02', score: 4 },
    { created_at: '06-03', score: 7 },
    { created_at: '06-04', score: 5 },
    { created_at: '06-05', score: 8 },
  ],
  mission_completion_rate: 0.6,
  revisit: 5,
};
