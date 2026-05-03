from cashflow import calculate
from postcodes import SUBURB_INTEL, DEFAULT_INTEL

RENT_ESTIMATES = {
    "5000":{3:650,4:800}, "5006":{3:700,4:850},
    "5034":{3:680,4:820}, "5041":{3:620,4:750},
    "5045":{3:700,4:850}, "5082":{3:650,4:780},
    "5095":{3:620,4:750}, "5108":{3:520,4:630},
    "5112":{3:480,4:580}, "5114":{3:540,4:650},
    "5116":{3:560,4:670}, "5117":{3:520,4:620},
    "5161":{3:590,4:710}, "5163":{3:600,4:720},
    "5170":{3:610,4:730}, "5171":{3:580,4:700},
    "5172":{3:560,4:680}, "5201":{3:520,4:630},
    "5210":{3:590,4:710}, "5211":{3:620,4:750},
    "5212":{3:570,4:690}, "5213":{3:640,4:770},
    "5015":{3:580,4:700}, "5019":{3:600,4:720},
    "5021":{3:650,4:780}, "5022":{3:640,4:770},
    "5024":{3:610,4:730},
}

DEFAULT_RENT = {3:550, 4:660}

def get_rent(postcode, beds):
    beds = min(max(int(beds), 3), 4)
    return RENT_ESTIMATES.get(postcode, DEFAULT_RENT)[beds]

def score_listing(listing, rate=0.065, deposit_pct=0.20, years=30):
    postcode = str(listing.get("postcode",""))
    price = float(listing.get("price", 0))
    beds = int(listing.get("bedrooms", 3))

    if price <= 0:
        return None

    intel = SUBURB_INTEL.get(postcode, DEFAULT_INTEL)
    weekly_rent = get_rent(postcode, beds)
    cf = calculate(price, weekly_rent, postcode, rate, deposit_pct, years)

    pts = 0

    # Growth signals (50 pts)
    g = intel["growth"]
    pts += 20 if g >= 10 else 14 if g >= 7 else 8 if g >= 5 else 0
    p = intel["pop"]
    pts += 10 if p >= 3 else 6 if p >= 1.5 else 2
    median = intel["median"] or price
    pts += 10 if price < median*0.93 else 5 if price < median*0.98 else 0
    dom = int(listing.get("days_on_market", 30))
    pts += 5 if dom < 15 else 2 if dom < 30 else 0
    pts += 5 if intel["infra"] else 0

    # Yield signals (50 pts)
    gy = cf["gross_yield"]
    pts += 20 if gy >= 6.0 else 12 if gy >= 5.0 else 5 if gy >= 4.0 else 0
    v = intel["vacancy"]
    pts += 15 if v < 1.5 else 8 if v < 3.0 else 0
    pts += 10 if cf["weekly_net"] >= 0 else 0
    pts += 5 if cf["stress_pass"] else 0

    grade = "A" if pts >= 80 else "B" if pts >= 65 else "C" if pts >= 45 else "D"

    return {
        **listing,
        **cf,
        "score": pts,
        "grade": grade,
        "weekly_rent_est": weekly_rent,
        "suburb_name": listing.get("suburb",""),
        "growth_5yr": g,
        "vacancy_rate": v,
    }
