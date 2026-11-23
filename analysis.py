"""
Demonetisation and UPI in India - analysis script
B.Tech project (secondary data analysis)

What this script does
---------------------
1. Reads demonetisation_upi_dataset.csv (every row has a source link).
2. Calculates the ratios used in the report (black money, formalisation, GDP).
3. Tests our four hypotheses (H1 to H4) with simple rules.
4. Prints everything and also saves it to analysis_results.txt

Only the standard library is used, so no pip install is needed.
Run:  python analysis.py
Keep the CSV file in the same folder as this script.
"""

import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "demonetisation_upi_dataset.csv")
OUT_FILE = os.path.join(HERE, "analysis_results.txt")

lines = []  # everything we print is also stored here


def say(text=""):
    print(text)
    lines.append(text)


# ---------------------------------------------------------------
# 1. Load the data
# ---------------------------------------------------------------
rows = []
with open(DATA_FILE, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        r["value"] = float(r["value"])
        rows.append(r)


def get(indicator, period):
    """Return the value for one indicator and one period."""
    for r in rows:
        if r["indicator"] == indicator and r["period"] == period:
            return r["value"]
    raise KeyError(f"{indicator} / {period} not found in dataset")


def pct(a, b):
    """Percentage change from a to b."""
    return (b - a) / a * 100


say("=" * 64)
say("DEMONETISATION AND UPI IN INDIA: RESULTS OF OUR ANALYSIS")
say("=" * 64)
say(f"Rows read from dataset: {len(rows)}")

# ---------------------------------------------------------------
# 2. Black money: how many notes came back? (H1)
# ---------------------------------------------------------------
say("\n--- PART A: BLACK MONEY (H1) ---")
circ = get("sbn_in_circulation", "2016-11-08")
back = get("sbn_returned", "2017-18 reconciliation")
not_back = get("sbn_not_returned", "2017-18 reconciliation")

share_back = back / circ * 100
share_not_back = (circ - back) / circ * 100
say(f"SBNs in circulation (Rs crore)        : {circ:,.0f}")
say(f"SBNs returned (Rs crore)              : {back:,.0f}")
say(f"Share returned                        : {share_back:.2f}%")
say(f"Share NOT returned                    : {share_not_back:.2f}%")
say(f"Check: circ - returned = {circ - back:,.0f} crore vs reported {not_back:,.0f} crore")

first_back = get("sbn_returned_first_estimate", "2016-17 (30 Jun 2017)")
first_circ = get("sbn_in_circulation_first_estimate", "2016-17")
say(f"First RBI estimate (AR 2016-17)       : {first_back / first_circ * 100:.2f}% returned")

# cost side
p16 = get("printing_cost", "FY2015-16")
p17 = get("printing_cost", "FY2016-17")
p18 = get("printing_cost", "FY2017-18")
extra = p17 - p16
say(f"\nPrinting cost FY16 / FY17 / FY18      : {p16:,.0f} / {p17:,.0f} / {p18:,.0f} Rs crore")
say(f"Extra printing cost in FY17           : {extra:,.0f} crore ({p17 / p16:.2f} times)")
say(f"Extra cost as % of non-returned notes : {extra / not_back * 100:.1f}%")
say(f"FY18 printing still above FY16 by     : {p18 - p16:,.0f} crore")
# if we also count the FY18 excess over FY16, the total extra cost gets bigger
two_year_extra = (p17 - p16) + (p18 - p16)
say(f"Two-year extra cost (FY17+FY18)       : {two_year_extra:,.0f} crore "
    f"= {two_year_extra / not_back * 100:.1f}% of non-returned notes")

# counterfeits
c500 = get("change_detected_rs500_sbn", "FY2016-17")
c1000 = get("change_detected_rs1000_sbn", "FY2016-17")
c100 = get("change_detected_rs100", "FY2016-17")
c50 = get("change_detected_rs50", "FY2016-17")
say(f"\nCounterfeits detected, change in FY17 : Rs500 {c500:+.1f}%, Rs1000 {c1000:+.1f}%, "
    f"Rs100 {c100:+.1f}%, Rs50 {c50:+.1f}%")

# tax returns
t16 = get("corporate_returns_filed", "FY2016-17")
t17 = get("corporate_returns_filed", "FY2017-18")
say(f"Corporate returns filed FY17 -> FY18  : {t16:,.0f} -> {t17:,.0f} ({pct(t16, t17):+.1f}%)")

h1 = share_not_back < 1.0
say(f"\nH1 rule: less than 1% of SBNs failed to return -> {'SUPPORTED' if h1 else 'NOT SUPPORTED'}")

# ---------------------------------------------------------------
# 3. GDP growth (H3)
# ---------------------------------------------------------------
say("\n--- PART B: GDP GROWTH (H3) ---")
g15 = get("gdp_growth_annual", "FY2014-15")
g16 = get("gdp_growth_annual", "FY2015-16")
g17 = get("gdp_growth_annual", "FY2016-17")
pre_avg = (g15 + g16) / 2
say(f"Annual GDP growth FY15 / FY16 / FY17  : {g15} / {g16} / {g17} %")
say(f"Average of the two years before       : {pre_avg:.2f}%")
say(f"FY17 shortfall vs that average        : {pre_avg - g17:.2f} percentage points")
say(f"FY17 vs FY16 fall                     : {g16 - g17:.2f} percentage points")

q2 = get("gdp_growth_quarter", "Q2 FY2016-17")
q3r = get("gdp_growth_quarter", "Q3 FY2016-17 (revised)")
q3o = get("gdp_growth_quarter", "Q3 FY2016-17 (original)")
q4 = get("gdp_growth_quarter", "Q4 FY2016-17")
say(f"\nQuarterly GDP growth Q2/Q3(rev)/Q4    : {q2} / {q3r} / {q4} %")
say(f"Fall from Q2 (pre-shock) to Q4        : {q2 - q4:.1f} percentage points")
say(f"Fall from Q2 to Q3 (revised)          : {q2 - q3r:.1f} percentage points")
say(f"Q3 original vs revised                : {q3o} vs {q3r} (data revision of {q3o - q3r:.1f} pp)")
say(f"Q4 GVA growth                         : {get('gva_growth_quarter', 'Q4 FY2016-17')}%")

# RBI forecast revisions
f_oct = get("gva_forecast_fy17", "Oct 2016 policy")
f_dec = get("gva_forecast_fy17", "Dec 2016 policy")
f_feb = get("gva_forecast_fy17", "Feb 2017 policy")
imp = get("demonetisation_impact_on_gva_fy17", "Feb 2017 estimate")
say(f"\nRBI FY17 GVA forecast Oct/Dec/Feb     : {f_oct} / {f_dec} / {f_feb} %")
say(f"Total forecast cut Oct -> Feb         : {f_oct - f_feb:.1f} pp")
say(f"RBI's own demonetisation effect       : {imp:.2f} pp -> {imp / (f_oct - f_feb) * 100:.0f}% of the forecast cut")
say(f"Official GDP FY17 vs RBI Feb forecast : {g17} vs {f_feb} (GVA and GDP are not the same, so only rough)")

# NBER (independent study)
nb_q = get("activity_growth_loss_quarter_of_shock", "2016 Q4 (Jan-Mar)")
nb_nd = get("activity_decline_nov_dec_2016", "Nov-Dec 2016")
say(f"\nNBER study: growth loss in the quarter: {nb_q:+.1f} pp, Nov-Dec activity {nb_nd:+.1f}%")
gap = abs(nb_q) / imp
say(f"NBER loss is about {gap:.1f} times the RBI's full-year estimate of {imp} pp")
say(f"(different periods - quarter vs whole year - so this is only a rough comparison)")
inf_e = get("informal_share_employment", "2018")
inf_o = get("informal_share_output", "2018")
say(f"Informal sector: {inf_e:.0f}% of jobs but {inf_o:.0f}% of output")

h3 = (q4 < q2) and (g17 < pre_avg) and (g17 > 6.0)
say(f"\nH3 rule: sharp short-run fall but not a collapse -> {'SUPPORTED' if h3 else 'NOT SUPPORTED'}")

# ---------------------------------------------------------------
# 4. UPI and digital payments (H2)
# ---------------------------------------------------------------
say("\n--- PART C: UPI AND FORMALISATION (H2) ---")
months = ["2026-08", "2026-09", "2026-10"]
say(f"{'Month':<9}{'Volume (bn)':>13}{'Value (Rs lakh cr)':>20}{'Avg ticket (Rs)':>17}")
for m in months:
    v = get("upi_volume", m)
    val = get("upi_value", m)
    ticket = val * 1e5 * 1e7 / (v * 1e9)  # lakh crore -> rupees, billion -> count
    say(f"{m:<9}{v:>13.2f}{val:>20.2f}{ticket:>17.0f}")

v_o, val_o = get("upi_volume", "2026-10"), get("upi_value", "2026-10")
v_s, val_s = get("upi_volume", "2026-09"), get("upi_value", "2026-09")
v_py, val_py = get("upi_volume", "2025-10"), get("upi_value", "2025-10")
say(f"\nOct vs Sep 2026: volume {pct(v_s, v_o):+.1f}%, value {pct(val_s, val_o):+.1f}% (Oct has 31 days, Sep has 30)")
say(f"Per-day volume Oct vs Sep: {pct(v_s / 30, v_o / 31):+.1f}%, per-day value {pct(val_s / 30, val_o / 31):+.1f}%")
say(f"Oct 2026 vs Oct 2025 (YoY): volume {pct(v_py, v_o):+.1f}%, value {pct(val_py, val_o):+.1f}%")
daily_val = val_o * 1e5 / 31  # Rs crore per day
say(f"Average daily value in Oct 2026: Rs {daily_val:,.0f} crore (NPCI reports about 1,01,707)")

doubling = math.log(2) / math.log(1 + pct(v_py, v_o) / 100)
say(f"If volume keeps growing at {pct(v_py, v_o):.0f}% a year it doubles in about {doubling:.1f} years")

# FY26 totals
vf, valf = get("upi_volume_fy26", "FY2025-26"), get("upi_value_fy26", "FY2025-26")
say(f"\nFY26 UPI: {vf:.1f} bn transactions, Rs {valf:.0f} lakh crore -> avg ticket Rs {valf * 1e12 / (vf * 1e9):,.0f}")
say(f"Average ticket FY26 vs Oct 2026: Rs {valf * 1e12 / (vf * 1e9):,.0f} vs "
    f"Rs {val_o * 1e12 / (v_o * 1e9):,.0f} (value per transaction is falling slightly)")
say(f"P2M share of volume: {get('p2m_share_of_volume', '2025'):.0f}% (so person-to-merchant dominates)")

cagr_v = get("digital_retail_volume_cagr_fy17_fy23", "FY2016-17 to FY2022-23")
cagr_val = get("digital_retail_value_cagr_fy17_fy23", "FY2016-17 to FY2022-23")
say(f"RBI paper: digital retail CAGR FY17-FY23 volume {cagr_v:.0f}%, value {cagr_val:.0f}%")
say(f"Volume grows about {cagr_v / cagr_val:.1f} times faster than value -> payments getting smaller and more frequent")

h2 = (pct(v_py, v_o) > 15) and (cagr_v > 20)
say(f"\nH2 rule: UPI volume still growing above 15% a year long after cash returned -> {'SUPPORTED' if h2 else 'NOT SUPPORTED'}")

# ---------------------------------------------------------------
# 5. Cash paradox (H4)
# ---------------------------------------------------------------
say("\n--- PART D: THE CASH PARADOX (H4) ---")
cic0 = get("currency_in_circulation", "2016-11-08")
cic1 = get("currency_in_circulation", "2026-10-23")
years = (2026 + 10 / 12 + 23 / 365) - (2016 + 10 / 12 + 8 / 365)
cagr = (cic1 / cic0) ** (1 / years) - 1
say(f"CIC on 8 Nov 2016 / 23 Oct 2026       : Rs {cic0} / {cic1} trillion")
say(f"Increase                              : {pct(cic0, cic1):.0f}% over {years:.1f} years")
say(f"CAGR of CIC                           : {cagr * 100:.1f}% a year")
say(f"Growth of CIC in FY26 alone           : {get('cic_growth_fy26', 'FY2025-26'):.1f}%")

upi_month_trn = val_o  # 1 lakh crore = 1 trillion, so same number
say(f"\nMonthly UPI value (Oct 2026)          : Rs {upi_month_trn:.2f} trillion")
say(f"UPI monthly value / CIC               : {upi_month_trn / cic1 * 100:.0f}%")
say(f"UPI annualised value / CIC            : {upi_month_trn * 12 / cic1:.1f} times")
say(f"UPI value in FY26 / CIC (end FY26)    : {valf / get('currency_in_circulation', 'FY2025-26 end'):.1f} times")

r16 = get("cic_to_gdp", "FY2015-16")
r17 = get("cic_to_gdp", "FY2016-17")
r21 = get("cic_to_gdp", "FY2020-21")
r24 = get("cic_to_gdp", "FY2023-24")
r25 = get("cic_to_gdp", "FY2024-25")
say(f"\nCIC/GDP FY16 / FY17 / FY21 / FY24 / FY25: {r16} / {r17} / {r21} / {r24} / {r25} %")
say(f"Drop in the year of shock (FY16->FY17): {r17 - r16:+.1f} pp")
say(f"Recovery FY17 -> FY21 peak            : {r21 - r17:+.1f} pp")
say(f"Fall FY21 -> FY25                     : {r25 - r21:+.1f} pp")
say(f"FY25 compared with FY16               : {r25 - r16:+.1f} pp (so cash/GDP is close to the pre-shock level)")

d16 = get("currency_to_demand_deposits_ratio", "FY2015-16")
d25 = get("currency_to_demand_deposits_ratio", "FY2024-25")
say(f"Currency / demand deposits FY16 -> FY25: {d16} -> {d25} ({pct(d16, d25):.0f}%)")

h4 = (cic1 > cic0 * 2) and (r25 < r21)
say(f"\nH4 rule: CIC more than doubled in rupees AND CIC/GDP fell from its peak -> {'SUPPORTED' if h4 else 'NOT SUPPORTED'}")

# ---------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------
say("\n--- SUMMARY OF HYPOTHESES ---")
say(f"H1 (black money, notes returned) : {'Supported' if h1 else 'Not supported'}")
say(f"H2 (UPI keeps growing)           : {'Supported' if h2 else 'Not supported'}")
say(f"H3 (sharp but short GDP hit)     : {'Supported' if h3 else 'Not supported'}")
say(f"H4 (cash and UPI grow together)  : {'Supported' if h4 else 'Not supported'}")
say("\nNote: these are simple rules we chose ourselves. They show whether the numbers")
say("are consistent with each hypothesis; they do not prove cause and effect.")

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"\nResults saved to {OUT_FILE}")
