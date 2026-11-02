"""Step 5a – candidate list: people who may be foreign nationals, to be verified on the source page.

Usage: python -I pipeline/05a_candidates.py pilot|full

Sources of candidates (screening only – never evidence):
  FOREIGN_VALUE   a nationality label in the 2025 AR/governance report whose value is a foreign country
  NAME_SCREEN     a name in the 2025 AR that is not a well-formed Vietnamese name (03d name_screen)
  FOREIGNER_TEXT  "người nước ngoài"/"foreign national"... within FOREIGNER_WINDOW characters of a name in the AR
Priority: HIGH = foreign value, foreigner text, or >= 2 non-Vietnamese name tokens; LOW = one odd token (mostly OCR noise).
For each candidate the AR text after every mention is searched for a nationality statement (Nationality_Hint).
Rows already settled in data/manual/manager_records.csv or candidate_decisions.csv are marked, not dropped.

Output: data/<run>/candidates.csv
"""
import json
import re
import sys
from collections import defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import read_csv, strip_accents, write_csv
from config import DATA

rost = import_module("03d_roster_cafef")
scan = import_module("03c_extract_text")
ppl = import_module("03e_people_from_text")

HINT_WINDOW = 600
FOREIGNER_WINDOW = 300
FOREIGNER_RE = re.compile(r"nguoi nuoc ngoai|foreign national|foreigner|quoc tich kep|hai quoc tich|dual (?:nationality|citizenship)")
FIELDS = ["Ticker_Local", "Name", "Name_Key", "Priority", "Candidate_Source", "N_Mentions", "Pages_AR", "Pages_GOV",
          "Non_VN_Tokens", "Nationality_Hint", "Hint_Page", "Hint_Snippet", "In_CafeF_Now", "Settled", "Settled_By"]


def non_vn_tokens(name: str) -> int:
    toks = [strip_accents(t).strip(".,()") for t in name.split()]
    return sum(1 for t in toks if t and not (rost.SYLLABLE_RE.match(t) or rost.SYLLABLE_RE.match(t.replace("uu", "uy"))))


def odd_tokens(name: str) -> set[str]:
    toks = (x.strip(".,()") for x in strip_accents(name).replace("-", " ").replace(".", " ").split())
    return {x for x in toks if len(x) > 3 and not (rost.SYLLABLE_RE.match(x) or rost.SYLLABLE_RE.match(x.replace("uu", "uy")))}


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    out_dir = DATA / run
    people = [p for p in read_csv(out_dir / "people_mentions.csv") if p["Pages_AR"] or p["Pages_GOV"]]
    links = read_csv(out_dir / "nationality_links.csv")
    stats = read_csv(out_dir / "pdf_stats.csv")
    for extra in ("pdf_stats_verify.csv", "pdf_stats_fallback.csv", "pdf_stats_verify_old.csv"):  # on-demand AGM / personnel documents (05b), fallbacks (06a)
        if (out_dir / extra).exists():
            stats += read_csv(out_dir / extra)
    manual = DATA / "manual"
    settled = defaultdict(str)
    for r in read_csv(manual / "manager_records.csv"):
        settled[(r["Ticker_Local"], ppl.name_key(r["Manager_Name"]))] = "RECORD:" + (r["Nationality"] or "UNKNOWN")
    for r in read_csv(manual / "candidate_decisions.csv"):
        for nm in r["Name"].split(";"):
            m = re.fullmatch(r"\(label on p\.(\d+)\)", nm.strip())
            key = f"label on p{m.group(1)}" if m else ppl.name_key(re.sub(r"\(.*?\)", "", nm))
            settled[(r["Ticker_Local"], key)] = "DECISION:" + r["Decision"]

    # page texts per company (all of its documents), for hints and the foreigner-text rule
    pages = defaultdict(list)
    for s in stats:
        if s["Error"]:
            continue
        f = out_dir / "text" / s["Ticker_Local"] / (Path(s["Local_File"]).name + ".jsonl")
        if f.exists():
            for pg in map(json.loads, f.open(encoding="utf-8")):
                pages[s["Ticker_Local"]].append((s["Doc_Kind"], pg["page"], pg["text"]))

    cands = {}
    for p in people:
        n_bad = non_vn_tokens(p["Name"])
        if p["Name_Screen"] == "NON_VN_STYLE":
            cands[(p["Ticker_Local"], p["Name_Key"])] = {**p, "Candidate_Source": "NAME_SCREEN", "Non_VN_Tokens": n_bad,
                                                         "Priority": "HIGH" if n_bad >= 2 else "LOW"}
    for l in links:
        if l["Value_Class"] == "FOREIGN":
            key = (l["Ticker_Local"], ppl.name_key(l["Linked_Name"]) or f"label on p{l['Page']}")
            c = cands.setdefault(key, {"Ticker_Local": l["Ticker_Local"], "Name": l["Linked_Name"] or f"(label on p.{l['Page']})",
                                       "Name_Key": key[1], "N_Mentions": "", "Pages_AR": "", "Pages_GOV": "",
                                       "In_CafeF_Roster": "", "Non_VN_Tokens": non_vn_tokens(l["Linked_Name"])})
            c["Candidate_Source"] = (c.get("Candidate_Source", "") + ";FOREIGN_VALUE").strip(";")
            c["Priority"] = "HIGH"
    # names close to "người nước ngoài" etc.
    for t, pgs in pages.items():
        for kind, page, text in pgs:
            f = scan.fold(text)
            for m in FOREIGNER_RE.finditer(f):
                for nm in ppl.NAME_RE.finditer(text[max(0, m.start() - FOREIGNER_WINDOW):m.end() + FOREIGNER_WINDOW]):
                    name = ppl.clean_name(nm.group(2))
                    if len(name.split()) < 2:
                        continue
                    key = (t, ppl.name_key(name))
                    c = cands.setdefault(key, {"Ticker_Local": t, "Name": name, "Name_Key": key[1], "N_Mentions": "",
                                               "Pages_AR": "", "Pages_GOV": "", "In_CafeF_Roster": "",
                                               "Non_VN_Tokens": non_vn_tokens(name)})
                    if "FOREIGNER_TEXT" not in c.get("Candidate_Source", ""):
                        c["Candidate_Source"] = (c.get("Candidate_Source", "") + ";FOREIGNER_TEXT").strip(";")
                    c["Priority"] = "HIGH"

    # LOW names promoted by a reviewer (Chinese/Korean names often look like Vietnamese syllables)
    prom_file = manual / "candidate_promotions.csv"
    for r in (read_csv(prom_file) if prom_file.exists() else []):
        c = cands.get((r["Ticker_Local"], ppl.name_key(r["Name"])))
        if c:
            c["Priority"] = "HIGH"
            c["Candidate_Source"] = (c.get("Candidate_Source", "") + ";MANUAL_PROMOTE").strip(";")
    # a partial name ("Andrew Colin") folds into the longer one of the same company ("Andrew Colin Vallis")
    longer = {(t, k): next((k2 for (t2, k2) in cands if t2 == t and k2 != k and k2.startswith(k + " ")), "")
              for (t, k) in cands}
    rows = []
    for (t, k), c in sorted(cands.items()):
        hint = hint_page = hint_snip = hint_class = ""
        odd = [tok for tok in strip_accents(c["Name"]).replace("-", " ").split()
               if len(tok) > 2 and not (rost.SYLLABLE_RE.match(tok.strip(".,()")) or rost.SYLLABLE_RE.match(tok.replace("uu", "uy")))]
        needle = max(odd, key=len) if odd else " ".join(strip_accents(c["Name"]).split())
        for kind, page, text in pages.get(t, []):
            ft = scan.fold(text)
            for m in re.finditer(re.escape(needle.strip(".,()")), ft):
                fm = scan.FIELD_RE.search(ft, m.end(), m.end() + HINT_WINDOW)
                if not fm:
                    continue
                v = scan.field_value(text, fm.end())
                vc = scan.value_class(v)
                if vc == "FOREIGN" and hint_class != "FOREIGN" or vc == "VIETNAM" and not hint:
                    hint, hint_class, hint_page = v, vc, f"{kind} p.{page}"
                    hint_snip = scan.snippet(text, m.start(), fm.end() + 40, 120)
        st = settled.get((t, k), "") or (f"PART_OF:{longer[(t, k)]}" if longer[(t, k)] else "")
        if not st:  # spelling/OCR variant of a settled name: shares a long non-Vietnamese token ("Louis T" ~ "Louis T.Nguyen")
            mine = odd_tokens(c["Name"])
            st = next((f"VARIANT_OF:{k2} -> {v}" for (t2, k2), v in settled.items()
                       if t2 == t and mine & odd_tokens(k2)), "")
        rows.append({"Ticker_Local": t, "Name": c["Name"], "Name_Key": k, "Priority": c.get("Priority", "LOW"),
                     "Candidate_Source": c.get("Candidate_Source", ""), "N_Mentions": c.get("N_Mentions", ""),
                     "Pages_AR": c.get("Pages_AR", ""), "Pages_GOV": c.get("Pages_GOV", ""), "Non_VN_Tokens": c.get("Non_VN_Tokens", ""),
                     "Nationality_Hint": hint, "Hint_Page": hint_page, "Hint_Snippet": hint_snip,
                     "In_CafeF_Now": c.get("In_CafeF_Roster", ""), "Settled": int(bool(st)), "Settled_By": st})
    write_csv(out_dir / "candidates.csv", rows, FIELDS)
    hi = [r for r in rows if r["Priority"] == "HIGH"]
    print(f"candidates {len(rows)} | HIGH {len(hi)} in {len({r['Ticker_Local'] for r in hi})} companies | "
          f"HIGH unsettled {sum(1 for r in hi if not r['Settled'])} | with hint {sum(1 for r in hi if r['Nationality_Hint'])}")


if __name__ == "__main__":
    main()
