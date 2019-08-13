import json
import logging
import os
import sys
from typing import Dict

import click
import pandas as pd
from transmart_loader.copy_writer import TransmartCopyWriter
from transmart_loader.transmart import DataCollection

from csr2transmart.blueprint import Blueprint, BlueprintElement
from csr2transmart.csr_mapper import CsrMapper
from csr2transmart.validations import get_blueprint_validator_initialised_with_modifiers

logger = logging.getLogger(__name__)


class TransmartTransformationException(Exception):
    pass


def check_if_blueprint_valid(modifier_file, blueprint):
    logger.info('Validating blueprint file')
    blueprint_validator = get_blueprint_validator_initialised_with_modifiers(modifier_file)
    violations = list(blueprint_validator.collect_tree_node_dimension_violations(blueprint))
    if violations:
        all_err_messages = '\n'.join(violations)
        raise TransmartTransformationException(
            '{} tree node violations have found:\n{}'.format(len(violations), all_err_messages))


def transform(csr_data_file_path: str,
              study_registry_data_file_path: str,
              output_dir: str,
              config_dir: str,
              study_id: str,
              top_tree_node: str):

    modifier_file = os.path.join(config_dir, 'modifiers.txt')
    blueprint_file = os.path.join(config_dir, 'blueprint.json')
    try:
        logger.info('Reading configuration data...')
        with open(blueprint_file, 'r') as bpf:
            bp: Dict = json.load(bpf)
        check_if_blueprint_valid(modifier_file, bp)
        blueprint: Blueprint = {k: BlueprintElement(**v) for k, v in bp.items()}
        modifiers = pd.read_csv(modifier_file, sep='\t')

        logger.info('Reading Central Subject Registry data...')
        csr_df = pd.read_csv(csr_data_file_path, sep='\t')
        sr_df = pd.read_csv(study_registry_data_file_path, sep='\t')  # TODO use for ontology mapping

        logger.info('Mapping data...')
        mapper = CsrMapper(study_id, top_tree_node)
        collection: DataCollection = mapper.map(csr_df, modifiers, blueprint)

        logger.info('Writing files to {}'.format(output_dir))
        copy_writer = TransmartCopyWriter(str(output_dir))
        copy_writer.write_collection(collection)

        logger.info('Done.')

    except FileNotFoundError as fnfe:
        print('File not found. {}'.format(fnfe))
        sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)


@click.command()
@click.option('--csr_data_file_path', type=click.Path(exists=True))
@click.option('--study_registry_data_file_path', type=click.Path(exists=True))
@click.option('--output_dir', type=click.Path(exists=True))
@click.option('--config_dir', type=click.Path(exists=True))
@click.option('--study_id')
@click.option('--top_node')
def transmart_transformation(csr_data_file_path,
                             study_registry_data_file_path,
                             output_dir,
                             config_dir,
                             study_id,
                             top_node):
    transform(csr_data_file_path, study_registry_data_file_path, output_dir, config_dir, study_id, top_node)


def main():
    transmart_transformation()


if __name__ == '__main__':
    main()
