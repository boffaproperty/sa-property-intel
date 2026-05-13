import re
import json
import time
import random
from scrapfly import ScrapflyClient, ScrapeConfig
from postcodes import SA_SUBURBS

SCRAPFLY_KEY = "scp-live-318dbdd64ce448e09b236c5928b005e4"
client = ScrapflyClient(key=SCRAPFLY_KEY)

def search_suburb(suburb_name, postcode, min_price=600000,
                  max_price=900000, min_beds=3):
    slug = suburb_name.lower().replace(" ", "-")
url = (
    f"https://www.realestate.com.au/buy/"
    f"property-house-between-{min_price}-{max_price}-"
    f"in-{slug},+sa+{postcode}/"
    f"?minbedrooms={min_beds}"
    f"&propertytype=house"
    f"&sortType=date-desc"
)
    try:
        result = client.scrape(ScrapeConfig(
            url=url,
            asp=True,
            country="AU",
            headers={
                "Accept-Language": "en-AU,en;q=0.9",
            }
        ))
        html = result.content
        listings = parse_listings(html, postcode, suburb_name)
        return listings
    except Exception as e:
        print(f"  ScrapFly error for {suburb_name}: {e}")
        return []

def parse_listings(html, postcode, suburb_name):
    listings = []
    try:
        pattern = r'window\.ArgonautExchange\s*=\s*(\{.+?\})(?=;\s*window\.|$)'
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            pattern2 = r'"listingsMap"\s*:\s*(\{[^}]+(?:\{[^}]*\}[^}]*)*\})'
            match = re.search(pattern2, html, re.DOTALL)
            if not match:
                return listings

        raw = match.group(1)
        try:
            data = json.loads(raw)
        except:
            return listings

        listings_map = None
        if "listingsMap" in data:
            listings_map = data["listingsMap"]
        else:
            for key in data:
                if isinstance(data[key], dict):
                    if "listingsMap" in data[key]:
                        listings_map = data[key]["listingsMap"]
                        break
                    if isinstance(data[key], dict):
                        for subkey in data[key]:
                            if subkey == "listingsMap":
                                listings_map = data[key][subkey]
                                break

        if not listings_map:
            return listings

        for lid, prop in listings_map.items():
            try:
                price_data = prop.get("price", {})
                price_val = price_data.get("value")
                price_display = price_data.get("display", "")

                if not price_val:
                    nums = re.findall(r"\d+",
                        str(price_display).replace(",", ""))
                    price_val = float(nums[0]) if nums else None

                if not price_val:
                    continue

                price_val = float(price_val)
                if price_val < 100000:
                    continue

                features = prop.get("generalFeatures", {})
                beds = int(features.get("bedrooms", {}).get("value", 0) or 0)
                address_data = prop.get("address", {}).get("display", {})
                address = address_data.get("shortAddress", "")
                land_size = prop.get("landSize", {})
                if isinstance(land_size, dict):
                    land_m2 = land_size.get("value")
                else:
                    land_m2 = None

                region = SA_SUBURBS.get(postcode, {}).get("region", "unknown")

                listings.append({
                    "listing_id": f"rea-{lid}",
                    "address": address,
                    "suburb": suburb_name,
                    "postcode": postcode,
                    "region": region,
                    "price": price_val,
                    "bedrooms": beds,
                    "bathrooms": int(
                        features.get("bathrooms", {}).get("value", 0) or 0),
                    "car_spaces": int(
                        features.get("parkingSpaces", {}).get("value", 0) or 0),
                    "land_size": land_m2,
                    "days_on_market": prop.get("daysListed", 0) or 0,
                    "url": f"https://www.realestate.com.au{prop.get('listingSlug', '')}",
                })
            except Exception as e:
                continue

    except Exception as e:
        print(f"  Parse error: {e}")

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
        print(f"Searching {suburb_name} ({i+1}/{total})...")
        listings = search_suburb(
            suburb_name, postcode,
            min_price=min_price,
            max_price=max_price,
            min_beds=min_beds,
        )
        print(f"  Found {len(listings)} listings")
        all_listings.extend(listings)
        delay = random.uniform(3, 6)
        time.sleep(delay)

    print(f"\nTotal listings found: {len(all_listings)}")
    return all_listings
