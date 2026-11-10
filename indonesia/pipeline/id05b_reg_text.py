"""Indonesia step 5b – page text of the BAE register reports (id03f; owner 10 Nov 2026, OPEN_DECISIONS 11a).

Most reports are scans with a garbage text layer, so every page is OCR'd (Tesseract ind+eng, 150 dpi) and both texts
are kept. Pages are tagged to find what a reviewer must read on the page image:
  COMPOSITION  "Komposisi Kepemilikan" / "Pemodal Asing" / "Pemodal Nasional" / "Lokal" + "Asing"
  XH1_1        form X.H.1-1 / "5% atau lebih" (holders >= 5 %, column Status A/I)
Screening only: the FO figure is read from the page image and recorded by hand (id_fo_batch / id_add_records).
Output  data/reg_text/<CODE>/<sha12>.json  {file, pages: [{text, ocr, tags}]};  data/reg_pages.csv  Code, File, Page, Tags, Snippet
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id05b_reg_text.py
"""
import csv, json, re, subprocess
from pathlib import Path

import fitz  # pymupdf

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
OUT = D / "reg_text"
TESS = "/opt/homebrew/bin/tesseract"
COMP = re.compile(r"(?i)komposisi\s+kepemilikan|pemodal\s+asing|pemodal\s+nasional|investor\s+asing|lokal.{0,400}asing|asing.{0,400}lokal|domestic.{0,300}foreign", re.S)
XH = re.compile(r"(?i)x\.?\s?h\.?\s?1\s?-\s?1|5\s?%\s*atau\s*lebih|status\s*a\s*/\s*i|5\s?%\s*or\s*more", re.S)


def ocr(page):
    png = page.get_pixmap(dpi=150).tobytes("png")
    r = subprocess.run([TESS, "stdin", "stdout", "-l", "ind+eng", "--psm", "6"], input=png, capture_output=True, timeout=300)
    return r.stdout.decode("utf-8", "replace")


def main():
    files = [r for r in csv.DictReader((D / "idx_reg_files.csv").open(encoding="utf-8")) if r.get("Status") == "OK"]
    idx = []
    for r in files:
        c, f = r["Code"], ROOT / r["File"]
        out = OUT / c / f"{r['SHA256'][:12]}.json"
        if out.exists():
            j = json.loads(out.read_text(encoding="utf-8"))
        else:
            pages = []
            for p in fitz.open(f):
                t, o = p.get_text(), ocr(p)
                both = t + "\n" + o
                tags = [k for k, rx in (("COMPOSITION", COMP), ("XH1_1", XH)) if rx.search(both)]
                pages.append({"text": t, "ocr": o, "tags": tags})
            j = {"file": r["File"], "pages": pages}
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
        for k, p in enumerate(j["pages"], 1):
            if p["tags"]:
                idx.append({"Code": c, "File": r["File"], "Page": k, "Tags": ";".join(p["tags"]),
                            "Snippet": re.sub(r"\s+", " ", p["ocr"])[:300]})
        print(c, Path(r["File"]).name, len(j["pages"]), "pages", sum(bool(p["tags"]) for p in j["pages"]), "tagged", flush=True)
    with (D / "reg_pages.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["Code", "File", "Page", "Tags", "Snippet"]); w.writeheader(); w.writerows(idx)
    print("tagged pages", len(idx), "in", len({x["Code"] for x in idx}), "companies")


if __name__ == "__main__":
    main()
