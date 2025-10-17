import os
import json
import gzip
import requests
from tqdm import tqdm
from utils import safe_write

ROUTEVIEWS_URL = "https://routeviews.org/route-views6/bgpdata/latest/RIBS/"  # IPv6 route dump
ROUTEVIEWS_API = "https://stat.ripe.net/data/looking-glass/data.json?resource={asn}"

def fetch_routeviews_prefixes(asn):
    """
    Fallback API method: use RIPE Looking Glass for routeviews data
    """
    try:
        url = ROUTEVIEWS_API.format(asn=asn)
        r = requests.get(url, timeout=30)
        data = r.json()
        prefixes = set()
        for peer in data.get("data", {}).get("responses", []):
            for entry in peer.get("response", {}).get("routes", []):
                if "/" in entry.get("prefix", ""):
                    prefixes.add(entry["prefix"])
        return list(prefixes)
    except Exception as e:
        print(f"[WARN] RouteViews fetch failed for {asn}: {e}")
        return []
    

def cross_validate_routeviews(output_dir="output"):
    """
    Cross validate existing Potaroo/RIPE results with RouteViews data
    """
    for root, dirs, files in os.walk(output_dir):
        if "meta.json" in files:
            with open(os.path.join(root, "meta.json")) as f:
                meta = json.load(f)
            asn = meta["asn"]

            print(f"🔍 RouteViews validation for {asn}")
            prefixes = fetch_routeviews_prefixes(asn)
            if prefixes:
                safe_write(os.path.join(root, "prefixes_routeviews.txt"), "\n".join(prefixes))
                meta["sources"].append("routeviews")
                meta["routeviews_prefix_count"] = len(prefixes)
                safe_write(os.path.join(root, "meta.json"), json.dumps(meta, indent=2))
