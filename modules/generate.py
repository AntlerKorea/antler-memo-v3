"""
generate.py — Antler Investment Memo 자동 콘텐츠 생성

Anthropic Claude API + Tool Use + Few-shot prompting으로
14개 완성본 패턴을 학습하여 placeholder JSON을 자동 생성한다.

안전장치:
  1. Few-shot prompting — 14개 example_reports를 system prompt에 주입
  2. Tool use — 강제 schema (placeholder 키 + 타입 + 영문 검증)
  3. Auto checklist — 영문/출처/DD critical 자동 검증

사용법 (CLI):
    python generate.py \\
        --team "handa" \\
        --csv-dir /path/to/csvs \\
        --output examples/handa_content.json \\
        [--strict]   # 안전장치 4 (슬라이드별) 활성화

사용법 (Python):
    from generate import generate_memo_content
    content = generate_memo_content(
        team_name="handa",
        csv_dir="/path/to/csvs",
        strict_mode=False,
    )

환경변수:
    ANTHROPIC_API_KEY — Claude API 키 (필수)

의존성:
    pip install anthropic
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys
from modules.facts import build_team_facts, format_facts_for_prompt
from pathlib import Path


# ============================================================
# 데이터 추출 (extract.py 기능 통합)
# ============================================================


def extract_team_data(csv_dir: str, team_name: str) -> dict:
    """4종 CSV에서 팀 데이터를 추출한다.

    Args:
        csv_dir: CSV 파일들이 있는 폴더
        team_name: 팀 이름 (대소문자 무시 매칭)

    Returns:
        {
            "dd_survey": {...},  # 가장 최신 레코드
            "dd_survey_history": [...],  # 모든 세션 레코드
            "founders": [...],
            "team_formation": [...],  # session_label 시간순 정렬
            "team_changes": [...],  # 멤버 변화 추적
            "retro_responses": [...],
        }
    """
    data = {
        "dd_survey": None,
        "dd_survey_history": [],
        "founders": [],
        "team_formation": [],
        "team_changes": [],
        "retro_responses": [],
    }

    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    team_lower = team_name.lower()

    for csv_file in csv_files:
        filename = os.path.basename(csv_file).lower()

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    # 팀 매칭: team_name 컬럼 정확 매칭만 (대소문자 무시)
                    # 이전엔 substring fallback 있었으나 오매칭 발생해서 제거
                    # (예: "Loop"가 INSUPIRE retro 텍스트에 등장해서 그 팀 데이터까지 끌려옴)
                    team_field = row.get("team_name", "").strip().lower()
                    if team_field != team_lower:
                        continue

                    if "dd_survey-export" in filename:
                        data["dd_survey_history"].append(dict(row))
                        if data["dd_survey"] is None or row.get("updated_at", "") > data["dd_survey"].get("updated_at", ""):
                            data["dd_survey"] = dict(row)
                    elif "founders-export" in filename:
                        data["founders"].append(dict(row))
                    elif "team_formation" in filename:
                        data["team_formation"].append(dict(row))
                    elif "retro_responses" in filename:
                        data["retro_responses"].append(dict(row))
        except Exception as e:
            print(f"⚠️  CSV 읽기 실패: {csv_file} — {e}", file=sys.stderr)
            continue

    # team_formation을 session_label 시간순 정렬
    session_order = {
        "Bootcamp 1": 1, "Bootcamp 2": 2, "Bootcamp 3-1": 3, "Bootcamp 3-2": 4,
        "Bootcamp 4": 5, "Bootcamp 5": 6, "Bootcamp 6": 7,
        "Group Office Hour": 8, "Trackout Only": 9, "trackout": 10,
    }
    data["team_formation"].sort(key=lambda r: session_order.get(r.get("session_label", ""), 99))

    # 팀 변화 추적
    prev_members = set()
    for row in data["team_formation"]:
        session = row.get("session_label", "")
        members = {row.get(f"member_{i}", "").strip() for i in range(1, 5) if row.get(f"member_{i}", "").strip()}
        if prev_members and members != prev_members:
            added = members - prev_members
            removed = prev_members - members
            change = {"session": session, "added": list(added), "removed": list(removed), "current_members": list(members)}
            data["team_changes"].append(change)
        prev_members = members

    return data


def parse_json_field(row: dict, field: str, default=None):
    """CSV의 JSON 필드를 안전하게 파싱한다."""
    raw = row.get(field, "")
    if not raw or raw == "[]" or raw == "{}":
        return default if default is not None else []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


# ============================================================
# Few-shot 예시 로드
# ============================================================


def load_example_reports(examples_dir: str, max_examples: int = 3) -> list:
    """references/example_reports/ 에서 완성본 로드.

    비용 + Rate limit 최적화: 14개 → 3개로 축소 (Tier 1 30K tokens/분 제한 대응).
    각 파트너(Jiho/JaeHee/Gabriel)별로 1개씩 균형 있게 추출.
    """
    all_examples = []
    for path in sorted(Path(examples_dir).glob("*.json")):
        if path.name == "INDEX.json":
            continue
        with open(path, "r", encoding="utf-8") as f:
            all_examples.append(json.load(f))

    if len(all_examples) <= max_examples:
        return all_examples

    # 파트너별로 균형 있게 선택
    by_partner = {}
    for ex in all_examples:
        p = ex.get("partner", "unknown")
        by_partner.setdefault(p, []).append(ex)

    selected = []
    while len(selected) < max_examples and any(by_partner.values()):
        for p in list(by_partner.keys()):
            if by_partner[p] and len(selected) < max_examples:
                selected.append(by_partner[p].pop(0))
    return selected


# ============================================================
# Tool Use Schema (강제 placeholder 구조)
# ============================================================


PLACEHOLDER_SCHEMA = {
    "type": "object",
    "properties": {
        # Slide 1
        "COMPANY_NAME": {"type": "string", "description": "Team/company name (15 chars)"},
        "ONELINER": {"type": "string", "description": "English one-liner. Pattern: 'AI [function] for [market]' (~50 chars)"},
        "COHORT": {"type": "string", "description": "Cohort label, e.g., 'KOR8'"},
        # Slide 2
        "PROBLEM_1": {"type": "string", "description": "English. Customer pain with statistic (~100 chars)"},
        "PROBLEM_2": {"type": "string", "description": "English. Limitation of current alternatives (~100 chars)"},
        "PROBLEM_3": {"type": "string", "description": "English. Resulting inefficiency or risk (~100 chars)"},
        "SOLUTION_1": {"type": "string", "description": "English. Core mechanism (~95 chars)"},
        "SOLUTION_2": {"type": "string", "description": "English. Technical/feature differentiation (~95 chars)"},
        "SOLUTION_3": {"type": "string", "description": "English. Integrated value (~95 chars)"},
        "VALUE_1": {"type": "string", "description": "English. Quantified value 1 (~70 chars)"},
        "VALUE_2": {"type": "string", "description": "English. Quantified value 2 (~70 chars)"},
        "VALUE_3": {"type": "string", "description": "English. Quantified value 3 (~70 chars)"},
        # Slide 3
        "TAM_AMOUNT": {"type": "string", "description": "TAM in $XB or $XM format (~5 chars)"},
        "TAM_DESC": {"type": "string", "description": "English. TAM definition (~40 chars)"},
        "TAM_RATIONALE": {"type": "string", "description": "English. Source + breakdown (~140 chars)"},
        "SAM_AMOUNT": {"type": "string"},
        "SAM_DESC": {"type": "string"},
        "SAM_RATIONALE": {"type": "string"},
        "SOM_AMOUNT": {"type": "string", "description": "SOM = company-capturable revenue, NOT market pool size"},
        "SOM_DESC": {"type": "string"},
        "SOM_RATIONALE": {"type": "string", "description": "Must include arithmetic: e.g., '500 leads × $1,497 ACV'"},
        "WHY_KOREA": {"type": "string", "description": "STRICT MAX 90 chars. English. ONE concise sentence. Box overflows beyond this length."},
        "WHY_NOW": {"type": "string", "description": "STRICT MAX 90 chars. English. ONE concise sentence. Box overflows beyond this length."},
        "WHY_GLOBAL": {"type": "string", "description": "STRICT MAX 90 chars. English. ONE concise sentence. Box overflows beyond this length."},
        # Slide 4 — Competition
        "COMP1_NAME": {"type": "string"},
        "COMP1_COUNTRY": {"type": "string", "description": "Country code or full name"},
        "COMP1_FUNDING": {"type": "string", "description": "Format: 'Stage / Year' e.g., 'Series B / 2010'"},
        "COMP1_DESC": {"type": "string", "description": "English. Strength + our advantage (~55 chars)"},
        "COMP2_NAME": {"type": "string"},
        "COMP2_COUNTRY": {"type": "string"},
        "COMP2_FUNDING": {"type": "string"},
        "COMP2_DESC": {"type": "string"},
        "COMP3_NAME": {"type": "string"},
        "COMP3_COUNTRY": {"type": "string"},
        "COMP3_FUNDING": {"type": "string"},
        "COMP3_DESC": {"type": "string"},
        "COMP4_NAME": {"type": "string"},
        "COMP4_COUNTRY": {"type": "string"},
        "COMP4_FUNDING": {"type": "string"},
        "COMP4_DESC": {"type": "string"},
        "DIFF_1": {"type": "string", "description": "English. Concrete differentiator (~100 chars)"},
        "DIFF_2": {"type": "string"},
        "DIFF_3": {"type": "string"},
        "DIFF_4": {"type": "string"},
        # Slide 5
        "GTM_1": {"type": "string", "description": "English. Stage 1 GTM"},
        "GTM_2": {"type": "string", "description": "English. Stage 2 GTM"},
        "GTM_3": {"type": "string", "description": "English. Stage 3 GTM"},
        "PRICING_1": {"type": "string", "description": "English. Price structure with comparison"},
        "PRICING_2": {"type": "string", "description": "English. ACV explicit"},
        "BM_1": {"type": "string", "description": "English. Revenue model"},
        "BM_2": {"type": "string", "description": "English. Unit economics"},
        "SCALE_1": {"type": "string", "description": "English. Specific scale lever 1"},
        "SCALE_2": {"type": "string"},
        "SCALE_3": {"type": "string"},
        # Slide 6
        "WHY_TEAM_1": {"type": "string", "description": "English. Founder-problem fit narrative"},
        "WHY_TEAM_2": {"type": "string"},
        "WHY_TEAM_3": {"type": "string"},
        "FOUNDER_1_HEADING": {"type": "string", "description": "Format: '[Name] ([Role])'"},
        "FOUNDER_1_BG_1": {"type": "string", "description": "STRICT MAX 50 chars. One concise bullet. English. Past role/credential or key achievement"},
        "FOUNDER_1_BG_2": {"type": "string"},
        "FOUNDER_1_BG_3": {"type": "string"},
        "FOUNDER_2_HEADING": {"type": "string"},
        "FOUNDER_2_BG_1": {"type": "string"},
        "FOUNDER_2_BG_2": {"type": "string"},
        "FOUNDER_2_BG_3": {"type": "string"},
        # Slide 7 — Program Trajectory (must include partner signals)
        "STAGE_1_DESC": {"type": "string", "description": "English. Program start status"},
        "STAGE_2_DESC": {"type": "string", "description": "English. Team building"},
        "STAGE_3_DESC": {"type": "string"},
        "STAGE_4_DESC": {"type": "string", "description": "English. Must include Bootcamp signal + partner name"},
        "STAGE_5_DESC": {"type": "string", "description": "English. Bootcamp score from partner"},
        "STAGE_6_DESC": {"type": "string", "description": "English. Trackout + IC sponsor"},
        "STAGE_7_DESC": {"type": "string", "description": "English. Post-trackout latest traction"},
        # Slide 8 — Evaluation (1-5 scores)
        "SCORE_1": {"type": "string", "description": "Score for Team Cohesion (1-5 integer). MUST evaluate ONLY this specific dimension."},
        "RATIONALE_1": {"type": "string", "description": "Rationale for Team Cohesion score. STRICT: must discuss ONLY Team Cohesion aspects, NOT other categories. Max 130 chars."},
        "SCORE_2": {"type": "string", "description": "Score for Execution (1-5 integer). MUST evaluate ONLY this specific dimension."},
        "RATIONALE_2": {"type": "string", "description": "Rationale for Execution score. STRICT: must discuss ONLY Execution aspects, NOT other categories. Max 130 chars."},
        "SCORE_3": {"type": "string", "description": "Score for Resilience (1-5 integer). MUST evaluate ONLY this specific dimension."},
        "RATIONALE_3": {"type": "string", "description": "Rationale for Resilience score. STRICT: must discuss ONLY Resilience aspects, NOT other categories. Max 130 chars."},
        "SCORE_4": {"type": "string", "description": "Score for Market Understanding (1-5 integer). MUST evaluate ONLY this specific dimension."},
        "RATIONALE_4": {"type": "string", "description": "Rationale for Market Understanding score. STRICT: must discuss ONLY Market Understanding aspects, NOT other categories. Max 130 chars."},
        "SCORE_5": {"type": "string", "description": "Score for Technology (1-5 integer). MUST evaluate ONLY this specific dimension."},
        "RATIONALE_5": {"type": "string", "description": "Rationale for Technology score. STRICT: must discuss ONLY Technology aspects, NOT other categories. Max 130 chars."},
        "SCORE_6": {"type": "string", "description": "Score for Innovation (1-5 integer). MUST evaluate ONLY this specific dimension."},
        "RATIONALE_6": {"type": "string", "description": "Rationale for Innovation score. STRICT: must discuss ONLY Innovation aspects, NOT other categories. Max 130 chars."},
        # Slide 9 — Strengths/Improvements
        "STRENGTH_1": {"type": "string", "description": "Title (~25 chars)"},
        "STRENGTH_1_DESC": {"type": "string", "description": "English. ~120 chars with specifics"},
        "STRENGTH_2": {"type": "string"},
        "STRENGTH_2_DESC": {"type": "string"},
        "STRENGTH_3": {"type": "string"},
        "STRENGTH_3_DESC": {"type": "string"},
        "STRENGTH_4": {"type": "string"},
        "STRENGTH_4_DESC": {"type": "string"},
        "IMPROVEMENT_1": {"type": "string"},
        "IMPROVEMENT_1_DESC": {"type": "string"},
        "IMPROVEMENT_2": {"type": "string"},
        "IMPROVEMENT_2_DESC": {"type": "string"},
        "IMPROVEMENT_3": {"type": "string"},
        "IMPROVEMENT_3_DESC": {"type": "string"},
        "IMPROVEMENT_4": {"type": "string"},
        "IMPROVEMENT_4_DESC": {"type": "string"},
        "FOUNDER_EQUITY": {"type": "string", "description": "English. Equity structure + status"},
        # Slide 10 — Investor Assessment
        "SUMMARY_DESC": {"type": "string", "description": "English. 1-2 sentences synthesizing the bet"},
        "RISKS_DESC": {"type": "string", "description": "English. Key risks summary"},
    },
    "required": ["COMPANY_NAME", "ONELINER", "COHORT"],
}


# ============================================================
# 메인 생성 함수
# ============================================================


def build_system_prompt(
    rules_path: str,
    examples: list,
    language: str = "english",
) -> str:
    """System prompt 구성: structure_rules + 14 examples + 언어 모드.

    Args:
        language: "english" (기본) 또는 "korean"
    """
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = f.read()

    # 14 examples를 압축된 형태로 포함
    examples_text = "\n\n".join([
        f"=== EXAMPLE: {ex['team_name']} (by {ex['partner']}) ===\n"
        + json.dumps(ex["slides"], ensure_ascii=False, indent=2)
        for ex in examples
    ])

    # 언어 모드별 지침
    if language == "korean":
        language_directive = """
# OUTPUT LANGUAGE: KOREAN (한국어 음슴체)

ALL content MUST be written in **Korean using 음슴체** style:
- "~합니다" → "~함"
- "~입니다" → "~임"
- "~됩니다" → "~됨"
- "~있습니다" → "~있음"
- Examples: "성장하고 있음", "검증되었음", "확보 가능함", "제한적임"

EXCEPTIONS (keep in English/original):
- Company names (proper nouns): "InBody", "Songtrust"
- Technical terms when commonly used in English: "AI", "API", "MVP", "GTM", "TAM/SAM/SOM"
- Founder names: "Daniel Kim", "Matt McLuckie"
- Dollar amounts and units: "$13.6B", "5%"

The 14 reference examples below are mostly in English — use them for STRUCTURE and DEPTH,
but write the actual output in Korean 음슴체 as described above.
"""
    else:
        language_directive = """
# OUTPUT LANGUAGE: ENGLISH

ALL content MUST be in English (except proper nouns like company/founder names).
"""

    return f"""You are a senior Antler Korea investment partner writing an Investment Memo (DD report) for an Antler portfolio team.

# YOUR ROLE
- Apply DD critical analysis (challenge founder claims, verify arithmetic)
- Write in the established Antler IC report style
- Match the quality of senior partners (Jiho, JaeHee, Gabriel)

{language_directive}

# STRUCTURE RULES (MUST FOLLOW)

{rules}

# 14 REFERENCE EXAMPLES (your gold standard)

{examples_text}

# YOUR TASK

Generate a complete Investment Memo content as a JSON object using the `submit_memo_content` tool.

CRITICAL REQUIREMENTS:
1. SOM = company-capturable revenue, NOT market pool size
2. Every dollar amount must cite a source
3. Challenge founder claims with arithmetic verification
4. Slide 7 STAGE descriptions MUST include Bootcamp signals + partner names + scores
5. Track team changes (members joining/leaving) from team_formation history
6. Slide 9 IMPROVEMENT items must be honest and specific (not generic)
7. Match the depth and skepticism shown in the JaeHee handa example
"""


def auto_checklist(content: dict, language: str = "english"):
    """안전장치 3: 자동 체크리스트.

    Args:
        language: "english" 또는 "korean" — 검증 방향 결정

    Returns:
        (통과 여부, 실패 항목 리스트)
    """
    issues = []

    # 1. 언어 검증 (모드별 반대 방향)
    long_text_fields = [
        "PROBLEM_1", "SOLUTION_1", "VALUE_1", "WHY_KOREA", "WHY_NOW",
        "DIFF_1", "GTM_1", "WHY_TEAM_1", "STAGE_4_DESC", "SUMMARY_DESC",
    ]
    for field in long_text_fields:
        text = content.get(field, "")
        if not text:
            continue
        korean_chars = sum(1 for c in text if "가" <= c <= "힣")
        total_chars = len(text)
        if total_chars == 0:
            continue
        ratio = korean_chars / total_chars
        if language == "english" and ratio > 0.3:
            issues.append(f"❌ {field}: 한국어 비율 너무 높음 ({korean_chars}/{total_chars})")
        elif language == "korean" and ratio < 0.2 and total_chars > 30:
            # 한국어 모드인데 한국어가 거의 없으면 NG
            issues.append(f"❌ {field}: 한국어 비율 너무 낮음 — 음슴체로 다시 작성 필요")

    # 2. 출처 명기 검증 (긴 rationale 필드)
    rationale_fields = ["TAM_RATIONALE", "SAM_RATIONALE", "SOM_RATIONALE"]
    source_keywords = ["McKinsey", "Bain", "BCG", "Goldman", "Morgan", "CISAC", "MLC", "IFPI", "RIAA",
                       "Statista", "Mordor", "통계청", "KDI", "Crunchbase", "PitchBook", "Euromonitor",
                       "Gartner", "IDC", "Forrester", "$", "%"]
    for field in rationale_fields:
        text = content.get(field, "")
        if text and not any(kw.lower() in text.lower() for kw in source_keywords):
            issues.append(f"⚠️  {field}: 출처/수치 부재")

    # 3. SOM 정의 검증 (시장 풀 사이즈 표현 의심)
    som_text = content.get("SOM_DESC", "") + " " + content.get("SOM_RATIONALE", "")
    if som_text and any(kw in som_text.lower() for kw in ["market pool", "전체 시장", "total addressable"]):
        issues.append("⚠️  SOM이 시장 풀 사이즈로 표현됨 — capturable revenue로 수정 필요")

    # 4. Slide 7 — 파트너 시그널 검증
    stage_4_to_6 = " ".join([content.get(f"STAGE_{i}_DESC", "") for i in [4, 5, 6]])
    has_partner = any(p in stage_4_to_6 for p in ["Jiho", "Jaehee", "JaeHee", "Gabriel"])
    has_signal = any(s in stage_4_to_6.lower() for s in ["red", "green", "yellow", "score", "9/9", "/9"])
    if not has_partner:
        issues.append("⚠️  Slide 7: 파트너 이름 없음 (Jiho/JaeHee/Gabriel)")
    if not has_signal:
        issues.append("⚠️  Slide 7: Bootcamp 시그널/점수 없음")

    # 5. 필수 필드 존재
    required = ["COMPANY_NAME", "ONELINER"]
    for field in required:
        if not content.get(field, "").strip():
            issues.append(f"❌ 필수 필드 누락: {field}")

    return len(issues) == 0, issues


def generate_memo_content(
    team_name: str,
    csv_dir: str,
    rules_path: str = None,
    examples_dir: str = None,
    api_key: str = None,
    model: str = "claude-sonnet-4-5",
    strict_mode: bool = False,
    max_retries: int = 2,
    verbose: bool = True,
    language: str = "english",
    team_size: int = 2,
) -> dict:
    """메인 콘텐츠 생성 함수.

    Args:
        team_name: 팀 이름
        csv_dir: CSV 4종 폴더
        rules_path: structure_rules.md 경로 (기본값: ../references/structure_rules.md)
        examples_dir: example_reports/ 폴더 경로
        api_key: Anthropic API 키 (환경변수 ANTHROPIC_API_KEY 자동 사용)
        model: 사용할 Claude 모델
        strict_mode: 안전장치 4 (슬라이드별 단계 생성) 활성화
        max_retries: 체크리스트 실패 시 재시도 횟수
        verbose: 진행 상황 출력

    Returns:
        placeholder content 딕셔너리
    """
    # Anthropic SDK 임포트
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic 패키지 필요: pip install anthropic")

    # 기본 경로 설정
    # data/ 폴더 위치 (modules/ 한 단계 위)
    base_dir = Path(__file__).parent.parent
    if rules_path is None:
        rules_path = str(base_dir / "data" / "structure_rules.md")
    if examples_dir is None:
        examples_dir = str(base_dir / "data" / "example_reports")

    # API 키
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY 환경변수 또는 --api-key 인자 필요")

    if verbose:
        print(f"🔍 팀 데이터 추출 중: {team_name}")

    # Step 1: CSV 데이터 추출
    team_data = extract_team_data(csv_dir, team_name)
    if not team_data["dd_survey"]:
        raise ValueError(f"DD Survey에서 '{team_name}' 팀 못 찾음")

    if verbose:
        print(f"   ✓ DD Survey: 1개 (Bootcamp {team_data['dd_survey'].get('session_label', '?')})")
        print(f"   ✓ Founders: {len(team_data['founders'])}개")
        print(f"   ✓ Team Formation: {len(team_data['team_formation'])}개 세션")
        print(f"   ✓ 팀 변화: {len(team_data['team_changes'])}회")
        print(f"   ✓ Retro: {len(team_data['retro_responses'])}개")

    # Step 2: 14 예시 로드
    examples = load_example_reports(examples_dir)
    if verbose:
        print(f"📚 Few-shot 예시 {len(examples)}개 로드")

    # Step 3: System prompt 구성 (언어 모드 반영)
    system_prompt = build_system_prompt(rules_path, examples, language=language)

    # Step 4: User prompt — 추출된 팀 데이터
    # === 80/20 OPTIMIZATION: Raw JSON 덤프 대신 deterministic facts 사용 ===
    # Python으로 미리 깔끔하게 추출한 팩트를 LLM에게 제공
    # → 디테일 누락 방지, Bootcamp 시그널 정확 인식
    team_facts = build_team_facts(team_data)
    facts_text = format_facts_for_prompt(team_facts)

    user_prompt = f"""Generate the Investment Memo content for team **{team_name}**.

# TEAM SIZE: {team_size} member(s)
- Generate FOUNDER_1~{team_size} fields with full content.
- For unused founder slots beyond {team_size}, set ALL fields to empty strings ("").

# CRITICAL: TEXT LENGTH LIMITS (STRICT — text overflows if exceeded)
- FOUNDER_N_HEADING: max 25 chars (e.g., "Daniel Kim (CEO)")
- FOUNDER_N_BG_1/BG_2/BG_3: max 50 chars each
- WHY_KOREA / WHY_NOW / WHY_GLOBAL: max 90 chars EACH (Market Timing & Opportunity box)
- TAM_RATIONALE / SAM_RATIONALE / SOM_RATIONALE: max 180 chars
- RATIONALE_1~6 (Slide 8): max 130 chars each
- Each bullet = ONE statement. No multi-clause sentences.

# CRITICAL: SLIDE 8 SCORE/RATIONALE CATEGORY MAPPING (STRICT)
The 6 score/rationale pairs MUST evaluate ONLY their assigned category:
- SCORE_1 + RATIONALE_1 → Team Cohesion (team dynamics, founder fit, role split)
- SCORE_2 + RATIONALE_2 → Execution (speed, delivery, milestone hitting)
- SCORE_3 + RATIONALE_3 → Resilience (handling setbacks, pivot capability, persistence)
- SCORE_4 + RATIONALE_4 → Market Understanding (TAM/SAM/SOM accuracy, customer insight)
- SCORE_5 + RATIONALE_5 → Technology (technical depth, defensibility, IP)
- SCORE_6 + RATIONALE_6 → Innovation (novelty, creative approach, unique angle)

DO NOT mix categories. RATIONALE_1 must talk about team cohesion only, not market.

# CRITICAL: USE THE FACTS BELOW

The facts below are pre-extracted from Antler CSVs by deterministic Python code.
- Use ALL founder background details (preserve specifics like company names, certifications, years)
- Bootcamp progression: faithfully describe each session's signal/score/feedback
- If "married couple: YES" or "preformed: YES", emphasize in narrative
- DO NOT invent numbers; use only what's in facts

═══════════════════════════════════════════════════════════
# TEAM FACTS (pre-extracted, ground truth)
═══════════════════════════════════════════════════════════

{facts_text}

═══════════════════════════════════════════════════════════

# REQUIRED OUTPUT

Use the `submit_memo_content` tool to submit complete content JSON.

Apply ALL structure rules. Match JaeHee/Jiho/Gabriel quality. Critical DD analysis required.
Slide 7 STAGE descriptions MUST cite Bootcamp signals + partner names from the facts above.
"""

    # Step 5: Anthropic API 호출 with tool use
    client = anthropic.Anthropic(api_key=api_key)

    if verbose:
        print(f"🤖 Claude {model} 호출 중...")

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=16000,
                # Prompt Caching: system prompt(예시+규칙)을 캐싱
                # → 두 번째 호출부터 input 비용 90% 할인
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[{
                    "name": "submit_memo_content",
                    "description": "Submit the complete Investment Memo content as a structured JSON.",
                    "input_schema": PLACEHOLDER_SCHEMA,
                }],
                tool_choice={"type": "tool", "name": "submit_memo_content"},
                messages=[{"role": "user", "content": user_prompt}],
            )

            # 캐시 사용량 로그 (verbose 모드)
            if verbose and hasattr(response, "usage"):
                usage = response.usage
                cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
                cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
                if cache_read > 0:
                    print(f"   💰 캐시 적중: {cache_read:,} tokens (90% 할인)")
                elif cache_write > 0:
                    print(f"   📝 캐시 생성: {cache_write:,} tokens (다음 호출부터 할인)")
        except Exception as e:
            print(f"❌ API 호출 실패: {e}", file=sys.stderr)
            raise

        # tool use 결과 추출
        content = None
        for block in response.content:
            if hasattr(block, "input") and block.input:
                content = block.input
                break
        if not content:
            print(f"❌ tool use 결과 없음 (재시도 {attempt + 1}/{max_retries})", file=sys.stderr)
            continue

        # Step 6: 자동 체크리스트
        if verbose:
            print(f"✅ 콘텐츠 생성 완료 ({len(content)}개 키)")
            print(f"🔍 자동 체크리스트 검증 중...")

        passed, issues = auto_checklist(content, language=language)

        if passed:
            if verbose:
                print(f"   ✓ 모든 체크 통과")
            break
        else:
            if verbose:
                print(f"   체크리스트 이슈 {len(issues)}건:")
                for issue in issues:
                    print(f"     {issue}")
            if attempt < max_retries:
                if verbose:
                    print(f"   ↻ 재시도 ({attempt + 1}/{max_retries})...")
                # 재시도 시 user_prompt에 이슈 추가
                user_prompt += f"\n\n# PREVIOUS ATTEMPT ISSUES (FIX THESE)\n" + "\n".join(issues)
            else:
                if verbose:
                    print(f"   ⚠️  재시도 한도 초과. 일부 이슈 남은 채로 반환")

    # 메타 추가
    content["_meta"] = {
        "team_name": team_name,
        "data_sources": {
            "dd_survey_session": team_data["dd_survey"].get("session_label", ""),
            "team_formation_sessions": len(team_data["team_formation"]),
            "team_changes": len(team_data["team_changes"]),
        },
        "generated_with": f"generate.py v2 (model: {model}, strict: {strict_mode})",
    }

    return content


# ============================================================
# CLI
# ============================================================


def main():
    parser = argparse.ArgumentParser(description="Antler Investment Memo 자동 콘텐츠 생성")
    parser.add_argument("--team", required=True, help="팀 이름")
    parser.add_argument("--csv-dir", required=True, help="CSV 폴더")
    parser.add_argument("--output", required=True, help="출력 JSON 경로")
    parser.add_argument("--rules", help="structure_rules.md 경로")
    parser.add_argument("--examples", help="example_reports/ 폴더")
    parser.add_argument("--api-key", help="Anthropic API 키")
    parser.add_argument("--model", default="claude-sonnet-4-5", help="Claude 모델")
    parser.add_argument("--strict", action="store_true", help="strict mode (안전장치 4)")
    parser.add_argument("--quiet", action="store_true", help="진행 상황 출력 안 함")
    args = parser.parse_args()

    content = generate_memo_content(
        team_name=args.team,
        csv_dir=args.csv_dir,
        rules_path=args.rules,
        examples_dir=args.examples,
        api_key=args.api_key,
        model=args.model,
        strict_mode=args.strict,
        verbose=not args.quiet,
    )

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    print(f"\n💾 출력: {args.output}")


if __name__ == "__main__":
    main()
