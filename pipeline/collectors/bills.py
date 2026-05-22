"""
立法院法案提案 / 連署 collector
資料來源：data.ly.gov.tw Open Data API

Dataset IDs（推測，實際以 API 回傳欄位為準）:
  14 = 委員提案
  16 = 委員連署
"""
import time
import requests
from config import supabase
from loguru import logger

LY_API   = "https://data.ly.gov.tw/odw/openDatasetJson.action"
TERMS    = list(range(5, 11))
PAGE_SIZE = 1000

PROPOSE_DATASET = 14
COSIGN_DATASET  = 16


import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Encoding": "identity",
    "Accept": "application/json",
}


def _fetch_all_for_term(dataset_id: int, term: int) -> list[dict]:
    results = []
    offset = 0
    while True:
        try:
            r = requests.get(LY_API, params={
                "id": dataset_id, "filterParam": "",
                "offset": offset, "limit": PAGE_SIZE,
            }, headers=LY_HEADERS, timeout=30, verify=False)
            r.raise_for_status()
            items = r.json().get("jsonList", []) or []
        except Exception as e:
            logger.warning(f"LY API 失敗 id={dataset_id} offset={offset}: {e}")
            break

        matched = [x for x in items if str(x.get("term", "")).strip() == str(term)]
        results.extend(matched)

        if len(items) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(0.3)

    return results


def _get_politician_map() -> dict[str, str]:
    res = supabase.from_("politicians").select("id, name").execute()
    return {p["name"]: p["id"] for p in (res.data or [])}


def _upsert_bill(row: dict, term: int) -> str | None:
    """插入或取得 bill id"""
    bill_no = row.get("billNo") or row.get("案號") or row.get("billId")
    title   = row.get("title") or row.get("案由") or row.get("billName") or ""
    if not title:
        return None

    data = {
        "bill_no":    bill_no,
        "title":      title[:300],
        "bill_date":  row.get("billDate") or row.get("日期"),
        "term":       term,
        "session":    _safe_int(row.get("session")),
        "status":     _map_status(row.get("status") or row.get("狀態")),
        "source_url": row.get("url") or row.get("pdfUrl"),
    }

    res = supabase.from_("bills").upsert(
        data, on_conflict="bill_no,term"
    ).execute()

    if res.data:
        return res.data[0]["id"]

    # fallback: look up by bill_no + term
    existing = supabase.from_("bills")\
        .select("id").eq("bill_no", bill_no).eq("term", term)\
        .maybeSingle().execute()
    return existing.data["id"] if existing.data else None


def _process_bill_rows(rows: list[dict], term: int, pol_map: dict, role: str) -> int:
    total = 0
    for r in rows:
        bill_id = _upsert_bill(r, term)
        if not bill_id:
            continue
        name_field = "proposer" if role == "proposer" else "cosigner"
        names = _parse_names(
            r.get(name_field) or r.get("relDocNum", "")[:4] or r.get("name") or ""
        )
        for name in names:
            pid = pol_map.get(name)
            if not pid:
                continue
            supabase.from_("bill_politicians").upsert(
                {"bill_id": bill_id, "politician_id": pid, "role": role},
                on_conflict="bill_id,politician_id"
            ).execute()
            total += 1
    return total


def collect_proposals(terms: list[int] = TERMS):
    pol_map = _get_politician_map()
    total = 0
    for term in terms:
        logger.info(f"收集第 {term} 屆提案...")
        rows = _fetch_all_for_term(PROPOSE_DATASET, term)
        if rows:
            n = _process_bill_rows(rows, term, pol_map, "proposer")
            total += n
            logger.info(f"  第 {term} 屆: {len(rows)} 筆提案 → {n} 筆關聯")
    logger.success(f"提案收集完成，共 {total} 筆政治人物-法案關聯")
    return total


def collect_cosigners(terms: list[int] = TERMS):
    pol_map = _get_politician_map()
    total = 0
    for term in terms:
        logger.info(f"收集第 {term} 屆連署...")
        rows = _fetch_all_for_term(COSIGN_DATASET, term)
        if rows:
            n = _process_bill_rows(rows, term, pol_map, "cosigner")
            total += n
            logger.info(f"  第 {term} 屆: {len(rows)} 筆連署 → {n} 筆關聯")
    logger.success(f"連署收集完成，共 {total} 筆政治人物-法案關聯")
    return total


def _parse_names(raw: str) -> list[str]:
    if not raw:
        return []
    import re
    # 分隔符：逗號、頓號、空白、「、」
    parts = re.split(r"[,、，\s]+", raw.strip())
    return [p.strip() for p in parts if 1 < len(p.strip()) <= 6]


def _map_status(raw: str | None) -> str:
    if not raw:
        return "pending"
    raw = raw.lower()
    if "通過" in raw or "pass" in raw:
        return "passed"
    if "否決" in raw or "reject" in raw or "廢" in raw:
        return "rejected"
    return "pending"


def _safe_int(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
