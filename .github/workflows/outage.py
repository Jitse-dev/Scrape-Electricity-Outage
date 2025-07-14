"""
scrape outage from the electricity company

Run Github action on schedule 

Send notification to phone when there
   is an outage
"""

import requests
from bs4 import BeautifulSoup
import re
import json

# Step 1: Get region codes from the main page
MAIN_URL = "https://info.ermzapad.bg/webint/vok/avplan.php"
session = requests.Session()
resp = session.get(MAIN_URL)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, "html.parser")

# Try to find region codes from divs with id attributes (e.g., id="MON")
region_divs = soup.find_all('div', id=True)
region_codes = set()
for div in region_divs:
    code = div.get('id')
    # Region codes are usually 3 uppercase letters
    if code and re.fullmatch(r'[A-Z]{3}', code):
        region_codes.add(code)

# If not found, use known codes as fallback
if not region_codes:
    region_codes = {"SOF", "SFO", "PER", "KNL", "BLG", "PVN", "LOV", "VRC", "MON", "VID"}

# Step 2: For each region, POST and get JSON
OUTAGES = []

for region in region_codes:
    post_url = MAIN_URL
    # Use dummy lat/lon (the backend seems to accept any values)
    data = {
        'action': 'draw',
        'gm_obstina': 'MON29',
        'lat': '42.7',
        'lon': '23.3'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (compatible; Python script)'
    }
    r = session.post(post_url, data=data, headers=headers)
    print(r.type)
    try:
        outages_json = r.json()
    except Exception:
        continue  # skip if not valid json

    #print(outages_json)

    # Step 3: Extract villages with outages
    for key, val in outages_json.items():
        # Some entries may be empty
        if not isinstance(val, dict):
            continue
        city = val.get('city_name') or val.get('cities')
        if city and city.strip():
            OUTAGES.append({
                'region': region,
                'village': city.strip(),
                'type': val.get('typedist', '').strip(),
                'begin': val.get('begin_event', '').strip(),
                'end': val.get('end_event', '').strip()
            })

# Step 4: Print as JSON
with open("outages.json", "w", encoding="utf-8") as f:
    json.dump(OUTAGES, f, ensure_ascii=False, indent=2)
