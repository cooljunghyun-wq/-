---
name: card-news
description: Turn a Korean press release (보도자료) PDF into a 5-7 slide Instagram "card news" (카드뉴스) image deck for 한국섬유산업연합회 (KOFOTI). Use this whenever the user asks to make/만들어줘 카드뉴스, wants a 보도자료 PDF (from Google Drive or uploaded) turned into Instagram carousel slides, or asks for a set of shareable summary/announcement images from a press release or report — even if they don't say "카드뉴스" explicitly (e.g. "이 PDF로 인스타 올릴 이미지 몇 장 만들어줘", "보도자료 카드뉴스로 제작"). Always produces 5-7 branded PNG images with the KOFOTI name/logo on the cover.
---

# Card News (카드뉴스) Generator

Turns a press release PDF into a 5-7 slide Instagram carousel: one idea per
card, one headline stat pulled out, one quote, a cover and a close — all
rendered as ready-to-upload PNGs.

## Workflow

### 1. Get the source PDF

The user's press releases usually live in Google Drive. If a Google Drive
connector is available in this session, use it to find and download the
PDF. Otherwise ask the user to upload the file or give a local path — don't
guess at a Drive URL.

### 2. Extract text and any embedded photos

```bash
pip install --quiet pymupdf   # one-time, only if not already installed
python3 scripts/extract_pdf_assets.py <input.pdf> --outdir extracted/
```

This writes `extracted/text.txt` (full text) and `extracted/images/*` (every
embedded image over ~8KB, i.e. real photos rather than logos/rule lines). If
the script errors because PyMuPDF won't install in this environment, fall
back to the `pdf` skill for extraction instead — the rest of this workflow
doesn't care how the text/images were pulled out, only that you have them.

**Requirement: image sourcing.** If the user separately supplies photos for
the release, use those. Only when no separate photos exist should you pull
from the images extracted out of the PDF itself. If a card has no relevant
photo at all (from either source), that's fine — just leave `"image": null`
and it renders on the brand color background instead. Don't stretch or
reuse an unrelated photo just to fill space.

### 3. Plan the 5-7 card breakdown

This is the part that needs judgment, not a script — read the extracted
text yourself and decide what the deck says. Read
`references/card_format_sample.md` first: it walks through a full worked
example (a sample press release turned into a 6-card breakdown) showing the
kind of compression and framing that works for social. Read
`references/cards_schema.md` for the exact JSON fields each card type takes.

A deck that reads well on Instagram is usually:

1. **cover** — the headline as a hook, not the press release's formal title.
   "섬유 수출, 상반기 12.4% 증가" beats "2026년 상반기 섬유산업 동향 보고서 발표".
2. **content** — what actually happened / background (1-2 cards)
3. **stat** — pull out the single most shareable number, big and alone
4. **quote** — an official's quote, if the release has one worth featuring
5. **closing** — what's next, plus a source line and the logo again if you like

Not every release has all five ingredients — a quote-less release just
skips that card type. Stay inside 5-7 cards total; more than that and
nobody swipes to the end. Keep text tight: titles under ~20 Korean
characters, body bullets under ~30 characters each, max 3-4 bullets per
card — the layout doesn't auto-shrink text, so long lines will crowd or
overflow (see step 6).

### 4. Write `cards.json`

Follow the schema in `references/cards_schema.md`. Set `brand.name` to
"한국섬유산업연합회" and `brand.short_name` to "KOFOTI". If the user has
supplied an actual KOFOTI logo file, set `brand.logo_path` to it; otherwise
leave it `null` and the renderer automatically draws a text badge with the
org name instead — either way, **the cover card must end up carrying the
KOFOTI name or logo**, so don't skip the `footer-brand` block by picking the
wrong card type for the cover.

### 5. Render

```bash
python3 scripts/render_cards.py --spec cards.json --outdir out/
```

No extra Python packages are needed for this step — it drives the
Chromium binary already installed in this environment as a headless
screenshotter, so it works even offline. Output is `out/card_01.png` …
`out/card_0N.png` at 1080x1350 (Instagram's 4:5 portrait, the largest
size the app allows — safe for both feed and carousel).

### 6. Review before delivering

Read the generated PNGs back (they're just image files) and check by eye:
text isn't clipped or overlapping the footer, the stat/quote cards aren't
awkwardly empty, photos aren't oddly cropped. If a card's text overflows,
shorten the copy in `cards.json` and re-run step 5 — cheaper than trying to
tune font sizes. Re-render only the cards you changed if you want to save
time (pass the same `--outdir`, it overwrites by filename).

### 7. Deliver

Hand the user all 5-7 PNGs. Since these are meant for Instagram, mention
they're sized for a carousel post/reel cover (4:5) and that card 1 is the
feed thumbnail, so it's worth a second look before posting.

## Reference files

- `references/cards_schema.md` — full JSON schema, one example per card type
- `references/card_format_sample.md` — a worked example: sample press
  release text → 6-card breakdown, useful as a template for tone and pacing
- `references/brand.md` — KOFOTI color palette defaults and logo/footer
  fallback behavior

## Troubleshooting

- **`error: no Chromium binary found`** — set `CHROMIUM_PATH` or confirm
  this environment has Chromium at `/opt/pw-browsers/chromium` (or install
  `chromium`/`google-chrome` and re-run).
- **Korean text renders as boxes/tofu** — the render script's font stack
  prefers Noto Sans KR (loaded from Google Fonts if the sandbox has network
  access) and falls back to whatever CJK font is already installed
  (commonly WenQuanYi Zen Hei). If both are missing, install a CJK font
  package or point the user to a fonts-CJK package for their environment.
- **PDF has no usable images** — either ask the user for separate photos,
  or just build a text-only deck on the brand color background; don't
  fabricate photos.
