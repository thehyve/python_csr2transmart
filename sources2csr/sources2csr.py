import os

import logging

import click
from csr2tsv.subject_registry_writer import SubjectRegistryWriter

from csr2tsv.study_registry_writer import StudyRegistryWriter
from sources2csr.sources_reader import SourcesReader


logger = logging.getLogger(__name__)


def sources2csr(input_dir, output_dir, config_dir):
    reader = SourcesReader(input_dir=input_dir, output_dir=output_dir, config_dir=config_dir)

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
