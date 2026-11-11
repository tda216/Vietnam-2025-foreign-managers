"""Nationality as written in a source (accent-folded, lower case) -> English country name (1:1 translation only).

Shared by all countries: English names and demonyms plus Vietnamese country names (the Vietnam run). Each country's
config.py adds its own local-language names (e.g. thailand/pipeline/config.py adds Thai) and exposes the merged dict as
config.NATIONALITY_EN, which is what QA checks against. Add a missing country here (EN) or in the country config (local
language) – never write a free-text value into the records.
"""
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
    "australian": "Australia", "canada": "Canada", "canadian": "Canada",
    "colombia": "Colombia", "colombian": "Colombia",
    "ha lan": "Netherlands",
    "netherlands": "Netherlands", "dutch": "Netherlands", "bi": "Belgium", "belgium": "Belgium", "thuy si": "Switzerland",
    "switzerland": "Switzerland", "swiss": "Switzerland", "thuy dien": "Sweden", "sweden": "Sweden", "swedish": "Sweden",
    "na uy": "Norway", "norway": "Norway", "dan mach": "Denmark", "denmark": "Denmark", "phan lan": "Finland",
    "finland": "Finland", "y": "Italy", "italia": "Italy", "italy": "Italy", "italian": "Italy", "tay ban nha": "Spain",
    "spain": "Spain", "nga": "Russia", "russia": "Russia", "russian": "Russia", "new zealand": "New Zealand",
    "ireland": "Ireland", "irish": "Ireland", "israel": "Israel",
}
