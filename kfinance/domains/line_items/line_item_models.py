from decimal import Decimal
from itertools import chain
from typing import TypedDict

from pydantic import BaseModel


class LineItemResponse(BaseModel):
    line_item: dict[str, Decimal]


class LineItemType(TypedDict):
    name: str
    aliases: set[str]
    dataitemid: int
    spgi_name: str


# all of these values must be lower case keys
LINE_ITEMS: list[LineItemType] = [
    {
        "name": "revenue",
        "aliases": {"normal_revenue", "regular_revenue"},
        "dataitemid": 112,
        "spgi_name": "Revenue",
    },
    {
        "name": "finance_division_revenue",
        "aliases": set(),
        "dataitemid": 52,
        "spgi_name": "Finance Div. Revenue",
    },
    {
        "name": "insurance_division_revenue",
        "aliases": set(),
        "dataitemid": 70,
        "spgi_name": "Insurance Div. Revenue",
    },
    {
        "name": "revenue_from_sale_of_assets",
        "aliases": set(),
        "dataitemid": 104,
        "spgi_name": "Gain(Loss) on Sale Of Assets (Rev)",
    },
    {
        "name": "revenue_from_sale_of_investments",
        "aliases": set(),
        "dataitemid": 106,
        "spgi_name": "Gain(Loss) on Sale Of Invest. (Rev)",
    },
    {
        "name": "revenue_from_interest_and_investment_income",
        "aliases": set(),
        "dataitemid": 110,
        "spgi_name": "Interest And Invest. Income (Rev)",
    },
    {"name": "other_revenue", "aliases": set(), "dataitemid": 90, "spgi_name": "Other Revenue"},
    {
        "name": "total_other_revenue",
        "aliases": set(),
        "dataitemid": 357,
        "spgi_name": "Other Revenue, Total",
    },
    {
        "name": "fees_and_other_income",
        "aliases": set(),
        "dataitemid": 168,
        "spgi_name": "Fees and Other Income",
    },
    {"name": "total_revenue", "aliases": set(), "dataitemid": 28, "spgi_name": "Total Revenue"},
    {
        "name": "cost_of_goods_sold",
        "aliases": {"cogs"},
        "dataitemid": 34,
        "spgi_name": "Cost Of Goods Sold",
    },
    {
        "name": "finance_division_operating_expense",
        "aliases": {"operating_expense_finance_division"},
        "dataitemid": 51,
        "spgi_name": "Finance Div. Operating Exp.",
    },
    {
        "name": "insurance_division_operating_expense",
        "aliases": {"operating_expense_insurance_division"},
        "dataitemid": 69,
        "spgi_name": "Insurance Div. Operating Exp.",
    },
    {
        "name": "finance_division_interest_expense",
        "aliases": {"interest_expense_finance_division"},
        "dataitemid": 50,
        "spgi_name": "Interest Expense - Finance Division",
    },
    {
        "name": "cost_of_revenue",
        "aliases": {"cor"},
        "dataitemid": 1,
        "spgi_name": "Cost Of Revenue",
    },
    {"name": "gross_profit", "aliases": set(), "dataitemid": 10, "spgi_name": "Gross Profit"},
    {
        "name": "selling_general_and_admin_expense",
        "aliases": {
            "selling_general_and_admin_cost",
            "selling_general_and_admin",
            "sg_and_a",
            "sga",
        },
        "dataitemid": 102,
        "spgi_name": "Selling General & Admin Exp.",
    },
    {
        "name": "exploration_and_drilling_costs",
        "aliases": {
            "exploration_and_drilling_expense",
        },
        "dataitemid": 49,
        "spgi_name": "Exploration/Drilling Costs",
    },
    {
        "name": "provision_for_bad_debts",
        "aliases": {
            "provision_for_bad_debt",
        },
        "dataitemid": 95,
        "spgi_name": "Provision for Bad Debts",
    },
    {
        "name": "pre_opening_costs",
        "aliases": {
            "pre_opening_expense",
        },
        "dataitemid": 96,
        "spgi_name": "Pre-Opening Costs",
    },
    {
        "name": "total_selling_general_and_admin_expense",
        "aliases": {
            "total_selling_general_and_admin_cost",
            "total_selling_general_and_admin",
            "total_sga",
        },
        "dataitemid": 23,
        "spgi_name": "SG&A Exp., Total",
    },
    {
        "name": "research_and_development_expense",
        "aliases": {
            "research_and_development_cost",
            "r_and_d_expense",
            "r_and_d_cost",
            "rnd_expense",
            "rnd_cost",
        },
        "dataitemid": 100,
        "spgi_name": "R & D Exp.",
    },
    {
        "name": "depreciation_and_amortization",
        "aliases": {
            "d_and_a",
            "dna",
        },
        "dataitemid": 41,
        "spgi_name": "Depreciation & Amort.",
    },
    {
        "name": "amortization_of_goodwill_and_intangibles",
        "aliases": set(),
        "dataitemid": 31,
        "spgi_name": "Amort. of Goodwill and Intangibles",
    },
    {
        "name": "impairment_of_oil_gas_and_mineral_properties",
        "aliases": {
            "impairment_of_oil_and_gas",
            "impairment_o_and_g",
        },
        "dataitemid": 71,
        "spgi_name": "Impair. of Oil, Gas & Mineral Prop.",
    },
    {
        "name": "total_depreciation_and_amortization",
        "aliases": {
            "total_d_and_a",
            "total_dna",
        },
        "dataitemid": 2,
        "spgi_name": "Depreciation & Amort., Total",
    },
    {
        "name": "other_operating_expense",
        "aliases": set(),
        "dataitemid": 260,
        "spgi_name": "Other Operating Expense/(Income)",
    },
    {
        "name": "total_other_operating_expense",
        "aliases": set(),
        "dataitemid": 380,
        "spgi_name": "Other Operating Exp., Total",
    },
    {
        "name": "total_operating_expense",
        "aliases": {
            "operating_expense",
        },
        "dataitemid": 373,
        "spgi_name": "Total Operating Expenses",
    },
    {
        "name": "operating_income",
        "aliases": set(),
        "dataitemid": 21,
        "spgi_name": "Operating Income",
    },
    {
        "name": "interest_expense",
        "aliases": set(),
        "dataitemid": 82,
        "spgi_name": "Interest Expense",
    },
    {
        "name": "interest_and_investment_income",
        "aliases": set(),
        "dataitemid": 65,
        "spgi_name": "Interest and Invest. Income",
    },
    {
        "name": "net_interest_expense",
        "aliases": set(),
        "dataitemid": 368,
        "spgi_name": "Net Interest Exp.",
    },
    {
        "name": "income_from_affiliates",
        "aliases": set(),
        "dataitemid": 47,
        "spgi_name": "Income / (Loss) from Affiliates",
    },
    {
        "name": "currency_exchange_gains",
        "aliases": set(),
        "dataitemid": 38,
        "spgi_name": "Currency Exchange Gains (Loss)",
    },
    {
        "name": "other_non_operating_income",
        "aliases": set(),
        "dataitemid": 85,
        "spgi_name": "Other Non-Operating Inc. (Exp.)",
    },
    {
        "name": "total_other_non_operating_income",
        "aliases": set(),
        "dataitemid": 371,
        "spgi_name": "Other Non-Operating Exp., Total",
    },
    {
        "name": "ebt_excluding_unusual_items",
        "aliases": {
            "earnings_before_taxes_excluding_unusual_items",
        },
        "dataitemid": 4,
        "spgi_name": "EBT Excl Unusual Items",
    },
    {
        "name": "restructuring_charges",
        "aliases": set(),
        "dataitemid": 98,
        "spgi_name": "Restructuring Charges",
    },
    {
        "name": "merger_charges",
        "aliases": set(),
        "dataitemid": 80,
        "spgi_name": "Merger & Related Restruct. Charges",
    },
    {
        "name": "merger_and_restructuring_charges",
        "aliases": set(),
        "dataitemid": 363,
        "spgi_name": "Merger & Restruct. Charges",
    },
    {
        "name": "impairment_of_goodwill",
        "aliases": set(),
        "dataitemid": 209,
        "spgi_name": "Impairment of Goodwill",
    },
    {
        "name": "gain_from_sale_of_assets",
        "aliases": set(),
        "dataitemid": 62,
        "spgi_name": "Gain (Loss) On Sale Of Invest.",
    },
    {
        "name": "gain_from_sale_of_investments",
        "aliases": set(),
        "dataitemid": 56,
        "spgi_name": "Gain (Loss) On Sale Of Assets",
    },
    {"name": "asset_writedown", "aliases": set(), "dataitemid": 32, "spgi_name": "Asset Writedown"},
    {
        "name": "in_process_research_and_development_expense",
        "aliases": {
            "in_process_research_and_development_cost",
            "in_process_r_and_d_expense",
            "in_process_r_and_d_cost",
            "in_process_rnd_expense",
            "in_process_rnd_cost",
        },
        "dataitemid": 72,
        "spgi_name": "In Process R & D Exp.",
    },
    {
        "name": "insurance_settlements",
        "aliases": set(),
        "dataitemid": 73,
        "spgi_name": "Insurance Settlements",
    },
    {
        "name": "legal_settlements",
        "aliases": set(),
        "dataitemid": 77,
        "spgi_name": "Legal Settlements",
    },
    {
        "name": "other_unusual_items",
        "aliases": set(),
        "dataitemid": 87,
        "spgi_name": "Other Unusual Items",
    },
    {
        "name": "total_other_unusual_items",
        "aliases": set(),
        "dataitemid": 374,
        "spgi_name": "Other Unusual Items, Total",
    },
    {
        "name": "total_unusual_items",
        "aliases": {
            "unusual_items",
        },
        "dataitemid": 19,
        "spgi_name": "Total Unusual Items",
    },
    {
        "name": "ebt_including_unusual_items",
        "aliases": {
            "earnings_before_taxes_including_unusual_items",
        },
        "dataitemid": 139,
        "spgi_name": "EBT Incl. Unusual Items",
    },
    {
        "name": "income_tax_expense",
        "aliases": {
            "income_taxes",
            "income_tax",
        },
        "dataitemid": 75,
        "spgi_name": "Income Tax Expense",
    },
    {
        "name": "earnings_from_continued_operations",
        "aliases": {
            "continued_operations_earnings",
        },
        "dataitemid": 7,
        "spgi_name": "Earnings from Cont. Ops.",
    },
    {
        "name": "earnings_from_discontinued_operations",
        "aliases": {
            "discontinued_operations_earnings",
        },
        "dataitemid": 40,
        "spgi_name": "Earnings of Discontinued Ops.",
    },
    {
        "name": "extraordinary_item_and_accounting_change",
        "aliases": set(),
        "dataitemid": 42,
        "spgi_name": "Extraord. Item & Account. Change",
    },
    {
        "name": "net_income_to_company",
        "aliases": set(),
        "dataitemid": 41571,
        "spgi_name": "Net Income to Company",
    },
    {
        "name": "minority_interest_in_earnings",
        "aliases": {
            "net_income_to_minority_interest",
        },
        "dataitemid": 83,
        "spgi_name": "Minority Int. in Earnings",
    },
    {"name": "net_income", "aliases": set(), "dataitemid": 15, "spgi_name": "Net Income"},
    {
        "name": "premium_on_redemption_of_preferred_stock",
        "aliases": set(),
        "dataitemid": 279,
        "spgi_name": "Premium on Redemption of Pref. Stock",
    },
    {
        "name": "preferred_stock_dividend",
        "aliases": set(),
        "dataitemid": 280,
        "spgi_name": "Preferred Stock Dividend",
    },
    {
        "name": "other_preferred_stock_adjustments",
        "aliases": set(),
        "dataitemid": 281,
        "spgi_name": "Other Pref. Stock Adjustments",
    },
    {
        "name": "other_adjustments_to_net_income",
        "aliases": set(),
        "dataitemid": 259,
        "spgi_name": "Other Adjustments to Net Income",
    },
    {
        "name": "preferred_dividends_and_other_adjustments",
        "aliases": set(),
        "dataitemid": 97,
        "spgi_name": "Pref. Dividends and Other Adj.",
    },
    {
        "name": "net_income_allocable_to_general_partner",
        "aliases": set(),
        "dataitemid": 249,
        "spgi_name": "Net Income Allocable to General Partner",
    },
    {
        "name": "net_income_to_common_shareholders_including_extra_items",
        "aliases": set(),
        "dataitemid": 16,
        "spgi_name": "NI to Common Incl. Extra Items",
    },
    {
        "name": "net_income_to_common_shareholders_excluding_extra_items",
        "aliases": set(),
        "dataitemid": 379,
        "spgi_name": "NI to Common Excl. Extra Items",
    },
    {
        "name": "cash_and_equivalents",
        "aliases": {
            "cash",
            "cash_and_cash_equivalents",
        },
        "dataitemid": 1096,
        "spgi_name": "Cash And Equivalents",
    },
    {
        "name": "short_term_investments",
        "aliases": set(),
        "dataitemid": 1069,
        "spgi_name": "Short Term Investments",
    },
    {
        "name": "trading_asset_securities",
        "aliases": set(),
        "dataitemid": 1244,
        "spgi_name": "Trading Asset Securities",
    },
    {
        "name": "total_cash_and_short_term_investments",
        "aliases": {
            "cash_and_short_term_investments",
        },
        "dataitemid": 1002,
        "spgi_name": "Total Cash & ST Investments",
    },
    {
        "name": "accounts_receivable",
        "aliases": {
            "short_term_accounts_receivable",
            "current_accounts_receivable",
        },
        "dataitemid": 1021,
        "spgi_name": "Accounts Receivable",
    },
    {
        "name": "other_receivables",
        "aliases": {
            "short_term_other_receivables",
            "current_other_receivables",
        },
        "dataitemid": 1206,
        "spgi_name": "Other Receivables",
    },
    {
        "name": "notes_receivable",
        "aliases": {
            "short_term_notes_receivable",
            "current_notes_receivable",
        },
        "dataitemid": 1048,
        "spgi_name": "Notes Receivable",
    },
    {
        "name": "total_receivables",
        "aliases": {
            "short_term_total_receivables",
            "current_total_receivables",
            "total_receivable",
            "short_term_total_receivable",
            "current_total_receivable",
        },
        "dataitemid": 1001,
        "spgi_name": "Total Receivables",
    },
    {
        "name": "inventory",
        "aliases": {
            "inventories",
        },
        "dataitemid": 1043,
        "spgi_name": "Inventory",
    },
    {
        "name": "prepaid_expense",
        "aliases": {
            "prepaid_expenses",
        },
        "dataitemid": 1212,
        "spgi_name": "Prepaid Exp.",
    },
    {
        "name": "finance_division_loans_and_leases_short_term",
        "aliases": {
            "finance_division_short_term_loans_and_leases",
            "short_term_finance_division_loans_and_leases",
            "short_term_loans_and_leases_of_the_finance_division",
        },
        "dataitemid": 1032,
        "spgi_name": "Finance Div. Loans and Leases, ST",
    },
    {
        "name": "finance_division_other_current_assets",
        "aliases": {
            "finance_division_other_short_term_assets",
            "other_current_assets_of_the_finance_division",
            "other_short_term_assets_of_the_finance_division",
        },
        "dataitemid": 1029,
        "spgi_name": "Finance Div. Other Curr. Assets",
    },
    {
        "name": "loans_held_for_sale",
        "aliases": set(),
        "dataitemid": 1185,
        "spgi_name": "Loans Held For Sale",
    },
    {
        "name": "deferred_tax_asset_current_portion",
        "aliases": {
            "current_deferred_tax_asset",
            "short_term_deferred_tax_asset",
        },
        "dataitemid": 1117,
        "spgi_name": "Deferred Tax Assets, Curr.",
    },
    {
        "name": "restricted_cash",
        "aliases": set(),
        "dataitemid": 1104,
        "spgi_name": "Restricted Cash",
    },
    {
        "name": "other_current_assets",
        "aliases": set(),
        "dataitemid": 1055,
        "spgi_name": "Other Current Assets",
    },
    {
        "name": "total_current_assets",
        "aliases": {
            "current_assets",
            "total_short_term_assets",
            "short_term_assets",
        },
        "dataitemid": 1008,
        "spgi_name": "Total Current Assets",
    },
    {
        "name": "gross_property_plant_and_equipment",
        "aliases": {
            "gppe",
            "gross_ppe",
        },
        "dataitemid": 1169,
        "spgi_name": "Gross Property, Plant & Equipment",
    },
    {
        "name": "accumulated_depreciation",
        "aliases": set(),
        "dataitemid": 1075,
        "spgi_name": "Accumulated Depreciation",
    },
    {
        "name": "net_property_plant_and_equipment",
        "aliases": {
            "property_plant_and_equipment",
            "nppe",
            "ppe",
            "net_ppe",
        },
        "dataitemid": 1004,
        "spgi_name": "Net Property, Plant & Equipment",
    },
    {
        "name": "long_term_investments",
        "aliases": {
            "non_current_investments",
        },
        "dataitemid": 1054,
        "spgi_name": "Long-term Investments",
    },
    {"name": "goodwill", "aliases": set(), "dataitemid": 1171, "spgi_name": "Goodwill"},
    {
        "name": "other_intangibles",
        "aliases": set(),
        "dataitemid": 1040,
        "spgi_name": "Other Intangibles",
    },
    {
        "name": "finance_division_loans_and_leases_long_term",
        "aliases": {
            "finance_division_long_term_loans_and_leases",
            "long_term_finance_division_loans_and_leases",
            "long_term_loans_and_leases_of_the_finance_division",
        },
        "dataitemid": 1033,
        "spgi_name": "Finance Div. Loans and Leases, LT",
    },
    {
        "name": "finance_division_other_non_current_assets",
        "aliases": {
            "finance_division_other_long_term_assets",
            "other_non_current_assets_of_the_finance_division",
            "other_long_term_assets_of_the_finance_division",
        },
        "dataitemid": 1034,
        "spgi_name": "Finance Div. Other LT Assets",
    },
    {
        "name": "long_term_accounts_receivable",
        "aliases": {
            "non_current_accounts_receivable",
        },
        "dataitemid": 1088,
        "spgi_name": "Accounts Receivable Long-Term",
    },
    {
        "name": "long_term_loans_receivable",
        "aliases": {
            "non_current_loans_receivable",
            "loans_receivable",
        },
        "dataitemid": 1050,
        "spgi_name": "Loans Receivable Long-Term",
    },
    {
        "name": "long_term_deferred_tax_assets",
        "aliases": {
            "non_current_deferred_tax_assets",
        },
        "dataitemid": 1026,
        "spgi_name": "Deferred Tax Assets, LT",
    },
    {
        "name": "long_term_deferred_charges",
        "aliases": {
            "non_current_deferred_charges",
        },
        "dataitemid": 1025,
        "spgi_name": "Deferred Charges, LT",
    },
    {
        "name": "other_long_term_assets",
        "aliases": {
            "long_term_other_assets",
            "other_non_current_assets",
            "non_current_other_assets",
        },
        "dataitemid": 1060,
        "spgi_name": "Other Long-Term Assets",
    },
    {
        "name": "total_assets",
        "aliases": {
            "assets",
        },
        "dataitemid": 1007,
        "spgi_name": "Total Assets",
    },
    {
        "name": "accounts_payable",
        "aliases": set(),
        "dataitemid": 1018,
        "spgi_name": "Accounts Payable",
    },
    {
        "name": "accrued_expenses",
        "aliases": set(),
        "dataitemid": 1016,
        "spgi_name": "Accrued Expenses",
    },
    {
        "name": "short_term_borrowings",
        "aliases": {
            "current_borrowings",
            "short_term_borrowing",
            "current_borrowing",
        },
        "dataitemid": 1046,
        "spgi_name": "Short-term Borrowings",
    },
    {
        "name": "current_portion_of_long_term_debt",
        "aliases": {
            "current_portion_of_non_current_debt",
            "current_portion_of_lt_debt",
        },
        "dataitemid": 1297,
        "spgi_name": "Current Portion of Long Term Debt",
    },
    {
        "name": "current_portion_of_capital_leases",
        "aliases": {
            "current_portion_of_capitalized_leases",
            "current_portion_of_cap_leases",
            "current_portion_of_leases",
        },
        "dataitemid": 1090,
        "spgi_name": "Curr. Port. of Cap. Leases",
    },
    {
        "name": "current_portion_of_long_term_debt_and_capital_leases",
        "aliases": {
            "current_portion_of_lt_debt_and_cap_leases",
            "current_portion_of_long_term_debt_and_capitalized_leases",
            "current_portion_of_non_current_debt_and_capital_leases",
            "current_portion_of_non_current_debt_and_capitalized_leases",
            "total_current_portion_of_long_term_debt_and_capital_leases",
            "total_current_portion_of_lt_debt_and_cap_leases",
            "total_current_portion_of_long_term_debt_and_capitalized_leases",
            "total_current_portion_of_non_current_debt_and_capital_leases",
            "total_current_portion_of_non_current_debt_and_capitalized_leases",
        },
        "dataitemid": 1279,
        "spgi_name": "Curr. Port. of LT Debt/Cap. Leases",
    },
    {
        "name": "finance_division_debt_current_portion",
        "aliases": set(),
        "dataitemid": 1030,
        "spgi_name": "Finance Div. Debt Current",
    },
    {
        "name": "finance_division_other_current_liabilities",
        "aliases": set(),
        "dataitemid": 1031,
        "spgi_name": "Finance Div. Other Curr. Liab.",
    },
    {
        "name": "current_income_taxes_payable",
        "aliases": {
            "current_portion_of_income_taxes_payable",
        },
        "dataitemid": 1094,
        "spgi_name": "Curr. Income Taxes Payable",
    },
    {
        "name": "current_unearned_revenue",
        "aliases": {
            "current_portion_of_unearned_revenue",
        },
        "dataitemid": 1074,
        "spgi_name": "Unearned Revenue, Current",
    },
    {
        "name": "current_deferred_tax_liability",
        "aliases": set(),
        "dataitemid": 1119,
        "spgi_name": "Def. Tax Liability, Curr.",
    },
    {
        "name": "other_current_liability",
        "aliases": {
            "other_current_liabilities",
        },
        "dataitemid": 1057,
        "spgi_name": "Other Current Liabilities",
    },
    {
        "name": "total_current_liabilities",
        "aliases": {
            "current_liabilities",
        },
        "dataitemid": 1009,
        "spgi_name": "Total Current Liabilities",
    },
    {
        "name": "long_term_debt",
        "aliases": {
            "non_current_debt",
        },
        "dataitemid": 1049,
        "spgi_name": "Long-Term Debt",
    },
    {
        "name": "capital_leases",
        "aliases": {
            "long_term_leases",
            "capitalized_leases",
        },
        "dataitemid": 1183,
        "spgi_name": "Capital Leases",
    },
    {
        "name": "finance_division_debt_non_current_portion",
        "aliases": {
            "finance_division_debt_long_term_portion",
            "finance_division_non_current_debt",
            "finance_division_long_term_debt",
        },
        "dataitemid": 1035,
        "spgi_name": "Finance Div. Debt Non-Curr.",
    },
    {
        "name": "finance_division_other_non_current_liabilities",
        "aliases": {
            "finance_division_other_long_term_liabilities",
        },
        "dataitemid": 1036,
        "spgi_name": "Finance Div. Other Non-Curr. Liab.",
    },
    {
        "name": "non_current_unearned_revenue",
        "aliases": {
            "long_term_unearned_revenue",
        },
        "dataitemid": 1256,
        "spgi_name": "Unearned Revenue, Non-Current",
    },
    {
        "name": "pension_and_other_post_retirement_benefit",
        "aliases": set(),
        "dataitemid": 1213,
        "spgi_name": "Pension & Other Post-Retire. Benefits",
    },
    {
        "name": "non_current_deferred_tax_liability",
        "aliases": set(),
        "dataitemid": 1027,
        "spgi_name": "Def. Tax Liability, Non-Curr.",
    },
    {
        "name": "other_non_current_liabilities",
        "aliases": {
            "non_current_other_liabilities",
            "other_long_term_liabilities",
            "long_term_other_liabilities",
        },
        "dataitemid": 1062,
        "spgi_name": "Other Non-Current Liabilities",
    },
    {
        "name": "total_liabilities",
        "aliases": {
            "liabilities",
        },
        "dataitemid": 1276,
        "spgi_name": "Total Liabilities",
    },
    {
        "name": "preferred_stock_redeemable",
        "aliases": {
            "redeemable_preferred_stock",
        },
        "dataitemid": 1217,
        "spgi_name": "Pref. Stock, Redeemable",
    },
    {
        "name": "preferred_stock_non_redeemable",
        "aliases": {
            "non_redeemable_preferred_stock",
        },
        "dataitemid": 1216,
        "spgi_name": "Pref. Stock, Non-Redeem.",
    },
    {
        "name": "preferred_stock_convertible",
        "aliases": {
            "convertible_preferred_stock",
        },
        "dataitemid": 1214,
        "spgi_name": "Pref. Stock, Convertible",
    },
    {
        "name": "preferred_stock_other",
        "aliases": {
            "other_preferred_stock",
        },
        "dataitemid": 1065,
        "spgi_name": "Pref. Stock, Other",
    },
    {
        "name": "preferred_stock_additional_paid_in_capital",
        "aliases": {
            "additional_paid_in_capital_preferred_stock",
        },
        "dataitemid": 1085,
        "spgi_name": "Additional Paid In Capital - Preferred Stock",
    },
    {
        "name": "preferred_stock_equity_adjustment",
        "aliases": {
            "equity_adjustment_preferred_stock",
        },
        "dataitemid": 1215,
        "spgi_name": "Equity Adjustment - Preferred Stock",
    },
    {
        "name": "treasury_stock_preferred_stock_convertible",
        "aliases": {
            "treasury_preferred_stock_convertible",
            "treasury_stock_convertible_preferred_stock",
            "treasury_convertible_preferred_stock",
        },
        "dataitemid": 1249,
        "spgi_name": "Treasury Stock : Preferred Stock Convertible",
    },
    {
        "name": "treasury_stock_preferred_stock_non_redeemable",
        "aliases": {
            "treasury_preferred_stock_non_redeemable",
            "treasury_stock_non_redeemable_preferred_stock",
            "treasury_non_redeemable_preferred_stock",
        },
        "dataitemid": 1250,
        "spgi_name": "Treasury Stock : Preferred Stock Non Redeemable",
    },
    {
        "name": "treasury_stock_preferred_stock_redeemable",
        "aliases": {
            "treasury_preferred_stock_redeemable",
            "treasury_stock_redeemable_preferred_stock",
            "treasury_redeemable_preferred_stock",
        },
        "dataitemid": 1251,
        "spgi_name": "Treasury Stock : Preferred Stock Redeemable",
    },
    {
        "name": "total_preferred_equity",
        "aliases": {
            "total_preferred_stock",
            "preferred_equity",
            "preferred_stock",
        },
        "dataitemid": 1005,
        "spgi_name": "Total Pref. Equity",
    },
    {"name": "common_stock", "aliases": set(), "dataitemid": 1103, "spgi_name": "Common Stock"},
    {
        "name": "additional_paid_in_capital",
        "aliases": set(),
        "dataitemid": 1084,
        "spgi_name": "Additional Paid In Capital",
    },
    {
        "name": "retained_earnings",
        "aliases": set(),
        "dataitemid": 1222,
        "spgi_name": "Retained Earnings",
    },
    {"name": "treasury_stock", "aliases": set(), "dataitemid": 1248, "spgi_name": "Treasury Stock"},
    {
        "name": "other_equity",
        "aliases": set(),
        "dataitemid": 1028,
        "spgi_name": "Comprehensive Inc. and Other",
    },
    {
        "name": "total_common_equity",
        "aliases": {
            "common_equity",
        },
        "dataitemid": 1006,
        "spgi_name": "Total Common Equity",
    },
    {
        "name": "total_equity",
        "aliases": {
            "equity",
            "total_shareholders_equity",
            "shareholders_equity",
        },
        "dataitemid": 1275,
        "spgi_name": "Total Equity",
    },
    {
        "name": "total_liabilities_and_equity",
        "aliases": {
            "liabilities_and_equity",
        },
        "dataitemid": 1013,
        "spgi_name": "Total Liabilities And Equity",
    },
    {
        "name": "common_shares_outstanding",
        "aliases": set(),
        "dataitemid": 1100,
        "spgi_name": "Common Shares Outstanding",
    },
    {
        "name": "adjustments_to_cash_flow_net_income",
        "aliases": set(),
        "dataitemid": 21523,
        "spgi_name": "Adjustments to Cash Flow Net Income",
    },
    {
        "name": "other_amortization",
        "aliases": set(),
        "dataitemid": 2014,
        "spgi_name": "Other Amortization",
    },
    {
        "name": "total_other_non_cash_items",
        "aliases": set(),
        "dataitemid": 2179,
        "spgi_name": "Other Non-Cash Items, Total",
    },
    {
        "name": "net_decrease_in_loans_originated_and_sold",
        "aliases": set(),
        "dataitemid": 2033,
        "spgi_name": "Net (Increase)/Decrease in Loans Orig/Sold",
    },
    {
        "name": "provision_for_credit_losses",
        "aliases": set(),
        "dataitemid": 2112,
        "spgi_name": "Provision for Credit Losses",
    },
    {
        "name": "loss_on_equity_investments",
        "aliases": set(),
        "dataitemid": 2086,
        "spgi_name": "(Income) Loss on Equity Invest.",
    },
    {
        "name": "stock_based_compensation",
        "aliases": set(),
        "dataitemid": 2127,
        "spgi_name": "Stock-Based Compensation",
    },
    {
        "name": "tax_benefit_from_stock_options",
        "aliases": set(),
        "dataitemid": 2135,
        "spgi_name": "Tax Benefit from Stock Options",
    },
    {
        "name": "net_cash_from_discontinued_operation",
        "aliases": {
            "cash_from_discontinued_operation",
        },
        "dataitemid": 2081,
        "spgi_name": "Net Cash From Discontinued Ops.",
    },
    {
        "name": "other_operating_activities",
        "aliases": set(),
        "dataitemid": 2047,
        "spgi_name": "Other Operating Activities",
    },
    {
        "name": "change_in_trading_asset_securities",
        "aliases": set(),
        "dataitemid": 2134,
        "spgi_name": "Change in Trad. Asset Securities",
    },
    {
        "name": "change_in_accounts_receivable",
        "aliases": set(),
        "dataitemid": 2018,
        "spgi_name": "Change In Accounts Receivable",
    },
    {
        "name": "change_in_inventories",
        "aliases": set(),
        "dataitemid": 2099,
        "spgi_name": "Change In Inventories",
    },
    {
        "name": "change_in_accounts_payable",
        "aliases": set(),
        "dataitemid": 2017,
        "spgi_name": "Change in Acc. Payable",
    },
    {
        "name": "change_in_unearned_revenue",
        "aliases": set(),
        "dataitemid": 2139,
        "spgi_name": "Change in Unearned Rev.",
    },
    {
        "name": "change_in_income_taxes",
        "aliases": set(),
        "dataitemid": 2101,
        "spgi_name": "Change in Inc. Taxes",
    },
    {
        "name": "change_in_deferred_taxes",
        "aliases": set(),
        "dataitemid": 2084,
        "spgi_name": "Change in Def. Taxes",
    },
    {
        "name": "change_in_other_net_operating_assets",
        "aliases": set(),
        "dataitemid": 2045,
        "spgi_name": "Change in Other Net Operating Assets",
    },
    {
        "name": "change_in_net_operating_assets",
        "aliases": set(),
        "dataitemid": 2010,
        "spgi_name": "Change in Net Operating Assets ",
    },
    {
        "name": "cash_from_operations",
        "aliases": {
            "cash_from_operating_activities",
            "cash_flow_from_operations",
        },
        "dataitemid": 2006,
        "spgi_name": "Cash from Ops.",
    },
    {
        "name": "capital_expenditure",
        "aliases": {
            "capital_expenditures",
            "capex",
        },
        "dataitemid": 2021,
        "spgi_name": "Capital Expenditure",
    },
    {
        "name": "sale_of_property_plant_and_equipment",
        "aliases": {
            "sale_of_ppe",
        },
        "dataitemid": 2042,
        "spgi_name": "Sale of Property, Plant, and Equipment",
    },
    {
        "name": "cash_acquisitions",
        "aliases": set(),
        "dataitemid": 2057,
        "spgi_name": "Cash Acquisitions",
    },
    {"name": "divestitures", "aliases": set(), "dataitemid": 2077, "spgi_name": "Divestitures"},
    {
        "name": "sale_of_real_estate",
        "aliases": {
            "sale_of_real_properties",
            "sale_of_real_estate_properties",
        },
        "dataitemid": 2040,
        "spgi_name": "Sale (Purchase) of Real Estate properties",
    },
    {
        "name": "sale_of_intangible_assets",
        "aliases": {
            "sale_of_intangible_asset",
            "sale_of_intangibles",
        },
        "dataitemid": 2029,
        "spgi_name": "Sale (Purchase) of Intangible assets",
    },
    {
        "name": "net_cash_from_investments",
        "aliases": set(),
        "dataitemid": 2027,
        "spgi_name": "Net Cash from Investments",
    },
    {
        "name": "net_decrease_in_investment_loans_originated_and_sold",
        "aliases": set(),
        "dataitemid": 2032,
        "spgi_name": "Net (Increase)/Decrease in Loans Orig/Sold",
    },
    {
        "name": "other_investing_activities",
        "aliases": set(),
        "dataitemid": 2051,
        "spgi_name": "Other Investing Activities",
    },
    {
        "name": "total_other_investing_activities",
        "aliases": set(),
        "dataitemid": 2177,
        "spgi_name": "Other Investing Activities, Total",
    },
    {
        "name": "cash_from_investing",
        "aliases": {
            "cash_from_investing_activities",
            "cashflow_from_investing",
            "cashflow_from_investing_activities",
        },
        "dataitemid": 2005,
        "spgi_name": "Cash from Investing",
    },
    {
        "name": "short_term_debt_issued",
        "aliases": {
            "current_debt_issued",
        },
        "dataitemid": 2043,
        "spgi_name": "Short Term Debt Issued",
    },
    {
        "name": "long_term_debt_issued",
        "aliases": {
            "non_current_debt_issued",
        },
        "dataitemid": 2034,
        "spgi_name": "Long-Term Debt Issued",
    },
    {
        "name": "total_debt_issued",
        "aliases": set(),
        "dataitemid": 2161,
        "spgi_name": "Total Debt Issued",
    },
    {
        "name": "short_term_debt_repaid",
        "aliases": {
            "current_debt_repaid",
        },
        "dataitemid": 2044,
        "spgi_name": "Short Term Debt Repaid",
    },
    {
        "name": "long_term_debt_repaid",
        "aliases": {
            "non_current_debt_repaid",
        },
        "dataitemid": 2036,
        "spgi_name": "Long-Term Debt Repaid",
    },
    {
        "name": "total_debt_repaid",
        "aliases": set(),
        "dataitemid": 2166,
        "spgi_name": "Total Debt Repaid",
    },
    {
        "name": "issuance_of_common_stock",
        "aliases": set(),
        "dataitemid": 2169,
        "spgi_name": "Issuance of Common Stock",
    },
    {
        "name": "repurchase_of_common_stock",
        "aliases": set(),
        "dataitemid": 2164,
        "spgi_name": "Repurchase of Common Stock",
    },
    {
        "name": "issuance_of_preferred_stock",
        "aliases": set(),
        "dataitemid": 2181,
        "spgi_name": "Issuance of Preferred Stock",
    },
    {
        "name": "repurchase_of_preferred_stock",
        "aliases": set(),
        "dataitemid": 2172,
        "spgi_name": "Repurchase of Preferred Stock",
    },
    {
        "name": "common_dividends_paid",
        "aliases": set(),
        "dataitemid": 2074,
        "spgi_name": "Common Dividends Paid",
    },
    {
        "name": "preferred_dividends_paid",
        "aliases": set(),
        "dataitemid": 2116,
        "spgi_name": "Pref. Dividends Paid",
    },
    {
        "name": "total_dividends_paid",
        "aliases": {
            "dividends_paid",
        },
        "dataitemid": 2022,
        "spgi_name": "Total Dividends Paid",
    },
    {
        "name": "special_dividends_paid",
        "aliases": set(),
        "dataitemid": 2041,
        "spgi_name": "Special Dividend Paid",
    },
    {
        "name": "other_financing_activities",
        "aliases": set(),
        "dataitemid": 2050,
        "spgi_name": "Other Financing Activities",
    },
    {
        "name": "cash_from_financing",
        "aliases": {
            "cash_from_financing_activities",
            "cashflow_from_financing",
            "cashflow_from_financing_activities",
        },
        "dataitemid": 2004,
        "spgi_name": "Cash from Financing",
    },
    {
        "name": "foreign_exchange_rate_adjustments",
        "aliases": {
            "fx_adjustments",
            "foreign_exchange_adjustments",
        },
        "dataitemid": 2144,
        "spgi_name": "Foreign Exchange Rate Adj.",
    },
    {
        "name": "miscellaneous_cash_flow_adjustments",
        "aliases": {
            "misc_cash_flow_adj",
        },
        "dataitemid": 2149,
        "spgi_name": "Misc. Cash Flow Adj.",
    },
    {
        "name": "net_change_in_cash",
        "aliases": {
            "change_in_cash",
        },
        "dataitemid": 2093,
        "spgi_name": "Net Change in Cash",
    },
    {
        "name": "depreciation",
        "aliases": set(),
        "dataitemid": 2143,
        "spgi_name": "Depreciation (From Notes)",
    },
    {
        "name": "depreciation_of_rental_assets",
        "aliases": set(),
        "dataitemid": 42409,
        "spgi_name": "Depreciation of Rental Assets",
    },
    {
        "name": "sale_proceeds_from_rental_assets",
        "aliases": set(),
        "dataitemid": 42411,
        "spgi_name": "Sale Proceeds from Rental Assets",
    },
    {
        "name": "basic_eps",
        "aliases": {
            "basic_earning_per_share",
            "basic_eps_including_extra_items",
            "basic_earning_per_share_including_extra_items",
        },
        "dataitemid": 9,
        "spgi_name": "Basic EPS",
    },
    {
        "name": "basic_eps_excluding_extra_items",
        "aliases": {
            "basic_earning_per_share_excluding_extra_items",
        },
        "dataitemid": 3064,
        "spgi_name": "Basic EPS Excl. Extra Items",
    },
    {
        "name": "basic_eps_from_accounting_change",
        "aliases": {
            "basic_earning_per_share_from_accounting_change",
        },
        "dataitemid": 145,
        "spgi_name": "Basic EPS - Accounting Change",
    },
    {
        "name": "basic_eps_from_extraordinary_items",
        "aliases": {
            "basic_earning_per_share_from_extraordinary_items",
        },
        "dataitemid": 146,
        "spgi_name": "Basic EPS - Extraordinary Items",
    },
    {
        "name": "basic_eps_from_accounting_change_and_extraordinary_items",
        "aliases": {
            "basic_earning_per_share_from_accounting_change_and_extraordinary_items",
        },
        "dataitemid": 45,
        "spgi_name": "Basic EPS - Extraordinary Items & Accounting Change",
    },
    {
        "name": "weighted_average_basic_shares_outstanding",
        "aliases": set(),
        "dataitemid": 3217,
        "spgi_name": "Weighted Avg. Basic Shares Out.",
    },
    {
        "name": "diluted_eps",
        "aliases": {
            "diluted_earning_per_share",
            "diluted_eps_including_extra_items",
            "diluted_earning_per_share_including_extra_items",
        },
        "dataitemid": 8,
        "spgi_name": "Diluted EPS",
    },
    {
        "name": "diluted_eps_excluding_extra_items",
        "aliases": {
            "diluted_earning_per_share_excluding_extra_items",
        },
        "dataitemid": 142,
        "spgi_name": "Diluted EPS Excl. Extra Items",
    },
    {
        "name": "weighted_average_diluted_shares_outstanding",
        "aliases": set(),
        "dataitemid": 342,
        "spgi_name": "Weighted Avg. Diluted Shares Out.",
    },
    {
        "name": "normalized_basic_eps",
        "aliases": {
            "normalized_basic_earning_per_share",
        },
        "dataitemid": 4379,
        "spgi_name": "Normalized Basic EPS",
    },
    {
        "name": "normalized_diluted_eps",
        "aliases": {
            "normalized_diluted_earning_per_share",
        },
        "dataitemid": 4380,
        "spgi_name": "Normalized Diluted EPS",
    },
    {
        "name": "dividends_per_share",
        "aliases": set(),
        "dataitemid": 3058,
        "spgi_name": "Dividends per share",
    },
    {
        "name": "distributable_cash_per_share",
        "aliases": set(),
        "dataitemid": 23317,
        "spgi_name": "Distributable Cash per Share",
    },
    {
        "name": "diluted_eps_from_accounting_change_and_extraordinary_items",
        "aliases": {
            "diluted_earning_per_share_from_accounting_change_and_extraordinary_items",
        },
        "dataitemid": 44,
        "spgi_name": "Diluted EPS - Extraordinary Items & Accounting Change",
    },
    {
        "name": "diluted_eps_from_accounting_change",
        "aliases": {
            "diluted_earning_per_share_from_accounting_change",
        },
        "dataitemid": 141,
        "spgi_name": "Diluted EPS - Accounting Change",
    },
    {
        "name": "diluted_eps_from_extraordinary_items",
        "aliases": {
            "diluted_earning_per_share_from_extraordinary_items",
        },
        "dataitemid": 144,
        "spgi_name": "Diluted EPS - Extraordinary Items",
    },
    {
        "name": "diluted_eps_from_discontinued_operations",
        "aliases": {
            "diluted_earning_per_share_from_discontinued_operations",
        },
        "dataitemid": 143,
        "spgi_name": "Diluted EPS - Discontinued Operations",
    },
    {
        "name": "funds_from_operations",
        "aliases": {
            "ffo",
        },
        "dataitemid": 3074,
        "spgi_name": "FFO",
    },
    {
        "name": "ebitda",
        "aliases": {
            "earnings_before_interest_taxes_depreciation_and_amortization",
        },
        "dataitemid": 4051,
        "spgi_name": "EBITDA",
    },
    {
        "name": "ebita",
        "aliases": {
            "earnings_before_interest_taxes_and_amortization",
        },
        "dataitemid": 100689,
        "spgi_name": "EBITA",
    },
    {
        "name": "ebit",
        "aliases": {
            "earnings_before_interest_and_taxes",
        },
        "dataitemid": 400,
        "spgi_name": "EBIT",
    },
    {
        "name": "ebitdar",
        "aliases": {
            "earnings_before_interest_taxes_depreciation_amortization_and_rental_expense",
        },
        "dataitemid": 21674,
        "spgi_name": "EBITDAR",
    },
    {"name": "net_debt", "aliases": set(), "dataitemid": 4364, "spgi_name": "Net Debt"},
    {
        "name": "effective_tax_rate",
        "aliases": {
            "tax_rate",
        },
        "dataitemid": 4376,
        "spgi_name": "Effective Tax Rate %",
    },
    {"name": "current_ratio", "aliases": set(), "dataitemid": 4030, "spgi_name": "Current Ratio"},
    {"name": "quick_ratio", "aliases": set(), "dataitemid": 4121, "spgi_name": "Quick Ratio"},
    {
        "name": "total_debt_to_capital",
        "aliases": set(),
        "dataitemid": 43907,
        "spgi_name": "Total Debt to Capital (%)",
    },
    {
        "name": "net_working_capital",
        "aliases": set(),
        "dataitemid": 1311,
        "spgi_name": "Net Working Capital",
    },
    {
        "name": "working_capital",
        "aliases": set(),
        "dataitemid": 4165,
        "spgi_name": "Working Capital",
    },
    {
        "name": "change_in_net_working_capital",
        "aliases": set(),
        "dataitemid": 4421,
        "spgi_name": "Change In Net Working Capital",
    },
    {
        "name": "total_debt",
        "aliases": set(),
        "dataitemid": 4173,
        "spgi_name": "Total Debt",
    },
    {
        "name": "total_debt_to_equity_ratio",
        "aliases": {
            "debt_ratio",
            "total_debt_ratio",
            "total_debt_to_total_equity",
            "total_debt_to_equity",
        },
        "dataitemid": 4034,
        "spgi_name": "Total Debt/Equity",
    },
]
LINE_ITEM_NAMES_AND_ALIASES: list[str] = list(
    chain(*[[line_item["name"]] + list(line_item["aliases"]) for line_item in LINE_ITEMS])
)
