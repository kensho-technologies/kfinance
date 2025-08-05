from pydantic import BaseModel
from strenum import StrEnum

from kfinance.domains.companies.company_models import CompanyIdAndName


class CompetitorSource(StrEnum):
    """The source type of the competitor information: 'filing' (from SEC filings), 'key_dev' (from key developments), 'contact' (from contact relationships), 'third_party' (from third-party sources), 'self_identified' (self-identified), 'named_by_competitor' (from competitor's perspective)."""

    all = "all"
    filing = "filing"
    key_dev = "key_dev"
    contact = "contact"
    third_party = "third_party"
    self_identified = "self_identified"
    named_by_competitor = "named_by_competitor"


class CompetitorResponse(BaseModel):
    competitors: list[CompanyIdAndName]
