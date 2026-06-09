import { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Card from '../../components/Card';
import { COLORS } from '../../constants/colors';

const SPECIES = ['강아지', '고양이', '기타'];
const GENDER = ['남아', '여아'];

export default function ProfileScreen() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: '',
    species: '강아지',
    gender: '남아',
    start_date: '',
    end_date: '',
    guardian_title: '',
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
    <LinearGradient
      colors={['#F9DFE6', '#EBDDF5', '#F0F4F8', '#E4DAF5']}
      locations={[0, 0.35, 0.6, 1]}
      style={styles.gradient}
    >
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
                placeholderTextColor="#A89FBC"
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

            {/* 성별 */}
            <View style={styles.field}>
              <Text style={styles.label}>성별</Text>
              <View style={styles.radioRow}>
                {GENDER.map((g) => (
                  <TouchableOpacity
                    key={g}
                    onPress={() => setForm((p) => ({ ...p, gender: g }))}
                    style={[styles.radioBtn, form.gender === g && styles.radioBtnSelected]}
                  >
                    <Text style={[styles.radioText, form.gender === g && styles.radioTextSelected]}>
                      {g}
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
                  placeholderTextColor="#A89FBC"
                  keyboardType="numeric"
                />
                <Text style={styles.dateSep}>~</Text>
                <TextInput
                  style={[styles.input, styles.dateInput]}
                  value={form.end_date}
                  onChangeText={(v) => setForm((p) => ({ ...p, end_date: v }))}
                  placeholder="2026-01-01"
                  placeholderTextColor="#A89FBC"
                  keyboardType="numeric"
                />
              </View>
            </View>

            {/* 보호자 호칭 */}
            <View style={styles.field}>
              <Text style={styles.label}>보호자 호칭</Text>
              <TextInput
                style={styles.input}
                value={form.guardian_title}
                onChangeText={(v) => setForm((p) => ({ ...p, guardian_title: v }))}
                placeholder="예) 엄마, 아빠"
                placeholderTextColor="#A89FBC"
              />
            </View>

            {error ? <Text style={styles.error}>{error}</Text> : null}

            <TouchableOpacity
              activeOpacity={0.8}
              style={styles.btnShadow}
              onPress={handleNext}
            >
              <LinearGradient
                colors={['#DDEDEA', '#DAEAF6']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.btn}
              >
                <Text style={styles.btnText}>다음 — 추억 입력</Text>
              </LinearGradient>
            </TouchableOpacity>
          </Card>
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: { flex: 1 },
  safe: { flex: 1 },
  scroll: { paddingHorizontal: 20, paddingVertical: 32 },
  logo: { fontSize: 22, fontWeight: '700', color: '#5B4E75', textAlign: 'center', marginBottom: 4 },
  subtitle: { fontSize: 13, color: '#8A7D9E', textAlign: 'center', marginBottom: 24 },
  card: { marginTop: 4 },
  cardTitle: { fontSize: 17, fontWeight: '700', color: '#5B4E75', marginBottom: 20 },
  field: { marginBottom: 20 },
  label: { fontSize: 14, fontWeight: '600', color: '#5B4E75', marginBottom: 8 },
  required: { color: COLORS.danger },
  hint: { fontSize: 12, color: '#A89FBC', marginBottom: 6 },
  input: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#E5DCF0',
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: '#4A4A4A',
    shadowColor: '#8A7D9E',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 6,
    elevation: 1,
  },
  radioRow: { flexDirection: 'row', gap: 10 },
  radioBtn: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E5DCF0',
    backgroundColor: '#FFFFFF',
  },
  radioBtnSelected: { borderColor: '#C4A8D8', backgroundColor: '#F3E8FF' },
  radioText: { fontSize: 14, color: '#8A7D9E', fontWeight: '500' },
  radioTextSelected: { color: '#5B4E75', fontWeight: '700' },
  dateRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  dateInput: { flex: 1 },
  dateSep: { fontSize: 16, color: '#8A7D9E' },
  error: { color: COLORS.danger, fontSize: 13, textAlign: 'center', marginBottom: 12 },
  btnShadow: {
    marginTop: 8,
    shadowColor: '#DAEAF6',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5,
    shadowRadius: 10,
    elevation: 4,
  },
  btn: {
    height: 54,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnText: {
    color: '#5B4E75',
    fontSize: 16,
    fontWeight: 'bold',
    letterSpacing: 0.3,
  },
});
