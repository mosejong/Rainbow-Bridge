"""
테스트 계정 시드 스크립트
회복 게이트 3단계(locked / teaser / open) 테스트용 계정 5개 생성

실행:
    cd backend
    python scripts/seed_test_accounts.py [BASE_URL]

    예) python scripts/seed_test_accounts.py http://localhost:8000
        python scripts/seed_test_accounts.py http://101.79.19.87
"""

import sys
import httpx

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"

# ── 테스트 계정 시나리오 ────────────────────────────────────────────
ACCOUNTS = [
    {
        "nickname": "테스트_잠김",
        "email": "test_locked@rainbow.dev",
        "password": "test1234",
        "pet_name": "봄이",
        "species": "강아지",
        # 체크인 없음 → gate: locked
        "emotions": [],
    },
    {
        "nickname": "테스트_데이터부족",
        "email": "test_few@rainbow.dev",
        "password": "test1234",
        "pet_name": "하늘이",
        "species": "고양이",
        # 체크인 2회 (최소 3회 미충족) → gate: locked
        "emotions": [
            {"score": 7, "note": "조금 나아진 것 같아요"},
            {"score": 6, "note": ""},
        ],
    },
    {
        "nickname": "테스트_티저",
        "email": "test_teaser@rainbow.dev",
        "password": "test1234",
        "pet_name": "달이",
        "species": "강아지",
        # 평균 6점 → recovery_pct 60 → gate: teaser
        "emotions": [
            {"score": 6, "note": ""},
            {"score": 6, "note": ""},
            {"score": 6, "note": ""},
            {"score": 6, "note": ""},
        ],
    },
    {
        "nickname": "테스트_오픈",
        "email": "test_open@rainbow.dev",
        "password": "test1234",
        "pet_name": "별이",
        "species": "고양이",
        # 평균 9점 → recovery_pct 90 → gate: open
        "emotions": [
            {"score": 9, "note": ""},
            {"score": 9, "note": ""},
            {"score": 9, "note": ""},
            {"score": 8, "note": ""},
            {"score": 9, "note": ""},
        ],
    },
    {
        "nickname": "테스트_위기잠김",
        "email": "test_risk@rainbow.dev",
        "password": "test1234",
        "pet_name": "구름이",
        "species": "강아지",
        # risk_level 2 발생 → 점수 높아도 gate: locked 유지
        "emotions": [
            {"score": 8, "note": ""},
            {"score": 8, "note": ""},
            {"score": 2, "note": "너무 힘들어서 사라지고 싶어요"},  # L2 위기 유발
            {"score": 8, "note": ""},
        ],
    },
]
# ────────────────────────────────────────────────────────────────────


def register(client, account):
    r = client.post("/api/v1/auth/register", json={
        "email": account["email"],
        "password": account["password"],
        "nickname": account["nickname"],
    })
    if r.status_code == 201:
        print("  ✅ 가입 완료")
    elif r.status_code == 400 and "already" in r.text.lower():
        print("  ⚠️  이미 존재하는 계정, 계속 진행")
    else:
        print(f"  ❌ 가입 실패: {r.status_code} {r.text}")


def login(client, account):
    r = client.post("/api/v1/auth/login", json={
        "email": account["email"],
        "password": account["password"],
    })
    if r.status_code != 200:
        print(f"  ❌ 로그인 실패: {r.status_code}")
        return None
    return r.json()["access_token"]


def create_pet(client, token, account):
    r = client.post("/api/v1/pets", json={
        "name": account["pet_name"],
        "species": account["species"],
        "period": "2020-01-01 ~ 2026-06-01",
        "caller_name": "보호자",
    }, headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 201:
        print(f"  ✅ 펫 등록: {account['pet_name']}")
        return r.json()["id"]
    else:
        # 이미 있으면 목록에서 가져오기
        pets = client.get("/api/v1/pets", headers={"Authorization": f"Bearer {token}"})
        if pets.status_code == 200 and pets.json():
            return pets.json()[0]["id"]
        print(f"  ❌ 펫 등록 실패: {r.status_code}")
        return None


def post_emotions(client, token, pet_id, emotions):
    for i, e in enumerate(emotions):
        r = client.post("/api/v1/emotions", json={
            "pet_id": pet_id,
            "score": e["score"],
            "note": e.get("note", ""),
        }, headers={"Authorization": f"Bearer {token}"})
        status = "✅" if r.status_code == 201 else "❌"
        risk = r.json().get("risk_level", "?") if r.status_code == 201 else "?"
        print(f"  {status} 체크인 {i+1}: score={e['score']} risk={risk}")


def check_gate(client, token, pet_id):
    r = client.get(f"/api/v1/emotions/recovery/{pet_id}",
                   headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 200:
        d = r.json()
        print(f"  🔒 gate_status={d.get('gate_status')} | "
              f"recovery_pct={d.get('recovery_pct')} | "
              f"content_unlocked={d.get('content_unlocked')} | "
              f"avg={d.get('avg_score')}")
    else:
        print(f"  ❌ recovery 조회 실패: {r.status_code}")


def main():
    print("🌈 레인보우 브릿지 테스트 계정 시드")
    print(f"   서버: {BASE_URL}\n")

    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        for acc in ACCOUNTS:
            print(f"── {acc['nickname']} ({acc['email']}) ──")
            register(client, acc)
            token = login(client, acc)
            if not token:
                continue
            pet_id = create_pet(client, token, acc)
            if not pet_id:
                continue
            if acc["emotions"]:
                post_emotions(client, token, pet_id, acc["emotions"])
            check_gate(client, token, pet_id)
            print()

    print("✅ 완료")
    print("\n테스트 계정 목록:")
    for acc in ACCOUNTS:
        print(f"  {acc['email']} / {acc['password']}  ({acc['nickname']})")


if __name__ == "__main__":
    main()
