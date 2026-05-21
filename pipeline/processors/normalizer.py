"""資料標準化"""
from config import PARTY_MAP


KNOWN_CODES = {"DPP", "KMT", "TPP", "TSP", "NPP", "IND", "NPSU", "OTHER"}

def normalize_party(raw: str) -> str:
    raw = (raw or "").strip()
    if raw in KNOWN_CODES:
        return raw
    for key, val in PARTY_MAP.items():
        if key in raw:
            return val
    return "OTHER"


def normalize_politician(data: dict) -> dict:
    data["party"] = normalize_party(data.get("party", ""))
    data["name"] = (data.get("name") or "").strip()
    data["role"] = (data.get("role") or "").strip()
    data["region"] = (data.get("region") or "").strip() or None
    return data
