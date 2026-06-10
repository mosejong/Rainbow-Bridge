import { useState, useRef, useEffect } from 'react';
import { Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Video, ResizeMode } from 'expo-av';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import Card from '../../components/Card';
import Button from '../../components/Button';
import LoadingSpinner from '../../components/LoadingSpinner';
import { uploadMedia, getMediaStatus } from '../../api/media';
import { API_URL } from '../../api/axiosInstance';
import { COLORS } from '../../constants/colors';

const POLL_INTERVAL = 5000; // 5초 간격 폴링
const POLL_MAX = 60; // 최대 ~5분 대기

export default function MediaScreen() {
  const [imageUri, setImageUri] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [error, setError] = useState('');
  const pollRef = useRef(null);

  // 화면 이탈 시 폴링 정리
  useEffect(() => () => clearTimeout(pollRef.current), []);

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
      setError('');
    }
  }

  async function handleGenerate() {
    if (!imageUri) return;
    clearTimeout(pollRef.current);
    setLoading(true);
    setError('');
    setVideoUrl(null);
    setStatusMsg('사진을 올리고 있어요...');
    try {
      const petId = await AsyncStorage.getItem('pet_id');
      if (!petId) {
        setError('반려동물 정보가 없어요. 먼저 프로필을 등록해주세요.');
        setLoading(false);
        return;
      }
      const formData = new FormData();
      const filename = imageUri.split('/').pop();
      formData.append('file', { uri: imageUri, name: filename, type: 'image/jpeg' });
      formData.append('pet_id', petId);
      const { asset_id } = await uploadMedia(formData);
      // 편지(message) 화면의 '영상 보기' 버튼이 이 키로 asset_id를 읽어 recordPlay 호출
      await AsyncStorage.setItem('pet_video_asset_id', asset_id);
      setStatusMsg('추모 영상을 만들고 있어요... (최대 1~2분)');
      pollStatus(asset_id, 0);
    } catch {
      setError('영상 생성에 실패했어요. 다시 시도해주세요.');
      setLoading(false);
    }
  }

  // 영상 생성은 서버 백그라운드 작업 → done 될 때까지 폴링
  function pollStatus(assetId, attempt) {
    pollRef.current = setTimeout(async () => {
      try {
        const res = await getMediaStatus(assetId);
        // 음성 합쳐진 voiced_url 우선, 없으면 무음 video_url. 상대경로 → 서버주소 붙임
        const url = res.voiced_url || res.video_url;
        if (res.status === 'done' && url) {
          const fullUrl = `${API_URL}${url}`;
          setVideoUrl(fullUrl);
          await AsyncStorage.setItem('pet_video_url', fullUrl);
          setLoading(false);
        } else if (res.status === 'error') {
          setError('영상 생성 중 문제가 생겼어요. 다른 사진으로 시도해보세요.');
          setLoading(false);
        } else if (attempt >= POLL_MAX) {
          setError('영상 생성이 오래 걸리고 있어요. 잠시 후 다시 시도해주세요.');
          setLoading(false);
        } else {
          pollStatus(assetId, attempt + 1);
        }
      } catch {
        setError('상태 확인에 실패했어요. 다시 시도해주세요.');
        setLoading(false);
      }
    }, POLL_INTERVAL);
  }

  return (
    <LinearGradient colors={['#F9DFE6', '#EBDDF5', '#F0F4F8', '#E4DAF5']} locations={[0, 0.35, 0.6, 1]} style={styles.gradient}>
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
                <Text style={styles.uploadHint}>정면을 바라보는 또렷한 사진일수록 좋아요</Text>
              </>
            )}
          </TouchableOpacity>
        </Card>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        {loading ? (
          <LoadingSpinner message={statusMsg || '잠시만 기다려주세요...'} />
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
            <Video
              source={{ uri: videoUrl }}
              style={styles.video}
              useNativeControls
              resizeMode={ResizeMode.CONTAIN}
              isLooping
              shouldPlay
            />
            <Text style={styles.disclaimer}>
              AI가 보호자가 전해준 기억을 바탕으로 재해석한 추모 영상이에요.
            </Text>
          </Card>
        ) : null}
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
  resultTitle: { fontSize: 15, fontWeight: '700', color: COLORS.textPrimary, marginBottom: 12 },
  video: { width: '100%', aspectRatio: 1, borderRadius: 12, backgroundColor: '#000' },
  disclaimer: { fontSize: 12, color: COLORS.textSecondary, marginTop: 10, lineHeight: 18 },
});
