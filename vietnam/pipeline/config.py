"""Paths and study-wide constants for the Vietnam 2025 foreign-managers pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
RAW_WEB_CACHE = RAW / "web" / "cache"
RAW_OWNERSHIP = RAW / "ownership"
RAW_DOCS = RAW / "docs"
DATA = ROOT / "data"
OUTPUT = ROOT / "output"

BLOOMBERG_FILE = ROOT / "Bloomberg-Vietnam2025_8520.xlsx"
LISTING_FILE = RAW / "web" / "listing" / "vci_symbols_getAll.decoded.json"
LISTING_SOURCE = "Vietcap (VCI) public symbol list: https://trading.vietcap.com.vn/api/price/symbols/getAll"

COUNTRY = "VN"
YEAR = 2025
FO_AS_OF = "2025-12-31"

# Ownership rule shared by all 5 countries: LOCAL <= 50 < FOREIGN_MAJORITY; missing -> REVIEW.
FO_THRESHOLD = 50.0
# FOREIGN_MAJORITY firms at or below this level are still searched for managers,
# so a reclassification from the annual report does not force a second pass.
FO_BORDERLINE_UPPER = 55.0

# C3 deep-search tier (agreed with the user).
DEEP_TOP_N_MCAP = 200
DEEP_FO_MIN = 10.0
DEEP_FOREIGN_HOLDER_MIN = 5.0

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
MIN_SECONDS_BETWEEN_REQUESTS = 1.0

# Accepted nationality values (QA rejects anything else): the shared table in shared/nationality.py.
from nationality import NATIONALITY_EN  # noqa: F401,E402
