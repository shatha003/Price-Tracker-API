import re

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
}

PRICE_PATTERN = re.compile(r"[\$SAR]\s*([\d,]+\.?\d*)|([\d,]+\.?\d*)\s*(?:SAR|\$)")


async def fetch_price(url: str) -> float | None:
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=15.0, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text(separator=" ", strip=True)
        match = PRICE_PATTERN.search(text)
        if match:
            raw = (match.group(1) or match.group(2)).replace(",", "")
            return float(raw)

        return None
    except (httpx.HTTPError, ValueError, TypeError):
        return None
