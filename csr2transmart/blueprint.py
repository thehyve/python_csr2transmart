from enum import Enum
from typing import Optional, Any, Dict

from pydantic import BaseModel


class ForceCategoricalBoolean(str, Enum):
    ForceTrue = 'Y'
    ForceFalse = 'N'


class BlueprintElement(BaseModel):
    """

    """
    path: Optional[str]
    label: str
    metadata_tags: Optional[Dict[str, str]]
    force_categorical: Optional[ForceCategoricalBoolean]
    word_map: Optional[Dict[str, Any]]
    data_type: Optional[str]


Blueprint = Dict[str, BlueprintElement]
