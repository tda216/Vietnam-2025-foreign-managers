"""Helpers to write review batches for id_add_records.py (import from a short batch script).

  import sys; sys.path.insert(0, "indonesia/pipeline"); from id_batch_helpers import *
  add(code, doc_no, page, name, raw_position, role_group, country, ap=..., note=...)   # quote cut around the screen label
  save("indonesia/data/manual/batches/id_batch_<date>_<n>.json")
The quote is cut verbatim from the page text around the k-th screen hit of that country; id_add_records.py checks it.
"""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
ti = list(csv.DictReader((D / "text_index.csv").open(encoding="utf-8")))
hits = list(csv.DictReader((D / "screen_nationality.csv").open(encoding="utf-8")))
_c, R = {}, []
CI = "BOARD_COMMITTEE_ONLY: committee member, not a Commissioner/Director; Management_Include left for the research team"
IMG = "Name / position from the page graphic (page image viewed)"
B, E, O = "Board", "Executive", "Other_Manager"


def F(code, d):
    return [x for x in ti if x["Code"] == code and x.get("SHA256")][d - 1]["File"]


def text(code, d, p):
    f = F(code, d)
    if f not in _c:
        sha = [x for x in ti if x["File"] == f][0]["SHA256"][:12]
        _c[f] = json.loads((D / "text" / code / f"{sha}.json").read_text(encoding="utf-8"))["pages"]
    return re.sub(r"\s+", " ", _c[f][p - 1]["text"])


def Q(code, d, p, country, k=0, before=70, after=40):
    f = F(code, d)
    hs = [h for h in hits if h["File"] == f and h["Page"] == str(p) and h["Country"] == country]
    if not hs:
        raise LookupError(f"no {country} hit on {code} {d}:{p}")
    t = text(code, d, p)
    raw = hs[min(k, len(hs) - 1)]["Raw"]
    ms = [m.start() for m in re.finditer(re.escape(raw).replace(r"\ ", r"\s*"), t, re.I)]
    i = ms[min(k, len(ms) - 1)]
    a = t.rfind(" ", 0, max(0, i - before)) + 1
    b = t.find(" ", i + len(raw) + after)
    return t[a: b if b > 0 else None].strip(), raw


def add(code, d, page, name, pos, rg, nat, quote=None, raw=None, k=0, ap="", rs="", note="", other=""):
    try:
        if quote is None:
            quote, raw0 = Q(code, d, page, nat, k)
            raw = raw or raw0
    except LookupError as e:
        print("SKIPPED:", e, name)
        return
    R.append({"Code": code, "File": F(code, d), "Page": page, "Manager_Name": name, "Raw_Position": pos, "Role_Group": rg,
              "Nationality": nat, "Nationality_Raw": raw or "", "Evidence_Quote": quote, "Appointed_Date": ap,
              "Resigned_Date": rs, "Note": note, "Other_Sources": other})


def save(path):
    Path(path).write_text(json.dumps({"records": R}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(R), "records ->", path)
