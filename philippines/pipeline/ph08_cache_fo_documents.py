"""Cache public ownership PDFs as research evidence; do not rebuild any workbook.

Usage: python -I philippines/pipeline/ph08_cache_fo_documents.py <source_manifest.json>
The manifest's sources list provides Document_ID, Symbol and Source_URL. Text and
review images are reading aids; observations require separate manual review.
"""
import hashlib
import json
import re
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore", message="urllib3 v2 only supports.*")
import requests
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "philippines"
RAW = PH / "raw" / "ownership_public"
REVIEW = PH / "data" / "ownership_source_review"


def main():
    manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    REVIEW.mkdir(parents=True, exist_ok=True)
    results = []
    for source in manifest["sources"]:
        key = source["Document_ID"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise ValueError(f"Invalid document ID {key}")
        folder = RAW / source["Symbol"]
        folder.mkdir(parents=True, exist_ok=True)
        pdf, meta_path = folder / (key + ".pdf"), folder / (key + ".meta.json")
        try:
            if not (pdf.exists() and meta_path.exists()):
                response = requests.get(source["Source_URL"], timeout=60,
                                        headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                if not response.content.lstrip().startswith(b"%PDF-"):
                    raise ValueError("Response is not a PDF")
                temporary = pdf.with_suffix(".part")
                temporary.write_bytes(response.content)
                temporary.replace(pdf)
                metadata = {**source, "Final_URL": response.url,
                            "Accessed_UTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "SHA256": hashlib.sha256(response.content).hexdigest(),
                            "Bytes": len(response.content), "Content_Type": response.headers.get("Content-Type", "")}
                meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                time.sleep(0.8)
            else:
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            pages = []
            with pymupdf.open(pdf) as document:
                for number, page in enumerate(document, 1):
                    text = page.get_text()
                    pages.append({"Page": number, "Text": text})
                    if number in source.get("Review_Pages", []):
                        page.get_pixmap(dpi=110).save(REVIEW / f"{key}_p{number}.png")
            (REVIEW / (key + ".json")).write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
            result = {"Document_ID": key, "Symbol": source["Symbol"], "Status": "CACHED",
                      "Local_File": str(pdf.relative_to(ROOT)), "Pages": len(pages), "SHA256": metadata["SHA256"]}
            print(json.dumps(result), flush=True)
        except Exception as error:
            result = {"Document_ID": key, "Symbol": source["Symbol"], "Status": "ERROR", "Error": str(error)}
            print(json.dumps(result), flush=True)
        results.append(result)
    (REVIEW / "download_status.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
