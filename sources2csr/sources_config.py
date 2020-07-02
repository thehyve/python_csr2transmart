from collections import Counter
from typing import Dict, Sequence, Optional

from pydantic import BaseModel, validator, Field


class SourcesConfigValidationException(ValueError):
    pass


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

    @validator('attributes')
    def validate_attribute_names(cls, attrs: Sequence[Attribute]):
        attribute_name_counts = Counter([attr.name for attr in attrs])
        duplicates = [k for k, v in attribute_name_counts.items() if v > 1]
        if duplicates:
            raise SourcesConfigValidationException(
                f'Duplicate attributes: {", ".join(duplicates)}')
        return attrs


class FileFormat(BaseModel):
    delimiter: str = Field('\t', min_length=1, max_length=1)


class SourcesConfig(BaseModel):

    """Mapping from entity name to entity sources"""
    entities: Dict[str, Entity]

    """Associates input files with codebook files"""
    codebooks: Optional[Dict[str, str]]

    """File format configuration for input files"""
    file_format: Optional[Dict[str, FileFormat]]
