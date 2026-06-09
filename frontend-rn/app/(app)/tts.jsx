import { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Audio } from 'expo-av';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Card from '../../components/Card';
import Button from '../../components/Button';
import LoadingSpinner from '../../components/LoadingSpinner';
import { generateTts } from '../../api/tts';
import { COLORS } from '../../constants/colors';

const TONES = [
  { value: 'warm', label: '따뜻하게', emoji: '🌸' },
  { value: 'calm', label: '차분하게', emoji: '🌿' },
  { value: 'soft', label: '부드럽게', emoji: '☁️' },
];

const API_BASE =
  process.env.EXPO_PUBLIC_API_URL ||
  'https://preacher-posing-lair.ngrok-free.dev';

export default function TtsScreen() {
  const router = useRouter();
  const [selectedTone, setSelectedTone] = useState('warm');
  const [audioUrl, setAudioUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(null);
  const [petName, setPetName] = useState('소중한 친구');
  const [messageText, setMessageText] = useState(null);
  const soundRef = useRef(null);

  useEffect(() => {
    Audio.setAudioModeAsync({ playsInSilentModeIOS: true });
    AsyncStorage.getItem('pet_name').then((v) => v && setPetName(v));
    AsyncStorage.getItem('message_content').then((v) => v && setMessageText(v));
    AsyncStorage.getItem('pet_id').then((v) => { if (v) void v; });
    return () => {
      soundRef.current?.unloadAsync();
    };
  }, []);

  async function handleGenerate() {
    if (!messageText) return;
    await soundRef.current?.stopAsync();
    await soundRef.current?.unloadAsync();
    soundRef.current = null;
    setAudioUrl(null);
    setPlaying(false);
    setLoading(true);
    setError(null);
    try {
      const petId = await AsyncStorage.getItem('pet_id');
      const res = await generateTts({ pet_id: petId, text: messageText, tone: selectedTone });
      const url = res.audio_url?.startsWith('http')
        ? res.audio_url
        : `${API_BASE}${res.audio_url}`;
      setAudioUrl(url);
      await AsyncStorage.setItem('tts_done', '1');
    } catch {
      setError('음성 생성에 실패했어요. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  }

  async function handlePlayPause() {
    if (!audioUrl) return;
    if (soundRef.current) {
      if (playing) {
        await soundRef.current.pauseAsync();
        setPlaying(false);
      } else {
        await soundRef.current.playAsync();
        setPlaying(true);
      }
    } else {
      const { sound } = await Audio.Sound.createAsync(
        { uri: audioUrl },
        { shouldPlay: true }
      );
      soundRef.current = sound;
      setPlaying(true);
      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.didJustFinish) setPlaying(false);
      });
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>음성으로 듣기</Text>
        <Text style={styles.subtitle}>{petName}를 위한 추모 메시지를 들어보세요.</Text>

        {/* 톤 선택 */}
        <Card style={styles.toneCard}>
          <Text style={styles.sectionLabel}>음성 톤 선택</Text>
          <View style={styles.toneRow}>
            {TONES.map((t) => (
              <TouchableOpacity
                key={t.value}
                onPress={() => { setSelectedTone(t.value); setAudioUrl(null); }}
                style={[styles.toneBtn, selectedTone === t.value && styles.toneBtnSelected]}
                activeOpacity={0.8}
              >
                <Text style={styles.toneEmoji}>{t.emoji}</Text>
                <Text style={[styles.toneLabel, selectedTone === t.value && styles.toneLabelSelected]}>
                  {t.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </Card>

        {/* 오디오 플레이어 */}
        {audioUrl ? (
          <Card style={styles.playerCard}>
            <TouchableOpacity
              onPress={handlePlayPause}
              style={styles.playBtn}
              activeOpacity={0.85}
            >
              <Text style={styles.playIcon}>{playing ? '⏸' : '▶'}</Text>
            </TouchableOpacity>
            <View style={styles.playerInfo}>
              <Text style={styles.playerTitle}>추모 메시지 낭독</Text>
              <Text style={styles.playerTone}>
                {TONES.find((t) => t.value === selectedTone)?.label} 톤
              </Text>
            </View>
          </Card>
        ) : null}

        {loading ? (
          <LoadingSpinner message="음성을 생성하고 있어요..." />
        ) : (
          <Button
            onPress={handleGenerate}
            disabled={!messageText}
            variant="primary"
            style={styles.btn}
          >
            {audioUrl ? '다시 생성하기' : '낭독 시작'}
          </Button>
        )}

        {!messageText ? (
          <Text style={styles.noMessage}>먼저 추모 메시지를 생성해주세요.</Text>
        ) : null}

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Button
          variant={audioUrl ? 'primary' : 'ghost'}
          onPress={() => router.push('/(app)/mission')}
          style={styles.nextBtn}
        >
          다음 — 오늘의 미션
        </Button>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  scroll: { paddingHorizontal: 24, paddingVertical: 36 },
  title: { fontSize: 22, fontWeight: '700', color: COLORS.textPrimary, textAlign: 'center', marginBottom: 6 },
  subtitle: { fontSize: 14, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 28 },
  toneCard: { marginBottom: 16 },
  sectionLabel: { fontSize: 15, fontWeight: '600', color: COLORS.textPrimary, marginBottom: 12 },
  toneRow: { flexDirection: 'row', gap: 8 },
  toneBtn: {
    flex: 1, alignItems: 'center', paddingVertical: 12,
    borderRadius: 12, borderWidth: 1.5, borderColor: COLORS.divider,
    backgroundColor: COLORS.white, gap: 4,
  },
  toneBtnSelected: { borderColor: COLORS.selectedBorder, backgroundColor: '#FBF1F3' },
  toneEmoji: { fontSize: 20 },
  toneLabel: { fontSize: 12, color: COLORS.textSecondary, fontWeight: '500' },
  toneLabelSelected: { color: COLORS.selectedText, fontWeight: '700' },
  playerCard: { flexDirection: 'row', alignItems: 'center', gap: 14, marginBottom: 20 },
  playBtn: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: COLORS.cta, alignItems: 'center', justifyContent: 'center',
    shadowColor: COLORS.cta, shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.3, shadowRadius: 6, elevation: 4,
  },
  playIcon: { fontSize: 18, color: '#fff', fontWeight: '700' },
  playerInfo: { flex: 1 },
  playerTitle: { fontSize: 14, fontWeight: '600', color: COLORS.textPrimary },
  playerTone: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  btn: { marginBottom: 12 },
  nextBtn: { marginTop: 4 },
  noMessage: { fontSize: 13, color: COLORS.textLight, textAlign: 'center', marginBottom: 12 },
  error: { color: COLORS.danger, fontSize: 13, textAlign: 'center', marginBottom: 12 },
});
