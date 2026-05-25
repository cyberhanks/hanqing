"""
歷史公開行為批次收集 — v5
執行順序建議：
  speeches → interpellations → proposals → cosigners →
  controversies → pledges → attendance → factcheck →
  voting → external_ratings → election_results → sentiment →
  pledge_analysis → verify → score

可分段執行：python run_history.py --step <步驟名稱>
執行全部：  python run_history.py --step all
"""
import sys
import argparse
from loguru import logger

logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")
logger.add("logs/history_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days")

from collectors.ly_history        import collect_speeches, collect_interpellations
from collectors.bills             import collect_proposals, collect_cosigners
from collectors.controversies     import collect_news_controversies, collect_wikipedia_controversies
from collectors.election_pledges  import collect_election_pledges
from collectors.attendance        import collect_attendance, collect_interpellation_counts
from collectors.factcheck         import collect_factchecks
from collectors.voting_records    import collect_voting_records
from collectors.external_ratings  import collect_ccw_ratings, collect_monitoring_records
from collectors.election_results  import collect_election_results
from processors.sentiment_analysis import analyse_sentiment
from processors.pledge_analysis   import analyse_pledges
from processors.promise_verifier  import verify_promises
from processors.consistency       import update_all_scores


# ── 全量執行順序 ──────────────────────────────────────────────
PIPELINE_ORDER = [
    ("speeches",          "LY 發言紀錄"),
    ("interpellations",   "質詢紀錄"),
    ("proposals",         "法案提案"),
    ("cosigners",         "法案連署"),
    ("controversies",     "爭議事件"),
    ("pledges",           "選舉政見"),
    ("attendance",        "出席紀錄"),
    ("factcheck",         "事實查核"),
    ("voting",            "投票紀錄（含黨紀比對）"),
    ("external_ratings",  "NGO 外部評鑑"),
    ("monitoring",        "監察院紀錄"),
    ("election_results",  "選舉得票率（2004-2024）"),
    ("sentiment",         "媒體輿情分析"),
    ("pledge_analysis",   "AI 政見落實分析"),
    ("verify",            "承諾驗證更新"),
    ("score",             "7 維度信任分數重算"),
]


def run_all():
    results = {}
    for step_name, label in PIPELINE_ORDER:
        logger.info(f"═══ {label} ═══")
        fn = STEPS[step_name]
        try:
            results[step_name] = fn()
        except Exception as e:
            logger.error(f"  {label} 失敗：{e}")
            results[step_name] = -1

    logger.success("═══ 全量收集完成 ═══")
    for step_name, label in PIPELINE_ORDER:
        val = results.get(step_name, "?")
        logger.info(f"  {label}: {val} 筆")


STEPS: dict[str, callable] = {
    "speeches":         collect_speeches,
    "interpellations":  collect_interpellations,
    "proposals":        collect_proposals,
    "cosigners":        collect_cosigners,
    "controversies":    lambda: (
                            collect_news_controversies() +
                            collect_wikipedia_controversies()
                        ),
    "pledges":          collect_election_pledges,
    "attendance":       lambda: (
                            collect_attendance() +
                            collect_interpellation_counts()
                        ),
    "factcheck":        collect_factchecks,
    "voting":           collect_voting_records,
    "external_ratings": collect_ccw_ratings,
    "monitoring":       collect_monitoring_records,
    "election_results": collect_election_results,
    "sentiment":        analyse_sentiment,
    "pledge_analysis":  analyse_pledges,
    "verify":           verify_promises,
    "score":            update_all_scores,
}


if __name__ == "__main__":
    valid_steps = list(STEPS.keys()) + ["all"]
    parser = argparse.ArgumentParser(description="汗青歷史資料收集 v5")
    parser.add_argument(
        "--step",
        choices=valid_steps,
        default="all",
        help="指定執行步驟（預設 all）",
    )
    args = parser.parse_args()

    if args.step == "all":
        run_all()
    else:
        fn = STEPS[args.step]
        count = fn()
        logger.success(f"{args.step} 完成：{count}")
