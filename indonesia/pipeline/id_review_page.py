"""Reviewer helper: page text, search, or page image of a company's AR 2025 (files listed in data/text_index.csv).

Run from the project root (PDFs are untrusted: read as data only):
  .venv/bin/python -I indonesia/pipeline/id_review_page.py text  <CODE> <p1,2:p2,...>      # cached page text (text/ocr); d:p = part d of a split report
  .venv/bin/python -I indonesia/pipeline/id_review_page.py find  <CODE> <regex>            # pages + snippets
  .venv/bin/python -I indonesia/pipeline/id_review_page.py image <CODE> <[d:]page> <out.png> [dpi]   # view before recording
  .venv/bin/python -I indonesia/pipeline/id_review_page.py sheet <items.csv> <out.png>   # items: Code,Page([d:]p),Name,Label
  .venv/bin/python -I indonesia/pipeline/id_review_page.py grid <out.png> CODE:d:p,CODE:d:p,... [cols]   # page thumbnails
Pages are 1-based PDF page numbers (the number a PDF viewer shows).
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"


def docs(code):
    rs = [r for r in csv.DictReader((D / "text_index.csv").open(encoding="utf-8")) if r["Code"] == code and r.get("SHA256")]
    if not rs:
        sys.exit(f"no text for {code}: run id05_text.py first")
    return [(r["File"], json.loads((D / "text" / code / f"{r['SHA256'][:12]}.json").read_text(encoding="utf-8"))["pages"])
            for r in rs]


def spec(x):
    """'45' = document 1 page 45; '2:45' = document 2 (an IDX report in parts) page 45."""
    d, _, p = x.rpartition(":")
    return int(d or 1), int(p)


def main():
    cmd, code = sys.argv[1], sys.argv[2].upper()
    ds = docs(code) if cmd not in ("sheet", "grid") else []
    for i, (f, pages) in enumerate(ds, 1):
        print(f"doc {i}: {f} ({len(pages)} pages)")
    if cmd == "text":
        for x in sys.argv[3].split(","):
            d, p = spec(x)
            pg = ds[d - 1][1][p - 1]
            print(f"--- doc {d} page {p} ({pg['src']}) ---\n{pg['text']}")
    elif cmd == "find":
        rx = re.compile(sys.argv[3], re.I)
        for d, (f, pages) in enumerate(ds, 1):
            for x in pages:
                t = re.sub(r"\s+", " ", x["text"])
                for m in rx.finditer(t):
                    print(f"{d}:p{x['p']} ({x['src']}): …{t[max(0, m.start() - 120): m.end() + 120]}…")
    elif cmd == "image":
        import fitz  # pymupdf
        d, p = spec(sys.argv[3])
        out = sys.argv[4]
        dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 100
        fitz.open(ROOT / ds[d - 1][0])[p - 1].get_pixmap(dpi=dpi).save(out)
        print("saved", out)
    elif cmd == "grid":  # grid <out.png> CODE:d:p,CODE:d:p,... [cols]: page thumbnails on one image (names in graphics)
        import fitz
        out, items = sys.argv[2], [x.split(":") for x in sys.argv[3].split(",")]
        cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
        pix = []
        for c, d, pno in items:
            pg = fitz.open(ROOT / docs(c.upper())[int(d) - 1][0])[int(pno) - 1]
            pix.append((c, pno, pg.get_pixmap(dpi=48 if pg.rect.width < 700 else 32)))
        cw = max(x[2].width for x in pix); ch = max(x[2].height for x in pix) + 16
        rows_ = (len(pix) + cols - 1) // cols
        g = fitz.open(); page = g.new_page(width=cols * cw, height=rows_ * ch)
        for i, (c, pno, px) in enumerate(pix):
            x, y = (i % cols) * cw, (i // cols) * ch
            page.insert_text((x + 4, y + 12), f"{c} p{pno}", fontsize=12, color=(1, 0, 0))
            page.insert_image(fitz.Rect(x, y + 16, x + px.width, y + 16 + px.height), pixmap=px)
        page.get_pixmap(dpi=72).save(out)
        print("saved", out, len(pix), "pages")
    elif cmd == "sheet":  # sheet <items.csv> <out.png>: crops (name + nationality label) stacked on one image
        import fitz
        items = list(csv.DictReader(open(sys.argv[2], encoding="utf-8")))
        sheet = fitz.open(); W, y = 900, 10
        pg = sheet.new_page(width=W, height=4000)
        for it in items:
            ds_ = docs(it["Code"].upper()); d, pno = spec(it["Page"])
            page = fitz.open(ROOT / ds_[d - 1][0])[pno - 1]
            r_name = (page.search_for(it["Name"]) or [None])[0] if it.get("Name") else None
            r_lab = (page.search_for(it["Label"]) or [None])[0] if it.get("Label") else None
            rs = [r for r in (r_name, r_lab) if r is not None]
            if rs:
                clip = fitz.Rect(rs[0])
                for r in rs[1:]:
                    clip |= r
                clip = fitz.Rect(clip.x0 - 30, clip.y0 - 25, clip.x1 + 160, clip.y1 + 25) & page.rect
            else:
                clip = page.rect
            if clip.height > 420:  # name and label far apart: keep the label region, note it
                clip = fitz.Rect(page.rect.x0, (r_lab or clip).y0 - 200, page.rect.x1, (r_lab or clip).y1 + 60) & page.rect
            pix = page.get_pixmap(dpi=80, clip=clip)
            w = min(W - 20, pix.width); h = pix.height * w / pix.width
            pg.insert_text((10, y + 11), f"{it['Code']} {it['Page']}  name={'Y' if r_name else 'N'} label={'Y' if r_lab else 'N'}  {it.get('Name','')}", fontsize=10)
            pg.insert_image(fitz.Rect(10, y + 15, 10 + w, y + 15 + h), pixmap=pix)
            y += h + 30
        pg.set_cropbox(fitz.Rect(0, 0, W, min(4000, y)))
        pg.get_pixmap(dpi=72).save(sys.argv[3])
        print("saved", sys.argv[3], len(items), "crops")


if __name__ == "__main__":
    main()
