---
name: lit-review
description: 박사논문(한국 섬유패션산업의 지속가능한 시장가치 창출 메커니즘)을 위한 문헌리서치 자동화 skill. 논문(PDF/링크/텍스트/초록/서지정보)을 100점 평가표로 채점하고, 85점 이상이면 A4 5쪽 표준 요약을 생성해 Study 1~4에 연결하며, research/db/papers.csv에 누적한다. 매일 신규 논문 1편을 찾아 5개 필드(제목/저널/연도/인용수/초록)를 카카오톡으로, 5쪽 요약을 Gmail로 보내는 일일 브리핑 모드도 지원한다. "논문 요약", "논문 평가", "문헌 리뷰", "오늘의 논문 찾아줘", "모닝 브리핑", "카카오톡으로 보내줘", "주간 다이제스트" 같은 요청에 사용한다.
---

# 문헌리서치 자동화 (lit-review)

이 skill 하나가 평가 → 요약 → DB 적재 → 일일 발견 → 카카오톡/Gmail 발송 → 주간·월간 롤업까지 전부 담당하는 통합 파이프라인이다. 이전에는 평가(정밀 채점 엔진)와 요약·발송(전체 워크플로)이 서로 다른 두 스킬로 나뉘어 있었는데, 이 문서에서 하나로 합쳤다 — §2 채점 엔진은 조작적으로 정의된 버전을, §3~§9 워크플로는 end-to-end 버전을 그대로 가져와 합쳤다.

## 0. 참조 문서와 우선순위

- **`연구계획서.md`** (저장소 루트) — 배경·RQ·이론·Study 1~4 설계·문헌리서치 전략의 서술형 마스터 문서. 사람이 읽는 기준.
- **`docs/박사학위논문 연구계획서 초안.pdf`** — 연구 내용(주제·RQ·Study·변수·가설·설계)의 **원본 기준 문서**.
- **`docs/박사논문_주제선정_연구계획_리서치자동화_통합보고서.docx`** — 리서치 자동화 운영안(파이프라인·평가표·저널 Watchlist·키워드·요약 템플릿)의 출처.
- **`docs/seed_papers.md`** — PDF 배경에서 인용된 선행연구 6편(서지정보 미확인) — 발견 단계의 검색 단서.

**충돌 규칙**: `연구계획서.md`(사람이 읽는 요약본)와 `docs/`의 원본 PDF/DOCX 내용이 어긋나면 **PDF가 우선**이다(연구 내용 기준). 자동화 운영안(평가표·파이프라인·키워드)이 어긋나면 DOCX와 이 skill 파일 중 **이 skill 파일이 우선**이다 — 조작적 정의는 여기서만 갱신한다. `연구계획서.md`는 문서가 스킬을 가리키도록 유지하고, 세부 채점 로직을 복제하지 않는다(§2 참고).

## 1. Study 1~4 기준표와 탐지 키워드

| Study | 분석단위 | 이론 | 탐지 키워드 |
|---|---|---|---|
| **Study 1. 패션 리세일과 지속가능 소비의 역설** | 소비자 (B2C) | Moral Licensing, Rebound Effect | fashion resale, secondhand clothing, recommerce, circular consumption, substitution effect, rebound effect, moral licensing, shopping frequency, clothing lifespan, disposal behavior, wardrobe turnover |
| **Study 2. 지속가능성 커뮤니케이션과 소비자 신뢰** | B2C | Signaling | greenwashing, sustainability claims, environmental claims, claim specificity, eco-label, third-party certification, claim credibility, brand trust, consumer trust |
| **Study 3. 지속가능 섬유소재의 Ingredient Branding** | B2B2C | Brand Equity, Signaling | ingredient branding, ingredient brand equity, host brand equity, textile brand, material branding, brand fit, quality signal, value transfer, co-branding, willingness to pay |
| **Study 4. 지속가능 공급망과 Traceability** | B2B | Signaling, Trust, Relationship Marketing | textile traceability, fashion supply chain transparency, information credibility, digital product passport, blockchain, chain of custody, inter-firm trust, relationship commitment |

보조 클러스터: **Consumer gap**(attitude-behavior gap, intention-behavior gap, identity conflict, price sensitivity, green skepticism) → Study 1·2 보조 / **Umbrella**(sustainable market value creation, sustainable fashion marketing, firm value, sustainable competitive advantage) → 4개 Study 공통 배경.

### Study별 연구모형·조절변수·가설 (관련성 판단 대조표)

**Study 1** — 경로① Resale Participation → Perceived Environmental Contribution → Moral Licensing → New Clothing Purchase / 경로② Resale Participation → Reduced Effective Cost of Fashion Consumption → Shopping Frequency → Total Clothing Consumption. 행동변수: 신규 실제구매량·중고구매량·중고판매량·구매빈도·보유기간·처분빈도. 조절: Fashion Involvement, Environmental Consciousness, Price Sensitivity, Age/Generation. 가설 H1~H5(§본문 표 참고, `연구계획서.md` §7).

**Study 2** — 2×2: Sustainability Claim(모호 vs 구체) × Certification(없음 vs 제3자 인증). 종속변수: Perceived Greenwashing, Claim Credibility, Brand Trust, Purchase Intention, WTP, Brand Attitude. 가설 H1~H5.

**Study 3** — Ingredient Brand Equity → Perceived Sustainability → Perceived Quality → Host Brand Equity → Purchase Intention/WTP (조절: Brand Fit). 가설 H1~H5.

**Study 4** — Traceability → Information Transparency → Information Credibility → Inter-firm Trust → Relationship Commitment → Sustainable Supply Chain Performance. 조절: 기업규모·수출비중·글로벌바이어거래·ESG역량·공급망복잡성·디지털역량. 가설은 연구계획서에 명시 없음 → 경로 대조로 판정.

## 2. 100점 평가 (조작적 정의)

### 입력

논문마다 최소 5개 필드를 받는다: **제목 / 저널 / 연도 / 인용수 / 초록**(가능하면 저자·DOI·국가·표본수도). **입력에 없는 정보는 추측하지 않는다** — 저자, 표본, 국가, 결과 수치는 주어진 자료에 적힌 것만 근거로 쓴다. 필드가 비어 있으면 "입력 누락"에 표시하고 §2.7 "누락 시 처리"를 따른다.

기준연도 = 평가를 실행하는 날의 연도. 경과연수 = 기준연도 − 발행연도. 연평균 인용 = 인용수 ÷ max(1, 경과연수).

### 2.1 박사논문 직접 관련성 (30점)

§1의 기준표·연구모형·가설과 초록을 대조한다.

| 점수 | 기준 |
|---|---|
| 25–30 | 한 Study의 가설(H1~H5)을 직접 검증하거나 연구모형 경로의 변수 2개 이상 관계를 검증. 예: 리세일 참여가 moral licensing을 거쳐 신규구매를 늘림(Study 1 H2), 주장구체성·제3자인증이 그린워싱 지각을 낮춤(Study 2 H3), 소재 브랜드자산이 host brand equity를 거쳐 WTP로 연결(Study 3 H4), traceability가 information credibility·inter-firm trust를 거쳐 관계몰입으로 연결(Study 4 경로) |
| 18–24 | 한 Study의 핵심 변수 1개 또는 조절변수만 다루거나, 같은 경로를 패션·섬유가 아닌 맥락에서 검증 |
| 10–17 | 탐지 키워드나 보조 클러스터(Consumer gap, Umbrella)는 겹치지만 Study 변수·경로와는 간접 연결 |
| 0–9 | 4개 Study 어느 것과도 변수·경로 연결 없음 |

여러 Study에 걸치면 가장 강하게 연결된 Study로 점수를 매기고 나머지는 보조 연결로 적는다. 근거에는 겹치는 가설 번호(예: Study 2 H4)나 경로를 적는다.

### 2.2 저널 수준 (15점)

`연구계획서.md` §12.1 워치리스트 기준.

| 점수 | Tier | 저널 |
|---|---|---|
| 14–15 | A | Journal of Marketing, Journal of Consumer Research, Journal of Consumer Psychology, Journal of Marketing Research, Journal of Retailing |
| 12–13 | A/B | Journal of Business Research, Journal of Retailing and Consumer Services |
| 9–11 | B | Journal of Consumer Marketing, Journal of Fashion Marketing and Management, Journal of Global Fashion Marketing, Business Strategy and the Environment, Journal of Cleaner Production, Sustainable Production and Consumption, Resources Conservation & Recycling |
| 7–8 | 보조 | International Journal of Consumer Studies |
| 3–8 | Watchlist 외 | 동료심사 학술지. 해당 분야 위상으로 판단, 근거에 "Watchlist 외" 명시 |
| 0–2 | — | 프리프린트, 학위논문, 학술대회 발표문, 비심사 보고서 |

저널의 우선 연구축이 이 논문의 연결 Study와 일치하면 구간 상단, 아니면 하단.

### 2.3 학술적 영향력 (15점)

연평균 인용으로 citation velocity를 대신한다.

| 점수 | 연평균 인용 |
|---|---|
| 14–15 | 30 이상 |
| 11–13 | 15–29 |
| 8–10 | 7–14 |
| 5–7 | 3–6 |
| 2–4 | 1–2 |
| 0–1 | 1 미만 |

- 총 인용수 500 이상이면 최소 13점(seminal 논문).
- **신규 논문 보정**: 경과연수 ≤1년이면 인용이 아직 쌓이지 않았으므로, 위 구간 점수와 저널 Tier 대체점수(A 10 / A·B 9 / B 8 / 보조 7 / 그 외 4) 중 **높은 값**을 준다. 근거에 "신규 논문 보정" 명시.

### 2.4 최근성 (10점)

| 점수 | 경과연수 |
|---|---|
| 10 | 0–1년 |
| 9 | 2년 |
| 8 | 3년 |
| 4–7 | 4–6년 |
| 1–3 | 7–10년 |
| 0 | 10년 초과 |

3년이 지났어도 최근 논쟁을 촉발한 연구(리세일 rebound effect 논쟁·Study 1, 그린워싱 불신/인증 신뢰 논쟁·Study 2, Digital Product Passport 논의·Study 4)의 기점이면 최대 8점까지 올리고 근거에 이유를 적는다.

### 2.5 이론적 중요성 (15점)

| 점수 | 기준 |
|---|---|
| 13–15 | 새 이론·통합모형 제시 |
| 9–12 | 4개 Study 이론(Moral Licensing/Rebound Effect·Study1, Signaling·Study2~4 공통, Brand Equity·Study3, Trust/Relationship Marketing·Study4)을 확장하거나 경계조건 제시 |
| 5–8 | 기존 이론을 새 맥락에 적용 |
| 0–4 | 이론 틀 없는 기술적(descriptive) 연구 |

### 2.6 방법론적 가치 (5점)

| 점수 | 기준 |
|---|---|
| 5 | 다중연구, 패널, 실제 행동자료(구매량·판매량·보유기간 — Study 1 행동변수 측정에 차용 가능), 현장실험 |
| 4 | 통제된 실험(Study 2·3의 2×2에 차용 가능), 메타분석, 대규모 조사+SEM(Study 1·4) |
| 3 | 단일 횡단 설문, 체계적 문헌리뷰 |
| 2 | 질적연구·사례연구(Study 3C, Study 4 인터뷰에 참고 가능하면 3) |
| 0–1 | 개념논문, 설계 불명 |

근거에는 이 설계를 어느 Study에 차용할 수 있는지 적는다.

### 2.7 산업 적용성 (10점)

| 점수 | 기준 |
|---|---|
| 8–10 | 한국 섬유패션 기업·소비자·정책 표본을 직접 다루거나 바로 적용 가능 |
| 5–7 | 해외 패션·섬유 산업 맥락이며 한국 적용 경로가 분명함 |
| 2–4 | 일반 소비재·리테일·제조 공급망 맥락으로 섬유패션에 옮겨 쓸 수 있음 |
| 0–1 | 산업 적용 경로 없음 |

### 등급

| 총점 | 등급 | 처리 |
|---|---|---|
| 85점 이상 | 즉시 정독 | §3 5쪽 요약 생성, DB status = Core/Read |
| 75~84점 | 주간리뷰 | `research/digests/weekly-pending.md`에 1문단 핵심노트, DB status = Skimmed |
| 65~74점 | DB 보관 | 메타데이터만 기록, DB status = Inbox |
| 64점 이하 | 메타데이터만 | 사용자에게 짧게 알리고 원하면만 기록 |

### 연결 Study 판정

- 주 연결: 2.1의 점수 근거가 된 Study. 보조 연결: 탐지 키워드·보조 클러스터만 겹치는 Study.
- 관련 가설·경로: 겹치는 가설 번호(예: Study 3 H4) 또는 경로(Study 4는 가설이 없으므로 경로로).
- 관련성 점수 9점 이하면 "연결 Study 없음". Study는 항상 전체 이름으로 표기.

### 누락 시 처리

| 누락 필드 | 처리 |
|---|---|
| 초록 | 관련성·이론·방법·산업적용성을 제목만으로 보수적으로(각 구간 하단) 채점. 방법론은 알 수 없으면 0–1점 |
| 인용수 | 영향력은 저널 Tier 대체점수(A 10 / A·B 9 / B 8 / 보조 7 / 그 외 4) 사용 |
| 연도 | 최근성 0점, 연평균 인용 계산 불가 → 인용수 누락과 같이 처리 |
| 저널 | 저널 수준 0–2점 |

### 평가 출력 형식

```markdown
## 논문 평가: {제목}

- 저널: {저널} ({Tier 또는 Watchlist 외}) | 연도: {연도} (경과 {N}년) | 인용수: {인용수} (연평균 {X.X})
- 입력 누락: {없음 / 누락 필드}

| 평가항목 | 점수 | 판단 근거 |
|---|---|---|
| 박사논문 직접 관련성 | {n}/30 | {근거} |
| 저널 수준 | {n}/15 | {근거} |
| 학술적 영향력 | {n}/15 | {근거} |
| 최근성 | {n}/10 | {근거} |
| 이론적 중요성 | {n}/15 | {근거} |
| 방법론적 가치 | {n}/5 | {근거} |
| 산업 적용성 | {n}/10 | {근거} |
| **총점** | **{합계}/100** | |

**등급:** {구간} — {처리}

**연결 Study**
- 주 연결: {Study 전체 이름} — {이유}
- 보조 연결: {Study 전체 이름 또는 없음} — {이유}
- 관련 가설·경로: {예: Study 2 H3, H4 / 없음}
```

여러 편이면 마지막에 총점 내림차순 요약표를 붙인다. **출력 전 자가검산**: 7개 항목 합이 총점과 같은가, 각 점수가 배점을 넘지 않는가, 등급이 총점 구간과 맞는가.

## 3. A4 5쪽 표준 요약 (85점 이상)

`research/summaries/<paper_id>.md`에 작성. `<paper_id>`는 DOI 슬러그(예 `10.1002-jfmm.2025.001` → `jfmm-2025-001`) 또는 DOI 없으면 `저자연도-키워드`.

1. **Executive Summary** — 한 문장 결론, 연구문제, 핵심 발견 3개, 본 박사논문과의 관련성
2. **Theory & Literature** — 사용 이론, 핵심 개념 정의, 기존 연구와의 차이, 연구가설/모형
3. **Method** — 표본, 국가, 데이터, 변수측정, 실험조건, 분석방법, 타당성
4. **Results & Contribution** — 주요 계수/효과(가능하면 효과크기·유의성), 매개·조절, 이론적·실무적 기여, 저자가 밝힌 한계
5. **Doctoral Research Memo** — Study 1~4 중 연결과 이유, 차용가능 척도/변수/가설/자극, replication 아이디어, research gap, 후속 연구질문 3개(한국 적용 아이디어 포함), 비판적 평가("이 논문이 못 보여준 것")

**원문에 없는 결과·수치를 절대 생성하지 않는다.**

## 4. DB 갱신

`research/db/papers.csv`에 append/update (헤더 없으면 생성). 컬럼: `paper_id,title,authors,year,journal,tier,cluster,study_mapping,theory,method,sample_country,key_constructs,citation_metrics,relevance_score,key_finding,scale_source,research_gap,summary_link,pdf_link,status`. 같은 `paper_id`가 이미 있으면 덮어쓰지 말고 사용자 확인 후 갱신(중복 판단은 DOI 또는 제목 유사도 기준).

## 5. 일일 논문 발견 (오늘의 1편)

목표: 매일 신규 논문 후보를 찾아 §2로 채점하고 가장 높은 점수 1편(동점이면 더 최근 연도)을 "오늘의 논문"으로 고른다. 이미 `research/db/papers.csv`에 있는 `paper_id`(DOI 또는 제목 유사도로 판단)는 후보에서 제외한다.

**중요한 기술적 한계**: Google Scholar는 공식 API가 없고 자동 조회를 차단한다(양쪽 원본 문서 모두 "Scholar를 직접 크롤링하지 않는다"고 명시). 따라서 발견 단계는 아래 순서로 시도하고, 실패하면 다음으로 넘어간다 — 어느 방법으로 찾았든 결과에 항상 **출처를 명시**한다:

1. **Gmail의 Google Scholar Alert 메일** — Gmail 커넥터(`mcp__Gmail__search_threads` / `get_thread`)가 읽기 권한으로 연결되어 있으면 사용 가능. `mcp__Gmail__search_threads`로 `from:scholaralerts-noreply@google.com`(또는 사용자가 등록한 Alert 발신 주소) 쿼리로 오늘 도착한 메일을 찾고, `get_thread`로 본문에서 논문 제목·링크를 파싱한다. **전제조건**: 사용자가 `연구계획서.md` §12.3의 검색식으로 Google Scholar Alert를 실제로 등록해 뒀어야 한다 — 등록돼 있지 않으면(검색 결과 0건) 이 방법은 건너뛰고 2번으로 넘어간다. 가장 원래 설계(§12.6 1단계)에 가깝고 우선순위가 가장 높다.
2. **OpenAlex API** (키 불필요, 무료) — `https://api.openalex.org/works?search=<키워드>&sort=publication_date:desc&per-page=10` 형태로, `연구계획서.md` §12.2 키워드 맵과 `docs/seed_papers.md`의 검색 단서를 순환하며 질의. 제목·저자·저널·연도·DOI·인용수(`cited_by_count`)·초록(`abstract_inverted_index` 복원)을 얻는다. Google Scholar와 같은 학술 인용 데이터베이스를 인덱싱하므로 사실상 동등한 커버리지를 제공하는 합법적 대체 소스다. **환경 제약**: 2026-09-15 실제 실행에서 Claude Code Remote 환경의 egress 정책이 `api.openalex.org`로의 Bash `curl`을 차단(`gateway 403`)하는 것을 확인했다. 이 환경에서는 시도하되, 막히면 즉시 3번으로 넘어간다 — 재시도로 시간 낭비하지 않는다. (다른 환경/향후 실제 Python 파이프라인에서는 정상 작동할 수 있음.)
3. **WebSearch 도구** — 1·2가 안 되면 사용. 같은 실행에서 `WebFetch`로 개별 저널 원문 페이지(nature.com, ncbi.nlm.nih.gov 등)에 접근하는 것도 `EGRESS_BLOCKED`로 막히는 것을 확인했다 — 이 환경에서는 **WebSearch만 안정적으로 작동**한다. 저널 워치리스트(`연구계획서.md` §12.1) + 키워드로 검색하고, 검색 결과 스니펫에서 얻을 수 있는 서지정보(제목·저자·저널·연도·DOI·핵심 발견)만 사용한다 — 스니펫에 없는 표본수·국가·정확한 초록 전문 등은 "확인 불가"로 명시하고 지어내지 않는다(§11).

후보가 여러 개면 전부 §2로 채점하고, **DB에 없는 것 중 최고점 1편**을 오늘의 후보로 정한다.

**발송 최소기준 (2026-09-16 변경)**: 오늘의 후보 점수가 **80점 미만이면 카카오톡·Gmail 모두 보내지 않는다** — 낮은 품질의 논문으로 매일 알림을 소비하지 않기 위함이다. 이 경우 DB에는 메타데이터를 기록하되(§4, status는 §2 등급표 기준), 사용자에게는 "오늘은 80점 이상 후보가 없어 브리핑을 보내지 않았다"는 사실과 최고점 후보의 점수·제목만 짧게 알린다(발송하지 않은 논문의 내용을 카카오톡/Gmail로 보내지 않는다). 후보가 하나도 없을 때(모든 발견 방법 실패)도 동일하게 처리한다.

80점 이상이면 그 논문을 "오늘의 논문"으로 확정해 §6 카카오톡을 보낸다. §7의 85점 Gmail 기준은 그대로 유지 — 즉 80~84점은 카카오톡만, 85점 이상은 카카오톡+Gmail(5쪽 요약)이 나간다.

## 6. 카카오톡 발송 — 5개 필드만

`mcp__PlayMCP__KakaotalkChat-MemoChat` 도구를 사용한다(세션에 연결돼 있지 않으면 사용자에게 알리고 메시지 본문만 텍스트로 보여준다). **메시지 1건 최대 200자**이므로 5개 필드(제목/저널/연도/인용수/초록)를 2건으로 나눠 보낸다:

메시지 1 (서지정보, ~200자):
```
[오늘의 논문] MM/DD
{제목 — 60자 넘으면 "…"로 절단}
저널: {저널} ({연도}) | 인용수: {인용수}
평가: {총점}점 → Study{n} 연결
```

메시지 2 (초록, ~200자):
```
초록: {초록을 180자 이내로 절단, 넘으면 "…(전체는 Gmail 참고)"}
```

오늘의 논문이 85점 이상이면 §3 요약이 Gmail로 간다는 사실을 메시지 1 끝에 짧게 덧붙인다(예: "5쪽요약→Gmail").

## 7. Gmail 발송 — 5쪽 요약

**전제 조건**: 이 skill은 Gmail을 직접 보내는 도구를 자체적으로 갖고 있지 않다. 실행 시점에 `mcp__Gmail__send_message`(또는 최소 `mcp__Gmail__create_draft`)가 이 세션에서 **스코프 오류 없이** 호출되는지 먼저 확인한다 — Gmail 커넥터가 `ListConnectors`에 `connected`로 떠 있어도 스코프가 읽기 전용일 수 있으니 지레짐작하지 않는다(2026-09-15 최초 연결 시 `search_threads`는 되는데 `send_message`/`create_draft`가 `Insufficient scope`였던 사례 있음; 같은 날 재연결(발송 권한 포함) 후 `send_message` 재시도로 정상 발송·수신함 도착까지 확인됨 — 이후로는 정상 동작을 전제로 하되, 스코프가 다시 좁아질 수 있으니 매 실행 시 한 번은 실제 호출 결과로 판단한다).

- **`send_message`가 성공하면**: §3에서 만든 5쪽 요약을 이메일 본문(또는 마크다운 첨부)으로 변환해 제목 `[박사논문 리서치] {날짜} — {논문 제목}`으로 사용자 본인 Gmail 주소로 발송한다.
- **`send_message`가 스코프 오류를 내지만 `create_draft`는 성공하면**: 초안으로 만들어 사용자가 검토 후 직접 보내게 한다. 자동 "발송"은 아니었다는 점을 함께 알린다.
- **`create_draft`도 스코프 오류면**: 자동 발송/초안 생성 모두 못한다는 사실을 명확히 알리고, 완성된 이메일 제목·본문을 대화창에 그대로 보여주거나 `research/summaries/<paper_id>.md`로 저장해 대체한다. "안 되는데 됐다고" 보고하지 않는다 — 원문에 없는 결과를 지어내지 않는다는 원칙과 같은 이유다. 사용자에게 claude.ai 커넥터 설정에서 Gmail 권한 범위를 "보내기(gmail.send)" 또는 "임시보관함 생성(gmail.compose)"까지 포함해 재연결해달라고 안내한다.
- 오늘의 논문이 85점 미만이면(§3을 만들지 않았으면) Gmail 발송 단계는 건너뛰고 그 사실을 알린다.

## 8. 매일 08:29 자동 실행 — 스킬과 스케줄러는 별개다

이 SKILL.md는 "무엇을 할지"의 절차서다. "언제 저절로 깨어날지"는 스킬 밖에서 별도로 등록해야 한다 — 대화 중에 이 skill을 부르는 것만으로는 매일 자동 실행되지 않는다.

실제로 매일 KST 08:29에 §5~§7을 돌리려면 Claude Code Remote의 **Routine**(cron 트리거)을 등록한다: cron은 UTC 기준이므로 KST 08:29 = UTC 23:29 → `29 23 * * *`. 이 트리거가 이 세션(또는 전용 세션)을 깨워 "오늘의 논문 찾아서 카톡·Gmail로 보내줘"를 실행하게 한다. 이 등록은 **매일 사용자의 카카오톡/Gmail로 실제 메시지를 자동 발송하는 지속적 동작**이므로, skill이 스스로 등록하지 않는다 — 사용자에게 확인받고 사람이(또는 사용자 승인 하에 Claude가) 명시적으로 만든다.

## 9. 주간/월간 롤업

- **주간**("이번 주 문헌 정리해줘"): `weekly-pending.md`의 75~84점 논문 + 이번 주 §3 요약을 묶어 "이번 주 문헌이 기존 연구모형을 어떻게 바꾸는가" 2~3쪽 메모를 `research/digests/weekly-<YYYY-MM-DD>.md`로 작성하고 `weekly-pending.md`를 비운다.
- **월간**("이번 달 정리해줘"): 그 달 Core 논문 핵심 10편과 이론/가설/변수에 실제 영향을 준 내용을 정리해 `연구계획서.md` §13 변경이력에 새 행 추가를 제안하고, 동의 시 반영한다. 연구모형(§4~7)은 사용자 확인 없이 임의로 고치지 않는다.

## 10. 엔지니어링 거버넌스 (향후 코드/파이프라인 구현 시 적용)

- 민감정보는 `.env`에만 둔다(API 키, Gmail·Kakao 토큰). 코드에서는 환경변수로 읽는다.
- `.gitignore` 제외 대상(저장소 루트 `.gitignore` 참고): `.env`, `credentials*.json`, `kakao_token*.json`, `gmail_token*.json`, `*.db`, `__pycache__/`, `research/papers/`(제3자 논문 원문 PDF — 저작권). `docs/`의 프로젝트 자체 원본 문서(연구계획서 PDF 등)는 예외로 커밋한다.
- 파일명 규칙: `.claude/skills/`와 향후 `src/`의 코드·스킬 이름은 영문(공백·한글 금지). `docs/`, `research/`의 사람이 읽는 문서는 한글 파일명 유지.
- Python으로 파이프라인을 구현할 경우: 3.10+, 주석은 한국어, 함수/변수명은 영어 snake_case, 각 수집·보강 소스는 독립 동작(하나 실패해도 기록 후 나머지 계속 진행), 로그는 콘솔에 실시간 출력.

## 11. 원칙

- 인용수 자체를 연구 질로 오인하지 않는다 — 연평균 인용·저널·이론적 중요성을 함께 본다.
- 원문에서 확인할 수 없는 결과·수치·인용정보·서지정보를 절대 생성하지 않는다(§2 입력, §5 발견, `docs/seed_papers.md` 모두 이 원칙을 따른다).
- 저작권·기관구독 정책을 준수한다 — 원문 PDF를 임의로 재배포하지 않고, 서지정보·초록·합법적 OA 원문만 다룬다.
- 연구 내용은 `docs/`의 PDF가, 자동화 조작적 정의는 이 skill 파일이 최종 기준이다(§0). `연구계획서.md`가 갱신되면 다음 요청부터 새 기준을 적용한다.
- 실제로 되지 않는 것(예: 커넥터 미연결로 Gmail 발송 불가)을 됐다고 보고하지 않는다.
