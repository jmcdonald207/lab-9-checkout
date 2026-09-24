"""Five-year pro forma financial statements and FCFE valuation.

Standard library only. All monetary inputs and outputs are in millions except
per-share amounts. Replace the illustrative assumptions below with company
figures; keep every opening balance sheet amount on the same date and scale.
"""

from decimal import Decimal, ROUND_HALF_UP


D = Decimal
YEARS = (2026, 2027, 2028, 2029, 2030)


# ---------------------------- EDIT INPUTS HERE ----------------------------
OPENING = {
    "revenue": D("10000.0"),
    "cash": D("300.0"),
    "inventory": D("1600.0"),
    "ppe": D("1200.0"),
    "other_assets": D("900.0"),
    "floor_plan": D("1200.0"),
    "debt": D("800.0"),
    "revolver": D("0.0"),
    "other_liabilities": D("700.0"),
    # Must make opening assets equal opening liabilities plus equity.
    "equity": D("1300.0"),
}

# Rates and ratios are decimals: enter 5% as Decimal("0.05").
ASSUMPTIONS = {
    "revenue_growth": {
        2026: D("0.05"), 2027: D("0.045"), 2028: D("0.04"),
        2029: D("0.035"), 2030: D("0.03"),
    },
    "gross_margin": {
        2026: D("0.22"), 2027: D("0.222"), 2028: D("0.224"),
        2029: D("0.225"), 2030: D("0.225"),
    },
    "sga_to_gross_profit": {
        2026: D("0.62"), 2027: D("0.615"), 2028: D("0.61"),
        2029: D("0.605"), 2030: D("0.60"),
    },
    "depreciation_to_opening_ppe": {
        year: D("0.10") for year in YEARS
    },
    "impairment": {
        2026: D("0.0"), 2027: D("0.0"), 2028: D("20.0"),
        2029: D("0.0"), 2030: D("0.0"),
    },
    "inventory_days": {
        2026: D("72"), 2027: D("71"), 2028: D("70"),
        2029: D("69"), 2030: D("68"),
    },
    "floor_plan_to_inventory": {year: D("0.75") for year in YEARS},
    "capex": {
        2026: D("150.0"), 2027: D("155.0"), 2028: D("160.0"),
        2029: D("165.0"), 2030: D("170.0"),
    },
    "debt_repayment": {
        2026: D("100.0"), 2027: D("100.0"), 2028: D("100.0"),
        2029: D("100.0"), 2030: D("100.0"),
    },
    "buyback": {
        2026: D("75.0"), 2027: D("75.0"), 2028: D("75.0"),
        2029: D("75.0"), 2030: D("75.0"),
    },
    "floor_plan_interest_rate": {year: D("0.05") for year in YEARS},
    "debt_interest_rate": {year: D("0.055") for year in YEARS},
    "revolver_interest_rate": {year: D("0.065") for year in YEARS},
    "tax_rate": {year: D("0.25") for year in YEARS},
    "other_assets_to_revenue_change": D("0.008"),
    "minimum_cash": D("200.0"),
    "cost_of_equity": D("0.10"),
    "terminal_growth": D("0.025"),
    "share_count": D("100.0"),
}
# -------------------------------------------------------------------------


def project(opening, assumptions):
    """Return annual projections, following the requested calculation order."""
    results = {}
    prior = dict(opening)

    for year in YEARS:
        revenue = prior["revenue"] * (D("1") + assumptions["revenue_growth"][year])
        gross_profit = revenue * assumptions["gross_margin"][year]
        sga = gross_profit * assumptions["sga_to_gross_profit"][year]
        depreciation = prior["ppe"] * assumptions["depreciation_to_opening_ppe"][year]
        impairment = assumptions["impairment"][year]
        operating_income = gross_profit - sga - depreciation - impairment
        interest = (
            prior["floor_plan"] * assumptions["floor_plan_interest_rate"][year]
            + prior["debt"] * assumptions["debt_interest_rate"][year]
            + prior["revolver"] * assumptions["revolver_interest_rate"][year]
        )
        pretax_income = operating_income - interest
        tax = max(D("0"), pretax_income) * assumptions["tax_rate"][year]
        net_income = pretax_income - tax

        inventory = (
            (revenue - gross_profit)
            * assumptions["inventory_days"][year]
            / D("365")
        )
        floor_plan = inventory * assumptions["floor_plan_to_inventory"][year]
        capex = assumptions["capex"][year]
        ppe = prior["ppe"] + capex - depreciation
        revenue_change = revenue - prior["revenue"]
        change_other_working_capital = (
            assumptions["other_assets_to_revenue_change"] * revenue_change
        )
        other_assets = (
            prior["other_assets"] + change_other_working_capital - impairment
        )
        repayment = min(assumptions["debt_repayment"][year], prior["debt"])
        debt = prior["debt"] - repayment
        other_liabilities = prior["other_liabilities"]
        buyback = assumptions["buyback"][year]
        equity = prior["equity"] + net_income - buyback

        change_inventory = inventory - prior["inventory"]
        change_floor_plan = floor_plan - prior["floor_plan"]
        fcfe = (
            net_income + depreciation + impairment - capex
            - change_inventory - change_other_working_capital
            + change_floor_plan - repayment
        )

        cash_before_revolver = prior["cash"] + fcfe - buyback
        minimum_cash = assumptions["minimum_cash"]
        revolver_draw = max(D("0"), minimum_cash - cash_before_revolver)
        available_for_repayment = max(D("0"), cash_before_revolver - minimum_cash)
        revolver_repayment = min(prior["revolver"], available_for_repayment)
        revolver = prior["revolver"] + revolver_draw - revolver_repayment
        cash = cash_before_revolver + revolver_draw - revolver_repayment

        assets = cash + inventory + ppe + other_assets
        liabilities_and_equity = (
            floor_plan + debt + revolver + other_liabilities + equity
        )

        row = {
            "revenue": revenue, "gross_profit": gross_profit, "sga": sga,
            "depreciation": depreciation, "impairment": impairment,
            "operating_income": operating_income, "interest": interest,
            "pretax_income": pretax_income, "tax": tax, "net_income": net_income,
            "cash": cash, "inventory": inventory, "ppe": ppe,
            "other_assets": other_assets, "total_assets": assets,
            "floor_plan": floor_plan, "debt": debt, "revolver": revolver,
            "other_liabilities": other_liabilities, "equity": equity,
            "total_liabilities_and_equity": liabilities_and_equity,
            "capex": capex, "change_inventory": change_inventory,
            "change_other_working_capital": change_other_working_capital,
            "change_floor_plan": change_floor_plan, "repayment": repayment,
            "fcfe": fcfe, "buyback": buyback, "revolver_draw": revolver_draw,
            "revolver_repayment": revolver_repayment,
            "balance_gap": assets - liabilities_and_equity,
            "minimum_cash_gap": cash - minimum_cash,
        }
        results[year] = row
        prior = {"revenue": revenue, "cash": cash, "inventory": inventory,
                 "ppe": ppe, "other_assets": other_assets,
                 "floor_plan": floor_plan, "debt": debt,
                 "revolver": revolver, "other_liabilities": other_liabilities,
                 "equity": equity}

    return results


def assert_balanced(results, tolerance=D("0.000001")):
    """Raise an error naming the year and gap if either annual check fails."""
    for year, row in results.items():
        if abs(row["balance_gap"]) > tolerance:
            raise ValueError(
                f"{year} balance sheet does not balance; gap = {row['balance_gap']}"
            )
        if row["minimum_cash_gap"] < -tolerance:
            raise ValueError(
                f"{year} cash is below the minimum; gap = {row['minimum_cash_gap']}"
            )


def print_table(title, lines, results):
    print(f"\n{title} (millions)")
    print(f"{'':34}" + "".join(f"{year:>13}" for year in YEARS))
    for label, key in lines:
        print(f"{label:<34}" + "".join(f"{results[y][key]:>13.1f}" for y in YEARS))


def value_equity(results, assumptions):
    cost = assumptions["cost_of_equity"]
    growth = assumptions["terminal_growth"]
    if cost <= growth:
        raise ValueError("Cost of equity must exceed terminal growth.")
    if assumptions["share_count"] <= 0:
        raise ValueError("Share count must be positive.")

    pv_explicit = sum(
        results[year]["fcfe"] / ((D("1") + cost) ** index)
        for index, year in enumerate(YEARS, start=1)
    )
    normalized_2030_fcfe = results[2030]["fcfe"] + results[2030]["repayment"]
    terminal_value = (
        normalized_2030_fcfe * (D("1") + growth) / (cost - growth)
    )
    pv_terminal = terminal_value / ((D("1") + cost) ** len(YEARS))
    equity_value = pv_explicit + pv_terminal
    terminal_share = pv_terminal / equity_value if equity_value else D("0")
    value_per_share = equity_value / assumptions["share_count"]
    return equity_value, terminal_share, value_per_share


def main():
    opening_gap = (
        OPENING["cash"] + OPENING["inventory"] + OPENING["ppe"]
        + OPENING["other_assets"] - OPENING["floor_plan"] - OPENING["debt"]
        - OPENING["revolver"] - OPENING["other_liabilities"] - OPENING["equity"]
    )
    if opening_gap:
        raise ValueError(f"Opening balance sheet does not balance; gap = {opening_gap}")

    results = project(OPENING, ASSUMPTIONS)

    print_table("Income statement", (
        ("Revenue", "revenue"), ("Gross profit", "gross_profit"),
        ("SG&A", "sga"), ("Depreciation", "depreciation"),
        ("Impairment", "impairment"), ("Operating income", "operating_income"),
        ("Interest", "interest"), ("Pretax income", "pretax_income"),
        ("Tax", "tax"), ("Net income", "net_income"),
    ), results)
    print_table("Balance sheet", (
        ("Cash", "cash"), ("Inventory", "inventory"), ("PP&E", "ppe"),
        ("Other assets", "other_assets"), ("Total assets", "total_assets"),
        ("Floor plan", "floor_plan"), ("Debt", "debt"),
        ("Revolver", "revolver"), ("Other liabilities", "other_liabilities"),
        ("Equity", "equity"),
        ("Total liabilities and equity", "total_liabilities_and_equity"),
    ), results)
    print_table("Cash flow", (
        ("Net income", "net_income"), ("Depreciation", "depreciation"),
        ("Impairment", "impairment"), ("Capital expenditures", "capex"),
        ("Change in inventory", "change_inventory"),
        ("Change in other working capital", "change_other_working_capital"),
        ("Change in floor plan", "change_floor_plan"),
        ("Debt repayment", "repayment"), ("FCFE", "fcfe"),
        ("Buyback", "buyback"), ("Revolver draw", "revolver_draw"),
        ("Revolver repayment", "revolver_repayment"),
    ), results)
    print_table("Checks", (
        ("Assets - liabilities - equity", "balance_gap"),
        ("Cash above minimum", "minimum_cash_gap"),
    ), results)

    # Required before valuation so an invalid projection cannot be valued.
    assert_balanced(results)
    equity_value, terminal_share, value_per_share = value_equity(results, ASSUMPTIONS)
    print("\nEquity valuation")
    print(f"Equity value: ${equity_value.quantize(D('0.1'), rounding=ROUND_HALF_UP)} million")
    print(f"Share of value after 2030: {(terminal_share * D('100')).quantize(D('0.1'), rounding=ROUND_HALF_UP)}%")
    print(f"Value per share: ${value_per_share.quantize(D('0.01'), rounding=ROUND_HALF_UP)}")


if __name__ == "__main__":
    main()
