"""essay_to_book harness verifier, standalone copy used by /publish 1단계.
This file lives in scripts/ as the canonical verifier.

책마다 달라지는 검사 규칙(금지 용어, 어미, em dash 허용 여부, 불릿 기호, 금지 영어 표현)은
book-config.md의 "## 검증 규칙" 섹션에서 읽는다. 그 섹션이나 개별 항목이 없으면 아래
기본값(해라체, em dash 비허용 등 학술 논문 관행)으로 폴백하므로, 규칙을 지워도 검사기는 돈다.

트레이드북용 book_publishing 스킬의 verify.py와 달리, 이 스킬은 "최소 편집" 원칙을
지켰는지를 대략적으로 감시하는 항목(분량 이상 변화, 연결 문단 존재 여부)을 추가로 검사한다.
정밀한 원문 대조는 /review 4단계(최소편집 준수 검수)가 사람이 읽고 판단하며,
이 스크립트는 그 결과를 전제로 기계적으로 확인 가능한 것만 잡는다.
"""
import re, sys, pathlib

if len(sys.argv) != 4:
    print("usage: verify.py <manuscript.md> <book-config.md> <verify-report.md>", file=sys.stderr)
    sys.exit(2)

SRC = pathlib.Path(sys.argv[1])
CONFIG = pathlib.Path(sys.argv[2])
REPORT = pathlib.Path(sys.argv[3])

text = SRC.read_text(encoding="utf-8")
config = CONFIG.read_text(encoding="utf-8")

issues = []  # [(severity, category, detail)]

# ---------------------------------------------------------------------------
# 검증 규칙 로드 — book-config.md "## 검증 규칙" 섹션을 정본으로 삼는다.
# ---------------------------------------------------------------------------
RULES = {
    "어미": "해라체",
    "em dash 허용": "아니오",
    "불릿 기호": "•",
    "금지 용어": "",
    "금지 영어 표현": "",
    "장 연결 문단 필수 문구": "",
}

rules_sec = re.search(r"^#+\s*검증\s*규칙\s*$(.*?)(?:^#+\s|\Z)", config, re.M | re.S)
if rules_sec:
    for line in rules_sec.group(1).splitlines():
        line = line.strip().lstrip("-").strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.split("#")[0].strip()
        if key in RULES:
            RULES[key] = val

def _parse_pairs(spec):
    pairs = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = re.split(r"\s*(?:→|->|⇒)\s*", chunk, maxsplit=1)
        wrong = parts[0].strip()
        right = parts[1].strip() if len(parts) > 1 else ""
        if wrong:
            pairs.append((wrong, right))
    return pairs

allow_emdash = RULES["em dash 허용"].strip() in ("예", "yes", "허용", "true", "True")
ending = RULES["어미"].strip()
bullet = (RULES["불릿 기호"].strip() or "•")[0]
banned_terms = _parse_pairs(RULES["금지 용어"])
banned_english = _parse_pairs(RULES["금지 영어 표현"])

# 1) em dash 잔존
if not allow_emdash:
    for m in re.finditer(r"[—–]", text):
        issues.append(("🔴", "em dash 잔존", f"위치 {m.start()}"))

# 2) ** 마크다운 잔존
for m in re.finditer(r"\*\*[^*\n]+\*\*", text):
    issues.append(("🔴", "마크다운 ** 잔존", m.group(0)[:30]))

# 3) 어미 통일성
da_endings = len(re.findall(r"다[\.!?]", text))
hap = len(re.findall(r"니다[\.!?]", text))
hae = max(0, da_endings - hap)
if ending == "합쇼체":
    intrusion, base, other = hae, da_endings, "해라체"
else:
    intrusion, base, other = hap, da_endings, "합쇼체"
if base and intrusion / base > 0.05:
    issues.append(("🟡", "어미 혼용 의심", f"{other} 종결 {intrusion}/{base}"))

# 4) 목차 항목 누락 검사 (book-config "## 목차" 섹션에서 부/장 라벨 추출)
def _despace(s):
    return re.sub(r"\s+", "", s)

toc_body = config
sec = re.search(r"^#+\s*목차.*?$(.*?)(?:^#+\s*(?:용어 통일|검증 규칙|퍼블리싱 사양)|\Z)", config, re.M | re.S)
if sec:
    toc_body = sec.group(1)

text_nospace = _despace(text)
seen_labels = set()
expected_labels = []

def _add_label(display, needle):
    if display not in seen_labels:
        seen_labels.add(display)
        expected_labels.append((display, needle))

for n in re.findall(r"제\s*(\d+)\s*부", toc_body):
    _add_label(f"제{n}부", f"제{n}부")
for n in re.findall(r"제\s*(\d+)\s*장", toc_body):
    _add_label(f"제{n}장", f"제{n}장")
for kw in ["서문", "결론", "참고문헌", "부록"]:
    if kw in toc_body:
        _add_label(kw, kw)

for display, needle in expected_labels:
    if _despace(needle) not in text_nospace:
        issues.append(("🔴", "목차 항목 누락", display))

# 5) 상태 마커 확인
if "<!-- STAGE_COMPLETE: 05_manuscript-v2 -->" not in text:
    issues.append(("🔴", "상태 마커 누락", "05_manuscript-v2 미완료"))

# 6) 장 연결 문단 존재 여부 (휴리스틱: 장 제목 뒤 500자 이내에 "앞", "지난", "이전 장" 등
#    연결을 암시하는 표현이 있는지). 첫 장은 연결할 대상이 없으므로 제외한다.
chapter_starts = [m.start() for m in re.finditer(r"제\s*\d+\s*장", text)]
bridge_hint = re.compile(r"(지난 장|이전 장|앞\s*장|앞에서|위에서 본|살펴본 바와 같이)")
if len(chapter_starts) > 1:
    missing_bridge = 0
    for idx, pos in enumerate(chapter_starts[1:], start=1):
        window = text[pos:pos + 500]
        if not bridge_hint.search(window):
            missing_bridge += 1
    if missing_bridge:
        issues.append(("🟡", "장 연결 문단 누락 의심", f"{missing_bridge}/{len(chapter_starts)-1}개 장 시작부에서 미검출"))

# 7) 금지 용어 / 금지 영어 표현
for wrong, right in banned_terms:
    if wrong in text:
        detail = f"'{wrong}'" + (f" → '{right}'" if right else "")
        issues.append(("🔴", "용어 위반", detail))

for wrong, right in banned_english:
    if wrong in text:
        detail = f"'{wrong}'" + (f" → '{right}'" if right else "")
        issues.append(("🟡", "영어 표현 과다", detail))

# 8) 불릿 부호
typo_bullets = ["●", "○", "▪", "▫", "■", "□", "◆", "◇", "‣", "⁃"]
for sym in typo_bullets:
    if sym != bullet and sym in text:
        issues.append(("🟡", "불릿 부호 비통일", f"'{sym}' 사용 (지정 기호 '{bullet}')"))

# 9) 분량 정보
char_count = len(re.sub(r"\s", "", text))
issues.append(("ℹ️", "분량", f"{char_count}자"))

# 10) 자가 채점
red = sum(1 for s, _, _ in issues if s == "🔴")
yellow = sum(1 for s, _, _ in issues if s == "🟡")
info = sum(1 for s, _, _ in issues if s == "ℹ️")

if red == 0:
    red_cap = 10
elif red == 1:
    red_cap = 7
elif red == 2:
    red_cap = 6
else:
    red_cap = max(1, 5 - (red - 3))

if yellow == 0:
    yellow_cap = 10
elif yellow <= 2:
    yellow_cap = 9
elif yellow <= 5:
    yellow_cap = 8
elif yellow <= 10:
    yellow_cap = 7
elif yellow <= 15:
    yellow_cap = 6
else:
    yellow_cap = 5

score = min(red_cap, yellow_cap)

lines = [
    "# verify-report",
    "",
    f"- 🔴 필수: {red}건",
    f"- 🟡 권장: {yellow}건",
    f"- ℹ️ 정보: {info}건",
    f"- **자가 채점: {score} / 10**",
    "",
    "## 상세",
]
for s, cat, detail in issues:
    lines.append(f"- {s} **{cat}** — {detail}")

lines += [
    "",
    "## 참고",
    "이 스킬은 최소 편집 원칙을 따른다. 위 🟡 항목 중 상당수는 결함이 아니라",
    "\"원문을 바꾸지 않기 위해 자동 반영하지 않은 제안\"일 수 있다.",
    "실제 출판 가능 여부는 점수 자체보다 output/{ACTIVE}/pending-suggestions.md를",
    "사용자가 확인했는지에 달려 있다.",
]

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"verify done: 🔴 {red}, 🟡 {yellow}, ℹ️ {info}, score={score}/10")
sys.exit(1 if red > 0 else 0)
