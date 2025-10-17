import argparse, json, os
from fetch_potaroo import fetch_asn_data
from fetch_ripe import cross_validate_prefixes
from fetch_routeviews import cross_validate_routeviews
from utils import safe_write

def main():
    parser = argparse.ArgumentParser(description="ASN Prefix Scraper")
    parser.add_argument("--mode", choices=["potaroo", "validate"], default="potaroo")
    parser.add_argument("--country", help="2-letter country code (e.g., SG)")
    parser.add_argument("--asn", help="Comma-separated ASN list")
    parser.add_argument("--out", default="output", help="Output directory")
    parser.add_argument("--include-routeviews", action="store_true", help="Include RouteViews validation")
    args = parser.parse_args()

    progress_file = os.path.join(args.out, "progress.json")
    progress = {"stage": args.mode, "country": args.country, "done": False}

    safe_write(progress_file, json.dumps(progress, indent=2))

    if args.mode == "potaroo":
        fetch_asn_data(output_dir=args.out, country=args.country, asn_list=args.asn)
        progress["stage"] = "potaroo_done"
    elif args.mode == "validate":
        cross_validate_prefixes(output_dir=args.out)
        if args.include_routeviews:
            cross_validate_routeviews(output_dir=args.out)
        progress["stage"] = "validate_done"

    progress["done"] = True
    safe_write(progress_file, json.dumps(progress, indent=2))
    print(f"✅ Job completed. Progress written to {progress_file}")

if __name__ == "__main__":
    main()
