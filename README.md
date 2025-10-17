# ASN Scraper & Validator

This project fetches IP prefix announcements for Autonomous Systems (ASNs) from multiple sources (Potaroo, RIPEstat, RouteViews / CAIDA), compares them, and reports discrepancies.

## Installation

```bash
git clone <repo_url>
cd asn_scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
