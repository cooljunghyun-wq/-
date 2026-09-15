#!/usr/bin/env python3
"""Pull text and embedded images out of a press-release PDF.

Usage:
    python3 extract_pdf_assets.py <input.pdf> --outdir extracted/

Writes:
    extracted/text.txt          -- all page text, concatenated
    extracted/page_XX_text.txt  -- per-page text
    extracted/images/imgNN_pXX.png -- every embedded image, in reading order

Requires PyMuPDF. Install it once with:
    pip install --quiet pymupdf

If PyMuPDF isn't available or can't be installed in this environment, fall
back to Claude's own "pdf" skill (anthropic-skills:pdf) for extraction
instead of running this script.
"""
import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print(
        "error: PyMuPDF not installed. Run `pip install --quiet pymupdf` "
        "and retry, or fall back to the pdf skill for extraction.",
        file=sys.stderr,
    )
    sys.exit(1)

MIN_IMAGE_BYTES = 8_000  # skip tiny icons/dividers/rule lines, keep real photos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", help="path to the press-release PDF")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        print(f"error: not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    outdir = Path(args.outdir)
    (outdir / "images").mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    all_text = []
    image_count = 0

    for page_index, page in enumerate(doc):
        page_no = page_index + 1
        text = page.get_text("text")
        all_text.append(f"\n===== page {page_no} =====\n{text}")
        (outdir / f"page_{page_no:02d}_text.txt").write_text(text, encoding="utf-8")

        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
            except Exception as e:  # noqa: BLE001
                print(f"warning: could not extract image xref {xref} on page {page_no}: {e}", file=sys.stderr)
                continue
            img_bytes = base["image"]
            if len(img_bytes) < MIN_IMAGE_BYTES:
                continue  # likely a logo/icon/rule, not a real photo
            ext = base.get("ext", "png")
            image_count += 1
            out_path = outdir / "images" / f"img{image_count:02d}_p{page_no:02d}.{ext}"
            out_path.write_bytes(img_bytes)
            print(f"wrote {out_path} ({len(img_bytes) // 1024} KB)")

    (outdir / "text.txt").write_text("".join(all_text), encoding="utf-8")
    print(f"\ndone: {len(doc)} page(s), {image_count} image(s) >= {MIN_IMAGE_BYTES // 1000}KB extracted.")
    if image_count == 0:
        print(
            "note: no usable embedded images found. Ask the user for separate "
            "photos, or fall back to a text-only / brand-color card design.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
