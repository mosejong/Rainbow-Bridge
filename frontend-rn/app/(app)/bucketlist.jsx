import { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import { getPet } from '../../api/pets';
import { COLORS } from '../../constants/colors';

const STORAGE_KEY = 'bucketlist_items';
const SAMPLES = ['함께 산책하기', '좋아하는 간식 먹기', '사진 찍기'];

export default function BucketlistScreen() {
  const router = useRouter();
  const [items, setItems] = useState([]);
  const [newText, setNewText] = useState('');
  const [petName, setPetName] = useState('소중한 친구');

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      const name = await AsyncStorage.getItem('pet_name');
      if (name) setPetName(name);

      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) { setItems(JSON.parse(stored)); return; }

      const petId = await AsyncStorage.getItem('pet_id');
      if (petId) {
        const pet = await getPet(petId);
        if (pet.bucket_list?.length > 0) {
          const initial = pet.bucket_list.map((text, i) => ({ id: String(i), text, checked: false }));
          setItems(initial);
          await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(initial));
          return;
        }
      }
    } catch { /* ignore */ }

    const initial = SAMPLES.map((text, i) => ({ id: String(i), text, checked: false }));
    setItems(initial);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(initial));
  }

  async function toggle(id) {
    const updated = items.map(it => it.id === id ? { ...it, checked: !it.checked } : it);
    setItems(updated);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  }

  async function addItem() {
    if (!newText.trim()) return;
    const item = { id: Date.now().toString(), text: newText.trim(), checked: false };
    const updated = [...items, item];
    setItems(updated);
    setNewText('');
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  }

  const doneCount = items.filter(i => i.checked).length;

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

            <View style={styles.headerRow}>
              <Text style={styles.title}>📋 {petName}와의 버킷리스트</Text>
              <View style={styles.countBadge}>
                <Text style={styles.countText}>{doneCount}/{items.length}</Text>
              </View>
            </View>

            {/* 진행 바 */}
            <View style={styles.progressTrack}>
              <View
                style={[
                  styles.progressFill,
                  { width: items.length ? `${(doneCount / items.length) * 100}%` : '0%' },
                ]}
              />
            </View>

            {/* 항목 목록 */}
            <View style={styles.listWrap}>
              {items.map(item => (
                <TouchableOpacity
                  key={item.id}
                  activeOpacity={0.75}
                  onPress={() => toggle(item.id)}
                  style={[styles.item, item.checked && styles.itemDone]}
                >
                  <View style={[styles.checkbox, item.checked && styles.checkboxChecked]}>
                    {item.checked && <Text style={styles.checkmark}>✓</Text>}
                  </View>
                  <Text style={[styles.itemText, item.checked && styles.itemTextDone]}>
                    {item.text}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* 새 항목 추가 */}
            <View style={styles.addRow}>
              <TextInput
                style={styles.addInput}
                value={newText}
                onChangeText={setNewText}
                placeholder="새 항목 추가..."
                placeholderTextColor="#A89FBC"
                onSubmitEditing={addItem}
                returnKeyType="done"
              />
              <TouchableOpacity style={styles.addBtn} onPress={addItem} activeOpacity={0.8}>
                <LinearGradient
                  colors={['#DDEDEA', '#DAEAF6']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.addBtnGrad}
                >
                  <Text style={styles.addBtnText}>추가</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>

            {doneCount === items.length && items.length > 0 && (
              <Text style={styles.allDone}>🎉 모든 항목을 완료했어요!</Text>
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

  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  title: { fontSize: 17, fontWeight: '800', color: '#5B4E75', flex: 1 },
  countBadge: {
    backgroundColor: '#F3E8FF',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: '#E5DCF0',
  },
  countText: { fontSize: 13, fontWeight: '700', color: '#5B4E75' },

  progressTrack: {
    height: 6,
    backgroundColor: '#EDE5DF',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 20,
  },
  progressFill: { height: '100%', backgroundColor: '#C4A8D8', borderRadius: 3 },

  listWrap: { gap: 10, marginBottom: 20 },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
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
  itemDone: { opacity: 0.55, backgroundColor: '#F8F5FC' },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#C4A8D8',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  checkboxChecked: { backgroundColor: '#C4A8D8', borderColor: '#C4A8D8' },
  checkmark: { color: '#FFFFFF', fontSize: 14, fontWeight: '800' },
  itemText: { flex: 1, fontSize: 14, color: '#4A4A4A', fontWeight: '500' },
  itemTextDone: { textDecorationLine: 'line-through', color: '#A89FBC' },

  addRow: { flexDirection: 'row', gap: 10, alignItems: 'center', marginBottom: 16 },
  addInput: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#E5DCF0',
    paddingHorizontal: 16,
    paddingVertical: 13,
    fontSize: 14,
    color: '#4A4A4A',
  },
  addBtn: {
    shadowColor: '#DAEAF6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 3,
  },
  addBtnGrad: {
    height: 48,
    paddingHorizontal: 18,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addBtnText: { color: '#5B4E75', fontSize: 14, fontWeight: '700' },

  allDone: {
    textAlign: 'center',
    color: '#5B4E75',
    fontWeight: '700',
    fontSize: 15,
    marginTop: 8,
  },
});
