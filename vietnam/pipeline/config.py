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

# Nationality as written in the source (accent-folded, lower case) -> English country name (1:1 translation only).
NATIONALITY_EN = {
    "viet nam": "Vietnam", "vietnam": "Vietnam", "vietnamese": "Vietnam",
    "nhat ban": "Japan", "japan": "Japan", "japanese": "Japan",
    "han quoc": "South Korea", "korea": "South Korea", "korean": "South Korea", "south korea": "South Korea",
    "trung quoc": "China", "china": "China", "chinese": "China",
    "dai loan": "Taiwan", "taiwan": "Taiwan", "taiwanese": "Taiwan", "trung hoa dan quoc": "Taiwan",
    "hong kong": "Hong Kong", "singapore": "Singapore", "singaporean": "Singapore", "xinh-ga-po": "Singapore",
    "sri lanka": "Sri Lanka", "sri lankan": "Sri Lanka", "kazakhstan": "Kazakhstan", "austria": "Austria", "austrian": "Austria", "bulgaria": "Bulgaria", "bulgarian": "Bulgaria", "poland": "Poland", "polish": "Poland", "turkey": "Turkey", "turkish": "Turkey", "thổ nhĩ kỳ": "Turkey", "ca-dắc-xtan": "Kazakhstan",
    "thai lan": "Thailand", "thailand": "Thailand", "thai": "Thailand", "malaysia": "Malaysia", "malaysian": "Malaysia",
    "indonesia": "Indonesia", "indonesian": "Indonesia", "philippines": "Philippines", "filipino": "Philippines",
    "an do": "India", "india": "India", "indian": "India", "lao": "Laos", "laos": "Laos", "campuchia": "Cambodia",
    "cambodia": "Cambodia", "myanmar": "Myanmar",
    "hoa ky": "United States", "my": "United States", "usa": "United States", "united states": "United States",
    "american": "United States", "anh": "United Kingdom", "vuong quoc anh": "United Kingdom", "british": "United Kingdom",
    "united kingdom": "United Kingdom", "uk": "United Kingdom", "phap": "France", "france": "France", "french": "France",
    "duc": "Germany", "germany": "Germany", "german": "Germany", "uc": "Australia", "australia": "Australia",
    "australian": "Australia", "canada": "Canada", "canadian": "Canada", "ha lan": "Netherlands",
    "netherlands": "Netherlands", "dutch": "Netherlands", "bi": "Belgium", "belgium": "Belgium", "thuy si": "Switzerland",
    "switzerland": "Switzerland", "swiss": "Switzerland", "thuy dien": "Sweden", "sweden": "Sweden", "swedish": "Sweden",
    "na uy": "Norway", "norway": "Norway", "dan mach": "Denmark", "denmark": "Denmark", "phan lan": "Finland",
    "finland": "Finland", "y": "Italy", "italia": "Italy", "italy": "Italy", "italian": "Italy", "tay ban nha": "Spain",
    "spain": "Spain", "nga": "Russia", "russia": "Russia", "russian": "Russia", "new zealand": "New Zealand",
    "ireland": "Ireland", "irish": "Ireland", "israel": "Israel",
}
