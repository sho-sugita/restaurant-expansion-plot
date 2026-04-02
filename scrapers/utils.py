import re

PREFECTURE_PATTERN = re.compile(
    r"(北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|"
    r"茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|"
    r"新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|"
    r"三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|"
    r"鳥取県|島根県|岡山県|広島県|山口県|"
    r"徳島県|香川県|愛媛県|高知県|"
    r"福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)"
)

DATE_PATTERNS = [
    re.compile(r"(\d{4})[年/\.-](\d{1,2})[月/\.-](\d{1,2})"),
    re.compile(r"(\d{4})[年/\.-](\d{1,2})月?"),
    re.compile(r"OPEN[:\s]*(\d{4})[./](\d{1,2})[./]?(\d{0,2})"),
    re.compile(r"オープン[:\s：]*(\d{4})[年/](\d{1,2})"),
]


def extract_prefecture(address: str) -> str:
    if not address:
        return ""
    m = PREFECTURE_PATTERN.search(address)
    return m.group(1) if m else ""


def normalize_date(date_str: str) -> str:
    if not date_str:
        return ""
    date_str = str(date_str).strip()
    for pat in DATE_PATTERNS:
        m = pat.search(date_str)
        if m:
            groups = [g for g in m.groups() if g]
            if len(groups) >= 3:
                return f"{groups[0]}-{int(groups[1]):02d}-{int(groups[2]):02d}"
            elif len(groups) == 2:
                return f"{groups[0]}-{int(groups[1]):02d}-01"
            elif len(groups) == 1:
                return f"{groups[0]}-01-01"
    return date_str
