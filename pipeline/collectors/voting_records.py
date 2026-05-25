"""
立法院投票紀錄 collector — v5
來源：LY Open Data API dataset 3（表決紀錄）
存入 votes 表，並計算 voting_align_rate（與黨紀一致率）

黨紀比對邏輯：
  1. 同法案中，取同黨多數立場為「黨紀立場」
  2. 若個人立場與黨紀相同 → deviated=False；不同 → deviated=True
  3. align_rate = (1 - deviated_count / total_votes) * 100
"""
import time
import requests
import urllib3
from config import supabase, ANTHROPIC_KEY
from loguru import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LY_API   = "https://data.ly.gov.tw/odw/openDatasetJson.action"
HEADERS  = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
TERM     = 10   # 第10屆（最新）
BATCH    = 100


def _fetch_batch(dataset_id: int, offset: int) -> list[dict]:
    params = {
        "id":          dataset_id,
        "filterParam": f"term={TERM}",
        "offset":      offset,
        "limit":       BATCH,
    }
    try:
        r = requests.get(LY_API, params=params, headers=HEADERS,
                         verify=False, timeout=30)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        return data.get("jsonList") or data.get("data") or []
    except Exception as e:
        logger.debug(f"  fetch offset={offset} error: {e}")
        return []


def _get_politicians() -> dict[str, dict]:
    """回傳 {name: {id, party}} 對應表"""
    rows = supabase.from_("politicians").select("id,name,party").execute().data or []
    return {r["name"]: r for r in rows}


def collect_voting_records() -> int:
    """收集第10屆表決紀錄，計算黨紀一致率"""
    politicians = _get_politicians()
    if not politicians:
        logger.warning("politicians 表無資料，略過")
        return 0

    # ── 1. 拉全量表決資料（dataset 3：委員投票紀錄）
    all_votes: list[dict] = []
    offset = 0
    consecutive_empty = 0

    logger.info(f"開始拉取第{TERM}屆表決紀錄...")
    while True:
        batch = _fetch_batch(3, offset)
        if not batch:
            consecutive_empty += 1
            if consecutive_empty >= 3:
                break
            offset += BATCH
            time.sleep(0.5)
            continue

        consecutive_empty = 0
        all_votes.extend(batch)
        logger.debug(f"  offset={offset}, 本批={len(batch)}, 累計={len(all_votes)}")
        if len(batch) < BATCH:
            break
        offset += BATCH
        time.sleep(0.3)

    logger.info(f"取得 {len(all_votes)} 筆原始表決資料")
    if not all_votes:
        return 0

    # ── 2. 計算每張選票的 bill_name / position
    written = 0
    # 聚合：{bill_key: {party: [positions]}}，用以計算黨紀
    bill_party_votes: dict[str, dict[str, list[str]]] = {}

    records_to_write: list[dict] = []

    for row in all_votes:
        # LY dataset 3 欄位：
        # seatingNo, name, party, billNo, billName, voteDate, voteResult
        name     = row.get("name", "").strip()
        pol      = politicians.get(name)
        if not pol:
            continue

        bill_no   = row.get("billNo", "") or ""
        bill_name = row.get("billName", "") or bill_no or "未知法案"
        vote_date = row.get("voteDate", "") or None
        position  = row.get("voteResult", "") or row.get("vote", "") or "棄權"
        party     = pol["party"] or row.get("party", "")

        # 統一立場字串
        if position in ("贊成", "同意", "支持", "Y", "y", "1"):
            position = "贊成"
        elif position in ("反對", "N", "n", "0"):
            position = "反對"
        elif position in ("棄權", "缺席", ""):
            position = "棄權"

        bill_key = f"{bill_no}||{bill_name[:40]}"
        bill_party_votes.setdefault(bill_key, {}).setdefault(party, []).append(position)

        records_to_write.append({
            "politician_id": pol["id"],
            "bill_name":     bill_name[:200],
            "position":      position,
            "vote_date":     vote_date,
            "bill_category": _categorise(bill_name),
            "party_line":    None,   # 稍後填入
            "deviated":      False,  # 稍後填入
            "_bill_key":     bill_key,
            "_party":        party,
        })

    # ── 3. 計算黨紀立場（同黨多數立場）
    party_line_map: dict[str, dict[str, str]] = {}  # {bill_key: {party: majority_pos}}
    for bill_key, party_dict in bill_party_votes.items():
        party_line_map[bill_key] = {}
        for party, positions in party_dict.items():
            from collections import Counter
            majority = Counter(positions).most_common(1)[0][0]
            party_line_map[bill_key][party] = majority

    # ── 4. 寫入 Supabase（批次 upsert）
    upsert_batch: list[dict] = []
    deviated_by_pol: dict[str, list[bool]] = {}

    for rec in records_to_write:
        bill_key = rec.pop("_bill_key")
        party    = rec.pop("_party")
        party_line = party_line_map.get(bill_key, {}).get(party)
        deviated   = (party_line is not None and
                      rec["position"] != "棄權" and
                      rec["position"] != party_line)

        rec["party_line"] = party_line
        rec["deviated"]   = deviated

        pid = rec["politician_id"]
        deviated_by_pol.setdefault(pid, []).append(deviated)
        upsert_batch.append(rec)

        if len(upsert_batch) >= 200:
            try:
                supabase.from_("votes").upsert(upsert_batch).execute()
                written += len(upsert_batch)
            except Exception as e:
                logger.debug(f"  upsert error: {e}")
            upsert_batch = []

    if upsert_batch:
        try:
            supabase.from_("votes").upsert(upsert_batch).execute()
            written += len(upsert_batch)
        except Exception as e:
            logger.debug(f"  upsert error: {e}")

    # ── 5. 更新 politicians.voting_align_rate
    for pid, flags in deviated_by_pol.items():
        total = len(flags)
        if total == 0:
            continue
        deviated_cnt = sum(flags)
        align_rate   = round((1 - deviated_cnt / total) * 100, 2)
        try:
            supabase.from_("politicians").update({
                "voting_align_rate":    align_rate,
                "vote_participation_rate": round((
                    sum(1 for f in flags) / max(total, 1)
                ) * 100, 2),
            }).eq("id", pid).execute()
        except Exception as e:
            logger.debug(f"  align_rate update error: {e}")

    logger.success(f"投票紀錄收集完成：{written} 筆，{len(deviated_by_pol)} 位議員")
    return written


def _categorise(bill_name: str) -> str:
    """簡單分類法案類型"""
    name = bill_name.lower()
    if any(k in name for k in ["預算", "追加減預算", "特別預算"]):
        return "預算"
    if any(k in name for k in ["組織", "設置"]):
        return "組織"
    if any(k in name for k in ["條例", "法", "規程", "辦法"]):
        return "法律"
    return "其他"
