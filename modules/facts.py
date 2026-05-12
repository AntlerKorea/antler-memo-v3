"""
facts.py — Deterministic 팩트 추출

원본 CSV를 AI에게 통째로 던지지 않고, Python으로 명확하게 구조화한 팩트만 추출.
이렇게 하면 AI의 인지 부담이 줄고, 디테일 누락이 사라짐.

핵심:
  - 파운더 배경: team_members JSON을 line-by-line 보존
  - Bootcamp progression: signal/score/partner/feedback 시간순
  - Team dynamics: preformed/married 같은 패턴 자동 감지
  - Team changes: 멤버 변화 timeline
"""

from __future__ import annotations

import json
import re
from typing import Any


def build_team_facts(team_data: dict) -> dict:
    """Raw CSV data → 깨끗하게 구조화된 팩트.

    Args:
        team_data: extract_team_data()의 출력 (dd_survey, team_formation, etc.)

    Returns:
        AI에게 줄 깨끗한 팩트 dict
    """
    dd = team_data.get("dd_survey") or {}
    team_formation = team_data.get("team_formation") or []
    team_changes = team_data.get("team_changes") or []

    return {
        "team_name": dd.get("team_name", "").strip(),
        "cohort": dd.get("cohort", "").strip() or "KOR8",
        "founders": _extract_founders(dd),
        "team_dynamics": _extract_team_dynamics(dd, team_formation),
        "bootcamp_progression": _extract_bootcamp_progression(team_formation),
        "team_changes": team_changes,
        # Raw narrative fields (AI가 직접 봐야 하는 free-text 필드)
        "narrative": {
            "problem_pain_points": dd.get("problem_pain_points", ""),
            "problem_alternatives": dd.get("problem_current_alternatives", ""),
            "solution_value_proposition": dd.get("solution_value_proposition", ""),
            "solution_why_us": dd.get("solution_why_us", ""),
            "market_tam": dd.get("market_tam", ""),
            "market_tam_rationale": dd.get("market_tam_rationale", ""),
            "market_sam": dd.get("market_sam", ""),
            "market_sam_rationale": dd.get("market_sam_rationale", ""),
            "market_som": dd.get("market_som", ""),
            "market_som_rationale": dd.get("market_som_rationale", ""),
            "market_why_now": dd.get("market_why_now", ""),
            "market_why_here": dd.get("market_why_here", ""),
            "market_why_global": dd.get("market_why_global", ""),
            "competition_differentiators": dd.get("competition_differentiators", ""),
            "competition_positioning": dd.get("competition_positioning", ""),
            "gtm_first_customer": dd.get("gtm_first_customer", ""),
            "bm_pricing": dd.get("bm_pricing", ""),
            "bm_revenue_model": dd.get("bm_revenue_model", ""),
            "bm_has_customers": dd.get("bm_has_customers", ""),
            "team_origin_story": dd.get("team_origin_story", ""),
            "team_gaps": dd.get("team_gaps", ""),
        },
        "competitors": _extract_competitors(dd),
        "solution_features": _parse_json_field(dd, "solution_features"),
    }


def _extract_founders(dd: dict) -> list:
    """team_members JSON → 구조화된 파운더 리스트 (전체 background 보존)."""
    raw = dd.get("team_members", "[]")
    try:
        members = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(members, list):
        return []

    result = []
    for m in members:
        if not isinstance(m, dict):
            continue
        name = (m.get("name") or "").strip()
        role = (m.get("role") or "").strip()
        if not name and not role:
            continue

        bg_full = (m.get("background") or "").strip()
        # background를 문장 단위로 쪼개기 (디테일 보존)
        bg_facts = [
            f.strip()
            for f in re.split(r"[;.]\s+|\n+", bg_full)
            if f.strip() and len(f.strip()) > 5
        ]

        result.append({
            "name": name,
            "role": role,
            "is_external": bool(m.get("is_external", False)),
            "background_full": bg_full,
            "background_facts": bg_facts,
        })
    return result


def _extract_team_dynamics(dd: dict, team_formation: list) -> dict:
    """팀 dynamics 패턴 자동 감지 (married couple, preformed 등)."""
    origin = (dd.get("team_origin_story") or "").lower()
    # 모든 텍스트 blob에서 키워드 검색
    blob_parts = []
    for v in dd.values():
        if isinstance(v, str):
            blob_parts.append(v)
    for row in team_formation:
        if isinstance(row, dict):
            for v in row.values():
                if isinstance(v, str):
                    blob_parts.append(v)
    blob = " ".join(blob_parts).lower()

    return {
        "is_preformed": "preformed" in blob or "pre-formed" in blob or "pre formed" in blob,
        "is_married_couple": (
            "married" in blob
            or "wife" in blob
            or "husband" in blob
            or "couple" in origin
            or "fiancé" in blob
            or "fiancee" in blob
        ),
        "origin_story": dd.get("team_origin_story", ""),
        "team_gaps": dd.get("team_gaps", ""),
    }


def _extract_bootcamp_progression(team_formation: list) -> list:
    """Bootcamp 세션을 시간순으로 정리 + 파트너 이름 추출."""
    progression = []
    for row in team_formation:
        if not isinstance(row, dict):
            continue
        session = (row.get("session_label") or "").strip()
        if not session:
            continue

        # evaluation_notes JSON 파싱 → 파트너별 노트 추출
        notes_raw = row.get("evaluation_notes", "[]")
        notes = []
        try:
            parsed = json.loads(notes_raw) if isinstance(notes_raw, str) else notes_raw
            if isinstance(parsed, list):
                for n in parsed:
                    if not isinstance(n, dict) or not n.get("text"):
                        continue
                    author_email = n.get("author", "")
                    # email → 이름 추출 ("jiho@antler.co" → "Jiho")
                    partner_name = _email_to_name(author_email)
                    notes.append({
                        "partner": partner_name,
                        "text": (n.get("text") or "").strip(),
                        "date": n.get("date", ""),
                        "is_public": bool(n.get("is_public", False)),
                    })
        except (json.JSONDecodeError, TypeError):
            pass

        progression.append({
            "session": session,
            "signal": (row.get("signal") or "").strip(),
            "score": (row.get("evaluation_score") or "").strip(),
            "one_liner": (row.get("one_liner") or "").strip(),
            "trackout_started_at": row.get("trackout_started_at", ""),
            "has_external_member": row.get("has_external_member", ""),
            "notes": notes,
        })
    return progression


def _email_to_name(email: str) -> str:
    """email에서 파트너 이름 추출.

    'jiho.kang@antler.co' → 'Jiho Kang'
    'jaehee@antler.co' → 'JaeHee'
    """
    if not email or "@" not in email:
        return ""
    local = email.split("@")[0]
    # known mapping
    known = {
        "jiho": "Jiho Kang",
        "jiho.kang": "Jiho Kang",
        "jaehee": "JaeHee Chang",
        "jaehee.chang": "JaeHee Chang",
        "gabriel": "Gabriel Jung",
        "gabriel.jung": "Gabriel Jung",
        "roy": "Roy Jang",
        "roy.jang": "Roy Jang",
    }
    return known.get(local.lower(), local.replace(".", " ").title())


def _extract_competitors(dd: dict) -> dict:
    """경쟁사 JSON 파싱 (domestic, global)."""
    return {
        "domestic": _parse_json_field(dd, "competition_domestic"),
        "global": _parse_json_field(dd, "competition_global"),
    }


def _parse_json_field(dd: dict, field: str) -> list:
    """CSV의 JSON 필드 안전 파싱."""
    raw = dd.get(field, "")
    if not raw or raw == "[]":
        return []
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def format_facts_for_prompt(facts: dict) -> str:
    """팩트를 LLM이 읽기 쉬운 markdown 형식으로 포맷팅."""
    lines = []

    # === Founders ===
    lines.append("## FOUNDERS (preserve ALL detail in output)\n")
    for f in facts.get("founders", []):
        role_str = f"({f['role']})" if f.get("role") else ""
        ext_str = " [EXTERNAL]" if f.get("is_external") else ""
        lines.append(f"### {f['name']} {role_str}{ext_str}")
        if f.get("background_facts"):
            lines.append("Background:")
            for fact in f["background_facts"]:
                lines.append(f"  - {fact}")
        elif f.get("background_full"):
            lines.append(f"Background: {f['background_full']}")
        lines.append("")

    # === Team Dynamics ===
    td = facts.get("team_dynamics", {})
    lines.append("## TEAM DYNAMICS")
    lines.append(f"- Preformed team: {'YES' if td.get('is_preformed') else 'No'}")
    lines.append(f"- Married couple: {'YES — emphasize in narrative' if td.get('is_married_couple') else 'No'}")
    if td.get("origin_story"):
        lines.append(f"- Origin story: {td['origin_story'][:500]}")
    if td.get("team_gaps"):
        lines.append(f"- Acknowledged gaps: {td['team_gaps'][:300]}")
    lines.append("")

    # === Bootcamp Progression ===
    lines.append("## BOOTCAMP PROGRESSION (chronological — use for Slide 7 STAGE descriptions)")
    for stage in facts.get("bootcamp_progression", []):
        signal = stage.get("signal", "—")
        score = stage.get("score", "—")
        lines.append(f"### {stage['session']}: signal={signal}, score={score}")
        for note in stage.get("notes", [])[:3]:  # 상위 3개
            lines.append(f"  - [{note['partner']}]: {note['text'][:250]}")
    lines.append("")

    # === Team Changes ===
    if facts.get("team_changes"):
        lines.append("## TEAM CHANGES (member additions/removals)")
        for chg in facts["team_changes"]:
            lines.append(f"- {chg.get('session', '?')}: added={chg.get('added', [])}, removed={chg.get('removed', [])}")
        lines.append("")

    # === Narrative content (raw) ===
    narr = facts.get("narrative", {})
    lines.append("## NARRATIVE FIELDS (raw text from DD Survey)")
    for key, label in [
        ("problem_pain_points", "Problem - Pain"),
        ("problem_alternatives", "Problem - Current Alternatives"),
        ("solution_value_proposition", "Solution - Value Prop"),
        ("solution_why_us", "Solution - Why Us"),
        ("market_tam", "TAM"),
        ("market_tam_rationale", "TAM Rationale"),
        ("market_sam", "SAM"),
        ("market_sam_rationale", "SAM Rationale"),
        ("market_som", "SOM"),
        ("market_som_rationale", "SOM Rationale"),
        ("market_why_now", "Why Now"),
        ("market_why_here", "Why Here"),
        ("market_why_global", "Why Global"),
        ("competition_differentiators", "Differentiators"),
        ("gtm_first_customer", "GTM - First Customer"),
        ("bm_revenue_model", "Revenue Model"),
        ("bm_pricing", "Pricing"),
        ("bm_has_customers", "Has Customers"),
    ]:
        val = (narr.get(key) or "").strip()
        if val:
            lines.append(f"### {label}\n{val[:1500]}\n")

    # === Competitors ===
    comp = facts.get("competitors", {})
    if comp.get("domestic") or comp.get("global"):
        lines.append("## COMPETITORS")
        if comp.get("domestic"):
            lines.append("### Domestic (Korean):")
            for c in comp["domestic"]:
                if isinstance(c, dict):
                    lines.append(f"  - {c.get('name', '?')}: {c.get('difference', '')[:300]}")
        if comp.get("global"):
            lines.append("### Global:")
            for c in comp["global"]:
                if isinstance(c, dict):
                    lines.append(f"  - {c.get('name', '?')}: {c.get('difference', '')[:300]}")
        lines.append("")

    return "\n".join(lines)
