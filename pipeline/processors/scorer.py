"""信心分數計算器"""


def calculate_confidence(item: dict, source_type: str = "web") -> int:
    score = 100
    source_penalty = {
        "ly_api": 0, "gazette": 5, "news": 10, "web": 15, "static": 20,
    }
    score -= source_penalty.get(source_type, 15)

    if not item.get("source_url"):         score -= 15
    if not item.get("source_date"):        score -= 10
    if not item.get("politician_name") and not item.get("politician_id"):
        score -= 20

    if item.get("type") == "promise":
        if not item.get("promise_text"):   score -= 30
        if not item.get("deadline"):       score -= 5
        if not item.get("verifiable"):     score -= 10

    ai_conf = item.get("confidence", 0.8)
    if ai_conf < 0.7:    score -= 20
    elif ai_conf < 0.8:  score -= 10
    elif ai_conf < 0.9:  score -= 5

    return max(0, min(100, score))


def needs_review(score: int) -> bool:
    return score < 85


def should_publish(score: int) -> bool:
    return score >= 85
