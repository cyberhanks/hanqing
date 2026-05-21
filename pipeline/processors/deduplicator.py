"""去除重複資料"""
from loguru import logger


def deduplicate(politicians: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for p in politicians:
        key = (p.get("name", ""), p.get("role", ""))
        if key in seen:
            logger.debug(f"去重：{key}")
            continue
        seen.add(key)
        result.append(p)
    logger.info(f"去重完成：{len(politicians)} → {len(result)} 筆")
    return result
