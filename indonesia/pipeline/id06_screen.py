"""Indonesia step 6 – screens on the AR page text (data/text/): (a) nationality labels, (b) shareholder composition.

SCREENING ONLY: a hit says which page to read. Nothing is recorded before the page (image, for OCR or multi-column
pages) has been read and quoted.

(a) Nationality labels, Indonesian and English, as OJK requires them in every Commissioner/Director profile:
    "warga negara <country>", "kewarganegaraan: <country>", "<demonym> citizen/national(ity)", "citizen of <country>",
    "nationality/citizenship: <country>", "WNA"/"warga negara asing" (foreign, country not stated).
    -> data/screen_nationality.csv (one row per hit) and data/screen_docs.csv (per document: Indonesian labels, foreign
       labels, countries, pages) – a document without any label needs reading by hand (profile without nationality).
(b) Shareholder composition (OJK: local/foreign x institution/individual): pages scored by keywords; on the best pages
    every row label (foreign/local institution/individual, total foreign/local) with the first percentage after it.
    Foreign_Sum + Local_Sum ~ 100 -> SUM_OK. Two dates on one page (2024 and 2025 columns) -> TWO_DATES (check which
    column is 31 Dec 2025). -> data/screen_composition.csv
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id06_screen.py [codes.csv]
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"

# country names: Indonesian, English, demonyms (lower case) -> English country
NAT = {}
for country, names in {
    "Indonesia": "indonesia|indonesian|republik indonesia|wni",
    "United States": "amerika serikat|amerika|united states of america|united states|usa|u.s.a.|american",
    "United Kingdom": "inggris|britania raya|kerajaan inggris|united kingdom|great britain|british|english|scottish|wales|welsh|irlandia utara|northern ireland",
    "Japan": "jepang|japan|japanese", "South Korea": "korea selatan|republik korea|korea|south korea|korean|south korean",
    "China": "tiongkok|republik rakyat tiongkok|rrt|cina|china|chinese|people's republic of china",
    "Taiwan": "taiwan|taiwanese", "Hong Kong": "hong kong|hongkong", "Macau": "makau|macau|macao",
    "Singapore": "singapura|singapore|singaporean", "Malaysia": "malaysia|malaysian", "Thailand": "thailand|thai",
    "Philippines": "filipina|philippines|filipino|filipina", "Vietnam": "vietnam|viet nam|vietnamese",
    "India": "india|indian", "Pakistan": "pakistan|pakistani", "Bangladesh": "bangladesh|bangladeshi",
    "Sri Lanka": "sri lanka|sri lankan", "Nepal": "nepal|nepali|nepalese", "Myanmar": "myanmar|burmese",
    "Cambodia": "kamboja|cambodia|cambodian", "Brunei": "brunei|brunei darussalam|bruneian",
    "Australia": "australia|australian", "New Zealand": "selandia baru|new zealand|new zealander",
    "Canada": "kanada|canada|canadian", "Germany": "jerman|germany|german", "France": "perancis|prancis|france|french",
    "Netherlands": "belanda|netherlands|the netherlands|dutch", "Belgium": "belgia|belgium|belgian",
    "Switzerland": "swiss|switzerland", "Austria": "austria|austrian", "Italy": "italia|italy|italian",
    "Spain": "spanyol|spain|spanish", "Portugal": "portugal|portuguese", "Ireland": "irlandia|ireland|irish",
    "Denmark": "denmark|danish", "Sweden": "swedia|sweden|swedish", "Norway": "norwegia|norway|norwegian",
    "Finland": "finlandia|finland|finnish", "Poland": "polandia|poland|polish", "Greece": "yunani|greece|greek",
    "Russia": "rusia|russia|russian", "Turkey": "turki|turkey|turkish|türkiye", "Israel": "israel|israeli",
    "Saudi Arabia": "arab saudi|saudi arabia|saudi", "United Arab Emirates": "uni emirat arab|united arab emirates|emirati|uae",
    "Qatar": "qatar|qatari", "Kuwait": "kuwait|kuwaiti", "Egypt": "mesir|egypt|egyptian", "Jordan": "yordania|jordan|jordanian",
    "South Africa": "afrika selatan|south africa|south african", "Brazil": "brasil|brazil|brazilian",
    "Mexico": "meksiko|mexico|mexican", "Luxembourg": "luksemburg|luxembourg",
    # added 8 Nov 2026 after HMSP's Lithuanian commissioner was missed: the rest of the world
    "Lithuania": "lituania|lithuania|lithuanian", "Latvia": "latvia|latvian", "Estonia": "estonia|estonian",
    "Ukraine": "ukraina|ukraine|ukrainian", "Belarus": "belarus|belarusian", "Czech Republic": "ceko|republik ceko|czech republic|czechia|czech",
    "Slovakia": "slowakia|slovakia|slovak", "Hungary": "hungaria|hungary|hungarian", "Romania": "rumania|romania|romanian",
    "Bulgaria": "bulgaria|bulgarian", "Serbia": "serbia|serbian", "Croatia": "kroasia|croatia|croatian", "Slovenia": "slovenia|slovenian",
    "Iceland": "islandia|iceland|icelandic", "Cyprus": "siprus|cyprus|cypriot", "Malta": "malta|maltese", "Monaco": "monako|monaco|monegasque",
    "Kazakhstan": "kazakhstan|kazakh", "Uzbekistan": "uzbekistan|uzbek", "Iran": "iran|iranian", "Iraq": "irak|iraq|iraqi",
    "Lebanon": "lebanon|libanon|lebanese", "Syria": "suriah|syria|syrian", "Oman": "oman|omani", "Bahrain": "bahrain|bahraini",
    "Yemen": "yaman|yemen|yemeni", "Afghanistan": "afganistan|afghanistan|afghan", "Mongolia": "mongolia|mongolian",
    "North Korea": "korea utara|north korea", "Laos": "laos|lao|laotian", "Timor-Leste": "timor leste|timor-leste|east timor|timorese",
    "Papua New Guinea": "papua nugini|papua new guinea", "Fiji": "fiji|fijian", "Maldives": "maladewa|maldives|maldivian",
    "Nigeria": "nigeria|nigerian", "Kenya": "kenya|kenyan", "Ghana": "ghana|ghanaian", "Ethiopia": "etiopia|ethiopia|ethiopian",
    "Morocco": "maroko|morocco|moroccan", "Algeria": "aljazair|algeria|algerian", "Tunisia": "tunisia|tunisian", "Libya": "libya|libyan",
    "Sudan": "sudan|sudanese", "Tanzania": "tanzania|tanzanian", "Uganda": "uganda|ugandan", "Zimbabwe": "zimbabwe|zimbabwean",
    "Zambia": "zambia|zambian", "Mauritius": "mauritius|mauritian", "Madagascar": "madagaskar|madagascar",
    "Argentina": "argentina|argentine|argentinian", "Chile": "chili|chile|chilean", "Colombia": "kolombia|colombia|colombian",
    "Peru": "peru|peruvian", "Venezuela": "venezuela|venezuelan", "Uruguay": "uruguay|uruguayan", "Paraguay": "paraguay|paraguayan",
    "Ecuador": "ekuador|ecuador|ecuadorian", "Bolivia": "bolivia|bolivian", "Cuba": "kuba|cuba|cuban", "Jamaica": "jamaika|jamaica|jamaican",
    "Panama": "panama|panamanian", "Costa Rica": "kosta rika|costa rica|costa rican", "Guatemala": "guatemala|guatemalan",
    "Trinidad and Tobago": "trinidad dan tobago|trinidad and tobago|trinidadian", "Bermuda": "bermuda|bermudian",
    "Cayman Islands": "kepulauan cayman|cayman islands", "British Virgin Islands": "kepulauan virgin britania raya|british virgin islands",
}.items():
    for n in names.split("|"):
        NAT[n] = country
ALT = "|".join(re.escape(k) for k in sorted(NAT, key=len, reverse=True))
B = r"(?<![a-z])"  # left word boundary that also works after punctuation
E = r"(?![a-z])"
SEP = r"\s*[:|/\-–]?\s*"
# "kebangsaan" not inside "Universiti Kebangsaan Malaysia" (a university, not a nationality label)
LAB_ID, LAB_EN = r"(?:(?:ber)?kewarganegaraan|(?<!universiti )(?<!universitas )(?<!university )kebangsaan|warga\s*negara)", r"(?:nationality|citizenship|citizen)"  # "Kewarganegaraan / Citizen Indonesia" (MDLN)
# tables with the labels in one column and the values in the next ("Kewarganegaraan Citizenship Usia Age Malaysia", NCKL)
GAP = r"(?:usia|age|umur|domisili|domicile|tempat|lahir|place|birth|and|dan|&)"
# bilingual labels put the English word between label and country: "Kewarganegaraan Citizenship Indonesia",
# "Warga Negara Nationality Indonesia", "Nationality | Warga Negara Australian"
NAT_RES = [
    ("WARGA_NEGARA", re.compile(B + LAB_ID + SEP + "(?:(?:" + LAB_EN + "|" + GAP + ")" + SEP + "){0,4}(" + ALT + ")" + E)),
    ("NATIONALITY_LABEL", re.compile(B + LAB_EN + SEP + "(?:(?:" + LAB_ID + "|" + GAP + ")" + SEP + "){0,4}(" + ALT + ")" + E)),
    ("CITIZEN_OF", re.compile(B + r"(?:citizen|national)\s+of\s+(?:the\s+)?(" + ALT + ")" + E)),
    ("FOREIGN_NO_COUNTRY", re.compile(B + r"(warga\s*negara\s+asing|wna|foreign\s+national|foreign\s+citizen)" + E)),
    # tables with labels first and values far after ("Kewarganegaraan Nationality Periode Jabatan ... Indonesia"); a looser
    # match: first country name within 150 characters, same sentence. Noisier – every foreign hit is read anyway.
    # value before label: "Thailand Thai Kewarganegaraan Nationality" (TPIA), "India Kewarganegaraan Nationale" (ESSA)
    ("LABEL_AFTER", re.compile(B + "(" + ALT + r")(?:\s+[a-z]+)?\s*[|/:]?\s*(?:" + LAB_ID + "|" + LAB_EN + r"|nationale)(?![a-z])")),
    ("LABEL_LOOSE", re.compile(B + "(?:" + LAB_ID + "|" + LAB_EN + r")(?![a-z])[^.]{0,150}?(?<![a-z])(" + ALT + ")" + E)),
]

# "national" only as a noun ("a Japanese national,"), not "Australian National University" / "National Australia Bank"
CIT = re.compile(r"\s(?:citizens?|nationality|citizenship|national(?=\s*[,.;:)]|\s+(?:and|who|with|since|born|residing|was|is|has|aged?)(?![a-z])|\s*$))" + E)
TAIL = re.compile(B + "(" + ALT + r")\s*$")


def norm(t):
    t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", t.replace("\u00ad", ""))  # OCR can leave NUL / control chars
    return re.sub(r"\s+", " ", t).lower()


GENERIC_BEFORE = re.compile(r"(?<![a-z])(?:seluruh|setiap|semua|segenap|kepada|bagi|all|every|any)\s+(?:[a-z]+\s+){0,2}\S*$")
GENERIC_AFTER = re.compile(r"\W*(?:yang\s+(?:memiliki|memenuhi|berhak|ingin)|who\s+(?:possess|have|meet|wish))")
LABWORD = re.compile(r"(?<![a-z])(?:kewarganegaraan|warga negara|nationality|citizenship)(?![a-z])")


class _M:
    """Match-like span for table_pairs (group(0) = the pair, group(1) = the first value)."""
    def __init__(self, t, a, b, c):
        self.t, self.a, self.b, self.c = t, a, b, c
    def group(self, k=0):
        return self.t[self.a:self.c] if k == 0 else self.t[self.a:self.b]
    def start(self, k=0):
        return self.a
    def end(self, k=0):
        return self.c if k == 0 else self.b


def table_pairs(t):
    """Two adjacent values naming the same country, e.g. 'indonesia indonesian', 'jepang japanese', 'thailand thai'
    (bilingual profile tables; lesson BAJA / PTMR / BIRD, 10 Nov 2026). Token scan, 1-3 words per value."""
    toks = [(m.group(0), m.start(), m.end()) for m in re.finditer(r"[a-z]+", t)]
    out, n = [], len(toks)
    for i in range(n):
        for l1 in (1, 2, 3):
            if i + l1 > n:
                break
            k1 = " ".join(x[0] for x in toks[i:i + l1])
            if k1 not in NAT:
                continue
            for l2 in (1, 2, 3):
                j = i + l1
                if j + l2 > n:
                    break
                k2 = " ".join(x[0] for x in toks[j:j + l2])
                if k2 != k1 and NAT.get(k2) == NAT[k1] and t[toks[j - 1][2]:toks[j][1]].strip(" |/") == "":
                    out.append(_M(t, toks[i][1], toks[i + l1 - 1][2], toks[j + l2 - 1][2]))
                    break
    return out


def screen_nat(code, doc, pages, hits):
    s = {"Code": code, "File": doc, "Indonesian_Labels": 0, "Foreign_Labels": 0, "Foreign_No_Country": 0,
         "Foreign_Countries": set(), "Foreign_Pages": set()}
    for pg in pages:
        t = norm(pg["text"])
        found, ends = [], set()
        for kind, rx in NAT_RES:
            for m in rx.finditer(t):
                if m.end(1) not in ends:  # "kewarganegaraan citizenship indonesia" is one label, not two
                    ends.add(m.end(1)); found.append((kind, m))
        for m in CIT.finditer(t):  # "<demonym> citizen": look back from the keyword (a leading 200-name alternation is slow)
            b = TAIL.search(t, max(0, m.start() - 40), m.start())
            if b and b.end(1) not in ends:
                ends.add(b.end(1)); found.append(("DEMONYM_CITIZEN", b))
        if LABWORD.search(t):  # profile tables: "Kewarganegaraan Citizenship ... Indonesia Indonesian" (value far from the label)
            for m in table_pairs(t):
                if m.end(1) not in ends:
                    ends.add(m.end(1)); found.append(("TABLE_PAIR", m))
        for kind, m in found:
            raw = m.group(1)
            country = "UNKNOWN" if kind == "FOREIGN_NO_COUNTRY" else NAT[raw if kind != "TABLE_PAIR" else re.sub(r"\s+", " ", raw)]
            if country == "Indonesia":
                # a generic sentence about citizens is not a person's label: 'kesempatan yang sama kepada seluruh warga negara
                # Indonesia yang memiliki kualifikasi' / 'to all Indonesian citizens who possess' (KOCI, QA sample 10 Nov 2026)
                if not (GENERIC_BEFORE.search(t, max(0, m.start() - 45), m.start() + 1) or GENERIC_AFTER.match(t, m.end(), m.end() + 40)):
                    s["Indonesian_Labels"] += 1
                continue
            if kind == "FOREIGN_NO_COUNTRY":
                s["Foreign_No_Country"] += 1
            else:
                s["Foreign_Labels"] += 1; s["Foreign_Countries"].add(country)
            s["Foreign_Pages"].add(pg["p"])
            hits.append({"Code": code, "File": doc, "Page": pg["p"], "Src": pg["src"], "Pattern": kind,
                         "Raw": m.group(0), "Country": country,
                         "Snippet": t[max(0, m.start() - 160): m.end() + 80]})
    s["Foreign_Countries"] = ";".join(sorted(s["Foreign_Countries"]))
    s["Foreign_Pages"] = ";".join(map(str, sorted(s["Foreign_Pages"])))
    s["Note"] = "NO_NATIONALITY_LABEL_READ_PROFILES" if not (s["Indonesian_Labels"] or s["Foreign_Labels"]) else ""
    return s


KEYS = re.compile(r"komposisi pemegang saham|shareholders? composition|shareholding composition|klasifikasi|"
                  r"classification|asing|foreign|lokal|local|domestik|domestic|dalam negeri|perorangan|individu|"
                  r"institusi|institution|badan usaha|lembaga")
SIDE_F = re.compile(r"asing|foreign|luar negeri|overseas")
SIDE_L = re.compile(r"lokal|local|domestik|domestic|dalam negeri|nasional|national|"
                    r"(?:perorangan|lembaga|individu|institusi|badan usaha|investor|pemodal|pemegang saham)\s+indonesia|"
                    r"indonesian\s+(?:individuals?|institutions?|investors?|shareholders?)")
SUB = re.compile(r"^(?:sub[ -]?total|sub[ -]?jumlah|jumlah sub|subjumlah)\b")
GRAND = re.compile(r"^(?:grand )?(?:total|jumlah)(?: keseluruhan| total)?(?:\s*[|/]\s*total)?(?:\s*\(.*\))?$")
PCT = re.compile(r"^(\()?(\d{1,3}(?:[.,]\d{1,2})?|\d{1,3}[.,]\d{1,4}(?=\s*%))\s*%?(?(1)\))$")  # "(5%)" yes, "5%)" no
NUM = re.compile(r"^[\d.,\s()%-]+$")


def page_dec(t):
    """Decimal mark of a page: ',' when thousands are written 1.234.567 (Indonesian), '.' for 1,234,567."""
    dots, commas = len(re.findall(r"\d{1,3}(?:\.\d{3}){2,}", t)), len(re.findall(r"\d{1,3}(?:,\d{3}){2,}", t))
    return "," if dots > commas else "." if commas > dots else None


def pct(line, dec=None):
    s = line.strip()
    if dec and re.fullmatch(r"\(?\d{1,3}" + re.escape(dec) + r"\d{3,6}\s*%?\)?", s):  # 3-6 decimals (ATIC: 9,34719)
        s = s.replace(dec, "#")  # 3-4 decimals (e.g. 78,718) when the page's decimal mark is known
        return (lambda v: v if v <= 100 else None)(float(re.sub(r"[^\d#]", "", s).replace("#", ".")))
    m = PCT.match(s)
    if not m or not (re.search(r"[.,]\d", m.group(0)) or "%" in m.group(0)):
        return None  # a bare integer is a count, not a percentage
    v = float(m.group(2).replace(",", "."))
    return v if v <= 100 else None


def side(ln):
    f, l = bool(SIDE_F.search(ln)), bool(SIDE_L.search(ln))
    return "F" if f and not l else "L" if l and not f else None


def parse_table(lines, dec=None):
    """Walk the page lines: a label followed by a percentage is a row (first percentage = first column); a sided label
    followed by another label is a section header (Foreign / Local); unsided rows add to the open section; Sub Total
    gives the section total. The next percentage in the same row is the second column (e.g. the other year).
    Returns (foreign, local, rows, foreign_col2, local_col2)."""
    sec, acc, sub, rows_, label = None, {"F": [], "L": []}, {}, [], None
    acc2, sub2, pend2 = {"F": [], "L": []}, {}, None
    for ln in lines:
        v = pct(ln, dec)
        if v is not None and label is None and pend2:
            kind2, k2 = pend2; pend2 = None
            if kind2 == "sub":
                sub2[k2] = v
            else:
                acc2[k2].append(v)
            continue
        if v is None:
            if NUM.match(ln) or len(ln) > 70 or not re.search(r"[a-z]", ln):
                continue
            pend2 = None
            if label is not None and label[1] and not SUB.match(label[0]):
                sec = label[1]  # sided label without a value = section header
            if GRAND.match(ln) and (acc["F"] or acc["L"] or sub):
                if (acc["F"] or "F" in sub) and (acc["L"] or "L" in sub):
                    break  # end of the local/foreign table
                sec, acc, sub, rows_ = None, {"F": [], "L": []}, {}, []  # another table: start again
                acc2, sub2 = {"F": [], "L": []}, {}
            label = (ln, side(ln))
            continue
        if label is None:
            continue
        ln_, sd = label
        label = None
        if SUB.match(ln_) or re.match(r"^(?:total|jumlah)\s", ln_) and sd:
            k = sd or sec
            if k:
                sub[k] = v; rows_.append(f"{k}:SUBTOTAL {ln_}={v}"); pend2 = ("sub", k)
            sec = None if not sd else sec
        elif sd:
            acc[sd].append(v); rows_.append(f"{sd}:{ln_}={v}"); sec = None; pend2 = ("acc", sd)
        elif sec:
            acc[sec].append(v); rows_.append(f"{sec}:{ln_}={v}"); pend2 = ("acc", sec)
    # leaf rows first (a Sub Total may cover only a sub-group, e.g. institutions); section totals as the alternative;
    # keep whichever pair adds up closest to 100
    gap = lambda d: abs((d["F"] or 0) + (d["L"] or 0) - 100) if d["F"] is not None and d["L"] is not None else 999

    def pick(acc, sub):
        leaf = {k: (sum(v) if v else None) for k, v in acc.items()}
        alt = {k: sub.get(k, leaf[k]) for k in acc}
        return min((leaf, alt), key=gap)
    best, best2 = pick(acc, sub), pick(acc2, sub2)
    if gap(best2) > 1.0:
        best2 = {"F": None, "L": None}  # no complete second column
    return best["F"], best["L"], rows_, best2["F"], best2["L"]


# named holders (>= 5 % list): legal form decides local / foreign, as in KSEI's investor classes; individuals unknown
MAJ_PAGE = re.compile(r"komposisi pemegang saham|shareholders? composition|pemegang saham utama|main shareholders?|"
                      r"major shareholders?|5% atau lebih|5% or more|lebih dari 5%|more than 5%|di atas 5%|above 5%|"
                      # financial-statement note on share capital, also inside the AR (owner 8a: improve once)
                      r"susunan pemegang saham|komposisi kepemilikan saham|modal saham|share capital|"
                      r"pemegang saham pengendali|controlling shareholders?")
CURRENCY = re.compile(r"mata uang asing|foreign currenc|exchange rate|nilai tukar|kurs |sensitivit")
ENT_L = re.compile(r"(?:^|\s)pt\.?\s|,\s*pt\.?$|\(persero\)|republik indonesia|republic of indonesia|pemerintah|"
                   r"koperasi|yayasan|dana pensiun|(?:^|\s)perum\s|bpjs|danantara|daya anagata")
ENT_F = re.compile(r"(?<![a-z])(?:ltd|limited|pte|inc|corp|corporation|llc|gmbh|b\.v|n\.v|s\.a|ag|plc|bhd|berhad|sdn|"
                   r"pty|kabushiki|k\.k|s\.a\.r\.l|sarl|l\.p)(?![a-z])")
ENT_SKIP = re.compile(r"kustodian sentral|masyarakat|public|total|jumlah|treasur|lain-lain|others|komisaris|direktur|"
                      r"director|commissioner|nama pemegang|shareholder name|persentase|percentage|"
                      # holder-type categories are not named holders ("Perseroan Terbatas / Limited Liability Company")
                      r"limited liability compan|perseroan terbatas|^corporations?$|^korporasi$|reksa ?dana|mutual fund|"
                      r"asuransi|insurance|pension fund|foundation|cooperative|broker|individu|perorangan|individual|"
                      r"\+/-|%\)")


def major(lines, dec=None, me=""):
    buf, seen, out = [], set(), {"L": 0.0, "F": 0.0}
    rows_ = []
    for ln in lines:
        v = pct(ln, dec)
        if v is None:
            if not NUM.match(ln) and re.search(r"[a-z]", ln) and len(ln) <= 90:
                buf.append(ln)
            continue
        name = " ".join(buf[-2:]); buf = []
        if not name or ENT_SKIP.search(name) or (len(me) >= 6 and re.search(re.escape(me) + r"\s*(?:persero\s*)?tbk", re.sub(r"[^a-z ]", " ", name).replace("  ", " "))):
            continue  # holder-type category, or the issuer itself (FS-note header / treasury shares)
        l, f = bool(ENT_L.search(name)), bool(ENT_F.search(name))
        key = re.sub(r"[^a-z]", "", name)[-18:]  # tail of the name: "pemegang saham utama toto limited" = "toto limited"
        if l == f or key in seen:  # individual / unclear, or the same holder in a second column / repeated
            continue
        seen.add(key); k = "L" if l else "F"
        out[k] += v; rows_.append(f"{k}:{name}={v}")
    return out["F"], out["L"], rows_


NUMTOK = re.compile(r"^\(?[\d.,]+\)?%?$|^%$")


def split_lines(text):
    """Page lines; 'pt abc 1.234.567 45,67%' becomes 'pt abc', '1.234.567', '45,67%' (label and numbers on one line).
    Token-based (a nested regex here backtracked for minutes on long rows of numbers)."""
    out = []
    for x in text.split("\n"):
        x = norm(x).strip()
        if not x:
            continue
        toks = x.split(" ")
        k = len(toks)
        while k > 0 and NUMTOK.match(toks[k - 1]):
            k -= 1
        head, nums = " ".join(toks[:k]), toks[k:]
        if nums and head and re.search(r"[a-z]", head) and len(head) <= 90:
            merged = []
            for t in nums:  # "25,00 %" -> "25,00%"
                if t == "%" and merged:
                    merged[-1] += "%"
                else:
                    merged.append(t)
            out.append(head); out += merged
        else:
            out.append(x)
    return out


SENT = re.compile(r"(?:dalam negeri|domestik|lokal|domestic|local)[^.%]{0,70}?(\d{1,3}[.,]\d{1,5})\s?%[^.%]{0,90}?"
                  r"(?:asing|foreign)[^.%]{0,50}?(\d{1,3}[.,]\d{1,5})\s?%")


AUM = re.compile(r"(?<![a-z])aum(?![a-z])|assets? under management|dana kelolaan")  # AMOR lesson: AuM by investor geography
_SELF = {}


def self_core(code):
    """Core of the issuer's own name ('mineral sumberdaya mandiri'): an FS-note header 'PT Mineral Sumberdaya Mandiri
    Tbk dan entitas anaknya ... 99,76%' is not a holder (AKSI lesson, 10 Nov 2026); treasury shares are skipped too.
    Only core + 'Tbk' is skipped: parents often share the core ('PT Charoen Pokphand Indonesia Group', 'Unilever
    Indonesia Holding B.V.', 'PT Samudera Indonesia Tangguh')."""
    if not _SELF:
        for u in csv.DictReader((D / "universe.csv").open(encoding="utf-8")):
            n = norm(u.get("KSEI_Issuer") or u.get("Short_Name") or "")
            n = re.sub(r"(?<![a-z])(pt|tbk|persero)(?![a-z])|[^a-z ]", " ", n)
            _SELF[u["Code"]] = re.sub(r"\s+", " ", n).strip()
    return _SELF.get(code, "")


def screen_comp(code, doc, pages):
    out = []
    me = self_core(code)
    for pg in pages:
        t = norm(pg["text"])
        if AUM.search(t):
            continue  # assets-under-management splits (domestic / foreign investors of the funds), not ownership
        n = len(KEYS.findall(t)) + 10 * bool(re.search(r"komposisi pemegang saham|shareholders? composition", t))
        lines = split_lines(pg["text"])
        dec = page_dec(pg["text"])
        two = ";TWO_DATES" if "2024" in t and "2025" in t else ""
        base = {"Code": code, "File": doc, "Page": pg["p"], "Src": pg["src"], "Score": n}
        if CURRENCY.search(t) and not re.search(r"pemegang saham|shareholder", t):
            continue  # foreign-currency / exchange-rate tables, not ownership
        if n >= 6 and re.search(r"asing|foreign", t):
            f, l, rows_, f2, l2 = parse_table(lines, dec)
            st = ("SUM_OK" if f is not None and l is not None and abs(f + l - 100) <= 1.0 else
                  "FOREIGN_ONLY" if f is not None and l is None else "SUM_OFF" if rows_ else "NO_ROWS")
            if rows_:
                out.append(dict(base, Method="LOCAL_FOREIGN_TABLE", Foreign_Pct="" if f is None else round(f, 4),
                                Local_Pct="" if l is None else round(l, 4), Status=st + two, Rows=" | ".join(rows_),
                                Foreign_Pct_Col2="" if f2 is None else round(f2, 4), Local_Pct_Col2="" if l2 is None else round(l2, 4)))
        if MAJ_PAGE.search(t):
            f, l, rows_ = major(lines, dec, me)
            if rows_:
                st = "MAJOR_LOCAL_GT50" if l > 50 else "MAJOR_FOREIGN_GT50" if f > 50 else "MAJOR_NO_MAJORITY"
                out.append(dict(base, Method="NAMED_HOLDERS", Foreign_Pct=round(f, 4), Local_Pct=round(l, 4),
                                Status=st + two, Rows=" | ".join(rows_)))
    for pg in pages:  # a sentence with both shares: "dalam negeri menguasai 51,45% sedangkan ... asing memegang 48,55%"
        t = norm(pg["text"])
        for m in SENT.finditer(t):
            l, f = (float(x.replace(",", ".")) for x in (m.group(1), m.group(2)))
            if abs(f + l - 100) <= 1:
                out.append({"Code": code, "File": doc, "Page": pg["p"], "Src": pg["src"], "Score": 50,
                            "Method": "LOCAL_FOREIGN_TABLE", "Foreign_Pct": round(f, 4), "Local_Pct": round(l, 4),
                            "Status": "SUM_OK;SENTENCE", "Rows": m.group(0)[:200]})
    rank = lambda r: (0 if r["Status"].startswith("SUM_OK") else 1 if "GT50" in r["Status"] else 2, -r["Score"])
    out.sort(key=rank)
    return out[:5] or [{"Code": code, "File": doc, "Page": "", "Status": "NO_COMPOSITION_PAGE"}]



def main():
    codes = None
    if len(sys.argv) > 1:
        codes = {r["Code"] for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))}
    hits, docs, comp = [], [], []
    conf = {r["File"] for r in csv.DictReader((D / "manual" / "ar_file_reviews.csv").open(encoding="utf-8"))
            if r["Decision"] == "CONFIRMED_AR2025"} if (D / "manual" / "ar_file_reviews.csv").exists() else set()
    bad_web = {r["File"] for r in csv.DictReader((D / "web_ar_files.csv").open(encoding="utf-8"))
               if r["Check"] != "VERIFIED" and r["File"] not in conf} if (D / "web_ar_files.csv").exists() else set()
    if (D / "manual" / "ar_file_reviews.csv").exists():
        bad_web |= {r["File"] for r in csv.DictReader((D / "manual" / "ar_file_reviews.csv").open(encoding="utf-8"))
                    if r["Decision"].startswith("REJECTED")}
    # only texts listed in text_index.csv: a replaced file (e.g. a truncated IDX download repaired by id03e, 10 Nov 2026)
    # keeps its old json in data/text/ and must not be screened twice
    # The json is named by content hash; its "file" is whichever copy was extracted first. The same report can exist as
    # an unchecked website file AND a valid IDX file (ALKA, AGAR): use the text_index files, skip only if all are bad.
    live = {}
    for r in csv.DictReader((D / "text_index.csv").open(encoding="utf-8")):
        if r.get("SHA256"):
            live.setdefault((r["Code"], r["SHA256"][:12]), []).append(r["File"])
    for f in sorted((D / "text").glob("*/*.json")):
        code = f.parent.name
        if codes is not None and code not in codes or (code, f.stem) not in live:
            continue
        good = [x for x in live[(code, f.stem)] if x not in bad_web]
        if not good:
            continue  # unchecked website file (may be the 2024 report) or rejected
        j = json.loads(f.read_text(encoding="utf-8"))
        name = j["file"] if j["file"] in good else sorted(good)[0]
        docs.append(screen_nat(code, name, j["pages"], hits))
        comp += screen_comp(code, name, j["pages"])
    for name, rs in [("screen_nationality.csv", hits), ("screen_docs.csv", docs), ("screen_composition.csv", comp)]:
        keys = list(dict.fromkeys(k for r in rs for k in r)) or ["Code"]
        with (D / name).open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rs)
    print("documents", len(docs), "| with foreign label", sum(bool(d["Foreign_Labels"]) for d in docs),
          "| no label at all", sum(bool(d["Note"]) for d in docs))
    best = {}
    for r in comp:
        best.setdefault(r["Code"], r)
    print("composition: SUM_OK", sum(r["Status"].startswith("SUM_OK") for r in best.values()), "of", len(best))


if __name__ == "__main__":
    main()
