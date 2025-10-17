# ASN Scraper

Fetch and validate Autonomous System (AS) prefixes from Potaroo, RIPEstat, and RouteViews.

---

## 🚀 Features
- Fetch ASNs and prefixes from Potaroo
- Filter by country or specific ASN list
- Cross-check prefixes with RIPEstat & RouteViews
- Organized per-AS folder output
- Automatic progress tracking in `progress.json`

---

## ⚙️ Installation
```bash
git clone https://github.com/nestho/asn_scraper.git
cd asn_scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
