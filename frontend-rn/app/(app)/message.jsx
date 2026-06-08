import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Card from '../../components/Card';
import Button from '../../components/Button';
import LoadingSpinner from '../../components/LoadingSpinner';
import SafetyModal from '../../components/SafetyModal';
import { generateMessage, getLatestMessage } from '../../api/messages';
import { COLORS } from '../../constants/colors';

export default function MessageScreen() {
  const router = useRouter();
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [petName, setPetName] = useState('소중한 친구');
  const [safetyOpen, setSafetyOpen] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem('pet_name').then((v) => v && setPetName(v));
    loadMessage();
  }, []);

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

  return (
    <SafeAreaView style={styles.safe}>
      <SafetyModal isOpen={safetyOpen} onClose={() => setSafetyOpen(false)} />
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>{petName}와(과)의 추억</Text>
        <Text style={styles.subtitle}>소중한 기억을 담아 메시지를 만들었어요.</Text>

        {loading && (
          <LoadingSpinner message={`${petName}의 추억을 떠올리고 있어요...`} />
        )}

        {!loading && error ? (
          <Text style={styles.error}>{error}</Text>
        ) : null}

        {!loading && message ? (
          <>
            <Card style={styles.messageCard}>
              <Text style={styles.messageText}>{message.content}</Text>
              {message.tone ? (
                <Text style={styles.toneBadge}>톤: {message.tone}</Text>
              ) : null}
            </Card>

            <Text style={styles.disclaimer}>
              이 메시지는 AI가 생성한 추모 글입니다. 반려동물이 직접 한 말이 아닙니다.
            </Text>

            <View style={styles.actions}>
              <Button variant="primary" onPress={() => router.push('/(app)/tts')}>
                🔊 음성으로 듣기
              </Button>
              <Button variant="ghost" onPress={regenerate} style={styles.btnGhost}>
                🔄 다시 생성
              </Button>
            </View>
          </>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  scroll: { paddingHorizontal: 24, paddingVertical: 36 },
  title: { fontSize: 22, fontWeight: '700', color: COLORS.textPrimary, textAlign: 'center', marginBottom: 6 },
  subtitle: { fontSize: 14, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 28 },
  messageCard: { backgroundColor: '#FBF1F3', borderColor: '#F0DFE2', borderWidth: 1, marginBottom: 14 },
  messageText: { fontSize: 15, color: COLORS.textPrimary, lineHeight: 24 },
  toneBadge: { fontSize: 12, color: COLORS.primary, marginTop: 12, textAlign: 'right' },
  disclaimer: {
    fontSize: 12,
    color: COLORS.textLight,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 18,
  },
  error: { color: COLORS.danger, fontSize: 14, textAlign: 'center', marginBottom: 16 },
  actions: { gap: 12 },
  btnGhost: {},
});
