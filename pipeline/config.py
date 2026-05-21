from dotenv import load_dotenv
from pathlib import Path
import os

# Explicit path so load_dotenv works regardless of CWD
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

SOURCES = {
    "legislators": "https://www.ly.gov.tw/Pages/List.aspx?nodeid=109",
    "ly_api_base": "https://www.ly.gov.tw/WebAPI",
    "mayors": "https://www.moi.gov.tw/LocalOfficial.aspx?n=579&TYP=KND0005",
    "cabinet": "https://www.ey.gov.tw/Page/7AC6136EBB87A125",
}

PARTY_MAP = {
    "民主進步黨": "DPP",
    "民進黨": "DPP",
    "中國國民黨": "KMT",
    "國民黨": "KMT",
    "台灣民眾黨": "TPP",
    "民眾黨": "TPP",
    "台灣基進": "TSP",
    "時代力量": "NPP",
    "無黨籍": "IND",
    "無黨團結聯盟": "NPSU",
}
