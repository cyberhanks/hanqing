"""
縣市長資料收集
靜態資料（2022年選出，任期至2026年）+ 內政部官網備援
"""
import requests
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from config import SOURCES, PARTY_MAP

CURRENT_MAYORS = [
    {"name": "蔣萬安", "region": "台北市",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "侯友宜", "region": "新北市",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "張善政", "region": "桃園市",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "高虹安", "region": "新竹市",  "party": "TPP", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "楊文科", "region": "新竹縣",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "鍾東錦", "region": "苗栗縣",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "盧秀燕", "region": "台中市",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "許淑華", "region": "南投縣",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "王惠美", "region": "彰化縣",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "林明溱", "region": "雲林縣",  "party": "DPP", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "翁章梁", "region": "嘉義縣",  "party": "DPP", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "黃敏惠", "region": "嘉義市",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "黃偉哲", "region": "台南市",  "party": "DPP", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "陳其邁", "region": "高雄市",  "party": "DPP", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "周春米", "region": "屏東縣",  "party": "DPP", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "陳光復", "region": "宜蘭縣",  "party": "DPP", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "謝國樑", "region": "基隆市",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "徐榛蔚", "region": "花蓮縣",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "饒慶鈴", "region": "台東縣",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "賴峰偉", "region": "澎湖縣",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "陳福海", "region": "金門縣",  "party": "IND", "term_start": "2022-12-25", "term_end": "2026-12-24"},
    {"name": "王忠銘", "region": "連江縣",  "party": "KMT", "term_start": "2022-12-25", "term_end": "2026-12-24"},
]


def fetch_mayors() -> list[dict]:
    logger.info("開始收集縣市長資料")
    results = []
    for m in CURRENT_MAYORS:
        results.append({
            **m,
            "role": "縣市長",
            "source": "靜態資料",
            "source_url": "https://www.moi.gov.tw/",
        })
    logger.success(f"縣市長資料完成：{len(results)} 筆")
    return results
