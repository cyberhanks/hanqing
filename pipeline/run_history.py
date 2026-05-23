"""
歷史公開行為批次收集
執行順序：
  1. LY 發言 / 質詢（第 5~10 屆）
  2. 法案提案 / 連署（第 5~10 屆）
  3. 爭議事件（Google News + 維基）
  4. 選舉政見（2004~2024）

執行時間預估：2~4 小時（視 API 速度）
可分段執行：python run_history.py --step speeches
"""
import sys
import argparse
from loguru import logger

# 設定 log 格式
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")
logger.add("logs/history_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days")

from collectors.ly_history       import collect_speeches, collect_interpellations
from collectors.bills            import collect_proposals, collect_cosigners
from collectors.controversies    import collect_news_controversies, collect_wikipedia_controversies
from collectors.election_pledges import collect_election_pledges
from collectors.attendance       import collect_attendance, collect_interpellation_counts
from collectors.factcheck        import collect_factchecks
from processors.pledge_analysis  import analyse_pledges
from processors.promise_verifier import verify_promises


def run_all():
    results = {}

    logger.info("═══ Step 1: LY 發言紀錄 ═══")
    results["speeches"] = collect_speeches()

    logger.info("═══ Step 2: 質詢紀錄 ═══")
    results["interpellations"] = collect_interpellations()

    logger.info("═══ Step 3: 法案提案 ═══")
    results["proposals"] = collect_proposals()

    logger.info("═══ Step 4: 法案連署 ═══")
    results["cosigners"] = collect_cosigners()

    logger.info("═══ Step 5: 爭議事件（新聞）═══")
    results["controversies_news"] = collect_news_controversies()

    logger.info("═══ Step 6: 爭議事件（維基）═══")
    results["controversies_wiki"] = collect_wikipedia_controversies()

    logger.info("═══ Step 7: 選舉政見 ═══")
    results["election_pledges"] = collect_election_pledges()

    logger.success("═══ 歷史收集完成 ═══")
    for k, v in results.items():
        logger.info(f"  {k}: {v} 筆")


STEPS = {
    "speeches":        collect_speeches,
    "interpellations": collect_interpellations,
    "proposals":       collect_proposals,
    "cosigners":       collect_cosigners,
    "controversies":   lambda: collect_news_controversies() + collect_wikipedia_controversies(),
    "pledges":         collect_election_pledges,
    "attendance":      lambda: collect_attendance() + collect_interpellation_counts(),
    "factcheck":       collect_factchecks,
    "pledge_analysis": analyse_pledges,
    "verify":          verify_promises,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="汗青歷史資料收集")
    parser.add_argument("--step", choices=list(STEPS.keys()) + ["all"],
                        default="all", help="指定執行步驟")
    args = parser.parse_args()

    if args.step == "all":
        run_all()
    else:
        fn = STEPS[args.step]
        count = fn()
        logger.success(f"{args.step} 完成：{count} 筆")
