import { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, ScrollView, TouchableOpacity } from 'react-native';
import { Video, ResizeMode } from 'expo-av';
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

const LINE_DELAY = 1500;
const LINE_DURATION = 900;
const BGM_FADE_DURATION = 500;
const TTS_START_OFFSET = LINE_DURATION / 2;

function speciesIcon(species) {
  if (species === '강아지') return '🐾';
  if (species === '고양이') return '🐱';
  return '🌸';
}

function splitLines(content) {
  if (!content) return [];
  return content
    .split(/(?<=[.!?])\s+|\n/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function MessageScreen() {
  const router = useRouter();
  const [phase, setPhase] = useState('loading'); // loading | envelope | letter
  const [message, setMessage] = useState(null);
  const [error, setError] = useState('');
  const [petName, setPetName] = useState('소중한 친구');
  const [petSpecies, setPetSpecies] = useState('');
  const [petVideoUrl, setPetVideoUrl] = useState(null);
  const [safetyOpen, setSafetyOpen] = useState(false);
  const [lines, setLines] = useState([]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [done, setDone] = useState(false);

  const anims = useRef([]);
  // 봉투 애니메이션
  const flapAnim = useRef(new Animated.Value(0)).current;        // 봉투 flap: 0=닫힘 1=열림
  const envelopeAnim = useRef(new Animated.Value(1)).current;    // 봉투 body: 1=보임 0=사라짐
  // 편지지 애니메이션
  const paperOpacity = useRef(new Animated.Value(0)).current;
  const paperTranslate = useRef(new Animated.Value(40)).current;

  const bgmRef = useRef(null);
  const ttsRef = useRef(null);
  const timersRef = useRef([]);
  const parsedRef = useRef([]);

  useEffect(() => {
    AsyncStorage.getItem('pet_name').then((v) => v && setPetName(v));
    AsyncStorage.getItem('pet_species').then((v) => v && setPetSpecies(v));
    AsyncStorage.getItem('pet_video_url').then((v) => v && setPetVideoUrl(v));
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
    if (data.risk_level >= 2 || data.source === 'safety') setSafetyOpen(true);
  }

  async function loadMessage() {
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
    }
  }

  // 메시지 도착 → 봉투 단계로
  useEffect(() => {
    if (!message) return;
    if (message.source === 'unavailable') { setPhase('letter'); return; }
    const parsed = splitLines(message.content);
    parsedRef.current = parsed;
    anims.current = parsed.map(() => ({
      opacity: new Animated.Value(0),
      translateY: new Animated.Value(20),
    }));
    setLines(parsed);
    setPhase('envelope');
  }, [message]);

  // 봉투 열기 버튼
  function openEnvelope() {
    // 1. 봉투 flap 위로 (translateY -100, opacity 0)
    // 2. 봉투 body 사라짐 + 편지지 올라옴 동시에
    Animated.sequence([
      Animated.parallel([
        Animated.timing(flapAnim, {
          toValue: 1, duration: 450, useNativeDriver: true,
        }),
      ]),
      Animated.parallel([
        Animated.timing(envelopeAnim, {
          toValue: 0, duration: 350, useNativeDriver: true,
        }),
        Animated.timing(paperOpacity, {
          toValue: 1, duration: 500, useNativeDriver: true,
        }),
        Animated.timing(paperTranslate, {
          toValue: 0, duration: 500, useNativeDriver: true,
        }),
      ]),
    ]).start(() => {
      setPhase('letter');
      startSequence(parsedRef.current, message.first_person, message);
    });
  }

  async function regenerate() {
    cleanup();
    setDone(false);
    setVisibleCount(0);
    setLines([]);
    setMessage(null);
    setError('');
    flapAnim.setValue(0);
    envelopeAnim.setValue(1);
    paperOpacity.setValue(0);
    paperTranslate.setValue(40);
    setPhase('loading');
    try {
      const petId = await AsyncStorage.getItem('pet_id');
      const data = await generateMessage({ pet_id: petId });
      await saveMessage(data);
    } catch {
      setError('메시지 생성에 실패했어요. 다시 시도해주세요.');
    }
  }

  async function startSequence(parsed, isFirstPerson, msgData) {
    await Audio.setAudioModeAsync({ playsInSilentModeIOS: true });

    // BGM 페이드인
    const bgmFile = isFirstPerson ? BGM_1ST : BGM_3RD;
    if (bgmFile) {
      try {
        const { sound } = await Audio.Sound.createAsync(bgmFile, { isLooping: true, volume: 0 });
        bgmRef.current = sound;
        await sound.playAsync();
        let vol = 0;
        const fade = setInterval(async () => {
          vol = Math.min(0.7, vol + 0.05);
          await sound.setVolumeAsync(vol);
          if (vol >= 0.7) clearInterval(fade);
        }, BGM_FADE_DURATION / 20);
      } catch {}
    }

    // TTS 미리 로드
    let ttsSound = null;
    try {
      const petId = await AsyncStorage.getItem('pet_id');
      const ttsData = await generateTts({ pet_id: petId, text: msgData.content, tone: msgData.tone || 'warm' });
      if (ttsData?.audio_url) {
        const { sound } = await Audio.Sound.createAsync({ uri: ttsData.audio_url }, { volume: 1.0 });
        ttsRef.current = sound;
        ttsSound = sound;
      }
    } catch {}

    // 줄별 슬라이드업
    parsed.forEach((_, i) => {
      const t = timersRef.current;
      const delay = BGM_FADE_DURATION + i * LINE_DELAY;
      t.push(setTimeout(() => {
        setVisibleCount((c) => c + 1);
        Animated.parallel([
          Animated.timing(anims.current[i].opacity, { toValue: 1, duration: LINE_DURATION, useNativeDriver: true }),
          Animated.timing(anims.current[i].translateY, { toValue: 0, duration: LINE_DURATION, useNativeDriver: true }),
        ]).start();
        if (i === 0) {
          t.push(setTimeout(() => {
            if (ttsSound) ttsSound.playAsync().catch(() => {});
          }, TTS_START_OFFSET));
        }
      }, delay));
    });

    const total = BGM_FADE_DURATION + parsed.length * LINE_DELAY + LINE_DURATION;
    timersRef.current.push(setTimeout(() => setDone(true), total));
  }

  const isFirst = message?.first_person;
  const icon = speciesIcon(petSpecies);

  // 봉투 flap: translateY 0→-120, opacity 1→0
  const flapTranslate = flapAnim.interpolate({ inputRange: [0, 1], outputRange: [0, -120] });
  const flapOpacity = flapAnim.interpolate({ inputRange: [0, 0.8, 1], outputRange: [1, 0.3, 0] });

  return (
    <LinearGradient colors={['#12101A', '#1E1528', '#12101A']} style={styles.safe}>
      <SafeAreaView style={styles.safeInner}>
        <SafetyModal isOpen={safetyOpen} onClose={() => setSafetyOpen(false)} />

        {/* 로딩 */}
        {phase === 'loading' && !error && (
          <View style={styles.center}>
            <LoadingSpinner message={`${petName}의 편지를 가져오고 있어요...`} />
          </View>
        )}

        {/* 에러 */}
        {error && (
          <View style={styles.center}>
            <Text style={styles.error}>{error}</Text>
            <Button variant="primary" onPress={regenerate}>다시 시도</Button>
          </View>
        )}

        {/* unavailable */}
        {phase === 'letter' && message?.source === 'unavailable' && (
          <View style={styles.center}>
            <Text style={styles.unavailable}>{message.content}</Text>
            <Button variant="ghost" onPress={regenerate} style={{ marginTop: 16 }}>다시 시도</Button>
          </View>
        )}

        {/* ── 봉투 단계 ── */}
        {(phase === 'envelope') && (
          <View style={styles.center}>
            {/* 봉투 컨테이너 */}
            <Animated.View style={[styles.envelope, isFirst && styles.envelopeFirst, { opacity: envelopeAnim, transform: [{ scaleY: envelopeAnim }] }]}>

              {/* Flap (위로 열림) */}
              <Animated.View style={[
                styles.envelopeFlap,
                isFirst && styles.envelopeFlapFirst,
                { transform: [{ translateY: flapTranslate }], opacity: flapOpacity },
              ]}>
                {/* 봉투 접힘선 — 두 대각선이 V를 이룸 */}
                <View style={[styles.foldLineLeft, isFirst && styles.foldLineFirst]} />
                <View style={[styles.foldLineRight, isFirst && styles.foldLineFirst]} />
              </Animated.View>

              {/* 봉투 바디 */}
              <View style={styles.envelopeBody}>
                <Text style={styles.envelopeSeal}>{icon}</Text>
                <Text style={[styles.envelopeName, isFirst && styles.envelopeNameFirst]}>
                  · {petName} ·
                </Text>
                <Text style={[styles.envelopeSubtitle, isFirst && styles.envelopeSubtitleFirst]}>
                  편지가 도착했어요
                </Text>
              </View>
            </Animated.View>

            {/* 듣기 버튼 — 봉투 밖 */}
            <Animated.View style={{ opacity: envelopeAnim, marginTop: 28 }}>
              <TouchableOpacity style={[styles.openBtn, isFirst && styles.openBtnFirst]} onPress={openEnvelope}>
                <Text style={styles.openBtnText}>✉️  열어볼까요?</Text>
              </TouchableOpacity>
            </Animated.View>
          </View>
        )}

        {/* ── 편지지 단계 ── */}
        {(phase === 'envelope' || phase === 'letter') && message && message.source !== 'unavailable' && (
          <Animated.View style={[
            styles.paperWrap,
            { opacity: paperOpacity, transform: [{ translateY: paperTranslate }] },
            phase === 'envelope' && styles.paperHidden,
          ]}>
            <View style={[styles.paper, isFirst && styles.paperFirst]}>

              {/* 편지지 상단 */}
              <View style={styles.paperHeader}>
                {isFirst && <Text style={styles.speciesIcon}>{icon}</Text>}
                <Text style={[styles.petLabel, isFirst && styles.petLabelFirst]}>· {petName} ·</Text>
                <View style={[styles.headerLine, isFirst && styles.headerLineFirst]} />
              </View>

              {/* LivePortrait 영상 */}
              {petVideoUrl && (
                <View style={[styles.videoWrap, isFirst && styles.videoWrapFirst]}>
                  <Video source={{ uri: petVideoUrl }} style={styles.video}
                    resizeMode={ResizeMode.COVER} isLooping shouldPlay isMuted />
                </View>
              )}

              {/* 편지 본문 */}
              <ScrollView style={styles.bodyScroll} contentContainerStyle={styles.bodyContent}
                scrollEnabled={done} showsVerticalScrollIndicator={false}>
                {lines.map((line, i) =>
                  i < visibleCount ? (
                    <Animated.Text key={i} style={[
                      styles.line,
                      isFirst && styles.lineFirst,
                      { opacity: anims.current[i]?.opacity ?? 1, transform: [{ translateY: anims.current[i]?.translateY ?? 0 }] },
                    ]}>
                      {line}
                    </Animated.Text>
                  ) : null
                )}
              </ScrollView>

              {/* 편지지 하단 */}
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

            {done && (
              <Button variant="ghost" onPress={regenerate} style={styles.regenBtn}>
                🔄 다시 재생
              </Button>
            )}
          </Animated.View>
        )}
      </SafeAreaView>
    </LinearGradient>
  );
}

const ENVELOPE_W = '88%';
const FLAP_H = 80;

const styles = StyleSheet.create({
  safe: { flex: 1 },
  safeInner: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },

  // ── 봉투 ──
  envelope: {
    width: ENVELOPE_W,
    backgroundColor: '#FFF8EE',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 14,
  },
  envelopeFirst: {
    backgroundColor: '#FDF3DC',
    borderWidth: 1,
    borderColor: '#E8C97A',
  },

  envelopeFlap: {
    height: FLAP_H,
    backgroundColor: '#F5EDDE',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  envelopeFlapFirst: { backgroundColor: '#F5E6B8' },

  // 봉투 접힘선 (대각선 V)
  foldLineLeft: {
    position: 'absolute',
    top: 0, left: 0,
    width: 120, height: 1,
    backgroundColor: '#D4C0A0',
    transform: [{ rotate: '35deg' }, { translateX: -10 }, { translateY: 28 }],
  },
  foldLineRight: {
    position: 'absolute',
    top: 0, right: 0,
    width: 120, height: 1,
    backgroundColor: '#D4C0A0',
    transform: [{ rotate: '-35deg' }, { translateX: 10 }, { translateY: 28 }],
  },
  foldLineFirst: { backgroundColor: '#C9A84C' },

  envelopeBody: {
    paddingVertical: 28,
    paddingHorizontal: 24,
    alignItems: 'center',
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: '#E8DCC8',
  },
  envelopeSeal: { fontSize: 40, marginBottom: 4 },
  envelopeName: { fontSize: 14, color: '#A08060', letterSpacing: 3, fontWeight: '500' },
  envelopeNameFirst: { color: '#9A6B20', letterSpacing: 4 },
  envelopeSubtitle: { fontSize: 13, color: '#B8A080' },
  envelopeSubtitleFirst: { color: '#C09040' },

  // 듣기 버튼
  openBtn: {
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 28,
    backgroundColor: 'rgba(255,248,238,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255,248,238,0.4)',
  },
  openBtnFirst: {
    borderColor: 'rgba(232,201,122,0.5)',
    backgroundColor: 'rgba(253,243,220,0.15)',
  },
  openBtnText: { fontSize: 16, color: '#EDE8F5', letterSpacing: 1 },

  // ── 편지지 ──
  paperHidden: { position: 'absolute', pointerEvents: 'none' },
  paperWrap: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 32,
    gap: 20,
  },
  paper: {
    width: '100%',
    backgroundColor: '#FFF8EE',
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
    backgroundColor: '#FDF3DC',
    borderWidth: 1,
    borderColor: '#E8C97A',
  },
  paperHeader: { alignItems: 'center', marginBottom: 20, gap: 10 },
  speciesIcon: { fontSize: 28, marginBottom: 4 },
  petLabel: { fontSize: 13, color: '#A08060', letterSpacing: 3, fontWeight: '500' },
  petLabelFirst: { color: '#9A6B20', letterSpacing: 4 },
  headerLine: { width: 48, height: 1, backgroundColor: '#D4C0A0' },
  headerLineFirst: { backgroundColor: '#C9A84C', width: 64 },

  videoWrap: {
    alignSelf: 'center', width: 120, height: 120, borderRadius: 60,
    overflow: 'hidden', marginBottom: 20, borderWidth: 3, borderColor: '#D4C0A0',
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2, shadowRadius: 8, elevation: 6,
  },
  videoWrapFirst: { borderColor: '#C9A84C', width: 140, height: 140, borderRadius: 70 },
  video: { width: '100%', height: '100%' },

  bodyScroll: { flexGrow: 0 },
  bodyContent: { gap: 16, paddingBottom: 4 },
  line: { fontSize: 16, color: '#3A2A1A', lineHeight: 27, textAlign: 'center', fontWeight: '400' },
  lineFirst: { color: '#4A2E0A', fontStyle: 'italic', fontWeight: '400' },

  paperFooter: { marginTop: 20, alignItems: 'center', gap: 10 },
  footerLine: { width: 48, height: 1, backgroundColor: '#D4C0A0' },
  disclaimer: { fontSize: 11, color: '#A09070', textAlign: 'center', lineHeight: 17 },
  regenBtn: { alignSelf: 'center' },

  error: { color: COLORS.danger, fontSize: 14, textAlign: 'center', marginBottom: 16 },
  unavailable: { fontSize: 15, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 20, lineHeight: 24 },
});
