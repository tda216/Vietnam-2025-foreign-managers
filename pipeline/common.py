"""Shared helpers: cached + throttled HTTP, CSV I/O, small text utilities."""
import csv
import hashlib
import json
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from config import MIN_SECONDS_BETWEEN_REQUESTS, RAW_WEB_CACHE, USER_AGENT

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "vi,en;q=0.8"})
_last_request_at: dict[str, float] = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def throttle(host: str) -> None:
    """Keep at least MIN_SECONDS_BETWEEN_REQUESTS between two requests to the same host."""
    wait = MIN_SECONDS_BETWEEN_REQUESTS - (time.time() - _last_request_at.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    _last_request_at[host] = time.time()


def download(url: str, dest: Path, *, timeout: int = 300, retries: int = 3) -> dict:
    """Stream a (large) file to dest once, with dest + '.meta.json' beside it; an existing file is kept.

    Returns meta (url, final_url, status, content_type, fetched_at, sha256, bytes).
    Raises requests.HTTPError for non-2xx responses.
    """
    meta_path = dest.with_name(dest.name + ".meta.json")
    if dest.exists() and meta_path.exists():
        return json.loads(meta_path.read_text())
    dest.parent.mkdir(parents=True, exist_ok=True)
    host = urlparse(url).netloc
    last_err = None
    for attempt in range(retries):
        throttle(host)
        tmp = dest.with_name(dest.name + ".part")
        try:
            with _session.get(url, timeout=timeout, stream=True) as r:
                r.raise_for_status()
                h = hashlib.sha256()
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        h.update(chunk)
                meta = {"url": url, "final_url": r.url, "status": r.status_code,
                        "content_type": r.headers.get("Content-Type", ""), "fetched_at": now_iso(),
                        "sha256": h.hexdigest(), "bytes": tmp.stat().st_size}
            tmp.replace(dest)
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
            return meta
        except requests.RequestException as e:
            last_err = e
            tmp.unlink(missing_ok=True)
            if isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code < 500:
                raise
            time.sleep(2 * (attempt + 1))
    raise last_err


def session() -> requests.Session:
    """The shared HTTP session (same User-Agent), for the few sources that need POST or cookies."""
    return _session


def _cache_paths(url: str) -> tuple[Path, Path]:
    host = urlparse(url).netloc or "local"
    key = hashlib.sha1(url.encode("utf-8")).hexdigest()
    d = RAW_WEB_CACHE / host
    return d / f"{key}.body", d / f"{key}.meta.json"


def fetch(url: str, *, refresh: bool = False, timeout: int = 60, retries: int = 3) -> tuple[bytes, dict]:
    """GET a URL once and keep the response on disk; later calls are served from the cache.

    Returns (body, meta). meta has url, status, fetched_at, sha256, content_type.
    Raises requests.HTTPError for non-2xx responses (those are not cached).
    """
    body_path, meta_path = _cache_paths(url)
    if not refresh and body_path.exists() and meta_path.exists():
        return body_path.read_bytes(), json.loads(meta_path.read_text())

    host = urlparse(url).netloc
    last_err = None
    for attempt in range(retries):
        throttle(host)
        try:
            r = _session.get(url, timeout=timeout)
            r.raise_for_status()
            break
        except requests.RequestException as e:
            last_err = e
            if isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code < 500:
                raise
            time.sleep(2 * (attempt + 1))
    else:
        raise last_err

    body = r.content
    meta = {
        "url": url,
        "final_url": r.url,
        "status": r.status_code,
        "content_type": r.headers.get("Content-Type", ""),
        "fetched_at": now_iso(),
        "sha256": sha256_bytes(body),
        "bytes": len(body),
    }
    body_path.parent.mkdir(parents=True, exist_ok=True)
    body_path.write_bytes(body)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    return body, meta


def fetch_text(url: str, **kw) -> tuple[str, dict]:
    body, meta = fetch(url, **kw)
    return body.decode("utf-8", errors="replace"), meta


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="raise")
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def strip_accents(s: str) -> str:
    """Lowercase ASCII fold, for matching only (never written back as data)."""
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
