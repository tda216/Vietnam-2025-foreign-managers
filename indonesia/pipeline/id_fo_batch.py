"""Write hand-read FO decisions (owner 8a: the rest read by hand) as an ownership batch for id_add_records.py.
  import sys; sys.path.insert(0, "indonesia/pipeline"); from id_fo_batch import *
  own(code, doc_no, page, fo_class, fo_pct, method, anchor, length=..., as_of=..., note=...)
The quote is cut verbatim from the page text starting at `anchor` (case-insensitive)."""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
ti = [r for r in csv.DictReader((D / "text_index.csv").open(encoding="utf-8")) if r.get("SHA256")]
O = []


def page_text(code, d, p):
    r = [x for x in ti if x["Code"] == code][d - 1]
    pg = json.loads((D / "text" / code / f"{r['SHA256'][:12]}.json").read_text(encoding="utf-8"))["pages"]
    return r["File"], re.sub(r"\s+", " ", pg[p - 1]["text"])


def own(code, d, p, cls, pct, method, anchor, length=160, as_of="2025-12-31", note=""):
    f, t = page_text(code, d, p)
    i = t.lower().find(anchor.lower())
    if i < 0:
        print("ANCHOR NOT FOUND:", code, d, p, anchor); return
    O.append({"Code": code, "FO_Class": cls, "FO_Pct": pct, "Method": method, "File": f, "Page": str(p),
              "Quote": t[i:i + length].strip(), "As_Of": as_of, "Note": note})


def save(path):
    Path(path).write_text(json.dumps({"ownership": O}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(O), "ownership rows ->", path)
