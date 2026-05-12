"""
render.py — 투자심의보고서 PPTX 렌더러 (v2 강화)

Placeholder 치환 + 폰트 통일 + 사진 자동 다운로드 + 레이더차트 자동 생성.

핵심 동작:
  1. 템플릿 PPTX 언팩
  2. 슬라이드 XML에서 {{KEY}} → 실제 값으로 치환
  3. 폰트 Arial 강제 통일
  4. (자동) 파운더 사진 다운로드 (founders CSV의 photo_url)
  5. (자동) 레이더차트 생성 + 슬라이드 8 image15.png 교체
  6. PPTX 다시 패킹

사용법 (CLI):
    python render.py \\
        --template templates/DD_Template_2person.pptx \\
        --content team_content.json \\
        --output output/TeamName_DD.pptx \\
        [--founders-csv path/to/founders.csv]   # 사진 자동 다운로드
        [--no-chart]                              # 차트 생성 안 함
        [--photos-dir local/photos/]              # 로컬 사진 폴더 fallback

파일명 컨벤션:
    출력: {TeamName}_DD.pptx (예: handa_DD.pptx, AList_DD.pptx)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import ssl
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, Union


# ============================================================
# 텍스트 처리
# ============================================================


def xml_escape(text: str) -> str:
    """XML 특수문자 이스케이프."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def replace_placeholders(xml: str, content: dict) -> tuple[str, list[str]]:
    """슬라이드 XML에서 {{KEY}} 패턴 치환."""
    replaced = []
    keys_in_xml = set(re.findall(r"\{\{([A-Z_0-9]+)\}\}", xml))
    for key in keys_in_xml:
        placeholder = f"{{{{{key}}}}}"
        value = content.get(key, "")
        xml = xml.replace(placeholder, xml_escape(value))
        replaced.append(key)
    return xml, replaced


def enforce_arial(xml: str) -> str:
    """모든 텍스트 폰트를 Arial로 강제 통일."""
    return re.sub(r'typeface="[^"]*"', 'typeface="Arial"', xml)


# ============================================================
# 사진 다운로드
# ============================================================


def lookup_founder_photo_url(
    founders_csv: str,
    founder_name: str,
    team_name: Optional[str] = None,
) -> Optional[str]:
    """founders CSV에서 이름으로 photo_url 검색.

    매칭 우선순위:
      1. 정확 이름 매칭
      2. Last name + first name 첫 글자 매칭 (예: "Matt McLuckie" ↔ "Matthew McLuckie")
      3. Last name 단독 매칭 (가장 약함, 마지막 fallback)

    team_name이 주어지면 같은 팀 안에서 우선 매칭하되, 팀 컬럼이 없는 CSV에서도 동작.
    """
    if not founders_csv or not os.path.exists(founders_csv):
        return None

    name_lower = founder_name.lower().strip()
    name_tokens = [w.lower() for w in re.split(r"\s+", founder_name) if len(w) >= 2]
    if not name_tokens:
        return None
    last_name = name_tokens[-1]
    first_initial = name_tokens[0][0] if name_tokens[0] else ""

    # 모든 row 로드
    with open(founders_csv, "r", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f, delimiter=";"))

    # 같은 팀 row 추리기 (가능하면)
    team_rows = []
    if team_name:
        tn = team_name.lower()
        for row in all_rows:
            blob = " ".join(str(v) for v in row.values()).lower()
            if tn in blob:
                team_rows.append(row)

    def match_in(rows):
        # 1차: 정확 매칭
        for row in rows:
            csv_name = (row.get("name") or "").strip().lower()
            if csv_name == name_lower:
                url = (row.get("photo_url") or "").strip()
                if url:
                    return url
        # 2차: last name + first initial 매칭
        for row in rows:
            csv_name = (row.get("name") or "").strip().lower()
            if not csv_name:
                continue
            csv_tokens = [w for w in re.split(r"\s+", csv_name) if len(w) >= 2]
            if not csv_tokens:
                continue
            csv_last = csv_tokens[-1]
            csv_first_initial = csv_tokens[0][0] if csv_tokens[0] else ""
            if csv_last == last_name and csv_first_initial == first_initial:
                url = (row.get("photo_url") or "").strip()
                if url:
                    return url
        return None

    # 우선 같은 팀 안에서 매칭
    if team_rows:
        url = match_in(team_rows)
        if url:
            return url

    # Fallback: 전체 CSV에서 매칭 (단, 팀 정보가 없을 때만)
    if not team_rows:
        return match_in(all_rows)

    # 같은 팀 안에서 못 찾았으면 전체에서도 안전하게 last+first_initial 매칭만
    return match_in(all_rows)


def download_photo(url: str, output_path: str, verbose: bool = True) -> bool:
    """URL에서 사진 다운로드. SSL 검증 우회 옵션 포함."""
    if not url:
        return False
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
        if verbose:
            size_kb = os.path.getsize(output_path) / 1024
            print(f"   📥 {os.path.basename(output_path)} ({size_kb:.0f}KB)")
        return True
    except Exception as e:
        if verbose:
            print(f"   ⚠️  다운로드 실패: {url[:60]}... — {e}")
        return False


def find_local_photo(photos_dir: str, founder_name: str) -> Optional[str]:
    """로컬 폴더에서 사진 찾기.

    매칭 우선순위:
      1. 정확 이름 매칭 (대소문자 무관)
      2. Last name 매칭 + first name이 prefix 관계 (예: "Razeen" ↔ "Razeenuddin")
      3. Last name 매칭 + 어떤 token이든 일치
    """
    if not photos_dir or not os.path.exists(photos_dir):
        return None

    name_lower = founder_name.lower().strip()
    name_tokens = [w.lower() for w in re.split(r"\s+", founder_name) if len(w) >= 2]
    if not name_tokens:
        return None
    last_name = name_tokens[-1]
    first_name = name_tokens[0] if len(name_tokens) > 1 else ""

    # 1. 정확 매칭
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join(photos_dir, f"{founder_name}{ext}")
        if os.path.exists(path):
            return path

    # 모든 파일 후보 수집
    candidates = []
    for filename in os.listdir(photos_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg"]:
            continue
        name_part = os.path.splitext(filename)[0]
        candidates.append((filename, name_part.lower()))

    # 2. 정확 매칭 (대소문자 무관)
    for filename, file_name_lower in candidates:
        if file_name_lower == name_lower:
            return os.path.join(photos_dir, filename)

    # 3. Last name + first name prefix 매칭
    # 예: "Razeen Mehdi" ↔ "Mohammad Razeenuddin Mehdi"
    #   - last name "mehdi" 매칭
    #   - "razeen" prefix of "razeenuddin" → 매칭
    for filename, file_name_lower in candidates:
        file_tokens = [w for w in re.split(r"\s+", file_name_lower) if len(w) >= 2]
        if not file_tokens:
            continue
        file_last = file_tokens[-1]

        if file_last != last_name:
            continue  # last name 다르면 skip

        # last name 같음 → first name 토큰 비교
        if not first_name:
            return os.path.join(photos_dir, filename)

        # 어느 token이든 prefix 관계면 매칭
        for ft in file_tokens[:-1]:  # last 제외
            if ft.startswith(first_name) or first_name.startswith(ft):
                return os.path.join(photos_dir, filename)

    # 4. Fallback: last name만 일치하면 매칭 (위험하지만 마지막 수단)
    last_name_matches = []
    for filename, file_name_lower in candidates:
        file_tokens = [w for w in re.split(r"\s+", file_name_lower) if len(w) >= 2]
        if file_tokens and file_tokens[-1] == last_name:
            last_name_matches.append(filename)
    if len(last_name_matches) == 1:
        # last name이 unique하면 매칭
        return os.path.join(photos_dir, last_name_matches[0])

    return None


def replace_image(unpacked_dir: str, target_image: str, new_image_path: str) -> bool:
    """PPTX 미디어 폴더의 특정 이미지를 교체."""
    media_path = os.path.join(unpacked_dir, "ppt", "media", target_image)
    if not os.path.exists(media_path):
        return False
    if not os.path.exists(new_image_path):
        return False
    shutil.copy2(new_image_path, media_path)
    return True


# ============================================================
# Native chart 데이터 교체
# ============================================================


def parse_score(value, max_score: int = 5) -> Optional[float]:
    """SCORE 필드 값을 숫자로 파싱 ('3.5/5', 'B+', '3' 등 처리)."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if "/" in s:
        s = s.split("/")[0].strip()
    grade_map = {
        "A+": 5.0, "A": 4.7, "A-": 4.3,
        "B+": 4.0, "B": 3.7, "B-": 3.3,
        "C+": 3.0, "C": 2.7, "C-": 2.3,
        "D+": 2.0, "D": 1.7, "F": 1.0,
    }
    if s.upper() in grade_map:
        return grade_map[s.upper()]
    try:
        return float(s)
    except ValueError:
        return None



def fix_founder3_image_ref(work_dir: str, verbose: bool = True) -> bool:
    """Slide 6의 Founder 3 사진이 Founder 2와 같은 image rId 공유 시 분리.

    PowerPoint에서 사진 박스 복사+붙여넣기로 만들면 같은 image11.png 참조함.
    이 함수는 image12.png를 새로 만들고 별도 rId를 부여하여 충돌 방지.
    """
    slide_path = os.path.join(work_dir, "ppt", "slides", "slide6.xml")
    rels_path = os.path.join(work_dir, "ppt", "slides", "_rels", "slide6.xml.rels")
    media_dir = os.path.join(work_dir, "ppt", "media")

    if not os.path.exists(slide_path) or not os.path.exists(rels_path):
        return False

    with open(slide_path, "r", encoding="utf-8") as f:
        slide_xml = f.read()
    with open(rels_path, "r", encoding="utf-8") as f:
        rels_xml = f.read()

    embed_matches = list(re.finditer(r'r:embed="(rId\d+)"', slide_xml))
    if len(embed_matches) < 3:
        return False  # founder 3 사진 없음

    second_rid = embed_matches[1].group(1)
    third_rid = embed_matches[2].group(1)
    if second_rid != third_rid:
        return False  # 이미 별도

    # 2번째 rId가 가리키는 image 찾기
    rid_to_target = dict(re.findall(
        r'Id="(rId\d+)"[^>]*Target="\.\./media/(image\d+\.[a-z]+)"',
        rels_xml
    ))
    if second_rid not in rid_to_target:
        return False
    second_image = rid_to_target[second_rid]

    # image12.png 생성 (복제)
    src = os.path.join(media_dir, second_image)
    dst = os.path.join(media_dir, "image12.png")
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy(src, dst)

    # 새 rId 추가
    existing_rids = [int(m) for m in re.findall(r'Id="rId(\d+)"', rels_xml)]
    new_rid_num = max(existing_rids) + 1
    new_rid = f"rId{new_rid_num}"
    new_rel = (
        f'<Relationship Id="{new_rid}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
        f'Target="../media/image12.png"/>'
    )
    rels_xml = rels_xml.replace("</Relationships>", new_rel + "</Relationships>")

    # 3번째 r:embed reference 교체 (마지막 발생만)
    last = embed_matches[2]
    slide_xml = slide_xml[:last.start()] + f'r:embed="{new_rid}"' + slide_xml[last.end():]

    with open(slide_path, "w", encoding="utf-8") as f:
        f.write(slide_xml)
    with open(rels_path, "w", encoding="utf-8") as f:
        f.write(rels_xml)

    if verbose:
        print(f"   🔧 Founder 3 image ref 분리: {second_rid} → {new_rid}")
    return True


def remove_unused_founder_shapes(slide_xml: str, content: dict) -> tuple:
    """FOUNDER_N_HEADING이 비어있으면 그 슬롯의 텍스트박스 + 사진 shape 제거.

    역순(3,2,1)으로 처리하여 인덱스 안정성 유지.
    Returns: (수정된_xml, 제거된_founder_번호_리스트)
    """
    removed = []

    for i in [3, 2, 1]:
        heading = (content.get(f"FOUNDER_{i}_HEADING") or "").strip()
        if heading:
            continue  # 이 founder는 사용 중

        # 1) 텍스트 shape 제거 (placeholder로 식별)
        text_pattern = re.compile(
            rf"<p:sp\b(?:(?!<p:sp\b).)*?\{{\{{FOUNDER_{i}_HEADING\}}\}}.*?</p:sp>",
            re.DOTALL,
        )
        before = slide_xml
        slide_xml = text_pattern.sub("", slide_xml, count=1)
        text_removed = (slide_xml != before)

        # 2) 사진 shape 제거 (위치 기반: i번째 <p:pic>)
        pic_blocks = list(re.finditer(r"<p:pic>.*?</p:pic>", slide_xml, re.DOTALL))
        pic_removed = False
        if pic_blocks and len(pic_blocks) >= i:
            block = pic_blocks[i - 1]  # 0-indexed
            slide_xml = slide_xml[:block.start()] + slide_xml[block.end():]
            pic_removed = True

        if text_removed or pic_removed:
            removed.append(i)

    return slide_xml, removed


def replace_chart_data(unpacked_dir: str, scores: list) -> bool:
    """ppt/charts/chart1.xml 의 radar chart 데이터 6개 값을 교체.

    Native chart 구조:
        <c:val>
          <c:numRef>
            <c:numCache>
              <c:pt idx="0"><c:v>4.000000</c:v></c:pt>
              ... (6개)
            </c:numCache>
          </c:numRef>
        </c:val>

    Args:
        unpacked_dir: 언팩된 PPTX 디렉토리
        scores: 6개 점수 리스트 [SCORE_1, ..., SCORE_6]

    Returns:
        교체 성공 여부
    """
    chart_path = os.path.join(unpacked_dir, "ppt", "charts", "chart1.xml")
    if not os.path.exists(chart_path):
        return False
    if len(scores) != 6:
        return False

    with open(chart_path, "r", encoding="utf-8") as f:
        xml = f.read()

    # <c:val>...</c:val> 블록만 타깃 (cat 블록의 string 값은 건드리지 않음)
    val_match = re.search(r"<c:val>.*?</c:val>", xml, re.DOTALL)
    if not val_match:
        return False
    val_block = val_match.group(0)

    # 새 val_block 만들기 — 6개 <c:v> 교체
    new_val_block = val_block
    pts = re.findall(r'<c:pt idx="(\d+)"><c:v>[^<]*</c:v></c:pt>', val_block)
    if len(pts) != 6:
        return False

    for i, score in enumerate(scores):
        # 6.0 형식 (Excel 기본 표기)
        new_v = f"{float(score):.6f}"
        new_val_block = re.sub(
            rf'(<c:pt idx="{i}"><c:v>)[^<]*(</c:v></c:pt>)',
            rf'\g<1>{new_v}\g<2>',
            new_val_block,
            count=1,
        )

    xml = xml.replace(val_block, new_val_block)

    with open(chart_path, "w", encoding="utf-8") as f:
        f.write(xml)
    return True


# ============================================================
# 글자수 검증
# ============================================================

# placeholder_keys.md 기반 권장 글자수 (영문 기준)
RECOMMENDED_LENGTHS = {
    "COMPANY_NAME": 15, "ONELINER": 60, "COHORT": 8,
    "PROBLEM_1": 130, "PROBLEM_2": 130, "PROBLEM_3": 130,
    "SOLUTION_1": 130, "SOLUTION_2": 130, "SOLUTION_3": 130,
    "VALUE_1": 90, "VALUE_2": 90, "VALUE_3": 90,
    "TAM_AMOUNT": 8, "TAM_DESC": 50, "TAM_RATIONALE": 180,
    "SAM_AMOUNT": 8, "SAM_DESC": 50, "SAM_RATIONALE": 180,
    "SOM_AMOUNT": 8, "SOM_DESC": 50, "SOM_RATIONALE": 180,
    "WHY_KOREA": 100, "WHY_NOW": 100, "WHY_GLOBAL": 100,
    "COMP1_NAME": 25, "COMP1_COUNTRY": 12, "COMP1_FUNDING": 25, "COMP1_DESC": 130,
    "COMP2_NAME": 25, "COMP2_COUNTRY": 12, "COMP2_FUNDING": 25, "COMP2_DESC": 130,
    "COMP3_NAME": 25, "COMP3_COUNTRY": 12, "COMP3_FUNDING": 25, "COMP3_DESC": 130,
    "COMP4_NAME": 25, "COMP4_COUNTRY": 12, "COMP4_FUNDING": 25, "COMP4_DESC": 130,
    "DIFF_1": 150, "DIFF_2": 150, "DIFF_3": 150, "DIFF_4": 150,
    "GTM_1": 130, "GTM_2": 130, "GTM_3": 130,
    "PRICING_1": 110, "PRICING_2": 110,
    "BM_1": 110, "BM_2": 110,
    "SCALE_1": 130, "SCALE_2": 130, "SCALE_3": 130,
    "WHY_TEAM_1": 150, "WHY_TEAM_2": 150, "WHY_TEAM_3": 150,
    "FOUNDER_1_HEADING": 25, "FOUNDER_1_BG_1": 60, "FOUNDER_1_BG_2": 60, "FOUNDER_1_BG_3": 50,
    "FOUNDER_2_HEADING": 25, "FOUNDER_2_BG_1": 60, "FOUNDER_2_BG_2": 60, "FOUNDER_2_BG_3": 50,
    "FOUNDER_3_HEADING": 25, "FOUNDER_3_BG_1": 60, "FOUNDER_3_BG_2": 60, "FOUNDER_3_BG_3": 50,
    "STAGE_1_DESC": 130, "STAGE_2_DESC": 130, "STAGE_3_DESC": 130,
    "STAGE_4_DESC": 130, "STAGE_5_DESC": 130, "STAGE_6_DESC": 130, "STAGE_7_DESC": 130,
    "SCORE_1": 8, "SCORE_2": 8, "SCORE_3": 8, "SCORE_4": 8, "SCORE_5": 8, "SCORE_6": 8,
    "RATIONALE_1": 130, "RATIONALE_2": 130, "RATIONALE_3": 130,
    "RATIONALE_4": 130, "RATIONALE_5": 130, "RATIONALE_6": 130,
    "STRENGTH_1": 35, "STRENGTH_1_DESC": 180,
    "STRENGTH_2": 35, "STRENGTH_2_DESC": 180,
    "STRENGTH_3": 35, "STRENGTH_3_DESC": 180,
    "STRENGTH_4": 35, "STRENGTH_4_DESC": 180,
    "IMPROVEMENT_1": 35, "IMPROVEMENT_1_DESC": 180,
    "IMPROVEMENT_2": 35, "IMPROVEMENT_2_DESC": 180,
    "IMPROVEMENT_3": 35, "IMPROVEMENT_3_DESC": 180,
    "IMPROVEMENT_4": 35, "IMPROVEMENT_4_DESC": 180,
    "FOUNDER_EQUITY": 200,
    "SUMMARY_DESC": 280, "RISKS_DESC": 280,
}


def check_overflow(content: dict, tolerance: float = 1.15) -> list[tuple[str, int, int]]:
    """글자수 초과 필드 검출.

    Returns:
        [(field, actual_length, recommended_length), ...]
    """
    overflow = []
    for field, value in content.items():
        if field.startswith("_") or not isinstance(value, str):
            continue
        rec = RECOMMENDED_LENGTHS.get(field)
        if rec is None:
            continue
        actual = len(value)
        if actual > rec * tolerance:
            overflow.append((field, actual, rec))
    return overflow


# ============================================================
# 메인 렌더 함수
# ============================================================


def render_memo(
    template_path: str,
    content_json: Union[str, dict],
    output_path: str,
    founders_csv: Optional[str] = None,
    photos_dir: Optional[str] = None,
    chart_path: Optional[str] = None,
    auto_generate_chart: bool = True,
    verbose: bool = True,
) -> dict:
    """투자심의보고서 PPTX 생성.

    Args:
        template_path: 템플릿 PPTX 경로
        content_json: 콘텐츠 JSON 경로 또는 dict
        output_path: 출력 PPTX 경로
        founders_csv: founders CSV (사진 photo_url 자동 검색)
        photos_dir: 로컬 사진 폴더 (CSV 없거나 다운로드 실패 시 fallback)
        chart_path: 레이더차트 PNG 경로 (제공 시 자동 생성 비활성)
        auto_generate_chart: SCORE_1~6 있으면 차트 자동 생성

    Returns:
        실행 결과 딕셔너리
    """
    # 콘텐츠 로드
    if isinstance(content_json, dict):
        content = dict(content_json)
    else:
        with open(content_json, "r", encoding="utf-8") as f:
            content = json.load(f)
    content_clean = {k: v for k, v in content.items() if not k.startswith("_")}

    if verbose:
        print(f"📄 템플릿: {template_path}")
        print(f"📋 콘텐츠 키: {len(content_clean)}개")

    # 글자수 사전 검사
    overflow = check_overflow(content_clean)
    if overflow and verbose:
        print(f"\n⚠️  글자수 초과 의심 ({len(overflow)}개):")
        for field, actual, rec in overflow[:5]:
            print(f"   {field}: {actual}자 (권장 {rec}자, +{actual - rec})")
        if len(overflow) > 5:
            print(f"   ... 외 {len(overflow) - 5}개")
        print()

    # 템플릿 언팩
    work_dir = output_path + ".tmp"
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(work_dir, exist_ok=True)
    with zipfile.ZipFile(template_path, "r") as z:
        z.extractall(work_dir)
        template_files = z.namelist()

    # Placeholder 치환 + Arial 통일
    slides_dir = os.path.join(work_dir, "ppt", "slides")
    all_template_keys = set()
    filled_count = 0

    # Slide 6 처리 전: Founder 3 image ref 분리 (중복 시)
    fix_founder3_image_ref(work_dir, verbose=verbose)

    founders_removed_in_slide6 = []
    for slide_path in sorted(Path(slides_dir).glob("slide*.xml")):
        with open(slide_path, "r", encoding="utf-8") as f:
            xml = f.read()

        # Slide 6 (Team)에서 사용 안 되는 founder shape 제거
        if slide_path.name == "slide6.xml":
            xml, founders_removed_in_slide6 = remove_unused_founder_shapes(xml, content_clean)
            if founders_removed_in_slide6 and verbose:
                print(f"   🚫 Slide 6: Founder {founders_removed_in_slide6} 슬롯 제거")

        keys = set(re.findall(r"\{\{([A-Z_0-9]+)\}\}", xml))
        all_template_keys.update(keys)
        xml, replaced = replace_placeholders(xml, content_clean)
        xml = enforce_arial(xml)
        for k in replaced:
            if k in content_clean:
                filled_count += 1
        with open(slide_path, "w", encoding="utf-8") as f:
            f.write(xml)

    unfilled_keys = sorted(all_template_keys - set(content_clean.keys()))
    if verbose:
        print(f"✅ Placeholder 치환: {filled_count}개")
        if unfilled_keys:
            print(f"⚠️  콘텐츠 미제공 ({len(unfilled_keys)}개): {', '.join(unfilled_keys[:3])}{'...' if len(unfilled_keys) > 3 else ''}")

    # 파운더 사진 자동 처리
    photos_replaced = []
    photo_temp_dir = tempfile.mkdtemp(prefix="founder_photos_")

    if verbose:
        print(f"\n📸 파운더 사진 처리:")

    # 사진 매칭에 쓸 team_name 추정 (콘텐츠의 COMPANY_NAME)
    team_name_for_photo = (content_clean.get("COMPANY_NAME") or "").strip()

    for i in [1, 2, 3]:
        heading_key = f"FOUNDER_{i}_HEADING"
        if heading_key not in content_clean:
            continue
        heading = content_clean[heading_key]
        if not heading.strip():
            continue

        # 이름 추출 (예: "Daniel Kim (CEO)" → "Daniel Kim")
        name = re.split(r"\s*[\(\[]", heading)[0].strip()
        if not name or "Recruiting" in name or "공석" in name:
            continue

        # 1순위: 로컬 photos_dir (사용자 제어 우선)
        photo_path = None
        if photos_dir:
            photo_path = find_local_photo(photos_dir, name)
            if photo_path and verbose:
                print(f"   📁 로컬: {os.path.basename(photo_path)}")

        # 2순위: founders CSV photo_url 다운로드 (fallback)
        if not photo_path and founders_csv:
            url = lookup_founder_photo_url(founders_csv, name, team_name=team_name_for_photo)
            if url:
                tmp_path = os.path.join(photo_temp_dir, f"{name}.png")
                if download_photo(url, tmp_path, verbose=verbose):
                    photo_path = tmp_path

        if not photo_path:
            if verbose:
                print(f"   ⚠️  {name}: 사진 못 찾음")
            continue

        # PPTX 미디어 교체 (새 템플릿: image10=founder1, image11=founder2)
        target_image = {1: "image10.png", 2: "image11.png", 3: "image12.png"}.get(i)
        if replace_image(work_dir, target_image, photo_path):
            photos_replaced.append(f"{name} → {target_image}")
            if verbose:
                print(f"   ✅ {name} → {target_image}")

    # 레이더차트 데이터 교체 (Native chart — chart1.xml 의 c:numCache)
    chart_replaced = False
    if auto_generate_chart:
        # SCORE_1~6 추출
        score_values = []
        for i in range(1, 7):
            raw = content_clean.get(f"SCORE_{i}", "")
            parsed = parse_score(raw)
            score_values.append(parsed if parsed is not None else 0.0)

        has_any = any(s > 0 for s in score_values)
        if has_any:
            if replace_chart_data(work_dir, score_values):
                chart_replaced = True
                if verbose:
                    print(f"\n📊 Native 레이더차트 데이터 교체:")
                    print(f"   점수: {score_values}")
            else:
                if verbose:
                    print(f"\n⚠️  Native chart 교체 실패 — chart1.xml 구조 확인 필요")

    # PPTX 다시 패킹
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except PermissionError:
            # 다른 프로세스가 열고 있을 수 있음 — 이름 변경
            output_path = output_path.replace(".pptx", "_new.pptx")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 원본 template_files + 처리 중 새로 추가된 파일 모두 포함
    # (예: fix_founder3_image_ref가 만든 image12.png)
    files_to_pack = set(template_files)
    work_dir_path = Path(work_dir)
    for fp in work_dir_path.rglob("*"):
        if fp.is_file():
            rel = str(fp.relative_to(work_dir_path))
            files_to_pack.add(rel)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as out_zip:
        for fname in sorted(files_to_pack):
            full_path = os.path.join(work_dir, fname)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, "rb") as f:
                    out_zip.writestr(fname, f.read())

    # 정리
    shutil.rmtree(work_dir, ignore_errors=True)
    shutil.rmtree(photo_temp_dir, ignore_errors=True)

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    if verbose:
        print(f"\n💾 출력: {output_path} ({size_mb:.1f} MB)")

    return {
        "success": True,
        "filled_count": filled_count,
        "unfilled_keys": unfilled_keys,
        "photos_replaced": photos_replaced,
        "chart_replaced": chart_replaced,
        "overflow_fields": overflow,
        "output_path": output_path,
    }


# ============================================================
# CLI
# ============================================================


def main():
    parser = argparse.ArgumentParser(
        description="투자심의보고서 PPTX 렌더러",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
파일명 컨벤션:
    출력은 {TeamName}_DD.pptx 형식 권장 (handa_DD.pptx, AList_DD.pptx 등)

예시:
  # 기본 (CSV 없이)
  python render.py \\
      --template templates/DD_Template_2person.pptx \\
      --content examples/handa_content.json \\
      --output output/handa_DD.pptx

  # 사진 자동 다운로드 + 차트 자동 생성
  python render.py \\
      --template templates/DD_Template_2person.pptx \\
      --content examples/handa_content.json \\
      --output output/handa_DD.pptx \\
      --founders-csv ../uploads/founders.csv
""",
    )
    parser.add_argument("--template", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--founders-csv", help="founders CSV (사진 photo_url 자동 검색)")
    parser.add_argument("--photos-dir", help="로컬 사진 폴더 (fallback)")
    parser.add_argument("--chart", help="레이더차트 PNG (자동 생성 비활성화)")
    parser.add_argument("--no-chart", action="store_true", help="차트 생성 안 함")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    result = render_memo(
        template_path=args.template,
        content_json=args.content,
        output_path=args.output,
        founders_csv=args.founders_csv,
        photos_dir=args.photos_dir,
        chart_path=args.chart,
        auto_generate_chart=not args.no_chart,
        verbose=not args.quiet,
    )

    if not args.quiet:
        print()
        print("=" * 50)
        print(f"렌더링 완료 — {result['output_path']}")
        if result["photos_replaced"]:
            print(f"📸 사진 교체: {len(result['photos_replaced'])}개")
        if result["chart_replaced"]:
            print(f"📊 차트 생성·교체 완료")
        if result["overflow_fields"]:
            print(f"⚠️  글자수 초과 {len(result['overflow_fields'])}개 필드 (콘텐츠 줄이기 권장)")

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
