"""Malaysia step 3 – find (and optionally download) annual reports outside Bursa.

Bursa (bursamalaysia.com) blocks scripts, and the malaysiastock.biz free login allows only a few
pages a day, so the owner chose (7 Nov 2026) the companies' own websites. Bursa Listing
Requirements oblige every listed issuer to publish its annual report on its website.

Reports needed per company (owner rule: managers in calendar 2025): the FY ending in 2025, plus the
FY ending in 2026 when the year end is not 31 December (from data/ar_index.csv, built by my02).

Sources, in order:
  1. InSage-hosted report (IR provider; data/insage_ar.csv from my03a)
  2. the company's website (from the KLSE Screener stock page; only the first ~300 KB of that page
     is read and cached in raw/klsescreener/<code>.html), crawled up to MAX_PAGES pages,
     investor-relations links and iframes first; also follows a meta refresh, IR pages hosted by an
     IR provider on another host (ChartNexus, listedcompany.com, ...) and PDF URLs inside page scripts.
     Sites that answer with a bot challenge (Cloudflare, Incapsula) are not worked around.
  Links that point to bursamalaysia.com are recorded (BURSA_LINK_ONLY) but cannot be fetched.

Status per needed report: AVAILABLE_INSAGE / AVAILABLE_WEBSITE (PDF confirmed), BURSA_LINK_ONLY (the site
  sends readers to Bursa), SITE_BLOCKS_SCRIPTS (bot challenge on the site or its IR provider), NOT_FOUND
  (site read, no matching PDF), SITE_ERROR (site does not answer), NO_WEBSITE, WEBSITE_LOOKUP_FAILED,
  NOT_DUE_YET (FY ends in 2026, report not filed and not yet due: 4 months after the year end),
  NO_FY2025_AR_IN_INDEX (no FY ending in 2025 in the i3investor index).

Modes
  --check   availability only: confirm each best link returns a PDF (first 4 KB), no full download
            -> data/ar_availability.csv
  default   download to raw/web_ar/<code>/ with meta.json (URL, time, SHA-256) and a first-pages
            check (year + "annual report" + company name) -> data/web_ar_found.csv, web_ar_files.csv

Run from the project root:
  .venv/bin/python -I malaysia/pipeline/my03_web_ar.py [--check] [--workers 8] (all | codes.csv | code ...)
Downloads are untrusted data: never execute them; parse only with pymupdf.
"""
import csv, datetime as dt, hashlib, html, json, re, sys, threading, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse, unquote

import requests
import urllib3

urllib3.disable_warnings()
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
TODAY = dt.date(2026, 11, 7)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
MAX_PAGES = 30
NAV = re.compile(r"investor|\bir\b|/ir/|annual|report|financial|shareholder|bursa|announcement|corporate|download|publication|governance|information", re.I)
AR = re.compile(r"annual[\s_\-+%20]*report|integrated[\s_\-+%20]*(annual[\s_\-+%20]*)?report|(^|[^a-z])i?ar[\s_\-]?(20)?\d\d([^0-9]|$)|laporan[\s_\-]*tahunan|sreporttype=ar([^a-z]|$)", re.I)
BAD = re.compile(r"corporate[\s_\-%20]*governance|cg[\s_\-%20]*report|(^|[^a-z])cgr?([^a-z]|$)|sustainab|circular|notice|proxy|form|quarter|minutes|agm|egm|policy|charter|terms|prospectus|press|presentation|dividend|interim|statement[\s_\-]*to|share[\s_\-]*buy|bursa[\s_\-]*announcement|summary", re.I)
_local = threading.local()


def sess():
    if not hasattr(_local, "s"):
        _local.s = requests.Session(); _local.s.headers["User-Agent"] = UA
    return _local.s


def get(url, timeout=40, **kw):
    try:
        return sess().get(url, timeout=timeout, allow_redirects=True, **kw)
    except requests.exceptions.SSLError:
        try:
            return sess().get(url, timeout=timeout, allow_redirects=True, verify=False, **kw)
        except requests.RequestException:
            return None
    except requests.RequestException:
        return None


def website(code):
    """Company website from the KLSE Screener stock page (first ~300 KB only, cached)."""
    p = RAW / "klsescreener" / f"{code}.html"
    if not p.exists():
        for attempt in range(3):
            r = get(f"https://www.klsescreener.com/v2/stocks/view/{code}", 60, stream=True)
            time.sleep(1.5)  # one host: pause after every request, success or not
            if r is not None and r.status_code == 200:
                break
            status = r.status_code if r is not None else "no response"
            print(f"klsescreener {code}: HTTP {status}, attempt {attempt + 1}", flush=True)
            if r is not None:
                r.close()
            time.sleep((10, 30, 60)[attempt])  # KLSE Screener answers 202 now and then; a short wait is enough
        else:
            return None  # unknown (not cached, retry later)
        buf = b""
        try:
            for chunk in r.iter_content(16384):
                buf += chunk
                k = buf.find(b"Website:")
                if (k >= 0 and len(buf) > k + 800) or len(buf) > 300000:
                    break
        except requests.RequestException:
            return None
        finally:
            r.close()
        p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(buf)
    m = re.search(r'Website:\s*<a href="([^"]+)"', p.read_text(encoding="utf-8", errors="ignore"))
    return m.group(1).strip() if m else ""


SKIP_HOSTS = re.compile(r"facebook|linkedin|twitter|(^|\.)x\.com|youtube|instagram|google|whatsapp|wa\.me|apple\.com|tiktok|"
                        r"i3investor|klsescreener|malaysiastock|theedgemalaysia|thestar|marketscreener|investing\.com|"
                        r"bloomberg|reuters|wikipedia|bursamalaysia", re.I)
IR_LINK = re.compile(r"investor|annual[\s_\-]*report|\bir\b|/ir/|shareholder", re.I)


def host(u):
    h = (urlparse(u).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def same_site(u, hosts):
    a = host(u)
    return any(a == b or a.endswith("." + b) or b.endswith("." + a) for b in hosts if b)


def start_variants(start):
    """The website as listed, then the other scheme and with/without www (old or mistyped listings)."""
    p = urlparse(start if "://" in start else "http://" + start)
    h = p.hostname or ""
    alt = h[4:] if h.startswith("www.") else "www." + h
    other = "https" if p.scheme == "http" else "http"
    return [p.geturl()] + [f"{sch}://{hh}{p.path or '/'}" for sch, hh in ((other, h), (p.scheme, alt), (other, alt))]


CHALLENGE = re.compile(r"Just a moment|cf-chl|_Incapsula_|captcha|Attention Required|challenge-platform|awswaf", re.I)


def blocked(r):
    """True if the host answered with a bot challenge (Cloudflare, Incapsula, AWS WAF): not worked around."""
    return (r.status_code == 202 and len(r.content) < 2000) or (
        r.status_code in (202, 403, 429, 503) and bool(CHALLENGE.search(r.text[:30000])))


CTX = " \x1f "  # separates a link's own text from the label just before it


def parse_page(r, pdfs, queue, seen, hosts, insage):
    """Collect PDF links and queue the next pages from one HTML page (also 404 pages, which keep the menu)."""
    ctype = r.headers.get("content-type", "").lower()
    if "pdf" in ctype:
        if r.status_code in (200, 206):
            pdfs.setdefault(r.url, "")
        return
    if "html" not in ctype or r.status_code >= 500:
        return
    t = r.text
    if not SKIP_HOSTS.search(host(r.url)):
        hosts.add(host(r.url))  # the site moved, or a link led to its IR provider
    m = re.search(r'<meta[^>]+http-equiv\s*=\s*["\']?refresh["\']?[^>]*?url\s*=\s*([^"\'>\s]+)', t[:20000], re.I)
    if m:
        u = urljoin(r.url, html.unescape(m.group(1).strip()))
        if u.startswith("http") and not SKIP_HOSTS.search(host(u)):
            hosts.add(host(u)); queue.append((0, u))
    for src in re.findall(r'<i?frame\b[^>]*?src\s*=\s*["\']([^"\']+)["\']', t, re.I):
        u = urljoin(r.url, html.unescape(src.strip()))
        if u.startswith("http") and u not in seen and not re.search(r"youtube|google|facebook|map", u, re.I):
            queue.append((0, u))  # IR widgets are often embedded as iframes
    for sym in re.findall(r"insage\.com\.my/[^\"'\s]*?(?:[?&]Symbol=|sCompanyCode=|/Upload/Docs/)([A-Za-z0-9&]+)", t, re.I):
        insage.add(sym.upper())  # the company's InSage symbol, which can differ from the stock code
    last = 0
    for mm in re.finditer(r'<a\b[^>]*?href\s*=\s*["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', t, re.S | re.I):
        href, text = mm.group(1), mm.group(2)
        before, last = t[max(last, mm.start() - 1500):mm.start()], mm.end()
        u = urljoin(r.url, html.unescape(href.strip()))
        if not u.startswith("http"):
            continue
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()[:200]
        label = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", before)))).strip()[-200:]
        if "bursamalaysia.com" in u.lower():  # not fetchable by script; kept for the manual list
            if AR.search(txt) or re.search(r"[/,=]ar(co)?([,&/]|$)|annual", u, re.I):
                pdfs.setdefault(u, "BURSA_LINK " + txt)
            continue
        if re.search(r"\.pdf($|\?)", u, re.I) or ("annual report" in txt.lower() and "download" in (u + txt).lower()):
            pdfs.setdefault(u, txt + (CTX + label if label else "")); continue
        if u in seen:
            continue
        if same_site(u, hosts):
            if NAV.search(u + " " + txt):
                queue.append((0 if re.search(r"annual|investor|\bir\b|/ir/", u + " " + txt, re.I) else 1, u))
        elif not SKIP_HOSTS.search(host(u)) and IR_LINK.search(u + " " + txt):
            hosts.add(host(u)); queue.append((0, u))  # IR pages hosted by a provider (ChartNexus, listedcompany.com, ...)
    for u in re.findall(r'https?:(?:\\?/){2}[^"\'\s<>()]+?\.pdf', t, re.I):  # PDF URLs written in scripts / JSON
        u = u.replace("\\/", "/")
        if "bursamalaysia.com" not in u.lower():
            pdfs.setdefault(u, "")


def crawl(start):
    """Return ({pdf_url: anchor_text}, pages that answered, hosts that sent a bot challenge, InSage symbols
    seen on the pages), within MAX_PAGES requests, IR links and iframes first."""
    seen, pdfs, queue, tried, answered, hosts, walls, syms = set(), {}, [], 0, 0, {host(start)}, set(), set()
    r = None
    for u in start_variants(start):
        seen.add(u); tried += 1
        r = get(u)
        if r is not None:
            break
    while True:
        if r is not None:
            if blocked(r):
                walls.add(host(r.url))
            else:
                answered += r.status_code < 500
                parse_page(r, pdfs, queue, seen, hosts, syms)
        r = None
        queue.sort(key=lambda x: x[0])
        while queue and (queue[0][1] in seen or host(queue[0][1]) in walls):
            queue.pop(0)
        if not queue or tried >= MAX_PAGES:
            return pdfs, answered, walls, syms
        _, url = queue.pop(0)
        seen.add(url); tried += 1
        r = get(url)
        time.sleep(0.5)


def year_points(s, full, year):
    """+4 if the file name or link text names the financial year (2025, AR25, FY25, 2024/25), -4 if it names
    another year, +2 if only the rest of the URL has the year. In a range "2024/2025" the second year is the year end."""
    ends = set()
    for a, b in re.findall(r"(20\d\d)\s*[/\-–_]\s*(20\d\d|\d\d)(?!\d)", s):
        b = b if len(b) == 4 else a[:2] + b
        if int(b) == int(a) + 1:
            ends.add(b)
    if ends:
        return 4 if str(year) in ends else -4
    if str(year) in s or re.search(r"(ar|fy|ir|report|annual)[\s_\-'’]*%s(?!\d)" % str(year)[2:], s):
        return 4
    if [y for y in re.findall(r"20\d\d", s) if y != str(year)]:
        return -4
    return 2 if str(year) in full else 0


def score(url, text, year, hints):
    text, _, label = text.partition(CTX)
    label = label.lower()
    s = (unquote(urlparse(url).path.split("/")[-1]) + " " + text).lower()
    full = unquote(url).lower() + " " + text.lower()
    ar_dir = re.search(r"/(ar|annual[\s_\-]*reports?|annualreports?)/", unquote(urlparse(url).path).lower())  # e.g. ChartNexus /docs/ar/2025.pdf
    pts = 5 if (AR.search(s) or AR.search(full) or ar_dir or AR.search(label[-80:])) else 0
    yp = year_points(s, full, year)
    if yp in (0, 2) and label:  # no year on the link itself: the heading or row label just before it
        yl = year_points(label[-80:], "", year)
        yp = 3 if yl > 0 else (-4 if yl < 0 else yp)
    pts += yp
    if BAD.search(s):
        pts -= 6
    toks = set(re.findall(r"[a-z0-9]+", s))
    for h in hints:
        ht = set(re.findall(r"[a-z0-9]+", h.lower())) - {"pdf"}
        if ht and len(toks & ht) / len(ht) >= 0.6:
            pts += 3; break
    return pts


INSAGE_TOP = "https://www.insage.com.my/ir/cmn/trps02/ArTop.aspx?Symbol={}"
INSAGE_RE = re.compile(r"<h4>([^<]+)</h4>\s*(?:<div[^>]*>)?\s*<a href=\"(https://www\.insage\.com\.my/ir/cmn/downloading\.aspx\?sFileName=(\d+)&(?:amp;)?sReportType=(\w+)[^\"]*)\"")


def insage_reports(symbol):
    """Report links on InSage's report page for an InSage symbol seen on the company website (cached)."""
    p = RAW / "insage" / f"sym_{re.sub(r'[^A-Za-z0-9]', '_', symbol)}.html"
    if not p.exists():
        r = get(INSAGE_TOP.format(quote(symbol)), 60)
        if r is None:
            return []
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(r.text if r.status_code == 200 else f"<!-- HTTP {r.status_code} -->", encoding="utf-8")
        time.sleep(0.7)
    t = p.read_text(encoding="utf-8", errors="ignore")
    return [{"Label": html.unescape(lb).strip(), "Report_Type": rt, "URL": html.unescape(u)} for lb, u, _, rt in INSAGE_RE.findall(t)]


def probe_pdf(url):
    """True if the URL serves a PDF (reads the first 4 KB only)."""
    r = get(url, 60, stream=True, headers={"Range": "bytes=0-4095"})
    if r is None:
        return False
    try:
        head = next(r.iter_content(4096), b"")
    except requests.RequestException:
        head = b""
    finally:
        r.close()
    return r.status_code in (200, 206) and head.lstrip().startswith(b"%PDF")


def check_pdf(path, year, company):
    import fitz  # pymupdf
    try:
        doc = fitz.open(path)
        text = " ".join(doc[i].get_text() for i in range(min(6, doc.page_count))).lower()
        n = doc.page_count
    except Exception:
        return 0, "NOT_A_PDF"
    first = re.findall(r"[a-z]+", company.lower())[:1]
    ok = (str(year) in text, any(k in text for k in ("annual report", "integrated report", "laporan tahunan")),
          bool(first) and first[0] in text)
    return n, "VERIFIED" if all(ok) else "CHECK(year={},ar={},name={})".format(*map(int, ok))


def needs(code, idx):
    """Reports needed: FY ending in 2025, and FY ending in 2026 if the year end is not December."""
    rows, out = idx.get(code, []), []
    dates = {}
    for r in rows:
        try:
            dates[dt.datetime.strptime(r["FY_End"], "%d-%b-%Y").date()] = r
        except ValueError:
            pass
    fy25 = [d for d in dates if d.year == 2025]
    for d in sorted(fy25):
        out.append((d, dates[d]["AR_Ann_Date"] != ""))
    for d in sorted(x for x in dates if x.year == 2026 and (x.month, x.day) != (12, 31)):
        out.append((d, dates[d]["AR_Ann_Date"] != ""))
    if fy25 and max(fy25).month != 12 and not any(d.year == 2026 for d, _ in out):
        d = max(fy25)
        exp = dt.date(2026, d.month, min(d.day, 28 if d.month == 2 else d.day))
        out.append((exp, False))  # expected FY2026 report not (yet) in the index
    return out


def process(code, ctx, check):
    idx, hints, names, insage = ctx
    found, files = [], []
    need = needs(code, idx)
    base = {"Stock_Code": code, "Company": names.get(code, "")}
    if not need:
        return [dict(base, FY_End="", AR_Filed_On_Bursa="", Status="NO_FY2025_AR_IN_INDEX", Source="", URL="",
                     Website="", Pages_Crawled=0, PDF_Links=0, Bursa_Links="")], []
    site, pdfs, pages, walls, syms, crawled = None, {}, 0, set(), set(), False
    for d, filed in need:
        fye, year = d.strftime("%d-%b-%Y"), d.year
        row = dict(base, FY_End=fye, AR_Filed_On_Bursa=int(filed), Status="", Source="", URL="", Website="",
                   Pages_Crawled=0, PDF_Links=0, Bursa_Links="", Blocked_Hosts="")
        if not filed and d + dt.timedelta(days=122) > TODAY:
            row["Status"] = "NOT_DUE_YET"; found.append(row); continue
        got = []
        for r in insage.get(code, []):  # 1) InSage
            if r["Report_Type"] == "AR" and str(year) in r["Label"] and not BAD.search(r["Label"]):
                got.append(("INSAGE", r["URL"], r["Label"], ""))
        if not got:  # 2) website
            if site is None:
                site = website(code)
            if site:
                if not crawled:
                    pdfs, pages, walls, syms = crawl(site); crawled = True
                for sym in sorted(syms - {code}):  # InSage pages under another symbol (e.g. LG for 3174)
                    for r in insage_reports(sym):
                        if r["Report_Type"] == "AR" and str(year) in r["Label"] and not BAD.search(r["Label"]):
                            got.append(("INSAGE", r["URL"], r["Label"], ""))
                cands = sorted(((score(u, t, year, hints.get((code, fye), [])), u, t) for u, t in pdfs.items()), reverse=True)
                bursa = [c for c in cands if c[2].startswith("BURSA_LINK") and c[0] >= 0]  # the site sends readers to Bursa
                row["Bursa_Links"] = ";".join(c[1] for c in bursa[:4])
                for sc, u, t in [c for c in cands if not c[2].startswith("BURSA_LINK") and c[0] >= 7][:4]:
                    got.append(("WEBSITE", u, t, sc))
        row.update(Website=site or "", Pages_Crawled=pages, PDF_Links=len(pdfs), Blocked_Hosts=";".join(sorted(walls)))
        ok_urls = []
        for source, u, t, sc in got:
            if check:
                if probe_pdf(u):
                    ok_urls.append((source, u)); break  # one confirmed link is enough for availability
                continue
            r = get(u, 180)
            if r is None or r.status_code != 200 or not r.content.startswith(b"%PDF"):
                continue
            h = hashlib.sha256(r.content).hexdigest()
            out = RAW / "web_ar" / code / f"{d.isoformat()}_{h[:12]}.pdf"
            out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(r.content)
            out.with_suffix(".meta.json").write_text(json.dumps({"url": u, "final_url": r.url, "anchor": t.replace(CTX, " || "), "source": source,
                "content_disposition": r.headers.get("content-disposition", ""),
                "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "sha256": h,
                "bytes": len(r.content)}, indent=1))
            n, chk = check_pdf(out, year, names.get(code, ""))
            files.append(dict(base, FY_End=fye, Source=source, File=str(out.relative_to(ROOT)), URL=u, Anchor=t.replace(CTX, " || "),
                              Score=sc, Pages=n, Check=chk))
            ok_urls.append((source, u))
        if ok_urls:
            row.update(Status="AVAILABLE_" + ok_urls[0][0], Source=ok_urls[0][0], URL=ok_urls[0][1])
        elif site == "" and not got:
            row["Status"] = "NO_WEBSITE"
        elif site is None and not got:
            row["Status"] = "WEBSITE_LOOKUP_FAILED"
        elif row["Bursa_Links"]:
            row["Status"] = "BURSA_LINK_ONLY"
        elif walls and not got:
            row["Status"] = "SITE_BLOCKS_SCRIPTS"  # bot challenge on the site or its IR provider: download by hand
        else:
            row["Status"] = "NOT_FOUND" if pages else "SITE_ERROR"
        found.append(row)
    return found, files


def main():
    args = sys.argv[1:]
    check = "--check" in args
    workers = int(args[args.index("--workers") + 1]) if "--workers" in args else 6
    rest = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--workers")]
    univ = list(csv.DictReader((ROOT / "data" / "universe.csv").open(encoding="utf-8")))
    if rest == ["all"]:
        codes = sorted({u["Stock_Code"] for u in univ if u["Exchange"] == "MK" and u["Stock_Code"] and u["In_Scope"] != "0"})
    elif rest and rest[0].endswith(".csv"):
        codes = [r["Stock_Code"] for r in csv.DictReader(open(rest[0], encoding="utf-8"))]
    else:
        codes = rest
    idx = defaultdict(list)
    for r in csv.DictReader((ROOT / "data" / "ar_index.csv").open(encoding="utf-8")):
        idx[r["Stock_Code"]].append(r)
    hints = defaultdict(list)
    for r in csv.DictReader((ROOT / "data" / "ar_attachments.csv").open(encoding="utf-8")):
        hints[(r["Stock_Code"], r["FY_End"])].append(r["Attachment_Name"])
    names = {u["Stock_Code"]: u["Bursa_Company_Name"] for u in univ}
    insage = defaultdict(list)
    for r in csv.DictReader((ROOT / "data" / "insage_ar.csv").open(encoding="utf-8")):
        insage[r["Stock_Code"]].append(r)
    ctx = (idx, hints, names, insage)
    # website lookups on KLSE Screener: one host, so sequential and polite, before the parallel crawl
    todo = [c for c in codes if not (RAW / "klsescreener" / f"{c}.html").exists()
            and not all(any(r["Report_Type"] == "AR" and str(d.year) in r["Label"] for r in insage.get(c, []))
                        for d, _ in needs(c, idx) or [(dt.date(2025, 1, 1), 0)])]
    for i, c in enumerate(todo):
        website(c)
        if (i + 1) % 100 == 0:
            print(f"websites {i + 1}/{len(todo)}", flush=True)
    found, files = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process, c, ctx, check): c for c in codes}
        for i, f in enumerate(as_completed(futs)):
            try:
                a, b = f.result()
            except Exception as e:  # keep going; record the failure
                a, b = [{"Stock_Code": futs[f], "Status": f"SCRIPT_ERROR {type(e).__name__}"}], []
            found += a; files += b
            if (i + 1) % 50 == 0:
                print(f"companies {i + 1}/{len(codes)}", flush=True)
    print("this run:", Counter(r["Status"] for r in found).most_common())
    outs = [("ar_availability.csv", found)] if check else [("web_ar_found.csv", found), ("web_ar_files.csv", files)]
    for name, rows in outs:
        path = ROOT / "data" / name
        if rest != ["all"] and path.exists():  # a run on part of the list keeps the other companies' rows
            run = set(codes)
            rows = [r for r in csv.DictReader(path.open(encoding="utf-8")) if r["Stock_Code"] not in run] + rows
        rows.sort(key=lambda r: (r["Stock_Code"], r.get("FY_End", "")))
        if rows:
            keys = list(dict.fromkeys(k for r in rows for k in r))
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
        if name != "web_ar_files.csv":
            print(name, "all companies:", Counter(r["Status"] for r in rows).most_common())


if __name__ == "__main__":
    main()
