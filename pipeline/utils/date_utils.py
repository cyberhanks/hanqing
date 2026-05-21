"""民國年 ↔ 西元年轉換工具"""
import re


def roc_to_ad(roc_date_str: str) -> str | None:
    if not roc_date_str:
        return None
    m = re.match(r'^(\d{3})(\d{2})(\d{2})$', str(roc_date_str).strip())
    if m:
        return f"{int(m.group(1))+1911}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.match(r'^(\d{2,3})[/\-.](\d{1,2})[/\-.](\d{1,2})$', str(roc_date_str).strip())
    if m:
        return f"{int(m.group(1))+1911}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.match(r'民國(\d+)年(\d+)月(\d+)日', roc_date_str)
    if m:
        return f"{int(m.group(1))+1911}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def normalize_date(date_str: str) -> str | None:
    if not date_str:
        return None
    result = roc_to_ad(date_str)
    if result:
        return result
    for pattern in [r'(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})', r'(\d{4})(\d{2})(\d{2})']:
        m = re.match(pattern, str(date_str).strip())
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1900 < y < 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
                return f"{y}-{mo:02d}-{d:02d}"
    return None
