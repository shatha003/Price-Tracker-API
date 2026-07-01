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

PRICE_PATTERN = re.compile(
    r"(?:(?:SAR|USD|EUR|GBP)\s*([\d,]+\.?\d*))"
    r"|(?:([\d,]+\.?\d*)\s*(?:SAR|USD|EUR|GBP))"
    r"|(?:[\$£€]\s*([\d,]+\.?\d*))"
    r"|(?:([\d,]+\.?\d*)\s*[\$£€])"
)


async def fetch_price(url: str, max_retries: int = 2) -> float | None:
    async with httpx.AsyncClient(
        headers=HEADERS, timeout=15.0, follow_redirects=True
    ) as client:
        for attempt in range(max_retries + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                text = soup.get_text(separator=" ", strip=True)
                match = PRICE_PATTERN.search(text)
                if match:
                    raw = next(g for g in match.groups() if g is not None).replace(",", "")
                    return float(raw)

                return None
            except (httpx.HTTPError, ValueError, TypeError):
                if attempt == max_retries:
                    return None
