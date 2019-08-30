import os

import logging
import sys

import click
from csr2tsv.subject_registry_writer import SubjectRegistryWriter

from csr2tsv.study_registry_writer import StudyRegistryWriter
from sources2csr.helper_variables import add_derived_values, add_helper_variables
from sources2csr.legacy.legacy_sources_reader import LegacySourcesReader
from sources2csr.sources_reader import SourcesReader


logger = logging.getLogger(__name__)


def legacy_sources2csr(input_dir, output_dir, config_dir):
    reader = LegacySourcesReader(input_dir=input_dir, output_dir=output_dir, config_dir=config_dir)

    subject_registry_df, subject_registry = reader.read_subject_data()

    subject_registry_file = os.path.join(output_dir, 'csr_transformation_data.tsv')
    logger.info('Writing CSR data to {}'.format(subject_registry_file))
    subject_registry_df.to_csv(subject_registry_file, sep='\t', index=False)

    subject_registry_writer = SubjectRegistryWriter(output_dir)
    subject_registry_writer.write(subject_registry)

    study_registry_df, study_registry = reader.read_study_data()

    study_registry_file = os.path.join(output_dir, 'study_registry.tsv')
    logger.info('Writing Study registry data to {}'.format(study_registry_file))
    study_registry_df.to_csv(study_registry_file, sep='\t', index=False)

    study_registry_writer = StudyRegistryWriter(output_dir)
    study_registry_writer.write(study_registry)


def sources2csr(input_dir, output_dir, config_dir):
    try:
        reader = SourcesReader(input_dir=input_dir, output_dir=output_dir, config_dir=config_dir)
        subject_registry = reader.read_subject_data()
        ngs_set = reader.read_ngs_data()
        add_helper_variables(subject_registry, ngs_set)
        subject_registry_writer = SubjectRegistryWriter(output_dir)
        subject_registry_writer.write(subject_registry)

        study_registry = reader.read_study_data()
        study_registry_writer = StudyRegistryWriter(output_dir)
        study_registry_writer.write(study_registry)
    except Exception as e:
        logger.error(f'Error: {e}')
        sys.exit(1)


@click.command()
@click.argument('input_dir')
@click.argument('output_dir')
@click.argument('config_dir')
@click.version_option()
def run(input_dir, output_dir, config_dir):
    sources2csr(input_dir, output_dir, config_dir)


def main():
    run()


if __name__ == '__main__':
    main()
