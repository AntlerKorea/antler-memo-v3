# Placeholder Keys — 마스터 문서

투자심의보고서 템플릿(`DD_Template_*.pptx`)에 박힌 모든 placeholder 키 정의.

## 전체 요약

| 슬라이드 | placeholder 수 | 비고 |
|---|---|---|
| 1. Cover | 3 | |
| 2. Idea (Problem/Solution/Value) | 9 | |
| 3. Market 1/3 (TAM·SAM·SOM + Why) | 12 | |
| 4. Market 2/3 (Competition) | 20 | 경쟁사 4개 × 4필드 + DIFF 4개 |
| 5. Market 3/3 (GTM·Pricing·BM·Scale) | 10 | |
| 6. Team 1/4 (Composition) | 11 (2인용) / 15 (3인용) | |
| 7. Team 2/4 (Program Trajectory) | 7 | |
| 8. Team 3/4 (Evaluation) | 12 | SCORE 6 + RATIONALE 6 |
| 9. Team 4/4 (Summary) | 17 | STRENGTH 4×2 + IMPROVEMENT 4×2 + EQUITY |
| 10. Investor Assessment | 2 | |
| 11. Closing | 0 | |

**총 합계**: 2인용 **103개** / 3인용 **107개**

## 컨벤션

- **`{{KEY}}` 형식** — 영문 대문자 + 언더스코어 + 숫자
- **단일 run으로 박혀야 함** — `verify.py`로 검증
- **고정 텍스트는 placeholder 아님** — 서브헤더·헤더는 템플릿에 직접 입력
- **권장 글자수**는 박스 크기 기준 가이드 (엄격한 제한 아님)

---

## Slide 1: Cover

| Key | 용도 | 권장 글자수 | 예시 |
|---|---|---|---|
| `{{COMPANY_NAME}}` | 회사명 | ~15자 | "Namatan" |
| `{{ONELINER}}` | 한 줄 요약 (한국어) | ~30자 | "AI 기반 스마트폰 체성분 분석 플랫폼" |
| `{{COHORT}}` | 코호트 | ~5자 | "KOR8" |

---

## Slide 2: Idea (Problem · Solution · Value Proposition)

### Problem (3 paragraphs)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{PROBLEM_1}}` | ~100자 | 시장/고객 pain point |
| `{{PROBLEM_2}}` | ~100자 | 기존 대안의 한계 |
| `{{PROBLEM_3}}` | ~100자 | 결과적 비효율 |

### Solution (3 paragraphs)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{SOLUTION_1}}` | ~95자 | 핵심 솔루션 기능 |
| `{{SOLUTION_2}}` | ~95자 | 기술 메커니즘 |
| `{{SOLUTION_3}}` | ~95자 | 통합 가치 |

### Value Proposition (3 paragraphs)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{VALUE_1}}` | ~70자 | 차별화 가치 1 |
| `{{VALUE_2}}` | ~70자 | 차별화 가치 2 |
| `{{VALUE_3}}` | ~70자 | 차별화 가치 3 |

---

## Slide 3: Market 1/3 (TAM·SAM·SOM + Why Now)

### TAM/SAM/SOM (3 set × 3 fields = 9 placeholders)

| Key | 용도 | 예시 |
|---|---|---|
| `{{TAM_AMOUNT}}` | TAM 금액 | "$232B" 또는 "152조 원" |
| `{{TAM_DESC}}` | TAM 설명 (~40자) | "글로벌 커피 시장 규모" |
| `{{TAM_RATIONALE}}` | TAM 산출근거 (~140자) | "북미 + APEC + 유럽 합산 ..." |
| `{{SAM_AMOUNT}}` | SAM 금액 | "$10B" |
| `{{SAM_DESC}}` | SAM 설명 (~40자) | |
| `{{SAM_RATIONALE}}` | SAM 산출근거 (~140자) | |
| `{{SOM_AMOUNT}}` | SOM 금액 | "$570M" |
| `{{SOM_DESC}}` | SOM 설명 (~40자) | |
| `{{SOM_RATIONALE}}` | SOM 산출근거 (~140자) | |

### Why Korea / Why Now / Why Global (3 placeholders)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{WHY_KOREA}}` | ~70자 | 한국이 적합한 이유 |
| `{{WHY_NOW}}` | ~70자 | 지금이 타이밍인 이유 |
| `{{WHY_GLOBAL}}` | ~70자 | 글로벌 확장 가능성 |

**고정 텍스트** (템플릿에 박아둠): "Why Korea (또는 Why Here)", "Why Now", "Why Global"

---

## Slide 4: Market 2/3 (Competition)

### 경쟁사 4개 (각 4필드 × 4 = 16 placeholders)

배치 규칙: 한국 회사는 위(Competitor 1, 2), 글로벌 회사는 아래(Competitor 3, 4).

| Competitor | NAME | COUNTRY | FUNDING | DESC |
|---|---|---|---|---|
| 1 (한국) | `{{COMP1_NAME}}` | `{{COMP1_COUNTRY}}` | `{{COMP1_FUNDING}}` | `{{COMP1_DESC}}` |
| 2 (한국) | `{{COMP2_NAME}}` | `{{COMP2_COUNTRY}}` | `{{COMP2_FUNDING}}` | `{{COMP2_DESC}}` |
| 3 (글로벌) | `{{COMP3_NAME}}` | `{{COMP3_COUNTRY}}` | `{{COMP3_FUNDING}}` | `{{COMP3_DESC}}` |
| 4 (글로벌) | `{{COMP4_NAME}}` | `{{COMP4_COUNTRY}}` | `{{COMP4_FUNDING}}` | `{{COMP4_DESC}}` |

권장 글자수: NAME ~25자, COUNTRY ~10자 ("KR"/"US"), FUNDING ~18자, DESC ~55자.

### Key Differentiator (4 paragraphs)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{DIFF_1}}` | ~100자 | 기술적 차별화 |
| `{{DIFF_2}}` | ~100자 | 비즈니스 모델 차별화 |
| `{{DIFF_3}}` | ~100자 | 시장 포지셔닝 |
| `{{DIFF_4}}` | ~100자 | 확장성/방어력 |

---

## Slide 5: Market 3/3 (GTM · Pricing · BM · Scale)

### GTM Stage Breakdown (3 paragraphs)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{GTM_1}}` | ~80자 | Phase 1 (B2B 진입) |
| `{{GTM_2}}` | ~80자 | Phase 2 (B2C 시장 검증) |
| `{{GTM_3}}` | ~80자 | Phase 3 (양산 + 해외) |

**고정 텍스트**: "Phase 1:", "Phase 2:", "Phase 3:"

### Pricing (2 paragraphs)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{PRICING_1}}` | ~55자 | B2B 가격 모델 |
| `{{PRICING_2}}` | ~55자 | B2C 가격 모델 |

### Business Model (2 paragraphs)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{BM_1}}` | ~55자 | 수익 구조 |
| `{{BM_2}}` | ~55자 | 마진/유닛 이코노믹스 |

### Build to Scale (3 paragraphs)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{SCALE_1}}` | ~80자 | 시장 확장 (글로벌·카테고리) |
| `{{SCALE_2}}` | ~80자 | 채널 다각화 |
| `{{SCALE_3}}` | ~80자 | Tech moat / 데이터 자산 |

---

## Slide 6: Team 1/4 (Composition & Roles)

### Why This Team (3 paragraphs)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{WHY_TEAM_1}}` | ~100자 | 역할 매핑 / 팀 구조 |
| `{{WHY_TEAM_2}}` | ~100자 | 도메인 전문성 |
| `{{WHY_TEAM_3}}` | ~100자 | 실행력 / PMF 시그널 |

### Founder 1 (CEO) — 4 paragraphs

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{FOUNDER_1_HEADING}}` | ~20자 | "[이름] (CEO)" — 볼드 |
| `{{FOUNDER_1_BG_1}}` | ~35자 | 학력/경력 1 |
| `{{FOUNDER_1_BG_2}}` | ~35자 | 학력/경력 2 |
| `{{FOUNDER_1_BG_3}}` | ~30자 | 핵심 책임/역할 |

### Founder 2 (COO/CTO/CPO) — 4 paragraphs

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{FOUNDER_2_HEADING}}` | ~20자 | "[이름] (직함)" — 볼드 |
| `{{FOUNDER_2_BG_1}}` | ~35자 | 학력/경력 1 |
| `{{FOUNDER_2_BG_2}}` | ~35자 | 학력/경력 2 |
| `{{FOUNDER_2_BG_3}}` | ~30자 | 핵심 책임/역할 |

### Founder 3 — **3인용 템플릿에만**

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{FOUNDER_3_HEADING}}` | ~20자 | "[이름] (직함)" — 볼드 |
| `{{FOUNDER_3_BG_1}}` | ~35자 | 학력/경력 1 |
| `{{FOUNDER_3_BG_2}}` | ~35자 | 학력/경력 2 |
| `{{FOUNDER_3_BG_3}}` | ~30자 | 핵심 책임/역할 |

### 파운더 사진 (placeholder 아님)

| 슬롯 | 미디어 파일 | 비고 |
|---|---|---|
| Founder 1 사진 | `image13.png` | 2인용/3인용 공통 |
| Founder 2 사진 | `image14.png` | 2인용/3인용 공통 |
| Founder 3 사진 | `image15.png` | **3인용만** |

이미지는 `render.py`가 photos_dir에서 이름 매칭으로 자동 교체.

---

## Slide 7: Team 2/4 (Program Trajectory / Timeline)

### 8개 스테이지 타이틀 — **고정 텍스트 (수정 금지)**

```
① Program Start
② Team Building
③ Team Bonding
④ Idea Validation
⑤ Bootcamp
⑥ Trackout
⑦ Post Trackout
```

→ 7개 단계 (Pre-IC 제거됨)

### Description 7개

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{STAGE_1_DESC}}` | ~80자 | 프로그램 시작 시점 팀 상태 |
| `{{STAGE_2_DESC}}` | ~80자 | 팀 빌딩 과정 |
| `{{STAGE_3_DESC}}` | ~80자 | 팀 결합력 |
| `{{STAGE_4_DESC}}` | ~80자 | 초기 아이디어 검증 |
| `{{STAGE_5_DESC}}` | ~80자 | 부트캠프 성과 |
| `{{STAGE_6_DESC}}` | ~80자 | 트랙아웃 결과 |
| `{{STAGE_7_DESC}}` | ~80자 | 트랙아웃 이후 진척 |

---

## Slide 8: Team 3/4 (Evaluation)

### 6개 평가 카테고리 (각 SCORE + RATIONALE)

| Category (고정) | SCORE | RATIONALE |
|---|---|---|
| Team Cohesion | `{{SCORE_1}}` | `{{RATIONALE_1}}` |
| Execution | `{{SCORE_2}}` | `{{RATIONALE_2}}` |
| Resilience | `{{SCORE_3}}` | `{{RATIONALE_3}}` |
| Market Understanding | `{{SCORE_4}}` | `{{RATIONALE_4}}` |
| Technology | `{{SCORE_5}}` | `{{RATIONALE_5}}` |
| Innovation | `{{SCORE_6}}` | `{{RATIONALE_6}}` |

권장 글자수: SCORE ~5자 (예: "3.5/5" 또는 "B+"), RATIONALE ~80자

### 레이더차트 이미지 (placeholder 아님)

- 미디어 파일: `image15.png` (슬라이드 8)
- `render.py`가 별도 chart_path 인자로 PNG 교체

---

## Slide 9: Team 4/4 (Summary)

### Strengths (4 항목 × 2필드 = 8 placeholders)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{STRENGTH_1}}` | ~25자 | 강점 제목 1 |
| `{{STRENGTH_1_DESC}}` | ~120자 | 강점 설명 1 |
| `{{STRENGTH_2}}` | ~25자 | 강점 제목 2 |
| `{{STRENGTH_2_DESC}}` | ~120자 | 강점 설명 2 |
| `{{STRENGTH_3}}` | ~25자 | 강점 제목 3 |
| `{{STRENGTH_3_DESC}}` | ~120자 | 강점 설명 3 |
| `{{STRENGTH_4}}` | ~25자 | 강점 제목 4 |
| `{{STRENGTH_4_DESC}}` | ~120자 | 강점 설명 4 |

### Areas for Improvement (4 항목 × 2필드 = 8 placeholders)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{IMPROVEMENT_1}}` | ~25자 | 보완점 제목 1 |
| `{{IMPROVEMENT_1_DESC}}` | ~120자 | 보완점 설명 1 |
| `{{IMPROVEMENT_2}}` | ~25자 | 보완점 제목 2 |
| `{{IMPROVEMENT_2_DESC}}` | ~120자 | 보완점 설명 2 |
| `{{IMPROVEMENT_3}}` | ~25자 | 보완점 제목 3 |
| `{{IMPROVEMENT_3_DESC}}` | ~120자 | 보완점 설명 3 |
| `{{IMPROVEMENT_4}}` | ~25자 | 보완점 제목 4 |
| `{{IMPROVEMENT_4_DESC}}` | ~120자 | 보완점 설명 4 |

### Founder Equity Structure (1 placeholder)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{FOUNDER_EQUITY}}` | ~150자 | 파운더 지분 구조 분석 (Pareto 명확성, 인센티브 정렬 등) |

---

## Slide 10: Investor Assessment

### 6개 카테고리 평가표 — **고정 텍스트**

```
Market Size · Competition · Defensibility · Commercial Traction · Global Scalability · Team
```

→ 평가표는 별도 채우기 (현재 템플릿에선 Slide 8 SCORE와 별도 영역. 사용 방식은 사용자 결정).

### Overall Summary + Key Risks (2 placeholders)

| Key | 권장 글자수 | 내용 |
|---|---|---|
| `{{SUMMARY_DESC}}` | ~200자 | 종합 의견 — 핵심 베팅 / 시나리오 / 멀티플 가능성 |
| `{{RISKS_DESC}}` | ~200자 | 핵심 리스크 — 검증 필요 항목 + 마일스톤 |

---

## Slide 11: Closing

placeholder 없음. 그대로 둠.

---

## 작성 가이드라인

### 공통
- **음슴체** (~함/~임/~됨/~있음) — `references/content_guidelines.md` 참조
- **구체성** — 추상 표현 대신 수치/회사명/기술명
- **권장 글자수 준수** — 박스 넘침 방지

### 검증
- `python scripts/verify.py output/팀이름.pptx`
- 깨진 placeholder 0개, 의도치 않은 미치환 0개여야 PASS

### 콘텐츠 JSON 예시
```json
{
  "_meta": {
    "team_name": "Namatan",
    "version": "v1.0"
  },
  "COMPANY_NAME": "Namatan",
  "ONELINER": "AI 기반 스마트폰 체성분 분석 플랫폼",
  "COHORT": "KOR8",
  "PROBLEM_1": "기존 InBody는 하드웨어 의존으로 ...",
  ...
}
```

`_`로 시작하는 키는 `render.py`가 무시 (메타데이터용).
