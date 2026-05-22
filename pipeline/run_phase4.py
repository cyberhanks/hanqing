"""Phase 4：月報產生 + 黨派排名更新（每月1日執行）"""
import sys
from loguru import logger
from reporters.monthly_report import generate_monthly_report
from reporters.party_ranking import calculate_party_rankings
from db.supabase_client import get_client

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | {level} | {message}")


def run():
    logger.info("Phase 4 開始：月報產生")
    db = get_client()

    # 1. 更新各政治人物的統計快取
    logger.info("[1/3] 更新政治人物統計快取")
    politicians = db.table("politicians").select("id").execute().data or []
    for p in politicians:
        pid = p["id"]
        promises = db.table("promises").select("status").eq("politician_id", pid).execute().data or []
        total     = len(promises)
        fulfilled = sum(1 for x in promises if x["status"] == "fulfilled")
        broken    = sum(1 for x in promises if x["status"] == "broken")
        stalled   = sum(1 for x in promises if x["status"] == "stalled")
        fulfill_rate = round(fulfilled / total * 100, 2) if total else 0

        db.table("politicians").update({
            "total_promises":   total,
            "fulfilled_count":  fulfilled,
            "broken_count":     broken,
            "stalled_count":    stalled,
            "fulfill_rate":     fulfill_rate,
        }).eq("id", pid).execute()

    logger.success(f"更新 {len(politicians)} 位政治人物統計")

    # 2. 黨派排名
    logger.info("[2/3] 計算黨派排名")
    rankings = calculate_party_rankings()
    for r in rankings:
        logger.info(f"  {r['party']:6} 信任 {r['avg_trust']} 兌現率 {r['avg_fulfill_rate']}%")

    # 3. 月報
    logger.info("[3/3] 產生月報")
    report = generate_monthly_report()
    logger.success(f"Phase 4 完成｜月報：{report['period']}，新承諾 {report['new_promises']} 筆")


if __name__ == "__main__":
    run()
