from datetime import date
from decimal import Decimal
from itertools import chain
import logging
from typing import Any, TypedDict

from pydantic import BaseModel, Field, model_validator

from kfinance.client.models.date_and_period_models import EstimatePeriodType, EstimateType
from kfinance.client.models.type_aliases import Source
from kfinance.domains.line_items.line_item_models import get_line_item_to_descriptions_map


logger = logging.getLogger(__name__)


class LineItem(BaseModel):
    name: str
    value: Decimal | None
    sources: list[Source] = Field(default_factory=list)


class TickerEstimatesGroup(BaseModel):
    currency: str | None
    estimates: list[LineItem]


class CiqEstimatesPeriodData(BaseModel):
    period_end_date: date
    estimates: dict[str, TickerEstimatesGroup]

    @model_validator(mode="before")
    @classmethod
    def group_by_ticker(cls, data: Any) -> Any:
        """Group a flat list of estimates by ticker_or_company.

        The API returns estimates as a flat list with ticker_or_company and currency on each item.
        This validator groups them into a dict keyed by ticker_or_company.
        For example:
        Before:
        "FY2026": {
            "period_end_date": "2026-12-31",
            "estimates": [
                {
                    "name": "EPS Consensus High",
                    "value": "14.0",
                    "currency": "EUR",
                    "ticker_or_company": "Company Level"
                },
                {
                    "name": "Book Value / Share Consensus High",
                    "value": "114.5",
                    "currency": "USD",
                    "ticker_or_company": "ENXTAM: ASM",
                }
            ]
        }

        After:
        "FY2026": {
            "period_end_date": "2026-12-31",
            "estimates": {
            "Company Level": {
                "currency": "EUR",
                "estimates": [{"name": "EPS Consensus High", "value": "14.0"}]
            },
            "ENXTAM: ASM": {
                "currency": "USD",
                "estimates": [{"name": "Book Value / Share Consensus High", "value": "114.5"}]
            }
        }
        """
        if not isinstance(data, dict):
            return data
        raw_estimates = data.get("estimates")
        if not isinstance(raw_estimates, list):
            return data
        grouped: dict[str, dict[str, Any]] = {}
        for item in raw_estimates:
            if not isinstance(item, dict):
                return data
            ticker = item.get("ticker_or_company", "Company Level")
            if ticker not in grouped:
                grouped[ticker] = {"currency": item.get("currency"), "estimates": []}
            elif grouped[ticker]["currency"] is None and item.get("currency") is not None:
                grouped[ticker]["currency"] = item.get("currency")
            grouped[ticker]["estimates"].append({"name": item["name"], "value": item.get("value")})
        data = {**data, "estimates": grouped}
        return data


class VaEstimatesPeriodData(BaseModel):
    period_end_date: date
    estimates: list[LineItem]


class Estimates(BaseModel):
    estimate_type: EstimateType | str
    period_type: EstimatePeriodType


class CiqEstimates(Estimates):
    estimate_type: EstimateType
    periods: dict[str, CiqEstimatesPeriodData]

    def remove_all_periods_other_than_the_most_recent_one(self) -> None:
        """Remove all period data other than the most recent one."""
        if self.periods:
            most_recent_period = max(self.periods.keys())
            most_recent_period_data = self.periods[most_recent_period]
            self.periods = {most_recent_period: most_recent_period_data}


class VisibleAlphaEstimates(Estimates):
    estimate_type: str
    currency: str | None
    periods: dict[str, VaEstimatesPeriodData]


class ConsensusTargetPriceItem(BaseModel):
    name: str
    value: Decimal | None


class ConsensusTargetPrice(BaseModel):
    currency: str | None
    effective_date: date
    estimates: list[ConsensusTargetPriceItem]


class AnalystRecommendationsItem(BaseModel):
    name: str
    value: Decimal | None


class AnalystRecommendations(BaseModel):
    effective_date: date | None
    estimates: list[AnalystRecommendationsItem]

class EstimateLineItemType(TypedDict):
    name: str
    aliases: set[str]
    dataitemids: set[int]
    spgi_name: str
    description: str

CONSENSUS_LINE_ITEMS: list[EstimateLineItemType] = [
    {
        "name": "adjusted_ffo_reit",
        "aliases": set(),
        "dataitemids": {105101, 105103, 105099, 105100, 105097, 105098},
        "spgi_name": "Adjusted FFO (REIT)",
        "description": "Adjusted FFO metric uses as a financial measure of REITs operating performance. The AFFO of a REIT, though subject to varying methods of computation, is generally equal to funds from operations (FFO) adjusted for maintenance capital expenditures. Analyst calculations also take into account GAAP straight-lining of rent, leasing costs and other material factors.",
    },
    {
        "name": "adjusted_ffo_per_share_reit",
        "aliases": set(),
        "dataitemids": {114159, 114154, 114156, 114158, 114155, 114157},
        "spgi_name": "Adjusted FFO / Share (REIT)",
        "description": "Adjusted FFO/Share metric uses as a financial measure of REITs operating performance. The AFFO of a REIT, though subject to varying methods of computation, is generally equal to funds from operations (FFO) adjusted for maintenance capital expenditures. Analyst calculations also take into account GAAP straight-lining of rent, leasing costs and other material factors which divided by the average number of shares in issue.",
    },
    {
        "name": "average_daily_production_gas",
        "aliases": set(),
        "dataitemids": {115466, 115468, 115464, 115465, 115462, 115463},
        "spgi_name": "Average Daily Production (Gas)",
        "description": "Average Daily Production (Gas) Estimate as the ratio of the total production of natural gas at a mining operation to the total number of production days worked at the operation.",
    },
    {
        "name": "average_daily_production_ngl",
        "aliases": set(),
        "dataitemids": {115440, 115442, 115438, 115439, 115436, 115437},
        "spgi_name": "Average Daily Production (NGL)",
        "description": "Average Daily Production (NGL) Estimate as the quantity of natural gas liquids produced per day.",
    },
    {
        "name": "average_daily_production_oil",
        "aliases": set(),
        "dataitemids": {115414, 115416, 115412, 115413, 115410, 115411},
        "spgi_name": "Average Daily Production (Oil)",
        "description": "Average Daily Production (Oil) Estimate as the quantity of oil produced per day.",
    },
    {
        "name": "book_value_per_share",
        "aliases": set(),
        "dataitemids": {104059, 104061, 104057, 104058, 104055, 104056},
        "spgi_name": "Book Value / Share",
        "description": "A measure used by owners of common shares in a firm to determine the level of safety associated with each individual share after all debts have been paid.",
    },
    {
        "name": "capital_expenditure",
        "aliases": set(),
        "dataitemids": {104094, 104096, 104092, 104093, 104090, 104091},
        "spgi_name": "Capital Expenditure",
        "description": "The outlay of money to acquire or improve capital assets such as buildings or machinery.",
    },
    {
        "name": "cash_eps",
        "aliases": set(),
        "dataitemids": {105308, 105307, 105304, 105305, 105302, 105303},
        "spgi_name": "Cash EPS",
        "description": "The portion of a company's profit plus non-cash items which allocated to each outstanding share of common stock. Cash EPS is a company's net income, plus depreciation, plus amortization of goodwill, intangibles, and prepaid assets (non-cash items), divided by diluted weighted average shares outstanding.",
    },
    {
        "name": "cash_flow_per_share",
        "aliases": set(),
        "dataitemids": {100205, 100207, 100203, 100204, 100201, 100202},
        "spgi_name": "Cash Flow / Share",
        "description": "Net earnings excluding the non-cash items depreciation and amortization but including the cash items net interest and taxation divided by the weighted average number of diluted shares outstanding.",
    },
    {
        "name": "cash_from_operations",
        "aliases": set(),
        "dataitemids": {104080, 104082, 104078, 104079, 104076, 104077},
        "spgi_name": "Cash From Operations",
        "description": "Net cash used or generated in operating activities during the stated period of time. It reflects the net impact of all operating activity transactions on the cash flow of the entity.",
    },
    {
        "name": "dps",
        "aliases": set(),
        "dataitemids": {100212, 100214, 100210, 100211, 100208, 100209},
        "spgi_name": "DPS",
        "description": "The total dividend payment made by a company to its shareholders divided by weighted average number of diluted shares outstanding.",
    },
    {
        "name": "depreciation_and_amortization",
        "aliases": set(),
        "dataitemids": {114192, 114187, 114189, 114191, 114188, 114190},
        "spgi_name": "Depreciation & Amortization",
        "description": "Non-cash periodic charge on the account of wear and tear of fixed assets used in the business. This item also includes amortization of all intangible assets and goodwill.",
    },
    {
        "name": "distributable_cash_income_trusts",
        "aliases": set(),
        "dataitemids": {105073, 105075, 105071, 105072, 105069, 105070},
        "spgi_name": "Distributable Cash (Income Trusts)",
        "description": "Distributable cash is a term unique to income funds and trusts. Distributable Cash as the net cash generated by the operating entity's business that is ultimately available for distribution to the income trust's unit holders.",
    },
    {
        "name": "distributable_cash_per_share_income_trust",
        "aliases": set(),
        "dataitemids": {105080, 105082, 105078, 105079, 105076, 105077},
        "spgi_name": "Distributable Cash / Share (Income Trust)",
        "description": "Distributable cash is a term unique to income funds and trusts. Distributable Cash as the net cash generated by the operating entity's business that is ultimately available for distribution to the income trust's unit holders. Total amount of Distributable Cash/Cash Distributions divided by the total number of units or shares issued and held by holders entitled to cash distribution.",
    },
    {
        "name": "ebit",
        "aliases": set(),
        "dataitemids": {100219, 100221, 100217, 100218, 100215, 100216},
        "spgi_name": "EBIT",
        "description": "Revenues minus expenses excluding the effects of interest expense or expense and taxation. EBIT includes both operating and non-operating income. EBIT is often used as a measure of a company's operating performance.",
    },
    {
        "name": "ebitda",
        "aliases": set(),
        "dataitemids": {100191, 100193, 100189, 100190, 100187, 100188},
        "spgi_name": "EBITDA",
        "description": "Revenues minus expenses excluding the effects of interest income or expense, taxation, depreciation and amortization. EBITDA includes both operating and non-operating income. EBITDA is often used to analyze the potential cash flow of a company or to compare companies' operating performance without the distorting effects of amortization and depreciation.",
    },
    {
        "name": "ebt_excl_excep_and_gw",
        "aliases": set(),
        "dataitemids": {100240, 100242, 100238, 100239, 100236, 100237},
        "spgi_name": "EBT (Excl. Excep & GW)",
        "description": "Revenue minus all expenses including operating and non-operating, interest expense and income adjusted to exclude the effects of exceptional items and Amortization of Goodwill.",
    },
    {
        "name": "ebt_gaap",
        "aliases": set(),
        "dataitemids": {100247, 100249, 100245, 100246, 100243, 100244},
        "spgi_name": "EBT (GAAP)",
        "description": "Revenue minus all expenses including operating and non-operating, interest expense and income.",
    },
    {
        "name": "ebt_normalized",
        "aliases": set(),
        "dataitemids": {100233, 100235, 100231, 100232, 100229, 100230},
        "spgi_name": "EBT Normalized",
        "description": "Revenue minus all expenses including operating and non-operating, interest expense and income adjusted to exclude the effects of exceptional items. In Japan Pre Tax Profit pre-exceptional items is more popularly known as Recurring Profit.",
    },
    {
        "name": "eps_excl_excep_and_gw",
        "aliases": set(),
        "dataitemids": {100275, 100277, 100273, 100274, 100271, 100272},
        "spgi_name": "EPS (Excl. Excep & GW)",
        "description": "The profit of a company from continuing operations and usually excludes unusual items, accounting changes, stock based compensation, goodwill amortization, and discontinued operations divided by the number of common shares outstanding (diluted).",
    },
    {
        "name": "eps_gaap",
        "aliases": set(),
        "dataitemids": {100282, 100284, 100280, 100281, 100278, 100279},
        "spgi_name": "EPS (GAAP)",
        "description": "The portion of a company's profit allocated to each outstanding share of common stock (diluted). EPS serves as an indicator of a company's profitability. It includes all one-time, exceptional or extraordinary incomes/expenditures.",
    },
    {
        "name": "eps_lt_growth",
        "aliases": set(),
        "dataitemids": {100171, 100169, 100170, 100167, 100168},
        "spgi_name": "EPS LT Growth",
        "description": "Long-term growth is an estimate of the average rate of earnings growth an analyst expects over a three to five year period and is expressed as a percentage increase per year. Long-term growth is non-periodic estimate in that the estimate is not for a specified time period. As such, there will be only one estimate (not the usual three forward yearly estimates) and will not have actual figures.",
    },
    {
        "name": "eps_normalized",
        "aliases": set(),
        "dataitemids": {100177, 100179, 100175, 100176, 100173, 100174},
        "spgi_name": "EPS Normalized",
        "description": "The profit of a company from continuing operations and usually excludes unusual items, accounting changes, stock based compensation, and discontinued operations divided by the number of common shares outstanding (diluted).",
    },
    {
        "name": "effective_tax_rate",
        "aliases": set(),
        "dataitemids": {114170, 114165, 114167, 114169, 114166, 114168},
        "spgi_name": "Effective Tax Rate",
        "description": "Effective Tax Rate as the net rate a company pays on income that includes all forms of taxes. It is calculated by dividing the total tax paid by taxable income.",
    },
    {
        "name": "exploration_expense",
        "aliases": set(),
        "dataitemids": {115531, 115533, 115529, 115530, 115527, 115528},
        "spgi_name": "Exploration Expense",
        "description": "The cost which an oil or gas company incurs while searching for oil or gas to drill is known as exploration expense. It includes the cost of researching appropriate places to drill, premium payments associated with acquisition of new acreage, costs incurred in evaluating commercial viability of geological entities and the cost of actually drilling.",
    },
    {
        "name": "ffo_reit",
        "aliases": set(),
        "dataitemids": {105112, 105114, 105110, 105111, 105108, 105109},
        "spgi_name": "FFO (REIT)",
        "description": "Net income excluding gains or losses from sales of property or debt restructuring, adding back depreciation and amortization of real estate and after adjustments for unconsolidated partnerships and joint ventures. FFO includes both recurring and non-recurring results of operations. This figure represents a supplemental measure of a company's operating performance, is used to define the cash flow from trust operations, and is provided for North American Real Estate Investment Trust Companies only.",
    },
    {
        "name": "ffo_per_share_reit",
        "aliases": set(),
        "dataitemids": {100198, 100200, 100196, 100197, 100194, 100195},
        "spgi_name": "FFO / Share (REIT)",
        "description": "Net income excluding gains or losses from sales of property or debt restructuring, adding back depreciation and amortization of real estate and after adjustments for unconsolidated partnerships and joint ventures. This amount is then divided by the diluted weighted average number of shares in issue. FFO includes both recurring and non-recurring results of operations. This figure represents a supplemental measure of a company's operating performance, is used to define the cash flow from trust operations, and is provided for North American Real Estate Investment Trust Companies only.",
    },
    {
        "name": "free_cash_flow",
        "aliases": set(),
        "dataitemids": {114225, 114220, 114222, 114224, 114221, 114223},
        "spgi_name": "Free Cash Flow",
        "description": "Free cash flow represents the cash that a company is able to generate after laying out the money required to maintain or expand its asset base.",
    },
    {
        "name": "gross_margin",
        "aliases": set(),
        "dataitemids": {105297, 105299, 105295, 105296, 105293, 105294},
        "spgi_name": "Gross Margin",
        "description": "company's total revenue minus cost of goods sold, divided by the total revenue, expressed as a percentage.",
    },
    {
        "name": "industry_net_asset_value_per_share_non_periodic",
        "aliases": set(),
        "dataitemids": {114214, 114209, 114211, 114213, 114210, 114212},
        "spgi_name": "Industry Net Asset Value / Share (Non Periodic)",
        "description": "The market value of an entity's assets less the market value of its liabilities. Industry NAVPS in various ways and S&P Global employs its majority methodology to ensure Industry NAV/Share is consistent for any particular Consensus estimate.",
    },
    {
        "name": "interest_expense",
        "aliases": set(),
        "dataitemids": {114181, 114176, 114178, 114180, 114177, 114179},
        "spgi_name": "Interest Expense",
        "description": "Interest Expense as the amount a company pays in interest on the debt borrowed.",
    },
    {
        "name": "maintenance_capital_expenditure",
        "aliases": set(),
        "dataitemids": {105066, 105068, 105064, 105065, 105062, 105063},
        "spgi_name": "Maintenance Capital Expenditure",
        "description": "Maintenance CAPEX as the expenditure to keep existing operations going at their current levels and to maintain a company's assets.",
    },
    {
        "name": "net_asset_value",
        "aliases": set(),
        "dataitemids": {105123, 105125, 105121, 105122, 105119, 105120},
        "spgi_name": "Net Asset Value",
        "description": "The tangible book value of a company's assets minus its current and long term liabilities adjusted as appropriate.",
    },
    {
        "name": "net_asset_value_per_share",
        "aliases": set(),
        "dataitemids": {105322, 105321, 105318, 105319, 105316, 105317},
        "spgi_name": "Net Asset Value / Share",
        "description": "The tangible book value of a company's assets minus its current and long term liabilities adjusted as appropriate and divided by the shares in issue at year-end. NAVPS is often used as an indication that a stock may be undervalued or overvalued in relation to the physical asset worth.",
    },
    {
        "name": "net_debt",
        "aliases": set(),
        "dataitemids": {104101, 104103, 104099, 104100, 104097, 104098},
        "spgi_name": "Net Debt",
        "description": "Short term and long term interest-bearing debt minus cash and cash equivalents.",
    },
    {
        "name": "net_income_excl_excep_and_gw",
        "aliases": set(),
        "dataitemids": {100261, 100263, 100259, 100260, 100257, 100258},
        "spgi_name": "Net Income (Excl. Excep & GW)",
        "description": "Revenue minus all expenses including operating and non-operating expenses, interest income and expense, and taxation adjusted to exclude the effects of exceptional items and amortization of goodwill.",
    },
    {
        "name": "net_income_gaap",
        "aliases": set(),
        "dataitemids": {100268, 100270, 100266, 100267, 100264, 100265},
        "spgi_name": "Net Income (GAAP)",
        "description": "Revenue minus all expenses including operating and non-operating, interest expense and income and taxation.",
    },
    {
        "name": "net_income_normalized",
        "aliases": set(),
        "dataitemids": {100254, 100256, 100252, 100253, 100250, 100251},
        "spgi_name": "Net Income Normalized",
        "description": "Revenue minus all expenses including operating and non-operating, interest income and expense, and taxation adjusted to exclude the effects of exceptional items.",
    },
    {
        "name": "periodic_target_price",
        "aliases": set(),
        "dataitemids": {112026, 112024, 112025, 112022, 112023},
        "spgi_name": "Periodic Target Price",
        "description": "Target Price should be Periodic and non-periodic Target Price is not available. S&P Global provides only nominal price assumptions for commodities Target Price.",
    },
    {
        "name": "return_on_assets",
        "aliases": set(),
        "dataitemids": {104122, 104124, 104120, 104121, 104118, 104119},
        "spgi_name": "Return on Assets",
        "description": "A measure to judge the profitability of the company in relation to its total assets. It is calculated by dividing a company's annual earnings by its total assets. ROA indicates what earnings were generated from invested capital (assets).",
    },
    {
        "name": "return_on_equity",
        "aliases": set(),
        "dataitemids": {104115, 104117, 104113, 104114, 104111, 104112},
        "spgi_name": "Return on Equity",
        "description": "This ratio represents earnings from continuing operations divided by average total equity and is expressed as a percent.",
    },
    {
        "name": "revenue",
        "aliases": set(),
        "dataitemids": {100184, 100186, 100182, 100183, 100180, 100181},
        "spgi_name": "Revenue",
        "description": "The total amount of money billed for a company's products or services.",
    },
    {
        "name": "revenues_gas",
        "aliases": set(),
        "dataitemids": {115518, 115520, 115516, 115517, 115514, 115515},
        "spgi_name": "Revenues (Gas)",
        "description": "Revenue (Gas) Estimate as the portion of total revenues of a company generated from the sale of the gas produced or extracted during a period.",
    },
    {
        "name": "revenues_ngl",
        "aliases": set(),
        "dataitemids": {115505, 115507, 115503, 115504, 115501, 115502},
        "spgi_name": "Revenues (NGL)",
        "description": "Revenue (NGL) Estimate as the portion of total revenues of a company generated from the sale of the natural gas liquids produced during a period.",
    },
    {
        "name": "revenues_oil",
        "aliases": set(),
        "dataitemids": {115492, 115494, 115490, 115491, 115488, 115489},
        "spgi_name": "Revenues (Oil)",
        "description": "Revenue (Oil) Estimate as the portion of total revenues of a company generated from the sale of the oil produced or extracted during a period.",
    },
    {
        "name": "same_store_sales_growth",
        "aliases": set(),
        "dataitemids": {114203, 114198, 114200, 114202, 114199, 114201},
        "spgi_name": "Same Store Sales Growth",
        "description": "Same Store Sales Growth as a percentage of revenue growth generated by retail chains over a certain amount of time, which is then compared to an identical period in the past, usually in the previous year. This only includes stores that have been operating for over a year or more."
    },
    {
        "name": "tev",
        "aliases": set(),
        "dataitemids": {104017, 104019, 104015, 104016, 104013, 104014},
        "spgi_name": "TEV",
        "description": "The cash- less value of a firm as an asset based on the market value of its debt and equity. In theory, this should be equal to the present value of expected cash flows discounted at the Weighted Average Cost of Capital (WACC).",
    },
    {
        "name": "target_price",
        "aliases": set(),
        "dataitemids": {100165, 100163, 100164, 100161, 100162},
        "spgi_name": "Target Price",
        "description": "The short-term target price as provided by contributing brokers. Short-term target prices cover a horizon between 0 and 18 months, with a horizon of 6 to 12 months being the most widely used. Price target is a non-periodic estimate. The estimate is not for a specified time period and as such will only have one estimate, unlike the usual multiple estimates and will also have no comparable actual figure."
    },
    {
        "name": "total_average_daily_production",
        "aliases": set(),
        "dataitemids": {115479, 115481, 115477, 115478, 115475, 115476},
        "spgi_name": "Total Average Daily Production",
        "description": "Total Average Daily Production Estimate as production is a measure of the amount of gas or other hydrocarbons that are produced from wells that a gas company has interests in. Since the outputs of crude oil and natural gas liquids are measured in terms of barrels, and output of natural gas is measured in cubic feet/cubic meters, there must be a way to convert each hydrocarbon to a standardized form of measurement so that the total production of a company can be analyzed."
    },
    {
        "name": "total_production_gas",
        "aliases": set(),
        "dataitemids": {115453, 115455, 115451, 115452, 115449, 115450},
        "spgi_name": "Total Production (Gas)",
        "description": "Total Production (Gas) Estimate as the total quantity of gas produced during a particular period. Gas withdrawn from reservoirs is reduced by volumes used at the production (lease) site and by processing losses. Volumes of dry gas withdrawn from gas storage reservoirs are not considered part of production. Dry natural gas production equals marketed production less extraction loss.",
    },
    {
        "name": "total_production_ngl",
        "aliases": set(),
        "dataitemids": {115427, 115429, 115425, 115426, 115423, 115424},
        "spgi_name": "Total Production (NGL)",
        "description": "Total Production (NGL) Estimate as the total volume of natural gas liquids removed from natural gas in lease separators, field facilities, gas processing plants or cycling plants during the reported period.",
    },
    {
        "name": "total_production_oil",
        "aliases": set(),
        "dataitemids": {115401, 115403, 115399, 115400, 115397, 115398},
        "spgi_name": "Total Production (Oil)",
        "description": "Total Production (Oil) Estimate as the total quantity of oil produced during a particular period. Oil is also referred to as Crude Oil, Petroleum, Coal Oil, Rock oil, Fossil Oil, etc.",
    },
    {
        "name": "total_production",
        "aliases": set(),
        "dataitemids": {115589, 115591, 115587, 115588, 115585, 115586},
        "spgi_name": "Total Production",
        "description": "Total Production Estimate as production is a measure of the amount of gas or other hydrocarbons that are produced from wells that a gas company has interests in. Since the outputs of crude oil and natural gas liquids are measured in terms of barrels, and output of natural gas is measured in cubic feet/cubic meters, there must be a way to convert each hydrocarbon to a standardized form of measurement so that the total production of a company can be analyzed.",
    },
]

CONSENSUS_LINE_ITEM_NAMES_AND_ALIASES: list[str] = list(
    chain(*[[line_item["name"]] + list(line_item["aliases"]) for line_item in CONSENSUS_LINE_ITEMS])
)

CONSENSUS_LINE_ITEM_TO_DESCRIPTIONS_MAP: dict[str, str] = get_line_item_to_descriptions_map(CONSENSUS_LINE_ITEMS)


GUIDANCE_LINE_ITEM_NAMES_AND_ALIASES: list[EstimateLineItemType] = [
    {
        "name": "adjusted_ffo_reit",
        "aliases": set(),
        "dataitemids": {22436, 22496, 22368},
        "spgi_name": "Adjusted FFO (REIT)",
        "description": "Adjusted FFO metric uses as a financial measure of REITs operating performance. The AFFO of a REIT, though subject to varying methods of computation, is generally equal to funds from operations (FFO) adjusted for maintenance capital expenditures. Analyst calculations also take into account GAAP straight-lining of rent, leasing costs and other material factors."
    },
    {
        "name": "adjusted_ffo_per_share_reit",
        "aliases": set(),
        "dataitemids": {114161, 114163, 114162},
        "spgi_name": "Adjusted FFO / Share (REIT)",
        "description": "Adjusted FFO/Share metric uses as a financial measure of REITs operating performance. The AFFO of a REIT, though subject to varying methods of computation, is generally equal to funds from operations (FFO) adjusted for maintenance capital expenditures. Analyst calculations also take into account GAAP straight-lining of rent, leasing costs and other material factors which divided by the average number of shares in issue."
    },
    {
        "name": "assets_under_management",
        "aliases": set(),
        "dataitemids": {602733, 602734, 602732},
        "spgi_name": "Assets Under Management",
        "description": "Assets Under Management(AUM) is the total market value of all investments /funds that a person or entity manages on behalf of clients.AUM definitions and formulas vary by company. In the calculation of AUM, some financial institutions include bank deposits, mutual funds, and cash in their calculations. Others limit it to funds under discretionary management , where the investor assigns authority to the company to trade on their behalf. Over all, AUM is only one aspect used in evaluating a company or investment. It is also usually considered in conjunction with management performance and management experience. However investor often consider higher investment inflows and higher AUM comparisons as a positive indicator of quality and management experience."
    },
    {
        "name": "available_seat_kms",
        "aliases": set(),
        "dataitemids": {603292, 603293, 603291},
        "spgi_name": "Available Seat Kms",
        "description": "A measure of an airline's carrying capacity to generate revenue. Available Seat Kilometers (ASK) captures the total flight passenger capacity of an airline in kilometers. It is obtained by multiplying the total number of seats available for scheduled passengers and the total number of kilometers in which those seats were flown.",
    },
    {
        "name": "available_seat_miles",
        "aliases": set(),
        "dataitemids": {604399, 604400, 604398},
        "spgi_name": "Available Seat Miles",
        "description": "A measure of an airline's carrying capacity to generate revenue. Available Seat Miles (ASM) captures the total flight passenger capacity of an airline in Miles. It is obtained by multiplying the total number of seats available for scheduled passengers and the total number of Miles in which those seats were flown.",
    },
    {
        "name": "average_daily_production_gas",
        "aliases": set(),
        "dataitemids": {115472, 115473, 115471},
        "spgi_name": "Average Daily Production (Gas)",
        "description": "Average Daily Production (Gas) Estimate as the ratio of the total production of natural gas at a mining operation to the total number of production days worked at the operation."
    },
    {
        "name": "average_daily_production_ngl",
        "aliases": set(),
        "dataitemids": {115446, 115447, 115445},
        "spgi_name": "Average Daily Production (NGL)",
        "description": "Average Daily Production (NGL) Estimate as the quantity of natural gas liquids produced per day."
    },
    {
        "name": "average_daily_production_oil",
        "aliases": set(),
        "dataitemids": {115420, 115421, 115419},
        "spgi_name": "Average Daily Production (Oil)",
        "description": "Average Daily Production (Oil) Estimate as the quantity of oil produced per day."
    },
    {
        "name": "average_earning_assets",
        "aliases": set(),
        "dataitemids": {600405, 600457, 600353},
        "spgi_name": "Average Earning Assets",
        "description": "A company’s earning assets are investments that produce income without any significant effort on its owner’s part. Some popular earning assets are stocks, bonds, certificates of deposits, notes, etc.A company’s earning assets are investments that produce income without any significant effort on its owner’s part. Some popular earning assets are stocks, bonds, certificates of deposits, notes, etc. To calculate the average earning assets, simply take the average of the beginning and ending asset balance."
    },
    {
        "name": "average_revenue_per_user",
        "aliases": set(),
        "dataitemids": {602746, 602747, 602745},
        "spgi_name": "Average Revenue Per User",
        "description": "Average revenue per unit (ARPU) is an indicator of the profitability of a product based on the amount of money that is generated from each of its users or subscribers. It is a particularly useful measurement for companies in the telecommunications and media industries, which rely on subscribers or users.ARPU= Total Revenue / Number of units, users, or subscribers.",
    },
    {
        "name": "avg_deposits",
        "aliases": set(),
        "dataitemids": {601377, 601378, 601379},
        "spgi_name": "Avg. Deposits",
        "description": "The difference between an average and standard balance sheet is that balances are expressed as average amounts rather than actual period-end amounts. An average balance is computed as the sum of the actual daily closing balance for a balance sheet account, divided by the number of calendar days in the reporting period.",
    },
    {
        "name": "avg_diluted_shares_outstanding",
        "aliases": set(),
        "dataitemids": {600420, 600472, 600368},
        "spgi_name": "Avg. Diluted Shares Outstanding",
        "description": "The number of shares outstanding in a company will often change due to a company issuing new shares, repurchasing shares, and retiring existing shares. Diluted Weighted Average Shares are the common shares that would be outstanding, if all convertible securities were converted to common stock, on average over the period, using the time-weighting factor."
    },
    {
        "name": "avg_loans",
        "aliases": set(),
        "dataitemids": {601390, 601391, 601392},
        "spgi_name": "Avg. Loans",
        "description": "The difference between an average and standard balance sheet is that balances are expressed as average amounts rather than actual period-end amounts. An average balance is computed as the sum of the actual daily closing balance for a balance sheet account, divided by the number of calendar days in the reporting period.",
    },
    {
        "name": "backlog_units",
        "aliases": set(),
        "dataitemids": {603331, 603332, 603330},
        "spgi_name": "Backlog (Units)",
        "description": "Backlog Units means the residential housing units which are the subjects of Existing Purchase Agreements, but which are not scheduled to close as of or prior to the Closing Date.",
    },
    {
        "name": "backlog_average_price",
        "aliases": set(),
        "dataitemids": {603357, 603358, 603356},
        "spgi_name": "Backlog Average Price",
        "description": "Backlog avg. price refers to price per order which are yet not been completed/filled. Here ‘Backlog’ refers to when the number of orders a company has taken but hasn’t yet completed. It is common in growing businesses and can indicate a higher demand for a product.",
    },
    {
        "name": "backlog_value",
        "aliases": set(),
        "dataitemids": {602759, 602760, 602758},
        "spgi_name": "Backlog Value",
        "description": "Homes in Backlog represents the number of housing units subject to pending sales contracts at the end of the period. Homes covered by sales contracts but not yet closed or completed at the end of the period are considered in backlog.",
    },
    {
        "name": "book_value_per_share",
        "aliases": set(),
        "dataitemids": {22387, 22447, 22319},
        "spgi_name": "Book Value / Share",
        "description": "A measure used by owners of common shares in a firm to determine the level of safety associated with each individual share after all debts have been paid."
    },
    {
        "name": "book_value_per_share_excl_aoci",
        "aliases": set(),
        "dataitemids": {602772, 602773, 602771},
        "spgi_name": "Book Value / Share Excl. AOCI",
        "description": "Book value per share excluding AOCI (diluted) means the per share amount of shareholders' equity excluding AOCI to the number of diluted common shares outstanding at a specified date. Diluted common shares outstanding takes into account all of the outstanding dilutive securities that could potentially be exercised.",
    },
    {
        "name": "capital_expenditure",
        "aliases": set(),
        "dataitemids": {22402, 22462, 22334},
        "spgi_name": "Capital Expenditure",
        "description": "The outlay of money to acquire or improve capital assets such as buildings or machinery."
    },
    {
        "name": "cash_eps",
        "aliases": set(),
        "dataitemids": {114233, 114235, 114234},
        "spgi_name": "Cash EPS",
        "description": "The portion of a company's profit plus non-cash items which allocated to each outstanding share of common stock. Cash EPS is a company's net income, plus depreciation, plus amortization of goodwill, intangibles, and prepaid assets (non-cash items), divided by diluted weighted average shares outstanding.",
    },
    {
        "name": "cash_flow_per_share",
        "aliases": set(),
        "dataitemids": {22386, 22446, 22318},
        "spgi_name": "Cash Flow / Share",
        "description": "Net earnings excluding the non-cash items depreciation and amortization but including the cash items net interest and taxation divided by the weighted average number of diluted shares outstanding.",
    },
    {
        "name": "cash_from_operations",
        "aliases": set(),
        "dataitemids": {22409, 22469, 22341},
        "spgi_name": "Cash From Operations",
        "description": "Net cash used or generated in operating activities during the stated period of time. It reflects the net impact of all operating activity transactions on the cash flow of the entity."
    },
    {
        "name": "churn_rate",
        "aliases": set(),
        "dataitemids": {603435, 603436, 603434},
        "spgi_name": "Churn Rate",
        "description": "Churn rate is the percentage of subscribers who discontinue or do not renew their subscription. Churn rate is calculated as the number of disconnected subscribers divided by the number of beginning subscribers. Churn rate measures service efficiency. Churn Rate = # of disconnected subscribers / Subscribers beginning of month x 100."
    },
    {
        "name": "coal_production",
        "aliases": set(),
        "dataitemids": {600424, 600476, 600372},
        "spgi_name": "Coal - Production",
        "description": "Coal production volumes represents the quality of Coal produced during a particular period by the Coal companies that are involved in Coal exploration and mining."
    },
    {
        "name": "combined_ratio",
        "aliases": set(),
        "dataitemids": {600412, 600464, 600360},
        "spgi_name": "Combined Ratio",
        "description": "Combined Ratio (%) represents the combination of Loss ratio and Expense ratio after considering policyholders dividends. A measure of profitability used by an insurance company to indicate how well it is performing in its daily operations.",
    },
    {
        "name": "common_equity_tier_1_ratio",
        "aliases": set(),
        "dataitemids": {603409, 603410, 603408},
        "spgi_name": "Common Equity Tier 1 Ratio",
        "description": "Common Equity Tier 1 (CET1) capital includes the core capital that a bank holds in its capital structure. CET1 ratio compares a bank's capital against its risk-weighted assets to determine its ability to withstand financial distress. The core capital of a bank includes equity capital and disclosed reserves such as retained earnings.",
    },
    {
        "name": "copper_production",
        "aliases": set(),
        "dataitemids": {600423, 600475, 600371},
        "spgi_name": "Copper - Production",
        "description": "Copper production volumes represents the quality of Copper produced during a particular period by the Copper companies that are involved in Copper exploration and mining.",
    },
    {
        "name": "dps",
        "aliases": set(),
        "dataitemids": {22388, 22448, 22320},
        "spgi_name": "DPS",
        "description": "The total dividend payment made by a company to its shareholders divided by weighted average number of diluted shares outstanding.",
    },
    {
        "name": "debt_adjusted_cash_flow",
        "aliases": set(),
        "dataitemids": {604163, 604164, 604162},
        "spgi_name": "Debt Adjusted Cash Flow",
        "description": "Debt-Adjusted cash flow (DACF) is a financial metric that represents pre-tax operating cash flow (OCF) adjusted for financing expenses after taxes. It is most commonly used to analyze the oil companies. Adjustments for exploration costs may also be included, as these vary from company to company depending on the accounting method used. By adding the exploration costs, the effect of the different accounting methods is removed. DACF is useful because companies finance themselves differently, with some relying more on debt.",
    },
    {
        "name": "deliveries_units",
        "aliases": set(),
        "dataitemids": {603318, 603319, 603317},
        "spgi_name": "Deliveries (Units)",
        "description": "Delivered represents the number of homes and condominiums that are delivered and treated as closings or deliveries at the end of the period. Here the main participants related can be Owners, Renters, and facilitator.",
    },
    {
        "name": "deliveries_average_price",
        "aliases": set(),
        "dataitemids": {602824, 602825, 602823},
        "spgi_name": "Deliveries Average Price",
        "description": "Deliveries Average Price represents the average selling price of homes and condominiums that are delivered and treated as closings or deliveries at the end of the period.",
    },
    {
        "name": "deposits_eop",
        "aliases": set(),
        "dataitemids": {600404, 600456, 600352},
        "spgi_name": "Deposits - EoP",
        "description": "The term 'Deposits' represents the sum of all types of deposits made by customers and deposits from financial institutions through a variety of accounts such as Savings Accounts, checking accounts and money market accounts. From the banks? viewpoint, Deposits are the liability that the bank must repay on agreed. Total Deposits comprises all categories of deposits such as Demand Deposits, Time Deposits, Savings Deposits, and other deposits. terms.",
    },
    {
        "name": "depreciation_and_amortization",
        "aliases": set(),
        "dataitemids": {114194, 114196, 114195},
        "spgi_name": "Depreciation & Amortization",
        "description": "Non-cash periodic charge on the account of wear and tear of fixed assets used in the business. This item also includes amortization of all intangible assets and goodwill.",
    },
    {
        "name": "distributable_cash",
        "aliases": set(),
        "dataitemids": {22432, 22492, 22364},
        "spgi_name": "Distributable Cash",
        "description": "Distributable cash is a term unique to income funds and trusts. Distributable Cash as the net cash generated by the operating entity's business that is ultimately available for distribution to the income trust's unit holders.",
    },
    {
        "name": "distributable_cash_per_share",
        "aliases": set(),
        "dataitemids": {22433, 22493, 22365},
        "spgi_name": "Distributable Cash / Share",
        "description": "Distributable cash is a term unique to income funds and trusts. Distributable Cash as the net cash generated by the operating entity's business that is ultimately available for distribution to the income trust's unit holders. Total amount of Distributable Cash/Cash Distributions divided by the total number of units or shares issued and held by holders entitled to cash distribution.",
    },
    {
        "name": "ebit",
        "aliases": set(),
        "dataitemids": {22393, 22453, 22325},
        "spgi_name": "EBIT",
        "description": "Revenues minus expenses excluding the effects of interest expense or expense and taxation. EBIT includes both operating and non-operating income. EBIT is often used as a measure of a company's operating performance.",
    },
    {
        "name": "ebitda",
        "aliases": set(),
        "dataitemids": {22391, 22451, 22323},
        "spgi_name": "EBITDA",
        "description": "Revenues minus expenses excluding the effects of interest income or expense, taxation, depreciation and amortization. EBITDA includes both operating and non-operating income. EBITDA is often used to analyze the potential cash flow of a company or to compare companies' operating performance without the distorting effects of amortization and depreciation.",
    },
    {
        "name": "ebt_excl_excep_and_gw",
        "aliases": set(),
        "dataitemids": {22396, 22456, 22328},
        "spgi_name": "EBT (Excl. Excep & GW)",
        "description": "Revenue minus all expenses including operating and non-operating, interest expense and income adjusted to exclude the effects of exceptional items and Amortization of Goodwill.",
    },
    {
        "name": "ebt_gaap",
        "aliases": set(),
        "dataitemids": {22395, 22455, 22327},
        "spgi_name": "EBT (GAAP)",
        "description": "Revenue minus all expenses including operating and non-operating, interest expense and income.",
    },
    {
        "name": "ebt_normalized",
        "aliases": set(),
        "dataitemids": {22394, 22454, 22326},
        "spgi_name": "EBT Normalized",
        "description": "Revenue minus all expenses including operating and non-operating, interest expense and income adjusted to exclude the effects of exceptional items. In Japan Pre Tax Profit pre-exceptional items is more popularly known as Recurring Profit.",
    },
    {
        "name": "epra_net_tangible_assets",
        "aliases": set(),
        "dataitemids": {604215, 604216, 604214},
        "spgi_name": "EPRA Net Tangible Assets",
        "description": "EPRA Net Tangible Assets (EPRA NTA) is a proportionally consolidated measure, representing the IFRS net assets excluding the mark-to-market on derivatives and related debt adjustments, the mark-to-market on the convertible bonds, the carrying value of intangibles as well as deferred taxation on property and derivative valuations. It includes the valuation surplus on trading properties and is adjusted for the dilutive impact of share options.",
    },
    {
        "name": "epra_net_tangible_assets_per_share",
        "aliases": set(),
        "dataitemids": {604254, 604255, 604253},
        "spgi_name": "EPRA Net Tangible Assets / Share",
        "description": "EPRA Net Tangible Assets (EPRA NTA) is a proportionally consolidated measure, representing the IFRS net assets excluding the mark-to-market on derivatives and related debt adjustments, the mark-to-market on the convertible bonds, the carrying value of intangibles as well as deferred taxation on property and derivative valuations and this value is derived from the EPRA NTA/Shares. It includes the valuation surplus on trading properties and is adjusted for the dilutive impact of share options.",
    },
    {
        "name": "eps_excl_excep_and_gw",
        "aliases": set(),
        "dataitemids": {22385, 22445, 22317},
        "spgi_name": "EPS (Excl. Excep & GW)",
        "description": "The profit of a company from continuing operations and usually excludes unusual items, accounting changes, stock based compensation, goodwill amortization, and discontinued operations divided by the number of common shares outstanding (diluted).",
    },
    {
        "name": "eps_gaap",
        "aliases": set(),
        "dataitemids": {22384, 22444, 22316},
        "spgi_name": "EPS (GAAP)",
        "description": "The portion of a company's profit allocated to each outstanding share of common stock. EPS serves as an indicator of a company's profitability. It includes all one-time, exceptional or extraordinary incomes/expenditures.",
    },
    {
        "name": "eps_normalized",
        "aliases": set(),
        "dataitemids": {22383, 22443, 22315},
        "spgi_name": "EPS Normalized",
        "description": "The profit of a company from continuing operations and usually excludes unusual items, accounting changes, stock based compensation, and discontinued operations divided by the number of common shares outstanding (diluted).",
    },
    {
        "name": "effective_tax_rate",
        "aliases": set(),
        "dataitemids": {114172, 114174, 114173},
        "spgi_name": "Effective Tax Rate",
        "description": "Effective Tax Rate as the net rate a company pays on income that includes all forms of taxes. It is calculated by dividing the total tax paid by taxable income.",
    },
    {
        "name": "efficiency_ratio",
        "aliases": set(),
        "dataitemids": {601455, 601456, 601457},
        "spgi_name": "Efficiency Ratio",
        "description": "The standard definition of the Efficiency ratio is as non-interest expenses divided by the total of net interest income and non-interest income.",
    },
    {
        "name": "embedded_value",
        "aliases": set(),
        "dataitemids": {602850, 602851, 602849},
        "spgi_name": "Embedded Value",
        "description": "Embedded Value(EV ) is one of the indicators representing the corporate value of life insurance companies, that is attributed to shareholders. EV is the sum of \"adjusted net worth,\" which is the accumulation of realized profits, and \"value of in-force business,\" which is estimated future profits on in-force business.",
    },
    {
        "name": "expense_ratio",
        "aliases": set(),
        "dataitemids": {600417, 600469, 600365},
        "spgi_name": "Expense Ratio",
        "description": "This data item represents the percentage of a company's net premiums earned that went toward underwriting expenses, such as commissions to agents and brokers, state and municipal taxes, salaries, employee benefits and other operating costs.",
    },
    {
        "name": "exploration_costs",
        "aliases": set(),
        "dataitemids": {600428, 600480, 600376},
        "spgi_name": "Exploration Costs",
        "description": "Exploration costs mean the cost incurred for the search of mineral resources including minerals, oils, natural gas, and other similar non-regenerative resources after the entity has obtained the rights to explore in specific areas by determining technical feasibility and commercial viability of extracting the mineral resource.",
    },
    {
        "name": "exploration_expense",
        "aliases": set(),
        "dataitemids": {115537, 115538, 115536},
        "spgi_name": "Exploration Expense",
        "description": "The cost which an oil or gas company incurs while searching for oil or gas to drill is known as exploration expense. It includes the cost of researching appropriate places to drill, premium payments associated with acquisition of new acreage, costs incurred in evaluating commercial viability of geological entities and the cost of actually drilling.",
    },
    {
        "name": "ffo_reit",
        "aliases": set(),
        "dataitemids": {22408, 22468, 22340},
        "spgi_name": "FFO (REIT)",
        "description": "Net income excluding gains or losses from sales of property or debt restructuring, adding back depreciation and amortization of real estate and after adjustments for unconsolidated partnerships and joint ventures. FFO includes both recurring and non-recurring results of operations. This figure represents a supplemental measure of a company's operating performance, is used to define the cash flow from trust operations, and is provided for North American Real Estate Investment Trust Companies only.",
    },
    {
        "name": "ffo_per_share_reit",
        "aliases": set(),
        "dataitemids": {22437, 22497, 22370},
        "spgi_name": "FFO / Share (REIT)",
        "description": "Net income excluding gains or losses from sales of property or debt restructuring, adding back depreciation and amortization of real estate and after adjustments for unconsolidated partnerships and joint ventures. This amount is then divided by the average number of shares in issue. FFO includes both recurring and non-recurring results of operations. This figure represents a supplemental measure of a company's operating performance, is used to define the cash flow from trust operations, and is provided for North American Real Estate Investment Trust Companies only.",
    },
    {
        "name": "financial_services_revenue",
        "aliases": set(),
        "dataitemids": {602863, 602864, 602862},
        "spgi_name": "Financial Services Revenue",
        "description": "Financial services revenue is part of total revenue for Home Building companies. Financial revenue derives from the services including insurance products, title services and mortgage banking services such as loan originations.",
    },
    {
        "name": "free_cash_flow",
        "aliases": set(),
        "dataitemids": {114227, 114229, 114228},
        "spgi_name": "Free Cash Flow",
        "description": "Free cash flow represents the cash that a company is able to generate after laying out the money required to maintain or expand its asset base.",
    },
    {
        "name": "gold_production",
        "aliases": set(),
        "dataitemids": {600422, 600474, 600370},
        "spgi_name": "Gold - Production",
        "description": "Gold production volumes represents the quality of gold produced during a particular period by the gold companies that are involved in Gold exploration and mining.",
    },
    {
        "name": "gross_additions",
        "aliases": set(),
        "dataitemids": {602876, 602877, 602875},
        "spgi_name": "Gross Additions",
        "description": "Gross additions are a client volume factor measuring the actual number of total new subscribers added before subtracting disconnects for a given period.Gross adds means the gross increase in the customer base measured in terms of accesses in a period.",
    },
    {
        "name": "gross_margin",
        "aliases": set(),
        "dataitemids": {114230, 114232, 114231},
        "spgi_name": "Gross Margin",
        "description": "company's total revenue minus cost of goods sold, divided by the total revenue, expressed as a percentage.",
    },
    {
        "name": "gross_premiums_earned",
        "aliases": set(),
        "dataitemids": {600421, 600473, 600369},
        "spgi_name": "Gross Premiums Earned",
        "description": "Gross earned premium is a term used in the insurance industry. It refers to the sum of all the insurance premiums earned by an insurance provider over a specific time period. Simply put it is the revenue earned from the sale of an insurance product.",
    },
    {
        "name": "gross_premiums_written",
        "aliases": set(),
        "dataitemids": {600415, 600467, 600363},
        "spgi_name": "Gross Premiums Written",
        "description": "Gross written premiums are the total revenue from a contract expected to be received by an insurer before deductions for reinsurance or ceding commissions.",
    },
    {
        "name": "home_sales",
        "aliases": set(),
        "dataitemids": {602902, 602903, 602901},
        "spgi_name": "Home Sales",
        "description": "It refers to revenue from the Sale of home. This is also known as residential sales. It includes revenue from existing homes and newly built homes. Total Homebuilding Revenue represents the total homebuilding revenue, which is the combination of land and lot sales revenue and other homebuilding revenue during the period.",
    },
    {
        "name": "industry_net_asset_value_per_share_non_periodic",
        "aliases": set(),
        "dataitemids": {114216, 114218, 114217},
        "spgi_name": "Industry Net Asset Value / Share (Non Periodic)",
        "description": "The market value of an entity's assets less the market value of its liabilities. Industry NAVPS in various ways and S&P Global employs its majority methodology to ensure Industry NAV/Share is consistent for any particular Consensus estimate.",
    },
    {
        "name": "interest_expense",
        "aliases": set(),
        "dataitemids": {114183, 114185, 114184},
        "spgi_name": "Interest Expense",
        "description": "Interest Expense as the amount a company pays in interest on the debt borrowed.",
    },
    {
        "name": "iron_ore_production",
        "aliases": set(),
        "dataitemids": {600427, 600479, 600375},
        "spgi_name": "Iron ore - Production",
        "description": "Iron ore production volumes represents the quality of Iron ore produced during a particular period by the Iron ore companies that are involved in Iron ore exploration and mining.",
    },
    {
        "name": "land_sales",
        "aliases": set(),
        "dataitemids": {602915, 602916, 602914},
        "spgi_name": "Land Sales",
        "description": "It refers to revenue from the Sale of Land. Land Sales Revenue represents the portion of revenue generated from the sale of land during the period.",
    },
    {
        "name": "load_factor",
        "aliases": set(),
        "dataitemids": {603448, 603449, 603447},
        "spgi_name": "Load Factor",
        "description": "The load factor is a metric used in the airline industry that measures the percentage of available seating capacity that has been filled with passengers. A high load factor indicates that an airline has sold most of its available seats and is preferred over a low load factor.",
    },
    {
        "name": "loan_loss_provision",
        "aliases": set(),
        "dataitemids": {600406, 600458, 600354},
        "spgi_name": "Loan Loss Provision",
        "description": "Provision for Loan Losses is an estimation of potential losses that a bank might experience due to customer default and is treated as an expense on the bank's financial statements.",
    },
    {
        "name": "loan_to_value",
        "aliases": set(),
        "dataitemids": {603461, 603462, 603460},
        "spgi_name": "Loan to Value",
        "description": "The loan-to-value is ratio of a loan to the value of an asset purchased. In Real estate, the term is commonly used by banks and building societies to represent the ratio of the first mortgage line as a percentage of the total appraised value of real property.",
    },
    {
        "name": "loans_eop",
        "aliases": set(),
        "dataitemids": {600402, 600454, 600350},
        "spgi_name": "Loans - EoP",
        "description": "Loans (End of the Period) is the data item that represents the outstanding balance of all types of loans and advances given to customers and other financial institutions at period end. The loan may be regarded as 'credit' granted where the money is disbursed, and its recovery is made on a later date. While granting loans, credit is given for a definite purpose and a predetermined period. 'Advance' on the other hand, is a 'credit facility' granted by the bank. Banks grant advances largely for short-term purposes, such as purchase of goods traded in and meeting other short-term trading liabilities.",
    },
    {
        "name": "loss_ratio",
        "aliases": set(),
        "dataitemids": {600419, 600471, 600367},
        "spgi_name": "Loss Ratio",
        "description": "It is the ratio of total losses paid by an insurance company in the form of claims and losses including adjustment expenses to Net earned premiums. The Loss Ratio measures the ratio of losses and loss adjustment expenses to earned premiums determined in accordance with applicable GAAP in the relevant jurisdiction.",
    },
    {
        "name": "maintenance_capital_expenditure",
        "aliases": set(),
        "dataitemids": {22431, 22491, 22363},
        "spgi_name": "Maintenance Capital Expenditure",
        "description": "Maintenance CAPEX as the expenditure to keep existing operations going at their current levels and to maintain a company's assets.",
    },
    {
        "name": "monthly_active_users",
        "aliases": set(),
        "dataitemids": {602928, 602929, 602927},
        "spgi_name": "Monthly Active Users",
        "description": "This data item represents the number of unique customers who interacted with a product or service of a company within a month.The metric is primarily used by internet businesses, including social networking, online gaming, and mobile app companies. The metric provides a quick overview of the company’s user growth. furthermore, MAU delivers some insights into the company’s ability to attract new customers and retain the existing ones.",
    },
    {
        "name": "net_additions",
        "aliases": set(),
        "dataitemids": {602941, 602942, 602940},
        "spgi_name": "Net Additions",
        "description": "Net additions measure the volume of net subscribers left after subtracting disconnects from gross additions. In addition to that definition, Net adds also means, with respect to any Fiscal Year, the Company's \"end of period customers\" on the last day of such Fiscal Year less \"end of period customers\" on the last day of the preceding Fiscal Year.",
    },
    {
        "name": "net_asset_value",
        "aliases": set(),
        "dataitemids": {22505, 22506, 22504},
        "spgi_name": "Net Asset Value",
        "description": "The tangible book value of a company's assets minus its current and long term liabilities adjusted as appropriate.",
    },
    {
        "name": "net_charge_offs",
        "aliases": set(),
        "dataitemids": {602954, 602955, 602953},
        "spgi_name": "Net Charge-offs",
        "description": "A net charge-off (NCO) is the difference between the amount of gross charge-offs and any recoveries of delinquent debt. An NCO can be thought of as the debt owed to a company or organization that is not likely to be recovered. The debt is written off initially as a gross charge-off; however, if any amount of the debt is recovered later, the amount is subtracted to arrive at net charge-offs.",
    },
    {
        "name": "net_charge_offs_to_avg_loans",
        "aliases": set(),
        "dataitemids": {600403, 600455, 600351},
        "spgi_name": "Net Charge-offs / Avg. Loans",
        "description": "Net charge offs to Loans ratio shows the relation between net charges offs during the period and the total loans outstanding.",
    },
    {
        "name": "net_debt",
        "aliases": set(),
        "dataitemids": {22403, 22463, 22335},
        "spgi_name": "Net Debt",
        "description": "Short term and long term interest-bearing debt minus cash and cash equivalents.",
    },
    {
        "name": "net_income_excl_excep_and_gw",
        "aliases": set(),
        "dataitemids": {22399, 22459, 22331},
        "spgi_name": "Net Income (Excl. Excep & GW)",
        "description": "Revenue minus all expenses including operating and non-operating expenses, interest income and expense, and taxation adjusted to exclude the effects of exceptional items and amortization of goodwill.",
    },
    {
        "name": "net_income_gaap",
        "aliases": set(),
        "dataitemids": {22398, 22458, 22330},
        "spgi_name": "Net Income (GAAP)",
        "description": "Revenue minus all expenses including operating and non-operating, interest expense and income and taxation.",
    },
    {
        "name": "net_income_normalized",
        "aliases": set(),
        "dataitemids": {22397, 22457, 22329},
        "spgi_name": "Net Income Normalized",
        "description": "Revenue minus all expenses including operating and non-operating, interest income and expense, and taxation adjusted to exclude the effects of exceptional items.",
    },
    {
        "name": "net_interest_income",
        "aliases": set(),
        "dataitemids": {600393, 600445, 600341},
        "spgi_name": "Net Interest Income",
        "description": "Net interest income is the difference between interest earned and interest paid and is commonly tracked metric by banks and other institutions that lend money. As banks both pay interest (on deposits) and earn it (from loans), interest is both an expense and a revenue stream.",
    },
    {
        "name": "net_interest_margin",
        "aliases": set(),
        "dataitemids": {600397, 600449, 600345},
        "spgi_name": "Net Interest Margin",
        "description": "The net interest margin, also sometimes referred to as the net yield on interest-earning assets, is usually defined as net interest income divided by average interest-earning assets. The margin is calculated for a period of time, a quarter, or a year, and is expressed as a percentage.",
    },
    {
        "name": "net_operating_income",
        "aliases": set(),
        "dataitemids": {600433, 600485, 600381},
        "spgi_name": "Net Operating Income",
        "description": "Net operating income (NOI) is a valuation method used by real estate professionals to determine the profit of the properties worth. Calculation used to analyze real estate investments that generate income from the property.",
    },
    {
        "name": "net_premiums_earned",
        "aliases": set(),
        "dataitemids": {600411, 600463, 600359},
        "spgi_name": "Net Premiums Earned",
        "description": "Net Premiums Earned represents total gross premium written less Premiums ceded to reinsurers and change in unearned premiums reserve. It represents Net Premiums written less change in unearned premiums.  Net Premiums Earned represents Gross Premiums Earned less ceded premiums to reinsurers.",
    },
    {
        "name": "net_premiums_written",
        "aliases": set(),
        "dataitemids": {600414, 600466, 600362},
        "spgi_name": "Net Premiums Written",
        "description": "The sum of premiums written by an Insurance company over the course of a period less premiums ceded to reinsurance companies and reinsurance assumed. (Net premiums written represents how much of the premiums the company gets to keep for assuming risk). Ceded premiums are the premium paid or payable by the captive to another insurer for reinsurance protection.",
    },
    {
        "name": "net_investment_income",
        "aliases": set(),
        "dataitemids": {600416, 600468, 600364},
        "spgi_name": "Net investment income",
        "description": "Net investment income (NII) is the total income before taxes that an investor receives on their portfolio of investment assets. NII is generated from dividends, capital gains, or similar investment-related returns. Below is the formula for net investment income.",
    },
    {
        "name": "new_students_enrollment",
        "aliases": set(),
        "dataitemids": {602980, 602981, 602979},
        "spgi_name": "New Students Enrollment",
        "description": "New Student enrollment refers to number of new students registering for school, particular classes, or co-curricular activities of any specific school.",
    },
    {
        "name": "non_interest_expense",
        "aliases": set(),
        "dataitemids": {600396, 600448, 600344},
        "spgi_name": "Non-Interest Expense",
        "description": "Non-Interest Expenses are nothing but the operating expenses and overheads other than the interest expense. Non-interest expenses may include employee salaries and benefits, equipment and property leases, stock-based compensation, administrative expenses, marketing expenses, Professional and legal fee, Business development expenses, Mortgage re-insurance costs, Distribution and servicing expenses, and any other operating costs.",
    },
    {
        "name": "non_interest_to_fee_income",
        "aliases": set(),
        "dataitemids": {600394, 600446, 600342},
        "spgi_name": "Non-Interest / Fee Income",
        "description": "Non-interest income is an income that is generated from the application of fees, rather than from interest income. Banks may get Non-interest income from different sources based on their range of offerings and operations, like the sources of, investment income, management fee, commission income, Trading income, Brokerage income, Dividend income, Mortgage banking, Trust Fees, Treasury operations, Credit card, foreign exchange services, Incentive income, and other.",
    },
    {
        "name": "non_performing_assets",
        "aliases": set(),
        "dataitemids": {602993, 602994, 602992},
        "spgi_name": "Non-performing Assets",
        "description": "A non-performing asset (NPA) is a classification used by financial institutions for loans and advances on which the principal is past due and on which no interest payments have been made for a period of time.",
    },
    {
        "name": "non_performing_loans",
        "aliases": set(),
        "dataitemids": {603006, 603007, 603005},
        "spgi_name": "Non-performing Loans",
        "description": "A nonperforming loan (NPL) is a loan that is in default due to the fact that the borrower has not made the scheduled payments for a specified period. Although the exact elements of nonperforming status can vary depending on the specific loan's terms, \"no payment\" is usually defined as zero payments of either principal or interest. The specified period also varies, depending on the industry and the type of loan. Generally, however, the period is 90 days or 180 days.",
    },
    {
        "name": "non_performing_assets_to_assets",
        "aliases": set(),
        "dataitemids": {600400, 600452, 600348},
        "spgi_name": "Non-performing Assets / Assets",
        "description": "The Non-Performing Assets to Assets ratio is used as a measure of the overall quality of the bank's loan book. Non-Performing Assets are those assets for which interest/Instalment is overdue for more than a specified period.",
    },
    {
        "name": "number_of_subscribers",
        "aliases": set(),
        "dataitemids": {603019, 603020, 603018},
        "spgi_name": "Number of Subscribers",
        "description": "It represents the number of subscribers a company has at the end of the period, which reflects the net additions to existing subscribers over a given period.",
    },
    {
        "name": "opex_per_unit",
        "aliases": set(),
        "dataitemids": {604176, 604177, 604175},
        "spgi_name": "OPEX Per Unit",
        "description": "Operational costs may be defined as the revenue required for the administration of a business and carrying out daily maintenance procedures. OPEX is basically operating costs such as fees for oil and water hauling, electricity, etc.",
    },
    {
        "name": "orders_units",
        "aliases": set(),
        "dataitemids": {603344, 603345, 603343},
        "spgi_name": "Orders (Units)",
        "description": "Net New Orders represents the number of homes and condominiums that come under contract at the end of the period.",
    },
    {
        "name": "orders_average_price",
        "aliases": set(),
        "dataitemids": {603370, 603371, 603369},
        "spgi_name": "Orders Average Price",
        "description": "Average order price tracks the average amount spent each time a customer places an order. To calculate the orders avg price, divide the total revenue earned from the product by the total number of units sold.",
    },
    {
        "name": "orders_value",
        "aliases": set(),
        "dataitemids": {603045, 603046, 603044},
        "spgi_name": "Orders Value",
        "description": "Order Value means the price set out on the Order Confirmation. In addition to that, Order Value means the gross value of the Product which shall be required to be paid by the Customer and is eventually delivered by the Seller.",
    },
    {
        "name": "passenger_revenue",
        "aliases": set(),
        "dataitemids": {603071, 603072, 603070},
        "spgi_name": "Passenger Revenue",
        "description": "Revenue passenger means the fares collected on the Services operated in the performance of the Contract including any on Airbus sales of prepaid tickets (except to the extent that there is agreement between the Operator and the Council to the contrary or that the sale relates to the sale of a multi operator ticket and the Operator is obliged to pass on that revenue to the body administering the sale proceeds of multi operator tickets).",
    },
    {
        "name": "pre_provision_profit",
        "aliases": set(),
        "dataitemids": {600401, 600453, 600349},
        "spgi_name": "Pre Provision Profit",
        
    },
    {
        "name": "product_sales",
        "spgi_name": "Product Sales",
        "aliases": set(),
        "high_dataitemid": 603084,
        "low_dataitemid": 603085,
        "mid_dataitemid": 603083,
    },
    {
        "name": "real_estate_depreciation",
        "spgi_name": "Real Estate Depreciation",
        "aliases": set(),
        "high_dataitemid": 600440,
        "low_dataitemid": 600492,
        "mid_dataitemid": 600388,
    },
    {
        "name": "research_and_development_expense",
        "spgi_name": "Research & Development Expense",
        "aliases": set(),
        "high_dataitemid": 603110,
        "low_dataitemid": 603111,
        "mid_dataitemid": 603109,
    },
    {
        "name": "restaurant_operating_margin_ratio",
        "spgi_name": "Restaurant Operating Margin Ratio",
        "aliases": set(),
        "high_dataitemid": 603383,
        "low_dataitemid": 603384,
        "mid_dataitemid": 603382,
    },
    {
        "name": "return_on_assets",
        "spgi_name": "Return on Assets",
        "aliases": set(),
        "high_dataitemid": 22407,
        "low_dataitemid": 22467,
        "mid_dataitemid": 22339,
    },
    {
        "name": "return_on_equity",
        "spgi_name": "Return on Equity",
        "aliases": set(),
        "high_dataitemid": 22406,
        "low_dataitemid": 22466,
        "mid_dataitemid": 22338,
    },
    {
        "name": "revenue",
        "spgi_name": "Revenue",
        "aliases": set(),
        "high_dataitemid": 22390,
        "low_dataitemid": 22450,
        "mid_dataitemid": 22322,
    },
    {
        "name": "revenue_passenger_kms",
        "spgi_name": "Revenue Passenger Kms",
        "aliases": set(),
        "high_dataitemid": 603305,
        "low_dataitemid": 603306,
        "mid_dataitemid": 603304,
    },
    {
        "name": "revenue_passenger_miles",
        "spgi_name": "Revenue Passenger Miles",
        "aliases": set(),
        "high_dataitemid": 604412,
        "low_dataitemid": 604413,
        "mid_dataitemid": 604411,
    },
    {
        "name": "revenue_per_available_room",
        "spgi_name": "Revenue / Available Room",
        "aliases": set(),
        "high_dataitemid": 603123,
        "low_dataitemid": 603124,
        "mid_dataitemid": 603122,
    },
    {
        "name": "revenues_gas",
        "spgi_name": "Revenues (Gas)",
        "aliases": set(),
        "high_dataitemid": 115524,
        "low_dataitemid": 115525,
        "mid_dataitemid": 115523,
    },
    {
        "name": "revenues_ngl",
        "spgi_name": "Revenues (NGL)",
        "aliases": set(),
        "high_dataitemid": 115511,
        "low_dataitemid": 115512,
        "mid_dataitemid": 115510,
    },
    {
        "name": "revenues_oil",
        "spgi_name": "Revenues (Oil)",
        "aliases": set(),
        "high_dataitemid": 115498,
        "low_dataitemid": 115499,
        "mid_dataitemid": 115497,
    },
    {
        "name": "risk_weighted_assets",
        "spgi_name": "Risk Weighted Assets",
        "aliases": set(),
        "high_dataitemid": 600409,
        "low_dataitemid": 600461,
        "mid_dataitemid": 600357,
    },
    {
        "name": "salaries_and_benefits",
        "spgi_name": "Salaries and Benefits",
        "aliases": set(),
        "high_dataitemid": 603136,
        "low_dataitemid": 603137,
        "mid_dataitemid": 603135,
    },
    {
        "name": "same_store_sales_growth",
        "spgi_name": "Same Store Sales Growth",
        "aliases": set(),
        "high_dataitemid": 114205,
        "low_dataitemid": 114207,
        "mid_dataitemid": 114206,
    },
    {
        "name": "same_store_sales",
        "spgi_name": "Same Store Sales",
        "aliases": set(),
        "high_dataitemid": 603149,
        "low_dataitemid": 603150,
        "mid_dataitemid": 603148,
    },
    {
        "name": "selling_general_and_administrative_expense",
        "spgi_name": "Selling, General and Administrative Expense",
        "aliases": set(),
        "high_dataitemid": 603162,
        "low_dataitemid": 603163,
        "mid_dataitemid": 603161,
    },
    {
        "name": "silver_production",
        "spgi_name": "Silver - Production",
        "aliases": set(),
        "high_dataitemid": 600426,
        "low_dataitemid": 600478,
        "mid_dataitemid": 600374,
    },
    {
        "name": "stores_closed",
        "spgi_name": "Stores Closed",
        "aliases": set(),
        "high_dataitemid": 603175,
        "low_dataitemid": 603176,
        "mid_dataitemid": 603174,
    },
    {
        "name": "stores_opened",
        "spgi_name": "Stores Opened",
        "aliases": set(),
        "high_dataitemid": 603188,
        "low_dataitemid": 603189,
        "mid_dataitemid": 603187,
    },
    {
        "name": "supplies",
        "spgi_name": "Supplies",
        "aliases": set(),
        "high_dataitemid": 603201,
        "low_dataitemid": 603202,
        "mid_dataitemid": 603200,
    },
    {
        "name": "tev",
        "spgi_name": "TEV",
        "aliases": set(),
        "high_dataitemid": 22378,
        "low_dataitemid": 22438,
        "mid_dataitemid": 22310,
    },
    {
        "name": "tangible_book_value_per_share",
        "spgi_name": "Tangible Book Value  / Share",
        "aliases": set(),
        "high_dataitemid": 601429,
        "low_dataitemid": 601430,
        "mid_dataitemid": 601431,
    },
    {
        "name": "tax_provision",
        "spgi_name": "Tax Provision",
        "aliases": set(),
        "high_dataitemid": 601442,
        "low_dataitemid": 601443,
        "mid_dataitemid": 601444,
    },
    {
        "name": "tier_1_capital_ratio",
        "spgi_name": "Tier 1 Capital Ratio",
        "aliases": set(),
        "high_dataitemid": 600399,
        "low_dataitemid": 600451,
        "mid_dataitemid": 600347,
    },
    {
        "name": "total_assets_guidance",
        "spgi_name": "Total Assets Guidance",
        "aliases": set(),
        "high_dataitemid": 600410,
        "low_dataitemid": 600462,
        "mid_dataitemid": 600358,
    },
    {
        "name": "total_average_daily_production",
        "spgi_name": "Total Average Daily Production",
        "aliases": set(),
        "high_dataitemid": 115485,
        "low_dataitemid": 115486,
        "mid_dataitemid": 115484,
    },
    {
        "name": "total_fuel_expense",
        "spgi_name": "Total Fuel Expense",
        "aliases": set(),
        "high_dataitemid": 603214,
        "low_dataitemid": 603215,
        "mid_dataitemid": 603213,
    },
    {
        "name": "total_occupancy_ratio",
        "spgi_name": "Total Occupancy Ratio",
        "aliases": set(),
        "high_dataitemid": 603396,
        "low_dataitemid": 603397,
        "mid_dataitemid": 603395,
    },
    {
        "name": "total_production_gas",
        "spgi_name": "Total Production (Gas)",
        "aliases": set(),
        "high_dataitemid": 115459,
        "low_dataitemid": 115460,
        "mid_dataitemid": 115458,
    },
    {
        "name": "total_production_ngl",
        "spgi_name": "Total Production (NGL)",
        "aliases": set(),
        "high_dataitemid": 115433,
        "low_dataitemid": 115434,
        "mid_dataitemid": 115432,
    },
    {
        "name": "total_production_oil",
        "spgi_name": "Total Production (Oil)",
        "aliases": set(),
        "high_dataitemid": 115407,
        "low_dataitemid": 115408,
        "mid_dataitemid": 115406,
    },
    {
        "name": "total_production",
        "spgi_name": "Total Production",
        "aliases": set(),
        "high_dataitemid": 115595,
        "low_dataitemid": 115596,
        "mid_dataitemid": 115594,
    },
    {
        "name": "total_restaurants_eop",
        "spgi_name": "Total Restaurants EoP",
        "aliases": set(),
        "high_dataitemid": 603240,
        "low_dataitemid": 603241,
        "mid_dataitemid": 603239,
    },
    {
        "name": "total_stores_eop",
        "spgi_name": "Total Stores EoP",
        "aliases": set(),
        "high_dataitemid": 603253,
        "low_dataitemid": 603254,
        "mid_dataitemid": 603252,
    },
    {
        "name": "total_students_enrollment",
        "spgi_name": "Total Students Enrollment",
        "aliases": set(),
        "high_dataitemid": 603266,
        "low_dataitemid": 603267,
        "mid_dataitemid": 603265,
    },
    {
        "name": "underwriting_profit_or_loss",
        "spgi_name": "Underwriting Profit or Loss",
        "aliases": set(),
        "high_dataitemid": 600413,
        "low_dataitemid": 600465,
        "mid_dataitemid": 600361,
    },
]
