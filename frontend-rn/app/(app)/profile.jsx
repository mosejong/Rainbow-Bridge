import { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { COLORS } from '../../constants/colors';

const SPECIES = ['강아지', '고양이', '기타'];

export default function ProfileScreen() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: '',
    species: '강아지',
    start_date: '',
    end_date: '',
  });
  const [error, setError] = useState('');

  function handleNext() {
    if (!form.name.trim()) {
      setError('반려동물 이름을 입력해주세요.');
      return;
    }
    if (!form.start_date || !form.end_date) {
      setError('함께한 기간을 입력해주세요. (예: 2018-01-01)');
      return;
    }
    setError('');
    router.push({ pathname: '/(app)/memories', params: { profile: JSON.stringify(form) } });
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
          <Text style={styles.cardTitle}>반려동물 프로필 입력</Text>

          {/* 이름 */}
          <View style={styles.field}>
            <Text style={styles.label}>반려동물 이름 <Text style={styles.required}>*</Text></Text>
            <TextInput
              style={styles.input}
              value={form.name}
              onChangeText={(v) => setForm((p) => ({ ...p, name: v }))}
              placeholder="예) 콩이"
              placeholderTextColor={COLORS.textLight}
            />
          </View>

          {/* 종 */}
          <View style={styles.field}>
            <Text style={styles.label}>종</Text>
            <View style={styles.radioRow}>
              {SPECIES.map((s) => (
                <TouchableOpacity
                  key={s}
                  onPress={() => setForm((p) => ({ ...p, species: s }))}
                  style={[styles.radioBtn, form.species === s && styles.radioBtnSelected]}
                >
                  <Text style={[styles.radioText, form.species === s && styles.radioTextSelected]}>
                    {s}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* 함께한 기간 */}
          <View style={styles.field}>
            <Text style={styles.label}>함께한 기간 <Text style={styles.required}>*</Text></Text>
            <Text style={styles.hint}>YYYY-MM-DD 형식으로 입력해주세요</Text>
            <View style={styles.dateRow}>
              <TextInput
                style={[styles.input, styles.dateInput]}
                value={form.start_date}
                onChangeText={(v) => setForm((p) => ({ ...p, start_date: v }))}
                placeholder="2018-01-01"
                placeholderTextColor={COLORS.textLight}
                keyboardType="numeric"
              />
              <Text style={styles.dateSep}>~</Text>
              <TextInput
                style={[styles.input, styles.dateInput]}
                value={form.end_date}
                onChangeText={(v) => setForm((p) => ({ ...p, end_date: v }))}
                placeholder="2026-01-01"
                placeholderTextColor={COLORS.textLight}
                keyboardType="numeric"
              />
            </View>
          </View>

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Button onPress={handleNext} variant="primary" style={styles.btn}>
            다음 — 추억 입력
          </Button>
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
  cardTitle: { fontSize: 17, fontWeight: '700', color: COLORS.textPrimary, marginBottom: 20 },
  field: { marginBottom: 20 },
  label: { fontSize: 14, fontWeight: '600', color: COLORS.textPrimary, marginBottom: 8 },
  required: { color: COLORS.danger },
  hint: { fontSize: 12, color: COLORS.textLight, marginBottom: 6 },
  input: {
    backgroundColor: COLORS.inputBg,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 13,
    fontSize: 15,
    color: COLORS.textPrimary,
    borderWidth: 1.5,
    borderColor: COLORS.divider,
  },
  radioRow: { flexDirection: 'row', gap: 10 },
  radioBtn: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: COLORS.divider,
    backgroundColor: COLORS.white,
  },
  radioBtnSelected: { borderColor: COLORS.primary, backgroundColor: '#FBF1F3' },
  radioText: { fontSize: 14, color: COLORS.textSecondary, fontWeight: '500' },
  radioTextSelected: { color: COLORS.selectedText, fontWeight: '700' },
  dateRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  dateInput: { flex: 1 },
  dateSep: { fontSize: 16, color: COLORS.textSecondary },
  error: { color: COLORS.danger, fontSize: 13, textAlign: 'center', marginBottom: 12 },
  btn: { marginTop: 8 },
});
