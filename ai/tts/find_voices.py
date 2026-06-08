"""ElevenLabs Voice Library 에서 '발랄·귀여운' 한국어 보이스 후보 검색.

라운드2(EL 9전 9승)에서 추린 9종은 차분·따뜻 위주라, 추모 톤 외에
**발랄/귀여운 성격**(활발 페르소나)용 보이스가 부족했다. 이 스크립트는
Voice Library 를 여러 필터 조합으로 훑어 후보 + **미리듣기 URL** 을 출력한다.

⚠️ 윤리: 어린아이(미성년) 목소리는 ElevenLabs 가 정책상 막아둠 + 우리 가이드(§0)
   상으로도 부적절. 그래서 'age=young 성인 여성 + 밝은/경쾌한 음색'으로 대체 탐색.
   합성 텍스트는 항상 보호자 대상 위로 멘트만(반려동물 1인칭 ❌).

실행:
    python -m ai.tts.find_voices
출력:
    콘솔에 (이름 / voice_id / 성별·나이·억양 / descriptive / 미리듣기URL).
    마음에 드는 voice_id 를 compare_elevenlabs.py 의 _VOICE_IDS 에 넣어 합성.
"""

from __future__ import annotations

import os
import sys

from .compare_elevenlabs import _load_dotenv

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


# (라벨, get_shared 키워드인자) — 발랄/귀여운/어린아이 방향으로 여러 각도 탐색.
# 전부 language="ko" 고정. 결과는 _KO_ACCENTS 로 한 번 더 한국어 네이티브만 거름.
_QUERIES: tuple[tuple[str, dict], ...] = (
    ("한국어·여성·young", dict(language="ko", gender="female", age="young")),
    ("한국어·검색 'cute'", dict(language="ko", search="cute")),
    ("한국어·검색 'bright cheerful'", dict(language="ko", search="bright cheerful")),
    ("한국어·검색 'kid'", dict(language="ko", search="kid")),
    ("한국어·검색 '아이 어린'", dict(language="ko", search="아이 어린")),
    ("한국어·검색 '발랄 귀여운'", dict(language="ko", search="발랄 귀여운")),
)
_PAGE_SIZE = 20

# 한국어 네이티브로 인정할 accent (비한국어=영어권/스페인계 제외용).
# 빈 accent 는 통과(미표기), peninsular/american/british 등은 컷.
_KO_ACCENTS = {"", "seoul", "standard", "korean", "gyeongsang", "jeolla", "busan"}


def _is_korean_native(v) -> bool:
    accent = (getattr(v, "accent", "") or "").strip().lower()
    return accent in _KO_ACCENTS


def _fmt(v) -> str:
    vid = getattr(v, "voice_id", "?")
    name = getattr(v, "name", "?")
    gender = getattr(v, "gender", "") or ""
    age = getattr(v, "age", "") or ""
    accent = getattr(v, "accent", "") or ""
    desc = getattr(v, "descriptive", "") or ""
    preview = getattr(v, "preview_url", "") or ""
    tags = ", ".join(x for x in (gender, age, accent, desc) if x)
    return f"  {name:<16} {vid}  [{tags}]\n      ▶ {preview}"


def main() -> None:
    _load_dotenv()
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("[stop] ELEVENLABS_API_KEY 없음 → .env 설정 후 재실행")
        return
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=api_key)
    seen: set[str] = set()
    print("== ElevenLabs 발랄·귀여운 한국어 보이스 탐색 ==\n")
    for label, kw in _QUERIES:
        try:
            resp = client.voices.get_shared(page_size=_PAGE_SIZE, **kw)
            voices = getattr(resp, "voices", None) or []
        except Exception as exc:
            print(f"── {label} ── [실패: {exc}]\n")
            continue
        # 한국어 네이티브 + 중복 제거.
        fresh = [
            v
            for v in voices
            if getattr(v, "voice_id", None) not in seen and _is_korean_native(v)
        ]
        dropped = len(voices) - len([v for v in voices if _is_korean_native(v)])
        print(f"── {label} ── ({len(voices)}건, 비한국어 {dropped} 컷, 신규 {len(fresh)})")
        if not fresh:
            print("  (한국어 네이티브 신규 없음)\n")
            continue
        for v in fresh:
            seen.add(getattr(v, "voice_id", ""))
            print(_fmt(v))
        print()
    print(f"총 신규 후보 {len(seen)}종. 미리듣기(▶) URL 브라우저로 들어보고,")
    print("마음에 드는 voice_id → compare_elevenlabs.py _VOICE_IDS 에 넣어 합성.")


if __name__ == "__main__":
    main()
