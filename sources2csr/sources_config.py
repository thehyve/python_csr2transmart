from typing import Dict, Sequence, Optional

from pydantic import BaseModel


class Source(BaseModel):
    """
    The source file column for the entity attribute.
    If the column is not specified, it is assumed that the column name
    is the attribute name.
    """
    file: str
    column: Optional[str]
    date_format: Optional[str]


class Attribute(BaseModel):
    name: str
    sources: Sequence[Source]


class Entity(BaseModel):
    attributes: Sequence[Attribute]


class SourcesConfig(BaseModel):

    """Mapping from entity name to entity sources"""
    entities: Dict[str, Entity]

    """Associates input files with codebook files"""
    codebooks: Optional[Dict[str, str]]
