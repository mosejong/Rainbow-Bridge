import { Stack, useRouter } from 'expo-router';
import { TouchableOpacity, Text } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS } from '../../constants/colors';

function HomeButton() {
  const router = useRouter();
  return (
    <TouchableOpacity
      onPress={() => router.replace('/(app)/home')}
      style={{ paddingRight: 8, paddingVertical: 4 }}
      hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
    >
      <Text style={{ color: COLORS.cta, fontSize: 14, fontWeight: '700' }}>홈</Text>
    </TouchableOpacity>
  );
}

function LogoutButton() {
  const router = useRouter();
  async function handleLogout() {
    await AsyncStorage.multiRemove([
      'access_token', 'pet_id', 'pet_name', 'pet_species',
      'bucketlist_items', 'diary_entries',
    ]);
    router.replace('/(auth)/login');
  }
  return (
    <TouchableOpacity
      onPress={handleLogout}
      style={{ paddingRight: 8, paddingVertical: 4 }}
      hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
    >
      <Text style={{ color: '#E57373', fontSize: 14, fontWeight: '700' }}>로그아웃</Text>
    </TouchableOpacity>
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
    </Stack>
  );
}
