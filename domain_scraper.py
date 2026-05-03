import requests
import time
from postcodes import SA_SUBURBS

API_KEY = "key_f1fd96340f3691ca2413e3061a11656b"
BASE_URL = "https://api.domain.com.au/v1"
HEADERS = {
    "X-Api-Key": API_KEY,
    "Accept": "application/json",
}

def search_listings(suburb, state="SA", min_price=600000,
                    max_price=900000, min_beds=3):
    url = f"{BASE_URL}/listings/residential/_search"
    payload = {
        "listingType": "Sale",
        "propertyTypes": ["House"],
        "locations": [{"state": state, "suburb": suburb}],
        "minBedrooms": min_beds,
        "minPrice": min_price,
        "maxPrice": max_price,
        "pageSize": 50,
    }
    try:
        resp = requests.post(url, json=payload,
                            headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"  API error {resp.status_code} for {suburb}")
            return []
        return resp.json()
    except Exception as e:
        print(f"  Error {suburb}: {e}")
        return []

def get_rental_estimate(suburb, state="SA", beds=3):
    url = f"{BASE_URL}/listings/residential/_search"
    payload = {
        "listingType": "Rent",
        "propertyTypes": ["House"],
        "locations": [{"state": state, "suburb": suburb}],
        "minBedrooms": beds,
        "maxBedrooms": beds,
        "pageSize": 20,
    }
    try:
        resp = requests.post(url, json=payload,
                            headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        rents = []
        for listing in data:
            price = listing.get("listing", {}).get(
                "priceDetails", {}).get("price")
            if price and price > 100:
                rents.append(price)
        if rents:
            return sorted(rents)[len(rents)//2]
        return None
    except:
        return None

def parse_listing(item, postcode, suburb, region):
    try:
        listing = item.get("listing", {})
        price_details = listing.get("priceDetails", {})
        price = price_details.get("price")
        if not price or price < 100000:
            return None
        prop_details = listing.get("propertyDetails", {})
        beds = int(prop_details.get("bedrooms", 0) or 0)
        address_parts = prop_details.get("displayableAddress", "")
        listing_id = f"domain-{listing.get('id', '')}"
        url = f"https://www.domain.com.au/{listing.get('listingSlug', '')}"
        date_listed = listing.get("dateListed", "")
        return {
            "listing_id": listing_id,
            "address": address_parts,
            "suburb": suburb,
            "postcode": postcode,
            "region": region,
            "price": float(price),
            "bedrooms": beds,
            "bathrooms": int(prop_details.get("bathrooms", 0) or 0),
            "car_spaces": int(prop_details.get("carspaces", 0) or 0),
            "land_size": prop_details.get("landArea"),
            "days_on_market": 0,
            "url": url,
            "date_listed": date_listed,
        }
    except:
        return None

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
        region = data["region"]
        print(f"Searching {suburb_name} ({i+1}/{total})...")
        raw = search_listings(
            suburb_name, min_price=min_price,
            max_price=max_price, min_beds=min_beds
        )
        count = 0
        for item in raw:
            parsed = parse_listing(item, postcode, suburb_name, region)
            if parsed:
                if not parsed.get("days_on_market"):
                    rent = get_rental_estimate(suburb_name, beds=min_beds)
                    if rent:
                        parsed["weekly_rent_override"] = rent
                all_listings.append(parsed)
                count += 1
        print(f"  Found {count} listings")
        time.sleep(1)
    print(f"\nTotal listings found: {len(all_listings)}")
    return all_listings
