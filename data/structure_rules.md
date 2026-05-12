# Structure Rules — Antler Investment Memo v2

14개 완성본 분석 결과 도출된 **반드시 지켜야 할 규칙**들. LLM이 콘텐츠 생성 시 매번 참조함.

---

## 🌐 Rule 1: All content in English

**모든 콘텐츠는 영문으로 작성**. (음슴체 한국어 ❌)

회사명만 한국어 그대로 사용 가능: "NAMATAN", "LAB OF APPAREL".

### Examples
- ❌ "스페셜티 커피 추출 표준화 하드웨어 솔루션"
- ✅ "AI-Native Fintech OS for Youth Sports"
- ✅ "Audit-Led Mechanical Royalty Recovery for Songwriters"
- ✅ "AI Drift Control for Polymer Manufacturing"

### Pattern for ONELINER
- "AI [function] for [market]"
- "[Brand]: [function description]"
- "[Method] [solution] for [target customer]"

---

## 📊 Rule 2: SOM = revenue, NOT market pool size

**SOM은 회사가 capture할 수 있는 실제 매출 규모**. 시장 풀 사이즈 ❌.

### Examples
- ✅ handa: "$1.5-6.0M (DD bottom-up: 300-700 recoveries × $1K-1.5K + 150-500 admin × $300-900)"
- ✅ Nacre: "$60M (capturing software budgets in defined industrial clusters)"
- ✅ Lab of Apparel: "$50M (5% take rate from $1B GMV)"
- ❌ "$1.5B (전체 MLC 분배 풀)"

### Rationale 형식
산식 명시: `[customer count] × [unit price] × [conversion rate] = [SOM]`

---

## 📚 Rule 3: All numbers must cite sources

모든 수치는 **출처 명기**. 출처 없는 수치는 신뢰성 ❌.

### Approved sources
- McKinsey, Bain, BCG (consulting)
- Goldman Sachs, Morgan Stanley (investment banks)
- CISAC, MLC, IFPI, RIAA (industry bodies)
- Statista, Mordor Intelligence (market research)
- 통계청, KDI (Korean public data)
- Crunchbase, PitchBook (private market data)

### Examples
- ✅ "$10.4B SAM (CISAC 2024)"
- ✅ "12,242 cafe closures in 2024 (통계청/KDI)"
- ✅ "Global coffee market $223B → $356B (Mordor Intelligence, 2024)"
- ❌ "거대한 시장임"
- ❌ "$15B" (출처 없음)

---

## 🔍 Rule 4: DD critical analysis — challenge founder claims

**Founder가 주장하는 숫자를 그대로 받지 말 것.** 산식 직접 검증.

### Examples (handa from JaeHee)
- Founder claim: "$840K Y1 target"
- DD analysis: "500 leads × 60% × $1,497 ACV = $449K, not $840K. Conservative DD estimate is $350-450K."

### Rules for SUMMARY_DESC and IMPROVEMENT_*_DESC
- Identify arithmetic gaps in founder projections
- Validate market sizing claims against external sources
- Surface hidden risks (e.g., "MLC pool quality declining — 95%+ of unmatched <$1")
- Compare to industry benchmarks

---

## 🚦 Rule 5: Bootcamp signals — partner names + scores explicit

Slide 7 (Program Trajectory)에 **반드시 포함**:
- Bootcamp 시그널: Red / Yellow / Green
- 파트너 이름 (Jiho, Jaehee, Gabriel)
- 점수 (1-9 scale)

### Example structure
```
① Program Start — [team formation status]
② Team Building — [team binding process]
③ Team Bonding — [trust foundation]
④ Idea Validation — Bootcamp 1 [Signal] from [Partner]; [feedback]
⑤ Bootcamp — Bootcamp [N] scored [X]/9 from [Partner]; [validation]
⑥ Trackout — [trackout signals + IC sponsor confirmation]
⑦ Post Trackout — [latest traction + IC readiness]
```

### Examples
- "Bootcamp 1 Red signal flagged broad scope and unclear problem"
- "Bootcamp 3-1 Green signal from Jaehee; praised MLC focus"
- "Group Office Hour scored 9 from Jaehee; JaeHee Chang confirmed as IC sponsor"

---

## 👥 Rule 6: Track team changes from team_formation

`team_formation.csv`의 `session_label`을 시간순으로 정렬해서 **member_1~4 변화 추적**.

### Track these events
- 멤버 추가 (예: Bootcamp 2에서 Daniel Kim 합류)
- 멤버 이탈 (예: handa의 Daniel Kim이 Trackout 중 이탈)
- 외부 파운더 합류 (예: Vahid Najafi external CTO)

### How to surface
- Slide 7 (Program Trajectory): 변화 시점·이유 명시
- Slide 6 (Team): 현재 시점 정확한 멤버 + commitment level
- Slide 9 (IMPROVEMENT): 이탈·공석으로 인한 리스크

---

## 🏢 Rule 7: Competition — categories, not domestic/global split

경쟁사 4개를 **카테고리별 상위 4개**로 선정. 한국/글로벌 강제 구분 ❌.

### Format per competitor
```
{Company} ({Country})
{Funding Stage} / {Founded Year}
{Description: strength acknowledgment + weakness/our advantage}
```

### Examples (handa from JaeHee)
1. **Songtrust (US)** — Acquired by Virgin Music Group at $775M / 2011 — Legacy publishing admin with 445K writers; strongest incumbent but no proactive audit
2. **Notes.fm (US)** — Pre-Seed / 2024 — Closest competitor in audit-first UX; subscription model $96+/year
3. **Claimy (France)** — Pre-Seed / 2023 — AI audit/claims for B2B publishers; proves audit-led category exists
4. **Muserk (US)** — Private / 2017 — AI-driven global rights admin; B2B infrastructure layer (complementary)

### Rules
- 4 competitors, ranked by relevance
- Funding format: `{Stage} / {Year}` (Pre-Seed, Seed, Series A/B, Acquisition, Private, Public, Acquired by X at $XM)
- Description: 1 sentence covering strength + our differentiator
- Country: 2-letter code or full name (US, UK, Korea, France, etc.)

---

## 💵 Rule 8: Pricing/BM — explicit ACV and revenue model

### Pricing must include
- 가격 단위: subscription/commission/per-unit
- 비교: 경쟁사 가격 대비
- ACV (Annual Contract Value) 명시

### Examples
- ✅ "20% commission on recovered royalties; zero upfront cost"
- ✅ "First-year ACV ~$1,497; 2-year contract with rollover"
- ✅ "1.7% net take rate on transactions; scales with GMV"
- ❌ "구독 모델로 수익 창출"

### Business Model must include
- 수익 스트림 (single vs dual)
- 단위 경제성 (gross margin if available)

---

## 📈 Rule 9: Build to Scale — 3 specific levers

3가지 확장 동력을 **구체적으로** 명시:

### Common patterns observed
1. **Sub-linear operational growth** (AI/automation으로 인력 비례 증가 ❌)
2. **Low-CAC distribution flywheel** (community/word-of-mouth/referrals)
3. **Territory or category expansion** (글로벌·인접 시장)

### Examples (handa from JaeHee)
- "Sub-Linear Operational Growth: AI-native registration pipeline scales without proportional headcount"
- "Low-CAC Community Flywheel: 200+ producer communities, viral audit tool"
- "Territory Expansion: Sequential rollout across global societies reuses core engine"

---

## 🎯 Rule 10: Investor Assessment — 6 categories with letter grades

Slide 10에는 6개 카테고리 등급 + 2 bullet rationale.

### Categories (fixed order)
1. Market Size
2. Competition
3. Defensibility
4. Commercial Traction
5. Global Scalability
6. Team

### Grade scale
- **A / A-** — Strong, high conviction
- **B+ / B / B-** — Moderate, conditional
- **C+ / C** — Weak, significant concerns
- **D** — Pass

### Each rationale: 1-2 bullets
- Bullet 1: Positive observation (with specifics)
- Bullet 2: Concern or qualification (with specifics)

### Overall Summary (last paragraph)
- 1-2 sentences synthesizing the bet
- Often ends with "core risk: [X]" or "core bet: [X]"

### Examples (Namatan from Jiho)
> "Large, fast-growing market with a clear wedge, but a crowded category where differentiation is not defensible at the technology level. Core bet is on execution: converting early B2B interest into real usage and proving repeatable user behavior, not just measurement accuracy."

---

## 📝 Rule 11: Slide 9 — Strengths and Improvements with • markers

### Format
```
● [Strength title — 25 chars]
[Strength description — 80-120 chars with specifics]

● [Improvement title — 25 chars]
[Improvement description — 80-120 chars with specifics]
```

### Strengths (4 items) — what's working
- Team composition advantages
- PMF signals (specific numbers)
- Defensibility lenses (data moat, lock-in, etc.)
- Strategic positioning

### Improvements (4 items) — honest gaps
- Team gaps (e.g., "solo founder", "CMO empty")
- Market/traction gaps (e.g., "no paid customers")
- Defensibility concerns (e.g., "tech moat fragile")
- Execution risks (e.g., "publisher license pending")

### FOUNDER_EQUITY (separate field)
지분 구조 + 결정 상태:
- "50/50 with co-founder, finalized post-Antler investment"
- "No co-founder yet, equity structure undetermined"
- "60/40 split reflecting CEO leadership; vesting 4-year"

---

## 🔬 Rule 12: Domain-specific terminology

산업별 전문 용어 정확히 사용:

### Music (handa)
- MLC (Mechanical Licensing Collective)
- CWR (Common Works Registration)
- ISRC (International Standard Recording Code)
- PRS/MCPS, KOMCA, GEMA, JASRAC, SACEM, APRA/AMCOS
- Mechanical/performance/sync royalties
- Q-Grader (coffee), CISAC

### Manufacturing (Nacre, AutoLabs)
- DCS (Distributed Control System)
- MES (Manufacturing Execution System)
- SPC (Statistical Process Control)
- TRL (Technology Readiness Level)
- BOM (Bill of Materials)

### B2B SaaS
- ACV (Annual Contract Value)
- LTV / CAC ratio
- GMV (Gross Merchandise Value)
- PMF (Product-Market Fit)

---

## ✅ Pre-flight Checklist

LLM이 결과물 출력 전 자동 체크:

- [ ] All content in English (except company name proper nouns)?
- [ ] SOM defined as company-capturable revenue (with formula)?
- [ ] Every dollar amount cites a source?
- [ ] Founder claims arithmetically verified?
- [ ] Bootcamp signals (Red/Green) + partner names + scores in Slide 7?
- [ ] Team changes from team_formation tracked?
- [ ] 4 competitors with `Stage / Year` format?
- [ ] ACV explicit in Pricing?
- [ ] 3 specific Build to Scale levers?
- [ ] 6 Investor Assessment grades + Overall Summary?
- [ ] Slide 9 has 4 strengths + 4 improvements with • markers?
- [ ] Domain-specific terminology used correctly?

체크리스트 모두 통과하지 않으면 재생성.

---

## 🎓 Style References (3 partners)

각 파트너 스타일 차이를 인지:

### Jiho (실행/시장 중심)
- 직설적, 정량적
- "1.7% take rate", "$3K-3.5K ACV" 같은 구체적 수치 강조
- Examples: 1-1 Scout, 1-4 FanDoor, 2-1 Namatan, 2-6 Lab of Apparel, 2-7 AutoLabs

### JaeHee (Deep DD)
- 산식 검증 강박
- 솔직한 risk 표기 ("$840K target → $449K calculation")
- Examples: 1-2 Genesis Studio, 2-2 handa, 2-4 Loop

### Gabriel (산업 도메인 깊이)
- 제조·B2B 산업 전문성
- 구조적 분석
- Examples: 1-3 Nacre, 1-5 VANDRO, 1-6 AHEADFATE, 1-7 UOS, 2-3 INSUPIRE, 2-5 Bigtablet

→ 새 보고서 생성 시 팀 산업·특성에 맞춰 적절한 파트너 스타일 참고.
