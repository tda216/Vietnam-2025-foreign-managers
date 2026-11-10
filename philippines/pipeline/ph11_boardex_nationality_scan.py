"""Step ph11: fill BoardEx's undisclosed nationalities from the company's own FY2025 filings (screen + strict auto-accept).

Run from the repository root:
  .venv/bin/python -I philippines/pipeline/ph11_boardex_nationality_scan.py scan     -> data/boardex_nationality_hits.csv
  .venv/bin/python -I philippines/pipeline/ph11_boardex_nationality_scan.py accept   -> appends STRICT 'Filipino' hits to
                                                                               data/manual/boardex_nationality_fill.csv
Scope: eligible BoardEx people with undisclosed nationality at companies where a manager search is required.
Documents: the company's 2026 17-1 (FY2025 SEC 17-A) and 17-5 (Information Statement) PDFs + cached OCR text.

A hit is STRICT when the nationality word sits directly after the person's name, as in the SEC director/officer formats:
  S1 'Name, Filipino, 58, ...'   S2 'Name, 58, Filipino ...'   S3 'Name ... Citizenship: Filipino' (first citizenship field
  of the person's bio block, within 300 characters and before any other 'Citizenship' field).
Only STRICT hits that say Filipino, with one consistent label, are accepted automatically (Is_Foreign = 0). Foreign, dual or
conflicting labels are listed for manual review and, once read, recorded with ph_add_records.py (they become filing records).
Screening only otherwise: LOOSE hits (label somewhere near the name) are not evidence.
"""
import csv
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PH = ROOT / "philippines"
DATA = PH / "data"
RAW = PH / "raw" / "pse"
sys.path.insert(0, str(HERE))
from ph10_build_workbook import boardex_eligibility, norm_tokens  # noqa: E402

spec = importlib.util.spec_from_file_location("ph05", HERE / "ph05_scan_17a_nationality.py")
ph05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph05)
DEM = {k.lower(): v for k, v in ph05.DEMONYMS.items()}
DEM.update({"filipino": "Philippines", "filipina": "Philippines"})
LAB = r"(Filipin[oa]|" + "|".join(re.escape(k) for k in sorted(DEM, key=len, reverse=True) if k not in ("filipino", "filipina")) + r")"
LABS = LAB + r"(?:\s*(?:/|and|&|,)\s*" + LAB + r")?"
SUFFIX = r"(?:\s*,?\s*(?:Jr|Sr|III|II|IV)\.?)?"
S1 = re.compile(r"^" + SUFFIX + r"\s*[,(–-]\s*" + LABS + r"\b", re.I)
S2 = re.compile(r"^" + SUFFIX + r"\s*[,(]?\s*(?:aged?\s*)?\d{2}\s*(?:years old)?\s*[,)]?\s*(?:years old,?\s*)?" + LABS + r"\b", re.I)
S3 = re.compile(r"Citizenship\s*[:\-]?\s*" + LABS + r"\b", re.I)
S5 = re.compile(r"^" + SUFFIX + r"\s*" + LABS + r"\s*,?\s*(?:aged?\s*)?\d{2}\b", re.I)  # 'NAME Filipino, 56 years old'
# S4 (table row): on a page with a Citizenship/Nationality column, the first nationality word within 110 characters after the
# name, with no other person's name (First M. Last) in between and not part of a phrase such as 'every Filipino'.
LAB_ANY = re.compile(r"\b" + LABS + r"\b", re.I)
OTHER_NAME = re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)* [A-Z]\. [A-Z][a-zA-Z-]+")
PHRASE_BEFORE = re.compile(r"(?i)\b(every|the|for|of|to|our|a|many|more|young)\s*$")
DITTO = re.compile(r"(?i)-do-|\bditto\b|\bsame as above\b")
CAPS_SEQ = re.compile(r"\b[A-Z][A-Z'-]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][A-Z'-]+){1,4}\b")
TITLE_WORDS = set("""VICE PRESIDENT SENIOR SR EXECUTIVE CHIEF OFFICER DIRECTOR INDEPENDENT NON CHAIRMAN CHAIRPERSON CHAIR TREASURER SECRETARY
CORPORATE FINANCIAL FINANCE COMPLIANCE HEAD MANAGER GENERAL ASSISTANT FIRST AND OF THE BOARD AUDIT RISK LEGAL OPERATING OPERATIONS
INFORMATION TECHNOLOGY HUMAN RESOURCES MARKETING SALES INVESTOR RELATIONS CONTROLLER COMPTROLLER DEPUTY GROUP PRESIDENT CEO CFO COO
CTO CIO CRO EVP SVP FVP AVP VP MD SD NED ED LEAD MEMBER COMMITTEE STRATEGY BUSINESS UNIT DIVISION DEPARTMENT ACCOUNTING TAX
INTERNAL EXTERNAL AFFAIRS PUBLIC GOVERNANCE DATA PROTECTION COMMERCIAL TECHNICAL PLANNING DEVELOPMENT INVESTMENTS INVESTMENT
TRUST BANKING RETAIL CONSUMER PROJECT PROJECTS SUPPLY CHAIN ENGINEERING PRODUCTION PLANT MANUFACTURING FILIPINO DIRECT INDIRECT
COMMON SHARES NIL NONE YES NO""".split())


def other_person_between(seg):
    if OTHER_NAME.search(seg) or DITTO.search(seg):
        return True
    return any(set(m.group(0).replace(".", " ").split()) - TITLE_WORDS - {w for w in m.group(0).split() if len(w) <= 2}
               for m in CAPS_SEQ.finditer(seg))
FIELDS = ["Symbol", "BoardEx_Director_ID", "Manager_Name", "Positions", "Hit_Class", "Pattern", "Label", "Country", "Is_Foreign",
          "Dual", "N_Strict_Hits", "Labels_Seen", "File", "Page", "Name_In_Text", "Snippet", "Source", "Source_URL", "Local_File"]


def name_regex(name):
    toks = [t for t in re.sub(r"[^A-Za-z' ]", " ", name).split() if len(t) > 1 and t.lower() not in
            {"jr", "sr", "ii", "iii", "iv", "dr", "atty", "mr", "ms", "mrs", "engr", "doctor"}]
    if len(toks) < 2:
        return None
    f, l = re.escape(toks[0]), re.escape(toks[-1])
    return re.compile(r"\b(?:" + f + r"\W+(?:[\w.'-]+\W+){0,4}?" + l + r"|" + l + r",\s*" + f + r"(?:\W+[\w.'-]+){0,3})\b", re.I)


def docs(sym):
    out = []
    metas = [(mp, json.loads(mp.read_text(encoding="utf-8"))) for mp in sorted((RAW / sym).glob("*/meta.json"))]
    # FY2025 documents: 2026 filings; for fiscal years not ending in December (or no 2026 17-A), the 2025 17-A / Information Statement
    has_2026_17a = any(m["form"] == "17-1" and "2026" in m["announced"] for _, m in metas)
    for mp, m in metas:
        if m["form"] not in ("17-1", "17-5") or not ("2026" in m["announced"] or (not has_2026_17a and "2025" in m["announced"])):
            continue
        src = f"{m['template']} ({m['form']}) {m['report_no']}, announced {m['announced']}"
        for f in m["files"]:
            n = f.get("saved_as", "")
            if not n.lower().endswith(".pdf"):
                continue
            try:
                d = fitz.open(mp.parent / n)
            except Exception:
                continue
            for i, p in enumerate(d, 1):
                t = re.sub(r"\s+", " ", p.get_text())
                if len(t) < 80:
                    ocr = DATA / "ocr" / sym / f"{n.split('_')[1] if n.startswith('att_') else n}_p{i}.txt"
                    if ocr.exists():
                        t = re.sub(r"\s+", " ", ocr.read_text(encoding="utf-8", errors="ignore"))
                out.append((n, i, t, src, m["viewer_url"], str((mp.parent / n).relative_to(ROOT))))
    return out


def classify(label):
    parts = [p for p in re.split(r"\s*(?:/|and|&|,)\s*", label.strip()) if p]
    countries = [DEM.get(p.lower(), "") for p in parts]
    foreign = [c for c in countries if c and c != "Philippines"]
    dual = len(set(countries)) > 1
    return (", ".join(dict.fromkeys(c for c in countries if c)), "1" if foreign else ("0" if countries and all(countries) else ""),
            "1" if dual else "")


def scan():
    # keys: local symbol (boardex_roles.csv carries the local symbol, the other files the Bloomberg ticker)
    fo = {r["Ticker"].split()[0]: r for r in csv.DictReader(open(DATA / "fo_final.csv", encoding="utf-8"))}
    comps = {r["Ticker"].split()[0]: r for r in csv.DictReader(open(DATA / "companies_boardex.csv", encoding="utf-8-sig"))}
    people = defaultdict(dict)
    for r in csv.DictReader(open(DATA / "boardex_roles.csv", encoding="utf-8-sig")):
        sym = r["Ticker"].split()[0]
        if r["Is_Foreign"] != "" or fo.get(sym, {}).get("Manager_Search") != "Y" or not comps.get(sym, {}).get("BoardEx_Coverage", "").startswith("MATCHED"):
            continue
        if not boardex_eligibility(r)[2]:
            continue
        p = people[sym].setdefault(r["BoardEx_Director_ID"], {"name": r["Manager_Name"], "pos": []})
        p["pos"].append(r["Raw_Position"])
    out = []
    for sym in sorted(people):
        pages = docs(sym)
        for did, p in people[sym].items():
            rx = name_regex(p["name"])
            strict, loose = [], []
            if rx and pages:
                for n, i, t, src, url, lf in pages:
                    for m in rx.finditer(t):
                        after = t[m.end(): m.end() + 300]
                        h = S1.match(after) or S2.match(after) or S5.match(after)
                        pat = ("S1" if S1.match(after) else "S2" if S2.match(after) else "S5") if h else ""
                        if not h:
                            c = S3.search(after)
                            if c and "citizenship" not in after[:c.start()].lower():
                                h, pat = c, "S3"
                        if not h and re.search(r"(?i)citizenship|nationality", t):
                            c = LAB_ANY.search(after[:110])
                            if c and not other_person_between(after[:c.start()]) and not PHRASE_BEFORE.search(after[:c.start()]):
                                h, pat = c, "S4_TABLE"
                        # a generational suffix must agree (Andres Soriano IV is not Andres Soriano III)
                        want_sfx = re.findall(r"\b(Jr|Sr|II|III|IV)\b\.?", p["name"])
                        got_sfx = re.match(r"\s*,?\s*(Jr|Sr|II|III|IV)\b", after)
                        if h and ((want_sfx and (not got_sfx or got_sfx.group(1).lower() != want_sfx[-1].lower()))
                                  or (not want_sfx and got_sfx and got_sfx.group(1) in ("III", "IV", "II"))):
                            h = None
                        snip = t[max(0, m.start() - 40): m.end() + (h.end() if h else 120) + 30]
                        if h:
                            strict.append((pat, h.group(0).split(":")[-1].strip(" ,(–-") if pat == "S3" else
                                           re.search(LABS, h.group(0), re.I).group(0), n, i, m.group(0), snip, src, url, lf))
                        elif re.search(r"(?i)\bfilipin|citizen", after[:150]):
                            loose.append(("LOOSE", "", n, i, m.group(0), snip, src, url, lf))
            labels = Counter(classify(s[1])[0] for s in strict)
            row = {"Symbol": sym, "BoardEx_Director_ID": did, "Manager_Name": p["name"], "Positions": "; ".join(dict.fromkeys(p["pos"])),
                   "N_Strict_Hits": len(strict), "Labels_Seen": "; ".join(f"{k}:{v}" for k, v in labels.items())}
            if strict:
                best = strict[0]
                country, isf, dual = classify(best[1])
                row.update(Hit_Class="STRICT" if len(labels) == 1 else "STRICT_CONFLICT", Pattern=best[0], Label=best[1], Country=country,
                           Is_Foreign=isf, Dual=dual, File=best[2], Page=best[3], Name_In_Text=best[4], Snippet=best[5][:400],
                           Source=best[6], Source_URL=best[7], Local_File=best[8])
            elif loose:
                b = loose[0]
                row.update(Hit_Class="LOOSE", File=b[2], Page=b[3], Name_In_Text=b[4], Snippet=b[5][:400], Source=b[6], Source_URL=b[7], Local_File=b[8])
            else:
                row.update(Hit_Class="NO_DOC" if not pages else "NOT_FOUND")
            out.append(row)
    with open(DATA / "boardex_nationality_hits.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    print("people:", len(out), Counter(r["Hit_Class"] for r in out))
    print("STRICT by Is_Foreign:", Counter((r["Hit_Class"], r.get("Is_Foreign", "")) for r in out if r["Hit_Class"].startswith("STRICT")))
    for r in out:
        if r["Hit_Class"] == "STRICT_CONFLICT" or (r["Hit_Class"] == "STRICT" and r.get("Is_Foreign") != "0"):
            print(f"  REVIEW {r['Symbol']} | {r['Manager_Name']} | {r['Label']} | {r['Labels_Seen']} | {r['File'][:14]} p{r['Page']} | {r['Snippet'][:160]}")


def accept():
    hits = list(csv.DictReader(open(DATA / "boardex_nationality_hits.csv", encoding="utf-8")))
    path = DATA / "manual" / "boardex_nationality_fill.csv"
    cols = ["Symbol", "BoardEx_Director_ID", "Manager_Name", "Name_In_Text", "Nationality", "Nationality_Raw", "Is_Foreign", "Dual_Nationality",
            "Source", "Source_URL", "Local_File", "Page", "Evidence_Quote", "Method", "Reviewed_On"]
    old = list(csv.DictReader(open(path, encoding="utf-8"))) if path.exists() else []
    have = {(r["Symbol"], r["BoardEx_Director_ID"]) for r in old}
    new = []
    for h in hits:
        if h["Hit_Class"] == "STRICT" and h["Is_Foreign"] == "0" and (h["Symbol"], h["BoardEx_Director_ID"]) not in have:
            new.append({"Symbol": h["Symbol"], "BoardEx_Director_ID": h["BoardEx_Director_ID"], "Manager_Name": h["Manager_Name"],
                        "Name_In_Text": h["Name_In_Text"], "Nationality": "Philippines", "Nationality_Raw": h["Label"], "Is_Foreign": "0",
                        "Dual_Nationality": "", "Source": h["Source"], "Source_URL": h["Source_URL"], "Local_File": h["Local_File"],
                        "Page": h["Page"], "Evidence_Quote": h["Snippet"], "Method": f"AUTO_STRICT_{h['Pattern']} (ph11)",
                        "Reviewed_On": date.today().isoformat()})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(old + new)
    print("accepted (Filipino, strict):", len(new), "| total rows", len(old) + len(new))


PARTICLES = {"de", "del", "dela", "delos", "de la", "de los", "san", "sta", "sto", "la", "van", "von", "di", "da", "dos", "das"}


def ascii_fold(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def name_parts(name, keep_hyphen=False):
    s = re.sub(r"[^A-Za-z' -]", " ", ascii_fold(name)).lower()
    toks = [t for t in (s if keep_hyphen else s.replace("-", " ")).split()
            if t not in {"jr", "sr", "ii", "iii", "iv", "dr", "atty", "mr", "ms", "mrs", "engr"}]
    if len(toks) < 2:
        return None, None
    last = toks[-1]
    if len(toks) >= 3 and toks[-2] in PARTICLES:
        last = toks[-2] + " " + toks[-1]
        if len(toks) >= 4 and toks[-3] in ("de",):
            last = toks[-3] + " " + last
    return toks[0], last


def infer():
    """Owner rule (2026-11-06): a person whose name is Filipino may be given Philippine nationality. Applied only to people
    still undisclosed after the filing scan. Name test (data-driven, conservative): the surname occurs among people stated
    Filipino (BoardEx-disclosed or filing-stated) and among NO person stated foreign; the first name does not occur only
    among foreigners. Recorded as Evidence_Type INFERRED, Note INFERRED_WEAK (name only)."""
    fil_s, for_s, fil_f, for_f = Counter(), Counter(), Counter(), Counter()
    for r in csv.DictReader(open(DATA / "boardex_roles.csv", encoding="utf-8-sig")):
        if r["Is_Foreign"] in ("0", "1"):
            f, l = name_parts(r["Manager_Name"])
            if l:
                (fil_s if r["Is_Foreign"] == "0" else for_s)[l] += 1
                (fil_f if r["Is_Foreign"] == "0" else for_f)[f] += 1
    fills_path = DATA / "manual" / "boardex_nationality_fill.csv"
    fills = list(csv.DictReader(open(fills_path, encoding="utf-8")))
    for r in fills:
        if r["Nationality_Raw"] == "INFERRED":
            continue  # reference sets use stated nationalities only (no circular inference)
        f, l = name_parts(r["Manager_Name"])
        if l:
            (fil_s if r["Is_Foreign"] == "0" else for_s)[l] += 1
            (fil_f if r["Is_Foreign"] == "0" else for_f)[f] += 1
    for r in csv.DictReader(open(DATA / "manual" / "manager_records.csv", encoding="utf-8")):
        f, l = name_parts(r["Manager_Name"])
        if l and r["Is_Foreign"] == "1":
            for_s[l] += 1
            for_f[f] += 1
    have = {(r["Symbol"], r["BoardEx_Director_ID"]) for r in fills}
    hits = list(csv.DictReader(open(DATA / "boardex_nationality_hits.csv", encoding="utf-8")))
    new, skipped = [], Counter()
    for h in hits:
        if (h["Symbol"], h["BoardEx_Director_ID"]) in have or h["Hit_Class"].startswith("STRICT"):
            continue
        f, l = name_parts(h["Manager_Name"])
        if not l:
            skipped["name_unparsed"] += 1
            continue
        _, lh = name_parts(h["Manager_Name"], keep_hyphen=True)
        parts = lh.split("-") if lh and "-" in lh else []
        first_fil_only = for_f[f] == 0 and fil_f[f] >= 2
        if for_f[f] and not fil_f[f]:
            skipped["first_name_foreign_only"] += 1
            continue
        if fil_s[l] and not for_s[l]:
            tier = "A: surname Filipino-only"
        elif not fil_s[l] and not for_s[l] and first_fil_only:
            tier = "B: surname unseen, first name Filipino-only"
        elif for_s[l] and fil_s[l] >= 3 * for_s[l] and first_fil_only:
            tier = "C: surname mostly Filipino, first name Filipino-only"
        elif parts and any(fil_s[p] and not for_s[p] for p in parts) and not any(for_s[p] for p in parts):
            tier = "D: compound surname with a Filipino-only part"
        else:
            skipped["not_decisive"] += 1
            continue
        new.append({"Symbol": h["Symbol"], "BoardEx_Director_ID": h["BoardEx_Director_ID"], "Manager_Name": h["Manager_Name"],
                    "Name_In_Text": "", "Nationality": "Philippines", "Nationality_Raw": "INFERRED", "Is_Foreign": "0",
                    "Dual_Nationality": "", "Source": "Name-based inference (research-owner rule, 2026-11-06)", "Source_URL": "",
                    "Local_File": "", "Page": "",
                    "Evidence_Quote": (f"Tier {tier}. Surname '{l}': {fil_s[l]} people stated Filipino, {for_s[l]} stated foreign; "
                                       f"first name '{f}': {fil_f[f]} Filipino, {for_f[f]} foreign (BoardEx-disclosed or filing-stated "
                                       f"nationalities). Filing scan result: {h['Hit_Class']}."),
                    "Method": f"INFERRED_WEAK tier {tier[0]}: Filipino name (owner rule 2026-11-06: 'neu ten philippin thi de quoc tich philippin')",
                    "Reviewed_On": date.today().isoformat()})
    with open(fills_path, "w", newline="", encoding="utf-8") as fo_:
        w = csv.DictWriter(fo_, fieldnames=list(fills[0].keys()))
        w.writeheader()
        w.writerows(fills + new)
    print("inferred Filipino by name:", len(new), "| not inferred:", dict(skipped), "| total fill rows:", len(fills) + len(new))


if __name__ == "__main__":
    {"scan": scan, "accept": accept, "infer": infer}[sys.argv[1]]()
