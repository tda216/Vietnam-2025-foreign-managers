"""Indonesia step 5 – page text of the AR 2025 files (text layer; OCR ind+eng only where a page has no text layer).

Documents: data/web_ar_files.csv (id03 download), data/idx_ar_files.csv (id03d, IDX; an AR may be in parts:
every part is a document) and data/manual_ar_files.csv (id03c register). Per company the
VERIFIED files (or files CONFIRMED_AR2025 in data/manual/ar_file_reviews.csv) are used; if none is, every file is used and Doc_Check says so.
Files are untrusted: opened with pymupdf / rendered to PNG for Tesseract only, never executed.

Output  data/text/<CODE>/<sha12>.json  {"file", "sha256", "pages": [{"p": 1-based PDF page, "src": text|ocr, "text"}]}
        data/text_index.csv            Code, File, SHA256, Doc_Check, Pages, Text_Pages, OCR_Pages, Chars
Run from the project root:
  .venv/bin/python -I indonesia/pipeline/id05_text.py <codes.csv | CODE ...> [--workers 4] [--no-ocr]
A document already in data/text/ is not redone (delete its json to redo it); a --no-ocr json gets its OCR on the next
run without --no-ocr (ocr_done flag). Fast order: run with --no-ocr first, then again for OCR.
"""
import csv, hashlib, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz  # pymupdf

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
TEXT = D / "text"
TESS = "/opt/homebrew/bin/tesseract"
DPI, MIN_CHARS = 200, 40


def rows(name):
    p = D / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def docs_for(codes):
    by = {}
    conf = {r["File"] for r in rows("manual/ar_file_reviews.csv") if r["Decision"] == "CONFIRMED_AR2025"}
    rejected = {r["File"] for r in rows("manual/ar_file_reviews.csv") if r["Decision"].startswith("REJECTED")}
    for src, name in (("web", "web_ar_files.csv"), ("idx", "idx_ar_files.csv"), ("manual", "manual_ar_files.csv")):
        for r in rows(name):
            if r.get("File") in conf:
                r = dict(r, Check="VERIFIED")  # first-pages check failed (e.g. image cover), confirmed by a reviewer
            if r["Code"] in codes and r.get("File") and (ROOT / r["File"]).exists():
                by.setdefault(r["Code"], []).append((src, r))
    out = []
    for c, rs in by.items():
        # website files only when checked (a CHECK file can be the 2024 report); IDX files are identified by the IDX
        # record (issuer, report type rda, year) even when a scan fails the first-pages check; manual files as checked
        ok = [r for s, r in rs if r["Check"] in ("VERIFIED", "SET_VERIFIED", "IDX_RECORD")
              or (s == "idx" and r["Check"].startswith("CHECK"))]
        out += [(c, r["File"], r["Check"]) for r in ok if r["File"] not in rejected]
    return out


def ocr(page):
    png = page.get_pixmap(dpi=DPI).tobytes("png")
    r = subprocess.run([TESS, "stdin", "stdout", "-l", "ind+eng", "--psm", "3"], input=png,
                       capture_output=True, timeout=300)
    return r.stdout.decode("utf-8", "replace")


def do_doc(code, rel, chk, use_ocr, pool):
    f = ROOT / rel
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    out = TEXT / code / f"{h[:12]}.json"
    j = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    if j is None or (use_ocr and not j.get("ocr_done", True)):  # older files (no flag) were OCR-ed
        pages = j["pages"] if j else [{"p": i + 1, "src": "text", "text": pg.get_text()} for i, pg in enumerate(fitz.open(f))]
        need = [x for x in pages if x["src"] == "text" and len(x["text"].strip()) < MIN_CHARS]
        if use_ocr and need:
            # each worker opens its own handle: pymupdf documents are not thread-safe
            def one(x):
                return ocr(fitz.open(f)[x["p"] - 1])
            for x, t in zip(need, pool.map(one, need)):
                if len(t.strip()) > len(x["text"].strip()):
                    x.update(src="ocr", text=t)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"file": rel, "sha256": h, "pages": pages, "ocr_done": use_ocr}, ensure_ascii=False), encoding="utf-8")
    pages = json.loads(out.read_text(encoding="utf-8"))["pages"]
    return {"Code": code, "File": rel, "SHA256": h, "Doc_Check": chk, "Pages": len(pages),
            "Text_Pages": sum(x["src"] == "text" and len(x["text"].strip()) >= MIN_CHARS for x in pages),
            "OCR_Pages": sum(x["src"] == "ocr" for x in pages), "Chars": sum(len(x["text"]) for x in pages)}


def main():
    args = sys.argv[1:]
    workers = int(args[args.index("--workers") + 1]) if "--workers" in args else 4
    rest = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--workers")]
    codes = {r["Code"] for r in csv.DictReader(open(rest[0], encoding="utf-8"))} if rest and rest[0].endswith(".csv") else set(rest)
    todo = docs_for(codes)
    print("documents", len(todo), "for", len({t[0] for t in todo}), "of", len(codes), "companies", flush=True)
    idx = {(r["Code"], r["File"]): r for r in rows("text_index.csv")}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, (c, rel, chk) in enumerate(todo):
            try:
                r = do_doc(c, rel, chk, "--no-ocr" not in args, pool)
            except Exception as e:  # keep going; record the failure
                r = {"Code": c, "File": rel, "Doc_Check": f"TEXT_ERROR {type(e).__name__}"}
            idx[(c, rel)] = r
            print(i + 1, c, r.get("Pages"), "pages,", r.get("OCR_Pages"), "OCR", r["Doc_Check"], flush=True)
    keys = ["Code", "File", "SHA256", "Doc_Check", "Pages", "Text_Pages", "OCR_Pages", "Chars"]
    with (D / "text_index.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        w.writerows(sorted(idx.values(), key=lambda r: (r["Code"], r["File"])))
    print("missing documents:", sorted(codes - {t[0] for t in todo}))


if __name__ == "__main__":
    main()
