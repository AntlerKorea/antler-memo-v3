"""
app.py — Antler Investment Memo 자동 생성 웹 앱 (Streamlit)

사용법:
    cd ~/Desktop/antler-memo-v2
    streamlit run app.py

브라우저가 자동으로 열립니다 (http://localhost:8501).
사내망에서 다른 사람도 접속하려면:
    streamlit run app.py --server.address 0.0.0.0
    → http://[Mac mini IP]:8501

요구사항:
    pip install streamlit anthropic
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

# 우리 스크립트 import
sys.path.insert(0, str(Path(__file__).parent))
from modules.generate import extract_team_data, generate_memo_content
from modules.render import render_memo

# ============================================================
# 페이지 설정
# ============================================================

st.set_page_config(
    page_title="Antler IC Memo Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Antler 브랜드 CSS (Residency Dashboard 스타일)
# ============================================================

ANTLER_CSS = """
<style>
/* Pretendard 폰트 import */
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

/* 앱 전체 배경/폰트 */
html, body, [class*="css"] {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.stApp {
    background-color: #FAFAFA;
}

/* Streamlit 기본 헤더/메뉴/푸터 숨김 */
#MainMenu, header[data-testid="stHeader"], footer {
    visibility: hidden;
    height: 0;
}

/* 메인 컨테이너 padding 조정 */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1100px !important;
}

/* === 사이드바 === */
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E5E7EB;
}

[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}

/* 사이드바 헤더 (로고 영역) */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 0 16px 0;
    border-bottom: 1px solid #F3F4F6;
    margin-bottom: 16px;
}
.sidebar-brand-logo {
    width: 32px; height: 32px;
    background: #1A1A1A;
    color: #F56565;
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 18px;
    font-family: 'Pretendard', sans-serif;
}
.sidebar-brand-text {
    font-size: 14px; font-weight: 700; color: #111827; line-height: 1.2;
}
.sidebar-brand-subtext {
    font-size: 11px; color: #6B7280; line-height: 1.2;
}

.sidebar-greeting {
    background: #F9FAFB;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #111827;
    line-height: 1.5;
}

.sidebar-section-label {
    font-size: 11px;
    text-transform: uppercase;
    color: #9CA3AF;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin: 12px 0 6px 0;
    padding-left: 4px;
}

/* === 메인 헤더 === */
.main-header {
    margin-bottom: 28px;
}
.main-title {
    font-size: 32px;
    font-weight: 800;
    color: #111827;
    line-height: 1.2;
    margin-bottom: 4px;
    letter-spacing: -0.02em;
}
.main-subtitle {
    font-size: 15px;
    color: #6B7280;
    font-weight: 400;
}

/* === Notice 배너 (Bootcamp X Team Formation Open 스타일) === */
.notice-banner {
    background: linear-gradient(180deg, #FFF5F5 0%, #FFEEEE 100%);
    border: 1px solid #FECACA;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 24px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
}
.notice-icon {
    width: 40px; height: 40px;
    background: #FFE4E4;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
}
.notice-title {
    color: #F56565;
    font-weight: 700;
    font-size: 15px;
    margin-bottom: 2px;
}
.notice-desc {
    color: #6B7280;
    font-size: 13px;
}

/* === 카드 (스텝/액션 박스) === */
.step-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 14px;
    transition: border-color 0.15s, box-shadow 0.15s;
}

/* 메인 영역의 모든 블록 사이 간격을 14px로 균일화 */
.block-container [data-testid="stVerticalBlock"] > div {
    margin-bottom: 0 !important;
}
.block-container [data-testid="stFileUploader"],
.block-container .stSelectbox,
.block-container .stButton,
.block-container .team-empty-state,
.block-container .step-card {
    margin-bottom: 14px !important;
    margin-top: 0 !important;
}
/* Streamlit이 자동 추가하는 spacer 제거 */
.block-container [data-testid="stVerticalBlock"] > div > div > div[style*="gap"] {
    gap: 0 !important;
}
.step-card:hover {
    border-color: #D1D5DB;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.step-card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
}
.step-number {
    width: 28px; height: 28px;
    background: #F0FDF4;
    color: #059669;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700;
    font-size: 13px;
}
.step-title {
    font-size: 16px;
    font-weight: 700;
    color: #111827;
}
.step-desc {
    font-size: 13px;
    color: #6B7280;
    margin-bottom: 12px;
}

/* === 버튼 (Antler 레드 primary) === */
.stButton > button[kind="primary"], .stButton button[kind="primary"] {
    background: #F56565 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.15s !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: #EF4444 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245,101,101,0.3) !important;
}
.stButton > button[kind="primary"]:disabled {
    background: #FCA5A5 !important;
    cursor: not-allowed !important;
    transform: none !important;
}

/* secondary 버튼 */
.stButton > button:not([kind="primary"]) {
    background: #FFFFFF !important;
    color: #374151 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #D1D5DB !important;
    background: #F9FAFB !important;
}

/* === 다운로드 버튼 === */
.stDownloadButton > button {
    background: #F56565 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background: #EF4444 !important;
}

/* === Input/Selectbox === */
.stTextInput input, .stSelectbox > div > div, .stTextArea textarea {
    border-radius: 8px !important;
    border-color: #E5E7EB !important;
    font-size: 14px !important;
}
.stTextInput input:focus, .stSelectbox > div > div:focus-within {
    border-color: #F56565 !important;
    box-shadow: 0 0 0 1px #F56565 !important;
}

/* 메인 영역의 팀 선택 selectbox — 진한 회색 + 흰 글씨 드롭다운 */
.block-container .stSelectbox div[data-baseweb="select"] > div {
    background: #1F2937 !important;
    border: 1px solid #1F2937 !important;
    border-radius: 10px !important;
    min-height: 60px !important;
    height: auto !important;
    padding: 10px 18px !important;
    color: #FFFFFF !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
    display: flex !important;
    align-items: center !important;
}
.block-container .stSelectbox div[data-baseweb="select"] > div *,
.block-container .stSelectbox div[data-baseweb="select"] > div span,
.block-container .stSelectbox div[data-baseweb="select"] > div input {
    color: #FFFFFF !important;
    font-size: 16px !important;
    line-height: 1.5 !important;
}
.block-container .stSelectbox div[data-baseweb="select"] [class*="valueContainer"],
.block-container .stSelectbox div[data-baseweb="select"] [class*="ValueContainer"] {
    padding: 0 !important;
    overflow: visible !important;
    line-height: 1.5 !important;
}
.block-container .stSelectbox div[data-baseweb="select"] > div:hover {
    background: #111827 !important;
    border-color: #111827 !important;
}
/* 드롭다운 화살표(chevron) 흰색으로 */
.block-container .stSelectbox div[data-baseweb="select"] svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
}
/* 사이드바 selectbox는 위 룰 영향 받지 않게 — 사이드바는 기본 사이즈 유지 */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    background: revert !important;
    border-style: solid !important;
    border-radius: 8px !important;
    min-height: revert !important;
    padding: revert !important;
}

/* 빈 상태 placeholder (파일 업로더와 동일한 스타일) */
.team-empty-state {
    display: flex;
    align-items: center;
    gap: 14px;
    background: #FAFAFA;
    border: 1px dashed #D1D5DB;
    border-radius: 10px;
    padding: 16px;
    margin-top: 8px;
}
.team-empty-state svg {
    flex-shrink: 0;
}
.team-empty-text {
    line-height: 1.4;
}
.team-empty-title {
    font-size: 14px;
    color: #6B7280;
    font-weight: 500;
}
.team-empty-sub {
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 2px;
}

/* === File uploader === */
[data-testid="stFileUploader"] {
    background: #FFFFFF;
}
[data-testid="stFileUploader"] section {
    border: 1px dashed #D1D5DB !important;
    border-radius: 10px !important;
    background: #FAFAFA !important;
    padding: 16px !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #F56565 !important;
    background: #FFF5F5 !important;
}
/* dropzone 안의 안내 문구 — 검정 톤 강제 */
[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small,
[data-testid="stFileUploader"] section div {
    color: #374151 !important;
}

/* Browse files 버튼 — 검정 배경 + 흰 글씨 강제 */
[data-testid="stFileUploader"] section button,
[data-testid="stFileUploader"] section button *,
[data-testid="stFileUploader"] section button p,
[data-testid="stFileUploader"] section button span {
    color: #FFFFFF !important;
    background-color: #1A1A1A !important;
}
[data-testid="stFileUploader"] section button:hover,
[data-testid="stFileUploader"] section button:hover * {
    background-color: #000000 !important;
    color: #FFFFFF !important;
}

/* 업로드된 파일 리스트 — 흰색 폰트 문제 해결 */
[data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"],
[data-testid="stFileUploaderFile"],
[data-testid="stFileUploaderFile"] * {
    color: #111827 !important;
}
[data-testid="stFileUploaderFile"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    margin-top: 8px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
[data-testid="stFileUploaderFile"] small {
    color: #6B7280 !important;
    font-size: 11px !important;
}

/* 삭제(X) 버튼 — 잘 보이게 */
[data-testid="stFileUploaderDeleteBtn"],
[data-testid="stFileUploaderFile"] button {
    background: transparent !important;
    border: none !important;
    color: #6B7280 !important;
    border-radius: 6px !important;
    cursor: pointer !important;
}
[data-testid="stFileUploaderDeleteBtn"]:hover,
[data-testid="stFileUploaderFile"] button:hover {
    background: #FEE2E2 !important;
    color: #DC2626 !important;
}
[data-testid="stFileUploaderDeleteBtn"] svg,
[data-testid="stFileUploaderFile"] button svg {
    fill: currentColor !important;
    width: 16px !important;
    height: 16px !important;
}
/* 파일명 — 어떤 selector든 검정으로 (Streamlit 버전 차이 대응) */
.uploadedFile, .uploadedFile *,
[data-testid="stFileUploaderFileName"],
[data-testid="stFileUploaderFileData"],
[data-testid="stFileUploaderFileData"] * {
    color: #111827 !important;
}
/* 파일 사이즈 (작은 글자) — 회색 */
[data-testid="stFileUploaderFileData"] small,
[data-testid="stFileUploaderFileData"] span:not(:first-child) {
    color: #6B7280 !important;
}

/* === Progress bar === */
.stProgress > div > div {
    background-color: #F56565 !important;
}

/* === Alert 박스 === */
.stAlert {
    border-radius: 10px !important;
    border: 1px solid !important;
    padding: 12px 16px !important;
}
[data-baseweb="notification"][kind="success"], div[data-testid="stAlert-success"] {
    background: #F0FDF4 !important;
    border-color: #BBF7D0 !important;
}
[data-baseweb="notification"][kind="warning"], div[data-testid="stAlert-warning"] {
    background: #FFFBEB !important;
    border-color: #FCD34D !important;
}

/* === Metric 카드 === */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    color: #6B7280 !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="stMetricValue"] {
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #111827 !important;
}

/* === Divider === */
hr {
    border: none !important;
    border-top: 1px solid #F3F4F6 !important;
    margin: 24px 0 !important;
}

/* === Caption === */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #9CA3AF !important;
    font-size: 12px !important;
}

/* === Expander === */
.streamlit-expanderHeader {
    background: #F9FAFB !important;
    border-radius: 8px !important;
    border: 1px solid #E5E7EB !important;
    font-weight: 500 !important;
}

/* 사이드바 푸터 (사용자 정보) */
.sidebar-footer {
    padding: 12px;
    background: #F9FAFB;
    border-radius: 8px;
    margin-top: 16px;
    font-size: 12px;
    color: #6B7280;
}

/* 사이드바 모든 입력 위젯 라벨 — 검정색 강제 */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] label span,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #111827 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

/* 라디오 옵션 라벨 (English / 한국어) */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label,
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
    color: #111827 !important;
    font-weight: 400 !important;
}

/* 사이드바 드롭다운 선택값 — 검정색 강제 (안 보이는 문제 해결) */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div *,
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] [class*="valueContainer"],
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] [class*="valueContainer"] * {
    color: #111827 !important;
}
</style>
"""

st.markdown(ANTLER_CSS, unsafe_allow_html=True)

# ============================================================
# 사이드바 — Antler 브랜드 + 설정
# ============================================================

with st.sidebar:
    # API 키 — secrets.toml 또는 환경변수에서 자동 로드 (UI 숨김)
    api_key = ""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # Claude 모델 (기본 고정)
    model = "claude-sonnet-4-5"

    # 기수 선택
    cohort = st.selectbox(
        "기수 선택",
        ["KOR8", "KOR7", "KOR6", "KOR5", "KOR4"],
        index=0,
    )

    # 프로그램 타입
    program_type = st.selectbox(
        "타입",
        ["Residency", "Fast track", "Forge"],
        index=0,
    )

    # 작성자 선택
    author = st.selectbox(
        "작성자",
        ["Jiho Kang", "JaeHee Chang", "Gabriel Jung", "Roy Jang", "기타"],
        index=0,
    )
    if author == "기타":
        author = st.text_input("작성자 이름", placeholder="이름 입력", label_visibility="collapsed")

    # 언어: 영어 고정 (UI 제거)
    language = "english"

    # 옵션 (UI 숨김 — 항상 활성화)
    auto_chart = True
    auto_photos = True

    # API 키가 없으면 안내
    if not api_key:
        st.warning("⚠️ secrets.toml 에 API 키 설정 필요")

    # === 푸터 ===
    st.markdown(
        """
        <div class="sidebar-footer">
            <b>v2.0</b> — Powered by Claude API<br>
            <span style="font-size:10px;color:#9CA3AF;">© 2026 Antler Korea</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# 메인 헤더
# ============================================================

st.markdown(
    """
    <div class="main-header">
        <div class="main-title">Investment Memo Generator</div>
        <div class="main-subtitle">Antler Korea Cohort 8 · DD 자료 자동 생성 도구</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# Step 1: CSV 업로드
# ============================================================

st.markdown(
    """
    <div class="step-card">
        <div class="step-card-header">
            <div class="step-number">1</div>
            <div class="step-title">파일 업로드</div>
        </div>
        <div class="step-desc">관련 파일을 모두 한 번에 올리세요 (CSV, PDF, PPTX 등 — 파일명으로 자동 분류).</div>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Drag & drop 또는 클릭해서 선택",
    accept_multiple_files=True,
    type=None,  # 모든 파일 형식 허용
    label_visibility="collapsed",
    key="all_files",
)

# 업로드된 파일 자동 분류
def classify_file(filename: str) -> str:
    """파일명으로 카테고리 자동 분류."""
    name = filename.lower()
    if "dd_survey_comments" in name:
        return "dd_survey_comments"
    if "dd_survey" in name:
        return "dd_survey"
    if "founders" in name:
        return "founders"
    if "team_formation" in name:
        return "team_formation"
    if "retro" in name:
        return "retro_responses"
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith(".pptx"):
        return "pptx"
    return "other"

# 분류 결과 표시
classified = {}
dd_survey_file = None
founders_file = None
team_form_file = None
retro_file = None

if uploaded_files:
    for f in uploaded_files:
        cat = classify_file(f.name)
        classified.setdefault(cat, []).append(f)

    # 메인 파일 변수에 매핑
    if "dd_survey" in classified:
        dd_survey_file = classified["dd_survey"][0]
    if "founders" in classified:
        founders_file = classified["founders"][0]
    if "team_formation" in classified:
        team_form_file = classified["team_formation"][0]
    if "retro_responses" in classified:
        retro_file = classified["retro_responses"][0]

    # 인식 결과 요약 (아이콘·마크다운 없이 깔끔하게)
    label_map = {
        "dd_survey": "DD Survey",
        "founders": "Founders",
        "team_formation": "Team Formation",
        "retro_responses": "Retro",
        "dd_survey_comments": "DD Comments",
        "pdf": "PDF",
        "pptx": "Presentation",
        "other": "기타",
    }
    summary_parts = []
    for cat, files in classified.items():
        label = label_map.get(cat, cat)
        summary_parts.append(f"<span style='font-weight:600'>{label}</span> × {len(files)}")

    st.markdown(
        f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;'
        f'padding:12px 16px;margin-top:8px;font-size:13px;color:#065F46;">'
        f'{len(uploaded_files)}개 파일 인식됨 — ' + "  ·  ".join(summary_parts) +
        '</div>',
        unsafe_allow_html=True,
    )

    if "dd_survey" not in classified:
        st.warning("⚠️ DD Survey CSV가 없어요 (필수). 파일명에 `dd_survey`가 포함돼야 인식됩니다.")

# ============================================================
# Step 2: 팀 선택
# ============================================================

st.markdown(
    """
    <div class="step-card">
        <div class="step-card-header">
            <div class="step-number">2</div>
            <div class="step-title">팀 선택</div>
        </div>
        <div class="step-desc">보고서를 만들 기업을 선택하세요.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# CSV에서 팀 목록 자동 추출
team_list = []
if dd_survey_file:
    import csv
    import io

    dd_survey_file.seek(0)
    content = dd_survey_file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    teams = set()
    for row in reader:
        team = row.get("team_name", "").strip()
        if team:
            teams.add(team)
    team_list = sorted(teams, key=str.lower)
    dd_survey_file.seek(0)

if team_list:
    team_name = st.selectbox(
        f"보고서를 만들 팀 ({len(team_list)}개 발견)",
        team_list,
        help="DD Survey에서 자동 추출",
        label_visibility="collapsed",
        key="team_select_active",
    )
else:
    # 파일 업로더와 동일한 스타일의 placeholder
    st.markdown(
        '<div class="team-empty-state">'
        '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" '
        'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '</svg>'
        '<div class="team-empty-text">'
        '<div class="team-empty-title">자료를 먼저 업로드하세요</div>'
        '<div class="team-empty-sub">파일 업로드 후 팀 목록이 자동으로 표시됩니다</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    team_name = ""

# ============================================================
# Step 3: 생성
# ============================================================

# 타입 검증 — Fast track/Forge는 아직 미지원
type_supported = (program_type == "Residency")
if not type_supported:
    st.markdown(
        f'<div style="background:#FFFBEB;border:1px solid #FCD34D;border-radius:10px;'
        f'padding:14px 18px;margin-bottom:12px;color:#92400E;font-size:13px;">'
        f'🚧 <b>{program_type}</b> 템플릿은 아직 서비스 준비 중입니다. '
        f'현재는 <b>Residency</b>만 지원돼요.'
        f'</div>',
        unsafe_allow_html=True,
    )

# 사전 검증 (경고 배너 없이 버튼 disabled로만 표시)
ready = bool(dd_survey_file and team_name and api_key and type_supported)

generate_btn = st.button(
    "✨ 보고서 생성 시작",
    type="primary",
    disabled=not ready,
    use_container_width=True,
)

# ============================================================
# Step 4: 생성 실행
# ============================================================

if generate_btn:
    base_dir = Path(__file__).parent

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_files_saved = {}
        for label, file_obj in [
            ("dd_survey-export.csv", dd_survey_file),
            ("founders-export.csv", founders_file),
            ("team_formation-export.csv", team_form_file),
            ("retro_responses-export.csv", retro_file),
        ]:
            if file_obj:
                p = os.path.join(tmp_dir, label)
                with open(p, "wb") as f:
                    f.write(file_obj.getvalue())
                csv_files_saved[label] = p

        try:
            with st.spinner("보고서를 만드는 중..."):
                # CSV 데이터 추출
                team_data = extract_team_data(tmp_dir, team_name)
                if not team_data["dd_survey"]:
                    st.error(f"❌ DD Survey에서 '{team_name}' 못 찾음")
                    st.stop()

                # 팀원 수 자동 감지 (CSV에서)
                import json as _json
                try:
                    members_raw = team_data["dd_survey"].get("team_members", "[]")
                    detected_members = _json.loads(members_raw)
                    team_size = len([m for m in detected_members if m.get("name") or m.get("role")])
                    team_size = max(1, min(3, team_size))
                except Exception:
                    team_size = 2

                # AI 콘텐츠 생성
                content = generate_memo_content(
                    team_name=team_name,
                    csv_dir=tmp_dir,
                    api_key=api_key,
                    model=model,
                    language=language,
                    team_size=team_size,
                    verbose=False,
                )
                # 사용자 선택값 강제 주입
                content["COHORT"] = cohort
                # 사용 안 되는 founder 슬롯은 빈 문자열로 강제
                for i in range(team_size + 1, 4):
                    content[f"FOUNDER_{i}_HEADING"] = ""
                    content[f"FOUNDER_{i}_BG_1"] = ""
                    content[f"FOUNDER_{i}_BG_2"] = ""
                    content[f"FOUNDER_{i}_BG_3"] = ""

                # PPTX 렌더링
                final_filename = f"[{cohort}] Investment Memo_{team_name}_{author}.pptx"
                output_path = os.path.join(tmp_dir, final_filename)

                # photos 폴더 자동 연결
                photos_dir = str(base_dir / "photos")
                if not os.path.exists(photos_dir):
                    photos_dir = None

                result = render_memo(
                    template_path=str(base_dir / "templates" / "DD_Template_2person.pptx"),
                    content_json=content,
                    output_path=output_path,
                    founders_csv=csv_files_saved.get("founders-export.csv") if auto_photos else None,
                    photos_dir=photos_dir,
                    auto_generate_chart=auto_chart,
                    verbose=False,
                )

            # 결과 — 다운로드 버튼만
            st.success(f"🎉 보고서 생성 완료!")

            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"📥 {final_filename} 다운로드",
                    data=f.read(),
                    file_name=final_filename,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    type="primary",
                    use_container_width=True,
                )

        except Exception as e:
            import traceback

            st.error(f"❌ 에러: {e}")
            with st.expander("자세한 에러 정보"):
                st.code(traceback.format_exc())

# ============================================================
# 푸터
# ============================================================

st.markdown(
    """
    <div style="text-align:center;padding:32px 0 16px;color:#9CA3AF;font-size:12px;">
        14개 완성본 + structure_rules.md 기반으로 학습된 AI가 자동 생성합니다.<br>
        결과물은 IC 제출 전 반드시 사람이 검토하세요.
    </div>
    """,
    unsafe_allow_html=True,
)
