# ASN Scraper Project

A production-ready Python tool to scrape and validate ASNs and IP prefixes.

---

## 🚀 Features

- Fetch all ASNs from **Potaroo**
- Filter by **country** or **specific ASNs**
- Validate prefixes via **RIPEstat** and **RouteViews**
- Saves data in structured folders
- Progress tracking in `progress.json`
- Error-safe, auto-resumable

---

## 🧩 Installation

```bash
git clone https://github.com/yourname/asn_scraper.git
cd asn_scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
