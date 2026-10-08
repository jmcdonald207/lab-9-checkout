"""
5-year pro forma (income statement, balance sheet, cash flow) and FCFE valuation.
Company: Walmart Inc.   Opening balance sheet: 10-K for fiscal year ended Jan 31, 2026.
All money in $ millions, except per-share values.
Standard library only.
 
Year labels: "2026" = the fiscal year that starts in 2026 (FY2027, ends Jan 31, 2027), ... "2030" = FY2031.
"""
 
YEARS = [2026, 2027, 2028, 2029, 2030]
 
# ----------------------------------------------------------------------------
# OPENING BALANCE SHEET  (Jan 31, 2026, 10-K / Q4 FY26 earnings release)
# ----------------------------------------------------------------------------
OPEN = {
    "cash": 10727.0,
    "inventory": 58851.0,
    "ppe": 136083.0,
    "other_assets": 79007.0,   # plug: total assets 284,668 less the three lines above
    "floor_plan": 63061.0,     # Walmart has no floor plan; this slot carries accounts payable
    "debt": 38166.0,           # long-term debt incl. current portion (3,542 + 34,624)
    "revolver": 6596.0,        # short-term borrowings
    "other_liab": 70958.0,     # plug: total liabilities 178,781 less payables, debt, revolver
    "equity": 105887.0,        # total equity incl. noncontrolling interest
    "revenue": 713163.0,       # FY26 total revenues
}
 
# ----------------------------------------------------------------------------
# ASSUMPTIONS (one value per year unless scalar)
# ----------------------------------------------------------------------------
A = {
    "growth":        [0.045, 0.045, 0.040, 0.040, 0.035],
    "gross_margin":  [0.2495, 0.2500, 0.2505, 0.2510, 0.2515],  # FY26 actual 24.93%
    "sga_ratio":     [0.7520, 0.7510, 0.7500, 0.7490, 0.7480],  # SG&A / gross profit, ex-depreciation
    "dep_ratio":     [0.110] * 5,                               # depreciation / opening PP&E
    "impairment":    [0.0] * 5,
    "capex":         [27500.0, 28000.0, 28500.0, 29000.0, 29500.0],
    "repayment":     [3500.0] * 5,
    "buyback":       [8000.0] * 5,      # shareholder payout (dividends ~ $0.99 x 7.97bn sh)
    "inv_days":      [40.1] * 5,        # inventory / cost of sales x 365
    "floor_ratio":   [1.0715] * 5,      # payables / inventory
    "tax_rate":      [0.244] * 5,
}
OTHER_WC_PCT = 0.008        # other assets rise 0.8% of each $ of revenue growth
RATE_FLOOR = 0.0            # payables carry no interest
RATE_DEBT = 0.055
RATE_REVOLVER = 0.045
MIN_CASH = 8000.0
COST_OF_EQUITY = 0.075
TERMINAL_GROWTH = 0.030
SHARES = 7972.4             # millions, as of Mar 11, 2026 (10-K cover)
 
 
# ----------------------------------------------------------------------------
# MODEL
# ----------------------------------------------------------------------------
def project():
    prev = dict(OPEN)
    out = []
    for i, yr in enumerate(YEARS):
        r = {"year": yr}
        # --- income statement
        r["revenue"] = prev["revenue"] * (1 + A["growth"][i])
        r["gross_profit"] = r["revenue"] * A["gross_margin"][i]
        r["cogs"] = r["revenue"] - r["gross_profit"]
        r["sga"] = r["gross_profit"] * A["sga_ratio"][i]
        r["dep"] = prev["ppe"] * A["dep_ratio"][i]
        r["impair"] = A["impairment"][i]
        r["op_income"] = r["gross_profit"] - r["sga"] - r["dep"] - r["impair"]
        r["interest"] = (prev["floor_plan"] * RATE_FLOOR + prev["debt"] * RATE_DEBT
                         + prev["revolver"] * RATE_REVOLVER)
        r["pretax"] = r["op_income"] - r["interest"]
        r["tax"] = max(0.0, r["pretax"]) * A["tax_rate"][i]
        r["net_income"] = r["pretax"] - r["tax"]
 
        # --- balance sheet except cash
        r["inventory"] = r["cogs"] * A["inv_days"][i] / 365
        r["floor_plan"] = r["inventory"] * A["floor_ratio"][i]
        r["capex"] = A["capex"][i]
        r["ppe"] = prev["ppe"] + r["capex"] - r["dep"]
        r["d_owc"] = OTHER_WC_PCT * (r["revenue"] - prev["revenue"])
        r["other_assets"] = prev["other_assets"] + r["d_owc"] - r["impair"]
        r["repay"] = A["repayment"][i]
        r["debt"] = prev["debt"] - r["repay"]
        r["other_liab"] = prev["other_liab"]
        r["buyback"] = A["buyback"][i]
        r["equity"] = prev["equity"] + r["net_income"] - r["buyback"]
 
        # --- free cash flow to equity
        r["d_inv"] = r["inventory"] - prev["inventory"]
        r["d_floor"] = r["floor_plan"] - prev["floor_plan"]
        r["fcfe"] = (r["net_income"] + r["dep"] + r["impair"] - r["capex"]
                     - r["d_inv"] - r["d_owc"] + r["d_floor"] - r["repay"])
 
        # --- cash and revolver
        pre = prev["cash"] + r["fcfe"] - r["buyback"]
        if pre < MIN_CASH:
            draw, rep = MIN_CASH - pre, 0.0
        else:
            draw, rep = 0.0, min(prev["revolver"], pre - MIN_CASH)
        r["rev_draw"], r["rev_repay"] = draw, rep
        r["revolver"] = prev["revolver"] + draw - rep
        r["cash"] = pre + draw - rep
 
        # --- totals and checks
        r["assets"] = r["cash"] + r["inventory"] + r["ppe"] + r["other_assets"]
        r["liabilities"] = r["floor_plan"] + r["debt"] + r["revolver"] + r["other_liab"]
        r["gap"] = r["assets"] - r["liabilities"] - r["equity"]
        r["cash_ok"] = r["cash"] >= MIN_CASH - 1e-6
        out.append(r)
        prev = r
    return out
 
 
# ----------------------------------------------------------------------------
# PRINTING
# ----------------------------------------------------------------------------
def table(title, rows, open_col=None):
    print("\n" + title)
    head = f"{'':32}" + (f"{'Open':>12}" if open_col is not None else "") + "".join(f"{y:>12}" for y in YEARS)
    print(head)
    print("-" * len(head))
    for label, vals, op in rows:
        line = f"{label:32}"
        if open_col is not None:
            line += f"{op:>12,.1f}" if op is not None else f"{'':>12}"
        line += "".join(f"{v:>12,.1f}" for v in vals)
        print(line)
 
 
def col(res, k):
    return [r[k] for r in res]
 
 
def print_statements(res):
    neg = lambda k: [-r[k] for r in res]
    table("INCOME STATEMENT ($mm)", [
        ("Revenue", col(res, "revenue"), None),
        ("Gross profit", col(res, "gross_profit"), None),
        ("SG&A", neg("sga"), None),
        ("Depreciation", neg("dep"), None),
        ("Impairment", neg("impair"), None),
        ("Operating income", col(res, "op_income"), None),
        ("Interest", neg("interest"), None),
        ("Pretax income", col(res, "pretax"), None),
        ("Tax", neg("tax"), None),
        ("Net income", col(res, "net_income"), None),
    ])
    o = OPEN
    o_assets = o["cash"] + o["inventory"] + o["ppe"] + o["other_assets"]
    o_liab = o["floor_plan"] + o["debt"] + o["revolver"] + o["other_liab"]
    table("BALANCE SHEET ($mm)", [
        ("Cash", col(res, "cash"), o["cash"]),
        ("Inventory", col(res, "inventory"), o["inventory"]),
        ("PP&E", col(res, "ppe"), o["ppe"]),
        ("Other assets", col(res, "other_assets"), o["other_assets"]),
        ("Total assets", col(res, "assets"), o_assets),
        ("Floor plan (accounts payable)", col(res, "floor_plan"), o["floor_plan"]),
        ("Debt", col(res, "debt"), o["debt"]),
        ("Revolver", col(res, "revolver"), o["revolver"]),
        ("Other liabilities", col(res, "other_liab"), o["other_liab"]),
        ("Total liabilities", col(res, "liabilities"), o_liab),
        ("Equity", col(res, "equity"), o["equity"]),
    ], open_col=True)
    table("CASH FLOW ($mm)", [
        ("Net income", col(res, "net_income"), None),
        ("+ Depreciation", col(res, "dep"), None),
        ("+ Impairment", col(res, "impair"), None),
        ("- Capex", neg("capex"), None),
        ("- Change in inventory", neg("d_inv"), None),
        ("- Change in other WC", neg("d_owc"), None),
        ("+ Change in floor plan", col(res, "d_floor"), None),
        ("- Debt repayment", neg("repay"), None),
        ("Free cash flow to equity", col(res, "fcfe"), None),
        ("- Buyback / payout", neg("buyback"), None),
        ("+ Revolver draw", col(res, "rev_draw"), None),
        ("- Revolver repayment", neg("rev_repay"), None),
        ("Ending cash", col(res, "cash"), None),
    ])
 
 
def print_checks(res):
    print("\nCHECKS")
    print(f"{'':32}" + "".join(f"{y:>12}" for y in YEARS))
    print(f"{'Assets - liabilities - equity':32}" + "".join(f"{r['gap']:>12.6f}" for r in res))
    print(f"{'Cash >= minimum (%.0f)' % MIN_CASH:32}" + "".join(f"{str(r['cash_ok']):>12}" for r in res))
 
 
def assert_balanced(res, tol=1e-6):
    for r in res:
        if abs(r["gap"]) > tol:
            raise AssertionError(f"Year {r['year']}: balance sheet out of balance by {r['gap']:.6f}")
        if not r["cash_ok"]:
            raise AssertionError(f"Year {r['year']}: cash {r['cash']:.1f} is below minimum {MIN_CASH:.1f}")
 
 
# ----------------------------------------------------------------------------
# VALUATION
# ----------------------------------------------------------------------------
def value(res):
    ke, g = COST_OF_EQUITY, TERMINAL_GROWTH
    pv_flows = sum(r["fcfe"] / (1 + ke) ** (t + 1) for t, r in enumerate(res))
    last = res[-1]
    tv = (last["fcfe"] + last["repay"]) * (1 + g) / (ke - g)
    pv_tv = tv / (1 + ke) ** 5
    eq = pv_flows + pv_tv
    return eq, pv_tv / eq, eq / SHARES
 
 
def main():
    res = project()
    print_statements(res)
    print_checks(res)
    assert_balanced(res)
    eq, share_tv, vps = value(res)
    print("\nVALUATION")
    print(f"Equity value ($mm):            {eq:,.1f}")
    print(f"Share of value after 2030:     {share_tv:.1%}")
    print(f"Value per share ($):           {vps:,.2f}")
 
 
if __name__ == "__main__":
    main()
