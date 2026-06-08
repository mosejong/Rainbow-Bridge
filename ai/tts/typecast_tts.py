"""Typecast API — 한국어 보이스 목록 조회 + 위로 멘트 합성 (스파이크).

성우 기반 완성형 보이스를 귀로 골라 쓰는 방향(묘사 추측 X). 추모 위로 멘트엔
'따뜻한 어른 내레이터' 톤을 목표로 한다(어린이 톤은 반려동물 1인칭 작별 전용).

키 준비(채팅에 붙이지 말 것 — 노출됨):
    ai/tts/.env 파일에 한 줄:  TYPECAST_API_KEY=발급받은키
    (.env 는 .gitignore 로 커밋 제외됨)

실행:
    conda run --no-capture-output -n qwen3-tts python ai/tts/typecast_tts.py list
    conda run --no-capture-output -n qwen3-tts python ai/tts/typecast_tts.py synth <voice_id> [voice_id2 ...]
출력:
    ai/tts/_output/typecast/typecast_{voice_id}.wav
"""

from __future__ import annotations

import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

import requests

_DIR = os.path.dirname(os.path.abspath(__file__))
_OUT_DIR = os.path.join(_DIR, "_output", "typecast")
_ENV = os.path.join(_DIR, ".env")
_BASE = "https://api.typecast.ai"

# 보호자 대상 위로 멘트 — 다른 엔진과 동일(공정 비교). 따뜻한 어른 내레이터 톤,
# 반려동물 1인칭/부활 표현 없음(윤리 경계 안).
_MENTS: dict[str, str] = {
    # ① 첫인상용 (짧게 — 목소리 결 확인)
    "m1": "오늘 하루도 정말 수고 많으셨어요. 천천히, 편안하게 쉬어도 괜찮아요.",
    # ② 메인 추모 위로 (감정 표현 확인 — 비교 기준 멘트)
    "m2": (
        "오늘도 마음이 많이 무거우셨죠. 함께한 시간들은 사라지지 않고 "
        "당신 곁에 따뜻하게 남아 있어요. 너무 자책하지 마시고, "
        "천천히 호흡하며 오늘 하루를 보내셔도 괜찮아요."
    ),
    # ③ 잔잔한 회복 독려 (밝되 들뜨지 않게)
    "m3": (
        "힘든 시간을 지나오느라 애쓰셨어요. 슬픔은 사랑했던 만큼 깊은 거예요. "
        "오늘은 따뜻한 차 한 잔과 함께, 잠시 숨을 고르는 건 어떨까요."
    ),
    # ④ 긴 호흡 (낭독 안정성·끊김 확인)
    "m4": (
        "당신이 함께한 모든 순간은 헛되지 않았어요. 작은 발소리, 곁에 머물던 온기, "
        "눈을 마주치던 그 시간들. 그 기억은 사라지지 않고 당신 안에 오래도록 남아, "
        "힘든 날엔 조용히 당신을 지켜줄 거예요. 그러니 너무 서두르지 말고, "
        "당신의 속도로 천천히 걸어가셔도 괜찮습니다."
    ),
}
_TEXT = _MENTS["m2"]  # 기존 단일 합성 호환

# 후보 보이스 — synthall 기본 대상. tc_69c1…은 환주님이 제외(2026-06-08) → 4종 유지.
_DEFAULT_VOICES: tuple[str, ...] = (
    "tc_66596206b7bd6e89c3a2c54e",
    "tc_60db308484130840f23e6ca0",
    "tc_5ffda49bcba8f6d3d46fc447",
    "tc_5ffda44bcba8f6d3d46fc41f",
)


def _load_key() -> str | None:
    if os.path.exists(_ENV):
        with open(_ENV, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TYPECAST_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("TYPECAST_API_KEY")


def _headers(key: str) -> dict:
    return {"X-API-KEY": key, "Content-Type": "application/json"}


def _get_voices(key: str):
    """보이스 목록 — 엔드포인트 버전차 대비 v1/v2 둘 다 시도."""
    last = None
    for ep in ("/v1/voices", "/v2/voices"):
        try:
            r = requests.get(_BASE + ep, headers=_headers(key), timeout=30)
        except Exception as e:  # noqa: BLE001
            last = e
            continue
        if r.ok:
            return ep, r.json()
        last = f"{ep} → {r.status_code}: {r.text[:200]}"
    raise RuntimeError(f"보이스 목록 조회 실패: {last}")


def _is_korean(v: dict) -> bool:
    blob = " ".join(str(v.get(k, "")) for k in ("language", "languages", "locale", "lang")).lower()
    if any(t in blob for t in ("kor", "ko-", "korea", "ko_")):
        return True
    name = str(v.get("voice_name") or v.get("name") or "")
    return any("가" <= ch <= "힣" for ch in name)  # 한글 포함


def cmd_list(key: str) -> None:
    ep, data = _get_voices(key)
    voices = data if isinstance(data, list) else data.get("voices") or data.get("data") or []
    print(f"== Typecast 보이스 {len(voices)}개 (조회 {ep}) ==\n")
    if voices:
        print(f"[샘플 객체 키] {list(voices[0].keys())}\n")

    kor = [v for v in voices if _is_korean(v)]
    print(f"-- 한국어로 보이는 보이스 {len(kor)}개 --")
    for v in kor:
        vid = v.get("voice_id") or v.get("id") or "?"
        name = v.get("voice_name") or v.get("name") or "?"
        meta = {
            k: v.get(k)
            for k in ("gender", "age", "emotions", "styles", "model", "language", "languages")
            if v.get(k) not in (None, "", [])
        }
        print(f"  {vid}  | {name}  | {meta}")
    if not kor:
        print("  (한국어 자동 식별 실패 — 아래 전체에서 직접 고르세요)")
        for v in voices[:60]:
            vid = v.get("voice_id") or v.get("id") or "?"
            name = v.get("voice_name") or v.get("name") or "?"
            print(f"  {vid}  | {name}")
    print("\n→ 마음에 드는 voice_id 로:  python ai/tts/typecast_tts.py synth <voice_id> ...")


def _synth_one(key: str, vid: str, text: str, dest: str) -> bool:
    body = {
        "voice_id": vid,
        "text": text,
        "model": "ssfm-v30",
        "language": "kor",
        "output": {"audio_format": "wav"},
    }
    try:
        r = requests.post(
            _BASE + "/v1/text-to-speech",
            headers=_headers(key),
            json=body,
            timeout=120,
        )
        if not r.ok:
            print(f"[fail] {os.path.basename(dest)}: {r.status_code} {r.text[:200]}")
            return False
        with open(dest, "wb") as f:
            f.write(r.content)
        print(f"saved {os.path.basename(dest)} | {len(r.content) / 1024:.0f} KB")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[fail] {os.path.basename(dest)}: {type(e).__name__}: {str(e)[:200]}")
        return False


def cmd_synth(key: str, voice_ids: list[str]) -> None:
    os.makedirs(_OUT_DIR, exist_ok=True)
    print(f"== Typecast 합성 → {_OUT_DIR} ==")
    print(f"텍스트({len(_TEXT)}자): {_TEXT}\n")
    for vid in voice_ids:
        _synth_one(key, vid, _TEXT, os.path.join(_OUT_DIR, f"typecast_{vid}.wav"))
    print("\ndone — _output/typecast/ 청취")


def cmd_synthall(key: str, voice_ids: list[str], ment_keys: list[str]) -> None:
    """멘트 여러 개 × 보이스 여러 개 매트릭스 합성. 파일: typecast_{vid}_{mkey}.wav."""
    os.makedirs(_OUT_DIR, exist_ok=True)
    print(f"== Typecast 매트릭스 합성 → {_OUT_DIR} ==")
    print(f"보이스 {len(voice_ids)}종 × 멘트 {ment_keys} = {len(voice_ids) * len(ment_keys)}건\n")
    for mk in ment_keys:
        print(f"[{mk}] ({len(_MENTS[mk])}자) {_MENTS[mk][:30]}…")
    print()
    ok = 0
    for vid in voice_ids:
        for mk in ment_keys:
            dest = os.path.join(_OUT_DIR, f"typecast_{vid}_{mk}.wav")
            if _synth_one(key, vid, _MENTS[mk], dest):
                ok += 1
    print(f"\ndone — {ok}/{len(voice_ids) * len(ment_keys)}건 성공 · _output/typecast/ 청취")


def cmd_refine(key: str, vid: str) -> None:
    """한 보이스의 지지직(아티팩트) 해결용 — 모델·라우드니스 조합별 재합성.

    멘트②로 변형 생성 → analyze_noise 로 glitch/crest 비교해 깨끗한 조합 채택.
    파일: _output/typecast/refine/{vid}_{label}.wav
    """
    out = os.path.join(_OUT_DIR, "refine")
    os.makedirs(out, exist_ok=True)
    text = _MENTS["m2"]
    # (라벨, model, output 추가옵션). target_lufs=라우드니스 정규화(과음량 완화).
    configs = [
        ("v30_base", "ssfm-v30", {}),
        ("v30_lufs16", "ssfm-v30", {"target_lufs": -16.0}),
        ("v21", "ssfm-v21", {}),
        ("v21_lufs16", "ssfm-v21", {"target_lufs": -16.0}),
    ]
    print(f"== refine {vid} → {out} ==\n")
    for label, model, extra in configs:
        body = {
            "voice_id": vid,
            "text": text,
            "model": model,
            "language": "kor",
            "output": {"audio_format": "wav", **extra},
        }
        dest = os.path.join(out, f"{vid}_{label}.wav")
        try:
            r = requests.post(
                _BASE + "/v1/text-to-speech", headers=_headers(key), json=body, timeout=120
            )
            if not r.ok:
                print(f"[fail] {label}: {r.status_code} {r.text[:200]}")
                continue
            with open(dest, "wb") as f:
                f.write(r.content)
            print(f"saved {label}.wav | {len(r.content) / 1024:.0f} KB | {model} {extra}")
        except Exception as e:  # noqa: BLE001
            print(f"[fail] {label}: {type(e).__name__}: {str(e)[:200]}")
    print("\ndone — analyze_noise 로 glitch/crest 비교")


def main() -> None:
    key = _load_key()
    if not key:
        print("❌ TYPECAST_API_KEY 없음 — ai/tts/.env 에  TYPECAST_API_KEY=키  한 줄 넣으세요.")
        sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        cmd_list(key)
    elif cmd == "synth":
        ids = sys.argv[2:]
        if not ids:
            print("사용법: python ai/tts/typecast_tts.py synth <voice_id> [voice_id2 ...]")
            sys.exit(1)
        cmd_synth(key, ids)
    elif cmd == "synthall":
        # synthall [m1 m3 m4 ...]  — 멘트키 생략 시 ②제외 ①③④(② 이미 합성됨).
        mks = [a for a in sys.argv[2:] if a in _MENTS]
        if not mks:
            mks = ["m1", "m3", "m4"]
        cmd_synthall(key, list(_DEFAULT_VOICES), mks)
    elif cmd == "refine":
        ids = sys.argv[2:]
        if not ids:
            print("사용법: python ai/tts/typecast_tts.py refine <voice_id>")
            sys.exit(1)
        cmd_refine(key, ids[0])
    else:
        print(f"알 수 없는 명령: {cmd} (list | synth | synthall | refine)")
        sys.exit(1)


if __name__ == "__main__":
    main()
