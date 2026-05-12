# Antler Memo v2

Antler Korea 투자심의보고서 자동 생성 시스템 (Placeholder 기반).

## 빠른 시작

### 1. 콘텐츠 JSON 작성

`references/placeholder_keys.md` 보면서 모든 placeholder 키 채우기:

```json
{
  "_meta": { "team_name": "Namatan" },
  "COMPANY_NAME": "Namatan",
  "ONELINER": "AI 기반 스마트폰 체성분 분석 플랫폼",
  "COHORT": "KOR8",
  "PROBLEM_1": "...",
  "PROBLEM_2": "...",
  "...": "..."
}
```

### 2. 렌더링

```bash
python scripts/render.py \
    --template templates/DD_Template_2person.pptx \
    --content my_content.json \
    --output output/Namatan_DD.pptx
```

### 3. 검증

```bash
python scripts/verify.py output/Namatan_DD.pptx
```

## 옵션

### 파운더 사진 자동 교체

`founder_photos/` 폴더에 `{이름}.png` 형식으로 사진 준비:

```
founder_photos/
├── 김영언.png
├── 방원민.png
└── 김태준.png
```

```bash
python scripts/render.py \
    --template templates/DD_Template_3person.pptx \
    --content content.json \
    --output output/CoffeeCherry_DD.pptx \
    --photos-dir founder_photos/
```

`render.py`가 `FOUNDER_*_HEADING`에서 이름 추출해서 자동 매칭.

### 레이더차트 교체

슬라이드 8의 평가 차트(`image15.png`)를 별도 PNG로 교체:

```bash
python scripts/render.py \
    --template templates/DD_Template_2person.pptx \
    --content content.json \
    --output output/Namatan_DD.pptx \
    --chart radar_charts/Namatan.png
```

차트 PNG는 별도 스크립트로 생성 (matplotlib·plotly 등).

## 폴더 구조

```
antler-memo-v2/
├── SKILL.md                     # Claude/Cowork용 스킬 정의
├── README.md                    # 이 파일
├── scripts/
│   ├── render.py                # 메인 렌더러
│   └── verify.py                # 검증 도구
├── references/
│   ├── placeholder_keys.md      # 모든 placeholder 키 마스터 문서
│   ├── content_guidelines.md    # 콘텐츠 작성 규칙
│   └── data_sources.md          # CSV 데이터 소스 구조
├── templates/
│   ├── DD_Template_2person.pptx # 2인 팀용
│   └── DD_Template_3person.pptx # 3인 팀용 (TBD)
├── assets/
│   └── person_icon.png          # 사진 폴백
└── examples/
    └── (콘텐츠 JSON 예시)
```

## 검증 출력 예시

### Pass

```
📄 파일: output/Namatan_DD.pptx
   크기: 70.3 MB

✅ 깨진 placeholder 조각 없음
✅ 모든 placeholder 치환 완료

==================================================
✅ 종합 결과: PASS
```

### Fail (미치환)

```
📄 파일: output/Namatan_DD.pptx

✅ 깨진 placeholder 조각 없음
⚠️  미치환된 placeholder (3개):
      {{BM_2}}
      {{SCALE_3}}
      {{FOUNDER_EQUITY}}

   💡 의도적으로 비워둔 슬라이드(예: 7~10)면 OK
   💡 그렇지 않으면 콘텐츠 JSON에 해당 키 추가 후 재렌더링

==================================================
❌ 종합 결과: FAIL
```

### Fail (깨진 조각)

```
📄 파일: templates/DD_Template_broken.pptx

❌ 깨진 placeholder 조각 발견 (3개):
   slide9.xml:
      run #18: '{{STRENGTH_2_'
      run #19: 'DESC'
      run #20: '}}'

   💡 해결: 해당 placeholder를 통째로 지우고 한 번에 다시 타이핑
```

## 의존성

- Python 3.10+
- 외부 라이브러리 불필요 (표준 라이브러리만 사용)

## 트러블슈팅

### Q. 깨진 placeholder가 자꾸 생겨요

A. Google Slides에서 placeholder 텍스트를 부분 수정하면 run splitting 발생.  
   **통째로 지우고 한 번에 다시 입력**해야 함.  
   `verify.py`로 매번 확인 권장.

### Q. 사진이 자동 교체 안 돼요

A. `FOUNDER_*_HEADING`의 첫 단어와 photos_dir의 파일명이 일치해야 함.  
   예: `"김영언 (CEO)"` → `김영언.png`

### Q. 한글이 깨져 보여요

A. 폰트가 Arial로 통일되는데, Arial은 시스템 fallback으로 한글을 처리함.  
   PowerPoint/Keynote 환경에 따라 달라질 수 있음.  
   다른 폰트 강제하려면 `render.py`의 `enforce_arial` 함수 수정.

## 다음 단계

- [ ] 3인용 템플릿 (`DD_Template_3person.pptx`)
- [ ] 레이더차트 자동 생성 (`generate_radar.py`)
- [ ] CSV → JSON 자동 추출 (`extract.py`)
- [ ] Claude API 콘텐츠 생성 (`generate.py`)
- [ ] CLI 통합 (`memo.py`)
