"""Step ph06: OCR the pages without a text layer of selected 17-A PDFs and screen them for non-Filipino nationality labels.

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph06_ocr_17a.py <targets.csv> [--max-page 100]

targets.csv columns: Symbol, File_Substring   (the 17-A PDF saved under philippines/raw/pse/<Symbol>/*/)
Reads  the PDFs (untrusted input, rendered as images only, never executed)
Writes philippines/data/ocr/<Symbol>/<file_id>_p<N>.txt   OCR text per page (cache; pages are not re-OCR'd)
       philippines/data/ocr_hits_17a.csv                  screening hits on OCR text (same HIGH/LOW logic as ph05)

OCR output is NOISY: a hit is only a pointer. Open the page image (render with PyMuPDF) before recording anything.
Tesseract: Homebrew build at /opt/homebrew/bin/tesseract (lang eng), 200 dpi.
"""
import csv
import importlib.util
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "philippines" / "raw" / "pse"
DATA = ROOT / "philippines" / "data"
OCR = DATA / "ocr"
TESS = "/opt/homebrew/bin/tesseract"
DPI = 200

spec = importlib.util.spec_from_file_location("ph05", Path(__file__).resolve().parent / "ph05_scan_17a_nationality.py")
ph05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph05)


def find_pdf(symbol, sub):
    out = []
    for mp in (RAW / symbol).glob("*/meta.json"):
        m = json.loads(mp.read_text(encoding="utf-8"))
        if m["form"] != "17-1":
            continue
        for f in m["files"]:
            n = f.get("saved_as", "")
            if sub in n and n.lower().endswith(".pdf"):
                out.append((mp.parent / n, m))
    if len(out) != 1:
        raise SystemExit(f"{len(out)} PDFs match {symbol} {sub}")
    return out[0]


def ocr_page(args):
    pdf, pno, dest = args
    if dest.exists():
        return dest
    try:
        doc = fitz.open(pdf)
        page = doc[pno - 1]
        if len(page.get_text()) >= 80:  # has a text layer; no OCR needed
            dest.write_text(page.get_text(), encoding="utf-8")
            return dest
        png = page.get_pixmap(dpi=DPI).tobytes("png")
        r = subprocess.run([TESS, "stdin", "stdout", "-l", "eng", "--psm", "6"], input=png, capture_output=True, timeout=180)
        dest.write_text(r.stdout.decode("utf-8", "replace"), encoding="utf-8")
    except Exception as e:  # keep going; the page is reported as failed
        dest.write_text(f"[OCR FAILED: {e}]", encoding="utf-8")
    return dest


def main():
    targets = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    maxp = int(sys.argv[sys.argv.index("--max-page") + 1]) if "--max-page" in sys.argv else 100
    hits = []
    for t in targets:
        pdf, meta = find_pdf(t["Symbol"], t["File_Substring"])
        n = min(len(fitz.open(pdf)), maxp)
        d = OCR / t["Symbol"]
        d.mkdir(parents=True, exist_ok=True)
        fid = re.search(r"att_(\d+)_", pdf.name).group(1)
        jobs = [(str(pdf), p, d / f"{fid}_p{p}.txt") for p in range(1, n + 1)]
        with ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(ocr_page, jobs))
        print(t["Symbol"], pdf.name[:50], "pages OCR'd/read:", n, flush=True)
        for p in range(1, n + 1):
            flat = re.sub(r"\s+", " ", (d / f"{fid}_p{p}.txt").read_text(encoding="utf-8"))
            seen = set()
            for m in ph05.HIGH_RE.finditer(flat):
                term = ph05.norm(m.group(1) or m.group(2))
                seen.add(term)
                hits.append({"Symbol": t["Symbol"], "File": pdf.name, "Page": p, "Level": "HIGH", "Term": term,
                             "Context": flat[max(0, m.start() - 140): m.end() + 80]})
            for term in sorted({ph05.norm(m.group(1)) for m in ph05.LOW_RE.finditer(flat)} - seen):
                m = re.search(r"\b" + re.escape(term) + r"\b", flat)
                hits.append({"Symbol": t["Symbol"], "File": pdf.name, "Page": p, "Level": "LOW", "Term": term,
                             "Context": flat[max(0, m.start() - 120): m.end() + 80]})
    if hits:
        with open(DATA / "ocr_hits_17a.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(hits[0]))
            w.writeheader()
            w.writerows(hits)
    print("OCR hits:", len(hits), "(HIGH:", sum(h["Level"] == "HIGH" for h in hits), ")")


if __name__ == "__main__":
    main()
