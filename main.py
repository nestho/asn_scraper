#!/usr/bin/env python3
import argparse
import asyncio
from pathlib import Path

from fetch_potaroo import run_potaroo_fetch
from fetch_ripe import run_ripe_validation
from fetch_routeviews import run_routeviews_validation, compare_prefixes

def parse_args():
    p = argparse.ArgumentParser(description="ASN Prefix Collector & Validator")
    p.add_argument("--mode", choices=["potaroo", "validate", "all"], default="all",
                   help="Which stages to run: potaroo only, validate (RIPE + RV), or all (fetch + validate)")
    p.add_argument("--country", help="2-letter country code (e.g. SG) to filter ASNs")
    p.add_argument("--asn", help="Comma-separated list of ASNs to restrict to")
    p.add_argument("--output", default="output", help="Root output directory")
    p.add_argument("--concurrency", type=int, default=10, help="HTTP concurrency")
    p.add_argument("--force", action="store_true", help="Force re-fetching even if outputs exist")
    return p.parse_args()

def parse_asn_list(asn_str: str):
    if asn_str is None:
        return None
    parts = [a.strip().upper().lstrip("AS") for a in asn_str.split(",") if a.strip()]
    return parts or None

async def main():
    args = parse_args()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)

    asn_list = parse_asn_list(args.asn)

    # 1) Run potaroo fetch if needed
    if args.mode in ("potaroo", "all"):
        await run_potaroo_fetch(root, asn_list, args.country, args.concurrency, args.force)

    # 2) RIPE validation
    if args.mode in ("validate", "all"):
        await run_ripe_validation(root)

    # 3) RouteViews validation + compare
    if args.mode in ("validate", "all"):
        await run_routeviews_validation(root)
        compare_prefixes(root)

if __name__ == "__main__":
    asyncio.run(main())
