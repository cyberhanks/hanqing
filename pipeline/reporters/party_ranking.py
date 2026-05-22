"""黨派兌現率排名計算"""
from loguru import logger
from db.supabase_client import get_client


def calculate_party_rankings() -> list[dict]:
    db = get_client()
    politicians = db.table("politicians")\
        .select("party, trust_score, consistency_score, fulfill_rate, total_promises, fulfilled_count, broken_count")\
        .execute().data or []

    stats: dict = {}
    for p in politicians:
        party = p["party"]
        if party not in stats:
            stats[party] = {
                "count": 0, "trust_sum": 0, "consistency_sum": 0,
                "fulfill_sum": 0, "total_promises": 0, "fulfilled": 0, "broken": 0
            }
        s = stats[party]
        s["count"]           += 1
        s["trust_sum"]       += p.get("trust_score") or 50
        s["consistency_sum"] += p.get("consistency_score") or 50
        s["fulfill_sum"]     += float(p.get("fulfill_rate") or 0)
        s["total_promises"]  += p.get("total_promises") or 0
        s["fulfilled"]       += p.get("fulfilled_count") or 0
        s["broken"]          += p.get("broken_count") or 0

    rankings = []
    for party, s in stats.items():
        n = s["count"]
        rankings.append({
            "party":            party,
            "politician_count": n,
            "avg_trust":        round(s["trust_sum"] / n),
            "avg_consistency":  round(s["consistency_sum"] / n),
            "avg_fulfill_rate": round(s["fulfill_sum"] / n, 1),
            "total_promises":   s["total_promises"],
            "fulfilled":        s["fulfilled"],
            "broken":           s["broken"],
        })

    rankings.sort(key=lambda x: x["avg_trust"], reverse=True)
    logger.info(f"黨派排名計算完成，共 {len(rankings)} 個黨派")
    return rankings
