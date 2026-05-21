"""
立法院 API 爬蟲
API 文件：https://data.ly.gov.tw/odw/openDatasetJson.action
"""
import requests
from datetime import datetime

LY_BASE = "https://data.ly.gov.tw/odw"

def fetch_votes(term: int = 11, session: int = 1) -> list[dict]:
    """取得指定屆期、會期的投票記錄"""
    url = f"{LY_BASE}/openDatasetJson.action?id=13&selectTerm={term}&selectSession={session}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("jsonList", [])

def fetch_legislators(term: int = 11) -> list[dict]:
    """取得指定屆期的立法委員名單"""
    url = f"{LY_BASE}/openDatasetJson.action?id=1&term={term}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json().get("jsonList", [])

if __name__ == "__main__":
    legislators = fetch_legislators()
    print(f"第11屆立委：{len(legislators)} 人")
