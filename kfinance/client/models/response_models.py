from typing import Any, Callable, Dict, Generic, TypeAlias, TypeVar

from pydantic import BaseModel, Field, model_serializer


T = TypeVar("T", bound=BaseModel)

Source: TypeAlias = dict[str, str]
