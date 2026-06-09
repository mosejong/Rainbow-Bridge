import { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
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

  return (
    <SafeAreaView style={styles.safe}>
      <SafetyModal isOpen={safetyOpen} onClose={() => setSafetyOpen(false)} />

      {loading && (
        <View style={styles.center}>
          <LoadingSpinner message={`${petName}의 추억을 떠올리고 있어요...`} />
        </View>
      )}

      {!loading && error && (
        <View style={styles.center}>
          <Text style={styles.error}>{error}</Text>
          <Button variant="primary" onPress={regenerate}>다시 시도</Button>
        </View>
      )}

      {/* unavailable — 연출 없이 안내 */}
      {!loading && message?.source === 'unavailable' && (
        <View style={styles.center}>
          <Text style={styles.unavailable}>{message.content}</Text>
          <Button variant="ghost" onPress={regenerate} style={styles.retryBtn}>
            다시 시도
          </Button>
        </View>
      )}

      {/* 편지 연출 */}
      {!loading && message && message.source !== 'unavailable' && (
        <View style={styles.letterWrap}>
          {lines.map((line, i) =>
            i < visibleCount ? (
              <Animated.Text
                key={i}
                style={[
                  styles.line,
                  message.first_person && styles.lineFirst,
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

          {done && (
            <View style={styles.actions}>
              <Text style={styles.disclaimer}>
                {message.first_person
                  ? 'AI가 보호자가 전해준 추억을 바탕으로 재해석한 꿈 속 작별 인사입니다.'
                  : 'AI가 생성한 추모 글입니다. 반려동물이 직접 한 말이 아닙니다.'}
              </Text>
              <Button variant="ghost" onPress={regenerate}>
                🔄 다시 생성
              </Button>
            </View>
          )}
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#1A1520' }, // 어두운 배경 — 편지 감성
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  letterWrap: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 32,
    paddingVertical: 48,
    gap: 20,
  },
  line: {
    fontSize: 17,
    color: '#EDE8F5',
    lineHeight: 28,
    textAlign: 'center',
    fontWeight: '300',
  },
  lineFirst: {
    color: '#F5E6FF', // 1인칭 — 살짝 더 따뜻한 색
    fontStyle: 'italic',
  },
  disclaimer: {
    fontSize: 11,
    color: '#7A6E8A',
    textAlign: 'center',
    lineHeight: 17,
    marginBottom: 12,
  },
  error: { color: COLORS.danger, fontSize: 14, textAlign: 'center', marginBottom: 16 },
  unavailable: {
    fontSize: 15,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 24,
  },
  retryBtn: { marginTop: 8 },
  actions: { marginTop: 32, gap: 8 },
});
