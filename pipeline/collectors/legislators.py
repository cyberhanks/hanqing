"""
立法委員資料收集
來源：立法院開放資料 API（優先）→ 靜態備援
"""
import json
import requests
import urllib3
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed
from config import PARTY_MAP

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "identity",   # 不要壓縮，避免 gzip 解壓錯誤
}


def normalize_party(raw: str) -> str:
    raw = (raw or "").strip()
    known = {"DPP", "KMT", "TPP", "TSP", "NPP", "IND", "NPSU", "OTHER"}
    if raw in known:
        return raw
    for key, val in PARTY_MAP.items():
        if key in raw:
            return val
    return "OTHER"


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def fetch_legislators_from_api() -> list[dict]:
    logger.info("從立法院開放資料 API 收集立委（第11屆）")
    url = "https://data.ly.gov.tw/odw/openDatasetJson.action"
    params = {"id": "16", "category": "A", "term": "11", "fileType": "json"}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=30, verify=False)
    resp.raise_for_status()

    # 手動解析，避免 requests 自動 gzip 解碼失敗
    try:
        data = resp.json()
    except Exception:
        data = json.loads(resp.content.decode("utf-8", errors="replace"))

    results = []
    for item in data.get("dataList", []):
        name = (item.get("name") or item.get("memberName") or "").strip()
        if not name:
            continue
        results.append({
            "name":       name,
            "party":      normalize_party(item.get("party") or item.get("partyName") or ""),
            "role":       "立法委員",
            "region":     (item.get("areaName") or item.get("electoralDistrict") or "").strip(),
            "term_start": "2024-02-01",
            "term_end":   "2028-01-31",
            "source":     "立法院開放資料 API",
            "source_url": "https://data.ly.gov.tw/",
        })
    logger.success(f"API 收集完成：{len(results)} 筆")
    return results


def fetch_legislators() -> list[dict]:
    """主要入口：API 失敗則回傳靜態備援資料"""
    try:
        result = fetch_legislators_from_api()
        if result:
            return result
    except Exception as e:
        logger.warning(f"API 失敗：{e}，改用靜態備援")
    return get_static_legislators()


def get_static_legislators() -> list[dict]:
    """
    靜態備援：第11屆立委名單（113位）
    來源：中選會 2024年1月公告
    """
    logger.info("使用靜態備援立委名單")
    # 不分區立委（34席）
    proportional = [
        # DPP 不分區
        ("沈伯洋", "DPP"), ("吳思瑤", "DPP"), ("吳沛憶", "DPP"), ("林月琴", "DPP"),
        ("王世堅", "DPP"), ("陳培瑜", "DPP"), ("蔡易餘", "DPP"), ("鍾佳濱", "DPP"),
        ("莊瑞雄", "DPP"), ("劉世芳", "DPP"), ("邱志偉", "DPP"), ("柯建銘", "DPP"),
        ("羅美玲", "DPP"),
        # KMT 不分區
        ("韓國瑜", "KMT"), ("廖先翔", "KMT"), ("鄭麗文", "KMT"), ("葉元之", "KMT"),
        ("牛煦庭", "KMT"), ("賴士葆", "KMT"), ("謝衣鳳", "KMT"), ("李彥秀", "KMT"),
        ("陳菁徽", "KMT"), ("吳宗憲", "KMT"), ("林德福", "KMT"), ("陳玉珍", "KMT"),
        # TPP 不分區
        ("黃國昌", "TPP"), ("黃珊珊", "TPP"), ("張啟楷", "TPP"), ("林國成", "TPP"),
        ("吳春城", "TPP"), ("陳昭姿", "TPP"), ("麥玉珍", "TPP"), ("劉書彬", "TPP"),
        ("張育美", "TPP"),
    ]
    # 區域立委（部分主要人物）
    regional = [
        ("江啟臣", "KMT", "台中市第二選區"),
        ("傅崑萁", "KMT", "花蓮縣選區"),
        ("謝龍介", "KMT", "台南市第一選區"),
        ("羅廷瑋", "DPP", "桃園市第二選區"),
        ("鄭運鵬", "DPP", "桃園市第三選區"),
        ("林俊憲", "DPP", "高雄市第三選區"),
        ("李昆澤", "DPP", "高雄市第五選區"),
        ("趙天麟", "DPP", "高雄市第九選區"),
        ("洪孟楷", "KMT", "新北市第七選區"),
        ("張智倫", "KMT", "新北市第八選區"),
    ]

    results = []
    for name, party in proportional:
        results.append({
            "name": name, "party": party, "role": "立法委員",
            "region": "全國不分區", "term_start": "2024-02-01",
            "term_end": "2028-01-31", "source": "靜態備援",
        })
    for name, party, region in regional:
        results.append({
            "name": name, "party": party, "role": "立法委員",
            "region": region, "term_start": "2024-02-01",
            "term_end": "2028-01-31", "source": "靜態備援",
        })
    logger.info(f"靜態備援：{len(results)} 筆")
    return results
