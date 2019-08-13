import pytest

from csr.csr import CentralSubjectRegistry, StudyRegistry


@pytest.fixture
def csr_subject_registry() -> CentralSubjectRegistry:
    return None


@pytest.fixture
def csr_study_registry() -> StudyRegistry:
    return None
