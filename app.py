import streamlit as st
import pandas as pd
from scorer import score_listing
from postcodes import SA_SUBURBS, REGION_NAMES

st.set_page_config(page_title="SA Property Intel", page_icon="🏡", layout="wide")

st.title("🏡 SA Property Intelligence — A-Grade Finder")
st.caption("Greater Adelaide + Lower Fleurieu · Houses · $600k–$900k · 50/50 Growth/Yield")

tab1, tab2 = st.tabs(["🔍 Auto Scanner", "📋 Manual Property Checker"])

with tab1:
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("Screened", "—")
    col2.metric("A-Grade Found", "—")
    col3.metric("Avg Gross Yield", "—")
    col4.metric("Avg Score", "—")
    col5.metric("Stress Test Pass", "—")
    st.info("👈 Set your parameters in the sidebar and click Analyse Properties for the auto scanner.")

    if st.sidebar.button("🔍 Analyse Properties", type="primary"):
        selected_regions = [k for k,v in regions.items() if v]
        filtered = [l for l in DEMO_LISTINGS if
                    l["price"] >= min_price and
                    l["price"] <= max_price and
                    l["bedrooms"] >= min_beds and
                    l["region"] in selected_regions]

        results = []
        for listing in filtered:
            scored = score_listing(listing, rate=rate,
                                  deposit_pct=deposit_pct, years=years)
            if scored and scored["grade"] == "A" and scored["gross_yield"] >= min_yield:
                results.append(scored)

        results.sort(key=lambda x: x["score"], reverse=True)

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
            st.success(f"Found {len(results)} A-grade properties")
            for r in results:
                with st.expander(f"🏆 {r['address']}, {r['suburb']} — Score {r['score']}/100", expanded=True):
                    c1,c2,c3,c4 = st.columns(4)
                    c1.metric("Price", f"${r['price']:,.0f}")
                    c2.metric("Score", f"{r['score']}/100")
                    c3.metric("Gross Yield", f"{r['gross_yield']}%")
                    c4.metric("Net Yield", f"{r['net_yield']}%")
                    col_a,col_b,col_c = st.columns(3)
                    with col_a:
                        st.markdown("**Income**")
                        st.write(f"Gross rent: ${r['gross_annual_rent']:,}")
                        st.write(f"Vacancy: -${r['vacancy_loss']:,}")
                        st.write(f"**Net: ${r['net_rental']:,}**")
                    with col_b:
                        st.markdown("**Expenses**")
                        st.write(f"Agent fees 8%: -${r['mgmt_fee']:,}")
                        st.write(f"Council: -${r['council_rates']:,}")
                        st.write(f"Water: -${r['water']:,}")
                        st.write(f"Insurance: -${r['insurance']:,}")
                        st.write(f"Maintenance: -${r['maintenance']:,}")
                        st.write(f"Land tax: -${r['land_tax']:,}")
                        st.write(f"**Total: -${r['total_expenses']:,}**")
                    with col_c:
                        st.markdown("**Mortgage & Net**")
                        st.write(f"Loan: ${r['loan_amount']:,}")
                        st.write(f"Monthly: ${r['monthly_repayment']:,}")
                        st.write(f"Stamp duty: ${r['stamp_duty']:,}")
                        st.write(f"Cash needed: ${r['total_upfront']:,}")
                        st.write(f"**Weekly net: ${r['weekly_net']:+,.0f}/wk**")
                        st.write(f"Stress ({r['stress_rate']}%): ${r['stress_weekly_net']:+,.0f}/wk")
                    st.markdown(f"[View listing →]({r['url']})")

with tab2:
    st.subheader("📋 Manual Property Checker")
    st.caption("Paste any address or Domain URL — score any property anywhere, anytime")

    st.markdown("### Enter Property Details")

    domain_url = st.text_input(
        "Domain URL (optional)",
        placeholder="https://www.domain.com.au/123-example-street-suburb-sa-2024-123456789"
    )

    col1, col2 = st.columns(2)
    with col1:
        manual_address = st.text_input("Street Address", placeholder="123 Example Street")
        manual_suburb = st.text_input("Suburb", placeholder="Goolwa")
        manual_state = st.selectbox("State", ["SA","VIC","NSW","QLD","WA","TAS","NT","ACT"])
        manual_postcode = st.text_input("Postcode", placeholder="5212")

    with col2:
        manual_price = st.number_input("Asking Price ($)", min_value=100000, max_value=5000000, value=700000, step=10000)
        manual_rent = st.number_input("Estimated Weekly Rent ($)", min_value=100, max_value=5000, value=550, step=10)
        manual_beds = st.selectbox("Bedrooms", [1,2,3,4,5], index=2)
        manual_baths = st.selectbox("Bathrooms", [1,2,3,4], index=1)

    st.markdown("### Suburb Intelligence")
    st.caption("Enter what you know about the suburb — or leave as defaults")

    col3, col4 = st.columns(2)
    with col3:
        manual_growth = st.slider("Est. 5yr Annual Growth (%)", 0.0, 20.0, 7.0, 0.1)
        manual_vacancy = st.slider("Est. Vacancy Rate (%)", 0.0, 10.0, 2.0, 0.1)
    with col4:
        manual_pop_growth = st.slider("Est. Population Growth (%)", 0.0, 10.0, 1.0, 0.1)
        manual_infra = st.checkbox("Infrastructure / development nearby")

    if st.button("⚡ Score This Property", type="primary"):
        if manual_price > 0 and manual_rent > 0:
            from cashflow import calculate

            postcode = manual_postcode if manual_postcode else "5000"
            cf = calculate(
                manual_price, manual_rent, postcode,
                rate=rate, deposit_pct=deposit_pct, years=years
            )

            pts = 0
            g = manual_growth
            pts += 20 if g>=10 else 14 if g>=7 else 8 if g>=5 else 0
            p = manual_pop_growth
            pts += 10 if p>=3 else 6 if p>=1.5 else 2
            pts += 5 if manual_infra else 0
            dom_pts = 5
            pts += dom_pts
            gy = cf["gross_yield"]
            pts += 20 if gy>=6.0 else 12 if gy>=5.0 else 5 if gy>=4.0 else 0
            v = manual_vacancy
            pts += 15 if v<1.5 else 8 if v<3.0 else 0
            pts += 10 if cf["weekly_net"] >= 0 else 0
            pts += 5 if cf["stress_pass"] else 0

            grade = "A" if pts>=80 else "B" if pts>=65 else "C" if pts>=45 else "D"
            grade_color = {"A":"🟢","B":"🔵","C":"🟡","D":"🔴"}

            st.markdown("---")
            st.markdown(f"## {grade_color[grade]} Grade: **{grade}** — Score: **{pts}/100**")

            if grade == "A":
                st.success("🏆 A-Grade — Strong investment prospect. Meets all key criteria.")
            elif grade == "B":
                st.info("👍 B-Grade — Good property but doesn't quite hit A-grade threshold.")
            elif grade == "C":
                st.warning("⚠️ C-Grade — Average. Some metrics below target.")
            else:
                st.error("❌ D-Grade — Does not meet investment criteria.")

            st.markdown("---")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Score", f"{pts}/100")
            c2.metric("Grade", grade)
            c3.metric("Gross Yield", f"{cf['gross_yield']}%")
            c4.metric("Net Yield", f"{cf['net_yield']}%")

            st.markdown("### Full Cash Flow Summary")
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.markdown("**Income**")
                st.write(f"Asking price: ${manual_price:,}")
                st.write(f"Weekly rent: ${manual_rent:,}/wk")
                st.write(f"Gross annual rent: ${cf['gross_annual_rent']:,}")
                st.write(f"Vacancy allowance: -${cf['vacancy_loss']:,}")
                st.write(f"**Net rental income: ${cf['net_rental']:,}**")

            with col_b:
                st.markdown("**Expenses**")
                st.write(f"Agent fees (8%): -${cf['mgmt_fee']:,}")
                st.write(f"Letting fee: -${cf['letting_fee']:,}")
                st.write(f"Council rates: -${cf['council_rates']:,}")
                st.write(f"Water/sewerage: -${cf['water']:,}")
                st.write(f"Landlord insurance: -${cf['insurance']:,}")
                st.write(f"Maintenance: -${cf['maintenance']:,}")
                st.write(f"Land tax: -${cf['land_tax']:,}")
                st.write(f"**Total expenses: -${cf['total_expenses']:,}**")

            with col_c:
                st.markdown("**Mortgage & Net**")
                st.write(f"Deposit ({int(deposit_pct*100)}%): ${int(manual_price*deposit_pct):,}")
                st.write(f"Loan amount: ${cf['loan_amount']:,}")
                st.write(f"Interest rate: {rate*100:.1f}%")
                st.write(f"Monthly repayment: ${cf['monthly_repayment']:,}")
                st.write(f"Annual mortgage: -${cf['annual_mortgage']:,}")
                st.write(f"Stamp duty: ${cf['stamp_duty']:,}")
                st.write(f"**Total cash needed: ${cf['total_upfront']:,}**")
                wn = cf['weekly_net']
                color = "green" if wn >= 0 else "red"
                st.markdown(f"**Weekly net CF: :{color}[${wn:+,.0f}/wk]**")
                swn = cf['stress_weekly_net']
                st.write(f"Stress test ({cf['stress_rate']}%): ${swn:+,.0f}/wk")
                stress = "✅ PASS" if cf['stress_pass'] else "⚠️ MARGINAL"
                st.write(f"Stress result: {stress}")

            st.markdown("### Score Breakdown")
            col_e, col_f = st.columns(2)
            with col_e:
                st.markdown("**Growth Signals**")
                st.write(f"5yr growth ({manual_growth}%): {20 if g>=10 else 14 if g>=7 else 8 if g>=5 else 0} pts")
                st.write(f"Population growth ({manual_pop_growth}%): {10 if p>=3 else 6 if p>=1.5 else 2} pts")
                st.write(f"Infrastructure nearby: {5 if manual_infra else 0} pts")
                st.write(f"Days on market bonus: 5 pts")
            with col_f:
                st.markdown("**Yield Signals**")
                st.write(f"Gross yield ({gy}%): {20 if gy>=6.0 else 12 if gy>=5.0 else 5 if gy>=4.0 else 0} pts")
                st.write(f"Vacancy rate ({manual_vacancy}%): {15 if v<1.5 else 8 if v<3.0 else 0} pts")
                st.write(f"Positive cash flow: {10 if cf['weekly_net']>=0 else 0} pts")
                st.write(f"Stress test pass: {5 if cf['stress_pass'] else 0} pts")

            if domain_url:
                st.markdown(f"[View on Domain →]({domain_url})")
        else:
            st.error("Please enter a price and weekly rent estimate.")
