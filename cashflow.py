FLEURIEU = {"5171","5172","5173","5174","5201","5203","5204","5210","5211","5212","5213","5214"}
NORTHERN = {"5112","5113","5114","5115","5116","5117","5118","5120"}

EXPENSES = {
    "metro":{"council":0.0038,"water":0.0010,"insurance":0.0014,"maintenance":0.0075,"land_tax":0.0018},
    "fleurieu":{"council":0.0032,"water":0.0012,"insurance":0.0018,"maintenance":0.0090,"land_tax":0.0015},
    "northern":{"council":0.0035,"water":0.0010,"insurance":0.0013,"maintenance":0.0080,"land_tax":0.0012},
}

MGMT_FEE = 0.08
VACANCY_WEEKS = 2
STRESS_ADD = 0.005
SA_STAMP = 0.055
LEGALS = 0.018

def get_profile(postcode):
    if postcode in FLEURIEU:
        return EXPENSES["fleurieu"]
    if postcode in NORTHERN:
        return EXPENSES["northern"]
    return EXPENSES["metro"]

def monthly_pi(loan, rate, years):
    r = rate / 12
    n = years * 12
    return loan * (r * (1+r)**n) / ((1+r)**n - 1)

def calculate(price, weekly_rent, postcode, rate=0.065, deposit_pct=0.20, years=30):
    exp = get_profile(postcode)
    deposit = price * deposit_pct
    stamp = price * SA_STAMP
    legals = price * LEGALS
    total_upfront = deposit + stamp + legals
    loan = price - deposit

    gross_annual = weekly_rent * 52
    vacancy_loss = weekly_rent * VACANCY_WEEKS
    net_rental = gross_annual - vacancy_loss

    mgmt = net_rental * MGMT_FEE
    letting = weekly_rent * 1.1
    council = price * exp["council"]
    water = price * exp["water"]
    insurance = price * exp["insurance"]
    maintenance = price * exp["maintenance"]
    land_tax = price * exp["land_tax"]
    total_exp = mgmt+letting+council+water+insurance+maintenance+land_tax

    mth_std = monthly_pi(loan, rate, years)
    ann_mortgage = mth_std * 12
    mth_stress = monthly_pi(loan, rate+STRESS_ADD, years)
    ann_stress = mth_stress * 12

    ann_net = net_rental - total_exp - ann_mortgage
    ann_net_stress = net_rental - total_exp - ann_stress

    gross_yield = (gross_annual / price) * 100
    net_yield = ((net_rental - total_exp) / price) * 100

    return {
        "gross_annual_rent": round(gross_annual),
        "vacancy_loss": round(vacancy_loss),
        "net_rental": round(net_rental),
        "mgmt_fee": round(mgmt),
        "letting_fee": round(letting),
        "council_rates": round(council),
        "water": round(water),
        "insurance": round(insurance),
        "maintenance": round(maintenance),
        "land_tax": round(land_tax),
        "total_expenses": round(total_exp),
        "loan_amount": round(loan),
        "monthly_repayment": round(mth_std),
        "annual_mortgage": round(ann_mortgage),
        "stamp_duty": round(stamp),
        "total_upfront": round(total_upfront),
        "annual_net": round(ann_net),
        "weekly_net": round(ann_net/52, 2),
        "stress_rate": round((rate+STRESS_ADD)*100, 2),
        "stress_weekly_net": round(ann_net_stress/52, 2),
        "stress_pass": ann_net_stress >= -2600,
        "gross_yield": round(gross_yield, 2),
        "net_yield": round(net_yield, 2),
    }
