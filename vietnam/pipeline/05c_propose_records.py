"""Step 5c – propose records from profile blocks: a candidate's name followed, before the next person's name, by a
nationality label with a country value. Proposals are reviewed by a person (text read; OCR pages flagged for an image
check) before tools/accept step copies them into data/manual/manager_records.csv.

Usage: python -I vietnam/pipeline/05c_propose_records.py pilot|full
Output: data/<run>/proposals.csv
"""
import json
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2] / "shared")]  # python -I; country config first
from common import read_csv, strip_accents, write_csv
from config import DATA, NATIONALITY_EN

scan = import_module("03c_extract_text")
ppl = import_module("03e_people_from_text")
cand = import_module("05a_candidates")

BLOCK_MAX = 700
POSITION_RE = re.compile(r"(?i)((?:phó\s+)?chủ tịch[^\n.;•]{0,60}|thành viên[^\n.;•]{0,60}|ủy viên[^\n.;•]{0,50}|uỷ viên[^\n.;•]{0,50}"
                         r"|(?:phó\s+)?tổng giám đốc[^\n.;•]{0,40}|(?:phó\s+)?giám đốc[^\n.;•]{0,50}|kế toán trưởng|trưởng ban[^\n.;•]{0,40}"
                         r"|kiểm soát viên|(?:vice\s+)?chairman[^\n.;•]{0,40}|(?:deputy\s+)?(?:general\s+)?director[^\n.;•]{0,40}"
                         r"|member of the[^\n.;•]{0,50}|chief [a-z ]{3,30}officer|ceo|cfo)")
FIELDS = ["Ticker_Local", "Candidate", "Name_In_Doc", "Raw_Position_Guess", "Role_Group_Guess", "Nationality_Raw", "Nationality",
          "Doc_Kind", "Local_File", "Page", "OCR", "Block"]


def role_group(pos: str) -> str:
    f = strip_accents(pos)
    if re.search(r"hdqt|hoi dong quan tri|board of directors|chu tich|chairman|bod", f) and not re.search(r"ban kiem soat|supervisory", f):
        return "Board"
    if re.search(r"kiem soat|bks|supervis|ubkt|uy ban kiem toan|audit committee", f):
        return "Supervisory"
    if re.search(r"giam doc|ke toan truong|director|ceo|cfo|chief|officer|tgd", f):
        return "Executive"
    return ""


def nationality_en(raw: str) -> str:
    f = strip_accents(raw).strip(" .,:;-–")
    for k in sorted(NATIONALITY_EN, key=len, reverse=True):
        if re.match(rf"{re.escape(k)}(?![a-z])", f):
            return NATIONALITY_EN[k]
    return ""


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    R = DATA / run
    cands = [c for c in read_csv(R / "candidates.csv") if c["Priority"] == "HIGH" and c["Settled"] != "1"
             and not c["Name"].startswith("(label")]
    stats = read_csv(R / "pdf_stats.csv") + [s for f in ("pdf_stats_verify.csv", "pdf_stats_fallback.csv", "pdf_stats_verify_old.csv", "pdf_stats_verify_old2.csv") if (R / f).exists()
                                             for s in read_csv(R / f)]
    by_t = {}
    for s in stats:
        by_t.setdefault(s["Ticker_Local"], []).append(s)
    out = []
    for c in cands:
        t = c["Ticker_Local"]
        odd = sorted(cand.odd_tokens(c["Name"]), key=len, reverse=True)
        if not odd:
            continue
        needle = odd[0]
        seen = set()
        for s in by_t.get(t, []):
            f = R / "text" / t / (Path(s["Local_File"]).name + ".jsonl")
            if not f.exists():
                continue
            for pg in map(json.loads, f.open(encoding="utf-8")):
                text = pg["text"]
                folded = scan.fold(text)
                for m in re.finditer(re.escape(needle), folded):
                    # block = from the line holding the name to the next person name (or BLOCK_MAX chars)
                    start = text.rfind("\n", 0, m.start()) + 1
                    nxt = [x.start() for x in ppl.NAME_RE.finditer(text, m.end(), m.end() + BLOCK_MAX)
                           if needle not in scan.fold(x.group(0))]
                    end = min(nxt + [m.end() + BLOCK_MAX])
                    block = text[start:end]
                    fm = scan.FIELD_RE.search(scan.fold(block))
                    if not fm:
                        continue
                    val = scan.field_value(block, fm.end())
                    if scan.value_class(val) != "FOREIGN" and not nationality_en(val):
                        continue
                    key = (s["Local_File"], pg["page"], val)
                    if key in seen:
                        continue
                    seen.add(key)
                    pos = POSITION_RE.search(block[:300])
                    out.append({"Ticker_Local": t, "Candidate": c["Name"], "Name_In_Doc": text[m.start():m.end() + 30].split("\n")[0],
                                "Raw_Position_Guess": pos.group(0).strip(" -–:,") if pos else "",
                                "Role_Group_Guess": role_group(pos.group(0)) if pos else "", "Nationality_Raw": val,
                                "Nationality": nationality_en(val), "Doc_Kind": s["Doc_Kind"], "Local_File": s["Local_File"],
                                "Page": pg["page"], "OCR": int(pg["ocr"]), "Block": re.sub(r"\s+", " ", block)[:600]})
    write_csv(R / "proposals.csv", out, FIELDS)
    print("proposals", len(out), "| candidates covered", len({(r["Ticker_Local"], r["Candidate"]) for r in out}),
          "| foreign", sum(r["Nationality"] not in ("", "Vietnam") for r in out))


if __name__ == "__main__":
    main()
