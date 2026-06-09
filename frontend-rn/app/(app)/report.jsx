import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Card from '../../components/Card';
import LoadingSpinner from '../../components/LoadingSpinner';
import { getReport } from '../../api/report';
import { mockReport } from '../../api/mock';
import { COLORS } from '../../constants/colors';

export default function ReportScreen() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [petName, setPetName] = useState('소중한 친구');

  useEffect(() => {
    AsyncStorage.getItem('pet_name').then((v) => v && setPetName(v));
    fetchReport();
  }, []);

  async function fetchReport() {
    try {
      const petId = await AsyncStorage.getItem('pet_id');
      const data = await getReport(petId);
      setReport(data);
    } catch {
      setReport(mockReport);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <LinearGradient colors={['#F9DFE6', '#EBDDF5', '#F0F4F8', '#E4DAF5']} locations={[0, 0.35, 0.6, 1]} style={styles.gradient}>
        <SafeAreaView style={styles.safe}>
          <LoadingSpinner message="리포트를 불러오고 있어요..." />
        </SafeAreaView>
      </LinearGradient>
    );
  }

  const trend = report?.emotion_trend ?? [];
  const maxScore = Math.max(...trend.map((t) => t.score), 10);

  return (
    <LinearGradient colors={['#F9DFE6', '#EBDDF5', '#F0F4F8', '#E4DAF5']} locations={[0, 0.35, 0.6, 1]} style={styles.gradient}>
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>회복 리포트</Text>
        <Text style={styles.subtitle}>{petName}를 기억하며 함께한 시간이에요.</Text>

        {/* 사용 현황 */}
        <Card style={styles.card}>
          <Text style={styles.sectionTitle}>📊 이용 현황</Text>
          <View style={styles.statsRow}>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{report?.usage?.emotions ?? 0}</Text>
              <Text style={styles.statLabel}>감정 기록</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{report?.usage?.messages ?? 0}</Text>
              <Text style={styles.statLabel}>추모 메시지</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{report?.usage?.missions ?? 0}</Text>
              <Text style={styles.statLabel}>미션 완료</Text>
            </View>
          </View>
        </Card>

        {/* 감정 변화 그래프 (간이 막대) */}
        {trend.length > 0 ? (
          <Card style={styles.card}>
            <Text style={styles.sectionTitle}>💭 감정 변화</Text>
            <View style={styles.chartRow}>
              {trend.map((t, i) => (
                <View key={i} style={styles.bar}>
                  <View
                    style={[
                      styles.barFill,
                      { height: Math.max(4, (t.score / maxScore) * 80) },
                    ]}
                  />
                  <Text style={styles.barLabel}>{t.created_at}</Text>
                </View>
              ))}
            </View>
          </Card>
        ) : null}

        {/* 미션 완료율 */}
        <Card style={styles.card}>
          <Text style={styles.sectionTitle}>🌱 미션 완료율</Text>
          <View style={styles.completionRow}>
            <View style={styles.completionTrack}>
              <View
                style={[
                  styles.completionFill,
                  { width: `${Math.round((report?.mission_completion_rate ?? 0) * 100)}%` },
                ]}
              />
            </View>
            <Text style={styles.completionPct}>
              {Math.round((report?.mission_completion_rate ?? 0) * 100)}%
            </Text>
          </View>
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
  title: { fontSize: 22, fontWeight: '700', color: COLORS.textPrimary, textAlign: 'center', marginBottom: 6 },
  subtitle: { fontSize: 14, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 28 },
  card: { marginBottom: 16 },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: COLORS.textPrimary, marginBottom: 16 },
  statsRow: { flexDirection: 'row', alignItems: 'center' },
  statBox: { flex: 1, alignItems: 'center' },
  statNumber: { fontSize: 26, fontWeight: '700', color: COLORS.cta },
  statLabel: { fontSize: 12, color: COLORS.textSecondary, marginTop: 4 },
  statDivider: { width: 1, height: 40, backgroundColor: COLORS.divider },
  chartRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 6, height: 100, paddingTop: 10 },
  bar: { flex: 1, alignItems: 'center', justifyContent: 'flex-end' },
  barFill: {
    width: '70%', backgroundColor: COLORS.secondary,
    borderRadius: 3, minHeight: 4,
  },
  barLabel: { fontSize: 9, color: COLORS.textLight, marginTop: 4, textAlign: 'center' },
  completionRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  completionTrack: { flex: 1, height: 10, backgroundColor: '#EDE5DF', borderRadius: 5, overflow: 'hidden' },
  completionFill: { height: '100%', backgroundColor: COLORS.primary, borderRadius: 5 },
  completionPct: { fontSize: 16, fontWeight: '700', color: COLORS.textPrimary, minWidth: 40, textAlign: 'right' },
});
