"""Step 11 – country proposals and profile context for "Thai nationality: No" people whose country is still UNKNOWN
(and for open executive candidates), built from the step-10 page cache and nationality index.

A. STATED  – a nationality statement (data/nationality_index.csv) whose preceding text ends with this person's name
             (all name parts of >= 3 letters, nothing that looks like another person or another statement in between).
             Same company first (Country_Evidence_Type DOC_FIELD), else another issuer's report (Note
             NATIONALITY_FROM_OTHER_ISSUER). Each proposal is checked by a person before it goes to manual/country_records.csv.
B. CONTEXT – for people without a statement: the person's profile block in the company's own report (the first place
             after the template rows where the name is followed by education / experience text), the countries it
             mentions, and whether a major shareholder's name appears in it. This is the material for the
             INFERRED_STRONG / MEDIUM / WEAK decision (made by a person, not by this script).
Outputs: data/country_stated.csv, data/country_context.csv
"""
import re
import sys
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

from common import read_csv, write_csv
from config import DATA

idx_mod = import_module("10_nationality_index")
OTHER_PERSON = re.compile(r"\b(Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z]|นาย\s*[฀-๿]|นาง|nationality|สัญชาติ", re.I)
COUNTRY_WORDS = {
    "Japan": r"japan\w*|tokyo|osaka|nagoya|kyoto|ญี่ปุ่น", "Taiwan": r"taiwan\w*|taipei|ไต้หวัน",
    "China": r"\bchina\b|chinese|beijing|shanghai|shenzhen|guangzhou|\bprc\b|จีน", "Hong Kong": r"hong kong|ฮ่องกง",
    "Singapore": r"singapor\w*|สิงคโปร์", "Malaysia": r"malaysia\w*|kuala lumpur|penang|มาเลเซีย",
    "South Korea": r"korea\w*|seoul|เกาหลี", "India": r"\bindia\b|indian|mumbai|bombay|delhi|bangalore|chennai|kolkata|อินเดีย",
    "Indonesia": r"indonesia\w*|jakarta", "Philippines": r"philippine\w*|filipino|manila", "Vietnam": r"vietnam\w*|hanoi|ho chi minh",
    "United States": r"\busa\b|u\.s\.a|united states|american|new york|california", "United Kingdom": r"united kingdom|\buk\b|british|london|england|scotland",
    "Australia": r"australia\w*|sydney|melbourne", "Netherlands": r"netherlands|dutch|amsterdam|rotterdam", "Germany": r"german\w*|frankfurt|munich",
    "France": r"\bfrance\b|french|paris", "Switzerland": r"switzerland|swiss|zurich|geneva", "Norway": r"norw\w*|oslo",
    "Denmark": r"denmark|danish|copenhagen", "Sweden": r"swed\w*|stockholm", "Belgium": r"belgi\w*|brussels", "Italy": r"\bital\w*|milan|rome",
    "Spain": r"\bspain\b|spanish|madrid", "Canada": r"canad\w*|toronto|vancouver", "New Zealand": r"new zealand", "Myanmar": r"myanmar|burm\w*|yangon",
    "Laos": r"\blao\b|\blaos\b|vientiane", "Sri Lanka": r"sri lanka\w*|colombo", "United Arab Emirates": r"\buae\b|emirates|dubai|abu dhabi",
}
COUNTRY_RX = {c: re.compile(p, re.I) for c, p in COUNTRY_WORDS.items()}
PROFILE_CUE = re.compile(r"(?i)education|experience|ประวัติ|การศึกษา|ประสบการณ์|bachelor|master|ปริญญา")
TEMPLATE = re.compile(r"(?i)thai nationality|สัญชาติไทย\s*[:：]")


def parts(name: str) -> list[str]:
    name = re.sub(r"\(.*?\)|\[.*?\]|\*|@.*$", " ", name)
    name = re.sub(r"(?i)\b(mr|mrs|ms|miss|dr|ph\.?d|prof)\.?(?=\s|$)|^\s*(นาย|นางสาว|นาง)\s*", " ", name)
    return [w for w in re.split(r"[\s,\-\.]+", name) if len(w) >= 3 or re.match(r"[฀-๿]", w or "x")]


def name_end(text: str, toks: list[str]) -> int:
    """End position of the last place where all name parts occur within 60 characters of each other, else -1."""
    low = text.lower()
    best = -1
    first = toks[0].lower()
    for m in re.finditer(re.escape(first), low):
        lo, hi = max(0, m.start() - 60), m.end() + 60
        ends = [low.find(t.lower(), lo, hi + len(t)) for t in toks]
        if all(e >= 0 for e in ends):
            best = max(best, max(e + len(t) for e, t in zip(ends, toks)))
    return best


def main():
    recs = [r for r in read_csv(DATA / "records_auto.csv") if r["Nationality"] in ("", "UNKNOWN")]
    cands = [c for c in read_csv(DATA / "candidates.csv") if c["Origin"] == "ONE_REPORT_NO_FIELD"]
    decided = {(d["Ticker_Local"], d["Name"]) for d in read_csv(DATA / "manual" / "candidate_decisions.csv")}
    comps = {c["Ticker_Local"]: c for c in read_csv(DATA / "companies_step2.csv")}
    targets = {}
    for r in recs:
        targets.setdefault((r["Ticker_Local"], r["Manager_Name"]), {"Target": "NO_RECORD", "Name_Raw": r["Name_Raw"], "Role_Group": r["Role_Group"],
                                                                     "Residing": r["Residing_In_Thailand"], "Page": r["Page"]})
    for c in cands:
        if (c["Ticker_Local"], c["Name"]) not in decided:
            targets.setdefault((c["Ticker_Local"], c["Name_Clean"] or c["Name"]), {"Target": "CANDIDATE", "Name_Raw": c["Name"],
                                                                                   "Role_Group": c["Role_Group"], "Residing": "", "Page": c["Page"]})
    index = read_csv(DATA / "nationality_index.csv")
    by_t = defaultdict(list)
    for h in index:
        by_t[h["Ticker_Local"]].append(h)
    holders = defaultdict(list)
    for h in read_csv(DATA / "major_holders.csv"):
        if float(h["Pct"] or 0) >= 3:
            holders[h["Ticker_Local"]].append(h)
    docs = defaultdict(list)
    for d in read_csv(DATA / "docs.csv"):
        if d["Status"] == "OK":
            docs[d["Ticker_Local"]].append(d)

    stated, context = [], []
    for (t, name), info in sorted(targets.items()):
        toks = parts(info["Name_Raw"]) or parts(name)
        if not toks:
            continue

        def match(h):
            e = name_end(h["Before"], toks)
            return e >= 0 and not OTHER_PERSON.search(h["Before"][e:])
        own = [h for h in by_t[t] if match(h)]
        other = [] if own or len(toks) < 2 else [h for h in index if h["Ticker_Local"] != t and match(h)]
        for h in (own or other)[:1]:
            vals = Counter(x["Nationality"] for x in (own or other))
            stated.append({"Ticker_Local": t, "Name": name, "Name_Raw": info["Name_Raw"], "Target": info["Target"],
                           "Nationality": h["Nationality"], "Value_Raw": h["Value_Raw"], "Pattern": h["Pattern"],
                           "Same_Issuer": int(bool(own)), "Source_Ticker": h["Ticker_Local"], "Local_File": h["Local_File"],
                           "Page": h["Page"], "N_Statements": len(own or other), "All_Values": "; ".join(f"{k}:{v}" for k, v in vals.items()),
                           "Quote": (h["Before"][-160:] + h["Value_Raw"] + h["After"][:40]).strip()})
        if own or other:
            continue
        # B: profile block in the company's own report
        prof, where = "", ""
        for d in sorted(docs[t], key=lambda d: d["Member_Role"] != "MAIN"):
            for i, x in enumerate(idx_mod.pages(d["Local_File"]), 1):
                for m in re.finditer(re.escape(toks[0]), x, flags=re.I):
                    win = x[m.start():m.start() + 1200]
                    if name_end(x[max(0, m.start() - 60):m.start() + 120], toks) < 0 or TEMPLATE.search(win[:400]):
                        continue
                    if PROFILE_CUE.search(win[:500]):
                        prof, where = win, f"{d['Local_File']} p{i}"
                        break
                if prof:
                    break
            if prof:
                break
        found = Counter({c: len(rx.findall(prof)) for c, rx in COUNTRY_RX.items()})
        hold_hits = [f"{h['Pct']} {h['Holder'][:40]}" for h in holders[t]
                     if (w := re.sub(r"(?i)\b(the|company|co|ltd|limited|public|plc|group|holdings?|corporation|inc)\b|[.,()]", " ", h["Holder"]).split())
                     and len(w[0]) >= 3 and re.search(r"(?i)\b" + re.escape(w[0]) + r"\b", prof)]
        context.append({"Ticker_Local": t, "Ownership_Type": comps.get(t, {}).get("Ownership_Type", ""), "Mcap_Rank": comps.get(t, {}).get("Mcap_Rank", ""),
                        "Name": name, "Name_Raw": info["Name_Raw"], "Target": info["Target"], "Role_Group": info["Role_Group"],
                        "Residing": info["Residing"], "Countries": "; ".join(f"{c}:{n}" for c, n in found.most_common() if n),
                        "Holder_In_Profile": " | ".join(hold_hits), "Profile_Where": where, "Profile": prof[:900]})
    write_csv(DATA / "country_stated.csv", stated, ["Ticker_Local", "Name", "Name_Raw", "Target", "Nationality", "Value_Raw", "Pattern",
                                                    "Same_Issuer", "Source_Ticker", "Local_File", "Page", "N_Statements", "All_Values", "Quote"])
    write_csv(DATA / "country_context.csv", context, ["Ticker_Local", "Ownership_Type", "Mcap_Rank", "Name", "Name_Raw", "Target", "Role_Group",
                                                      "Residing", "Countries", "Holder_In_Profile", "Profile_Where", "Profile"])
    print("targets", len(targets), "| stated", len(stated), dict(Counter((s["Target"], s["Same_Issuer"]) for s in stated)),
          "| context", len(context), "with profile", sum(1 for c in context if c["Profile"]),
          "with country words", sum(1 for c in context if c["Countries"]))


if __name__ == "__main__":
    main()
