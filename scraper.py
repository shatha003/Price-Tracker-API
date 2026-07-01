import json
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


def _parse_json_ld(soup: BeautifulSoup) -> float | None:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                offers = data.get("offers", data)
                if isinstance(offers, dict):
                    price = offers.get("price")
                    if price:
                        return float(price)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        offers = item.get("offers", item)
                        if isinstance(offers, dict):
                            price = offers.get("price")
                            if price:
                                return float(price)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    return None


def _parse_meta_tags(soup: BeautifulSoup) -> float | None:
    for prop in ("product:price:amount", "og:price:amount"):
        meta = soup.find("meta", property=prop)
        if meta and meta.get("content"):
            try:
                return float(meta["content"].replace(",", ""))
            except (ValueError, TypeError):
                continue
    return None


def _parse_amazon_selectors(soup: BeautifulSoup) -> float | None:
    selectors = [
        ".a-price .a-offscreen",
        ".a-price-whole",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            raw = el.get_text(strip=True).replace(",", "").replace("$", "").replace("SAR", "")
            try:
                return float(raw)
            except (ValueError, TypeError):
                continue
    return None


def _parse_regex(soup: BeautifulSoup) -> float | None:
    text = soup.get_text(separator=" ", strip=True)
    match = PRICE_PATTERN.search(text)
    if match:
        raw = next(g for g in match.groups() if g is not None).replace(",", "")
        return float(raw)
    return None


async def fetch_price(url: str, max_retries: int = 2) -> float | None:
    async with httpx.AsyncClient(
        headers=HEADERS, timeout=15.0, follow_redirects=True
    ) as client:
        for attempt in range(max_retries + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                parsers = [
                    _parse_json_ld,
                    _parse_meta_tags,
                    _parse_amazon_selectors,
                    _parse_regex,
                ]
                for parse in parsers:
                    price = parse(soup)
                    if price is not None:
                        return price

                return None
            except (httpx.HTTPError, ValueError, TypeError):
                if attempt == max_retries:
                    return None
