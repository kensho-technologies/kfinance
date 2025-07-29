from datetime import datetime, timezone

from pydantic import AliasPath, BaseModel, Field


class EarningsCall(BaseModel):
    name: str
    key_dev_id: int
    datetime: datetime


class EarningsCallResp(BaseModel):
    earnings_calls: list[EarningsCall] = Field(validation_alias=AliasPath("earnings"))

    @property
    def most_recent_earnings(self) -> EarningsCall | None:
        """Returns the most recent earnings call if available."""

        past_earnings = [e for e in self.earnings_calls if e.datetime < datetime.now(timezone.utc)]
        if past_earnings:
            return max(past_earnings, key=lambda x: x.datetime)
        return None

    @property
    def next_earnings(self) -> EarningsCall | None:
        """Returns the next earnings call if available."""

        future_earnings = [
            e for e in self.earnings_calls if e.datetime > datetime.now(timezone.utc)
        ]
        if future_earnings:
            return min(future_earnings, key=lambda x: x.datetime)
        return None


class TranscriptComponent(BaseModel):
    """A transcript component with person name, text, and component type."""

    person_name: str
    text: str
    component_type: str
