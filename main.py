import argparse
from fetch_potaroo import fetch_asn_data
from fetch_ripe import cross_validate_prefixes

def main():
    parser = argparse.ArgumentParser(description="ASN Prefix Scraper")
    parser.add_argument("--mode", choices=["potaroo", "validate"], default="potaroo")
    parser.add_argument("--country", help="2-letter country code (e.g., SG)")
    parser.add_argument("--asn", help="Comma-separated ASN list")
    parser.add_argument("--out", default="output", help="Output directory")
    args = parser.parse_args()

    if args.mode == "potaroo":
        fetch_asn_data(output_dir=args.out, country=args.country, asn_list=args.asn)
    elif args.mode == "validate":
        cross_validate_prefixes(output_dir=args.out)

if __name__ == "__main__":
    main()
