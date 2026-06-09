import { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { createPet } from '../../api/pets';
import { COLORS } from '../../constants/colors';

const EMPTY = { keyword: '', detail: '' };

export default function MemoriesScreen() {
  const router = useRouter();
  const { profile: profileStr } = useLocalSearchParams();
  const profile = profileStr ? JSON.parse(profileStr) : null;

  const [slots, setSlots] = useState([{ ...EMPTY }, { ...EMPTY }, { ...EMPTY }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function updateSlot(idx, field, value) {
    setSlots((prev) => prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s)));
  }

  async function handleSubmit() {
    const memories = slots
      .filter((s) => s.keyword.trim())
      .map((s) => ({ keyword: s.keyword.trim(), detail: s.detail.trim() }));

    if (memories.length === 0) {
      setError('추억 키워드를 최소 1개 입력해주세요.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const payload = {
        name: profile.name.trim(),
        species: profile.species,
        period: `${profile.start_date} ~ ${profile.end_date}`,
        memories,
      };
      const pet = await createPet(payload);
      await AsyncStorage.setItem('pet_id', pet.id || pet._id);
      await AsyncStorage.setItem('pet_name', pet.name);
      await AsyncStorage.setItem('pet_species', profile.species || '');
      router.replace('/(app)/emotion');
    } catch {
      setError('저장 중 오류가 발생했어요. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  }

  if (!profile) {
    router.replace('/(app)/profile');
    return null;
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.logo}>🌈 레인보우 브릿지</Text>
        <Text style={styles.subtitle}>소중한 가족을 기억해요</Text>

        <Card style={styles.card}>
          <TouchableOpacity
            onPress={() => router.back()}
            style={styles.backBtn}
          >
            <Text style={styles.backText}>← 이전</Text>
          </TouchableOpacity>

          <Text style={styles.cardTitle}>추억 키워드 입력</Text>
          <Text style={styles.cardDesc}>
            {profile.name}와(과) 나눈 소중한 기억을 알려주세요.{' '}
            <Text style={styles.cardDescMuted}>(최대 3개)</Text>
          </Text>

          {slots.map((slot, idx) => (
            <View key={idx} style={styles.slotGroup}>
              <TextInput
                style={styles.input}
                value={slot.keyword}
                onChangeText={(v) => updateSlot(idx, 'keyword', v)}
                placeholder={`추억 키워드 ${idx + 1} (예: 공원 산책)`}
                placeholderTextColor={COLORS.textLight}
              />
              <TextInput
                style={[styles.input, styles.detailInput, !slot.keyword.trim() && styles.inputDisabled]}
                value={slot.detail}
                onChangeText={(v) => updateSlot(idx, 'detail', v)}
                placeholder="상세 내용 (예: 저녁마다 한강공원 같이 걸었어요)"
                placeholderTextColor={COLORS.textLight}
                editable={!!slot.keyword.trim()}
              />
            </View>
          ))}

          {error ? <Text style={styles.error}>{error}</Text> : null}

          {loading ? (
            <View style={styles.loadingRow}>
              <ActivityIndicator color={COLORS.cta} />
              <Text style={styles.loadingText}>저장 중이에요...</Text>
            </View>
          ) : (
            <Button onPress={handleSubmit} variant="primary" style={styles.btn}>
              다음 — 감정 체크인
            </Button>
          )}
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  scroll: { paddingHorizontal: 20, paddingVertical: 32 },
  logo: { fontSize: 22, fontWeight: '700', color: COLORS.textPrimary, textAlign: 'center', marginBottom: 4 },
  subtitle: { fontSize: 13, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 24 },
  card: { marginTop: 4 },
  backBtn: { marginBottom: 16 },
  backText: { fontSize: 14, color: COLORS.textSecondary },
  cardTitle: { fontSize: 17, fontWeight: '700', color: COLORS.textPrimary, marginBottom: 6 },
  cardDesc: { fontSize: 13, color: COLORS.textSecondary, marginBottom: 20, lineHeight: 20 },
  cardDescMuted: { color: COLORS.textLight },
  slotGroup: { marginBottom: 16, gap: 6 },
  input: {
    backgroundColor: COLORS.inputBg,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 13,
    fontSize: 14,
    color: COLORS.textPrimary,
    borderWidth: 1.5,
    borderColor: COLORS.divider,
  },
  detailInput: { borderColor: '#F0EAE7' },
  inputDisabled: { backgroundColor: '#F5F0EC', borderColor: '#EDE8E5', opacity: 0.6 },
  error: { color: COLORS.danger, fontSize: 13, textAlign: 'center', marginBottom: 12 },
  loadingRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 10, paddingVertical: 12 },
  loadingText: { fontSize: 14, color: COLORS.textSecondary },
  btn: { marginTop: 4 },
});
