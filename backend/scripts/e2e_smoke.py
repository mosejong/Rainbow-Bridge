"""백엔드 E2E 스모크 — 실제 떠 있는 서버에 전체 사용자 흐름을 왕복 호출합니다.

흐름: 회원가입 → 로그인 → 펫 등록 → 감정 체크인 → 회복 신호 → 추모 메시지 → TTS

mock 없이 진짜 HTTP 로 돕니다. 로컬(uvicorn) 또는 NCP 실서버 어디에나 사용 가능.

실행:
    # 로컬 (기본값 http://localhost:8000)
    python backend/scripts/e2e_smoke.py

    # NCP 실서버 대상
    E2E_BASE_URL=https://rainbow-bridge.duckdns.org python backend/scripts/e2e_smoke.py

종료 코드: 실패한 단계 수 (0 = 전부 통과).
"""

import os
import sys
import uuid

import httpx

# Windows 콘솔(cp949)에서도 한글·체크마크가 깨지지 않게 UTF-8 강제
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE_URL}/api/v1"

# 매 실행마다 새 유저 → DB 상태에 의존하지 않음
_UID = uuid.uuid4().hex[:8]
EMAIL = f"e2e_{_UID}@example.com"
PASSWORD = "e2etest123"
NICKNAME = f"E2E_{_UID}"

_failures: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> bool:
    """단계 결과를 기록·출력하고 성공 여부를 반환."""
    mark = "✅" if ok else "❌"
    print(f"{mark} {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        _failures.append(name)
    return ok


def main() -> int:
    print(f"▶ 대상: {API}")
    print(f"▶ 테스트 계정: {EMAIL}\n")

    # httpx 동기 클라이언트, TTS(원격 합성) 대비 타임아웃 넉넉히
    with httpx.Client(timeout=90.0) as client:
        # 1) 회원가입
        r = client.post(
            f"{API}/auth/register",
            json={"email": EMAIL, "password": PASSWORD, "nickname": NICKNAME},
        )
        if not _check(
            "회원가입 POST /auth/register", r.status_code == 201, f"{r.status_code}"
        ):
            print("   회원가입 실패 → 중단", r.text[:200])
            return len(_failures)

        # 2) 로그인 → 토큰
        r = client.post(
            f"{API}/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
        token = r.json().get("access_token", "") if r.status_code == 200 else ""
        if not _check(
            "로그인 POST /auth/login",
            bool(token),
            f"{r.status_code}, token_len={len(token)}",
        ):
            print("   토큰 없음 → 중단", r.text[:200])
            return len(_failures)
        auth = {"Authorization": f"Bearer {token}"}

        # 3) 펫 등록
        r = client.post(
            f"{API}/pets",
            headers=auth,
            json={
                "name": "초코",
                "species": "강아지",
                "breed": "푸들",
                "memories": [
                    {"keyword": "공원산책", "detail": "매일 아침 함께 걸었어요"}
                ],
                "caller_name": "엄마",
            },
        )
        pet_id = r.json().get("id", "") if r.status_code == 201 else ""
        if not _check(
            "펫 등록 POST /pets", bool(pet_id), f"{r.status_code}, pet_id={pet_id}"
        ):
            print("   펫 ID 없음 → 중단", r.text[:200])
            return len(_failures)

        # 4) 펫 조회
        r = client.get(f"{API}/pets/{pet_id}", headers=auth)
        _check("펫 조회 GET /pets/{id}", r.status_code == 200, f"{r.status_code}")

        # 5) 감정 체크인 (여러 번 → 회복 신호 산출용)
        for i, score in enumerate([4, 6, 7], 1):
            r = client.post(
                f"{API}/emotions",
                headers=auth,
                json={"pet_id": pet_id, "score": score, "note": f"체크인 {i}"},
            )
            ok = r.status_code == 201 and "risk_level" in r.json()
            _check(
                f"감정 체크인 #{i} POST /emotions (score={score})",
                ok,
                f"{r.status_code}, risk={r.json().get('risk_level') if ok else '-'}",
            )

        # 6) 회복 신호
        r = client.get(f"{API}/emotions/recovery/{pet_id}", headers=auth)
        body = r.json() if r.status_code == 200 else {}
        ok = r.status_code == 200 and "recovery_pct" in body
        _check(
            "회복 신호 GET /emotions/recovery/{id}",
            ok,
            f"{r.status_code}, trend={body.get('trend')}, pct={body.get('recovery_pct')}, "
            f"unlocked={body.get('content_unlocked')}, 1인칭={body.get('allow_first_person')}",
        )

        # 7) 추모 메시지 (guardian_nickname 전달 포함)
        r = client.post(
            f"{API}/messages",
            headers=auth,
            json={
                "pet_id": pet_id,
                "tone": "warm",
                "emotion_score": 7,
                "consent": False,
                "guardian_nickname": NICKNAME,
            },
        )
        body = r.json() if r.status_code == 201 else {}
        ok = r.status_code == 201 and bool(body.get("content"))
        _check(
            "추모 메시지 POST /messages",
            ok,
            f"{r.status_code}, source={body.get('source')}, len={len(body.get('content', ''))}",
        )

        # 8) TTS 합성 (원격 Qwen3 or Google 폴백 — 둘 다 정상)
        r = client.post(
            f"{API}/tts",
            headers=auth,
            json={"pet_id": pet_id, "tone": "warm", "text": "무지개 다리 잘 건너가렴"},
        )
        body = r.json() if r.status_code == 201 else {}
        ok = r.status_code == 201 and bool(body.get("audio_url"))
        _check(
            "TTS 합성 POST /tts",
            ok,
            f"{r.status_code}, format={body.get('format')}, dur={body.get('duration')}, "
            f"url={body.get('audio_url')}",
        )

    print()
    if _failures:
        print(f"❌ 실패 {len(_failures)}건: {', '.join(_failures)}")
    else:
        print("✅ 전체 흐름 통과")
    return len(_failures)


if __name__ == "__main__":
    sys.exit(main())
