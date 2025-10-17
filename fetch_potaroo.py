import asyncio
import aiohttp
import async_timeout
import json
from pathlib import Path
import logging
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm_asyncio

from utils import fetch_text, extract_prefixes_from_text, safe_makedirs, RE_AS_NUMBER, get_country_asns

POTAROO_URL = "https://bgp.potaroo.net/cidr/autnums.html"

logger = logging.getLogger("fetch_potaroo")

async def run_potaroo_fetch(root: Path, asn_filter, country, concurrency, force):
    safe_makedirs(root)
    # Determine base URL segment for linking
    base = "/".join(POTAROO_URL.split("/")[:3]) + "/" + "/".join(POTAROO_URL.split("/")[3:-1])

    connector = aiohttp.TCPConnector(limit_per_host=concurrency, ssl=True)
    headers = {"User-Agent": "asn-scraper/1.0"}
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        logger.info("Fetching potaroo autnums page %s", POTAROO_URL)
        html = await fetch_text(session, POTAROO_URL)
        soup = BeautifulSoup(html, "lxml")

        # Extract all ASNs
        seen = set()
        as_entries = []
        for a in soup.find_all("a", href=True):
            text = a.get_text().strip()
            m = RE_AS_NUMBER.search(text)
            if m:
                asn = m.group(1).lstrip("0") or "0"
                if asn not in seen:
                    seen.add(asn)
                    link = a["href"]
                    as_entries.append((asn, link))
        if not as_entries:
            # fallback scanning whole text
            txt = soup.get_text()
            for m in RE_AS_NUMBER.finditer(txt):
                asn = m.group(1).lstrip("0") or "0"
                if asn not in seen:
                    seen.add(asn)
                    as_entries.append((asn, None))

        logger.info("Found %d AS entries", len(as_entries))

        # Filter by country
        if country:
            country_asns = await get_country_asns(session, country)
            before = len(as_entries)
            as_entries = [(asn, link) for (asn, link) in as_entries if asn in country_asns]
            logger.info("Filtered by country %s: %d -> %d", country, before, len(as_entries))
            # Use a subfolder
            country_root = root / country.upper()
        else:
            country_root = root

        safe_makedirs(country_root)

        # Filter by asn_filter if provided
        if asn_filter:
            before = len(as_entries)
            as_entries = [(asn, link) for (asn, link) in as_entries if asn in asn_filter]
            logger.info("Filtered by input list: %d -> %d", before, len(as_entries))

        sem = asyncio.Semaphore(concurrency)

        async def work_one(asn, link):
            async with sem:
                return await _process_asn(session, country_root, asn, link, base, force)

        tasks = [work_one(asn, link) for (asn, link) in as_entries]
        results = []
        for r in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Potaroo fetch"):
            res = await r
            results.append(res)

        # Write report
        rep = {
            "mode": "potaroo",
            "country": country,
            "total_as": len(as_entries),
            "results": results,
        }
        (country_root / "report_potaroo.json").write_text(json.dumps(rep, indent=2))
        logger.info("Potaroo fetch done. Report at %s", country_root / "report_potaroo.json")


async def _process_asn(session, country_root: Path, asn: str, link: str, base_url: str, force: bool):
    folder = country_root / f"AS{asn}"
    safe_makedirs(folder)
    out_file = folder / "prefixes_potaroo.txt"
    meta_file = folder / "meta.json"

    if out_file.exists() and not force:
        return {"asn": asn, "status": "skipped"}

    prefixes = []
    source_urls = []
    if link:
        # join relative
        if link.startswith("http"):
            url = link
        else:
            url = base_url.rstrip("/") + "/" + link.lstrip("/")
        try:
            txt = await fetch_text(session, url)
            prefixes = extract_prefixes_from_text(txt)
            source_urls.append(url)
        except Exception as e:
            logger.warning("AS%s link fetch failed: %s", asn, e)

    if not prefixes:
        # try standard path
        alt = base_url.rstrip("/") + f"/as{asn}/"
        try:
            txt = await fetch_text(session, alt)
            prefixes = extract_prefixes_from_text(txt)
            source_urls.append(alt)
        except Exception as e:
            logger.warning("AS%s alt fetch failed: %s", asn, e)

    if prefixes:
        prefixes = sorted(set(prefixes))
        out_file.write_text("\n".join(prefixes))
        meta = {"asn": asn, "count_potaroo": len(prefixes), "sources_potaroo": source_urls}
    else:
        # write empty
        out_file.write_text("")
        meta = {"asn": asn, "count_potaroo": 0, "sources_potaroo": source_urls}

    meta_file.write_text(json.dumps(meta, indent=2))
    return {"asn": asn, "count": meta.get("count_potaroo", 0), "sources": source_urls}
