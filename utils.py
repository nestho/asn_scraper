import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path


def clean_asn(text):
    return text.replace("AS", "").strip()


def safe_write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


def get_country_asns(country_code):
    """
    Pull ASNs for a specific country from Potaroo's country table.
    """
    url = "https://bgp.potaroo.net/cidr/country_table.html"
    resp = requests.get(url, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")

    anchor = soup.find("a", {"name": country_code.upper()})
    if not anchor:
        print(f"[WARN] No country data found for {country_code}")
        return []

    table = anchor.find_next("pre")
    if not table:
        return []

    asns = []
    for line in table.text.splitlines():
        if line.strip().startswith("AS"):
            asns.append(line.split()[0].replace("AS", ""))
    return asns
