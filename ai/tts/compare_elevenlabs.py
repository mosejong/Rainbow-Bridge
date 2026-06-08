"""TTS 엔진 비교 스파이크 — ElevenLabs 4성격 샘플 vs Google 현행.

PR #115가 지정한 ElevenLabs 전환을 **바로 코드에 반영하지 않고**, 같은
보호자 위로 멘트를 ElevenLabs 목소리 + Google 현행으로 합성해 A/B 청취용
mp3를 만든다. 청취 결과로 전환 여부를 결정한다(ROADMAP 🔴1).

→ 전환 확정 시에만 `tts.py` 본체·`requirements.txt`·`.env.example` 손댄다.

⚠️ 윤리(ai/tts/CLAUDE.md §5): 샘플 텍스트는 **보호자 대상 위로 멘트**만.
   반려동물 1인칭 발화·목소리 흉내 ❌. 성격별로 바뀌는 건 음색뿐, 텍스트 동일.

준비:
    1) ElevenLabs 가입 → API 키 발급, 로컬 .env 에 ELEVENLABS_API_KEY=... (커밋 금지)
       ※ 패키지(pip install elevenlabs)는 설치돼 있음.
실행:
    python -m ai.tts.compare_elevenlabs
동작:
    - 키만 넣으면 voice_id 안 채워도 **계정 기본 보이스**로 자동 합성됨.
    - 끝에 **한국어 네이티브 보이스 후보**(Voice Library)를 출력 → 더 좋은 걸로
      바꾸고 싶으면 그 voice_id 를 _VOICE_IDS 에 붙여넣고 재실행.
출력:
    ai/tts/_output/compare/el_{성격}.mp3       (ElevenLabs)
    ai/tts/_output/compare/google_{tone}.mp3   (GCP 키 있을 때만)
"""

from __future__ import annotations

import os
import sys

from .tts import _OUTPUT_DIR, TtsTone, synthesize

# Windows 콘솔(cp949)에서 한글·기호 출력 깨짐/크래시 방지.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def _load_dotenv() -> None:
    """레포 루트 .env 를 읽어 환경변수로 주입(이 스크립트는 단독 실행이라 필요).

    KEY=VALUE 형식, '=' 앞뒤 공백·따옴표 허용. 이미 설정된 값은 덮어쓰지 않음.
    """
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, ".env")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value


# 비교 출력 폴더 (*.mp3 는 .gitignore 됨 — 각자 로컬 생성).
_COMPARE_DIR = os.path.join(_OUTPUT_DIR, "compare")

# 보호자 대상 위로 멘트(특정 반려동물 언급·1인칭 ❌). 전 성격 공통 — 음색만 비교.
_SAMPLE_TEXT = (
    "오늘도 마음이 많이 무거우셨죠. 함께한 시간들은 사라지지 않고 "
    "당신 곁에 따뜻하게 남아 있어요. 너무 자책하지 마시고, "
    "천천히 호흡하며 오늘 하루를 보내셔도 괜찮아요."
)

# 4성격 — PR #115 음색 방향. voice_id 는 비워두면 계정 기본 보이스로 자동 배정.
# 더 좋은 한국어 보이스를 쓰려면 실행 끝의 "한국어 후보" 목록에서 voice_id 복사해 채운다.
_PERSONALITIES: tuple[tuple[str, str], ...] = (
    ("활발", "밝고 통통 튀는"),
    ("순둥이", "따뜻하고 포근한"),
    ("도도", "차분하고 낮은"),
    ("노령", "느리고 온화한"),
)
# ⚠️ Free 플랜은 API 로 Library(한국어 네이티브) 보이스 사용 불가 → 유료 Creator+ 필요.
# 그래서 기본은 비워서 **계정 기본 보이스(영어권)** 로 자동 합성(한국어 발음에 억양 섞임).
# 유료 전환·네이티브 보이스 테스트 시 아래에 한국어 voice_id 채우기(실행 끝 후보 목록 참고).
_VOICE_IDS: dict[str, str] = {name: "" for name, _ in _PERSONALITIES}

# ElevenLabs 합성 파라미터 — 추모 맥락이라 안정적·절제된 톤. 청취 후 튜닝.
_MODEL_ID = "eleven_multilingual_v2"
_OUTPUT_FORMAT = "mp3_44100_128"


def _voice_settings():
    """추모용 차분한 기본 보이스 세팅(있으면). 실패해도 None 으로 진행."""
    try:
        from elevenlabs import VoiceSettings

        return VoiceSettings(
            stability=0.55, similarity_boost=0.75, style=0.0, use_speaker_boost=True
        )
    except Exception:
        return None


def _account_voice_ids(client, n: int) -> list[tuple[str, str]]:
    """계정에서 바로 쓸 수 있는 보이스 n개 (name, voice_id)."""
    try:
        resp = client.voices.get_all()
        voices = getattr(resp, "voices", None) or []
        out = []
        for v in voices:
            vid = getattr(v, "voice_id", None)
            if vid:
                out.append((getattr(v, "name", "?"), vid))
            if len(out) >= n:
                break
        return out
    except Exception as exc:
        print(f"[warn] 계정 보이스 조회 실패: {exc}")
        return []


def _resolve_mapping(client) -> dict[str, str]:
    """성격→voice_id 확정. 수동 지정값 우선, 빈 칸은 계정 보이스로 자동 채움."""
    mapping = {name: vid for name, vid in _VOICE_IDS.items() if vid}
    missing = [name for name, _ in _PERSONALITIES if name not in mapping]
    if missing:
        auto = _account_voice_ids(client, len(missing))
        if not auto:
            print("[warn] 자동 배정할 계정 보이스가 없음 → _VOICE_IDS 수동 입력 필요")
        for name, (vname, vid) in zip(missing, auto):
            mapping[name] = vid
            print(f"  [자동] {name} ← 계정 보이스 '{vname}' ({vid})")
    return mapping


def _synthesize_elevenlabs(client, voice_id: str, dest: str, settings) -> None:
    """ElevenLabs 로 _SAMPLE_TEXT(한국어) 합성해 dest(mp3) 저장."""
    kwargs = dict(
        voice_id=voice_id,
        text=_SAMPLE_TEXT,
        model_id=_MODEL_ID,
        output_format=_OUTPUT_FORMAT,
        language_code="ko",
    )
    if settings is not None:
        kwargs["voice_settings"] = settings
    audio = client.text_to_speech.convert(**kwargs)
    with open(dest, "wb") as f:
        for chunk in audio:  # convert() 는 bytes 청크 이터레이터
            if chunk:
                f.write(chunk)


def _print_korean_candidates(client, limit: int = 12) -> None:
    """Voice Library 의 한국어 네이티브 보이스 후보 출력(수동 교체용)."""
    try:
        resp = client.voices.get_shared(language="ko", page_size=limit)
        voices = getattr(resp, "voices", None) or []
    except Exception as exc:
        print(f"[skip] 한국어 후보 조회 실패: {exc}")
        return
    if not voices:
        print("[info] 한국어 공개 보이스 후보 없음")
        return
    print(
        "\n── 한국어 네이티브 보이스 후보 (Voice Library) — 더 쓰려면 voice_id 복사 ──"
    )
    for v in voices:
        vid = getattr(v, "voice_id", "?")
        name = getattr(v, "name", "?")
        accent = getattr(v, "accent", "") or ""
        gender = getattr(v, "gender", "") or ""
        age = getattr(v, "age", "") or ""
        desc = ", ".join(x for x in (gender, age, accent) if x)
        print(f"  {vid}  {name}  [{desc}]")


def _run_elevenlabs() -> None:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print(
            "[skip] ELEVENLABS_API_KEY 없음 → ElevenLabs 건너뜀 (.env 설정 후 재실행)"
        )
        return
    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        print("[skip] elevenlabs 미설치 → `python -m pip install elevenlabs` 후 재실행")
        return

    client = ElevenLabs(api_key=api_key)
    settings = _voice_settings()
    mapping = _resolve_mapping(client)

    for name, _hint in _PERSONALITIES:
        voice_id = mapping.get(name)
        if not voice_id:
            print(f"[skip] {name}: voice_id 없음")
            continue
        dest = os.path.join(_COMPARE_DIR, f"el_{name}.mp3")
        try:
            _synthesize_elevenlabs(client, voice_id, dest, settings)
            print(f"saved {dest}  (voice_id={voice_id})")
        except Exception as exc:  # 한 성격 실패해도 나머지 계속
            print(f"[warn] ElevenLabs 합성 실패 [{name}/{voice_id}]: {exc}")

    _print_korean_candidates(client)


def _run_google() -> None:
    """현행 Google(또는 gTTS 폴백) 베이스라인 — 동일 텍스트, 톤별."""
    for tone in TtsTone:
        try:
            result = synthesize(
                _SAMPLE_TEXT, tone, filename=f"compare_google_{tone.value}.mp3"
            )
            print(
                f"saved {result['audio_path']}  ({tone.value}, {result['duration']}s)"
            )
        except Exception as exc:
            print(f"[skip] Google 베이스라인 [{tone.value}] 건너뜀: {exc}")
            break  # 키 없으면 전부 실패 → 첫 실패에서 중단


def main() -> None:
    _load_dotenv()
    os.makedirs(_COMPARE_DIR, exist_ok=True)
    print(f"== TTS 비교 샘플 → {_COMPARE_DIR} ==")
    print(f"샘플 텍스트: {_SAMPLE_TEXT}\n")
    _run_elevenlabs()
    print()
    _run_google()
    print("\ndone — _output/compare/ 청취 후 ENGINE_NOTES.md 에 비교 기록")


if __name__ == "__main__":
    main()
