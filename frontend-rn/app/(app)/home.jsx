import { useEffect, useState } from 'react';
import {
  View, Text, Pressable, StyleSheet, ScrollView,
  LayoutAnimation, UIManager, Platform,
} from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// ─────────────────────────────────────────────
// 데이터 정의
// ─────────────────────────────────────────────
const LIVING_CARDS = [
  { id: 'bucketlist', emoji: '📋', title: '버킷리스트',      desc: '함께 하고 싶은 것들을 체크해요',           route: '/(app)/bucketlist' },
  { id: 'diary',      emoji: '📔', title: '일기 & 추억 메모', desc: '함께한 소중한 하루하루를 기록해요',         route: '/(app)/diary' },
];

const FAREWELL_SUBS = [
  {
    id: 'farewell_info',
    emoji: '🕊️',
    label: '이별 안내',
    desc: '이별을 준비하고 잘 보내드려요',
    bg: '#EDF4FB',
    border: '#C8D8E8',
    cards: [
      { id: 'farewell', emoji: '🕊️', title: '이별 진행 안내', desc: '지금 해야 할 것들을 차분하게 안내해드려요', route: '/(app)/farewell' },
      { id: 'funeral',  emoji: '🌸', title: '장례 안내',       desc: '장례 절차와 주변 장례식장 정보를 안내해요', route: '/(app)/funeral' },
    ],
  },
  {
    id: 'memorial',
    emoji: '💌',
    label: '마음 돌봄',
    desc: '추억을 간직하고 마음을 돌봐요',
    bg: '#F3EFF9',
    border: '#D4C4E8',
    cards: [
      { id: 'emotion', emoji: '💭', title: '감정 체크인',    desc: '오늘 마음이 어떤지 솔직하게 기록해요',   route: '/(app)/emotion' },
      { id: 'message', emoji: '💌', title: '추모 메시지',    desc: '소중한 추억으로 만드는 AI 추모 편지',    route: '/(app)/message' },
      { id: 'tts',     emoji: '🔊', title: 'TTS 음성 듣기', desc: '추모 메시지를 목소리로 들어요',          route: '/(app)/tts' },
    ],
  },
  {
    id: 'recovery',
    emoji: '🌱',
    label: '일상 복귀',
    desc: '작은 발걸음으로 일상으로 돌아가요',
    bg: '#EBF5F0',
    border: '#B8D8CC',
    cards: [
      { id: 'mission',  emoji: '🌱', title: '오늘의 미션',    desc: '작은 일상 활동으로 회복의 첫 걸음을 내딛어요', route: '/(app)/mission' },
      { id: 'timeline', emoji: '🌿', title: '추모 타임라인', desc: '함께한 기억들을 시간순으로 되돌아봐요',       route: '/(app)/timeline' },
      { id: 'report',   emoji: '📊', title: '회복 리포트',   desc: '감정 변화와 회복 과정을 기록으로 확인해요',   route: '/(app)/report' },
    ],
  },
];

// ─────────────────────────────────────────────
// 하위 카드 컴포넌트
// ─────────────────────────────────────────────
function NavCard({ card }) {
  return (
    <Pressable
      style={({ pressed }) => [styles.navCard, pressed && { opacity: 0.75 }]}
      onPress={() => router.push(card.route)}
    >
      <View style={styles.navCardIcon}>
        <Text style={styles.navCardEmoji}>{card.emoji}</Text>
      </View>
      <View style={styles.navCardBody}>
        <Text style={styles.navCardTitle}>{card.title}</Text>
        <Text style={styles.navCardDesc}>{card.desc}</Text>
      </View>
      <Text style={styles.navCardArrow}>›</Text>
    </Pressable>
  );
}

// ─────────────────────────────────────────────
// 작별 기록 하위 섹션 (이별안내/마음돌봄/일상복귀)
// ─────────────────────────────────────────────
function SubSection({ sub, openSubs, toggleSub }) {
  const isOpen = !!openSubs[sub.id];
  return (
    <View style={[styles.subSection, { borderColor: sub.border }]}>
      <Pressable
        style={({ pressed }) => [
          styles.subHeader,
          { backgroundColor: pressed ? sub.border : sub.bg },
        ]}
        onPress={() => toggleSub(sub.id)}
      >
        <Text style={styles.subEmoji}>{sub.emoji}</Text>
        <View style={styles.subLabelWrap}>
          <Text style={styles.subLabel}>{sub.label}</Text>
          <Text style={styles.subDesc}>{sub.desc}</Text>
        </View>
        <Text style={[styles.chevron, isOpen && styles.chevronOpen]}>▾</Text>
      </Pressable>
      {isOpen && (
        <View style={styles.subCards}>
          {sub.cards.map(card => <NavCard key={card.id} card={card} />)}
        </View>
      )}
    </View>
  );
}

// ─────────────────────────────────────────────
// 메인 화면
// ─────────────────────────────────────────────
export default function HomeScreen() {
  const [petName, setPetName] = useState('');
  const [petSpecies, setPetSpecies] = useState('');
  const [livingOpen, setLivingOpen] = useState(true);
  const [farewellOpen, setFarewellOpen] = useState(false);
  const [openSubs, setOpenSubs] = useState({});

  useEffect(() => {
    AsyncStorage.getItem('pet_name').then(v => v && setPetName(v));
    AsyncStorage.getItem('pet_species').then(v => v && setPetSpecies(v));
  }, []);

  function animate(fn) {
    LayoutAnimation.configureNext({
      duration: 260,
      create: { type: 'easeInEaseOut', property: 'opacity' },
      update: { type: 'easeInEaseOut' },
      delete: { type: 'easeInEaseOut', property: 'opacity' },
    });
    fn();
  }

  function toggleLiving() {
    animate(() => setLivingOpen(v => !v));
  }

  function toggleFarewell() {
    animate(() => setFarewellOpen(v => !v));
  }

  function toggleSub(id) {
    animate(() => setOpenSubs(prev => ({ ...prev, [id]: !prev[id] })));
  }

  const speciesEmoji =
    petSpecies === '강아지' ? '🐶' :
    petSpecies === '고양이' ? '🐱' : '🐾';

  return (
    <LinearGradient
      colors={['#F9DFE6', '#EBDDF5', '#F0F4F8', '#E4DAF5']}
      locations={[0, 0.35, 0.6, 1]}
      style={styles.gradient}
    >
      <SafeAreaView style={styles.safe}>
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
        >
          <Text style={styles.logo}>🌈 레인보우 브릿지</Text>
          <Text style={styles.logoSub}>소중한 가족을 기억해요</Text>

          {/* 반려동물 정보 카드 */}
          {petName ? (
            <View style={styles.petCard}>
              <Text style={styles.petEmoji}>{speciesEmoji}</Text>
              <View style={styles.petInfo}>
                <Text style={styles.petName}>{petName}</Text>
                <Text style={styles.petSub}>와(과) 함께하는 공간이에요</Text>
              </View>
            </View>
          ) : null}

          {/* ── 생전 기록 그룹 ── */}
          <View style={styles.group}>
            <Pressable
              style={({ pressed }) => [
                styles.groupHeader,
                { backgroundColor: pressed ? '#F0C8D8' : '#FCEEF2' },
              ]}
              onPress={toggleLiving}
            >
              <View style={styles.groupHeaderLeft}>
                <Text style={styles.groupEmoji}>🐾</Text>
                <View>
                  <Text style={styles.groupLabel}>생전 기록</Text>
                  <Text style={styles.groupDesc}>함께하는 소중한 시간을 남겨요</Text>
                </View>
              </View>
              <Text style={[styles.chevron, livingOpen && styles.chevronOpen]}>▾</Text>
            </Pressable>

            {livingOpen && (
              <View style={styles.groupCards}>
                {LIVING_CARDS.map(card => <NavCard key={card.id} card={card} />)}
              </View>
            )}
          </View>

          {/* ── 작별 기록 그룹 ── */}
          <View style={styles.group}>
            <Pressable
              style={({ pressed }) => [
                styles.groupHeader,
                { backgroundColor: pressed ? '#D4C4E8' : '#F0EAFA' },
              ]}
              onPress={toggleFarewell}
            >
              <View style={styles.groupHeaderLeft}>
                <Text style={styles.groupEmoji}>🌸</Text>
                <View>
                  <Text style={styles.groupLabel}>작별 기록</Text>
                  <Text style={styles.groupDesc}>이별부터 회복까지 함께해요</Text>
                </View>
              </View>
              <Text style={[styles.chevron, farewellOpen && styles.chevronOpen]}>▾</Text>
            </Pressable>

            {farewellOpen && (
              <View style={styles.groupCards}>
                {FAREWELL_SUBS.map(sub => (
                  <SubSection
                    key={sub.id}
                    sub={sub}
                    openSubs={openSubs}
                    toggleSub={toggleSub}
                  />
                ))}
              </View>
            )}
          </View>
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

// ─────────────────────────────────────────────
// 스타일
// ─────────────────────────────────────────────
const styles = StyleSheet.create({
  gradient: { flex: 1 },
  safe: { flex: 1 },
  scroll: { paddingHorizontal: 18, paddingVertical: 28, paddingBottom: 52 },

  logo: {
    fontSize: 22, fontWeight: '700', color: '#5B4E75',
    textAlign: 'center', marginBottom: 4,
  },
  logoSub: {
    fontSize: 13, color: '#8A7D9E',
    textAlign: 'center', marginBottom: 22,
  },

  petCard: {
    flexDirection: 'row', alignItems: 'center', gap: 14,
    backgroundColor: '#FFFFFF',
    borderRadius: 18, paddingVertical: 16, paddingHorizontal: 20,
    marginBottom: 22,
    borderWidth: 1.5, borderColor: '#E5DCF0',
    shadowColor: '#8A7D9E',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.09, shadowRadius: 8, elevation: 2,
  },
  petEmoji: { fontSize: 36 },
  petInfo: { flex: 1 },
  petName: { fontSize: 18, fontWeight: '800', color: '#5B4E75' },
  petSub: { fontSize: 13, color: '#8A7D9E', marginTop: 2 },

  // ── 그룹 ──
  group: {
    marginBottom: 14,
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: '#E5DCF0',
    backgroundColor: '#FFFFFF',
    shadowColor: '#8A7D9E',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08, shadowRadius: 8, elevation: 2,
  },
  groupHeader: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 18, paddingHorizontal: 18,
  },
  groupHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  groupEmoji: { fontSize: 26 },
  groupLabel: { fontSize: 16, fontWeight: '800', color: '#5B4E75' },
  groupDesc: { fontSize: 12, color: '#8A7D9E', marginTop: 2 },
  groupCards: { paddingHorizontal: 14, paddingBottom: 14, paddingTop: 4, gap: 10 },

  chevron: {
    fontSize: 18, color: '#C4A8D8', fontWeight: '700',
    transform: [{ rotate: '0deg' }],
  },
  chevronOpen: {
    transform: [{ rotate: '180deg' }],
  },

  // ── 하위 섹션 ──
  subSection: {
    borderRadius: 14, overflow: 'hidden',
    borderWidth: 1.5,
    backgroundColor: '#FFFFFF',
  },
  subHeader: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingVertical: 14, paddingHorizontal: 16,
  },
  subEmoji: { fontSize: 20 },
  subLabelWrap: { flex: 1 },
  subLabel: { fontSize: 14, fontWeight: '700', color: '#5B4E75' },
  subDesc: { fontSize: 11, color: '#8A7D9E', marginTop: 1 },
  subCards: { paddingHorizontal: 12, paddingBottom: 12, paddingTop: 4, gap: 8 },

  // ── 네비게이션 카드 ──
  navCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1.5, borderColor: '#EDE6F5',
    paddingVertical: 13, paddingHorizontal: 14,
    shadowColor: '#8A7D9E',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05, shadowRadius: 4, elevation: 1,
  },
  navCardIcon: {
    width: 40, height: 40, borderRadius: 11,
    backgroundColor: '#F5F0FA',
    justifyContent: 'center', alignItems: 'center',
    marginRight: 12,
  },
  navCardEmoji: { fontSize: 20 },
  navCardBody: { flex: 1 },
  navCardTitle: { fontSize: 13, fontWeight: '700', color: '#5B4E75', marginBottom: 2 },
  navCardDesc: { fontSize: 11, color: '#8A7D9E', lineHeight: 16 },
  navCardArrow: { fontSize: 20, color: '#C4A8D8', marginLeft: 6 },
});
