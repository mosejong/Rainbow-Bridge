import { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS } from '../../constants/colors';

const STORAGE_KEY = 'diary_entries';

function todayLabel() {
  return new Date().toLocaleDateString('ko-KR', {
    year: 'numeric', month: 'long', day: 'numeric', weekday: 'short',
  });
}

export default function DiaryScreen() {
  const router = useRouter();
  const [entries, setEntries] = useState([]);
  const [writing, setWriting] = useState(false);
  const [content, setContent] = useState('');
  const [petName, setPetName] = useState('소중한 친구');

  useEffect(() => {
    AsyncStorage.getItem('pet_name').then(v => v && setPetName(v));
    AsyncStorage.getItem(STORAGE_KEY).then(stored => {
      if (stored) setEntries(JSON.parse(stored));
    });
  }, []);

  async function saveEntry() {
    if (!content.trim()) return;
    const entry = {
      id: Date.now().toString(),
      dateLabel: todayLabel(),
      dateRaw: new Date().toISOString(),
      content: content.trim(),
    };
    const updated = [entry, ...entries];
    setEntries(updated);
    setContent('');
    setWriting(false);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  }

  return (
    <LinearGradient
      colors={['#F9DFE6', '#EBDDF5', '#F0F4F8', '#E4DAF5']}
      locations={[0, 0.35, 0.6, 1]}
      style={styles.gradient}
    >
      <SafeAreaView style={styles.safe}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={{ flex: 1 }}
        >
          <ScrollView
            contentContainerStyle={styles.scroll}
            keyboardShouldPersistTaps="handled"
          >
            <Text style={styles.logo}>🌈 레인보우 브릿지</Text>
            <Text style={styles.subtitle}>소중한 가족을 기억해요</Text>

            <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
              <Text style={styles.backText}>← 이전</Text>
            </TouchableOpacity>

            <Text style={styles.title}>📔 {petName}와의 일기</Text>
            <Text style={styles.desc}>함께한 하루하루를 기록해요.</Text>

            {/* 새 글쓰기 */}
            {writing ? (
              <View style={styles.writeBox}>
                <Text style={styles.dateLabel}>{todayLabel()}</Text>
                <TextInput
                  style={styles.writeInput}
                  value={content}
                  onChangeText={setContent}
                  placeholder={`오늘 ${petName}와 있었던 일을 적어주세요.`}
                  placeholderTextColor="#A89FBC"
                  multiline
                  numberOfLines={5}
                  textAlignVertical="top"
                  autoFocus
                />
                <View style={styles.writeActions}>
                  <TouchableOpacity
                    style={styles.cancelBtn}
                    onPress={() => { setWriting(false); setContent(''); }}
                  >
                    <Text style={styles.cancelText}>취소</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={saveEntry} activeOpacity={0.8} style={styles.saveBtnWrap}>
                    <LinearGradient
                      colors={['#DDEDEA', '#DAEAF6']}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 0 }}
                      style={styles.saveBtn}
                    >
                      <Text style={styles.saveBtnText}>저장하기</Text>
                    </LinearGradient>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              <TouchableOpacity
                style={styles.newEntryBtn}
                onPress={() => setWriting(true)}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={['#DDEDEA', '#DAEAF6']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.newEntryGrad}
                >
                  <Text style={styles.newEntryText}>✏️ 오늘 일기 쓰기</Text>
                </LinearGradient>
              </TouchableOpacity>
            )}

            {/* 지난 일기 목록 */}
            {entries.length > 0 && (
              <View style={styles.entriesList}>
                {entries.map(entry => (
                  <View key={entry.id} style={styles.entryCard}>
                    <Text style={styles.entryDate}>{entry.dateLabel}</Text>
                    <Text style={styles.entryContent}>{entry.content}</Text>
                  </View>
                ))}
              </View>
            )}

            {entries.length === 0 && !writing && (
              <Text style={styles.emptyText}>아직 기록된 일기가 없어요.{'\n'}오늘의 이야기를 들려주세요. 🌸</Text>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: { flex: 1 },
  safe: { flex: 1 },
  scroll: { paddingHorizontal: 20, paddingVertical: 32 },

  logo: { fontSize: 22, fontWeight: '700', color: '#5B4E75', textAlign: 'center', marginBottom: 4 },
  subtitle: { fontSize: 13, color: '#8A7D9E', textAlign: 'center', marginBottom: 20 },

  backBtn: { marginBottom: 16 },
  backText: { fontSize: 14, color: '#8A7D9E' },

  title: { fontSize: 17, fontWeight: '800', color: '#5B4E75', marginBottom: 6 },
  desc: { fontSize: 13, color: '#8A7D9E', marginBottom: 20 },

  writeBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: '#E5DCF0',
    padding: 16,
    marginBottom: 20,
    shadowColor: '#8A7D9E',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 6,
    elevation: 1,
  },
  dateLabel: { fontSize: 12, color: '#A89FBC', marginBottom: 10, fontWeight: '600' },
  writeInput: {
    fontSize: 14,
    color: '#4A4A4A',
    lineHeight: 22,
    minHeight: 110,
    paddingTop: 0,
    textAlignVertical: 'top',
    marginBottom: 12,
  },
  writeActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 10 },
  cancelBtn: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E5DCF0',
  },
  cancelText: { fontSize: 14, color: '#8A7D9E', fontWeight: '600' },
  saveBtnWrap: {
    shadowColor: '#DAEAF6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 3,
  },
  saveBtn: {
    height: 40,
    paddingHorizontal: 20,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveBtnText: { color: '#5B4E75', fontSize: 14, fontWeight: '700' },

  newEntryBtn: {
    shadowColor: '#DAEAF6',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    elevation: 3,
    marginBottom: 24,
  },
  newEntryGrad: {
    height: 52,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  newEntryText: { color: '#5B4E75', fontSize: 15, fontWeight: '700' },

  entriesList: { gap: 12 },
  entryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: '#E5DCF0',
    paddingHorizontal: 16,
    paddingVertical: 14,
    shadowColor: '#8A7D9E',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 5,
    elevation: 1,
  },
  entryDate: { fontSize: 12, color: '#A89FBC', fontWeight: '600', marginBottom: 6 },
  entryContent: { fontSize: 14, color: '#4A4A4A', lineHeight: 21 },

  emptyText: {
    textAlign: 'center',
    color: '#A89FBC',
    fontSize: 14,
    lineHeight: 22,
    marginTop: 32,
  },
});
