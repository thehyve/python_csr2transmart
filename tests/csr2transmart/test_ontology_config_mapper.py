import pytest
from pydantic import ValidationError

from csr.exceptions import DataException
from csr2transmart.csr2transmart import read_configuration
from csr2transmart.mappers.ontology_mapper import OntologyMapper

"""Tests for the ontology config mapper.
"""


def test_valid_ontology_config():
    ontology_config = read_configuration('./test_data/input_data/config')
    tree_nodes = OntologyMapper('test').map(ontology_config.nodes)
    assert len(tree_nodes) == 1
    assert len(tree_nodes[0].children) == 5


def test_ontology_config_invalid_entity_field():
    with pytest.raises(ValidationError) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/ontology_config_invalid_entity_field')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Invalid concept code: Individual.not_existing_field. ' \
           'Field: not_existing_field is not a valid field of Individual entity.' in str(excinfo.value)


def test_ontology_config_invalid_entity_name():
    with pytest.raises(ValidationError) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/ontology_config_invalid_entity_name')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Invalid concept code: InvalidEntity.taxonomy. ' \
           'InvalidEntity is not a valid CSR entity.' in str(excinfo.value)


def test_ontology_config_invalid_concept_code():
    with pytest.raises(ValidationError) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/ontology_config_invalid_concept_code')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Invalid concept code format: gender. Concept code has to have format: ' \
           '`<entity_name>.<entity_field>`' in str(excinfo.value)


def test_ontology_config_mutually_exclusive_properties():
    with pytest.raises(ValidationError) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/mutually_exclusive_properties')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Node cannot have both concept_code and children' in str(excinfo.value)


def test_ontology_config_neither_children_nor_concept_code():
    with pytest.raises(ValidationError) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/neither_children_nor_concept_code')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Node must have either concept_code or children' in str(excinfo.value)


def test_duplicate_child_names_rejected():
    with pytest.raises(ValidationError) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/duplicate_children')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Duplicate child names: 01. Date of birth' in str(excinfo.value)


def test_duplicate_top_node_names_rejected():
    with pytest.raises(ValidationError) as excinfo:
        ontology_config = read_configuration(
            './test_data/input_data/config/invalid_ontology_config/duplicate_nodes')
        OntologyMapper('test').map(ontology_config.nodes)
    assert 'Duplicate node names: 01. Patient information' in str(excinfo.value)


def test_invalid_json():
    with pytest.raises(DataException) as excinfo:
        read_configuration('./test_data/input_data/config/invalid_ontology_config/invalid_json')
    assert 'Error parsing ontology config file' in str(excinfo.value)
