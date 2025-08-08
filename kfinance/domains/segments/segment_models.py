from typing import Any

from pydantic import BaseModel
from strenum import StrEnum


class SegmentType(StrEnum):
    """The type of segment"""

    business = "business"
    geographic = "geographic"


class SegmentsResp(BaseModel):
    segments: dict[str, Any]
