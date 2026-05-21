"""
汗青 HanQing — 資料收集主程式
執行方式：python main.py
"""
import sys
from loguru import logger

from collectors.legislators import fetch_legislators
from collectors.mayors import fetch_mayors
from processors.deduplicator import deduplicate
from processors.normalizer import normalize_politician
from db.supabase_client import upsert_politicians

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}", colorize=True)
logger.add("logs/collector_{time:YYYY-MM-DD}.log", rotation="1 day", retention="7 days", encoding="utf-8")


def run():
    logger.info("=" * 50)
    logger.info("汗青 資料收集開始")
    logger.info("=" * 50)

    all_politicians = []

    # 1. 立法委員
    logger.info("[1/3] 收集立法委員資料")
    legislators = fetch_legislators()
    all_politicians.extend(legislators)
    logger.success(f"立委：{len(legislators)} 筆")

    # 2. 縣市長
    logger.info("[2/3] 收集縣市長資料")
    mayors = fetch_mayors()
    all_politicians.extend(mayors)
    logger.success(f"縣市長：{len(mayors)} 筆")

    # 標準化 + 去重
    all_politicians = [normalize_politician(p) for p in all_politicians]
    all_politicians = deduplicate(all_politicians)

    # 3. 寫入資料庫
    logger.info(f"[3/3] 寫入 Supabase（共 {len(all_politicians)} 筆）")
    result = upsert_politicians(all_politicians)

    logger.info("=" * 50)
    logger.success(f"完成｜新增 {result['success']} 筆，跳過 {result['skipped']} 筆，失敗 {result['failed']} 筆")
    logger.info("=" * 50)


if __name__ == "__main__":
    run()
