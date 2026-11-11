"""Reviewer helper (QA, 10 Nov 2026): candidate Board / Direksi profile pages of a company's AR 2025 (a role title plus
career / education words) and whether a nationality label word appears on each.
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id_qa_boardpages.py CODE [CODE ...]
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
ROLE = re.compile(r"(?i)(komisaris utama|presiden komisaris|president commissioner|direktur utama|presiden direktur|president director|komisaris independen|independent commissioner)")
BIO = re.compile(r"(?i)(riwayat|pengalaman|career|education|pendidikan|experience|menjabat|appointed)")
LAB = re.compile(r"(?i)(warga\s*negara|kewarganegaraan|nationality|citizenship|citizen|\bwni\b|berkebangsaan)")


def main():
    rej = {r["File"] for r in csv.DictReader((D / "manual" / "ar_file_reviews.csv").open(encoding="utf-8"))
           if r["Decision"].startswith(("REJECTED", "SOURCE"))}
    ti = [r for r in csv.DictReader((D / "text_index.csv").open(encoding="utf-8")) if r.get("SHA256") and r["File"] not in rej]
    for c in sys.argv[1:]:
        out = []
        for d, r in enumerate([x for x in ti if x["Code"] == c], 1):
            pages = json.loads((D / "text" / c / f"{r['SHA256'][:12]}.json").read_text(encoding="utf-8"))["pages"]
            for k, p in enumerate(pages, 1):
                t = p["text"]
                if len(ROLE.findall(t)) >= 1 and len(BIO.findall(t)) >= 2 and len(t) > 600:
                    out.append(f"{d}:{k}{'+L' if LAB.search(t) else '-'}")
        print(c, " ".join(out[:24]))


if __name__ == "__main__":
    main()
