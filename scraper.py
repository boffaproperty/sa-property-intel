import requests
import re
import time
import json
from bs4 import BeautifulSoup
from postcodes import SA_SUBURBS

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def parse_price(price_str):
    if not price_str:
        return None
    nums = re.findall(r"\d+", str(price_str).replace(",", ""))
    if not nums:
        return None
    price = int(nums[0])
    if price < 100000:
        return None
    return float(price)

def scrape_suburb(postcode, suburb_name, min_price=600000,
                  max_price=900000, min_beds=3):
    slug = suburb_name.lower().replace(" ", "-")
    url = (
        f"https://www.realestate.com.au/buy/property-house"
        f"/in-{slug},+sa+{postcode}/"
        f"?minprice={min_price}&maxprice={max_price}"
        f"&minbedrooms={min_beds}&propertytype=house"
        f"&sortType=date-desc"
    )
    listings = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return listings
        soup = BeautifulSoup(resp.text, "html.parser")
        scripts = soup.find_all("script", type="application/json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                props = data.get("props", {}).get("pageProps", {}).get("componentProps", {}).get("listingsMap", {})
                for lid, prop in props.items():
                    try:
                        price_data = prop.get("price", {})
                        price = parse_price(
                            price_data.get("value") or
                            price_data.get("display", "")
                        )
                        if not price:
                            continue
                        if price < min_price or price > max_price:
                            continue
                        features = prop.get("generalFeatures", {})
                        beds = int(features.get("bedrooms", {}).get("value", 0))
                        if beds < min_beds:
                            continue
                        address_data = prop.get("address", {}).get("display", {})
                        address = address_data.get("shortAddress", "")
                        listings.append({
                            "listing_id": f"rea-{lid}",
                            "address": address,
                            "suburb": suburb_name,
                            "postcode": postcode,
                            "region": SA_SUBURBS[postcode]["region"],
                            "price": price,
                            "bedrooms": beds,
                            "bathrooms": int(features.get("bathrooms", {}).get("value", 0)),
                            "car_spaces": int(features.get("parkingSpaces", {}).get("value", 0)),
                            "days_on_market": prop.get("daysListed", 0) or 0,
                            "url": f"https://www.realestate.com.au{prop.get('listingSlug', '')}",
                        })
                    except:
                        continue
            except:
                continue
    except Exception as e:
        print(f"Error scraping {suburb_name}: {e}")
    return listings

def scrape_all(min_price=600000, max_price=900000,
               min_beds=3, regions=None):
    all_listings = []
    suburbs = {
        pc: data for pc, data in SA_SUBURBS.items()
        if regions is None or data["region"] in regions
    }
    total = len(suburbs)
    for i, (postcode, data) in enumerate(suburbs.items()):
        suburb_name = data["name"]
        print(f"Scraping {suburb_name} ({i+1}/{total})...")
        listings = scrape_suburb(
            postcode, suburb_name, min_price, max_price, min_beds
        )
        print(f"  Found {len(listings)} listings")
        all_listings.extend(listings)
        time.sleep(3)
    print(f"\nTotal listings scraped: {len(all_listings)}")
    return all_listings
