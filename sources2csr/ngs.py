from enum import Enum
from typing import Optional

from pydantic import BaseModel


class LibraryStrategy(Enum):
    """
    Type of library strategy (sequencing type)
    """
    SNV = "SNV"
    CNV = "CNV"


class AnalysisType(Enum):
    """
    Type of analysis
    """
    WGS = "WGS"
    WXS = "WXS"


class NGS(BaseModel):
    biosource_id: str
    biomaterial_id: str
    library_strategy: LibraryStrategy
    analysis_type: Optional[AnalysisType]

    def __hash__(self):
        return hash(('biosource_id', self.biosource_id,
                     'biomaterial_id', self.biomaterial_id,
                     'library_strategy', self.library_strategy,
                     'analysis_type', self.analysis_type))
