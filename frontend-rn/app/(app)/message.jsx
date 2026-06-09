import { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, ScrollView, TouchableOpacity } from 'react-native';
import { Video, ResizeMode } from 'expo-av';
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

const BGM_3RD = null;
const BGM_1ST = null;

const FLAP_H = 110;       // 봉투 flap 높이
const LINE_DELAY = 1500;
const LINE_DURATION = 900;
const BGM_FADE = 500;
const TTS_OFFSET = LINE_DURATION / 2;

function speciesIcon(s) {
  if (s === '강아지') return '🐾';
  if (s === '고양이') return '🐱';
  return '🌸';
}

function splitLines(content) {
  if (!content) return [];
  return content.split(/(?<=[.!?])\s+|\n/).map(s => s.trim()).filter(Boolean);
}

function ResourceCard({ resource }) {
  return (
    <View style={styles.resourceCard}>
      <View style={styles.rcHeader}>
        <Text style={styles.rcName}>{resource.name}</Text>
        {resource.category && <Text style={styles.rcCat}>{resource.category}</Text>}
      </View>
      {resource.contact && <Text style={styles.rcContact}>{resource.contact}</Text>}
      {resource.description && <Text style={styles.rcDesc}>{resource.description}</Text>}
    </View>
  );
}

export default function MessageScreen() {
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [petName, setPetName] = useState('소중한 친구');
  const [petSpecies, setPetSpecies] = useState('');
  const [petVideoUrl, setPetVideoUrl] = useState(null);
  const [safetyOpen, setSafetyOpen] = useState(false);
  const [lines, setLines] = useState([]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [done, setDone] = useState(false);
  const [welfareExpanded, setWelfareExpanded] = useState(false);
  // 3단계: 'loading' → 'envelope' → 'letter'
  const [phase, setPhase] = useState('loading');

  const anims = useRef([]);
  const paperAnim = useRef(new Animated.Value(0)).current;
  const envelopeOpacity = useRef(new Animated.Value(0)).current;
  const envelopeScale = useRef(new Animated.Value(0.88)).current;
  const flapTranslate = useRef(new Animated.Value(0)).current;
  const flapOpacity = useRef(new Animated.Value(1)).current;
  const bgmRef = useRef(null);
  const ttsRef = useRef(null);
  const timersRef = useRef([]);

  useEffect(() => {
    AsyncStorage.getItem('pet_name').then(v => v && setPetName(v));
    AsyncStorage.getItem('pet_species').then(v => v && setPetSpecies(v));
    AsyncStorage.getItem('pet_video_url').then(v => v && setPetVideoUrl(v));
    loadMessage();
    return () => cleanup();
  }, []);

  function cleanup() {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
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
    setWelfareExpanded(false);
    setPhase('loading');
    paperAnim.setValue(0);
    envelopeOpacity.setValue(0);
    envelopeScale.setValue(0.88);
    flapTranslate.setValue(0);
    flapOpacity.setValue(1);
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

  // 메시지 로드 완료 → envelope 단계 시작
  useEffect(() => {
    if (!message || loading) return;
    if (message.source === 'unavailable') return;

    const parsed = splitLines(message.content);
    anims.current = parsed.map(() => ({
      opacity: new Animated.Value(0),
      translateY: new Animated.Value(20),
    }));
    setLines(parsed);

    // 애니메이션 초기화
    paperAnim.setValue(0);
    envelopeOpacity.setValue(0);
    envelopeScale.setValue(0.88);
    flapTranslate.setValue(0);
    flapOpacity.setValue(1);

    setPhase('envelope');
    runEnvelopeSequence(parsed, message.first_person, message);
  }, [message, loading]);

  function runEnvelopeSequence(parsed, isFirstPerson, msgData) {
    const t = timersRef.current;

    // 1단계: 봉투 등장 (scale + fade in)
    Animated.parallel([
      Animated.timing(envelopeOpacity, { toValue: 1, duration: 500, useNativeDriver: true }),
      Animated.spring(envelopeScale, { toValue: 1, tension: 80, friction: 7, useNativeDriver: true }),
    ]).start();

    // 2단계: 1000ms 후 flap 위로 열림
    t.push(setTimeout(() => {
      Animated.parallel([
        Animated.timing(flapTranslate, { toValue: -(FLAP_H + 30), duration: 700, useNativeDriver: true }),
        Animated.timing(flapOpacity, { toValue: 0, duration: 600, useNativeDriver: true }),
      ]).start();
    }, 1000));

    // 3단계: 2000ms 후 봉투 페이드아웃 + 편지지 슬라이드업 동시 실행
    t.push(setTimeout(() => {
      Animated.parallel([
        Animated.timing(envelopeOpacity, { toValue: 0, duration: 400, useNativeDriver: true }),
        Animated.timing(paperAnim, { toValue: 1, duration: 700, useNativeDriver: true }),
      ]).start(() => setPhase('letter'));

      // 편지지 줄별 시퀀스 시작
      startSequence(parsed, isFirstPerson, msgData);
    }, 2000));
  }

  async function startSequence(parsed, isFirstPerson, msgData) {
    await Audio.setAudioModeAsync({ playsInSilentModeIOS: true });
    // paperAnim은 runEnvelopeSequence에서 처리 — 여기서 중복 실행 안 함

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
        }, BGM_FADE / 20);
      } catch {}
    }

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

    parsed.forEach((_, i) => {
      const t = timersRef.current;
      const delay = BGM_FADE + i * LINE_DELAY;
      t.push(setTimeout(() => {
        setVisibleCount(c => c + 1);
        Animated.parallel([
          Animated.timing(anims.current[i].opacity, { toValue: 1, duration: LINE_DURATION, useNativeDriver: true }),
          Animated.timing(anims.current[i].translateY, { toValue: 0, duration: LINE_DURATION, useNativeDriver: true }),
        ]).start();
        if (i === 0) {
          t.push(setTimeout(() => {
            if (ttsSound) ttsSound.playAsync().catch(() => {});
          }, TTS_OFFSET));
        }
      }, delay));
    });

    const total = BGM_FADE + parsed.length * LINE_DELAY + LINE_DURATION;
    timersRef.current.push(setTimeout(() => setDone(true), total));
  }

  const isFirst = message?.first_person;
  const icon = speciesIcon(petSpecies);
  const featuredResources = message?.welfare_resources?.filter(r => r.featured) ?? [];
  const extraResources = message?.welfare_resources?.filter(r => !r.featured) ?? [];

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

        {/* unavailable */}
        {!loading && message?.source === 'unavailable' && (
          <View style={styles.center}>
            <Text style={styles.unavailable}>{message.content}</Text>
            <Button variant="ghost" onPress={regenerate} style={{ marginTop: 16 }}>다시 시도</Button>
          </View>
        )}

        {/* 봉투 + 편지지 스테이지 (두 레이어 동시 렌더, opacity로 전환) */}
        {!loading && message && message.source !== 'unavailable' && (
          <View style={styles.stage}>

            {/* ── 레이어1: 편지지 (아래, paperAnim으로 페이드인) ── */}
            <Animated.View style={[StyleSheet.absoluteFillObject, styles.paperLayer, { opacity: paperAnim }]}>
              <ScrollView
                style={styles.paperScrollView}
                contentContainerStyle={styles.paperScrollContent}
                showsVerticalScrollIndicator={false}
                scrollEnabled={phase === 'letter'}
              >
                {/* 편지지 카드 */}
                <View style={[styles.paper, isFirst && styles.paperFirst]}>
                  <View style={styles.paperHeader}>
                    {isFirst && <Text style={styles.speciesIcon}>{icon}</Text>}
                    <Text style={[styles.petLabel, isFirst && styles.petLabelFirst]}>· {petName} ·</Text>
                    <View style={[styles.headerLine, isFirst && styles.headerLineFirst]} />
                  </View>

                  {petVideoUrl && (
                    <View style={[styles.videoWrap, isFirst && styles.videoWrapFirst]}>
                      <Video
                        source={{ uri: petVideoUrl }}
                        style={styles.video}
                        resizeMode={ResizeMode.COVER}
                        isLooping shouldPlay isMuted
                      />
                    </View>
                  )}

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

                {/* 상담 자원 섹션 */}
                {done && (featuredResources.length > 0 || extraResources.length > 0) && (
                  <View style={styles.welfareSection}>
                    {message.support_message && (
                      <View style={styles.supportBanner}>
                        <Text style={styles.supportText}>{message.support_message}</Text>
                      </View>
                    )}
                    {message.crisis_message && (
                      <View style={styles.crisisBanner}>
                        <Text style={styles.crisisText}>{message.crisis_message}</Text>
                      </View>
                    )}
                    <Text style={styles.welfareSectionTitle}>상담 자원 안내</Text>
                    {featuredResources.map((r, i) => <ResourceCard key={`f-${i}`} resource={r} />)}
                    {extraResources.length > 0 && (
                      <>
                        <TouchableOpacity
                          style={styles.expandToggle}
                          onPress={() => setWelfareExpanded(e => !e)}
                          activeOpacity={0.7}
                        >
                          <Text style={styles.expandToggleText}>
                            {welfareExpanded ? '접기 ▲' : `더 보기 (${extraResources.length}곳) ▼`}
                          </Text>
                        </TouchableOpacity>
                        {welfareExpanded && extraResources.map((r, i) => <ResourceCard key={`nf-${i}`} resource={r} />)}
                      </>
                    )}
                  </View>
                )}
              </ScrollView>
            </Animated.View>

            {/* ── 레이어2: 봉투 (위, envelopeOpacity로 페이드인→페이드아웃) ── */}
            <Animated.View style={[StyleSheet.absoluteFillObject, styles.envelopeLayer, { opacity: envelopeOpacity }]}>
              <Animated.View style={[styles.envelopeOuter, { transform: [{ scale: envelopeScale }] }]}>

                {/* 봉투 본체 카드 */}
                <View style={[styles.envelopeBody, isFirst && styles.envelopeBodyFirst]}>
                  <View style={styles.envelopeContent}>
                    <Text style={styles.envelopeSeal}>{isFirst ? '🌟' : '💌'}</Text>
                    <Text style={[styles.envelopePetName, isFirst && styles.envelopePetNameFirst]}>
                      · {petName} ·
                    </Text>
                    <Text style={[styles.envelopeHint, isFirst && styles.envelopeHintFirst]}>
                      편지를 열어볼게요
                    </Text>
                  </View>
                </View>

                {/* 봉투 flap — 절대 위치, 위로 슬라이드업 */}
                <Animated.View style={[
                  styles.envelopeFlap,
                  isFirst && styles.envelopeFlapFirst,
                  { transform: [{ translateY: flapTranslate }], opacity: flapOpacity },
                ]}>
                  <View style={styles.flapFold} />
                </Animated.View>

              </Animated.View>
            </Animated.View>

          </View>
        )}
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  safeInner: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  stage: { flex: 1 },

  // ── 편지지 레이어 ──
  paperLayer: { paddingHorizontal: 20, paddingVertical: 32 },
  paperScrollView: { flex: 1 },
  paperScrollContent: { flexGrow: 1, justifyContent: 'center', gap: 20, paddingBottom: 24 },

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
  petLabel: { fontSize: 13, color: '#A08060', letterSpacing: 3, fontWeight: '500' },
  speciesIcon: { fontSize: 28, marginBottom: 4 },
  petLabelFirst: { color: '#9A6B20', letterSpacing: 4 },
  headerLine: { width: 48, height: 1, backgroundColor: '#D4C0A0' },
  headerLineFirst: { backgroundColor: '#C9A84C', width: 64 },

  videoWrap: {
    alignSelf: 'center', width: 120, height: 120, borderRadius: 60,
    overflow: 'hidden', marginBottom: 20,
    borderWidth: 3, borderColor: '#D4C0A0',
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2, shadowRadius: 8, elevation: 6,
  },
  videoWrapFirst: { borderColor: '#C9A84C', width: 140, height: 140, borderRadius: 70 },
  video: { width: '100%', height: '100%' },

  bodyScroll: { flexGrow: 0 },
  bodyContent: { gap: 16, paddingBottom: 4 },
  line: { fontSize: 16, color: '#3A2A1A', lineHeight: 27, textAlign: 'center', fontWeight: '400' },
  lineFirst: { color: '#4A2E0A', fontStyle: 'italic' },

  paperFooter: { marginTop: 20, alignItems: 'center', gap: 10 },
  footerLine: { width: 48, height: 1, backgroundColor: '#D4C0A0' },
  disclaimer: { fontSize: 11, color: '#A09070', textAlign: 'center', lineHeight: 17 },

  regenBtn: { alignSelf: 'center' },

  // ── 상담 자원 ──
  welfareSection: { gap: 10 },
  welfareSectionTitle: {
    fontSize: 11, fontWeight: '600', color: 'rgba(255,255,255,0.4)',
    textAlign: 'center', letterSpacing: 1.5, marginBottom: 2,
  },
  supportBanner: {
    backgroundColor: 'rgba(180,150,220,0.15)',
    borderWidth: 1, borderColor: 'rgba(196,168,216,0.35)',
    borderRadius: 12, padding: 14,
  },
  supportText: { fontSize: 13, color: '#C4A8D8', lineHeight: 20, textAlign: 'center' },
  crisisBanner: {
    backgroundColor: 'rgba(240,140,60,0.15)',
    borderWidth: 1, borderColor: 'rgba(232,140,60,0.4)',
    borderRadius: 12, padding: 14,
  },
  crisisText: { fontSize: 13, color: '#E8A060', lineHeight: 20, textAlign: 'center', fontWeight: '600' },
  resourceCard: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.10)',
    borderRadius: 12, padding: 14, gap: 5,
  },
  rcHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  rcName: { fontSize: 13, fontWeight: '700', color: 'rgba(255,255,255,0.85)', flex: 1 },
  rcCat: {
    fontSize: 11, color: 'rgba(255,255,255,0.38)',
    backgroundColor: 'rgba(255,255,255,0.07)',
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8,
  },
  rcContact: { fontSize: 14, color: '#C4A8D8', fontWeight: '600' },
  rcDesc: { fontSize: 12, color: 'rgba(255,255,255,0.45)', lineHeight: 18 },
  expandToggle: {
    alignSelf: 'center', paddingHorizontal: 18, paddingVertical: 8,
    borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.07)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.10)',
  },
  expandToggleText: { fontSize: 13, color: 'rgba(255,255,255,0.45)' },

  // ── 봉투 레이어 ──
  envelopeLayer: { justifyContent: 'center', alignItems: 'center' },
  envelopeOuter: {
    width: '82%',
    // overflow 기본값(visible) — flap이 카드 위로 올라갈 수 있도록
  },
  envelopeBody: {
    width: '100%',
    height: 260,
    backgroundColor: '#FFF8EE',
    borderRadius: 14,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.45,
    shadowRadius: 24,
    elevation: 14,
  },
  envelopeBodyFirst: { backgroundColor: '#FDF3DC' },
  envelopeContent: {
    flex: 1,
    justifyContent: 'flex-end',
    alignItems: 'center',
    paddingBottom: 44,
    gap: 10,
  },
  envelopeSeal: { fontSize: 52 },
  envelopePetName: { fontSize: 15, color: '#A08060', letterSpacing: 3, fontWeight: '600' },
  envelopePetNameFirst: { color: '#9A6B20', letterSpacing: 4 },
  envelopeHint: { fontSize: 12, color: '#B89A70' },
  envelopeHintFirst: { color: '#C49A30' },

  // flap — 봉투 본체 위에 절대 위치, 위로 슬라이드
  envelopeFlap: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: FLAP_H,
    backgroundColor: '#FFEDCC',
    borderTopLeftRadius: 14,
    borderTopRightRadius: 14,
    justifyContent: 'flex-end',
    alignItems: 'center',
    zIndex: 10,
  },
  envelopeFlapFirst: { backgroundColor: '#FFE4A0' },
  flapFold: {
    width: '88%',
    height: 1.5,
    backgroundColor: 'rgba(160,120,60,0.25)',
    marginBottom: 0,
  },

  // 에러/unavailable
  error: { color: COLORS.danger, fontSize: 14, textAlign: 'center', marginBottom: 16 },
  unavailable: { fontSize: 15, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 20, lineHeight: 24 },
});
