# KOFOTI branding defaults

No official brand asset (logo file, exact hex palette) was available when
this skill was built, so it ships with sensible placeholder defaults rather
than guessed-at real ones. Treat these as a starting point, not ground
truth:

- `primary_color`: `#0f2f4f` — a dark navy, a common institutional/textile
  industry tone. Safe as a full-bleed background for text-only cards.
- `accent_color`: `#d4a72c` — a muted gold, used sparingly for the kicker
  pill, the stat number, bullet markers, quote mark, and the active page
  dot. Keeps the deck from looking like a generic blue-and-white template.

**If the user has an actual KOFOTI brand guide or logo file**, prefer it
over these defaults:

- Drop the logo file somewhere accessible (e.g. `assets/kofoti_logo.png`
  next to this skill, or wherever the user uploads it) and set
  `brand.logo_path` in `cards.json` to that path. The renderer inlines it
  automatically on the cover card — no code changes needed.
- If they give real hex codes, just set `brand.primary_color` /
  `brand.accent_color` in `cards.json` per-run; there's nothing to edit in
  the skill itself.

## Logo fallback behavior

When `brand.logo_path` is unset (or points to a file that doesn't exist),
`render_cards.py` renders a text badge instead: the org's full name in bold,
with `short_name` (e.g. "KOFOTI") in small letter-spaced caps underneath.
This satisfies the "logo **or** name" requirement without needing an actual
image file, and it upgrades automatically the moment a real logo path is
supplied — so don't special-case "no logo" runs, just leave `logo_path`
null and move on.
