# Record found after replacing OMRE's website AR 2024 by the IDX AR 2025 (QA 10 Nov 2026). Page image viewed.
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_batch_helpers import *
add("OMRE", 2, 22, "Chiu Man Sing", "Komisaris", B, "Singapore",
    quote="Warga Negara Singapura, lahir pada 25 September 1952. Menjabat sebagai Komisaris Perusahaan sejak 19 Juni 2025",
    raw="Warga Negara Singapura", ap="2025-06-19", note=IMG + "; spread page with two profiles, the Singapore text block belongs to Chiu Man Sing (right-hand profile)")
save("indonesia/data/manual/batches/id_batch_20261110_17.json")
