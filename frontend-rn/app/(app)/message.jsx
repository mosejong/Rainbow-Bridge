import { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Audio } from 'expo-av';
import SafetyModal from '../../components/SafetyModal';
import Button from '../../components/Button';
import LoadingSpinner from '../../components/LoadingSpinner';
import { generateMessage, getLatestMessage } from '../../api/messages';
import { generateTts } from '../../api/tts';
import { COLORS } from '../../constants/colors';

// BGM 파일 — 민수님 작업 완료 후 주석 해제
// const BGM_3RD = require('../../assets/audio/bgm_3rd.mp3');
// const BGM_1ST = require('../../assets/audio/bgm_1st.mp3');
const BGM_3RD = null;
const BGM_1ST = null;

const LINE_DELAY = 1500;       // 줄 사이 간격 (ms)
const LINE_DURATION = 900;     // 한 줄 슬라이드업 duration (ms)
const BGM_FADE_DURATION = 500; // BGM 페이드인 (ms)
const TTS_START_OFFSET = LINE_DURATION / 2; // 첫 줄 절반 올라올 때 TTS 시작

function splitLines(content) {
  if (!content) return [];
  return content
    .split(/(?<=[.!?])\s+|\n/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function MessageScreen() {
  const router = useRouter();
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [petName, setPetName] = useState('소중한 친구');
  const [safetyOpen, setSafetyOpen] = useState(false);
  const [lines, setLines] = useState([]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [done, setDone] = useState(false);

  const anims = useRef([]);
  const paperAnim = useRef(new Animated.Value(0)).current; // 편지지 페이드인
  const bgmRef = useRef(null);
  const ttsRef = useRef(null);
  const timersRef = useRef([]);

  useEffect(() => {
    AsyncStorage.getItem('pet_name').then((v) => v && setPetName(v));
    loadMessage();
    return () => cleanup();
  }, []);

  function cleanup() {
    timersRef.current.forEach(clearTimeout);
    if (bgmRef.current) bgmRef.current.unloadAsync();
    if (ttsRef.current) ttsRef.current.unloadAsync();
  }

  async function saveMessage(data) {
    setMessage(data);
    await AsyncStorage.setItem('message_id', data.id || data._id || '');
    await AsyncStorage.setItem('message_content', data.content || '');
    await AsyncStorage.setItem('message_tone', data.tone || 'warm');
    if (data.risk_level >= 2 || data.source === 'safety') {
      setSafetyOpen(true);
    }
  }

  async function loadMessage() {
    setLoading(true);
    try {
      const petId = await AsyncStorage.getItem('pet_id');
      try {
        const existing = await getLatestMessage(petId);
        await saveMessage(existing);
      } catch {
        const data = await generateMessage({ pet_id: petId });
        await saveMessage(data);
      }
    } catch {
      setError('메시지 생성에 실패했어요. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  }

  async function regenerate() {
    cleanup();
    setDone(false);
    setVisibleCount(0);
    setLines([]);
    setLoading(true);
    setError('');
    try {
      const petId = await AsyncStorage.getItem('pet_id');
      const data = await generateMessage({ pet_id: petId });
      await saveMessage(data);
    } catch {
      setError('메시지 생성에 실패했어요. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  }

  // 메시지 확정 후 연출 시작
  useEffect(() => {
    if (!message || loading) return;
    if (message.source === 'unavailable') return; // graceful — 연출 없음

    const parsed = splitLines(message.content);
    anims.current = parsed.map(() => ({
      opacity: new Animated.Value(0),
      translateY: new Animated.Value(20),
    }));
    setLines(parsed);
    startSequence(parsed, message.first_person, message);
  }, [message, loading]);

  async function startSequence(parsed, isFirstPerson, msgData) {
    await Audio.setAudioModeAsync({ playsInSilentModeIOS: true });

    // 편지지 페이드인
    Animated.timing(paperAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();

    // BGM 페이드인
    const bgmFile = isFirstPerson ? BGM_1ST : BGM_3RD;
    if (bgmFile) {
      try {
        const { sound } = await Audio.Sound.createAsync(bgmFile, {
          isLooping: true,
          volume: 0,
        });
        bgmRef.current = sound;
        await sound.playAsync();
        let vol = 0;
        const fade = setInterval(async () => {
          vol = Math.min(0.7, vol + 0.05); // BGM은 0.7로 — TTS 소리에 묻히지 않게
          await sound.setVolumeAsync(vol);
          if (vol >= 0.7) clearInterval(fade);
        }, BGM_FADE_DURATION / 20);
      } catch {}
    }

    // TTS 오디오 미리 로드 (백그라운드)
    let ttsSound = null;
    try {
      const petId = await AsyncStorage.getItem('pet_id');
      const ttsData = await generateTts({
        pet_id: petId,
        text: msgData.content,
        tone: msgData.tone || 'warm',
      });
      if (ttsData?.audio_url) {
        const { sound } = await Audio.Sound.createAsync(
          { uri: ttsData.audio_url },
          { volume: 1.0 }
        );
        ttsRef.current = sound;
        ttsSound = sound;
      }
    } catch {}

    // 줄별 슬라이드업
    parsed.forEach((_, i) => {
      const t = timersRef.current;
      const delay = BGM_FADE_DURATION + i * LINE_DELAY;

      t.push(
        setTimeout(() => {
          setVisibleCount((c) => c + 1);
          Animated.parallel([
            Animated.timing(anims.current[i].opacity, {
              toValue: 1,
              duration: LINE_DURATION,
              useNativeDriver: true,
            }),
            Animated.timing(anims.current[i].translateY, {
              toValue: 0,
              duration: LINE_DURATION,
              useNativeDriver: true,
            }),
          ]).start();

          // 첫 줄 절반 올라올 때 TTS 재생
          if (i === 0) {
            t.push(
              setTimeout(() => {
                if (ttsSound) ttsSound.playAsync().catch(() => {});
              }, TTS_START_OFFSET)
            );
          }
        }, delay)
      );
    });

    // 전체 완료 후 버튼 노출
    const total = BGM_FADE_DURATION + parsed.length * LINE_DELAY + LINE_DURATION;
    timersRef.current.push(setTimeout(() => setDone(true), total));
  }

  const isFirst = message?.first_person;

  return (
    <LinearGradient colors={['#12101A', '#1E1528', '#12101A']} style={styles.safe}>
      <SafeAreaView style={styles.safeInner}>
        <SafetyModal isOpen={safetyOpen} onClose={() => setSafetyOpen(false)} />

        {/* 로딩 */}
        {loading && (
          <View style={styles.center}>
            <LoadingSpinner message={`${petName}의 추억을 떠올리고 있어요...`} />
          </View>
        )}

        {/* 에러 */}
        {!loading && error && (
          <View style={styles.center}>
            <Text style={styles.error}>{error}</Text>
            <Button variant="primary" onPress={regenerate}>다시 시도</Button>
          </View>
        )}

        {/* unavailable — 편지지 없이 안내 */}
        {!loading && message?.source === 'unavailable' && (
          <View style={styles.center}>
            <Text style={styles.unavailable}>{message.content}</Text>
            <Button variant="ghost" onPress={regenerate} style={{ marginTop: 16 }}>
              다시 시도
            </Button>
          </View>
        )}

        {/* 편지지 연출 */}
        {!loading && message && message.source !== 'unavailable' && (
          <Animated.View style={[styles.paperWrap, { opacity: paperAnim }]}>
            {/* 편지지 카드 */}
            <View style={[styles.paper, isFirst && styles.paperFirst]}>

              {/* 편지지 상단 — 이름 + 장식선 */}
              <View style={styles.paperHeader}>
                <Text style={[styles.petLabel, isFirst && styles.petLabelFirst]}>
                  · {petName} ·
                </Text>
                <View style={[styles.headerLine, isFirst && styles.headerLineFirst]} />
              </View>

              {/* 편지 본문 */}
              <ScrollView
                style={styles.bodyScroll}
                contentContainerStyle={styles.bodyContent}
                scrollEnabled={done}
                showsVerticalScrollIndicator={false}
              >
                {lines.map((line, i) =>
                  i < visibleCount ? (
                    <Animated.Text
                      key={i}
                      style={[
                        styles.line,
                        isFirst && styles.lineFirst,
                        {
                          opacity: anims.current[i]?.opacity ?? 1,
                          transform: [{ translateY: anims.current[i]?.translateY ?? 0 }],
                        },
                      ]}
                    >
                      {line}
                    </Animated.Text>
                  ) : null
                )}
              </ScrollView>

              {/* 편지지 하단 — 구분선 + disclaimer */}
              {done && (
                <View style={styles.paperFooter}>
                  <View style={[styles.footerLine, isFirst && styles.headerLineFirst]} />
                  <Text style={styles.disclaimer}>
                    {isFirst
                      ? 'AI가 보호자가 전해준 추억을 바탕으로 재해석한 꿈 속 작별 인사입니다.'
                      : 'AI가 생성한 추모 글입니다. 반려동물이 직접 한 말이 아닙니다.'}
                  </Text>
                </View>
              )}
            </View>

            {/* 다시 생성 버튼 — 편지지 밖 */}
            {done && (
              <Button variant="ghost" onPress={regenerate} style={styles.regenBtn}>
                🔄 다시 생성
              </Button>
            )}
          </Animated.View>
        )}
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  safeInner: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },

  // 편지지 전체 래퍼 (페이드인 대상)
  paperWrap: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 32,
    gap: 20,
  },

  // 편지지 카드
  paper: {
    width: '100%',
    backgroundColor: '#FFF8EE',   // 크림/아이보리 — 3인칭 기본
    borderRadius: 16,
    paddingHorizontal: 28,
    paddingTop: 28,
    paddingBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 20,
    elevation: 12,
    maxHeight: '82%',
  },
  paperFirst: {
    backgroundColor: '#FFF4EC', // 1인칭 — 살짝 따뜻한 황금빛 크림
  },

  // 편지지 상단
  paperHeader: {
    alignItems: 'center',
    marginBottom: 20,
    gap: 10,
  },
  petLabel: {
    fontSize: 13,
    color: '#A08060',
    letterSpacing: 3,
    fontWeight: '500',
  },
  petLabelFirst: {
    color: '#B06840', // 1인칭 — 따뜻한 갈색
  },
  headerLine: {
    width: 48,
    height: 1,
    backgroundColor: '#D4C0A0',
  },
  headerLineFirst: {
    backgroundColor: '#D4A080',
  },

  // 본문 스크롤
  bodyScroll: { flexGrow: 0 },
  bodyContent: { gap: 16, paddingBottom: 4 },

  // 편지 줄
  line: {
    fontSize: 16,
    color: '#3A2A1A',
    lineHeight: 27,
    textAlign: 'center',
    fontWeight: '400',
  },
  lineFirst: {
    color: '#4A2010',
    fontStyle: 'italic',
    fontWeight: '300',
  },

  // 편지지 하단
  paperFooter: {
    marginTop: 20,
    alignItems: 'center',
    gap: 10,
  },
  footerLine: {
    width: 48,
    height: 1,
    backgroundColor: '#D4C0A0',
  },
  disclaimer: {
    fontSize: 11,
    color: '#A09070',
    textAlign: 'center',
    lineHeight: 17,
  },

  // 다시 생성 버튼
  regenBtn: { alignSelf: 'center' },

  // 에러/unavailable
  error: { color: COLORS.danger, fontSize: 14, textAlign: 'center', marginBottom: 16 },
  unavailable: {
    fontSize: 15,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 24,
  },
});
