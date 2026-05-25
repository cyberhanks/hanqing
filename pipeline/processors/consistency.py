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
    """更新所有政治人物的分數（每週執行）

    7 維度信任分數公式（v5）：
      consistency_score  × 25%   AI 分析言行一致性
      fulfill_rate       × 20%   承諾兌現率（客觀）
      attendance_rate    × 15%   立院出席率（客觀）
      external_rating    × 15%   NGO 外部評鑑（最客觀）
      sentiment_score    × 10%   媒體輿情
      voting_align_rate  × 10%   投票參與率
      vote_share_trend   ×  5%   得票趨勢（正向加分）
      factcheck_penalty  最多扣 15 分
    """
    db = get_client()
    politicians = db.table("politicians").select("id, name").execute().data or []
    logger.info(f"開始更新 {len(politicians)} 位政治人物的分數")

    for p in politicians:
        try:
            result = calculate_consistency_score(p["id"])
            score        = result.get("score", 50)
            fulfill_rate = result.get("fulfill_rate", 0)

            # 取多維度欄位
            extra = db.table("politicians").select(
                "attendance_rate,factcheck_false_count,factcheck_count,"
                "external_rating,sentiment_score,voting_align_rate,vote_share_trend"
            ).eq("id", p["id"]).single().execute().data or {}

            attendance      = float(extra.get("attendance_rate")   or 70)
            false_cnt       = int(extra.get("factcheck_false_count") or 0)
            external_rating = float(extra.get("external_rating")    or 60)
            sentiment_score = float(extra.get("sentiment_score")    or 60)
            align_rate      = float(extra.get("voting_align_rate")  or 80)
            vs_trend        = float(extra.get("vote_share_trend")   or 0)

            # 事實查核懲罰：每筆錯誤/誤導扣 3 分，上限 15 分
            factcheck_penalty = min(false_cnt * 3, 15)

            # 得票趨勢轉換：trend ∈ [-20,+20] → [0,10] 分貢獻
            trend_score = max(0, min(10, (vs_trend + 10) / 2))

            # 7 維度加權合成
            trust = round(
                score           * 0.25 +   # AI 言行一致性
                fulfill_rate    * 0.20 +   # 承諾兌現率
                attendance      * 0.15 +   # 出席率
                external_rating * 0.15 +   # NGO 外部評鑑
                sentiment_score * 0.10 +   # 媒體輿情
                align_rate      * 0.10 +   # 黨紀投票一致率
                trend_score     * 0.05 -   # 得票趨勢
                factcheck_penalty           # 事實查核懲罰
            )
            trust = max(0, min(100, trust))

            # 分項明細（存入 score_breakdown JSONB）
            breakdown = {
                "consistency":       score,
                "fulfill_rate":      fulfill_rate,
                "attendance":        attendance,
                "external_rating":   external_rating,
                "sentiment":         sentiment_score,
                "voting_align":      align_rate,
                "vote_trend":        vs_trend,
                "factcheck_penalty": factcheck_penalty,
            }

            db.table("politicians").update({
                "consistency_score": score,
                "fulfill_rate":      fulfill_rate,
                "trust_score":       trust,
                "score_breakdown":   breakdown,
            }).eq("id", p["id"]).execute()

            logger.success(
                f"[OK] {p['name']}：信任 {trust} "
                f"(一致 {score}|兌現 {fulfill_rate}|出席 {attendance}|"
                f"外評 {external_rating}|輿情 {sentiment_score}|"
                f"黨紀 {align_rate}|扣 {factcheck_penalty})"
            )
        except Exception as e:
            logger.error(f"X {p['name']} 分數更新失敗：{e}")
