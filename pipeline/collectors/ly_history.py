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
TERMS = list(range(5, 11))   # 第 5~10 屆

SPEECH_DATASET   = 4
INTERP_DATASET   = 6

# 每次 API 最多回 1000 筆
PAGE_SIZE = 1000


def _fetch_dataset(dataset_id: int, term: int, page: int = 1) -> list[dict]:
    try:
        params = {
            "id": dataset_id,
            "selectTerm": term,
            "page": page,
            "limit": PAGE_SIZE,
        }
        r = requests.get(LY_API, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("jsonList", []) or []
    except Exception as e:
        logger.warning(f"LY API 失敗 id={dataset_id} term={term}: {e}")
        return []


def _get_politician_map() -> dict[str, str]:
    """名字 -> id"""
    res = supabase.from_("politicians").select("id, name").execute()
    return {p["name"]: p["id"] for p in (res.data or [])}


def collect_speeches(terms: list[int] = TERMS):
    """收集委員發言，存入 statements 表"""
    pol_map = _get_politician_map()
    total_inserted = 0

    for term in terms:
        logger.info(f"收集第 {term} 屆發言...")
        page = 1
        while True:
            rows = _fetch_dataset(SPEECH_DATASET, term, page)
            if not rows:
                break

            records = []
            for r in rows:
                name = r.get("name") or r.get("委員姓名", "")
                pid = pol_map.get(name)
                if not pid:
                    continue

                content = (
                    r.get("content") or r.get("發言內容") or
                    r.get("meetingContent") or r.get("meetingDateDesc") or ""
                )
                if len(content) < 10:
                    continue

                records.append({
                    "politician_id":   pid,
                    "content":         content[:2000],
                    "statement_type":  "speech",
                    "statement_date":  r.get("meetingDate") or r.get("date"),
                    "source_name":     "立法院公報",
                    "source_url":      r.get("pdfUrl") or r.get("url"),
                    "term":            term,
                    "session":         _safe_int(r.get("session") or r.get("屆別")),
                    "committee":       r.get("committee") or r.get("委員會"),
                })

            if records:
                # 批次 upsert（以 politician_id + content 前 100 字去重）
                res = supabase.from_("statements").upsert(
                    records, on_conflict="politician_id,statement_date,statement_type"
                ).execute()
                total_inserted += len(records)
                logger.info(f"  第 {term} 屆 p{page}: 新增 {len(records)} 筆發言")

            if len(rows) < PAGE_SIZE:
                break
            page += 1
            time.sleep(0.5)

    logger.success(f"發言收集完成，共 {total_inserted} 筆")
    return total_inserted


def collect_interpellations(terms: list[int] = TERMS):
    """收集質詢事項，存入 statements 表"""
    pol_map = _get_politician_map()
    total_inserted = 0

    for term in terms:
        logger.info(f"收集第 {term} 屆質詢...")
        page = 1
        while True:
            rows = _fetch_dataset(INTERP_DATASET, term, page)
            if not rows:
                break

            records = []
            for r in rows:
                name = r.get("name") or r.get("委員姓名", "")
                pid = pol_map.get(name)
                if not pid:
                    continue

                content = (
                    r.get("content") or r.get("質詢內容") or
                    r.get("interpellation") or r.get("subject") or ""
                )
                if len(content) < 5:
                    continue

                records.append({
                    "politician_id":   pid,
                    "content":         content[:2000],
                    "statement_type":  "interpellation",
                    "statement_date":  r.get("date") or r.get("質詢日期"),
                    "source_name":     "立法院質詢紀錄",
                    "source_url":      r.get("pdfUrl") or r.get("url"),
                    "term":            term,
                    "session":         _safe_int(r.get("session")),
                    "committee":       r.get("committee"),
                    "topics":          _extract_topics(content),
                })

            if records:
                res = supabase.from_("statements").upsert(
                    records, on_conflict="politician_id,statement_date,statement_type"
                ).execute()
                total_inserted += len(records)
                logger.info(f"  第 {term} 屆 p{page}: 新增 {len(records)} 筆質詢")

            if len(rows) < PAGE_SIZE:
                break
            page += 1
            time.sleep(0.5)

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
