"""Step 3c/5 – page text from every downloaded PDF + scan for nationality evidence.

Usage: python -I pipeline/03c_extract_text.py pilot|full [docs_<name>.csv] [--no-ocr] [--kinds=AGM2025,BOARD2025]
       [--tickers=ticker_list.txt] [--fast]
  --tickers: OCR only these companies' documents (the text pass still covers the whole list, using cached OCR pages)
  --fast: OCR at FULL_OCR_DPI / FULL_OCR_LANG instead of OCR_DPI / vie+eng
  (default docs.csv; another list, e.g. docs_verify.csv, writes pdf_stats_verify.csv / nationality_hits_verify.csv)

Page = PDF page number (1-based), the number a reader types into a PDF viewer.
Hit types (screening only – a person still reads the page before anything becomes a record):
  FIELD            a nationality label ("Quốc tịch", "Nationality", "国籍"); Value_Raw = text right after it
  COUNTRY_NEAR_FIELD  a foreign country/demonym within FIELD_WINDOW characters after a label
  FOREIGNER_PHRASE    "người nước ngoài" / "foreign national" / "passport" etc.
Full run: only each company's main Vietnamese AR is OCR'd, in page order, stopping at the page that opens the audited
financial statements (OCR_Stopped_At_FS_Page; 0 = none found, all pages done; capN = no FS heading, OCR stopped at
page N). Settings for the full run: FULL_OCR_DPI / FULL_OCR_LANG (pages cached before the change keep 300 dpi vie+eng).
A page with fewer than TEXT_PAGE_MIN_CHARS characters, or whose text layer is garbled (fonts without a Unicode map:
more than GARBLED_CTRL_SHARE control characters), is treated as scanned and OCR'd with Tesseract
(vie+eng, OCR_DPI); OCR text is cached per page under data/<run>/ocr/ and flagged ocr=true in the JSONL,
so a hit on an OCR'd page is always re-read on the PDF image before it becomes a record.

Outputs (data/<run>/): text/<TICKER>/<file>.jsonl (page texts), pdf_stats.csv, nationality_hits.csv
"""
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import read_csv, strip_accents, write_csv
from config import DATA, ROOT

TEXT_PAGE_MIN_CHARS = 200
GARBLED_CTRL_SHARE = 0.03  # added 2026-11-01 after QA: e.g. BVL, LPB text layers are glyph codes, not text
CTRL_RE = re.compile(r"[\x00-\x08\x0b-\x1f]")


def needs_ocr(text: str) -> bool:
    """No usable text layer: (almost) empty, or garbled glyph codes."""
    return len(text.strip()) < TEXT_PAGE_MIN_CHARS or len(CTRL_RE.findall(text)) > GARBLED_CTRL_SHARE * len(text)
OCR_DPI = 300
OCR_WORKERS = max(1, (os.cpu_count() or 2) - 2)
TESS = ROOT / ".tools" / "tesseract"  # official Ubuntu packages unpacked without root (see README)
TESS_ENV = {**os.environ, "LD_LIBRARY_PATH": str(TESS / "usr/lib/x86_64-linux-gnu"),
            "TESSDATA_PREFIX": str(TESS / "usr/share/tesseract-ocr/5/tessdata"), "OMP_THREAD_LIMIT": "1"}
FIELD_WINDOW = 400
FIELD_RE = re.compile(r"quoc\s*tich|nationality|nationalities|国籍|국적")
FOREIGNER_RE = re.compile(r"nguoi nuoc ngoai|foreign national|foreigner|ho chieu|passport|thuong tru nhan|permanent resident"
                          r"|quoc tich kep|dual (?:nationality|citizenship)")
# Folded (lower-case, no accents) foreign countries and demonyms, VN + EN. Vietnam itself is not listed.
FOREIGN_TERMS = [
    "nhat ban", "han quoc", "trung quoc", "dai loan", "hong kong", "singapore", "xinh-ga-po", "thai lan", "malaysia",
    "ma-lai-xi-a", "indonesia", "philippines", "phi-lip-pin", "an do", "lao", "campuchia", "cam-pu-chia", "myanmar",
    "brunei", "hoa ky", "my", "anh", "anh quoc", "vuong quoc anh", "phap", "duc", "uc", "australia", "o-xtray-li-a", "canada",
    "ca-na-da", "ha lan", "bi", "thuy si", "thuy dien", "na uy", "dan mach", "phan lan", "y", "italia", "tay ban nha",
    "bo dao nha", "nga", "lien bang nga", "ba lan", "sec", "ao", "ai len", "ireland", "new zealand", "israel", "a rap",
    "japan", "japanese", "korea", "korean", "china", "chinese", "taiwan", "taiwanese", "singaporean", "thai", "thailand",
    "malaysian", "indonesian", "filipino", "india", "indian", "laos", "cambodia", "cambodian", "united states",
    "american", "usa", "u.s.", "united kingdom", "british", "england", "english", "france", "french", "germany", "german",
    "australian", "canadian", "netherlands", "dutch", "belgium", "belgian", "switzerland", "swiss", "sweden", "swedish",
    "norway", "norwegian", "denmark", "danish", "finland", "finnish", "italy", "italian", "spain", "spanish",
    "portugal", "portuguese", "russia", "russian", "poland", "polish", "czech", "austria", "austrian", "irish",
    "new zealander", "israeli", "uae", "emirati", "hongkonger", "macau",
]
# whole-word match on folded text; short/ambiguous VN words ("my", "y", "bi", "ao", "duc", "uc", "anh", "lao") only
# count right after a nationality label (Value_Raw), never in free text.
AMBIGUOUS = {"anh", "my", "y", "bi", "ao", "duc", "uc", "lao", "sec", "english", "thai", "nga", "phap"}
TERM_RE = re.compile(r"(?<![a-z])(" + "|".join(sorted((re.escape(t) for t in FOREIGN_TERMS), key=len, reverse=True)) + r")(?![a-z])")
VN_VALUE_RE = re.compile(r"^\W*(viet\s*nam|vietnam|vietnamese|vn)(?![a-z])")

STAT_FIELDS = ["Ticker_Local", "Doc_Kind", "Local_File", "N_Pages", "N_Text_Pages", "Text_Page_Share", "Likely_Scanned",
               "N_OCR_Pages", "OCR_Stopped_At_FS_Page", "N_Field_Hits", "N_Field_Pages", "Error"]
HIT_FIELDS = ["Ticker_Local", "Doc_Kind", "Local_File", "Page", "OCR", "Hit_Type", "Matched", "Value_Raw", "Value_Class",
              "Snippet"]


def fold(text: str) -> str:
    """Accent-folded lower-case copy with the same length as text, so match positions map back 1:1."""
    return "".join((strip_accents(c) or " ")[0] for c in text)


def value_class(v: str) -> str:
    f = fold(v).strip()
    if not f:
        return "EMPTY"
    if VN_VALUE_RE.match(f):
        return "VIETNAM"
    m = TERM_RE.match(f.lstrip(" :-–.\t"))
    return "FOREIGN" if m else "OTHER"


def field_value(text: str, end: int) -> str:
    """Text right after a nationality label: same line, or the next non-empty line if the label ends its line."""
    lines = text[end:end + 120].lstrip(" :：-–\t").split("\n")
    first = lines[0].strip(" :：-–\t|")
    if not first and len(lines) > 1:
        first = next((l.strip(" :：-–\t|") for l in lines[1:3] if l.strip()), "")
    return re.split(r"\|", first, maxsplit=1)[0].strip()[:40]


def snippet(text: str, a: int, b: int, pad: int = 250) -> str:
    return re.sub(r"\s+", " ", text[max(0, a - pad):b + pad]).strip()


def scan_page(text: str):
    f = fold(text)
    for m in FIELD_RE.finditer(f):
        value = field_value(text, m.end())
        yield "FIELD", text[m.start():m.end()], value, value_class(value), snippet(text, m.start(), m.end())
        window = f[m.end():m.end() + FIELD_WINDOW]
        for t in TERM_RE.finditer(window):
            if t.group(1) in AMBIGUOUS:
                continue
            a, b = m.end() + t.start(), m.end() + t.end()
            yield "COUNTRY_NEAR_FIELD", text[a:b], "", "", snippet(text, a, b, 150)
    for m in FOREIGNER_RE.finditer(f):
        yield "FOREIGNER_PHRASE", text[m.start():m.end()], "", "", snippet(text, m.start(), m.end())


def _ocr_task(task: tuple[str, int, str, int, str]) -> int:
    """Worker process: render one page (grey, dpi) and OCR it into the cache file."""
    pdf, i, cache, dpi, lang = task
    with pymupdf.open(pdf) as doc:
        img = doc[i].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY).tobytes("pnm")
    r = subprocess.run([str(TESS / "usr/bin/tesseract"), "stdin", "stdout", "-l", lang, "--psm", "3"],
                       input=img, capture_output=True, env=TESS_ENV, timeout=600)
    Path(cache).parent.mkdir(parents=True, exist_ok=True)
    Path(cache + ".part").write_bytes(r.stdout)
    Path(cache + ".part").replace(cache)
    return i


def ocr_cache(out_dir: Path, d: dict, i: int) -> Path:
    return out_dir / "ocr" / d["Ticker_Local"] / Path(d["Local_File"]).name / f"p{i + 1:04d}.txt"


def is_english(path: str) -> bool:
    f = Path(path).name.lower()
    return any(k in f for k in ("_en_", "eng", "english", "annualreport", "annual_report", "anual", "annunal"))


def main_ar_files(docs: list[dict]) -> set[str]:
    """Per company, the one annual report to OCR: the longest non-English AR2025 PDF with >= 5 pages
    (user decision 2026-11-01: OCR only the main Vietnamese AR; other documents only on demand)."""
    best = {}
    for d in docs:
        if d["Doc_Kind"] != "AR2025":
            continue
        try:
            with pymupdf.open(ROOT / d["Local_File"]) as doc:
                n = doc.page_count
        except Exception:
            continue
        if n < 5:
            continue
        key = (not is_english(d["Local_File"]), n)
        if d["Ticker_Local"] not in best or key > best[d["Ticker_Local"]][0]:
            best[d["Ticker_Local"]] = (key, d["Local_File"])
    return {v[1] for v in best.values()}


FS_HEADING_RE = re.compile(r"bao cao kiem toan doc lap|independent auditor|bang can doi ke toan|balance sheet"
                           r"|bao cao tinh hinh tai chinh|statement of financial position")
FS_MIN_SHARE = 0.25  # the audited FS start no earlier than this share of the AR's pages
FS_HEADING_CHARS = 400
# full run (from 2026-11-01 02:55): faster settings; pages OCR'd earlier at 300 dpi vie+eng keep their cached text
FULL_OCR_DPI = 200
FULL_OCR_LANG = "vie"
FULL_MAX_OCR_PAGE = 250  # AR without a detectable FS heading: OCR at most this many pages (was 60 until QA 2026-11-01: governance sections of long scanned ARs sit after p60)


def fs_stop_file(out_dir: Path, d: dict) -> Path:
    return out_dir / "ocr" / d["Ticker_Local"] / Path(d["Local_File"]).name / "_stopped_at_fs.txt"


def _ocr_doc_until_fs(task: tuple[str, str, str]) -> int:
    """Worker process (full run): go through one AR in page order, OCR pages without text, and stop at the first
    page whose heading opens the audited financial statements (management/governance sections come before them)."""
    pdf, cache_dir, stop_file = task
    with pymupdf.open(pdf) as doc:
        n = doc.page_count
        for i in range(n):
            text = doc[i].get_text("text")
            cache = Path(cache_dir) / f"p{i + 1:04d}.txt"
            if needs_ocr(text):
                if cache.exists():
                    text = cache.read_text(encoding="utf-8", errors="replace")
                else:
                    if i >= FULL_MAX_OCR_PAGE:
                        Path(stop_file).parent.mkdir(parents=True, exist_ok=True)
                        Path(stop_file).write_text(f"cap{FULL_MAX_OCR_PAGE}\n")
                        return -1
                    img = doc[i].get_pixmap(dpi=FULL_OCR_DPI, colorspace=pymupdf.csGRAY).tobytes("pnm")
                    r = subprocess.run([str(TESS / "usr/bin/tesseract"), "stdin", "stdout", "-l", FULL_OCR_LANG, "--psm", "3"],
                                       input=img, capture_output=True, env=TESS_ENV, timeout=600)
                    cache.parent.mkdir(parents=True, exist_ok=True)
                    cache.with_suffix(".part").write_bytes(r.stdout)
                    cache.with_suffix(".part").replace(cache)
                    text = r.stdout.decode("utf-8", errors="replace")
            if i >= FS_MIN_SHARE * n and FS_HEADING_RE.search(strip_accents(text[:FS_HEADING_CHARS])):
                Path(stop_file).parent.mkdir(parents=True, exist_ok=True)
                Path(stop_file).write_text(f"{i + 1}\n")
                return i + 1
    Path(stop_file).parent.mkdir(parents=True, exist_ok=True)
    Path(stop_file).write_text("0\n")  # no FS heading found: every page was processed
    return 0


def run_ocr_until_fs(out_dir: Path, docs: list[dict]) -> None:
    tasks = [(str(ROOT / d["Local_File"]), str(ocr_cache(out_dir, d, 0).parent), str(fs_stop_file(out_dir, d)))
             for d in docs if not fs_stop_file(out_dir, d).exists()]
    print(f"OCR (until FS): {len(tasks)} documents with {OCR_WORKERS} workers", flush=True)
    with ProcessPoolExecutor(OCR_WORKERS) as ex:
        for n, _ in enumerate(ex.map(_ocr_doc_until_fs, tasks), 1):
            if n % 25 == 0:
                print(f"  OCR docs {n}/{len(tasks)}", flush=True)


def run_ocr(out_dir: Path, docs: list[dict], dpi: int = OCR_DPI, lang: str = "vie+eng") -> None:
    """OCR every page without a usable text layer (all documents, one process pool); cached pages are skipped."""
    tasks = []
    for d in docs:
        try:
            with pymupdf.open(ROOT / d["Local_File"]) as doc:
                for i, page in enumerate(doc):
                    if needs_ocr(page.get_text("text")) and not ocr_cache(out_dir, d, i).exists():
                        tasks.append((str(ROOT / d["Local_File"]), i, str(ocr_cache(out_dir, d, i)), dpi, lang))
        except Exception:
            continue  # reported as Error in pdf_stats
    print(f"OCR: {len(tasks)} pages to do with {OCR_WORKERS} workers", flush=True)
    with ProcessPoolExecutor(OCR_WORKERS) as ex:
        for n, _ in enumerate(ex.map(_ocr_task, tasks, chunksize=4), 1):
            if n % 200 == 0:
                print(f"  OCR {n}/{len(tasks)}", flush=True)


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    no_ocr = "--no-ocr" in sys.argv  # text layer only (e.g. a first cheap pass over on-demand documents)
    only_kinds = next((x.split("=", 1)[1].split(",") for x in sys.argv if x.startswith("--kinds=")), None)
    only_tickers = next((set(Path(x.split("=", 1)[1]).read_text().split()) for x in sys.argv if x.startswith("--tickers=")), None)
    run = args[0] if args else "pilot"
    docs_file = args[1] if len(args) > 1 else "docs.csv"
    suffix = docs_file.removeprefix("docs").removesuffix(".csv")
    out_dir = DATA / run
    if run == "full" and docs_file == "docs.csv":  # merge the collection shards done so far
        done = {t for f in (out_dir / "shards").glob("done_*.txt") for t in f.read_text().split()}  # fully written companies
        all_docs = [r for f in sorted((out_dir / "shards").glob("docs_*.csv")) for r in read_csv(f) if r["Ticker_Local"] in done]
        write_csv(out_dir / "docs.csv", all_docs, list(all_docs[0].keys()))
    docs = [d for d in read_csv(out_dir / docs_file) if d["Status"] == "OK" and not d["Duplicate_Of"]]
    stats, hits = [], []
    ocr_set = main_ar_files(docs) if run == "full" and docs_file == "docs.csv" else {d["Local_File"] for d in docs}
    full_mode = run == "full" and docs_file == "docs.csv"
    todo = [d for d in docs if d["Local_File"] in ocr_set
            and not (full_mode and fs_stop_file(out_dir, d).exists())]  # run_ocr skips pages already cached
    if only_kinds:
        todo = [d for d in todo if d["Doc_Kind"] in only_kinds]
    if only_tickers:
        todo = [d for d in todo if d["Ticker_Local"] in only_tickers]
    if not no_ocr:
        if full_mode:
            run_ocr_until_fs(out_dir, todo)
        else:
            run_ocr(out_dir, todo, *((FULL_OCR_DPI, FULL_OCR_LANG) if "--fast" in sys.argv else ()))
    for d in docs:
        path = ROOT / d["Local_File"]
        st = {"Ticker_Local": d["Ticker_Local"], "Doc_Kind": d["Doc_Kind"], "Local_File": d["Local_File"],
              "N_Pages": "", "N_Text_Pages": "", "Text_Page_Share": "", "Likely_Scanned": "", "N_OCR_Pages": "",
              "OCR_Stopped_At_FS_Page": "", "N_Field_Hits": "",
              "N_Field_Pages": "", "Error": ""}
        try:
            doc = pymupdf.open(path)
        except Exception as e:
            stats.append({**st, "Error": f"{e!r}"[:200]})
            continue
        text_dir = out_dir / "text" / d["Ticker_Local"]
        text_dir.mkdir(parents=True, exist_ok=True)
        n_text, n_ocr, field_pages, n_field = 0, 0, set(), 0
        jsonl = text_dir / (path.name + ".jsonl")
        stop = fs_stop_file(out_dir, d)
        final = jsonl.exists() and (d["Local_File"] not in ocr_set
                                    or (stop.exists() and jsonl.stat().st_mtime >= stop.stat().st_mtime))
        if full_mode and final:  # done in an earlier pass: rescan the stored page texts
            texts = [(pg["text"], pg["ocr"]) for pg in map(json.loads, jsonl.open(encoding="utf-8"))]
        else:
            texts = []
            for i, page in enumerate(doc):
                t = page.get_text("text")
                if needs_ocr(t) and ocr_cache(out_dir, d, i).exists():
                    texts.append((ocr_cache(out_dir, d, i).read_text(encoding="utf-8", errors="replace"), True))
                else:
                    texts.append((t, False))
            with jsonl.open("w", encoding="utf-8") as jf:
                for i, (text, is_ocr) in enumerate(texts, 1):
                    jf.write(json.dumps({"page": i, "chars": len(text), "ocr": is_ocr, "text": text}, ensure_ascii=False) + "\n")
        for i, (text, is_ocr) in enumerate(texts, 1):
            n_text += (not is_ocr) and not needs_ocr(text)
            n_ocr += is_ocr
            for hit_type, matched, value, vclass, snip in scan_page(text):
                if hit_type == "FIELD":
                    n_field += 1
                    field_pages.add(i)
                hits.append({"Ticker_Local": d["Ticker_Local"], "Doc_Kind": d["Doc_Kind"], "Local_File": d["Local_File"],
                             "Page": i, "OCR": int(is_ocr), "Hit_Type": hit_type, "Matched": matched, "Value_Raw": value,
                             "Value_Class": vclass, "Snippet": snip})
        n = doc.page_count
        stats.append({**st, "N_Pages": n, "N_Text_Pages": n_text, "Text_Page_Share": round(n_text / n, 3) if n else "",
                      "Likely_Scanned": int(n > 0 and n_text / n < 0.5), "N_OCR_Pages": n_ocr,
                      "OCR_Stopped_At_FS_Page": fs_stop_file(out_dir, d).read_text().strip() if fs_stop_file(out_dir, d).exists() else "",
                      "N_Field_Hits": n_field,
                      "N_Field_Pages": len(field_pages)})
        if run != "full":
            print(f"{d['Ticker_Local']:5s} {d['Doc_Kind']:8s} pages={n:4d} text={n_text:4d} ocr={n_ocr:4d} field_hits={n_field:3d}  {path.name[:60]}",
                  flush=True)

    print(f"docs {len(docs)} | OCR'd this pass {len(todo)} | stats {len(stats)} | hits {len(hits)}", flush=True)
    write_csv(out_dir / f"pdf_stats{suffix}.csv", stats, STAT_FIELDS)
    write_csv(out_dir / f"nationality_hits{suffix}.csv", hits, HIT_FIELDS)


if __name__ == "__main__":
    main()
