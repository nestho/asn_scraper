import os
import json
import requests
from tqdm import tqdm
from utils import safe_write

RIPE_API = "https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn}"

def cross_validate_prefixes(output_dir="output"):
    for root, dirs, files in os.walk(output_dir):
        if "meta.json" in files:
            with open(os.path.join(root, "meta.json")) as f:
                meta = json.load(f)
            asn = meta["asn"]

            try:
                url = RIPE_API.format(asn=asn)
                r = requests.get(url, timeout=20)
                data = r.json()
                prefixes = [p["prefix"] for p in data.get("data", {}).get("prefixes", [])]

                if prefixes:
                    safe_write(os.path.join(root, "prefixes_ripestat.txt"), "\n".join(prefixes))
                    meta["sources"].append("ripestat")
                    meta["ripe_prefix_count"] = len(prefixes)
                    safe_write(os.path.join(root, "meta.json"), json.dumps(meta, indent=2))
            except Exception as e:
                print(f"[WARN] Failed RIPE check for {asn}: {e}")
