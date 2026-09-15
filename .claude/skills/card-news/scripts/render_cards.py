#!/usr/bin/env python3
"""Render a card-news JSON spec into numbered PNG images for Instagram.

Usage:
    python3 render_cards.py --spec cards.json --outdir out/ [--width 1080] [--height 1350]

No third-party Python packages are required. Rendering is done by driving
the Chromium binary that ships with this environment in headless
screenshot mode, so each card is just an HTML/CSS page that gets
screenshotted to PNG. Any local image referenced in the spec (hero photos,
the org logo) is inlined into the HTML as a base64 data URI, so the
generated HTML files are fully self-contained and don't depend on
file:// relative paths.

See ../references/cards_schema.md for the JSON spec format and
../references/brand.md for the default KOFOTI color palette / logo
fallback behavior.
"""
import argparse
import base64
import html
import json
import mimetypes
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1350  # 4:5, Instagram's tallest allowed portrait ratio

FONT_STACK = (
    "'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', "
    "'WenQuanYi Zen Hei', 'Pretendard', sans-serif"
)

BASE_CSS = f"""
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    width: {{W}}px;
    height: {{H}}px;
    font-family: {FONT_STACK};
    color: #ffffff;
    position: relative;
    overflow: hidden;
    background: {{BG}};
  }}
  .overlay {{
    position: absolute; inset: 0;
    background: {{OVERLAY}};
  }}
  .pad {{
    position: absolute; inset: 0;
    padding: 88px 84px;
    display: flex;
    flex-direction: column;
  }}
  .kicker {{
    display: inline-block;
    align-self: flex-start;
    font-size: 30px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 10px 26px;
    border-radius: 999px;
    background: {{ACCENT}};
    color: #14202b;
    margin-bottom: 40px;
  }}
  .title {{
    font-size: 76px;
    font-weight: 900;
    line-height: 1.28;
    margin: 0 0 28px 0;
    word-break: keep-all;
  }}
  .subtitle {{
    font-size: 38px;
    font-weight: 500;
    line-height: 1.5;
    color: rgba(255,255,255,0.88);
    word-break: keep-all;
  }}
  .heading {{
    font-size: 58px;
    font-weight: 800;
    line-height: 1.32;
    margin: 0 0 44px 0;
    word-break: keep-all;
  }}
  .body-list {{
    list-style: none;
    margin: 0; padding: 0;
    font-size: 38px;
    line-height: 1.55;
    font-weight: 500;
    word-break: keep-all;
  }}
  .body-list li {{
    position: relative;
    padding-left: 44px;
    margin-bottom: 30px;
  }}
  .body-list li::before {{
    content: "";
    position: absolute; left: 0; top: 18px;
    width: 16px; height: 16px;
    border-radius: 50%;
    background: {{ACCENT}};
  }}
  .spacer {{ flex: 1 1 auto; }}
  .stat-value {{
    font-size: 168px;
    font-weight: 900;
    color: {{ACCENT}};
    line-height: 1.05;
    margin: 0 0 24px 0;
  }}
  .stat-label {{
    font-size: 42px;
    font-weight: 600;
    line-height: 1.5;
    word-break: keep-all;
  }}
  .quote-mark {{
    font-size: 140px;
    font-weight: 900;
    color: {{ACCENT}};
    line-height: 1;
    margin: 0 0 12px 0;
  }}
  .quote-text {{
    font-size: 52px;
    font-weight: 700;
    line-height: 1.45;
    word-break: keep-all;
    margin: 0 0 40px 0;
  }}
  .attribution {{
    font-size: 34px;
    font-weight: 600;
    color: rgba(255,255,255,0.82);
  }}
  .source {{
    font-size: 30px;
    font-weight: 500;
    color: rgba(255,255,255,0.72);
    margin-bottom: 16px;
  }}
  .page-dots {{
    position: absolute; top: 56px; right: 64px;
    display: flex; gap: 10px;
  }}
  .page-dots span {{
    width: 14px; height: 14px; border-radius: 50%;
    background: rgba(255,255,255,0.32);
  }}
  .page-dots span.active {{ background: {{ACCENT}}; width: 34px; border-radius: 8px; }}
  .footer-brand {{
    display: flex; align-items: center; gap: 22px;
    padding-top: 36px;
    border-top: 2px solid rgba(255,255,255,0.28);
  }}
  .footer-brand img {{ height: 56px; display: block; }}
  .footer-brand .badge {{
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 1px;
  }}
  .footer-brand .badge small {{
    display: block;
    font-size: 20px;
    font-weight: 500;
    letter-spacing: 3px;
    color: rgba(255,255,255,0.72);
    margin-top: 4px;
  }}
"""


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def find_chromium() -> str:
    candidates = [
        "/opt/pw-browsers/chromium",
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    die(
        "no Chromium binary found. Set CHROMIUM_PATH env var or install "
        "chromium (this environment normally ships one at /opt/pw-browsers/chromium)."
    )


def to_data_uri(path: str) -> str:
    p = Path(path).expanduser()
    if not p.is_file():
        die(f"image not found: {path}")
    mime = mimetypes.guess_type(str(p))[0] or "image/jpeg"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def render_body_list(items):
    if not items:
        return ""
    lis = "".join(f"<li>{esc(item)}</li>" for item in items)
    return f'<ul class="body-list">{lis}</ul>'


def render_page_dots(index: int, total: int) -> str:
    if total <= 1:
        return ""
    dots = "".join(
        f'<span class="{"active" if i == index else ""}"></span>' for i in range(total)
    )
    return f'<div class="page-dots">{dots}</div>'


def render_footer_brand(brand: dict) -> str:
    logo_path = brand.get("logo_path")
    name = brand.get("name", "")
    short_name = brand.get("short_name", "")
    if logo_path and Path(logo_path).expanduser().is_file():
        logo_uri = to_data_uri(logo_path)
        return f"""
        <div class="footer-brand">
          <img src="{logo_uri}" alt="logo" />
        </div>
        """
    # Fallback: no logo file supplied, render the org name as a text badge.
    sub = f"<small>{esc(short_name)}</small>" if short_name else ""
    return f"""
    <div class="footer-brand">
      <div class="badge">{esc(name)}{sub}</div>
    </div>
    """


def card_css(brand: dict, width: int, height: int, image: str | None, type_: str) -> str:
    primary = brand.get("primary_color", "#0f2f4f")
    accent = brand.get("accent_color", "#d4a72c")
    if image:
        bg = f"#000 url('{to_data_uri(image)}') center / cover no-repeat"
        overlay = (
            "linear-gradient(180deg, rgba(10,20,30,0.35) 0%, "
            "rgba(10,20,30,0.55) 55%, rgba(10,20,30,0.92) 100%)"
            if type_ != "cover"
            else "linear-gradient(180deg, rgba(10,20,30,0.25) 0%, "
            "rgba(10,20,30,0.5) 45%, rgba(10,20,30,0.94) 100%)"
        )
    else:
        bg = primary
        overlay = "rgba(0,0,0,0)"
    css = BASE_CSS.replace("{W}", str(width)).replace("{H}", str(height))
    css = css.replace("{BG}", bg).replace("{OVERLAY}", overlay).replace("{ACCENT}", accent)
    return css


def render_cover(card: dict, brand: dict) -> str:
    kicker = f'<div class="kicker">{esc(card.get("kicker", "보도자료"))}</div>' if card.get(
        "kicker"
    ) else ""
    date = f'<div class="source">{esc(card["date"])}</div>' if card.get("date") else ""
    return f"""
    {kicker}
    <div class="spacer"></div>
    <h1 class="title">{esc(card.get("title", ""))}</h1>
    <p class="subtitle">{esc(card.get("subtitle", ""))}</p>
    <div class="spacer"></div>
    {date}
    {render_footer_brand(brand)}
    """


def render_content(card: dict) -> str:
    kicker = f'<div class="kicker">{esc(card["kicker"])}</div>' if card.get("kicker") else ""
    return f"""
    {kicker}
    <h2 class="heading">{esc(card.get("heading", ""))}</h2>
    {render_body_list(card.get("body", []))}
    <div class="spacer"></div>
    """


def render_stat(card: dict) -> str:
    heading = f'<h2 class="heading">{esc(card["heading"])}</h2>' if card.get("heading") else ""
    return f"""
    {heading}
    <div class="spacer"></div>
    <div class="stat-value">{esc(card.get("stat_value", ""))}</div>
    <div class="stat-label">{esc(card.get("stat_label", ""))}</div>
    <div class="spacer"></div>
    """


def render_quote(card: dict) -> str:
    attribution = (
        f'<div class="attribution">{esc(card["attribution"])}</div>'
        if card.get("attribution")
        else ""
    )
    return f"""
    <div class="quote-mark">&ldquo;</div>
    <div class="spacer"></div>
    <p class="quote-text">{esc(card.get("quote", ""))}</p>
    {attribution}
    <div class="spacer"></div>
    """


def render_closing(card: dict, brand: dict) -> str:
    heading = f'<h2 class="heading">{esc(card["heading"])}</h2>' if card.get("heading") else ""
    source = f'<div class="source">{esc(card["source"])}</div>' if card.get("source") else ""
    cta = f'<p class="subtitle">{esc(card["cta"])}</p>' if card.get("cta") else ""
    return f"""
    {heading}
    {render_body_list(card.get("body", []))}
    {cta}
    <div class="spacer"></div>
    {source}
    {render_footer_brand(brand)}
    """


RENDERERS = {
    "cover": lambda card, brand: render_cover(card, brand),
    "content": lambda card, brand: render_content(card),
    "stat": lambda card, brand: render_stat(card),
    "quote": lambda card, brand: render_quote(card),
    "closing": lambda card, brand: render_closing(card, brand),
}


def build_html(card: dict, brand: dict, width: int, height: int, index: int, total: int) -> str:
    type_ = card.get("type", "content")
    renderer = RENDERERS.get(type_)
    if renderer is None:
        die(f"unknown card type: {type_!r} (expected one of {list(RENDERERS)})")
    body_html = renderer(card, brand)
    css = card_css(brand, width, height, card.get("image"), type_)
    dots = render_page_dots(index, total)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body>
  <div class="overlay"></div>
  {dots}
  <div class="pad">
    {body_html}
  </div>
</body></html>"""


def screenshot(chromium: str, html_path: Path, png_path: Path, width: int, height: int) -> None:
    cmd = [
        chromium,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--screenshot={png_path}",
        f"--window-size={width},{height}",
        f"file://{html_path}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if not png_path.exists():
        die(
            "chromium screenshot failed:\n"
            + result.stdout[-2000:]
            + "\n"
            + result.stderr[-2000:]
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", required=True, help="path to cards.json")
    ap.add_argument("--outdir", required=True, help="output directory for PNGs")
    ap.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    ap.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    ap.add_argument("--prefix", default="card", help="output filename prefix")
    args = ap.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.is_file():
        die(f"spec not found: {spec_path}")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    brand = spec.get("brand", {})
    cards = spec.get("cards", [])
    if not (5 <= len(cards) <= 7):
        print(
            f"warning: spec has {len(cards)} cards; Instagram card-news decks "
            "read best at 5-7 slides.",
            file=sys.stderr,
        )

    chromium = find_chromium()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for i, card in enumerate(cards):
            html_str = build_html(card, brand, args.width, args.height, i, len(cards))
            html_file = tmp_path / f"{args.prefix}_{i + 1:02d}.html"
            html_file.write_text(html_str, encoding="utf-8")
            png_file = outdir / f"{args.prefix}_{i + 1:02d}.png"
            screenshot(chromium, html_file, png_file, args.width, args.height)
            print(f"wrote {png_file}")

    print(f"done: {len(cards)} card(s) written to {outdir}")


if __name__ == "__main__":
    main()
