"""
verify.py — 투자심의보고서 검증 도구 (PPTX + 콘텐츠 JSON)

[PPTX 검증]
  1. 깨진 placeholder (run splitting)
  2. 미치환 placeholder

[콘텐츠 JSON 검증] (NEW)
  3. 영문 검증 (한국어 비율 체크)
  4. 출처 명기 (TAM/SAM/SOM rationale에 출처 키워드)
  5. SOM 정의 (시장 풀 사이즈 ❌, 매출 단위 ✅)
  6. Slide 7 — 파트너 시그널·점수 포함
  7. 필수 필드 존재

사용법 (CLI):
    # PPTX 검증
    python verify.py templates/DD_Template_2person.pptx
    python verify.py output/Namatan_DD.pptx

    # 콘텐츠 JSON 검증
    python verify.py examples/handa_content.json --content

    # JSON 출력
    python verify.py output/Namatan_DD.pptx --json

  Exit codes:
    0 = 모두 OK
    1 = 문제 발견
    2 = 파일 에러
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile


def extract_runs_from_xml(xml: str) -> list[str]:
    """슬라이드 XML에서 모든 <a:t> 태그 내용 추출 (순서대로)."""
    return re.findall(r"<a:t[^>]*>([^<]*)</a:t>", xml)


def find_intact_placeholders(xml: str) -> set[str]:
    """단일 run으로 살아있는 placeholder 추출."""
    runs = extract_runs_from_xml(xml)
    placeholders = set()
    for r in runs:
        for ph in re.findall(r"\{\{[A-Z_0-9]+\}\}", r):
            placeholders.add(ph)
    return placeholders


def find_broken_fragments(xml: str) -> list[tuple[int, str]]:
    """쪼개진 placeholder 조각 찾기.

    예: <a:t>{{</a:t><a:t>KEY</a:t><a:t>}}</a:t> 처럼
    중괄호가 들어있지만 단일 placeholder를 형성하지 못하는 run.
    """
    runs = extract_runs_from_xml(xml)
    broken = []
    for i, r in enumerate(runs):
        if "{" in r or "}" in r:
            # 단일 run에 valid placeholder가 들어있으면 OK
            if re.fullmatch(r".*\{\{[A-Z_0-9]+\}\}.*", r):
                continue
            broken.append((i, r))
    return broken


def verify_pptx(pptx_path: str) -> dict:
    """PPTX 검증 실행.

    Returns:
        {
            "ok": bool,
            "total_placeholders": int,
            "broken_fragments": [{"slide": str, "run_idx": int, "text": str}],
            "remaining_placeholders": [str],   # 미치환된 {{KEY}}
            "all_intact_keys": [str],
            "errors": [str],
        }
    """
    result = {
        "ok": True,
        "total_placeholders": 0,
        "broken_fragments": [],
        "remaining_placeholders": [],
        "all_intact_keys": [],
        "errors": [],
    }

    if not os.path.exists(pptx_path):
        result["ok"] = False
        result["errors"].append(f"파일이 없음: {pptx_path}")
        return result

    try:
        with zipfile.ZipFile(pptx_path, "r") as z:
            slide_files = sorted(
                [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
                key=lambda x: int(re.search(r"(\d+)\.xml$", x).group(1)),
            )

            all_intact = set()
            all_remaining = set()

            for slide_name in slide_files:
                xml = z.read(slide_name).decode("utf-8")

                # 단일 run placeholder
                intact = find_intact_placeholders(xml)
                all_intact.update(intact)

                # 모든 placeholder (단일 run으로 살아있는 것 = 미치환)
                # 즉, 치환이 끝났으면 placeholder가 0개여야 함
                all_remaining.update(intact)

                # 깨진 조각
                broken = find_broken_fragments(xml)
                for run_idx, text in broken:
                    result["broken_fragments"].append({
                        "slide": os.path.basename(slide_name),
                        "run_idx": run_idx,
                        "text": text,
                    })

            result["all_intact_keys"] = sorted(all_intact)
            result["remaining_placeholders"] = sorted(all_remaining)
            result["total_placeholders"] = len(all_intact)

    except zipfile.BadZipFile:
        result["ok"] = False
        result["errors"].append(f"PPTX 파일이 손상됨: {pptx_path}")
        return result
    except Exception as e:
        result["ok"] = False
        result["errors"].append(f"검증 중 오류: {e}")
        return result

    # 깨진 조각이 있으면 NG
    if result["broken_fragments"]:
        result["ok"] = False

    return result


def print_human_report(result: dict, pptx_path: str, mode: str = "auto"):
    """사람이 읽기 좋은 형태로 결과 출력.

    mode:
      "template" — 템플릿 검증 (placeholder가 살아있어야 함)
      "rendered" — 렌더링 결과 검증 (placeholder가 0개여야 함)
      "auto"     — 자동 판별
    """
    print(f"📄 파일: {pptx_path}")
    print(f"   크기: {os.path.getsize(pptx_path) / 1024 / 1024:.1f} MB")
    print()

    # 에러 있으면 우선 출력
    if result["errors"]:
        print("❌ 에러:")
        for e in result["errors"]:
            print(f"   - {e}")
        return

    # 자동 모드 판별
    if mode == "auto":
        # placeholder가 많이 살아있으면 템플릿, 적거나 0이면 렌더링 결과
        if result["total_placeholders"] > 50:
            mode = "template"
        else:
            mode = "rendered"

    # === 깨진 조각 체크 (둘 다 적용) ===
    if result["broken_fragments"]:
        print(f"❌ 깨진 placeholder 조각 발견 ({len(result['broken_fragments'])}개):")
        # 슬라이드별로 그룹핑
        by_slide = {}
        for f in result["broken_fragments"]:
            by_slide.setdefault(f["slide"], []).append(f)
        for slide, fragments in sorted(by_slide.items()):
            print(f"   {slide}:")
            for f in fragments[:5]:
                print(f"      run #{f['run_idx']}: {f['text']!r}")
            if len(fragments) > 5:
                print(f"      ... 외 {len(fragments) - 5}개")
        print()
        print("   💡 해결: 해당 placeholder를 통째로 지우고 한 번에 다시 타이핑")
        print()
    else:
        print("✅ 깨진 placeholder 조각 없음")

    # === 모드별 추가 체크 ===
    if mode == "template":
        # 템플릿: 단일 run placeholder 수 표기
        print(f"📋 단일 run placeholder: {result['total_placeholders']}개")
        if result["all_intact_keys"]:
            print()
            print("   슬라이드에 박힌 placeholder 목록:")
            for k in result["all_intact_keys"][:20]:
                print(f"      {k}")
            if len(result["all_intact_keys"]) > 20:
                print(f"      ... 외 {len(result['all_intact_keys']) - 20}개")

    elif mode == "rendered":
        # 렌더링 결과: 미치환된 placeholder 있으면 경고
        if result["remaining_placeholders"]:
            print(f"⚠️  미치환된 placeholder ({len(result['remaining_placeholders'])}개):")
            for k in result["remaining_placeholders"][:15]:
                print(f"      {k}")
            if len(result["remaining_placeholders"]) > 15:
                print(f"      ... 외 {len(result['remaining_placeholders']) - 15}개")
            print()
            print("   💡 의도적으로 비워둔 슬라이드(예: 7~10)면 OK")
            print("   💡 그렇지 않으면 콘텐츠 JSON에 해당 키 추가 후 재렌더링")
        else:
            print("✅ 모든 placeholder 치환 완료")

    print()
    print("=" * 50)
    if result["ok"] and not result["broken_fragments"]:
        print("✅ 종합 결과: PASS")
    else:
        print("❌ 종합 결과: FAIL")


# ============================================================
# 콘텐츠 JSON 품질 검증 (NEW)
# ============================================================


SOURCE_KEYWORDS = [
    "McKinsey", "Bain", "BCG", "Goldman", "Morgan Stanley", "JPMorgan",
    "CISAC", "MLC", "IFPI", "RIAA", "ASCAP", "BMI",
    "Statista", "Mordor", "Gartner", "IDC", "Forrester", "Euromonitor",
    "통계청", "KDI", "Crunchbase", "PitchBook", "Adroit",
    "$", "%", "B", "M", "K", "year",
]


def verify_content_json(json_path: str) -> dict:
    """콘텐츠 JSON의 품질을 검증한다.

    Returns:
        {
            "ok": bool,
            "issues": [str],
            "warnings": [str],
            "passed_checks": [str],
            "field_count": int,
        }
    """
    result = {
        "ok": True,
        "issues": [],
        "warnings": [],
        "passed_checks": [],
        "field_count": 0,
        "errors": [],
    }

    if not os.path.exists(json_path):
        result["ok"] = False
        result["errors"].append(f"파일이 없음: {json_path}")
        return result

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            content = json.load(f)
    except Exception as e:
        result["ok"] = False
        result["errors"].append(f"JSON 파싱 실패: {e}")
        return result

    # 메타 필드 제외
    content_only = {k: v for k, v in content.items() if not k.startswith("_")}
    result["field_count"] = len(content_only)

    # === Check 1: 영문 검증 ===
    long_text_fields = [
        "PROBLEM_1", "PROBLEM_2", "PROBLEM_3",
        "SOLUTION_1", "SOLUTION_2", "SOLUTION_3",
        "VALUE_1", "VALUE_2", "VALUE_3",
        "WHY_KOREA", "WHY_NOW", "WHY_GLOBAL",
        "DIFF_1", "DIFF_2", "DIFF_3", "DIFF_4",
        "GTM_1", "GTM_2", "GTM_3",
        "PRICING_1", "PRICING_2",
        "BM_1", "BM_2",
        "SCALE_1", "SCALE_2", "SCALE_3",
        "WHY_TEAM_1", "WHY_TEAM_2", "WHY_TEAM_3",
        "STAGE_1_DESC", "STAGE_2_DESC", "STAGE_3_DESC",
        "STAGE_4_DESC", "STAGE_5_DESC", "STAGE_6_DESC", "STAGE_7_DESC",
        "RATIONALE_1", "RATIONALE_2", "RATIONALE_3",
        "RATIONALE_4", "RATIONALE_5", "RATIONALE_6",
        "STRENGTH_1_DESC", "STRENGTH_2_DESC", "STRENGTH_3_DESC", "STRENGTH_4_DESC",
        "IMPROVEMENT_1_DESC", "IMPROVEMENT_2_DESC", "IMPROVEMENT_3_DESC", "IMPROVEMENT_4_DESC",
        "FOUNDER_EQUITY", "SUMMARY_DESC", "RISKS_DESC",
    ]
    korean_fields = []
    for field in long_text_fields:
        text = content_only.get(field, "")
        if not text:
            continue
        korean_chars = sum(1 for c in text if "가" <= c <= "힣")
        total_chars = sum(1 for c in text if c.isalpha() or "가" <= c <= "힣")
        if total_chars > 0 and korean_chars / total_chars > 0.3:
            korean_fields.append(f"{field} ({korean_chars}/{total_chars} 한글)")

    if korean_fields:
        result["issues"].append(f"❌ 영문 검증 실패 ({len(korean_fields)}개 필드)")
        result["issues"].extend([f"   - {f}" for f in korean_fields[:5]])
        if len(korean_fields) > 5:
            result["issues"].append(f"   - ... 외 {len(korean_fields) - 5}개")
        result["ok"] = False
    else:
        result["passed_checks"].append("✓ 모든 텍스트 영문")

    # === Check 2: 출처 명기 ===
    rationale_fields = ["TAM_RATIONALE", "SAM_RATIONALE", "SOM_RATIONALE"]
    missing_sources = []
    for field in rationale_fields:
        text = content_only.get(field, "")
        if text and not any(kw.lower() in text.lower() for kw in SOURCE_KEYWORDS):
            missing_sources.append(field)

    if missing_sources:
        result["warnings"].append(f"⚠️  출처/수치 부재: {', '.join(missing_sources)}")
    else:
        result["passed_checks"].append("✓ TAM/SAM/SOM 출처 명기")

    # === Check 3: SOM 정의 ===
    som_text = (content_only.get("SOM_DESC", "") + " " + content_only.get("SOM_RATIONALE", "")).lower()
    danger_phrases = ["market pool", "전체 시장", "total addressable", "전체 풀"]
    if som_text and any(p in som_text for p in danger_phrases):
        result["warnings"].append("⚠️  SOM이 시장 풀로 표현됨 (capturable revenue로 수정 권장)")
    elif som_text and any(kw in som_text for kw in ["×", "x ", "= $"]):
        result["passed_checks"].append("✓ SOM에 산식 포함 (capturable revenue)")

    # === Check 4: Slide 7 파트너 시그널 ===
    stage_4_to_6 = " ".join([content_only.get(f"STAGE_{i}_DESC", "") for i in [4, 5, 6]])
    has_partner = any(p in stage_4_to_6 for p in ["Jiho", "Jaehee", "JaeHee", "Gabriel"])
    has_signal = any(s.lower() in stage_4_to_6.lower() for s in ["red", "green", "yellow", "scored", "signal"])

    if not has_partner:
        result["warnings"].append("⚠️  Slide 7: 파트너 이름 없음 (Jiho/JaeHee/Gabriel 명시 필요)")
    if not has_signal:
        result["warnings"].append("⚠️  Slide 7: Bootcamp 시그널 없음 (Red/Green/score 명시 필요)")
    if has_partner and has_signal:
        result["passed_checks"].append("✓ Slide 7 파트너 시그널 포함")

    # === Check 5: 필수 필드 ===
    required = ["COMPANY_NAME", "ONELINER", "COHORT"]
    missing = [f for f in required if not content_only.get(f, "").strip()]
    if missing:
        result["issues"].append(f"❌ 필수 필드 누락: {', '.join(missing)}")
        result["ok"] = False
    else:
        result["passed_checks"].append("✓ 필수 필드 존재")

    # === Check 6: 채움률 ===
    filled = sum(1 for v in content_only.values() if v and str(v).strip())
    fill_rate = filled / max(len(content_only), 1) * 100
    if fill_rate < 70:
        result["warnings"].append(f"⚠️  채움률 낮음: {fill_rate:.0f}% ({filled}/{len(content_only)})")

    return result


def print_content_report(result: dict, json_path: str):
    """콘텐츠 JSON 검증 결과 사람이 읽기 쉽게 출력."""
    print(f"📄 파일: {json_path}")
    print(f"📋 필드 수: {result['field_count']}개")
    print()

    if result["errors"]:
        print("❌ 에러:")
        for e in result["errors"]:
            print(f"   - {e}")
        return

    if result["passed_checks"]:
        print("✅ 통과 항목:")
        for c in result["passed_checks"]:
            print(f"   {c}")
        print()

    if result["warnings"]:
        print("⚠️  경고:")
        for w in result["warnings"]:
            print(f"   {w}")
        print()

    if result["issues"]:
        print("❌ 실패 항목:")
        for i in result["issues"]:
            print(f"   {i}")
        print()

    print("=" * 50)
    if result["ok"] and not result["issues"]:
        if result["warnings"]:
            print("⚠️  종합 결과: PASS (경고 있음)")
        else:
            print("✅ 종합 결과: PASS")
    else:
        print("❌ 종합 결과: FAIL")


def main():
    parser = argparse.ArgumentParser(
        description="투자심의보고서 검증 도구 (PPTX + 콘텐츠 JSON)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # PPTX 검증
  python verify.py templates/DD_Template_2person.pptx
  python verify.py output/Namatan_DD.pptx

  # 콘텐츠 JSON 검증 (NEW)
  python verify.py examples/handa_content.json --content

  # JSON 출력
  python verify.py output/Namatan_DD.pptx --json
""",
    )
    parser.add_argument("file", help="검증할 PPTX 또는 JSON 파일")
    parser.add_argument(
        "--mode",
        choices=["template", "rendered", "auto"],
        default="auto",
        help="PPTX 검증 모드",
    )
    parser.add_argument("--content", action="store_true", help="콘텐츠 JSON 검증 (자동 감지)")
    parser.add_argument("--json", action="store_true", help="JSON 형식으로 결과 출력")

    args = parser.parse_args()

    # 파일 종류 자동 감지
    is_content_json = args.content or args.file.endswith(".json")

    if is_content_json:
        result = verify_content_json(args.file)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_content_report(result, args.file)
    else:
        result = verify_pptx(args.file)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_human_report(result, args.file, mode=args.mode)

    if result.get("errors"):
        sys.exit(2)
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
