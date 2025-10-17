import aiohttp
import asyncio
import json
import logging
from pathlib import Path

from utils import safe_makedirs

# CAIDA’s daily prefix-to-AS dataset (pfx2as) — one URL per day. You may want to build logic to pick the latest.
CAIDA_PFX2AS_URL = "https://publicdata.caida.org/datasets/rw-pfx2as/routeviews-prefix2as-latest.pfx2as.gz"

logger = logging.getLogger("fetch_routeviews")

async def run_routeviews_validation(root: Path):
    safe_makedirs(root)
    # Download the gz file
    async with aiohttp.ClientSession(headers={"User-Agent": "asn-scraper/1.0"}) as session:
        try:
            logger.info("Fetching CAIDA pfx2as from %s", CAIDA_PFX2AS_URL)
            resp = await session.get(CAIDA_PFX2AS_URL)
            resp.raise_for_status()
            compressed = await resp.read()
        except Exception as e:
            logger.error("Failed to fetch pfx2as: %s", e)
            return

    import gzip
    import io

    try:
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as gz:
            data = gz.read().decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error("Failed to decompress pfx2as: %s", e)
        return

    # Build mapping: prefix → origin AS (string)
    pfx2as = {}
    for line in data.splitlines():
        parts = line.strip().split()
        if len(parts) >= 3:
            prefix = parts[0]
            asns = parts[2]
            # For multi-origin, the field may be "AS1_AS2"
            origin = asns.split("_")[0]
            pfx2as[prefix] = origin

    logger.info("Loaded %d prefix→AS mappings from RouteViews", len(pfx2as))

    # For each AS folder, filter the entries
    for country_dir in root.iterdir():
        if not country_dir.is_dir():
            continue
        for asd in country_dir.iterdir():
            if not asd.is_dir() or not asd.name.startswith("AS"):
                continue
            asn = asd.name.lstrip("AS")
            out = asd / "prefixes_routeviews.txt"
            matched = []
            # Check all pfx → see which prefixes map to this AS
            for pfx, origin in pfx2as.items():
                if origin == asn:
                    matched.append(pfx)
            out.write_text("\n".join(sorted(matched)))
            # Update meta
            meta_file = asd / "meta.json"
            meta = {}
            if meta_file.exists():
                meta = json.loads(meta_file.read_text())
            meta["count_routeviews"] = len(matched)
            meta.setdefault("sources_routeviews", []).append(CAIDA_PFX2AS_URL)
            meta_file.write_text(json.dumps(meta, indent=2))
            logger.info("AS%s from RouteViews: %d prefixes", asn, len(matched))

    logger.info("RouteViews validation done")

def compare_prefixes(root: Path):
    """Compare Potaroo, RIPE and RouteViews prefix sets for each AS, write diff JSON."""
    diff_report = {}
    for country_dir in root.iterdir():
        if not country_dir.is_dir():
            continue
        for asd in country_dir.iterdir():
            if not asd.is_dir() or not asd.name.startswith("AS"):
                continue
            asn = asd.name.lstrip("AS")
            def read_set(fname):
                p = asd / fname
                if p.exists():
                    return set(p.read_text().splitlines())
                return set()

            s_potaroo = read_set("prefixes_potaroo.txt")
            s_ripe = read_set("prefixes_ripe.txt")
            s_rv = read_set("prefixes_routeviews.txt")
            diff = {
                "only_potaroo": sorted(s_potaroo - (s_ripe | s_rv)),
                "only_ripe": sorted(s_ripe - (s_potaroo | s_rv)),
                "only_routeviews": sorted(s_rv - (s_potaroo | s_ripe)),
                "in_all_three": sorted(s_potaroo & s_ripe & s_rv),
            }
            diff_report[asn] = diff
            # Also write a local diff file
            (asd / "diff_report.json").write_text(json.dumps(diff, indent=2))
    # Write top-level
    (root / "prefixes_comparison.json").write_text(json.dumps(diff_report, indent=2))
    logger.info("Wrote prefixes_comparison.json at %s", root / "prefixes_comparison.json")
