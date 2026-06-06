# driving/ — 발화(말하는) driving 영상 폴더

> LivePortrait에 **driving 영상**으로 넣어 동물 사진을 "말하는 것처럼" 만드는 입력 영상을 여기에 둡니다.
> (멀티모달 방향 전환 — [docs/LIPSYNC_EXPERIMENT.md](../../../docs/LIPSYNC_EXPERIMENT.md) 방법 3 채택: PERSO 드랍 → LivePortrait `driving_multiplier 0.4` + calm 발화영상)

## 여기에 넣을 것
- 사람이 **차분히 말하는(calm) 정면 발화 영상** (예: CREMA-D `*_calm_*.mp4`)
- 기준선: `060_TomCarper_calm_3clips.mp4` → 입 동기화 0.84, 자연스러움 4/5
- 가급적 **단일 클립**(여러 클립 concat은 전환 구간 블러 발생 — 실험 문서 참고)

## 사용 예 (animals 모드)
```bash
conda activate liveportrait
cd <LivePortrait clone>
python inference_animals.py \
  -s <동물사진.jpg> \
  -d ai/liveportrait/driving/<발화영상.mp4> \
  -o output/ \
  --no_flag_stitching \
  --driving_multiplier 0.4
```

## ⚠️ 주의
- **영상 파일(`*.mp4`·`*.mov`)은 git에 커밋되지 않습니다** (`.gitignore` 전역 처리). 이 폴더의 영상은 로컬/공유 드라이브로만 주고받으세요.
- 비교 테스트 결과는 [docs/LIPSYNC_EXPERIMENT.md](../../../docs/LIPSYNC_EXPERIMENT.md)에 기록합니다.
