# Streamlit Cloud 배포 가이드

이 앱을 클라우드에 배포해서 **누구나 URL로 접속**할 수 있게 만드는 절차.

---

## 사전 준비 (이미 완료된 것)

✅ `.gitignore` — secrets.toml 자동 제외
✅ `requirements.txt` — Python 의존성 정의
✅ `references/example_reports/` — AI 학습 예시 (private repo에 포함)
✅ Prompt caching + 6 examples — 비용 최적화

---

## 1단계: GitHub Private Repo 생성 (3분)

1. https://github.com/new 접속
2. **Repository name**: `antler-memo-v2` (원하는 이름)
3. **반드시 Private 선택** ⚠️ (sensitive 데이터 포함)
4. README, .gitignore 추가 옵션은 **체크 해제** (이미 있음)
5. **Create repository** 클릭

---

## 2단계: 로컬 코드 push (5분)

터미널에서:

```bash
cd ~/Desktop/antler-memo-v2

# Git 초기화
git init
git add .
git commit -m "Initial commit"

# GitHub 연결 (URL은 너의 repo 주소로 교체)
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/antler-memo-v2.git
git push -u origin main
```

GitHub 비밀번호 대신 **Personal Access Token** 필요할 수 있음:
- https://github.com/settings/tokens → Generate new token (classic)
- `repo` 권한 체크 → 토큰 복사 → 비밀번호 자리에 붙여넣기

---

## 3단계: Streamlit Cloud 가입 + 연결 (5분)

1. https://share.streamlit.io 접속
2. **Sign in with GitHub** 클릭 → 권한 허용
3. 우측 상단 **New app** 클릭
4. 입력:
   - **Repository**: `YOUR_USERNAME/antler-memo-v2`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. **Advanced settings** 확장:
   - **Python version**: 3.11
   - **Secrets**: 아래 1줄 붙여넣기
     ```toml
     ANTHROPIC_API_KEY = "sk-ant-api03-xxxxxxxxxxxxx"
     ```
     (너의 실제 API 키로 교체)
6. **Deploy** 클릭

---

## 4단계: 배포 완료 (2~3분 자동)

Streamlit이 자동으로:
- GitHub 코드 pull
- pip install
- streamlit run

완료되면 URL 받음:
- 예: `https://antler-memo-v2.streamlit.app`
- 또는 `https://YOUR_USERNAME-antler-memo-v2-xyz.streamlit.app`

---

## 5단계: 사내 공유

URL을 Slack/이메일로 공유:
> 🚀 Investment Memo 자동 생성 도구
> https://antler-memo-v2.streamlit.app
> CSV 4개 업로드 → 팀 선택 → 끝

---

## 코드 수정 후 자동 재배포

```bash
git add .
git commit -m "수정 내용"
git push
```

→ Streamlit Cloud가 자동 감지하고 1~2분 안에 새 버전 배포.

---

## 비용

- **Streamlit Cloud**: 무료 (Community plan)
- **Anthropic API**: 보고서당 ~$0.05~0.18 (캐싱 적중 시)
- **GitHub Private repo**: 무료

---

## 트러블슈팅

**"Module not found"**:
- `requirements.txt`에 누락된 패키지 → 추가 후 push

**"API key not found"**:
- Streamlit Cloud → 앱 설정 → Secrets에 `ANTHROPIC_API_KEY` 다시 확인

**보고서가 영문으로만 생성됨**:
- 사이드바 **보고서 언어**에서 한국어 선택

**5분 걸려요**:
- Streamlit Cloud 무료 플랜은 약간 느림. 정상.
