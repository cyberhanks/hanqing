"""
言行一致性分數計算器
比對：選前承諾 vs 投票行為 vs 發言立場
"""
import json
import anthropic
from loguru import logger
from config import ANTHROPIC_KEY
from db.supabase_client import get_client

client_ai = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

CONSISTENCY_PROMPT = """你是台灣政治分析專家，立場完全中立。

以下是一位政治人物的資料，請分析其言行一致性。

評分標準（0–100）：
- 90–100：承諾幾乎全部兌現，投票與發言高度一致
- 70–89：大部分兌現，偶有落差但有合理說明
- 50–69：約半數兌現，有明顯落差但非完全背離
- 30–49：兌現率偏低，發言與投票常有矛盾
- 0–29：承諾大量跳票，言行嚴重不一致

回傳 JSON：
{
  "score": 0–100 的整數,
  "reasoning": "50字內的分析",
  "key_inconsistencies": ["最明顯的矛盾點1", "矛盾點2"],
  "key_fulfillments": ["最明顯的兌現點1", "兌現點2"]
}

只回傳 JSON，不要任何說明。"""


def calculate_consistency_score(politician_id: str) -> dict:
    """計算單一政治人物的言行一致性分數"""
    db = get_client()

    promises = db.table("promises")\
        .select("text, summary, status, deadline")\
        .eq("politician_id", politician_id)\
        .execute().data or []

    votes = db.table("votes")\
        .select("bill_name, position, vote_date")\
        .eq("politician_id", politician_id)\
        .order("vote_date", desc=True)\
        .limit(50)\
        .execute().data or []

    if not promises and not votes:
        return {"score": 50, "reasoning": "資料不足，無法計算", "fulfill_rate": 0}

    promise_summary = "\n".join([
        f"- [{p['status']}] {p['summary'] or p['text'][:50]}"
        for p in promises[:20]
    ])
    vote_summary = "\n".join([
        f"- {v.get('vote_date') or '?'} {v['bill_name'][:40]}：{v['position']}"
        for v in votes[:20]
    ]) or "（無投票紀錄）"

    total = len(promises)
    fulfilled = sum(1 for p in promises if p["status"] == "fulfilled")
    broken = sum(1 for p in promises if p["status"] == "broken")
    fulfill_rate = round(fulfilled / total * 100) if total else 0

    try:
        response = client_ai.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": (
                    f"{CONSISTENCY_PROMPT}\n\n"
                    f"承諾紀錄（共{total}項，兌現{fulfilled}，跳票{broken}）：\n"
                    f"{promise_summary}\n\n"
                    f"近期投票紀錄：\n{vote_summary}"
                )
            }]
        )
        raw = response.content[0].text.strip()
        raw = raw.removeprefix("```json").removesuffix("```").strip()
        result = json.loads(raw)
        result["fulfill_rate"] = fulfill_rate
        return result
    except Exception as e:
        logger.error(f"一致性分數計算失敗：{e}")
        return {
            "score": min(100, fulfill_rate + 20),
            "reasoning": f"基於兌現率 {fulfill_rate}% 估算",
            "fulfill_rate": fulfill_rate,
        }


def update_all_scores():
    """更新所有政治人物的分數（每週執行）"""
    db = get_client()
    politicians = db.table("politicians").select("id, name").execute().data or []
    logger.info(f"開始更新 {len(politicians)} 位政治人物的分數")

    for p in politicians:
        try:
            result = calculate_consistency_score(p["id"])
            score = result.get("score", 50)
            fulfill_rate = result.get("fulfill_rate", 0)

            db.table("politicians").update({
                "consistency_score": score,
                "fulfill_rate":      fulfill_rate,
                "trust_score":       round((score * 0.6 + fulfill_rate * 0.4)),
            }).eq("id", p["id"]).execute()

            logger.success(f"[OK] {p['name']}：一致性 {score}，兌現率 {fulfill_rate}%")
        except Exception as e:
            logger.error(f"✗ {p['name']} 分數更新失敗：{e}")
