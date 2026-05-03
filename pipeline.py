import sqlite3, smtplib, time, schedule, logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from scorer import score_listing
from postcodes import SA_SUBURBS
from domain_scraper import scrape_all

logging.basicConfig(
    filename='/opt/sa-property/data/logs/pipeline.log',
    level=logging.INFO,
    format='%(asctime)s %(message)s'
)

CONFIG = {
    "min_price": 600000,
    "max_price": 900000,
    "min_beds": 3,
    "rate": 0.065,
    "deposit": 0.20,
    "years": 30,
    "smtp_user": "mboffa53@gmail.com",
    "smtp_pass": "uwbb cllk llox plsd",
    "alert_email": "mboffa53@gmail.com",
    "db": "/opt/sa-property/data/properties.db",
}

def init_db():
    con = sqlite3.connect(CONFIG["db"])
    con.execute("""CREATE TABLE IF NOT EXISTS seen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id TEXT UNIQUE,
        address TEXT,
        suburb TEXT,
        postcode TEXT,
        price REAL,
        score INTEGER,
        gross_yield REAL,
        weekly_net REAL,
        stress_pass INTEGER,
        found_at TEXT
    )""")
    con.commit()
    return con

def is_new(listing_id):
    con = sqlite3.connect(CONFIG["db"])
    row = con.execute(
        "SELECT 1 FROM seen WHERE listing_id=?", (listing_id,)
    ).fetchone()
    con.close()
    return row is None

def save_listing(r):
    con = sqlite3.connect(CONFIG["db"])
    con.execute("""INSERT OR IGNORE INTO seen
        (listing_id,address,suburb,postcode,price,
         score,gross_yield,weekly_net,stress_pass,found_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)""", (
        r.get("listing_id",""),
        r.get("address",""),
        r.get("suburb",""),
        r.get("postcode",""),
        r.get("price",0),
        r.get("score",0),
        r.get("gross_yield",0),
        r.get("weekly_net",0),
        int(r.get("stress_pass",False)),
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ))
    con.commit()
    con.close()

def send_email(properties):
    body = "<h2>🏡 New A-Grade Properties Found</h2>"
    for r in properties:
        stress = "✅ PASS" if r["stress_pass"] else "⚠️ MARGINAL"
        body += f"""
        <div style="border:1px solid #d4c9b5;border-radius:8px;
                    padding:16px;margin:12px 0;font-family:sans-serif">
            <h3 style="margin:0 0 4px">{r['address']}</h3>
            <p style="color:#888;margin:0 0 12px">
                {r['suburb']}, SA {r['postcode']}
            </p>
            <table style="width:100%;border-collapse:collapse;font-size:14px">
                <tr>
                    <td><b>Price</b></td>
                    <td>${r['price']:,.0f}</td>
                    <td><b>Score</b></td>
                    <td>{r['score']}/100 — A Grade</td>
                </tr>
                <tr>
                    <td><b>Gross Yield</b></td>
                    <td>{r['gross_yield']}%</td>
                    <td><b>Net Yield</b></td>
                    <td>{r['net_yield']}%</td>
                </tr>
                <tr>
                    <td><b>Weekly Net CF</b></td>
                    <td>${r['weekly_net']:+,.0f}/wk</td>
                    <td><b>Stress Test</b></td>
                    <td>{stress} at {r['stress_rate']}%</td>
                </tr>
                <tr>
                    <td><b>Est. Rent</b></td>
                    <td>${r['weekly_rent_est']}/wk</td>
                    <td><b>Cash Needed</b></td>
                    <td>${r['total_upfront']:,.0f}</td>
                </tr>
            </table>
            <a href="{r.get('url','https://realestate.com.au')}"
               style="display:inline-block;margin-top:10px;
                      color:#1d4e89;font-weight:bold">
                View on realestate.com.au →
            </a>
        </div>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏡 SA Property Alert — {len(properties)} New A-Grade Found"
    msg["From"] = CONFIG["smtp_user"]
    msg["To"] = CONFIG["alert_email"]
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(CONFIG["smtp_user"], CONFIG["smtp_pass"])
        s.send_message(msg)
    logging.info(f"Email sent — {len(properties)} properties")

def get_listings():
    print("Scraping live listings...")
    return scrape_all(
        min_price=600000,
        max_price=900000,
        min_beds=3,
    )

def run_scan():
    logging.info("Scan started")
    init_db()
    new_a_grade = []

    for listing in get_listings():
        if not is_new(listing["listing_id"]):
            continue
        scored = score_listing(
            listing,
            rate=CONFIG["rate"],
            deposit_pct=CONFIG["deposit"],
            years=CONFIG["years"],
        )
        if scored and scored["grade"] == "A":
            save_listing(scored)
            new_a_grade.append(scored)
            logging.info(f"A-Grade found: {scored['address']} — {scored['score']}/100")

    if new_a_grade:
        send_email(new_a_grade)
        logging.info(f"Scan complete — {len(new_a_grade)} new A-grade alerts sent")
    else:
        logging.info("Scan complete — no new A-grade properties")

if __name__ == "__main__":
    logging.info("Pipeline starting — scanning every 6 hours")
    run_scan()
    schedule.every(6).hours.do(run_scan)
    while True:
        schedule.run_pending()
        time.sleep(60)
