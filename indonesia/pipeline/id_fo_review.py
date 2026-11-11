"""Reviewer helper for FO by hand: for each NEEDS_MANUAL firm (data/fo_classification.csv), the KSEI bounds and the lines
with a percentage on the pages that look like a shareholder list (best 2 pages).
Run:  .venv/bin/python -I indonesia/pipeline/id_fo_review.py [first] [count]
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
KEY = re.compile(r"(?i)pemegang saham|shareholder|kepemilikan|ownership")
PCT = re.compile(r"\d{1,3}[.,]\d{1,4}\s*%|\d{1,3}\s*%")


def main():
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    fo = [r for r in csv.DictReader((D / "fo_classification.csv").open(encoding="utf-8")) if r["FO_Status"].startswith("NEEDS_MANUAL")]
    ti = [r for r in csv.DictReader((D / "text_index.csv").open(encoding="utf-8")) if r.get("SHA256")]
    rej = {r["File"] for r in csv.DictReader((D / "manual" / "ar_file_reviews.csv").open(encoding="utf-8")) if r["Decision"].startswith("REJECTED")}
    for r in fo[a:a + n]:
        c = r["Code"]
        print(f'#### {c} KSEI {float(r["FO_Lower"] or 0)*100:.1f}-{float(r["FO_Upper"] or 1)*100:.1f}% {r["FO_Status"]}')
        cands = []
        for d, t in enumerate([x for x in ti if x["Code"] == c], 1):
            if t["File"] in rej:
                continue
            pages = json.loads((D / "text" / c / f"{t['SHA256'][:12]}.json").read_text(encoding="utf-8"))["pages"]
            for k, p in enumerate(pages, 1):
                txt = p["text"]
                low = txt.lower()
                sc = 3 * len(re.findall(r"pemegang saham|shareholders?", low)) + len(PCT.findall(txt))
                if re.search(r"31 desember 2025|december 31, 2025|2025", low) and re.search(r"pemegang saham|shareholder", low):
                    sc += 5
                if re.search(r"komposisi pemegang saham|shareholders? composition|pemegang saham utama|5% atau lebih", low):
                    sc += 15
                if re.search(r"entitas anak|subsidiar|mata uang asing|foreign currenc", low):
                    sc -= 10
                cands.append((sc, d, k, txt))
        for sc, d, k, txt in sorted(cands, key=lambda x: -x[0])[:2]:
            ls = [re.sub(r"\s+", " ", x).strip() for x in txt.split("\n")]
            out = []
            for i, x in enumerate(ls):
                if PCT.search(x) or (re.match(r"^[\d.,]+$", x) and i and re.search(r"[A-Za-z]", ls[i - 1])):
                    out.append((ls[i - 1][:45] + " | " if not re.search(r"[A-Za-z]{3}", x) else "") + x[:90])
            print(f'  {d}:{k} score {sc}: ' + " || ".join(out[:14])[:900])


if __name__ == "__main__":
    main()
