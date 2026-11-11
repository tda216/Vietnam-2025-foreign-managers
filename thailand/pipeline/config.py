"""Paths and study-wide constants for the Thailand 2025 foreign-managers pipeline.

Same names as vietnam/pipeline/config.py, so the shared helpers in shared/ (common.py, xlsx_tables.py, archives.py)
bind to this module: every Thailand script puts thailand/pipeline first and shared/ second on sys.path.
"""
from pathlib import Path

from nationality import NATIONALITY_EN as _SHARED_NATIONALITY_EN

ROOT = Path(__file__).resolve().parent.parent          # thailand/
REPO = ROOT.parent
RAW = ROOT / "raw"
RAW_WEB_CACHE = RAW / "web" / "cache"
RAW_OWNERSHIP = RAW / "ownership"
RAW_DOCS = RAW / "docs"
DATA = ROOT / "data"
OUTPUT = ROOT / "output"

BLOOMBERG_FILE = ROOT / "Bloomberg-Thailan2025_9666.xlsx"
BOARDEX_ROLES_FILE = ROOT / "Broad-20thailan-202025_9300.xlsx"
BOARDEX_PEOPLE_FILE = ROOT / "Thai-20lan-20national-202025_8540.xlsx"

COUNTRY = "TH"
YEAR = 2025
FO_AS_OF = "2025-12-31"

# Ownership rule shared by all 5 countries: LOCAL <= 50 < FOREIGN_MAJORITY; missing -> REVIEW.
FO_THRESHOLD = 50.0
FO_BORDERLINE_UPPER = 55.0

DEEP_TOP_N_MCAP = 200
DEEP_FO_MIN = 10.0
DEEP_FOREIGN_HOLDER_MIN = 5.0

# Honest client name (no browser imitation, no personal contact details); stop on 403/429 instead of working around it.
USER_AGENT = "corp-data-research/1.0"
MIN_SECONDS_BETWEEN_REQUESTS = 3.0

SET_FACTSHEET = "https://www.set.or.th/{lang}/market/product/stock/quote/{ticker}/factsheet"
# One Report files are linked from the SET factsheet (weblink.set.or.th, robots: Disallow /); they are downloaded from
# the SEC's public disclosure system instead, whose robots.txt only disallows *.aspx pages.
SEC_DOWNLOAD = "https://market.sec.or.th/public/idisc/Download?FILEID=dat/{path}"


# Nationality as written in the source (lower case) -> English country name; the shared table (shared/nationality.py)
# plus BoardEx demonyms and Thai-language country names.
NATIONALITY_EN = dict(_SHARED_NATIONALITY_EN) | {
    "chinese (taiwan)": "Taiwan", "belgian": "Belgium", "lebanese": "Lebanon", "lebanon": "Lebanon", "tanzanian": "Tanzania",
    "tanzania": "Tanzania", "norwegian": "Norway", "danish": "Denmark", "spanish": "Spain", "portuguese": "Portugal",
    "portugal": "Portugal", "new zealander": "New Zealand", "sri lankan": "Sri Lanka", "bangladeshi": "Bangladesh",
    "bangladesh": "Bangladesh", "pakistani": "Pakistan", "pakistan": "Pakistan", "vietnamese": "Vietnam",
    "burmese": "Myanmar", "cambodian": "Cambodia", "laotian": "Laos", "hong konger": "Hong Kong", "hongkonger": "Hong Kong",
    "south african": "South Africa", "south africa": "South Africa", "mexican": "Mexico", "mexico": "Mexico",
    "brazilian": "Brazil", "brazil": "Brazil", "israeli": "Israel", "emirati": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates", "uae": "United Arab Emirates", "qatari": "Qatar", "qatar": "Qatar",
    "saudi": "Saudi Arabia", "saudi arabia": "Saudi Arabia", "finnish": "Finland", "irish": "Ireland", "greek": "Greece",
    "greece": "Greece", "czech": "Czech Republic", "hungarian": "Hungary", "hungary": "Hungary", "luxembourg": "Luxembourg",
    "nepalese": "Nepal", "nepali": "Nepal", "nepal": "Nepal", "iranian": "Iran", "iran": "Iran",
    "เนปาล": "Nepal", "อิหร่าน": "Iran", "ลาว": "Laos", "เมียนมา": "Myanmar", "พม่า": "Myanmar",
    "ไทย": "Thailand", "ญี่ปุ่น": "Japan", "จีน": "China", "ไต้หวัน": "Taiwan", "เกาหลีใต้": "South Korea", "เกาหลี": "South Korea",
    "สิงคโปร์": "Singapore", "มาเลเซีย": "Malaysia", "อินเดีย": "India", "ฮ่องกง": "Hong Kong", "อเมริกัน": "United States",
    "สหรัฐอเมริกา": "United States", "อังกฤษ": "United Kingdom", "สหราชอาณาจักร": "United Kingdom", "ฝรั่งเศส": "France",
    "เยอรมัน": "Germany", "เยอรมนี": "Germany", "ออสเตรเลีย": "Australia", "เนเธอร์แลนด์": "Netherlands", "สวิส": "Switzerland",
    "สวิตเซอร์แลนด์": "Switzerland", "ฟิลิปปินส์": "Philippines", "อินโดนีเซีย": "Indonesia", "เวียดนาม": "Vietnam",
    "แคนาดา": "Canada", "เดนมาร์ก": "Denmark", "นอร์เวย์": "Norway", "สวีเดน": "Sweden", "เบลเยียม": "Belgium", "อิตาลี": "Italy",
}
