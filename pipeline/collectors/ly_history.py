"""
立法院歷史發言 / 質詢 collector
資料來源：data.ly.gov.tw Open Data API
覆蓋屆期：第 5 屆（1999）~ 第 10 屆（現任）

Dataset IDs:
  4  = 委員發言 (speeches in full sessions)
  6  = 質詢事項 (interpellations)
"""
import time
import requests
from config import supabase
from loguru import logger

LY_API = "https://data.ly.gov.tw/odw/openDatasetJson.action"
# 只抓最新一屆（第 10 屆）
# 歷史屆期（5-9）資料量龐大（40萬筆以上）需逐頁掃描，效益低
# 待日後 LY 提供分屆 API endpoint 再補
TERMS = [10]

SPEECH_DATASET   = 4
INTERP_DATASET   = 6

# 每次 API 最多回 1000 筆
PAGE_SIZE = 1000


import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Encoding": "identity",
    "Accept": "application/json",
}


def _fetch_dataset(dataset_id: int, term: int, offset: int = 0) -> list[dict]:
    """抓取單頁資料，透過 term 欄位過濾屆期"""
    try:
        params = {
            "id":          dataset_id,
            "filterParam": "",
            "offset":      offset,
            "limit":       PAGE_SIZE,
        }
        r = requests.get(LY_API, params=params, headers=LY_HEADERS, timeout=30, verify=False)
        r.raise_for_status()
        all_items = r.json().get("jsonList", []) or []
        # 過濾指定屆期
        return [x for x in all_items if str(x.get("term", "")).strip() == str(term)]
    except Exception as e:
        logger.warning(f"LY API 失敗 id={dataset_id} offset={offset}: {e}")
        return []


def _fetch_all_for_term(dataset_id: int, term: int,
                         max_pages: int = 50) -> list[dict]:
    """
    分頁抓取，過濾指定屆期。
    max_pages: 最多抓幾頁（避免抓超久）
    第 10 屆資料約在最前面，通常 10 頁以內就找完
    """
    results = []
    offset = 0
    consecutive_empty = 0   # 連續幾頁完全沒有該屆資料就停

    for _ in range(max_pages):
        params = {
            "id": dataset_id, "filterParam": "",
            "offset": offset, "limit": PAGE_SIZE,
        }
        try:
            r = requests.get(LY_API, params=params, headers=LY_HEADERS,
                             timeout=60, verify=False)
            r.raise_for_status()
            items = r.json().get("jsonList", []) or []
        except Exception as e:
            logger.warning(f"LY API 失敗 id={dataset_id} offset={offset}: {e}")
            # 自動重試一次
            time.sleep(5)
            try:
                r = requests.get(LY_API, params=params, headers=LY_HEADERS,
                                 timeout=60, verify=False)
                items = r.json().get("jsonList", []) or []
            except Exception:
                break

        matched = [x for x in items if str(x.get("term", "")).strip() == str(term)]
        results.extend(matched)

        if not matched:
            consecutive_empty += 1
            if consecutive_empty >= 3:
                logger.debug(f"  連續 3 頁無第 {term} 屆資料，停止")
                break
        else:
            consecutive_empty = 0

        if len(items) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(0.5)

    return results


def _get_politician_map() -> dict[str, str]:
    """名字 -> id"""
    res = supabase.from_("politicians").select("id, name").execute()
    return {p["name"]: p["id"] for p in (res.data or [])}


def _rows_to_statements(rows: list[dict], term: int, stmt_type: str,
                         pol_map: dict, source_name: str) -> list[dict]:
    records = []
    for r in rows:
        # 嘗試多個欄位名稱
        name = (r.get("name") or r.get("委員姓名") or
                r.get("proposer") or r.get("relDocNum", "")[:4] or "")
        pid = pol_map.get(name.strip())
        if not pid:
            continue

        content = (r.get("content") or r.get("發言內容") or
                   r.get("billName") or r.get("relDocNum") or
                   r.get("meetingContent") or "")
        if len(content) < 5:
            continue

        pdf_url = r.get("pdfUrl") or r.get("docUrl") or r.get("url")
        records.append({
            "politician_id":  pid,
            "content":        content[:2000],
            "statement_type": stmt_type,
            "statement_date": r.get("meetingDate") or r.get("date"),
            "source_name":    source_name,
            "source_url":     pdf_url,
            "term":           term,
            "session":        _safe_int(r.get("sessionPeriod") or r.get("session")),
            "committee":      r.get("committee"),
            "topics":         _extract_topics(content),
        })
    return records


def collect_speeches(terms: list[int] = TERMS):
    """收集委員發言，存入 statements 表"""
    pol_map = _get_politician_map()
    total_inserted = 0

    for term in terms:
        logger.info(f"收集第 {term} 屆發言...")
        rows = _fetch_all_for_term(SPEECH_DATASET, term)
        if not rows:
            logger.info(f"  第 {term} 屆無資料")
            continue

        records = _rows_to_statements(rows, term, "speech", pol_map, "立法院公報")
        if records:
            supabase.from_("statements").upsert(
                records, on_conflict="politician_id,statement_date,statement_type"
            ).execute()
            total_inserted += len(records)
            logger.info(f"  第 {term} 屆: {len(rows)} 筆原始 → {len(records)} 筆入庫")

    logger.success(f"發言收集完成，共 {total_inserted} 筆")
    return total_inserted


def collect_interpellations(terms: list[int] = TERMS):
    """收集質詢事項，存入 statements 表"""
    pol_map = _get_politician_map()
    total_inserted = 0

    for term in terms:
        logger.info(f"收集第 {term} 屆質詢...")
        rows = _fetch_all_for_term(INTERP_DATASET, term)
        if not rows:
            logger.info(f"  第 {term} 屆無資料")
            continue

        records = _rows_to_statements(rows, term, "interpellation", pol_map, "立法院質詢紀錄")
        if records:
            supabase.from_("statements").upsert(
                records, on_conflict="politician_id,statement_date,statement_type"
            ).execute()
            total_inserted += len(records)
            logger.info(f"  第 {term} 屆: {len(rows)} 筆原始 → {len(records)} 筆入庫")

    logger.success(f"質詢收集完成，共 {total_inserted} 筆")
    return total_inserted


def _safe_int(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


TOPIC_KEYWORDS = {
    "經濟": ["經濟", "產業", "GDP", "投資", "貿易"],
    "教育": ["教育", "學校", "學生", "大學", "師資"],
    "環境": ["環境", "污染", "空氣", "水質", "碳"],
    "醫療": ["醫療", "健保", "醫院", "衛生", "疫情"],
    "國防": ["國防", "軍事", "軍備", "軍隊", "兵役"],
    "司法": ["司法", "法院", "檢察", "判決", "起訴"],
    "社福": ["社會福利", "勞工", "老人", "弱勢", "津貼"],
    "交通": ["交通", "道路", "鐵路", "捷運", "航空"],
    "兩岸": ["兩岸", "中國", "統一", "台獨", "九二共識"],
}


def _extract_topics(text: str) -> list[str]:
    found = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(topic)
    return found or None
