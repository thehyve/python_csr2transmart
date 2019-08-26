from typing import List, Dict

from pandas import DataFrame
from transmart_loader.transmart import Modifier, Dimension, \
    ValueType, DimensionType


class ModifierMapper:
    """
    Map modifiers file to transmart-loader Modifier and Dimension classes
    """
    def __init__(self):
        self.dimensions: List[Dimension] = []
        self.modifier_key_to_modifier: Dict[str, Modifier] = {}

    @staticmethod
    def type_to_value_type(value: str) -> ValueType:
        if value is not None and value.lower() == 'numeric':
            return ValueType.Numeric
        else:
            return ValueType.Categorical

    @staticmethod
    def type_to_dimension_type(dimension_type: str) -> DimensionType:
        if dimension_type is not None and dimension_type.lower() == 'subject':
            return DimensionType.Subject
        else:
            return DimensionType.Attribute

    def map(self, modifiers: DataFrame):
        modifier_code_col = 'modifier_cd'
        name_col = 'name_char'
        modifier_path_col = 'modifier_path'
        dimension_type_col = 'dimension_type'
        sort_index_col = 'sort_index'
        value_type_col = 'Data Type'

        for index, row in modifiers.iterrows():
            modifier = Modifier(row.get(modifier_code_col),
                                row.get(name_col),
                                row.get(modifier_path_col),
                                self.type_to_value_type(row.get(value_type_col)))
            self.modifier_key_to_modifier[row[name_col]] = modifier

            modifier_dimension = Dimension(row.get(name_col),
                                           modifier,
                                           self.type_to_dimension_type(row.get(dimension_type_col)),
                                           row.get(sort_index_col))
            self.dimensions.append(modifier_dimension)
