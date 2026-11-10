"""Indonesia step 3 – find (and optionally download) the 2025 annual report on the company's website.

idx.co.id blocks scripts (Cloudflare 403), so the owner chose (7 Nov 2026) the company's own website first
(OJK rule: every issuer publishes its annual report on its website); reports a script cannot reach are
listed for download by hand from IDX in a browser.

Website per company from data/websites.csv (id03a). The site is crawled up to MAX_PAGES pages,
investor-relations links and iframes first; also follows a meta refresh, IR pages hosted on another host
and PDF URLs inside page scripts. Sites that answer with a bot challenge (Cloudflare, Incapsula, AWS WAF)
are not worked around. Links that point to idx.co.id are recorded (IDX_LINK_ONLY) but not fetched.
Crawler code adapted from malaysia/pipeline/my03_web_ar.py (Indonesian keywords added).

WordPress sites (seen from /wp-content/ in a page): the public media REST API is also searched for PDFs.
After the home page, the sitemap (robots.txt, /sitemap.xml) supplies IR pages (menus built by JavaScript are not in the HTML).

Status: AVAILABLE_WEBSITE (PDF confirmed), IDX_LINK_ONLY, SITE_BLOCKS_SCRIPTS (bot challenge or a short 403),
  JS_ONLY_SITE (pages answered but carry < 5 links: built by JavaScript), NOT_FOUND (site read, no matching
  PDF), SITE_ERROR (site does not answer), NO_WEBSITE, WEBSITE_LOOKUP_FAILED

Modes
  --check   availability only: confirm the best link returns a PDF (first 4 KB) -> data/ar_availability.csv
  default   download to raw/web_ar/<code>/ with .meta.json (URL, time, SHA-256) and a first-pages check
  --known   (download) reuse the candidate links of data/ar_availability.csv instead of crawling again
            (year + "annual report/laporan tahunan" + company name) -> data/web_ar_found.csv, web_ar_files.csv

Run from the project root:
  .venv/bin/python -I indonesia/pipeline/id03_web_ar.py [--check] [--workers 8] [--year 2025] [--sites websites.csv]
      [--out dir] [--max-pages 30] [--guess] (all | codes.csv | code ...)
  Second pass (owner 8 Nov 2026): --max-pages 60 --guess on the companies not yet AVAILABLE.
Downloads are untrusted data: never execute them; parse only with pymupdf.
"""
import csv, datetime as dt, hashlib, html, json, re, shutil, sys, threading, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
import urllib3

urllib3.disable_warnings()
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
KNOWN = {}  # code -> [(score, url, anchor)] with --known
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
MAX_PAGES = 30  # --max-pages
GUESS = False   # --guess: also try common IR paths (second pass)
GUESS_PATHS = ["/hubungan-investor", "/id/hubungan-investor", "/investor-relations", "/en/investor-relations", "/investor",
               "/laporan-tahunan", "/id/laporan-tahunan", "/annual-report", "/en/annual-report",
               "/investor-relations/annual-report", "/hubungan-investor/laporan-tahunan", "/id/hubungan-investor/laporan-tahunan"]
NAV = re.compile(r"investor|hubungan|\bir\b|/ir/|annual|report|laporan|tahunan|financial|keuangan|shareholder|pemegang|"
                 r"publikasi|publication|governance|tata[\s_\-]*kelola|informasi|information|download|unduh|corporate|perusahaan", re.I)
AR = re.compile(r"annual[\s_\-+%20]*report|integrated[\s_\-+%20]*(annual[\s_\-+%20]*)?report|laporan[\s_\-+%20]*tahunan|"
                r"(^|[^a-z])(i?ar|lt)[\s_\-]?(20)?\d\d([^0-9]|$)", re.I)
BAD = re.compile(r"sustainab|keberlanjutan|laporan[\s_\-%20]*keuangan|financial[\s_\-%20]*(statement|report)|"
                 r"(^|[^a-z])(lk|fs)[\s_\-]?(20)?\d\d([^0-9]|$)|circular|notice|pemanggilan|pengumuman|proxy|kuasa|(^|[^a-z])forms?([^a-z]|$)|"
                 r"quarter|triwulan|kuartal|semester|interim|minutes|risalah|(^|[^a-z])(agm|egm|rups|rupst|rupslb)([^a-z]|$)|"
                 r"policy|kebijakan|charter|piagam|pedoman|prospe[ck]t|(^|[^a-z])press|siaran|presentation|presentasi|public[\s_\-]*expose|"
                 r"paparan|dividen|keterbukaan|summary|ringkas", re.I)
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
        except (requests.RequestException, UnicodeError, ValueError):
            return None
    except (requests.RequestException, UnicodeError, ValueError):  # bad URLs on a site (IDNA, odd schemes)
        return None


SKIP_HOSTS = re.compile(r"facebook|linkedin|twitter|(^|\.)x\.com|youtube|instagram|google|whatsapp|wa\.me|apple\.com|tiktok|"
                        r"stockanalysis|idnfinancials|marketscreener|investing\.com|kontan|bisnis\.com|cnbcindonesia|"
                        r"bloomberg|reuters|wikipedia|idx\.co\.id|ksei\.co\.id|ojk\.go\.id", re.I)
IR_LINK = re.compile(r"investor|annual[\s_\-]*report|laporan[\s_\-]*tahunan|hubungan[\s_\-]*investor|\bir\b|/ir/|shareholder", re.I)


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
    return (r.status_code in (202, 403) and len(r.content) < 2000) or (
        r.status_code in (202, 403, 429, 503) and bool(CHALLENGE.search(r.text[:30000])))


CTX = " \x1f "  # separates a link's own text from the label just before it


def parse_page(r, pdfs, queue, seen, hosts):
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
    last = 0
    for mm in re.finditer(r'<a\b[^>]*?href\s*=\s*["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', t, re.S | re.I):
        href, text = mm.group(1), mm.group(2)
        before, last = t[max(last, mm.start() - 1500):mm.start()], mm.end()
        u = urljoin(r.url, html.unescape(href.strip()))
        if not u.startswith("http"):
            continue
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()[:200]
        label = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", before)))).strip()[-200:]
        if "idx.co.id" in u.lower():  # IDX blocks scripts; kept for the manual list
            if AR.search(txt) or AR.search(unquote(u)) or re.search(r"annual|tahunan", u, re.I):
                pdfs.setdefault(u, "IDX_LINK " + txt)
            continue
        if re.search(r"\.pdf($|\?)", u, re.I) or (re.search(r"annual report|laporan tahunan", txt, re.I) and re.search(r"download|unduh", u + txt, re.I)):
            pdfs.setdefault(u, txt + (CTX + label if label else "")); continue
        if u in seen:
            continue
        if same_site(u, hosts):
            if NAV.search(u + " " + txt):
                queue.append((0 if re.search(r"annual|tahunan|investor|\bir\b|/ir/", u + " " + txt, re.I) else 1, u))
        elif not SKIP_HOSTS.search(host(u)) and IR_LINK.search(u + " " + txt):
            hosts.add(host(u)); queue.append((0, u))  # IR pages hosted by a provider (ChartNexus, listedcompany.com, ...)
    for u in re.findall(r'https?:(?:\\?/){2}[^"\'\s<>()]+?\.pdf', t, re.I):  # PDF URLs written in scripts / JSON
        u = u.replace("\\/", "/")
        if "idx.co.id" not in u.lower():
            pdfs.setdefault(u, "")


def wp_media(base, pdfs):
    """WordPress sites: PDFs in the media library via the public REST API (/wp-json/wp/v2/media), searched for
    the report words; title used as link text. Returns the number of requests made."""
    n = 0
    for q in ("annual report", "laporan tahunan", "2025"):
        r = get(urljoin(base, "/wp-json/wp/v2/media"), params={"search": q, "per_page": 100, "mime_type": "application/pdf"})
        n += 1
        if r is None or r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
            return n
        try:
            items = r.json()
        except ValueError:
            return n
        for it in items if isinstance(items, list) else []:
            u = it.get("source_url") or ""
            title = html.unescape(re.sub(r"<[^>]+>", " ", (it.get("title") or {}).get("rendered", ""))).strip()
            if u.lower().endswith(".pdf"):
                pdfs.setdefault(u, title)
        time.sleep(0.5)
    return n


SITEMAP_PAGE = re.compile(r"annual|tahunan|investor|laporan|report|hubungan|shareholder|pemegang", re.I)


def sitemap_urls(base):
    """URLs from /robots.txt 'Sitemap:' lines, /sitemap.xml and /sitemap_index.xml (sites whose menu is built by
    JavaScript still list their pages there). At most 8 sitemap files. Returns (pdf urls, page urls)."""
    todo, done, pdfs, pages = [], set(), [], []
    r = get(urljoin(base, "/robots.txt"), 20)
    if r is not None and r.status_code == 200 and "text" in r.headers.get("content-type", ""):
        todo += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", r.text)
    todo += [urljoin(base, "/sitemap.xml"), urljoin(base, "/sitemap_index.xml")]
    while todo and len(done) < 8:
        u = todo.pop(0)
        if u in done:
            continue
        done.add(u)
        r = get(u, 30)
        if r is None or r.status_code != 200 or "<loc>" not in r.text[:200000]:
            continue
        for loc in re.findall(r"<loc>\s*(?:<!\[CDATA\[)?([^<\]]+)", r.text):
            loc = html.unescape(loc.strip())
            if re.search(r"\.xml(\.gz)?$", loc, re.I):
                if SITEMAP_PAGE.search(loc) or "page" in loc.lower() or len(done) + len(todo) < 8:
                    todo.append(loc)
            elif re.search(r"\.pdf($|\?)", loc, re.I):
                pdfs.append(loc)
            elif SITEMAP_PAGE.search(unquote(loc)):
                pages.append(loc)
    return pdfs, pages


def crawl(start):
    """Return ({pdf_url: anchor_text}, pages that answered, hosts that sent a bot challenge, links seen,
    WordPress flag), within MAX_PAGES requests, IR links and iframes first."""
    seen, pdfs, queue, tried, answered, hosts, walls = set(), {}, [], 0, 0, {host(start)}, set()
    links, wp, base, sitemap_done = 0, False, None, False
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
                if "html" in r.headers.get("content-type", "").lower():
                    t = r.text
                    links += len(re.findall(r"<a\b[^>]*href", t, re.I))
                    if not wp and re.search(r"/wp-content/|/wp-json/|wp-includes", t):
                        wp, base = True, r.url
                    if base is None:
                        base = r.url
                parse_page(r, pdfs, queue, seen, hosts)
        r = None
        queue.sort(key=lambda x: x[0])
        while queue and (queue[0][1] in seen or host(queue[0][1]) in walls):
            queue.pop(0)
        if not sitemap_done and base and not walls:
            sitemap_done = True  # right after the home page: menus built by JavaScript are missing from the HTML
            sp, pg = sitemap_urls(base)
            for u in sp:
                pdfs.setdefault(u, "")
            pg.sort(key=lambda u: (not re.search(r"annual|tahunan", u, re.I), len(u)))
            queue += [(-1 if re.search(r"annual|tahunan", u, re.I) else 0, u) for u in pg[:15] if u not in seen]
            if GUESS:
                queue += [(0, urljoin(base, g)) for g in GUESS_PATHS if urljoin(base, g) not in seen]
            links += len(sp) + len(pg)
        if not queue or tried >= MAX_PAGES:
            if wp:
                wp_media(base, pdfs)
            return pdfs, answered, walls, links, wp
        _, url = queue.pop(0)
        seen.add(url); tried += 1
        r = get(url)
        time.sleep(0.5)


MONTH = r"(\d{1,2}|jan\w*|feb\w*|mar\w*|apr\w*|mei|may|jun\w*|jul\w*|agu\w*|aug\w*|sep\w*|okt\w*|oct\w*|nov\w*|des\w*|dec\w*)"
DATES = [re.compile(r"(?<!\d)\d{1,2}[\s_\-.]*%s[\s_\-.]*(20\d\d)(?!\d)" % MONTH, re.I),
         re.compile(r"(?<!\d)(20\d\d)[\-_.]?(0[1-9]|1[0-2])[\-_.]?([0-2]\d|3[01])(?!\d)")]
MONTH_NO = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
MONTH_NO.update({"mei": 5, "agu": 8, "okt": 10, "des": 12})


def strip_dates(s):
    """Remove day-month-year dates (publication dates such as '29-April-2025', '30-04-2025', '20250430').
    Returns the text and the years of dates in January-June (a report published then is usually the
    previous year's report)."""
    early = set()
    for rx in DATES:
        for m in rx.finditer(s):
            g = m.groups()
            if len(g) == 2:
                mon, yr = g[0].lower(), g[1]
                mon = int(mon) if mon.isdigit() else MONTH_NO.get(mon[:3], 0)
            else:
                yr, mon = g[0], int(g[1])
            if 1 <= mon <= 6:
                early.add(yr)
        s = rx.sub(" ", s)
    return s, early


def year_points(s, full, year):
    """+4 if the file name or link text names the financial year (2025, AR25, FY25, 2024/25), -4 if it names
    another year, +2 if only the rest of the URL has the year. In a range "2024/2025" the second year is the year end.
    Publication dates are removed first; a January-June date of the year alone (no year left) gives -4."""
    s, early = strip_dates(s)
    if str(year) in early and not re.search(r"20\d\d", s):
        return -4
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


BLOCKED = []  # 403 / 429 answers met by fetch_pdf (callers stop at once)


def fetch_pdf(url, dest, tries=12, start=None, pause=0):
    """Stream a PDF to dest/.part (large reports time out when read into memory). A dropped connection resumes with
    an HTTP Range request; the size is checked against Content-Length / Content-Range. Returns
    (tmp_path, sha256, bytes, response) or None. Not a PDF -> None at once.
    Lesson (10 Nov 2026): IDX answers with Transfer-Encoding: chunked and no Content-Length, and the connection can end
    cleanly after ~20-30 MB, which looked like a complete file (43 truncated IDX reports). With the size unknown, the
    next pass asks for the rest (Range): 206 = more bytes, 416 with Content-Range */N == size = complete.
    start = an earlier partial download to resume from (repair); pause = seconds before every retry request."""
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / ".part"
    tmp.unlink(missing_ok=True)
    if start is not None:
        shutil.copyfile(start, tmp)
    total, last, done, prev200 = None, None, False, None
    for k in range(tries):
        have = tmp.stat().st_size if tmp.exists() else 0
        if k and pause:
            time.sleep(pause)
        r = get(url, 120, stream=True, headers={"Range": f"bytes={have}-"} if have else {})
        if r is not None and r.status_code == 416 and have:
            m = re.search(r"/(\d+)$", r.headers.get("content-range", "")); r.close()
            if m and int(m.group(1)) == have:  # the server has no further bytes
                done = True; break
            tmp.unlink(missing_ok=True); continue  # size mismatch: start again
        if r is not None and r.status_code in (403, 429):  # blocked: never retry against a block
            BLOCKED.append(f"{r.status_code} {url}"); r.close(); tmp.unlink(missing_ok=True)
            return None
        if r is None or r.status_code not in (200, 206):
            time.sleep(5 * (k + 1)); continue
        if r.status_code == 200:
            have, total = 0, int(r.headers.get("content-length") or 0) or None  # no range support: from the start
        elif total is None:
            m = re.search(r"/(\d+)$", r.headers.get("content-range", ""))
            total = int(m.group(1)) if m else None
        try:
            with tmp.open("ab" if have else "wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
        except (requests.RequestException, OSError):
            time.sleep(5 * (k + 1)); continue
        finally:
            r.close()
        last = last if r.status_code == 206 and last is not None else r
        with tmp.open("rb") as fh:
            if not fh.read(16).lstrip().startswith(b"%PDF"):
                tmp.unlink(missing_ok=True)
                return None
        size = tmp.stat().st_size
        if total is not None and size >= total:
            done = True; break
        if r.status_code == 200 and total is None:  # size unknown: the next pass probes with Range
            if prev200 == size:  # no Range support and the same size twice: accept
                done = True; break
            prev200 = size
    if not done:
        tmp.unlink(missing_ok=True)
        return None
    h = hashlib.sha256()
    with tmp.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return tmp, h.hexdigest(), tmp.stat().st_size, last


def check_pdf(path, year, company):
    import fitz  # pymupdf
    try:
        doc = fitz.open(path)
        text = " ".join(doc[i].get_text() for i in range(min(6, doc.page_count))).lower()
        n = doc.page_count
    except Exception:
        return 0, "NOT_A_PDF"
    first = [w for w in re.findall(r"[a-z]+", company.lower()) if w not in ("pt", "tbk")][:1]
    ok = (str(year) in text, any(k in text for k in ("annual report", "integrated report", "laporan tahunan")),
          bool(first) and first[0] in text)
    return n, "VERIFIED" if all(ok) else "CHECK(year={},ar={},name={})".format(*map(int, ok))


def process(code, ctx, check, year):
    sites, names = ctx
    w = sites.get(code, {})
    site = w.get("Website", "")
    row = {"Code": code, "Company": names.get(code, ""), "Year": year, "Status": "", "URL": "", "Website": site,
           "Website_Source": w.get("Website_Source", ""), "Pages_Crawled": 0, "PDF_Links": 0, "IDX_Links": "",
           "Blocked_Hosts": "", "Candidates": ""}
    if not site:
        row["Status"] = "WEBSITE_LOOKUP_FAILED" if w.get("Website_Source") == "LOOKUP_FAILED" else "NO_WEBSITE"
        return [row], []
    if code in KNOWN:  # --known: candidates of the earlier check pass, no new crawl
        good, idx, walls, pages, links = KNOWN[code], [], set(), 1, 99
        row.update(Pages_Crawled="KNOWN", Candidates=" | ".join(f"{c[0]}:{c[1]}" for c in good))
    else:
        pdfs, pages, walls, links, wp = crawl(site)
        cands = sorted(((score(u, t, year, []), u, t) for u, t in pdfs.items()), reverse=True)
        idx = [c for c in cands if c[2].startswith("IDX_LINK") and c[0] >= 0]
        good = [c for c in cands if not c[2].startswith("IDX_LINK") and c[0] >= 7][:4]
        row.update(Pages_Crawled=pages, PDF_Links=len(pdfs), Links_Seen=links, WordPress=int(wp),
                   IDX_Links=";".join(c[1] for c in idx[:4]),
                   Blocked_Hosts=";".join(sorted(walls)), Candidates=" | ".join(f"{c[0]}:{c[1]}" for c in good))
    files, ok = [], None
    for sc, u, t in good:
        if check:
            if probe_pdf(u):
                ok = u; break
            continue
        res = fetch_pdf(u, RAW / "web_ar" / code)
        if res is None:
            continue
        tmp, h, nbytes, r = res
        out = RAW / "web_ar" / code / f"AR{year}_{h[:12]}.pdf"
        tmp.replace(out)
        out.with_suffix(".meta.json").write_text(json.dumps({"url": u, "final_url": r.url, "anchor": t.replace(CTX, " || "),
            "content_disposition": r.headers.get("content-disposition", ""),
            "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "sha256": h,
            "bytes": nbytes}, indent=1))
        n, chk = check_pdf(out, year, names.get(code, ""))
        files.append({"Code": code, "Year": year, "File": str(out.relative_to(ROOT)), "URL": u,
                      "Anchor": t.replace(CTX, " || "), "Score": sc, "Pages": n, "Check": chk})
        ok = ok or u
        if chk == "VERIFIED":
            break
    if ok:
        row.update(Status="AVAILABLE_WEBSITE", URL=ok)
    elif idx:
        row["Status"] = "IDX_LINK_ONLY"
    elif walls:
        row["Status"] = "SITE_BLOCKS_SCRIPTS"  # bot challenge on the site or its IR host: download by hand
    elif pages and links < 5:
        row["Status"] = "JS_ONLY_SITE"  # page built by JavaScript, no links in the HTML: needs a browser
    else:
        row["Status"] = "NOT_FOUND" if pages else "SITE_ERROR"
    return [row], files


def main():
    args = sys.argv[1:]
    check = "--check" in args
    opt = lambda k, d: args[args.index(k) + 1] if k in args else d
    global MAX_PAGES, GUESS
    workers, year = int(opt("--workers", 6)), int(opt("--year", 2025))
    MAX_PAGES, GUESS = int(opt("--max-pages", MAX_PAGES)), "--guess" in args
    if "--known" in args:  # download mode: reuse the Candidates column of data/ar_availability.csv
        for r in csv.DictReader((ROOT / "data" / "ar_availability.csv").open(encoding="utf-8")):
            cs = [c.split(":", 1) for c in (r.get("Candidates") or "").split(" | ") if ":" in c]
            if r["Status"] == "AVAILABLE_WEBSITE" and cs:
                KNOWN[r["Code"]] = [(int(sc), u, "") for sc, u in cs]
    rest = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] not in ("--workers", "--year", "--sites", "--out", "--max-pages"))]
    univ = [u for u in csv.DictReader((ROOT / "data" / "universe.csv").open(encoding="utf-8"))
            if u["Security_Kind"] == "COMPANY" and u["Exchange"] == "IJ"]
    if rest == ["all"]:
        codes = [u["Code"] for u in univ if u["In_Scope"] != "0"]
    elif rest and rest[0].endswith(".csv"):
        codes = [r["Code"] for r in csv.DictReader(open(rest[0], encoding="utf-8"))]
    else:
        codes = rest
    sites_csv = Path(opt("--sites", ROOT / "data" / "websites.csv"))
    sites = {r["Code"]: r for r in csv.DictReader(sites_csv.open(encoding="utf-8"))}
    names = {u["Code"]: u["Short_Name"] for u in univ}
    found, files = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process, c, (sites, names), check, year): c for c in codes}
        for i, f in enumerate(as_completed(futs)):
            try:
                a, b = f.result()
            except Exception as e:  # keep going; record the failure
                a, b = [{"Code": futs[f], "Year": year, "Status": f"SCRIPT_ERROR {type(e).__name__}"}], []
            found += a; files += b
            if (i + 1) % 50 == 0:
                print(f"companies {i + 1}/{len(codes)}", flush=True)
    print("this run:", Counter(r["Status"] for r in found).most_common())
    outs = [("ar_availability.csv", found)] if check else [("web_ar_found.csv", found), ("web_ar_files.csv", files)]
    for name, rows in outs:
        path = Path(opt("--out", ROOT / "data")) / name
        if rest != ["all"] and path.exists():  # a run on part of the list keeps the other companies' rows
            run = set(codes)
            rows = [r for r in csv.DictReader(path.open(encoding="utf-8")) if r["Code"] not in run] + rows
        rows.sort(key=lambda r: r["Code"])
        if rows:
            keys = list(dict.fromkeys(k for r in rows for k in r))
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
        if name != "web_ar_files.csv":
            print(name, "all companies:", Counter(r["Status"] for r in rows).most_common())


if __name__ == "__main__":
    main()
