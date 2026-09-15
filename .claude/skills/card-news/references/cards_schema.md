# cards.json schema

Top level:

```json
{
  "brand": { "...": "see below" },
  "cards": [ { "...": "1 object per slide, 5-7 total" } ]
}
```

## `brand`

| field | required | notes |
|---|---|---|
| `name` | yes | full org name, e.g. `"한국섬유산업연합회"` |
| `short_name` | no | shown as a small caption under `name` in the logo fallback, e.g. `"KOFOTI"` |
| `logo_path` | no | local path to a logo image (PNG/JPG/SVG-as-raster). If set and the file exists, it's inlined and used instead of the text badge. If omitted or missing, the renderer draws `name` / `short_name` as a text badge automatically — you don't need to handle the fallback yourself. |
| `primary_color` | no | hex background color for text-only (no photo) cards. Default `#0f2f4f` (KOFOTI navy — see `brand.md`). |
| `accent_color` | no | hex accent used for the kicker pill, stat number, bullet dots, quote mark, active page-dot. Default `#d4a72c` (gold). |

## `cards[]` — common fields

| field | applies to | notes |
|---|---|---|
| `type` | all | one of `cover`, `content`, `stat`, `quote`, `closing` |
| `image` | all | optional local path to a photo. If present, it fills the card as a full-bleed background with a dark gradient for legibility. If omitted, the card uses `brand.primary_color` as a flat background. |

## Card types

### `cover`
The first slide. **This is the only card type that is required to carry the
brand footer** — always use `cover` for slide 1 so the KOFOTI name/logo
requirement is met automatically.

```json
{
  "type": "cover",
  "kicker": "보도자료",
  "title": "K-패션, 세계로 뻗어나가다",
  "subtitle": "2026년 상반기 섬유·패션 수출 12.4% 증가",
  "date": "2026. 9. 15.",
  "image": null
}
```
`kicker`, `date`, `image` are optional. `title`/`subtitle` are the hook —
keep `title` especially short, it's set in a very large weight.

### `content`
A body/background slide with a heading and up to ~4 short bullets.

```json
{
  "type": "content",
  "kicker": "배경",
  "heading": "무슨 일이 있었나요?",
  "body": [
    "2026년 상반기 섬유·패션 수출액 68억 달러 기록",
    "전년 동기 대비 12.4% 증가"
  ],
  "image": null
}
```

### `stat`
One big number, for the single most shareable figure in the release.

```json
{
  "type": "stat",
  "heading": "핵심 수치",
  "stat_value": "12.4%",
  "stat_label": "2026년 상반기 섬유·패션 수출 증가율 (전년 동기 대비)"
}
```
`heading` is optional (a small label above the number). Keep `stat_value`
very short — it renders at ~170px.

### `quote`
An official's quote from the release, if there is one worth featuring.

```json
{
  "type": "quote",
  "quote": "국내 섬유산업의 디지털 전환과 친환경 소재 개발이 수출 경쟁력 강화의 핵심입니다.",
  "attribution": "한국섬유산업연합회 회장"
}
```

### `closing`
Last slide: what's next, a CTA, and the source line.

```json
{
  "type": "closing",
  "heading": "앞으로의 계획",
  "body": ["하반기 해외 전시회 참가 지원 확대"],
  "cta": "자세한 내용은 프로필 링크에서 확인하세요",
  "source": "자료 출처: 한국섬유산업연합회 보도자료 (2026.9.15)"
}
```
`closing` also renders the brand footer (logo/name), so a `cover` +
`closing` bookend is a common, brand-safe pattern — but only `cover` is
required to have it.
