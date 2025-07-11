from typing import NamedTuple

from pydantic import BaseModel, field_serializer


COMPANY_ID_PREFIX = "C_"


class CompanyIdAndName(BaseModel):
    """A company_id and name"""

    company_id: int
    company_name: str

    @field_serializer("company_id")
    def serialize_with_prefix(self, company_id: int) -> str:
        """Serialize the company_id with a prefix ("C_<company_id>").

        Including the prefix allows us to distinguish tickers and company_ids.
        """
        return f"{COMPANY_ID_PREFIX}{company_id}"


class IdentificationTriple(NamedTuple):
    trading_item_id: int
    security_id: int
    company_id: int
