"""Reviewer helper (QA, 10 Nov 2026): for each company, the text just before every nationality label of the AR 2025
(who the label belongs to) and any non-Indonesian label value. Used to check that a NONE_FOUND firm's Board / Direksi
profiles really carry nationality labels (KOCI / MBSS / MEJA lesson: labels of committee members, the internal-audit
head or an HR sentence are not enough).
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id_qa_labels.py CODE [CODE ...] [--max 8]
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
LAB = re.compile(r"(?i)(warga\s*negara|kewarganegaraan|nationality|citizenship|citizen|berkebangsaan)")
SKIP = {"usia", "age", "domisili", "domicile", "riwayat", "tempat", "the", "and", "of", "background", "dan", "or",
        "status", "data", "pribadi", "personal", "information", "periode", "jabatan", "dasar", "gender"}


def main():
    args = sys.argv[1:]
    mx = int(args[args.index("--max") + 1]) if "--max" in args else 8
    codes = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--max")]
    rej = {r["File"] for r in csv.DictReader((D / "manual" / "ar_file_reviews.csv").open(encoding="utf-8"))
           if r["Decision"].startswith(("REJECTED", "SOURCE"))}
    ti = [r for r in csv.DictReader((D / "text_index.csv").open(encoding="utf-8")) if r.get("SHA256") and r["File"] not in rej]
    for c in codes:
        print(f"######## {c}")
        shown = 0
        for d, r in enumerate([x for x in ti if x["Code"] == c], 1):
            pages = json.loads((D / "text" / c / f"{r['SHA256'][:12]}.json").read_text(encoding="utf-8"))["pages"]
            for k, p in enumerate(pages, 1):
                t = re.sub(r"\s+", " ", p["text"])
                for m in LAB.finditer(t):
                    after = re.findall(r"[A-Za-z]+", t[m.end():m.end() + 80])
                    vals = [w.lower() for w in after if w.lower() not in SKIP and w.lower() not in
                            ("warga", "negara", "kewarganegaraan", "nationality", "citizenship", "citizen")][:2]
                    ind = any(v.startswith("indonesia") for v in vals)
                    if ind and shown < mx:
                        shown += 1
                        print(f"  {d}:{k} …{t[max(0, m.start() - 110):m.start()]}")
                    elif not ind and vals and vals[0] in ("singapura", "singapore", "malaysia", "japan", "jepang", "india",
                                                          "china", "korea", "thailand", "australia", "amerika", "inggris"):
                        print(f"  !! {d}:{k} {t[max(0, m.start() - 60):m.end() + 40]}")


if __name__ == "__main__":
    main()
