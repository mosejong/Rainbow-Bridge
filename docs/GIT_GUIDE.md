# 📖 Git 활용법 & 브랜치 관리 (팀원 필독)

> 이 문서 하나면 우리 프로젝트에서 Git 때문에 막힐 일은 없습니다.
> **Git이 처음이어도 괜찮습니다.** 위에서부터 그대로 따라 하세요.
> 협업 규칙(브랜치 네이밍·커밋 컨벤션)은 [CONTRIBUTING.md](CONTRIBUTING.md) 참고.

---

## 목차

1. [Git이 뭐고 왜 쓰나](#1-git이-뭐고-왜-쓰나)
2. [최초 1회 세팅](#2-최초-1회-세팅)
3. [레포 가져오기 (clone)](#3-레포-가져오기-clone)
4. [매일 작업하는 기본 흐름 ⭐](#4-매일-작업하는-기본-흐름-)
5. [브랜치 관리](#5-브랜치-관리)
6. [Pull Request 올리기](#6-pull-request-올리기)
7. [충돌(conflict) 해결](#7-충돌conflict-해결)
8. [자주 하는 실수 & 되돌리기](#8-자주-하는-실수--되돌리기)
9. [절대 하면 안 되는 것 🚫](#9-절대-하면-안-되는-것-)
10. [치트시트](#10-치트시트)

---

## 1. Git이 뭐고 왜 쓰나

- **Git** = 코드의 "저장 + 변경 이력" 관리 도구 (내 PC에서 동작)
- **GitHub** = 그 Git 저장소를 인터넷에 올려 팀과 공유하는 곳
- 비유: Git은 게임 "세이브 파일", GitHub는 그 세이브를 올리는 "클라우드"

핵심 단어 3개만 기억:
| 단어 | 뜻 |
|------|-----|
| `commit` | 변경사항을 한 덩어리로 "저장" (세이브) |
| `push` | 내 커밋을 GitHub로 "올리기" |
| `pull` | GitHub의 최신 코드를 내 PC로 "내려받기" |

---

## 2. 최초 1회 세팅

설치: [git-scm.com](https://git-scm.com) 에서 다운로드 후 설치.

설치 후 터미널(Windows는 PowerShell)에서 **내 정보 등록** (한 번만):

```bash
git config --global user.name "본인이름"
git config --global user.email "github가입이메일@example.com"

# 줄바꿈 문자 자동 변환 (Windows 권장)
git config --global core.autocrlf true

# 기본 브랜치 이름 main 으로
git config --global init.defaultBranch main

# 확인
git config --global --list
```

> ⚠️ `user.email` 은 **GitHub 가입 이메일과 동일**해야 커밋에 내 프로필이 연결됩니다.

---

## 3. 레포 가져오기 (clone)

```bash
# 원하는 폴더로 이동 후
git clone <레포_주소>
cd rainbow-bridge

# 환경변수 파일 준비
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
```

> 레포 주소는 GitHub 레포 페이지의 초록색 **Code** 버튼 → HTTPS 주소 복사.

---

## 4. 매일 작업하는 기본 흐름 ⭐

> 우리는 **인당 1브랜치**입니다. 내 이름 브랜치 하나에서만 작업해요.
> (모세종=`mosejong`, 김윤한=`kimyunhan`, 반소람=`bansoram`, 정환주=`junghwanju`, 민경이=`mingyeongi`, 장민수=`jangminsu`)

> 평소 작업은 **`dev`** 에 모읍니다. `main` 은 MVP 완성·서비스 가능 시점에만 써요.

### 🥚 최초 1회 — 내 브랜치 만들기 (딱 한 번)

```bash
git checkout dev
git pull origin dev
git checkout -b mosejong          # ← 본인 영문 이름으로!
git push -u origin mosejong       # 내 브랜치를 GitHub에도 올림
```

### 🔁 매일 작업 — 이 4단계가 전부입니다

```bash
# (1) 내 브랜치로 가서, dev 최신 내용 받아오기  ← 작업 시작 전 항상!
git checkout mosejong
git merge dev                     # (또는: git pull origin dev)

# (2) 코드 작업... 그리고 저장(커밋)
git add .                                  # 변경 파일 전부 무대에 올림
git commit -m "feat: 반려동물 프로필 등록 API 추가"

# (3) GitHub로 올리기
git push                          # 최초 1회 -u 했으면 이후엔 git push 만

# (4) 기능 하나 끝났으면 GitHub 웹에서 Pull Request 생성 (base: dev, 아래 6번 참고)
```

> 💡 커밋은 자주·잘게. PR은 "기능 하나 끝났을 때" 단위로, **`dev` 로** 올립니다.
> 💡 PR이 머지된 뒤에도 **내 브랜치는 그대로 둡니다.** (1)번처럼 dev를 다시 받아와서 계속 쓰면 됩니다.

### `git add` 세분화

```bash
git add .                  # 전부 추가
git add app/main.py        # 특정 파일만
git status                 # 지금 무슨 파일이 바뀌었는지 확인 (자주 쓰기!)
git diff                   # 뭐가 어떻게 바뀌었는지 코드로 확인
```

---

## 5. 브랜치 관리

```bash
git branch                 # 내 로컬 브랜치 목록 (현재 위치 * 표시)
git branch -a              # 원격 포함 전체
git checkout 내이름         # 내 브랜치로 이동 (예: git checkout mosejong)
git checkout dev           # dev로 이동 (보기/최신화용, 직접 작업 ❌)
```

> 🌳 브랜치 3종류: `main`(서비스 가능 시) · `dev`(평소 통합) · `내이름`(내 작업). 작업은 **내 이름 브랜치에서만.**

### 내 브랜치 = 내 영문 이름 (인당 1개)

| 이름 | 브랜치 | 이름 | 브랜치 |
|------|--------|------|--------|
| 모세종 | `mosejong` | 정환주 | `junghwanju` |
| 김윤한 | `kimyunhan` | 민경이 | `mingyeongi` |
| 반소람 | `bansoram` | 장민수 | `jangminsu` |

> 🔁 **한 사람 = 한 브랜치.** 새 브랜치를 계속 만들지 않고, 내 이름 브랜치 하나만 씁니다.
> PR이 머지돼도 **삭제하지 않습니다** — 같은 브랜치에서 계속 작업해요.

### 작업 시작 전 / 도중에 dev가 업데이트됐다면 (최신 반영)

```bash
git checkout dev
git pull origin dev
git checkout 내이름         # 예: git checkout mosejong
git merge dev              # dev의 최신 변경을 내 브랜치로 가져옴
# (충돌나면 7번 참고)
```

---

## 6. Pull Request 올리기

1. `git push` 하면 터미널에 PR 생성 링크가 뜸 → 클릭
   (또는 GitHub 레포 페이지에 "Compare & pull request" 노란 버튼)
2. **base: `dev`** ← **compare: `내이름`(예: mosejong)** 인지 확인 ⚠️ (base가 main 아님!)
3. 제목: 커밋 컨벤션대로 (`feat: 추모 메시지 생성 API`)
4. 본문 템플릿 채우기 (무엇을/왜/테스트 방법)
5. 오른쪽 **Reviewers** 에 리뷰어 지정
6. **Create pull request**
7. 리뷰어 1명 승인 → **Squash and merge** (⚠️ 머지 후 **내 브랜치는 삭제하지 않음**)

> 머지된 뒤엔 `git checkout 내이름 && git merge dev` 로 내 브랜치를 최신화하고 계속 작업.
> 🚀 `main` 은 MVP 완성·서비스 가능 시점에 **PM이 `dev → main` PR**로 승격합니다.

---

## 7. 충돌(conflict) 해결

여러 명이 같은 파일 같은 줄을 고치면 충돌이 납니다. **당황 금지, 흔한 일입니다.**

충돌 시 파일 안에 이런 표시가 생깁니다:

```
<<<<<<< HEAD
내 코드 (현재 브랜치)
=======
상대 코드 (가져오는 쪽)
>>>>>>> main
```

**해결 순서:**

1. `<<<<<<<`, `=======`, `>>>>>>>` 표시를 **직접 지우고**, 최종적으로 남길 코드만 손으로 정리
2. 살릴 코드 확정 후 저장
3. ```bash
   git add <충돌났던파일>
   git commit            # 충돌 해결 커밋 (메시지 자동 입력됨, 그대로 저장)
   ```
4. 헷갈리면 **반드시 팀에 물어보세요.** 잘못 합치면 코드가 날아갑니다.

> 💡 VS Code는 충돌 부분에 "Accept Current / Incoming / Both" 버튼을 띄워줍니다. 그걸 써도 됩니다.

---

## 8. 자주 하는 실수 & 되돌리기

| 상황 | 해결 |
|------|------|
| 커밋 메시지 오타 (아직 push 전) | `git commit --amend -m "올바른 메시지"` |
| `add` 잘못함 (커밋 전) | `git restore --staged <파일>` |
| 파일 수정 통째로 되돌리기 (커밋 전) | `git restore <파일>` ⚠️ 변경 사라짐 |
| 방금 커밋 취소 (변경은 유지) | `git reset --soft HEAD~1` |
| `.env` 같은 거 실수로 커밋함 | 팀에 즉시 알림 + `git rm --cached .env` 후 다시 커밋 |
| 브랜치 잘못 만들어 작업함 | 당황 말고 팀에 공유, 같이 옮김 |

> ⚠️ `git reset --hard` 와 `git push -f` 는 **혼자 판단 금지.** 반드시 PM(모세종)/팀과 상의.

---

## 9. 절대 하면 안 되는 것 🚫

1. ❌ **`main`·`dev` 에 직접 push** → 항상 내 이름 브랜치 + PR(`dev`로)
2. ❌ `.env` / API 키 / 비밀번호 커밋 → `.gitignore` 확인, 실수 시 즉시 신고
3. ❌ 모델 가중치·영상·음성 등 **대용량 파일 커밋** (`.mp4`, `.safetensors` 등 — 이미 .gitignore 처리됨)
4. ❌ `git push -f` (강제 푸시) 를 공용 브랜치에
5. ❌ 남의 브랜치를 마음대로 머지/삭제
6. ❌ 커밋 메시지 `ㅁㄴㅇㄹ`, `최종최종`

---

## 10. 치트시트

```bash
# 최초 1회 — 내 브랜치 만들기 (영문 이름, dev에서 분기)
git checkout dev && git pull origin dev
git checkout -b 내이름 && git push -u origin 내이름   # 예: mosejong

# 매일 작업 시작 — 내 브랜치 + dev 최신 반영
git checkout 내이름
git merge dev

# 저장 & 올리기
git status
git add .
git commit -m "feat: 한 일 한 줄"
git push                              # 기능 하나 끝나면 → GitHub에서 PR (base: dev)

# 현재 상태 확인용 (자주!)
git status        # 변경 파일
git log --oneline # 커밋 히스토리
git branch        # 브랜치 목록
```

---

막히면 5분만 혼자 해보고 **바로 팀 채널에 질문하세요.** 에러 메시지는 전체 복사해서. 🙌
