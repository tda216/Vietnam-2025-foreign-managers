# Records for firms that became LOCAL on 10 Nov 2026 (hand-read / BAE FO) or whose truncated IDX report was repaired.
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_batch_helpers import *
add("CMRY", 1, 59, "Bharat Shah Joshi", "Direktur / Chief Financial Officer", E, "Malaysia")
add("DEPO", 2, 63, "Piphop Vasanaarchasakul", "Komisaris", B, "Thailand", note=IMG)
add("DEPO", 2, 79, "Pathama Sirikul", "Direktur Omni Channel", E, "Thailand", note=IMG)
add("ECII", 1, 64, "Ku Siew Kuan", "Komisaris Independen", B, "Singapore")
add("FILM", 1, 75, "William Hyongmin Kim", "Direktur", E, "United States",
    quote="Merupakan Warga Negara Amerika berusia 34 tahun dan berdomisili di Korea Selatan. He is an American Citizen aged 34 years and domiciled in South Korea.",
    raw="Warga Negara Amerika", ap="2025-08-14", note=IMG + "; appointed by the EGMS, Notarial Deed No. 27 dated 14 August 2025")
add("KRYA", 1, 98, "An Shaohong", "Komisaris Utama", B, "China",
    quote="Warga Republik Rakyat Tiongkok, 55 tahun A citizen of the People's Republic of China, 55 years old",
    raw="Warga Republik Rakyat Tiongkok", ap="2025-08-26", note=IMG + "; GMS resolution No. 98 dated 26 August 2025 (profile text: 11 August 2025)")
add("PALM", 2, 143, "Gavin Arnold Caudle", "Anggota Komite Investasi", O, "Australia", ap="2025-03-17", note=CI)
add("PMJS", 1, 62, "Eiichiro Hamazaki", "Wakil Direktur Utama", E, "Japan")
add("PMJS", 1, 66, "Shinya Oka", "Direktur", E, "Japan")
add("PMJS", 1, 69, "Masanori Goto", "Komisaris Independen", B, "Japan", ap="2025-03-20")
add("WOMF", 1, 95, "Thilagavathy Nadason", "Komisaris", B, "Malaysia", note=IMG)
save("indonesia/data/manual/batches/id_batch_20261110_14.json")
