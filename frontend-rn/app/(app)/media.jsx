import { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import Card from '../../components/Card';
import Button from '../../components/Button';
import LoadingSpinner from '../../components/LoadingSpinner';
import { uploadMedia } from '../../api/media';
import { COLORS } from '../../constants/colors';

export default function MediaScreen() {
  const [imageUri, setImageUri] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function pickImage() {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      setError('갤러리 접근 권한이 필요합니다.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
      setVideoUrl(null);
    }
  }

  async function handleGenerate() {
    if (!imageUri) return;
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      const filename = imageUri.split('/').pop();
      formData.append('file', { uri: imageUri, name: filename, type: 'image/jpeg' });
      const res = await uploadMedia(formData);
      setVideoUrl(res.video_url);
    } catch {
      setError('영상 생성에 실패했어요. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>추모 영상 만들기</Text>
        <Text style={styles.subtitle}>
          사진으로 소중한 기억을 영상으로 담아드려요.
        </Text>

        <Card style={styles.uploadCard}>
          <TouchableOpacity onPress={pickImage} style={styles.uploadArea} activeOpacity={0.8}>
            {imageUri ? (
              <Text style={styles.uploadDone}>✅ 사진이 선택되었어요{'\n'}다시 선택하려면 탭하세요</Text>
            ) : (
              <>
                <Text style={styles.uploadIcon}>📷</Text>
                <Text style={styles.uploadLabel}>사진 선택</Text>
                <Text style={styles.uploadHint}>갤러리에서 반려동물 사진을 골라주세요</Text>
              </>
            )}
          </TouchableOpacity>
        </Card>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        {loading ? (
          <LoadingSpinner message="추모 영상을 만들고 있어요..." />
        ) : (
          <Button
            onPress={handleGenerate}
            disabled={!imageUri}
            variant="primary"
            style={styles.btn}
          >
            영상 생성하기
          </Button>
        )}

        {videoUrl ? (
          <Card style={styles.resultCard}>
            <Text style={styles.resultTitle}>🎞️ 추모 영상이 준비됐어요</Text>
            <Text style={styles.resultUrl} numberOfLines={2}>{videoUrl}</Text>
          </Card>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  scroll: { paddingHorizontal: 20, paddingVertical: 32 },
  title: { fontSize: 22, fontWeight: '700', color: COLORS.textPrimary, textAlign: 'center', marginBottom: 6 },
  subtitle: { fontSize: 14, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 28 },
  uploadCard: { marginBottom: 16 },
  uploadArea: {
    borderWidth: 2, borderColor: COLORS.secondary, borderStyle: 'dashed',
    borderRadius: 14, paddingVertical: 36, alignItems: 'center', gap: 8,
    backgroundColor: '#F5FBFA',
  },
  uploadIcon: { fontSize: 40 },
  uploadLabel: { fontSize: 16, fontWeight: '700', color: COLORS.textPrimary },
  uploadHint: { fontSize: 13, color: COLORS.textSecondary },
  uploadDone: { fontSize: 14, color: COLORS.textPrimary, textAlign: 'center', lineHeight: 22 },
  error: { color: COLORS.danger, fontSize: 13, textAlign: 'center', marginBottom: 12 },
  btn: { marginBottom: 16 },
  resultCard: { backgroundColor: '#F0F8F6', borderColor: COLORS.secondary, borderWidth: 1 },
  resultTitle: { fontSize: 15, fontWeight: '700', color: COLORS.textPrimary, marginBottom: 8 },
  resultUrl: { fontSize: 12, color: COLORS.textSecondary },
});
