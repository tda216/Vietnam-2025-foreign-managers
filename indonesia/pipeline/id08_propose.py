"""Indonesia step 8 – record PROPOSALS from the nationality screen, for LOCAL firms only (owner 8 Nov 2026).

For every foreign hit (data/screen_nationality.csv) in a company with FO_Class LOCAL (data/fo_classification.csv)
that has no record yet (data/manual/manager_records.csv): the page text (original case) around the label gives a
candidate name (nearest Title-Case / CAPS run of 2-6 words before or after the label), a candidate position
(nearest role term), appointment / end-of-term phrases with a year, and a context tag:
  PROFILE   – label next to age / domicile / education words (a person's profile)
  STATEMENT – board-composition sentence ("terdiri dari ... warga negara ...", "consists of ... citizens")
  OTHER     – anything else (employee statistics, rules, news) – usually not a manager
A proposal is NOT a record: the reviewer opens the page image (id_review_page.py image) and writes the record.
Output  data/proposals.csv  (one row per label occurrence)
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id08_propose.py
"""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
ROLE = re.compile(r"(Presiden Komisaris|Komisaris Utama|Wakil Komisaris Utama|Komisaris Independen|Komisaris|"
                  r"Presiden Direktur|Direktur Utama|Wakil Presiden Direktur|Wakil Direktur Utama|Direktur Independen|"
                  r"Direktur [A-Z][a-z]+(?: [A-Z][a-z]+)?|Direktur|President Commissioner|Vice President Commissioner|"
                  r"Independent Commissioner|Commissioner|President Director|Vice President Director|Independent Director|"
                  r"Director|Chief [A-Z][a-z]+(?: [A-Z][a-z]+)? Officer|Head of [A-Z][A-Za-z&, ]{2,40}|"
                  r"Anggota Komite [A-Z][a-z]+|Ketua Komite [A-Z][a-z]+|(?:Audit|Risk|Nomination|Remuneration)[A-Za-z ]{0,30}Committee|"
                  r"Sekretaris Perusahaan|Corporate Secretary|Dewan Pengawas Syariah|Sharia Supervisory Board)")
STOP = set("""Komisaris Direktur Utama Independen Presiden Wakil Dewan Direksi Board Commissioner Commissioners Director Directors
President Vice Profil Profile Laporan Tahunan Annual Report Integrated Tbk PT Persero Company Perseroan Perusahaan Warga Negara
Kewarganegaraan Citizenship Nationality Usia Age Domisili Domicile Riwayat Pendidikan Education Educational Background Pengalaman
Kerja Work Experience Jabatan Dasar Hukum Pengangkatan Legal Basis Appointment Rangkap Concurrent Position Positions Hubungan
Afiliasi Affiliation Affiliated Kepemilikan Saham Shareholding Tahun Years Old Bapak Ibu Mr Mrs Ms Beliau He She The And Dan
Head Chief Officer Committee Komite Anggota Ketua Member Chairman Sekretaris Corporate Secretary Sustainability Keberlanjutan
Indonesia Indonesian Jakarta Tata Kelola Governance Of Di Dari Sebagai Since Sejak""".split())
NAME = re.compile(r"\b([A-Z][A-Za-z'\-\.]+(?: (?:[A-Z][A-Za-z'\-\.]+|bin|binti|van|de|der|von|da|dos|Mc|Mac)){1,5})\b")
PROFILE = re.compile(r"(?i)\b(usia|age|tahun|years old|domisili|domicile|lahir|born|pendidikan|education|riwayat)\b")
STATEMENT = re.compile(r"(?i)(terdiri (?:dari|atas)|consists? of|komposisi|composition|seluruh anggota|all members|"
                       r"satu anggota|one member|warga negara asing sebanyak)")
APPT = re.compile(r"(?i)(diangkat|ditunjuk|menjabat (?:sebagai [^.]{0,60})?sejak|appointed|serv(?:es|ing|ed) as [^.]{0,60} since|"
                  r"sejak|since|rups(?:t|lb)?|agms|egms|gms)[^.]{0,80}?(20\d\d)")
LEAVE = re.compile(r"(?i)(mengundurkan diri|pengunduran diri|berakhir|tidak lagi menjabat|diberhentikan|resign\w*|"
                   r"end of (?:the )?(?:tenure|term)|ceased|no longer)[^.]{0,100}?(20\d\d)")


def rows(name):
    p = D / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def names_near(t, i, j):
    """Candidate person names in t[i:j] (Title-Case or CAPS runs, stop words removed), nearest to the label first."""
    out = []
    for m in NAME.finditer(t, i, j):
        words = [w for w in m.group(1).split() if w.strip(".").title() not in STOP and w.strip(".") not in STOP]
        if len(words) >= 2 and not any(ch.isdigit() for ch in m.group(1)):
            out.append(" ".join(words))
    return out


def main():
    fc = {r["Code"]: r for r in rows("fo_classification.csv")}
    known = {}  # code -> name tokens already recorded or decided (records, candidate decisions)
    for r in rows("manual/manager_records.csv"):
        known.setdefault(r["Code"], set()).update(w.lower() for w in re.findall(r"[A-Za-z]{4,}", r["Manager_Name"]))
    for r in rows("manual/candidate_decisions.csv"):
        known.setdefault(r["Code"], set()).update(w.lower() for w in re.findall(r"[A-Za-z]{4,}", r["Name"].split("(")[0]))
    from collections import Counter
    rec_pages = Counter((r["Code"], str(r["Page"]), r["Nationality"]) for r in rows("manual/manager_records.csv"))
    hits_all = rows("screen_nationality.csv")
    ages = {}  # (code, page, country) -> distinct ages next to the labels (two people of one nationality on a page)
    for h in hits_all:
        for a_ in re.findall(r"(\d{2})\s*(?:tahun|years?)", h["Snippet"]):
            ages.setdefault((h["Code"], h["Page"], h["Country"]), set()).add(a_)
    texts = {}
    seen, out = set(), []
    for h in hits_all:
        c = h["Code"]
        g = (c, h["Page"], h["Country"])
        if h["Country"] != "UNKNOWN" and rec_pages[g] >= max(1, len(ages.get(g, ()))):
            continue  # every person with this nationality on this page (any language version) is recorded
        if fc.get(c, {}).get("FO_Class") != "LOCAL":
            continue
        key = (c, h["File"], h["Page"], h["Country"], h["Snippet"][-120:])  # per label occurrence, not per page
        if key in seen:
            continue
        seen.add(key)
        if h["File"] not in texts:
            sha = [r for r in rows("text_index.csv") if r["File"] == h["File"]][0]["SHA256"][:12]
            texts[h["File"]] = json.loads((D / "text" / c / f"{sha}.json").read_text(encoding="utf-8"))["pages"]
        t = re.sub(r"\s+", " ", texts[h["File"]][int(h["Page"]) - 1]["text"])
        ms = [m.start() for m in re.finditer(re.escape(h["Raw"]).replace(r"\ ", r"\s*"), t, re.I)]
        k = sum(1 for x in out if (x["Code"], x["File"], x["Page"], x["Label"]) == (c, h["File"], h["Page"], h["Raw"]))
        i = ms[min(k, len(ms) - 1)] if ms else 0  # n-th occurrence of the same label on the page
        win = t[max(0, i - 500): i + 300]
        near = set(w.lower() for w in re.findall(r"[A-Za-z]{4,}", t[max(0, i - 350): i + 250]))
        if known.get(c) and len(known[c] & near) >= 1 and h["Country"] != "UNKNOWN":
            continue  # a recorded / decided person sits next to this label
        before = names_near(t, max(0, i - 500), i)
        after = names_near(t, i, i + 300)
        roles = [r.group(1) for r in ROLE.finditer(t, max(0, i - 600), i + 200)]
        ctx = ("STATEMENT" if STATEMENT.search(t[max(0, i - 250): i + 100]) else
               "PROFILE" if PROFILE.search(t[max(0, i - 200): i + 200]) else "OTHER")
        if h["Country"] == "UNKNOWN" and ctx != "STATEMENT":
            ctx = "OTHER"  # "WNA" in employee tables / rules
        out.append({"Code": c, "Company": fc[c]["Company"], "File": h["File"], "Page": h["Page"], "Src": h["Src"],
                    "Country": h["Country"], "Context": ctx, "Label": h["Raw"],
                    "Name_Candidates": " | ".join((before[-2:][::-1] + after[:2])[:4]),
                    "Role_Candidates": " | ".join(dict.fromkeys(roles[-4:])),
                    "Appointed_Hint": " | ".join(f"{a.group(1)[:20]}…{a.group(2)}" for a in APPT.finditer(t, max(0, i - 800), i + 800))[:120],
                    "Left_Hint": " | ".join(f"{a.group(1)[:20]}…{a.group(2)}" for a in LEAVE.finditer(t, max(0, i - 800), i + 800))[:120],
                    "Snippet": win})
    out.sort(key=lambda r: (r["Context"] == "OTHER", r["Code"], r["File"], int(r["Page"])))
    keys = ["Code", "Company", "File", "Page", "Src", "Country", "Context", "Label", "Name_Candidates", "Role_Candidates",
            "Appointed_Hint", "Left_Hint", "Snippet"]
    with (D / "proposals.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(out)
    from collections import Counter
    print("proposals", len(out), Counter(r["Context"] for r in out), "companies", len({r["Code"] for r in out}))


if __name__ == "__main__":
    main()
