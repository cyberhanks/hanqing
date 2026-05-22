"""
財產申報自動收集
來源：監察院財產申報查詢系統
"""
import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

ASSET_BASE = "https://pa.cy.gov.tw"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_assets_for_politician(name: str) -> list[dict]:
    """取得財產申報歷年資料"""
    logger.info(f"收集財產申報：{name}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(
            f"{ASSET_BASE}/api/declaration/search",
            params={"name": name},
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        records = []
        prev_net = None
        for record in data.get("data", []):
            total_assets = record.get("totalAssets", 0) or 0
            total_debts  = record.get("totalDebts", 0) or 0
            net_assets   = total_assets - total_debts
            year         = record.get("year", 0)
            records.append({
                "year":            year,
                "total_assets":    total_assets,
                "total_debts":     total_debts,
                "net_assets":      net_assets,
                "change_from_prev": (net_assets - prev_net) if prev_net is not None else None,
                "source_url":      f"{ASSET_BASE}/declaration/{record.get('id', '')}",
            })
            prev_net = net_assets
        logger.success(f"收集到 {len(records)} 筆財產申報：{name}")
        return records
    except Exception as e:
        logger.warning(f"財產申報 API 失敗：{name} — {e}")
        return []
