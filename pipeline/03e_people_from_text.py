"""Step 3e/5 – person mentions in the 2025 annual/governance reports, linked to nearby nationality labels.

Usage: python -I pipeline/03e_people_from_text.py pilot|full

A mention is an honorific + capitalised name ("Ông Takeo Shimotsu", "Bà Nguyễn Thị A", "Mr. Loic Faussier"), or
(Found_By = NO_HONORIFIC, added 2026-11-01 after QA) a name in a table without honorific: 2-4 capitalised unaccented
words within BARE_POS_WINDOW characters of a position word, with >= 2 words that are not Vietnamese syllables, look like
name words, are not organisation words and occur in at most BARE_RARE_DF companies' reports (drops English words, brands).
For every nationality label (03c FIELD hit) the closest preceding mention on the same page (within
LINK_WINDOW characters) is taken as the person it describes; Nationality_Raw is the text after the label.
This is a reading aid: each FOREIGN/UNLINKED row is checked by a person on the PDF page before it becomes a record.

Outputs (data/<run>/): people_mentions.csv (one row per company × name), nationality_links.csv (one row per label)
"""
import json
import re
import unicodedata
import sys
from collections import defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import read_csv, strip_accents, write_csv
from config import DATA

_rost = import_module("03d_roster_cafef")
_screen = _rost.name_screen
_scan = import_module("03c_extract_text")

LINK_WINDOW = 700
UPPER = "A-ZĐÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
WORD = rf"[{UPPER}][\w'’\-]*"
# unaccented honorifics: ARs in legacy fonts (e.g. ACE, HPX: "Ong Nguyen Van A", OCR "6ng"); added 2026-11-01 after QA
NAME_RE = re.compile(rf"\b(Ông|Bà|ÔNG|BÀ|Ong|ONG|6ng|Ba|BA|Mr\.?|Mrs\.?|Ms\.?|Mdm\.?|Dr\.?)[ \t]+({WORD}(?:,?[ \t]+{WORD}){{1,5}})")
POSITION_WORDS = re.compile(r"chu tich|thanh vien|tong giam doc|giam doc|ke toan truong|kiem soat|truong ban|uy ban kiem toan"
                            r"|chairman|director|member|ceo|cfo|officer|supervisor|audit committee")
MENTION_FIELDS = ["Ticker_Local", "Name", "Name_Key", "Name_Screen", "Found_By", "N_Mentions", "Docs", "First_Page_AR",
                  "Pages_AR", "Pages_GOV", "In_CafeF_Roster"]
BARE_RE = re.compile(r"\b([A-Z][a-zA-Z'\-]{1,15}(?:,?[ ]+[A-Z][a-zA-Z'\-]{1,15}){1,3})\b")
BARE_POS = re.compile(r"chu tich|thanh vien|uy vien|tong giam doc|giam doc|ke toan truong|kiem soat|truong ban|chairman|director"
                      r"|member of|ceo|cfo|supervisor|hdqt|bks")
BARE_POS_WINDOW = 60
BARE_RARE_DF = 15
BARE_WORD = re.compile(r"^(?:[A-Z][a-z]{1,14}|[A-Z]{4,14})(?:-[A-Z]?[a-z]{1,14})?$")
NOT_A_NAME = set("""ctcp cty tnhh mtv jsc co ltd limited corporation corp group company companies bank fund funds holding holdings
international joint stock securities insurance investment development vietnam viet global asia asian pacific industrial industry
park resort resorts hotel residences residence tower towers center centre program programme graduate university school institute
college diploma certificate ministry committee council board award awards plaza city garden green golden royal grand the of and for
in on with at by trust capital partners partner management services service solutions systems technology technologies energy power
water food foods beverage beverages trading logistics port terminal shipping marine airlines airport real estate properties property
land homes home house village villas bay beach island hills river lake mountain street road district province ward commune office
branch factory plant project projects deloitte kpmg ernst young pwc pricewaterhousecoopers baker tilly grant thornton mazars rsm
moore crowe audit accounting finance marketing sales human resources legal risk compliance strategy operations digital data
analytics retail wholesale consumer products product chemicals cement steel rubber coffee rice seafood textile garment pharma
pharmaceutical medical hospital clinic health care sciences science research foundation association federation union chamber
commerce system suite ventures venture equity assets asset wealth curriculum vitae brief biographies""".split())
LINK_FIELDS = ["Ticker_Local", "Doc_Kind", "Local_File", "Page", "Label", "Nationality_Raw", "Value_Class",
               "Linked_Name", "Linked_Name_Screen", "Chars_Between", "Snippet"]


def name_key(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", "", strip_accents(name).replace("-", " "))).strip()


ROLE_CUT = re.compile(r"\s+(?:Chủ|CHỦ|Thành|THÀNH|Tổng|TỔNG|Phó|PHÓ|Giám|GIÁM|Kế|KẾ|Trưởng|TRƯỞNG|Ủy|Uỷ|Năm|Sinh|Quốc|Chức"
                      r"|Trình|Hiện|Đại|Kiểm|Chairman|Chairwoman|Chairperson|Vice|Member|Director|Deputy|Chief|Head|Born|Independent|Non"
                      r"|Board|Supervisory|General|Former|Administration|Management|University|Executive|Accountant|Manager|Audit|Committee|None"
                      r"|TV|HĐQT|HDQT|TGĐ|TGD|GĐ|BKS|BĐH|BTGĐ|UBKT|KTT|CEO|CFO|COO|CTO|BOD|BOM)\b")


# words that make a capitalised run an address or an organisation, not a person ("Ba Ria Ward", "Hai Ba Trung District")
NOT_PERSON_WORDS = re.compile(r"\b(?:Ward|District|Dist|Street|Str|Road|City|Province|Commune|Town|Village|Hanoi|HCMC|Project|Proj"
                              r"|Plant|Park|Hydropower|JSC|Company|Corporation|Group|Bank|Branch)\b", re.I)
PLACE_AFTER_BA = {"Rịa", "RỊA", "Trưng", "TRƯNG", "Triệu", "TRIỆU", "Chiểu", "Điểm", "Đen", "Hom", "Quẹo", "Lãnh", "Huyện"}


def clean_name(raw: str) -> str:
    name = re.sub(r"\s+", " ", ROLE_CUT.split(raw)[0]).strip(" ,")
    name = re.sub(r"^(?:(?:Ông|Bà|ÔNG|BÀ)\s+)+", "", name)  # doubled honorific from the text layer
    tokens = name.split()
    half = len(tokens) // 2
    if len(tokens) % 2 == 0 and half >= 2 and tokens[:half] == tokens[half:]:  # "HỒ MINH HOÀNG HỒ MINH HOÀNG"
        name = " ".join(tokens[:half])
    # place names that start with "Bà" (Bà Rịa, Hai Bà Trưng, Bà Triệu, Bà Chiểu, ...) and address fragments
    if tokens and (tokens[0].strip(",") in PLACE_AFTER_BA or any(t.strip(",.") in {"TP", "Tp", "P", "Q", "Tỉnh", "Quận"} for t in tokens)):
        return ""
    if re.search(r"\d", name) or NOT_PERSON_WORDS.search(name):  # OCR / legacy-font digits ("Nguy6n"), addresses, organisations
        return ""
    return name


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    out_dir = DATA / run
    stats = [s for s in read_csv(out_dir / "pdf_stats.csv") if not s["Error"]]
    if (out_dir / "pdf_stats_fallback.csv").exists():  # 06a: RAR / website ARs, 2025 governance reports; AR2024 when nothing else (user 2026-11-01)
        stats += [s for s in read_csv(out_dir / "pdf_stats_fallback.csv") if not s["Error"] and s["Doc_Kind"] in ("AR2025", "GOV2025", "AR2024")]
    cafef = defaultdict(set)
    if (out_dir / "roster_cafef.csv").exists():
        for r in read_csv(out_dir / "roster_cafef.csv"):
            cafef[r["Ticker_Local"]].add(name_key(re.sub(r"^(Ông|Bà)\s+", "", r["Name_Raw"])))
    people = {}
    links = []
    bare, bare_df = [], defaultdict(set)  # (ticker, kind, page, name) without honorific; companies per word
    for s in stats:
        t, kind = s["Ticker_Local"], s["Doc_Kind"]
        path = out_dir / "text" / t / (Path(s["Local_File"]).name + ".jsonl")
        for line in path.open(encoding="utf-8"):
            pg = json.loads(line)
            text, page = unicodedata.normalize("NFC", pg["text"]), pg["page"]  # some text layers are decomposed (NFD)
            mentions = []
            for m in NAME_RE.finditer(text):
                name = clean_name(m.group(2))
                if len(name.split()) < 2:
                    continue
                mentions.append((m.start(), name))
                key = (t, name_key(name))
                p = people.setdefault(key, {"Ticker_Local": t, "Name": name, "Name_Key": key[1], "Name_Screen": _screen(name),
                                             "Found_By": "HONORIFIC", "N_Mentions": 0, "Docs": set(), "Pages_AR": set(),
                                             "Pages_GOV": set()})
                p["N_Mentions"] += 1
                p["Docs"].add(kind)
                (p["Pages_AR"] if kind == "AR2025" else p["Pages_GOV"]).add(page)
            folded = _scan.fold(text)
            for m in BARE_RE.finditer(text):
                words = [w for w in re.split(r"[ ,]+", m.group(1)) if w]
                for w in words:
                    bare_df[w.lower()].add(t)
                if (all(BARE_WORD.match(w) for w in words) and not any(w.lower() in NOT_A_NAME for w in words)
                        and clean_name(" ".join(words))
                        and BARE_POS.search(folded[max(0, m.start() - BARE_POS_WINDOW):m.end() + BARE_POS_WINDOW])
                        and not any(m.start() >= pos and m.start() <= pos + len(n) + 12 for pos, n in mentions)):
                    bare.append((t, kind, page, " ".join(words)))
            for f in _scan.FIELD_RE.finditer(folded):
                value = _scan.field_value(text, f.end())
                before = [(pos, n) for pos, n in mentions if pos < f.start() and f.start() - pos <= LINK_WINDOW]
                pos, name = before[-1] if before else (None, "")
                links.append({"Ticker_Local": t, "Doc_Kind": kind, "Local_File": s["Local_File"], "Page": page,
                              "Label": text[f.start():f.end()], "Nationality_Raw": value,
                              "Value_Class": _scan.value_class(value), "Linked_Name": name,
                              "Linked_Name_Screen": _screen(name) if name else "",
                              "Chars_Between": f.start() - pos if pos is not None else "",
                              "Snippet": _scan.snippet(text, f.start(), f.end(), 200)})
    is_vn = lambda w: bool(_rost.SYLLABLE_RE.match(strip_accents(w)) or _rost.SYLLABLE_RE.match(strip_accents(w).replace("uu", "uy")))
    for t, kind, page, name in bare:
        if sum(1 for w in name.split() if not is_vn(w) and len(bare_df[w.lower()]) <= BARE_RARE_DF) < 2:
            continue
        key = (t, name_key(name))
        if key in people:
            continue
        p = people.setdefault(key, {"Ticker_Local": t, "Name": name, "Name_Key": key[1], "Name_Screen": _screen(name),
                                     "Found_By": "NO_HONORIFIC", "N_Mentions": 0, "Docs": set(), "Pages_AR": set(), "Pages_GOV": set()})
        p["N_Mentions"] += 1
        p["Docs"].add(kind)
        (p["Pages_AR"] if kind == "AR2025" else p["Pages_GOV"]).add(page)
    rows = []
    for (t, k), p in sorted(people.items()):
        rows.append({**p, "Docs": ";".join(sorted(p["Docs"])),
                     "First_Page_AR": min(p["Pages_AR"]) if p["Pages_AR"] else "",
                     "Pages_AR": ";".join(map(str, sorted(p["Pages_AR"])[:30])),
                     "Pages_GOV": ";".join(map(str, sorted(p["Pages_GOV"])[:30])),
                     "In_CafeF_Roster": int(k in cafef[t]) if t in cafef else ""})
    write_csv(out_dir / "people_mentions.csv", rows, MENTION_FIELDS)
    write_csv(out_dir / "nationality_links.csv", links, LINK_FIELDS)
    print("mentions:", len(rows), "| NO_HONORIFIC:", sum(r["Found_By"] == "NO_HONORIFIC" for r in rows),
          "| NON_VN_STYLE:", sum(r["Name_Screen"] == "NON_VN_STYLE" for r in rows),
          "| labels:", len(links), "| FOREIGN values:", sum(l["Value_Class"] == "FOREIGN" for l in links))


if __name__ == "__main__":
    main()
