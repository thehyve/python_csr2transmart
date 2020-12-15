from datetime import date
from typing import Sequence, Optional, Union, Dict, List, Any

from pydantic import BaseModel, validator, Field

from csr.entity_validation import validate_entity_data
from csr.exceptions import DataException


class Individual(BaseModel):
    """
    Individual entity
    """
    individual_id: str = Field(..., min_length=1, identity=True)
    taxonomy: Optional[str]
    gender: Optional[str]
    birth_date: Optional[date]
    death_date: Optional[date]
    ic_type: Optional[str]
    ic_version: Optional[float]
    ic_given_date: Optional[date]
    ic_withdrawn_date: Optional[date]
    report_her_susc: Optional[str]
    report_inc_findings: Optional[str]
    diagnosis_count: Optional[int]
    age_first_diagnosis: Optional[int]


class Diagnosis(BaseModel):
    """
    Diagnosis entity
    """
    diagnosis_id: str = Field(..., min_length=1, identity=True)
    individual_id: str = Field(..., min_length=1, references='Individual')
    tumor_type: Optional[str]
    topography: Optional[str]
    treatment_protocol: Optional[str]
    tumor_stage: Optional[str]
    diagnosis_date: Optional[date]
    diagnosis_center: Optional[str]


class Biosource(BaseModel):
    """
    Biosource entity
    """
    biosource_id: str = Field(..., min_length=1, identity=True)
    biosource_dedicated: Optional[str]
    individual_id: str = Field(..., min_length=1, references='Individual')
    diagnosis_id: Optional[str] = Field(None, min_length=1, references='Diagnosis')
    src_biosource_id: Optional[str] = Field(None, min_length=1, references='Biosource')
    tissue: Optional[str]
    biosource_date: Optional[date]
    disease_status: Optional[str]
    tumor_percentage: Optional[int]

    @validator('src_biosource_id')
    def check_self_reference(cls, src_biosource_id, values):
        if src_biosource_id == values['biosource_id']:
            raise DataException(f'Biosource cannot be derived from itself')
        return src_biosource_id


class Biomaterial(BaseModel):
    """
    Biomaterial entity
    """
    biomaterial_id: str = Field(..., min_length=1, identity=True)
    src_biosource_id: str = Field(..., min_length=1, references='Biosource')
    src_biomaterial_id: Optional[str] = Field(None, min_length=1, references='Biomaterial')
    biomaterial_date: Optional[date]
    type: Optional[str]
    library_strategy: Optional[List[str]] = Field(None, derived=True)
    analysis_type: Optional[List[str]] = Field(None, derived=True)

    @validator('src_biomaterial_id')
    def check_self_reference(cls, src_biomaterial_id, values):
        if src_biomaterial_id == values['biomaterial_id']:
            raise DataException(f'Biomaterial cannot be derived from itself')
        return src_biomaterial_id


class Study(BaseModel):
    """
    Study
    """
    study_id: str = Field(..., min_length=1, identity=True)
    acronym: Optional[str]
    title: Optional[str]
    datadictionary: Optional[str]


class IndividualStudy(BaseModel):
    """
    Study to individual mapping
    """
    study_id_individual_study_id: str = Field(..., min_length=1, identity=True)
    individual_study_id: str
    individual_id: str = Field(..., min_length=1, references='Individual')
    study_id: str = Field(..., min_length=1, references='Study')


SubjectEntity = Union[Individual, Diagnosis, Biosource, Biomaterial]


class CentralSubjectRegistry(BaseModel):
    """
    Central subject registry
    """
    entity_data: Dict[str, Sequence[Any]]

    @staticmethod
    def create(entity_data: Dict[str, Sequence[Any]]):
        validate_entity_data(entity_data, list(SubjectEntity.__args__))
        return CentralSubjectRegistry(entity_data=entity_data)


StudyEntity = Union[Study, IndividualStudy]


class StudyRegistry(BaseModel):
    """
    Study registry
    """
    entity_data: Dict[str, Sequence[Any]]

    @staticmethod
    def create(entity_data: Dict[str, Sequence[Any]]):
        validate_entity_data(entity_data, list(StudyEntity.__args__))
        return StudyRegistry(entity_data=entity_data)
