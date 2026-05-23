"""
立委出席率 / 質詢次數 collector
資料來源：data.ly.gov.tw Open Data API
  Dataset 15 = 委員出席
  Dataset  6 = 質詢事項（用 count 算質詢次數）

直接更新 politicians 表的量化欄位
"""
import requests
import urllib3
from collections import defaultdict
from config import supabase
from loguru import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LY_API    = "https://data.ly.gov.tw/odw/openDatasetJson.action"
LY_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Encoding": "identity",
    "Accept":          "application/json",
}
PAGE_SIZE = 1000


def _fetch_all(dataset_id: int, max_pages: int = 200) -> list[dict]:
    results = []
    offset  = 0
    for _ in range(max_pages):
        try:
            r = requests.get(LY_API, params={
                "id": dataset_id, "filterParam": "",
                "offset": offset, "limit": PAGE_SIZE,
            }, headers=LY_HEADERS, timeout=60, verify=False)
            r.raise_for_status()
            items = r.json().get("jsonList", []) or []
        except Exception as e:
            logger.warning(f"LY API id={dataset_id} offset={offset}: {e}")
            break

        results.extend(items)
        if len(items) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return results


def collect_attendance():
    """計算第 10 屆每位立委出席率並更新 DB"""
    politicians = {p["name"]: p["id"]
                   for p in (supabase.from_("politicians").select("id,name").execute().data or [])}

    logger.info("抓取出席紀錄 (dataset 15)...")
    rows = _fetch_all(dataset_id=15)
    logger.info(f"  取得 {len(rows)} 筆原始記錄")

    # 統計每人：出席 / 總次數
    present  = defaultdict(int)
    total    = defaultdict(int)

    for r in rows:
        name   = r.get("name") or r.get("委員姓名", "")
        result = r.get("result") or r.get("出席狀況", "")
        if not name:
            continue
        total[name] += 1
        if result in ("出席", "present", "1", "Y"):
            present[name] += 1

    updated = 0
    for name, pid in politicians.items():
        t = total.get(name, 0)
        if t == 0:
            continue
        rate = round(present[name] / t * 100, 2)
        supabase.from_("politicians").update({
            "attendance_rate": rate,
        }).eq("id", pid).execute()
        updated += 1
        logger.info(f"  {name}: 出席率 {rate}% ({present[name]}/{t})")

    logger.success(f"出席率更新完成，共 {updated} 人")
    return updated


def collect_interpellation_counts():
    """統計第 10 屆每位立委質詢次數"""
    politicians = {p["name"]: p["id"]
                   for p in (supabase.from_("politicians").select("id,name").execute().data or [])}

    logger.info("抓取質詢紀錄 (dataset 6)...")
    rows = _fetch_all(dataset_id=6)
    logger.info(f"  取得 {len(rows)} 筆原始記錄")

    counts = defaultdict(int)
    for r in rows:
        name = r.get("name") or r.get("委員姓名", "")
        if name:
            counts[name] += 1

    updated = 0
    for name, pid in politicians.items():
        c = counts.get(name, 0)
        if c == 0:
            continue
        supabase.from_("politicians").update({
            "interpellation_count": c,
        }).eq("id", pid).execute()
        updated += 1
        logger.info(f"  {name}: {c} 次質詢")

    logger.success(f"質詢次數更新完成，共 {updated} 人")
    return updated
