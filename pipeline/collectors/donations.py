"""
政治獻金自動收集
來源：監察院政治獻金申報平台 ardata.cy.gov.tw
"""
import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

DONATION_BASE = "https://ardata.cy.gov.tw"

INDUSTRY_KEYWORDS = {
    "建設": ["建設", "營造", "地產", "不動產", "開發", "建築"],
    "科技": ["科技", "資訊", "軟體", "半導體", "電子", "網路"],
    "金融": ["銀行", "保險", "證券", "投資", "金融", "資產"],
    "媒體": ["媒體", "傳播", "廣播", "電視", "出版", "新聞"],
    "醫療": ["醫院", "診所", "製藥", "醫療", "健康", "生技"],
    "餐飲": ["餐飲", "食品", "飲料", "餐廳", "飯店"],
    "製造": ["工業", "製造", "機械", "化工", "鋼鐵"],
    "農業": ["農業", "漁業", "畜牧", "農產"],
    "交通": ["航空", "航運", "運輸", "物流", "港口"],
    "能源": ["能源", "電力", "石油", "天然氣", "太陽能"],
}


def classify_donor_industry(donor_name: str) -> str:
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(kw in donor_name for kw in keywords):
            return industry
    return "其他"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_donations_for_politician(name: str, year: int) -> list[dict]:
    """取得特定政治人物的政治獻金申報資料"""
    logger.info(f"收集政治獻金：{name} {year}年")
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    try:
        session = requests.Session()
        session.headers.update(headers)
        resp = session.get(
            f"{DONATION_BASE}/financial/search",
            params={"name": name, "year": year},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        donations = []
        for record in data.get("data", []):
            donor_name = record.get("donorName", "")
            donations.append({
                "donor_name":     donor_name,
                "donor_type":     record.get("donorType", ""),
                "donor_industry": classify_donor_industry(donor_name),
                "amount":         record.get("amount", 0),
                "year":           year,
                "source_url":     f"{DONATION_BASE}/financial/{record.get('id', '')}",
            })
        logger.success(f"收集到 {len(donations)} 筆獻金：{name}")
        return donations
    except Exception as e:
        logger.warning(f"監察院 API 失敗：{name} {year} — {e}")
        return []


def collect_all_donations(politician_id: str, name: str) -> list[dict]:
    """收集近三年的政治獻金"""
    from datetime import date
    current_year = date.today().year
    all_donations = []
    for year in range(current_year - 2, current_year + 1):
        donations = fetch_donations_for_politician(name, year)
        for d in donations:
            d["politician_id"] = politician_id
        all_donations.extend(donations)
    return all_donations
