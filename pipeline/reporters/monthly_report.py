"""月報自動產生器 — 每月1日統計上月資料"""
from datetime import date
from dateutil.relativedelta import relativedelta
from loguru import logger
from db.supabase_client import get_client


def generate_monthly_report() -> dict:
    db = get_client()
    now = date.today()
    last_month_start = (now.replace(day=1) - relativedelta(months=1))
    last_month_end   = now.replace(day=1)
    logger.info(f"產生月報：{last_month_start} ~ {last_month_end}")

    total_politicians = db.table("politicians").select("id", count="exact").execute().count or 0
    new_promises = db.table("promises")\
        .select("id", count="exact")\
        .gte("created_at", str(last_month_start))\
        .lt("created_at", str(last_month_end))\
        .execute().count or 0

    logs = db.table("audit_logs")\
        .select("metadata")\
        .eq("action", "verify")\
        .gte("created_at", str(last_month_start))\
        .execute().data or []

    fulfilled_this_month = sum(
        1 for log in logs
        if (log.get("metadata") or {}).get("new_status") == "fulfilled"
    )
    broken_this_month = sum(
        1 for log in logs
        if (log.get("metadata") or {}).get("new_status") == "broken"
    )

    # 黨派統計
    politicians = db.table("politicians")\
        .select("party, fulfill_rate, consistency_score, trust_score")\
        .execute().data or []

    party_stats: dict = {}
    for p in politicians:
        party = p["party"]
        if party not in party_stats:
            party_stats[party] = {"count": 0, "fulfill_sum": 0, "consistency_sum": 0, "trust_sum": 0}
        party_stats[party]["count"] += 1
        party_stats[party]["fulfill_sum"]      += float(p["fulfill_rate"] or 0)
        party_stats[party]["consistency_sum"]  += float(p["consistency_score"] or 50)
        party_stats[party]["trust_sum"]        += float(p["trust_score"] or 50)

    party_ranking = sorted([
        {
            "party":              party,
            "avg_fulfill_rate":   round(s["fulfill_sum"] / s["count"], 1),
            "avg_consistency":    round(s["consistency_sum"] / s["count"], 1),
            "avg_trust":          round(s["trust_sum"] / s["count"], 1),
            "politician_count":   s["count"],
        }
        for party, s in party_stats.items() if s["count"] > 0
    ], key=lambda x: x["avg_trust"], reverse=True)

    report = {
        "period":                str(last_month_start)[:7],
        "total_politicians":     total_politicians,
        "new_promises":          new_promises,
        "fulfilled_this_month":  fulfilled_this_month,
        "broken_this_month":     broken_this_month,
        "party_ranking":         party_ranking,
        "generated_at":          str(date.today()),
    }

    db.table("audit_logs").insert({
        "record_type": "monthly_report",
        "action":      "generated",
        "actor":       "system:reporter",
        "metadata":    report,
    }).execute()

    logger.success(f"月報產生完成：{report['period']}")
    return report
