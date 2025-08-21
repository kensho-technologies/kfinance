from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


COMPANY_ID_PREFIX = "C_"


def prefix_company_id(company_id: int) -> str:
    """Return the company_id with the COMPANY_ID_PREFIX"""
    return f"{COMPANY_ID_PREFIX}{company_id}"


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


class IdentificationTriple(BaseModel):
    company_id: int
    security_id: int | None = Field(description="Private companies do not have a security_id.")
    trading_item_id: int | None = Field(
        description="Private companies do not have a trading_item_id."
    )

    # frozen to allow hashing
    model_config = ConfigDict(frozen=True)


class IdTripleResolutionError(BaseModel):
    """Error returned when an identifier cannot be resolved."""

    error: str


class UnifiedIdTripleResponse(BaseModel):
    """A response from the unified id triple endpoint (POST /ids).

    For easier handling within tools, we split the api response into
    identifiers_to_id_triples (successful resolution) and errors (resolution failed).
    """

    identifiers_to_id_triples: dict[str, IdentificationTriple] = Field(
        description="A mapping of all identifiers that could successfully be resolved"
        "to the corresponding identification triples."
    )
    errors: dict[str, str] = Field(
        description="A mapping of all identifiers that could not be resolved or don't have "
        "a required field like security_id with the corresponding error messages."
    )

    @model_validator(mode="before")
    @classmethod
    def separate_successful_and_failed_resolutions(cls, data: Any) -> Any:
        """Split response into identifiers_to_id_triples (success) and errors

        Pre-processed API response:
        {
            'data': {
                'SPGI': {'trading_item_id': 2629108, 'security_id': 2629107, 'company_id': 21719},
                'non-existent': {'error': 'No identification triple found for the provided identifier: NON-EXISTENT of type: ticker'}
            }
        }

        Post-processed API response:
        {
            'identifiers_to_id_triples': {
                'SPGI': {'trading_item_id': 2629108, 'security_id': 2629107, 'company_id': 21719},
            },
            'errors': {
                'non-existent': 'No identification triple found for the provided identifier: NON-EXISTENT of type: ticker'
            }
        }


        """
        # Separate successful and failed resolutions for kfinance api responses
        if isinstance(data, dict) and "data" in data:
            output: dict[str, dict] = dict(identifiers_to_id_triples=dict(), errors=dict())

            for key, val in data["data"].items():
                if "error" in val:
                    output["errors"][key] = val["error"]
                else:
                    output["identifiers_to_id_triples"][key] = val
            return output
        # In all other cases (e.g. UnifiedIdTripleResponse directly initialized),
        # just return the data.
        else:
            return data

    def filter_out_companies_without_security_ids(self) -> None:
        """Filter out companies that don't have a security_id and add an error for them."""

        identifiers_to_remove = [
            identifier
            for identifier, id_triple in self.identifiers_to_id_triples.items()
            if id_triple.security_id is None
        ]
        for identifier in identifiers_to_remove:
            self.errors[identifier] = f"{identifier} is a private company without a security_id."
            self.identifiers_to_id_triples.pop(identifier)

    def filter_out_companies_without_trading_item_ids(self) -> None:
        """Filter out companies that don't have a trading_item_id and add an error for them."""

        identifiers_to_remove = [
            identifier
            for identifier, id_triple in self.identifiers_to_id_triples.items()
            if id_triple.trading_item_id is None
        ]
        for identifier in identifiers_to_remove:
            self.errors[identifier] = (
                f"{identifier} is a private company without a trading_item_id."
            )
            self.identifiers_to_id_triples.pop(identifier)


class CompanyDescriptions(BaseModel):
    """A company summary and description"""

    summary: str
    description: str


class NativeName(BaseModel):
    """A company's native name's name and language"""

    name: str
    language: str


class CompanyOtherNames(BaseModel):
    """A company's alternate, historical, and native names"""

    alternate_names: list[str]
    historical_names: list[str]
    native_names: list[NativeName]
