import pytest

from csr2transmart.mappers.ontology_mapper import OntologyMapper
from csr2transmart.ontology_config import OntologyConfigValidationException
from csr2transmart.transmart_transformation import read_configuration

"""Tests for the ontology config mapper.
"""


def test_valid_ontology_config():
    ontology_config = read_configuration('./test_data/input_data/config')
    tree_nodes = OntologyMapper('test').map(ontology_config.nodes)
    assert len(tree_nodes) == 1
    assert len(tree_nodes[0].children) == 5


def test_ontology_config_invalid_entity_field():
    with pytest.raises(OntologyConfigValidationException) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/ontology_config_invalid_entity_field')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Invalid concept code: Individual.not_existing_field. ' \
           'Field: not_existing_field is not a valid field of Individual entity.' in str(excinfo.value)


def test_ontology_config_invalid_entity_name():
    with pytest.raises(OntologyConfigValidationException) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/ontology_config_invalid_entity_name')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Invalid concept code: InvalidEntity.taxonomy. ' \
           'InvalidEntity is not a valid CSR entity.' in str(excinfo.value)


def test_ontology_config_invalid_concept_code():
    with pytest.raises(OntologyConfigValidationException) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/ontology_config_invalid_concept_code')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Invalid concept code format: gender. Concept code has to have format: ' \
           '`<entity_name>.<entity_field>`' in str(excinfo.value)
