"""Supabase 資料庫操作"""
from supabase import create_client, Client
from loguru import logger
from config import SUPABASE_URL, SUPABASE_KEY


def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_politicians(politicians: list[dict]) -> dict:
    """寫入政治人物，以 name 為唯一鍵避免重複"""
    client = get_client()
    success, skipped, failed = 0, 0, 0

    # 取得已存在的人名
    existing = {p["name"] for p in client.table("politicians").select("name").execute().data}

    for p in politicians:
        name = p.get("name", "").strip()
        if not name:
            continue
        if name in existing:
            logger.debug(f"跳過（已存在）：{name}")
            skipped += 1
            continue
        try:
            record = {
                "name":        name,
                "party":       p.get("party", "OTHER"),
                "role":        p.get("role", "立法委員"),
                "region":      p.get("region"),
                "term_start":  p.get("term_start"),
                "term_end":    p.get("term_end"),
                "trust_score": 50,
            }
            client.table("politicians").insert(record).execute()
            client.table("audit_logs").insert({
                "record_type": "politician",
                "action":      "created",
                "actor":       "system:collector",
                "note":        f"來源：{p.get('source', 'unknown')}",
            }).execute()
            existing.add(name)
            success += 1
            logger.debug(f"[OK] 新增：{name} ({p.get('party')})")
        except Exception as e:
            failed += 1
            logger.error(f"✗ 失敗：{name} — {e}")

    return {"success": success, "skipped": skipped, "failed": failed}


def get_all_politicians() -> list[dict]:
    client = get_client()
    return client.table("politicians").select("*").execute().data


def get_politician_id(name: str) -> str | None:
    """依姓名查詢政治人物 ID"""
    client = get_client()
    result = (
        client.table("politicians")
        .select("id")
        .eq("name", name)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]
    return None


def upsert_promise(promise: dict, politician_id: str) -> bool:
    """寫入承諾紀錄"""
    client = get_client()
    confidence = promise.pop("_confidence", 85)

    record = {
        "politician_id":  politician_id,
        "text":           promise.get("promise_text", ""),
        "summary":        promise.get("summary", ""),
        "topic":          promise.get("topic", "其他"),
        "deadline":       promise.get("deadline"),
        "status":         "active",
        "source_url":     promise.get("source_url", ""),
        "source_name":    promise.get("source_name", ""),
        "source_date":    promise.get("source_date") or None,
        "confidence":     confidence,
        "verified_by":    "ai" if confidence >= 85 else "pending",
    }

    try:
        client.table("promises").insert(record).execute()
        logger.debug(f"承諾寫入：{promise.get('summary', '')[:30]}")
        return True
    except Exception as e:
        logger.error(f"承諾寫入失敗：{e}")
        return False
