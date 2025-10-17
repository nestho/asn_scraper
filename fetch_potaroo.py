import os
import json
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from utils import clean_asn, safe_write, get_country_asns


POTAROO_ASN_URL = "https://bgp.potaroo.net/cidr/autnums.html"
POTAROO_CIDR_BASE = "https://bgp.potaroo.net/cidr/autnums/{asn}.html"


def fetch_asn_data(output_dir="output", country=None, asn_list=None):
    os.makedirs(output_dir, exist_ok=True)
    report = {"country": country, "processed": 0, "success": 0,
              "failed": 0, "asns": []}

    print(f"🌍 Fetching ASN list from Potaroo...")
    resp = requests.get(POTAROO_ASN_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    asn_tags = soup.find_all("a")
    all_asns = [clean_asn(a.text) for a in asn_tags if "AS" in a.text]

    # Filter
    if country:
        country_asns = get_country_asns(country)
        all_asns = [a for a in all_asns if a in country_asns]
        root_dir = os.path.join(output_dir, country.upper())
    elif asn_list:
        all_asns = [clean_asn(a) for a in asn_list.split(",")]
        root_dir = output_dir
    else:
        root_dir = output_dir

    os.makedirs(root_dir, exist_ok=True)

    print(f"🔍 Fetching prefix data for {len(all_asns)} ASNs...")
    for asn in tqdm(all_asns, desc="Fetching prefixes"):
        folder = os.path.join(root_dir, f"AS{asn}")
        os.makedirs(folder, exist_ok=True)
        try:
            prefix_url = POTAROO_CIDR_BASE.format(asn=asn)
            r = requests.get(prefix_url, timeout=20)
            r.raise_for_status()
            html = BeautifulSoup(r.text, "html.parser")
            prefixes = [x.text.strip()
                        for x in html.find_all("tt") if "/" in x.text]

            safe_write(os.path.join(folder, "prefixes_potaroo.txt"),
                       "\n".join(prefixes))

            meta = {
                "asn": f"AS{asn}",
                "country": country,
                "prefix_count": len(prefixes),
                "sources": ["potaroo"],
            }
            safe_write(os.path.join(folder, "meta.json"),
                       json.dumps(meta, indent=2))

            report["success"] += 1
            report["asns"].append(meta)
        except Exception as e:
            print(f"[ERROR] Failed for AS{asn}: {e}")
            report["failed"] += 1
        report["processed"] += 1

    safe_write(os.path.join(root_dir, "report.json"),
               json.dumps(report, indent=2))
    print(f"✅ Done! Saved {report['success']} ASNs in {root_dir}")
