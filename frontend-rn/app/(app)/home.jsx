import { useEffect, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';

const LIVING_SECTION = {
  emoji: '🐾',
  title: '생전 기록',
  sub: '함께하는 소중한 시간을 남겨요',
  cards: [
    {
      id: 'bucketlist',
      emoji: '📋',
      title: '버킷리스트 & 다이어리',
      desc: '함께 하고 싶은 것들과 소중한 추억을 기록해요',
      route: '/(app)/memories_diary',
    },
  ],
};

const MEMORIAL_SECTION = {
  emoji: '🌈',
  title: '추모 공간',
  sub: '추억을 간직하고 마음을 돌봐요',
  cards: [
    {
      id: 'emotion',
      emoji: '💭',
      title: '감정 체크인',
      desc: '오늘 마음이 어떤지 솔직하게 기록해요',
      route: '/(app)/emotion',
    },
    {
      id: 'message',
      emoji: '💌',
      title: '추모 메시지',
      desc: '소중한 추억으로 만드는 AI 추모 편지',
      route: '/(app)/message',
    },
    {
      id: 'tts',
      emoji: '🔊',
      title: 'TTS 음성 듣기',
      desc: '추모 메시지를 목소리로 들어요',
      route: '/(app)/tts',
    },
    {
      id: 'timeline',
      emoji: '🌿',
      title: '추모 타임라인',
      desc: '함께한 기억들을 시간순으로 되돌아봐요',
      route: '/(app)/timeline',
    },
  ],
};

function SectionCard({ card, onPress }) {
  return (
    <TouchableOpacity
      activeOpacity={0.8}
      style={styles.card}
      onPress={onPress}
    >
      <View style={styles.cardLeft}>
        <Text style={styles.cardEmoji}>{card.emoji}</Text>
      </View>
      <View style={styles.cardBody}>
        <Text style={styles.cardTitle}>{card.title}</Text>
        <Text style={styles.cardDesc}>{card.desc}</Text>
      </View>
      <Text style={styles.cardArrow}>›</Text>
    </TouchableOpacity>
  );
}

export default function HomeScreen() {
  const router = useRouter();
  const [petName, setPetName] = useState('');
  const [petSpecies, setPetSpecies] = useState('');

  useEffect(() => {
    AsyncStorage.getItem('pet_name').then(v => v && setPetName(v));
    AsyncStorage.getItem('pet_species').then(v => v && setPetSpecies(v));
  }, []);

  const speciesEmoji =
    petSpecies === '강아지' ? '🐶' :
    petSpecies === '고양이' ? '🐱' : '🐾';

  function renderSection(section) {
    return (
      <View style={styles.section} key={section.emoji}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionEmoji}>{section.emoji}</Text>
          <View>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            <Text style={styles.sectionSub}>{section.sub}</Text>
          </View>
        </View>
        <View style={styles.cardGroup}>
          {section.cards.map(card => (
            <SectionCard
              key={card.id}
              card={card}
              onPress={() => router.push(card.route)}
            />
          ))}
        </View>
      </View>
    );
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
          showsVerticalScrollIndicator={false}
        >
          <Text style={styles.logo}>🌈 레인보우 브릿지</Text>
          <Text style={styles.logoSub}>소중한 가족을 기억해요</Text>

          {petName ? (
            <View style={styles.petCard}>
              <Text style={styles.petEmoji}>{speciesEmoji}</Text>
              <View style={styles.petInfo}>
                <Text style={styles.petName}>{petName}</Text>
                <Text style={styles.petSubText}>와(과) 함께하는 공간이에요</Text>
              </View>
            </View>
          ) : null}

          {renderSection(LIVING_SECTION)}
          {renderSection(MEMORIAL_SECTION)}
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: { flex: 1 },
  safe: { flex: 1 },
  scroll: { paddingHorizontal: 20, paddingVertical: 32, paddingBottom: 48 },

  logo: { fontSize: 22, fontWeight: '700', color: '#5B4E75', textAlign: 'center', marginBottom: 4 },
  logoSub: { fontSize: 13, color: '#8A7D9E', textAlign: 'center', marginBottom: 24 },

  petCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    paddingVertical: 16,
    paddingHorizontal: 20,
    marginBottom: 28,
    borderWidth: 1.5,
    borderColor: '#E5DCF0',
    shadowColor: '#8A7D9E',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.10,
    shadowRadius: 8,
    elevation: 2,
  },
  petEmoji: { fontSize: 36 },
  petInfo: { flex: 1 },
  petName: { fontSize: 18, fontWeight: '800', color: '#5B4E75' },
  petSubText: { fontSize: 13, color: '#8A7D9E', marginTop: 2 },

  section: { marginBottom: 24 },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 12,
    paddingLeft: 2,
  },
  sectionEmoji: { fontSize: 22 },
  sectionTitle: { fontSize: 15, fontWeight: '800', color: '#5B4E75' },
  sectionSub: { fontSize: 12, color: '#8A7D9E', marginTop: 1 },

  cardGroup: { gap: 10 },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: '#E5DCF0',
    paddingVertical: 16,
    paddingHorizontal: 16,
    shadowColor: '#8A7D9E',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 6,
    elevation: 2,
  },
  cardLeft: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#F5F0FA',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  cardEmoji: { fontSize: 22 },
  cardBody: { flex: 1 },
  cardTitle: { fontSize: 14, fontWeight: '700', color: '#5B4E75', marginBottom: 3 },
  cardDesc: { fontSize: 12, color: '#8A7D9E', lineHeight: 17 },
  cardArrow: { fontSize: 22, color: '#C4A8D8', marginLeft: 8 },
});
