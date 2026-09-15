# Worked example: press release → 6-card deck

This walks through turning a typical 보도자료 into a card-news deck, from
raw text to the final `cards.json`. Use it as a template for tone and
pacing, not as a fixed formula — a shorter or more technical release might
only need 5 cards, a denser one might need 7.

## 1. The source text (as extracted from the PDF)

```
한국섬유산업연합회, 2026년 상반기 섬유·패션 수출 12.4% 증가 발표

한국섬유산업연합회(회장 ○○○)는 2026년 상반기 국내 섬유·패션 수출액이
68억 달러를 기록하며 전년 동기 대비 12.4% 증가했다고 15일 밝혔다.

이번 증가는 국내 중소 섬유기업의 해외 진출 확대와 고부가가치 소재
개발이 주요 원인으로 분석된다. 특히 친환경 소재와 기능성 원단 수출이
전체 증가분의 절반 이상을 차지했다.

○○○ 회장은 "국내 섬유산업의 디지털 전환과 친환경 소재 개발이 수출
경쟁력 강화의 핵심"이라며 "정부와 협력해 중소기업의 해외 판로 개척을
적극 지원하겠다"고 말했다.

한국섬유산업연합회는 하반기 해외 전시회 참가 지원을 확대하고, 친환경
섬유 인증 지원 사업을 신설할 계획이라고 밝혔다.
```

## 2. Reading it for a deck

Skim for: one hook, the who/what/when, one standout number, one quotable
line, and one forward-looking close. This release has all five, so it
becomes 5 cards (cover + content + stat + quote + closing) rather than
stretching to 6-7 by padding.

- **Hook** → not the formal headline, the most interesting fact:
  "K-패션, 세계로 뻗어나가다" reads better on a feed than the release's own
  title.
- **Background** → the who/what compressed to 2-3 bullets.
- **Standout number** → 12.4% is the one figure worth its own slide.
- **Quote** → the chair's quote, shortened to the punchiest clause if the
  original run-on is too long for a slide.
- **Close** → the two forward-looking initiatives, plus source line.

## 3. Resulting `cards.json`

```json
{
  "brand": {
    "name": "한국섬유산업연합회",
    "short_name": "KOFOTI",
    "logo_path": null,
    "primary_color": "#0f2f4f",
    "accent_color": "#d4a72c"
  },
  "cards": [
    {
      "type": "cover",
      "kicker": "보도자료",
      "title": "K-패션, 세계로 뻗어나가다",
      "subtitle": "2026년 상반기 섬유·패션 수출 12.4% 증가",
      "date": "2026. 9. 15."
    },
    {
      "type": "content",
      "kicker": "배경",
      "heading": "무슨 일이 있었나요?",
      "body": [
        "2026년 상반기 섬유·패션 수출액 68억 달러 기록",
        "전년 동기 대비 12.4% 증가한 수치",
        "중소 섬유기업의 해외 진출 확대가 주요 원인"
      ]
    },
    {
      "type": "stat",
      "heading": "핵심 수치",
      "stat_value": "12.4%",
      "stat_label": "2026년 상반기 섬유·패션 수출 증가율 (전년 동기 대비)"
    },
    {
      "type": "quote",
      "quote": "국내 섬유산업의 디지털 전환과 친환경 소재 개발이 수출 경쟁력 강화의 핵심입니다.",
      "attribution": "한국섬유산업연합회 회장"
    },
    {
      "type": "closing",
      "heading": "앞으로의 계획",
      "body": [
        "하반기 해외 전시회 참가 지원 확대",
        "친환경 섬유 인증 지원 사업 신설"
      ],
      "cta": "자세한 내용은 프로필 링크에서 확인하세요",
      "source": "자료 출처: 한국섬유산업연합회 보도자료 (2026.9.15)"
    }
  ]
}
```

This exact spec is what `scripts/render_cards.py` was smoke-tested against
while building this skill — running it end to end reliably produces a
clean 5-card deck with the KOFOTI name in the cover footer. If the user's
real release includes a photo (either supplied separately or extracted
from the PDF), add `"image": "path/to/photo.jpg"` to whichever card it best
illustrates — the cover and the content card are the most natural spots.
