"""
HS455 - Demonetisation & UPI: extra analysis (regressions + 5 figures)
Run:  pip install requests pandas numpy scipy statsmodels matplotlib
      python demonetisation_analysis.py
Outputs: figures/fig1..fig5 (.png) and results.txt (numbers to quote in the report)
Data: World Bank Open Data API (no key needed) + figures already used in the report
      (RBI / NPCI / MoF; see the DATA block - verify the UPI table against npci.org.in).
"""
import os, requests
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import curve_fit

os.makedirs("figures", exist_ok=True)
LOG = []
def say(s=""):
    print(s); LOG.append(str(s))

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight"})
BLUE, GREY, RED = "#2a73d4", "#9a9a8c", "#c0392b"

# ------------------------------------------------------------------ DATA
def wb(indicator, countries, start, end):
    """World Bank API -> tidy DataFrame (iso, year, value)."""
    url = f"https://api.worldbank.org/v2/country/{';'.join(countries)}/indicator/{indicator}"
    r = requests.get(url, params={"format": "json", "per_page": 2000, "date": f"{start}:{end}"}, timeout=40)
    r.raise_for_status()
    rows = [(d["countryiso3code"], int(d["date"]), d["value"]) for d in r.json()[1] if d["value"] is not None]
    return pd.DataFrame(rows, columns=["iso", "year", "value"])

# UPI annual totals (NPCI): FY label, volume (billion txns), value (Rs lakh crore).
# FY26 is the figure used in the report; earlier years are from NPCI product statistics - VERIFY before submitting.
upi = pd.DataFrame({
    "fy":  [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    "vol": [0.0179, 0.915, 5.35, 12.52, 22.33, 45.97, 83.75, 131.1, 185.8, 241.6],
    "val": [0.07, 1.09, 8.77, 21.32, 41.03, 84.17, 139.1, 199.9, 260.6, 314.0]})

# Currency in circulation as % of GDP (RBI, as in Figure 1 of the report)
cic = pd.DataFrame({"fy": [2016, 2017, 2021, 2024, 2025], "cic_gdp": [12.1, 8.7, 14.4, 11.7, 11.2]})

# Cost-benefit numbers from the report (Rs crore, RBI Annual Reports)
NOT_RETURNED, PRINT_FY17_EXTRA, PRINT_FY18_EXTRA = 10720, 4544, 1491

# RBI & NBER estimates (percentage points), from the report
RBI_EST, NBER_EST, OFFICIAL_ANNUAL = 0.33, 2.0, 0.70

# ------------------------------------------------------------------ FIG 1: UPI growth (OLS + logistic)
say("=== FIG 1: UPI volume growth ===")
d = upi[upi.fy >= 2019].copy()          # skip launch years when base is ~0
d["t"] = d.fy - 2019
X = sm.add_constant(d.t); y = np.log(d.vol)
ols = sm.OLS(y, X).fit()
g = np.exp(ols.params["t"]) - 1
lo, hi = np.exp(ols.conf_int().loc["t"]) - 1
say(f"Log-linear OLS (FY19-FY26): CAGR = {g*100:.1f}% (95% CI {lo*100:.1f}% to {hi*100:.1f}%), R2 = {ols.rsquared:.3f}")
say(f"Implied doubling time = {np.log(2)/np.log(1+g):.2f} years")

upi["yoy"] = upi.vol.pct_change() * 100
gr = upi[upi.fy >= 2021].copy(); gr["t"] = gr.fy - 2021
ols_g = sm.OLS(gr.yoy, sm.add_constant(gr.t)).fit()
say(f"YoY growth trend (FY21-FY26): slope = {ols_g.params['t']:.1f} pp per year (p = {ols_g.pvalues['t']:.3f})")

def logistic(t, L, k, t0): return L / (1 + np.exp(-k * (t - t0)))
try:
    p, _ = curve_fit(logistic, d.t, d.vol, p0=[500, 0.5, 6], bounds=([250, 0.05, 0], [5000, 3, 20]), maxfev=20000)
    say(f"Logistic fit: saturation L = {p[0]:.0f} bn txns/yr, k = {p[1]:.2f}, midpoint = FY{2019+p[2]:.1f}")
    logi_ok = True
except Exception as e:
    say(f"Logistic fit failed: {e}"); logi_ok = False

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
tt = np.linspace(0, 11, 100)
ax[0].scatter(upi.fy, upi.vol, color=BLUE, zorder=3, label="NPCI actual")
ax[0].plot(2019 + tt, np.exp(ols.params["const"] + ols.params["t"] * tt), color=GREY, ls="--", label=f"Exponential fit ({g*100:.0f}%/yr)")
if logi_ok: ax[0].plot(2019 + tt, logistic(tt, *p), color=RED, label="Logistic (S-curve) fit")
ax[0].set_yscale("log"); ax[0].axvline(2017, color="k", ls=":", lw=1)
ax[0].text(2017.1, ax[0].get_ylim()[0] * 1.5, "Demonetisation\n(Nov 2016)", fontsize=8)
ax[0].set_title("UPI annual volume (log scale)"); ax[0].set_ylabel("Billion transactions"); ax[0].set_xlabel("Financial year (ending March)"); ax[0].legend(fontsize=8)
ax[1].bar(gr.fy, gr.yoy, color=BLUE)
ax[1].plot(gr.fy, ols_g.fittedvalues, color=RED, label=f"Trend: {ols_g.params['t']:.0f} pp/yr")
ax[1].set_title("Year-on-year growth in UPI volume"); ax[1].set_ylabel("%"); ax[1].set_xlabel("Financial year"); ax[1].legend(fontsize=8)
fig.suptitle("Fig 1. UPI kept growing long after cash was restored, but growth is decelerating", fontsize=11)
fig.savefig("figures/fig1_upi_growth.png"); plt.close()

# ------------------------------------------------------------------ FIG 2: India vs peers (diff-in-diff style)
say("\n=== FIG 2: India vs peer economies (World Bank GDP growth) ===")
PEERS = ["BGD", "PAK", "IDN", "PHL", "VNM", "LKA"]
g_df = wb("NY.GDP.MKTP.KD.ZG", ["IND"] + PEERS, 2010, 2019)
piv = g_df.pivot(index="year", columns="iso", values="value")
gap = (piv["IND"] - piv[PEERS].mean(axis=1)).rename("gap").reset_index()
gap["post"] = (gap.year >= 2016).astype(int)       # WB labels FY2016-17 as 2016
gap["trend"] = gap.year - 2010
m = sm.OLS(gap.gap, sm.add_constant(gap[["post", "trend"]])).fit(cov_type="HC1")
b, ci = m.params["post"], m.conf_int().loc["post"]
say(f"gap_t = a + b*post2016 + c*trend  ->  b = {b:.2f} pp, 95% CI [{ci[0]:.2f}, {ci[1]:.2f}], p = {m.pvalues['post']:.3f}, N = {len(gap)}")
say(f"Mean gap 2010-15 = {gap[gap.post==0].gap.mean():.2f} pp; mean gap 2016-19 = {gap[gap.post==1].gap.mean():.2f} pp")
# placebo: pretend the shock was in 2013
pl = gap[gap.year <= 2015].copy(); pl["post"] = (pl.year >= 2013).astype(int)
mp = sm.OLS(pl.gap, sm.add_constant(pl[["post"]])).fit(cov_type="HC1")
say(f"Placebo (fake shock in 2013, pre-period only): b = {mp.params['post']:.2f}, p = {mp.pvalues['post']:.3f}")

fig, ax = plt.subplots(figsize=(8, 4))
cols = [GREY if y < 2016 else BLUE for y in gap.year]
ax.bar(gap.year, gap.gap, color=cols)
ax.axhline(0, color="k", lw=0.8)
ax.hlines(gap[gap.post == 0].gap.mean(), 2009.6, 2015.4, color=RED, ls="--", label="Pre-2016 mean")
ax.hlines(gap[gap.post == 1].gap.mean(), 2015.6, 2019.4, color=RED, label="2016-19 mean")
ax.set_ylabel("India minus peer-average GDP growth (pp)"); ax.set_xlabel("Year (WB fiscal-year label)")
ax.set_title(f"Fig 2. India's growth gap vs peers (BGD, PAK, IDN, PHL, VNM, LKA)\npost-2016 shift = {b:.2f} pp (95% CI {ci[0]:.1f} to {ci[1]:.1f})", fontsize=10)
ax.legend(fontsize=8); fig.savefig("figures/fig2_gdp_gap.png"); plt.close()

# ------------------------------------------------------------------ FIG 3: financial inclusion + cash
say("\n=== FIG 3: account ownership (Global Findex) and CIC/GDP ===")
fx = wb("FX.OWN.TOTL.ZS", ["IND"], 2011, 2024).sort_values("year")
say(fx.to_string(index=False))
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].plot(fx.year, fx.value, marker="o", color=BLUE)
ax[0].axvline(2016.85, color="k", ls=":", lw=1); ax[0].text(2016.95, fx.value.min(), "Demonetisation", fontsize=8)
ax[0].set_title("Adults with a bank/mobile-money account, India (%)"); ax[0].set_ylabel("%"); ax[0].set_xlabel("Findex survey year")
for _, r_ in fx.iterrows(): ax[0].annotate(f"{r_.value:.0f}", (r_.year, r_.value), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
ax[1].plot(cic.fy, cic.cic_gdp, marker="o", color=BLUE)
ax[1].axhline(12.1, color=GREY, ls="--"); ax[1].text(2021.5, 12.25, "FY16 level", color=GREY, fontsize=8)
for _, r_ in cic.iterrows(): ax[1].annotate(f"{r_.cic_gdp}", (r_.fy, r_.cic_gdp), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
ax[1].set_title("Currency in circulation (% of GDP)"); ax[1].set_xlabel("Financial year"); ax[1].set_ylabel("%")
fig.suptitle("Fig 3. Access to accounts jumped, but cash holding returned close to its old level", fontsize=11)
fig.savefig("figures/fig3_inclusion_cash.png"); plt.close()

# ------------------------------------------------------------------ FIG 4: cost-benefit
say("\n=== FIG 4: printing cost vs non-returned notes ===")
tot = PRINT_FY17_EXTRA + PRINT_FY18_EXTRA
say(f"Extra printing = Rs {tot} crore = {tot/NOT_RETURNED*100:.1f}% of non-returned notes (Rs {NOT_RETURNED} crore)")
fig, ax = plt.subplots(figsize=(6.5, 4.2))
ax.bar(["Notes not returned\n(max one-off gain)"], [NOT_RETURNED], color=GREY)
ax.bar(["Extra printing cost\n(FY17+FY18)"], [PRINT_FY17_EXTRA], color=BLUE, label="FY17")
ax.bar(["Extra printing cost\n(FY17+FY18)"], [PRINT_FY18_EXTRA], bottom=[PRINT_FY17_EXTRA], color=RED, label="FY18")
ax.text(0, NOT_RETURNED + 150, f"{NOT_RETURNED:,}", ha="center"); ax.text(1, tot + 150, f"{tot:,}\n({tot/NOT_RETURNED*100:.0f}% of gain)", ha="center")
ax.set_ylabel("Rs crore"); ax.set_ylim(0, NOT_RETURNED * 1.2); ax.legend(fontsize=8)
ax.set_title("Fig 4. Over half of the maximum one-off gain\nwas spent on printing new notes", fontsize=10)
fig.savefig("figures/fig4_cost_benefit.png"); plt.close()

# ------------------------------------------------------------------ FIG 5: estimates of GDP effect
say("\n=== FIG 5: competing estimates of the GDP effect ===")
labels = ["RBI (annual GVA)", "Official annual\nshortfall vs FY15-16", "Peer-gap regression\n(annual, this study)", "NBER (quarter of shock)"]
vals = [RBI_EST, OFFICIAL_ANNUAL, -b, NBER_EST]       # shown as growth LOST (pp)
fig, ax = plt.subplots(figsize=(8, 4))
colors = [GREY, GREY, BLUE, RED]
ax.barh(labels, vals, color=colors)
ax.errorbar(-b, 2, xerr=[[(-b) - (-ci[1])], [(-ci[0]) - (-b)]], color="k", capsize=4)
ax.axvline(0, color="k", lw=0.8); ax.invert_yaxis()
for i, v in enumerate(vals): ax.text(v + 0.05, i, f"{v:.2f}", va="center", fontsize=9)
ax.set_xlabel("Growth lost (percentage points)")
ax.set_title("Fig 5. Estimated growth cost of demonetisation depends on the data and the window", fontsize=10)
fig.savefig("figures/fig5_estimates.png"); plt.close()
say(f"Peer-gap estimate expressed as growth lost = {-b:.2f} pp (CI {-ci[1]:.2f} to {-ci[0]:.2f})")

open("results.txt", "w").write("\n".join(LOG))
print("\nDone. Figures in ./figures, numbers in results.txt")
