import { Stack, router } from 'expo-router';
import { Pressable, Text } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS } from '../../constants/colors';

function HomeButton() {
  return (
    <Pressable
      onPress={() => router.navigate('/(app)/home')}
      style={({ pressed }) => ({
        paddingHorizontal: 12,
        paddingVertical: 6,
        opacity: pressed ? 0.6 : 1,
      })}
      hitSlop={12}
    >
      <Text style={{ color: COLORS.cta, fontSize: 14, fontWeight: '700' }}>홈</Text>
    </Pressable>
  );
}

function LogoutButton() {
  async function handleLogout() {
    try {
      await AsyncStorage.multiRemove([
        'access_token', 'pet_id', 'pet_name', 'pet_species',
        'bucketlist_items', 'diary_entries',
      ]);
    } catch {}
    router.replace('/');
  }
  return (
    <Pressable
      onPress={handleLogout}
      style={({ pressed }) => ({
        paddingHorizontal: 12,
        paddingVertical: 6,
        opacity: pressed ? 0.6 : 1,
      })}
      hitSlop={12}
    >
      <Text style={{ color: '#E57373', fontSize: 14, fontWeight: '700' }}>로그아웃</Text>
    </Pressable>
  );
}

export default function AppLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: COLORS.background },
        headerTintColor: COLORS.textPrimary,
        headerTitleStyle: { fontWeight: '600', fontSize: 17 },
        headerShadowVisible: false,
        headerBackTitle: '',
        contentStyle: { backgroundColor: COLORS.background },
        headerRight: () => <HomeButton />,
      }}
    >
      <Stack.Screen
        name="home"
        options={{ title: '홈', headerRight: () => <LogoutButton /> }}
      />
      <Stack.Screen name="farewell"       options={{ title: '이별 안내' }} />
      <Stack.Screen name="funeral"        options={{ title: '장례 안내' }} />
      <Stack.Screen name="mission"        options={{ title: '오늘의 미션' }} />
      <Stack.Screen name="timeline"       options={{ title: '추모 타임라인' }} />
      <Stack.Screen name="report"         options={{ title: '회복 리포트' }} />
      <Stack.Screen name="emotion"        options={{ title: '감정 체크인' }} />
      <Stack.Screen name="message"        options={{ title: '추모 메시지', headerShown: false }} />
      <Stack.Screen name="tts"            options={{ title: 'TTS 음성' }} />
      <Stack.Screen name="bucketlist"     options={{ title: '버킷리스트' }} />
      <Stack.Screen name="diary"          options={{ title: '일기 & 추억 메모' }} />
      <Stack.Screen name="profile"        options={{ title: '프로필 등록' }} />
      <Stack.Screen name="memories"       options={{ title: '추억 입력' }} />
      <Stack.Screen name="memories_diary" options={{ title: '추억 메모' }} />
      <Stack.Screen name="photos"         options={{ title: '사진 기록' }} />
    </Stack>
  );
}
