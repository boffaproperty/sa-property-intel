import streamlit as st
import pandas as pd
from scorer import score_listing
from postcodes import SA_SUBURBS, REGION_NAMES

st.set_page_config(page_title="SA Property Intel", page_icon="🏡", layout="wide")

st.title("🏡 SA Property Intelligence — A-Grade Finder")
st.caption("Greater Adelaide + Lower Fleurieu · Houses · $600k–$900k · 50/50 Growth/Yield")

# Sidebar
st.sidebar.header("Search Parameters")
min_price = st.sidebar.number_input("Min Price ($)", value=600000, step=10000)
max_price = st.sidebar.number_input("Max Price ($)", value=900000, step=10000)
min_beds = st.sidebar.selectbox("Min Bedrooms", [2,3,4], index=1)
min_yield = st.sidebar.slider("Min Gross Yield (%)", 3.0, 7.0, 4.0, 0.1)

st.sidebar.header("Regions")
regions = {}
for key, name in REGION_NAMES.items():
    regions[key] = st.sidebar.checkbox(name, value=True)

st.sidebar.header("Finance")
deposit_pct = st.sidebar.slider("Deposit (%)", 10, 40, 20) / 100
rate = st.sidebar.slider("Interest Rate (%)", 4.5, 8.5, 6.5, 0.1) / 100
years = st.sidebar.selectbox("Loan Term (years)", [25, 30], index=1)

# Demo listings
DEMO_LISTINGS = [
    {"address":"12 Caernarvon Crescent","suburb":"Salisbury","postcode":"5108","region":"north","price":618000,"bedrooms":4,"days_on_market":6,"url":"https://realestate.com.au"},
    {"address":"7 Edison Drive","suburb":"Mawson Lakes","postcode":"5095","region":"north","price":655000,"bedrooms":4,"days_on_market":5,"url":"https://realestate.com.au"},
    {"address":"3 McFarlane Street","suburb":"Elizabeth","postcode":"5112","region":"north","price":620000,"bedrooms":3,"days_on_market":4,"url":"https://realestate.com.au"},
    {"address":"26 Seaford Rise","suburb":"Seaford","postcode":"5163","region":"south","price":658000,"bedrooms":4,"days_on_market":7,"url":"https://realestate.com.au"},
    {"address":"14 Marlin Drive","suburb":"Christies Beach","postcode":"5161","region":"south","price":672000,"bedrooms":3,"days_on_market":9,"url":"https://realestate.com.au"},
    {"address":"22 McCracken Drive","suburb":"Goolwa","postcode":"5212","region":"fleurieu","price":618000,"bedrooms":3,"days_on_market":21,"url":"https://realestate.com.au"},
    {"address":"7 Waitpinga Crescent","suburb":"Encounter Bay","postcode":"5210","region":"fleurieu","price":682000,"bedrooms":3,"days_on_market":8,"url":"https://realestate.com.au"},
    {"address":"18 Ascot Avenue","suburb":"Goodwood","postcode":"5034","region":"inner","price":785000,"bedrooms":3,"days_on_market":9,"url":"https://realestate.com.au"},
    {"address":"31 Trimmer Parade","suburb":"Seaton","postcode":"5024","region":"west","price":710000,"bedrooms":3,"days_on_market":14,"url":"https://realestate.com.au"},
    {"address":"24 Humbug Scrub Road","suburb":"Angle Vale","postcode":"5116","region":"north","price":680000,"bedrooms":4,"days_on_market":8,"url":"https://realestate.com.au"},
    {"address":"55 Lyndoch Road","suburb":"Gawler","postcode":"5114","region":"north","price":648000,"bedrooms":4,"days_on_market":12,"url":"https://realestate.com.au"},
    {"address":"45 Strathalbyn Road","suburb":"Strathalbyn","postcode":"5201","region":"fleurieu","price":635000,"bedrooms":4,"days_on_market":18,"url":"https://realestate.com.au"},
]

if st.sidebar.button("🔍 Analyse Properties", type="primary"):
    selected_regions = [k for k,v in regions.items() if v]
    filtered = [l for l in DEMO_LISTINGS if
                l["price"] >= min_price and
                l["price"] <= max_price and
                l["bedrooms"] >= min_beds and
                l["region"] in selected_regions]

    results = []
    for listing in filtered:
        scored = score_listing(listing, rate=rate, deposit_pct=deposit_pct, years=years)
        if scored and scored["grade"] == "A" and scored["gross_yield"] >= min_yield:
            results.append(scored)

    results.sort(key=lambda x: x["score"], reverse=True)

    # Summary metrics
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("Screened", len(filtered))
    col2.metric("A-Grade Found", len(results))
    avg_yield = round(sum(r["gross_yield"] for r in results)/len(results),2) if results else 0
    col3.metric("Avg Gross Yield", f"{avg_yield}%")
    avg_score = round(sum(r["score"] for r in results)/len(results)) if results else 0
    col4.metric("Avg Score", f"{avg_score}/100")
    passes = sum(1 for r in results if r["stress_pass"])
    col5.metric("Stress Test Pass", f"{passes}/{len(results)}")

    if not results:
        st.warning("No A-grade properties found. Try adjusting your filters.")
    else:
        st.success(f"Found {len(results)} A-grade properties — showing best first")

        for r in results:
            with st.expander(f"🏆 {r['address']}, {r['suburb']} — Score {r['score']}/100 · {r['gross_yield']}% yield · {'✅ Stress PASS' if r['stress_pass'] else '⚠️ Stress MARGINAL'}", expanded=True):

                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Price", f"${r['price']:,.0f}")
                c2.metric("Score", f"{r['score']}/100 A-Grade")
                c3.metric("Gross Yield", f"{r['gross_yield']}%")
                c4.metric("Net Yield", f"{r['net_yield']}%")

                st.markdown("**Cash Flow Summary**")
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.markdown("**Income**")
                    st.write(f"Gross rent: ${r['gross_annual_rent']:,}")
                    st.write(f"Vacancy (2wks): -${r['vacancy_loss']:,}")
                    st.write(f"**Net rental: ${r['net_rental']:,}**")

                with col_b:
                    st.markdown("**Expenses**")
                    st.write(f"Agent fees (8%): -${r['mgmt_fee']:,}")
                    st.write(f"Council rates: -${r['council_rates']:,}")
                    st.write(f"Water: -${r['water']:,}")
                    st.write(f"Insurance: -${r['insurance']:,}")
                    st.write(f"Maintenance: -${r['maintenance']:,}")
                    st.write(f"Land tax: -${r['land_tax']:,}")
                    st.write(f"**Total: -${r['total_expenses']:,}**")

                with col_c:
                    st.markdown("**Mortgage & Net**")
                    st.write(f"Loan: ${r['loan_amount']:,}")
                    st.write(f"Monthly repayment: ${r['monthly_repayment']:,}")
                    st.write(f"Stamp duty: ${r['stamp_duty']:,}")
                    st.write(f"Cash needed: ${r['total_upfront']:,}")
                    wn = r['weekly_net']
                    st.write(f"**Weekly net: ${wn:+,.0f}/wk**")
                    swn = r['stress_weekly_net']
                    st.write(f"Stress ({r['stress_rate']}%): ${swn:+,.0f}/wk")

                st.markdown(f"[View on realestate.com.au →]({r['url']})")
else:
    st.info("👈 Set your parameters in the sidebar and click Analyse Properties")
