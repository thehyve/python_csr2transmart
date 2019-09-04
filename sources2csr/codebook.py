from typing import Dict, Any

from pydantic import BaseModel


class ColumnValueMapping(BaseModel):
    value_mapping: Dict[Any, Any]


class CodeBook(BaseModel):
    column_mappings: Dict[str, ColumnValueMapping]
