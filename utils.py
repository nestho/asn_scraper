import os
import re
import aiohttp
import async_timeout
from typing import Optional, List
from bs4 import BeautifulSoup

# Regexes
RE_IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}\b")
RE_IPV6 = re.compile(r"\b[0-9a-fA-F:]+/\d{1,3}\b")
RE_AS_NUMBER = re.compile(r"AS?0*(\d+)\b", re.IGNORECASE)

async def fetch_text(session: aiohttp.ClientSession, url: str, timeout: int = 30) -> str:
    for attempt in range(5):
        try:
            async with async_timeout.timeout(timeout):
                resp = await session.get(url)
                resp.raise_for_status()
                return await resp.text()
        except Exception:
            await asyncio.sleep(1 + attempt * 2)
    raise Exception(f"Failed to fetch {url}")

def extract_prefixes_from_text(text: str) -> List[str]:
    s = set()
    s.update(RE_IPV4.findall(text))
    s.update(RE_IPV6.findall(text))
    return sorted(s)

def safe_makedirs(path: Path):
    os.makedirs(path, exist_ok=True)

async def get_country_asns(session: aiohttp.ClientSession, country: str) -> List[str]:
    """Scrape the country table page to get ASNs for the given country code."""
    url = "https://bgp.potaroo.net/cidr/country_table.html"
    html = await fetch_text(session, url)
    soup = BeautifulSoup(html, "lxml")
    # Look for anchor named country
    anchor = soup.find("a", {"name": country.upper()})
    if not anchor:
        return []
    # Then next <pre> block contains lines like "AS12345 …"
    pre = anchor.find_next("pre")
    if not pre:
        return []
    asns = []
    for line in pre.get_text().splitlines():
        line = line.strip()
        if line.upper().startswith("AS"):
            parts = line.split()
            asns.append(parts[0].lstrip("AS"))
    return asns
