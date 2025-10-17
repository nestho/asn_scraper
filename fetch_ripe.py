import asyncio
import aiohttp
import json
import logging
from pathlib import Path
from utils import fetch_text

RIPE_API = "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{}"

logger = logging.getLogger("fetch_ripe")

async def run_ripe_validation(root: Path):
    # Walk through AS folders under root
    async with aiohttp.ClientSession(headers={"User-Agent": "asn-scraper/1.0"}) as session:
        tasks = []
        for country_dir in root.iterdir():
            if not country_dir.is_dir():
                continue
            for asd in country_dir.iterdir():
                if asd.is_dir() and asd.name.upper().startswith("AS"):
                    tasks.append(_handle_asn(session, asd))
        if not tasks:
            logger.warning("No AS folders found for RIPE validation")
            return
        for f in asyncio.as_completed(tasks):
            await f
        logger.info("RIPE validation done")

async def _handle_asn(session: aiohttp.ClientSession, as_folder: Path):
    asn = as_folder.name.lstrip("AS")
    url = RIPE_API.format(asn)
    try:
        txt = await fetch_text(session, url)
        data = json.loads(txt)
        prefixes = [p["prefix"] for p in data.get("data", {}).get("prefixes", [])]
    except Exception as e:
        logger.warning("RIPEstat failed for AS%s: %s", asn, e)
        prefixes = []

    out = as_folder / "prefixes_ripe.txt"
    out.write_text("\n".join(prefixes))
    # Update meta.json
    meta = {}
    meta_file = as_folder / "meta.json"
    if meta_file.exists():
        meta = json.loads(meta_file.read_text())
    meta["count_ripe"] = len(prefixes)
    meta.setdefault("sources_ripe", []).append(url)
    meta_file.write_text(json.dumps(meta, indent=2))
    logger.info("AS%s RIPEstat: %d prefixes", asn, len(prefixes))
