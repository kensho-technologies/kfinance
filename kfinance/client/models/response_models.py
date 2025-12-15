from typing import TypeAlias, TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)

Source: TypeAlias = dict[str, str]
