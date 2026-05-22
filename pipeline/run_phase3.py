"""Phase 3：承諾核實 + 一致性分數更新（每週執行）"""
import sys
from loguru import logger
from processors.verifier import verify_promise, REQUIRES_HUMAN_CONFIRM
from processors.consistency import update_all_scores
from db.supabase_client import get_client

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | {level} | {message}")


def run_verification():
    logger.info("Phase 3a：承諾核實")
    client = get_client()

    result = (
        client.table("promises")
        .select("*, politicians(name)")
        .eq("status", "active")
        .order("updated_at", desc=False)
        .limit(50)
        .execute()
    )
    promises = result.data
    logger.info(f"待核實承諾：{len(promises)} 筆")

    changed, unchanged = 0, 0
    for promise in promises:
        politician_name = (promise.get("politicians") or {}).get("name", "")
        if not politician_name:
            continue

        verification = verify_promise(promise, politician_name)
        new_status   = verification.get("status", "active")
        confidence   = verification.get("confidence", 0)

        if confidence >= 0.8 and new_status != promise["status"]:
            needs_human  = new_status in REQUIRES_HUMAN_CONFIRM
            update_data  = {
                "status":      new_status if not needs_human else promise["status"],
                "verified_by": "auto" if not needs_human else "pending_human",
                "evidence_url": verification.get("evidence_url"),
            }
            client.table("promises").update(update_data).eq("id", promise["id"]).execute()
            client.table("audit_logs").insert({
                "record_type": "promise", "record_id": promise["id"],
                "action": "verify", "actor": "system:verifier",
                "note": verification.get("reasoning", ""),
                "metadata": {
                    "old_status":  promise["status"],
                    "new_status":  new_status,
                    "confidence":  confidence,
                    "needs_human": needs_human,
                },
            }).execute()
            changed += 1
            if needs_human:
                logger.warning(f"需人工確認：{politician_name} → {new_status}")
        else:
            unchanged += 1

    logger.success(f"核實完成｜變更 {changed} 筆，無變化 {unchanged} 筆")


def run_score_update():
    logger.info("Phase 3b：言行一致性分數更新")
    update_all_scores()


def run():
    run_verification()
    run_score_update()


if __name__ == "__main__":
    run()
