import { Stack } from 'expo-router';
import { COLORS } from '../../constants/colors';

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
      }}
    />
  );
}
